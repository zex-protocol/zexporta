import asyncio
import json
import logging
import logging.config

from eth_typing import ChecksumAddress
import httpx
from pyfrost.network.sa import SA
from web3 import AsyncWeb3, Web3
from eth_account.signers.local import LocalAccount

from zex_deposit.custom_types import (
    ChainConfig,
    WithdrawRequest,
)
from .config import WITHDRAWER_PRIVATE_KEY
from zex_deposit.utils.abi import VAULT_ABI
from zex_deposit.utils.dkg import parse_dkg_json
from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config
from zex_deposit.utils.node_info import NodesInfo
from zex_deposit.utils.web3 import async_web3_factory, get_vault_nonce
from zex_deposit.utils.zex_api import (
    ZexAPIError,
)

from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    LOGGER_PATH,
    SA_DELAY_SECOND,
    SA_TIMEOUT,
    VAULT_ADDRESS,
)

logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/sa.log"))
logger = logging.getLogger(__name__)

nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=SA_TIMEOUT)
dkg_key = dkg_key = parse_dkg_json(DKG_JSON_PATH, DKG_NAME)


async def process_withdraw_sa(
    w3: AsyncWeb3,
    account: LocalAccount,
    chain: ChainConfig,
    dkg_party,
    logger: ChainLoggerAdapter,
):
    nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce["data"][0]

    vault_nonce = await get_vault_nonce(w3, Web3.to_checksum_address(VAULT_ADDRESS))

    data = {
        "method": "withdraw",
        "data": {"chain_id": chain.chain_id, "vault_nonce": vault_nonce},
    }

    result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
    logger.debug(f"Validator results is: {result}")

    if result.get("result") == "SUCCESSFUL":
        data = list(result["signature_data_from_node"].values())[0]["data"]

        await send_withdraw(
            w3,
            account,
            result["signature"],
            WithdrawRequest(**data),
            result["nonce"],
            logger,
        )


async def send_withdraw(
    w3: AsyncWeb3,
    account: LocalAccount,
    signature: str,
    withdraw_request: WithdrawRequest,
    signature_nonce: ChecksumAddress,
    logger: logging.Logger | ChainLoggerAdapter = logger,
):
    vault = w3.eth.contract(
        address=Web3.to_checksum_address(VAULT_ADDRESS), abi=VAULT_ABI
    )
    nonce = await w3.eth.get_transaction_count(account.address)
    tx = await vault.functions.withdraw(
        withdraw_request.token_address,
        withdraw_request.amount,
        withdraw_request.recipient,
        withdraw_request.nonce,
        signature,
        signature_nonce,
    ).build_transaction({"from": account.address, "nonce": nonce})
    signed_tx = account.sign_transaction(tx)
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    await w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Method called successfully. Transaction Hash: {tx_hash.hex()}")


async def withdraw(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)

    while True:
        try:
            w3 = await async_web3_factory(chain)
            account = w3.eth.account.from_key(WITHDRAWER_PRIVATE_KEY)

            client = httpx.AsyncClient()
            dkg_party = dkg_key["party"]

            try:
                await process_withdraw_sa(
                    w3=w3,
                    account=account,
                    chain=chain,
                    dkg_party=dkg_party,
                    logger=_logger,
                )
            except ZexAPIError as e:
                _logger.error(f"Error at sending deposit to Zex: {e}")
                continue
            except AssertionError as e:
                _logger.error(f"Validator error, error: {e}")
                continue
            except (KeyError, json.JSONDecodeError, TypeError) as e:
                _logger.exception(f"Error occurred in pyfrost, {e}")
                continue
            except asyncio.TimeoutError as e:
                logger.error(f"Timeout occurred continue after 1 min, error {e}")
                await asyncio.sleep(60)
                continue
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
