import asyncio
import json
import logging
import logging.config
import math
from hashlib import sha256

import httpx
from eth_typing import BlockNumber
from pyfrost.network.sa import SA

from zex_deposit.custom_types import ChainConfig, TransferStatus, UserTransfer
from zex_deposit.db.transfer import (
    to_reorg,
    upsert_transfers,
)
from zex_deposit.utils.encode_deposit import DEPOSIT_OPERATION, encode_zex_deposit
from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config
from zex_deposit.utils.node_info import NodesInfo
from zex_deposit.utils.web3 import async_web3_factory, get_finalized_block_number
from zex_deposit.utils.dkg import parse_dkg_json
from zex_deposit.utils.zex_api import (
    ZexAPIError,
    get_zex_latest_block,
    send_deposits,
)

from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    LOGGER_PATH,
    SA_BATCH_BLOCK_NUMBER_SIZE,
    SA_TIMEOUT,
    ZEX_ENCODE_VERSION,
)

logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/sa.log"))
logger = logging.getLogger(__name__)


nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=SA_TIMEOUT)
dkg_key = parse_dkg_json(DKG_JSON_PATH, DKG_NAME)


async def process_sa(
    client: httpx.AsyncClient,
    chain: ChainConfig,
    from_block: BlockNumber | int,
    to_block: BlockNumber | int,
    dkg_party,
    logger: ChainLoggerAdapter,
):
    logger.info(f"Processing blocks: {from_block}, {to_block}")
    nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce["data"][0]
    data = {
        "method": "deposit",
        "data": {
            "from_block": from_block,
            "to_block": to_block,
            "chain_id": chain.chain_id,
        },
    }

    result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
    logger.debug(f"Validator results is: {result}")

    if result.get("result") == "SUCCESSFUL":
        data = list(result["signature_data_from_node"].values())[0]["users_transfers"]
        users_transfers = [UserTransfer(**user_transfer) for user_transfer in data]
        encoded_data = encode_zex_deposit(
            version=ZEX_ENCODE_VERSION,
            operation_type=DEPOSIT_OPERATION,
            chain=chain,
            from_block=from_block,
            to_block=to_block,
            users_transfers=users_transfers,
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
        await upsert_transfers(users_transfers)
        await to_reorg(chain.chain_id, from_block, to_block, TransferStatus.FINALIZED)


async def send_result_to_zex(
    client: httpx.AsyncClient,
    msg: bytes,
    nonce: str,
    signature: int,
    logger: ChainLoggerAdapter | logging.Logger = logger,
) -> None:
    logger.debug("Start sending deposit to Zex.")
    data = msg + nonce.encode() + signature.to_bytes(32, "big")
    logger.debug(f"encoded data to send: {data}")
    result = await send_deposits(client, [data.decode("latin-1")])
    logger.debug("Finish sending deposit to Zex.")
    return result


async def deposit(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    while True:
        try:
            client = httpx.AsyncClient()
            w3 = await async_web3_factory(chain)
            dkg_party = dkg_key["party"]
            try:
                (
                    zex_latest_block,
                    finalized_block,
                ) = await asyncio.gather(
                    get_zex_latest_block(client, chain),
                    get_finalized_block_number(w3, chain),
                )
            except ZexAPIError as e:
                logger.error(f"Can not get from_block or to_block, error: {e}")
                continue

            if zex_latest_block is None:
                _logger.info(
                    f"Zex did not return latest block for chain: {chain.chain_id.value}"
                )
                continue

            from_block = zex_latest_block + 1
            to_block = finalized_block - chain.finalize_block_count
            _logger.info(
                f"from_block: {from_block} , to_block: {to_block}, block_diff: {to_block - from_block}"
            )
            if from_block > to_block:
                continue
            for i in range(
                math.ceil((to_block - from_block) / SA_BATCH_BLOCK_NUMBER_SIZE)
            ):
                try:
                    await process_sa(
                        client,
                        chain,
                        (i * SA_BATCH_BLOCK_NUMBER_SIZE) + from_block,
                        min(
                            ((i + 1) * SA_BATCH_BLOCK_NUMBER_SIZE) + from_block - 1,
                            to_block,
                        ),
                        dkg_party,
                        logger=_logger,
                    )
                except ZexAPIError as e:
                    _logger.error(f"Error at sending deposit to Zex: {e}")
                    break
                except AssertionError as e:
                    _logger.error(f"Validator error, to_block: {to_block} | error: {e}")
                    break
                except (KeyError, json.JSONDecodeError, TypeError) as e:
                    _logger.exception(f"Error occurred in pyfrost, {e}")
                    break
                except asyncio.TimeoutError as e:
                    logger.error(f"Timeout occurred continue after 1 min, error {e}")
                    await asyncio.sleep(60)
        finally:
            await client.aclose()
            await asyncio.sleep(chain.delay)


async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(deposit(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
