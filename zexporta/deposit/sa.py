import asyncio
import json
import logging
import logging.config
from hashlib import sha256

import httpx
import sentry_sdk
from pyfrost.network.sa import SA

from zexporta.custom_types import (
    BlockNumber,
    ChainConfig,
    Deposit,
    DepositStatus,
)
from zexporta.db.deposit import (
    get_block_numbers_by_status,
    to_reorg,
    upsert_deposits,
)
from zexporta.utils.dkg import parse_dkg_json
from zexporta.utils.encoder import DEPOSIT_OPERATION, encode_zex_deposit
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config
from zexporta.utils.node_info import NodesInfo
from zexporta.utils.web3 import get_signed_data
from zexporta.utils.zex_api import (
    ZexAPIError,
    send_deposits,
)

from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    LOGGER_PATH,
    SA_BATCH_BLOCK_NUMBER_SIZE,
    SA_SHIELD_PRIVATE_KEY,
    SA_TIMEOUT,
    SENTRY_DNS,
    ZEX_ENCODE_VERSION,
)

logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/sa.log"))
logger = logging.getLogger(__name__)


nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=SA_TIMEOUT)
dkg_key = parse_dkg_json(DKG_JSON_PATH, DKG_NAME)


async def process_deposit(
    client: httpx.AsyncClient,
    chain: ChainConfig,
    blocks: list[BlockNumber],
    dkg_party,
    logger: ChainLoggerAdapter,
):
    logger.info(f"Processing blocks: {blocks}")
    nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce["data"][0]
    data = {
        "method": "deposit",
        "data": {
            "blocks": blocks,
            "chain_id": chain.chain_id,
        },
    }

    result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
    logger.debug(f"Validator results is: {result}")

    if result.get("result") == "SUCCESSFUL":
        data = list(result["signature_data_from_node"].values())[0]["deposits"]
        deposits = [Deposit(**deposit) for deposit in data]
        encoded_data = encode_zex_deposit(
            version=ZEX_ENCODE_VERSION,
            operation_type=DEPOSIT_OPERATION,
            chain=chain,
            deposits=deposits,
        )
        hash_ = sha256(encoded_data).hexdigest()
        if hash_ != result["message_hash"]:
            logger.error("Hash message is not valid.")
            return

        await send_result_to_zex(
            client,
            encoded_data,
            result["nonce"],
            result["signature"],
            logger=logger,
        )
        await upsert_deposits(deposits)
        await to_reorg(chain.chain_id, blocks[0], blocks[-1], DepositStatus.FINALIZED)


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
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    while True:
        try:
            client = httpx.AsyncClient()
            dkg_party = dkg_key["party"]
            finalized_deposit_blocks_number = await get_block_numbers_by_status(
                chain.chain_id, DepositStatus.FINALIZED
            )
            if len(finalized_deposit_blocks_number) <= 0:
                _logger.info("No finalized deposit found.")
                continue
            try:
                await process_deposit(
                    client,
                    chain,
                    finalized_deposit_blocks_number[:SA_BATCH_BLOCK_NUMBER_SIZE],
                    dkg_party,
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
