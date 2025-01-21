import asyncio
import json
import logging
import logging.config
from datetime import datetime, timezone
from hashlib import sha256

import httpx
import sentry_sdk
from pyfrost.network.sa import SA

from zexporta.clients.evm import get_signed_data
from zexporta.custom_types import (
    BlockNumber,
    ChainConfig,
    ChainSymbol,
    Deposit,
    DepositStatus,
    SaDepositSchema,
    TxHash,
)
from zexporta.db.deposit import (
    find_deposit_by_status,
    to_reorg_with_tx_hash,
    upsert_deposits,
)
from zexporta.utils.dkg import parse_dkg_json
from zexporta.utils.encoder import DEPOSIT_OPERATION, encode_zex_deposit
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config
from zexporta.utils.node_info import NodesInfo
from zexporta.utils.zex_api import (
    ZexAPIError,
    send_deposits,
)

from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    LOGGER_PATH,
    SA_SHIELD_PRIVATE_KEY,
    SA_TIMEOUT,
    SA_TRANSACTIONS_BATCH_SIZE,
    SENTRY_DNS,
    ZEX_ENCODE_VERSION,
)

logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/sa.log"))
logger = logging.getLogger(__name__)


nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=SA_TIMEOUT)
dkg_key = parse_dkg_json(DKG_JSON_PATH, DKG_NAME)


class DepositDifferentHashError(Exception):
    """Raise when validator hash is different from sa hash"""


async def process_deposit(
    client: httpx.AsyncClient,
    chain_symbol: ChainSymbol,
    txs_hash: list[TxHash],
    dkg_party: list[str],
    finalized_block_number: BlockNumber,
    logger: ChainLoggerAdapter,
):
    logger.info(f"Processing txs: {txs_hash}")
    nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce["data"][0]
    data = {
        "method": "deposit",
        "data": SaDepositSchema(
            txs_hash=txs_hash,
            timestamp=int(datetime.now(timezone.utc).timestamp()),
            chain_symbol=chain_symbol,
            finalized_block_number=finalized_block_number,
        ).model_dump(mode="json"),
    }

    result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
    logger.debug(f"Validator results is: {result}")

    if result.get("result") == "SUCCESSFUL":
        data = list(result["signature_data_from_node"].values())[0]["deposits"]
        deposits = [Deposit(**deposit) for deposit in data]
        encoded_data = encode_zex_deposit(
            version=ZEX_ENCODE_VERSION,
            operation_type=DEPOSIT_OPERATION,
            chain_symbol=chain_symbol,
            deposits=deposits,
        )
        hash_ = sha256(encoded_data).hexdigest()
        if hash_ != result["message_hash"]:
            raise DepositDifferentHashError("Hash message is not valid")

        await send_result_to_zex(
            client,
            encoded_data,
            result["nonce"],
            result["signature"],
            logger=logger,
        )
        await upsert_deposits(deposits)
        await to_reorg_with_tx_hash(
            chain_symbol=chain_symbol,
            txs_hash=txs_hash,
            status=DepositStatus.FINALIZED,
        )


async def send_result_to_zex(
    client: httpx.AsyncClient,
    msg: bytes,
    nonce: str,
    signature: int,
    logger: ChainLoggerAdapter | logging.Logger = logger,
) -> None:
    logger.debug("Start sending deposit to Zex.")
    _data = msg + nonce.encode() + signature.to_bytes(32, "big")
    signed_data = get_signed_data(SA_SHIELD_PRIVATE_KEY, primitive=msg).encode()
    data = _data + signed_data
    logger.debug(f"encoded data to send: {data}")
    result = await send_deposits(client, [data.decode("latin-1")])
    logger.debug("Finish sending deposit to Zex.")
    return result


async def deposit(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
    while True:
        try:
            client = httpx.AsyncClient()
            dkg_party = dkg_key["party"]
            deposits = await find_deposit_by_status(
                chain_symbol=chain.chain_symbol,
                status=DepositStatus.FINALIZED,
                limit=SA_TRANSACTIONS_BATCH_SIZE,
            )
            txs_hash = [deposit.tx_hash for deposit in (deposits)]
            if len(txs_hash) <= 0:
                _logger.info("No finalized deposit found.")
                continue
            finalized_block_number = deposits[-1].block_number
            try:
                await process_deposit(
                    client,
                    chain.chain_symbol,
                    txs_hash,
                    dkg_party,
                    finalized_block_number=finalized_block_number,
                    logger=_logger,
                )
            except ZexAPIError as e:
                _logger.error(f"Error at sending deposit to Zex: {e}")
            except AssertionError as e:
                _logger.error(f"Validator error, error: {e}")
            except (KeyError, json.JSONDecodeError, TypeError) as e:
                _logger.exception(f"Error occurred in pyfrost, {e}")
            except asyncio.TimeoutError as e:
                _logger.error(f"Timeout occurred continue after 1 min, error {e}")
            except DepositDifferentHashError as e:
                _logger.error(e)

        finally:
            await client.aclose()
            await asyncio.sleep(chain.delay)


async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(deposit(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
