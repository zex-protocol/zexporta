import asyncio
import json
import logging
import logging.config
import math
from hashlib import sha256

import httpx
from eth_typing import BlockNumber
from pyfrost.network.sa import SA

from zex_deposit.custom_types import ChainConfig, TransferStatus, UserTransfer, WithdrawRequest
from zex_deposit.db.transfer import (
    to_reorg,
    upsert_transfers,
)
from zex_deposit.utils.abi import VAULT_ABI
from zex_deposit.utils.encode_deposit import DEPOSIT_OPERATION, encode_zex_deposit
from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config
from zex_deposit.utils.node_info import NodesInfo
from zex_deposit.utils.web3 import async_web3_factory, get_finalized_block_number
from zex_deposit.utils.zex_api import (
    ZexAPIError,
    get_zex_latest_block,
    send_deposits, get_zex_withdraws,
)

from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    LOGGER_PATH,
    SA_BATCH_BLOCK_NUMBER_SIZE,
    SA_DELAY_SECOND,
    SA_TIMEOUT,
    ZEX_ENCODE_VERSION,
)

logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/sa.log"))
logger = logging.getLogger(__name__)


nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=SA_TIMEOUT)


def _parse_dkg_json() -> dict:
    with open(DKG_JSON_PATH, "r") as f:
        dkg_info = json.load(f)

    return dkg_info[DKG_NAME]


async def process_withdraw_sa(
    client: httpx.AsyncClient,
    chain: ChainConfig,
    zex_nonce: int,
    dkg_party,
    logger: ChainLoggerAdapter,
):
    logger.info(f"Processing withdraw: {zex_nonce} on {chain.symbol}")

    nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce["data"][0]

    data = {
        "method": "withdraw",
        "data": {
            "zex_nonce": zex_nonce,
            "chain_id": chain.chain_id,
        },
    }

    result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
    logger.debug(f"Validator results is: {result}")

    if result.get("result") == "SUCCESSFUL":
        data = list(result["signature_data_from_node"].values())[0]
        for withdraw in data:


async def send_withdraw(
        w3: AsyncWeb3,
        account: LocalAccount,
        withdraw: WithdrawRequest,
        logger: logging.Logger | ChainLoggerAdapter = logger,
):
    user_deposit = w3.eth.contract(address=transfer.to, abi=VAULT_ABI)
    nonce = await w3.eth.get_transaction_count(account.address)
    tx = await user_deposit.functions.withdraw(
        transfer.token, transfer.value
    ).build_transaction({"from": account.address, "nonce": nonce})
    signed_tx = account.sign_transaction(tx)
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    await w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Method called successfully. Transaction Hash: {tx_hash.hex()}")
    transfer = transfer.model_copy(update={"status": TransferStatus.WITHDRAW.value})
    await upsert_transfer(transfer)

dkg_key = _parse_dkg_json()


async def withdraw(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    while True:
        try:
            client = httpx.AsyncClient()
            w3 = await async_web3_factory(chain)
            dkg_party = dkg_key["party"]
            (
                zex_latest_block,
                finalized_block,
            ) = await asyncio.gather(
                get_zex_latest_block(client, chain),
                get_finalized_block_number(w3, chain),
            )
            if zex_latest_block is None:
                _logger.info(
                    f"Zex did not return latest block for chain: {chain.chain_id.value}"
                )
                continue

            from_block = zex_latest_block + 1
            to_block = finalized_block - 5
            _logger.info(f"from_block: {from_block} , to_block: {to_block}")
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
                except AssertionError as e:
                    logger.error(f"Validator error, to_block: {to_block} | error: {e}")
                    break
        finally:
            await client.aclose()
            await asyncio.sleep(SA_DELAY_SECOND)


async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(withdraw(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
