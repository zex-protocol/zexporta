import asyncio
import json
import logging
import logging.config

import httpx
import web3.exceptions
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from pyfrost.network.sa import SA
from web3 import AsyncWeb3, Web3

from zex_deposit.custom_types import (
    ChainConfig,
    WithdrawRequest,
)
from zex_deposit.db.chain import (
    get_last_withdraw_nonce,
    upsert_chain_last_withdraw_nonce,
)
from zex_deposit.utils.abi import VAULT_ABI
from zex_deposit.utils.decode_error import decode_custom_error_data
from zex_deposit.utils.dkg import parse_dkg_json
from zex_deposit.utils.encoder import get_withdraw_hash
from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config
from zex_deposit.utils.node_info import NodesInfo
from zex_deposit.utils.web3 import async_web3_factory, get_signed_data
from zex_deposit.utils.zex_api import (
    ZexAPIError,
    get_zex_last_withdraw_nonce,
    get_zex_withdraw,
)

from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    LOGGER_PATH,
    SA_DELAY_SECOND,
    SA_SHIELD_PRIVATE_KEY,
    SA_TIMEOUT,
    WITHDRAWER_PRIVATE_KEY,
)


class WithdrawDifferentHash(Exception):
    """Raise when validator hash is different from sa hash"""


logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/sa-withdrawer.log"))
logger = logging.getLogger(__name__)

nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=SA_TIMEOUT)
dkg_key = dkg_key = parse_dkg_json(DKG_JSON_PATH, DKG_NAME)


async def check_validator_data(
    chain: ChainConfig,
    zex_withdraw: WithdrawRequest,
    validator_hash: str,
):
    withdraw_hash = get_withdraw_hash(zex_withdraw)
    if withdraw_hash != validator_hash:
        raise WithdrawDifferentHash(
            f"validator_hash: {validator_hash}, withdraw_hash: {withdraw_hash}"
        )


async def process_withdraw_sa(
    w3: AsyncWeb3,
    client: httpx.AsyncClient,
    account: LocalAccount,
    chain: ChainConfig,
    sa_withdraw_nonce: int,
    dkg_party,
    logger: ChainLoggerAdapter,
):
    last_nonce = await get_zex_last_withdraw_nonce(client, chain)

    if sa_withdraw_nonce >= last_nonce:
        logger.info("No withdraw to process ...")
        return

    nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce["data"][0]

    data = {
        "method": "withdraw",
        "data": {
            "chain_id": chain.chain_id,
            "sa_withdraw_nonce": sa_withdraw_nonce,
        },
    }

    result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
    logger.debug(f"Validator results is: {result}")

    if result.get("result") == "SUCCESSFUL":
        validator_hash = result["message_hash"]
        zex_withdraw = await get_zex_withdraw(
            client, chain, offset=sa_withdraw_nonce, limit=sa_withdraw_nonce + 1
        )
        await check_validator_data(
            chain, zex_withdraw=zex_withdraw, validator_hash=validator_hash
        )
        data = list(result["signature_data_from_node"].values())[0]
        await send_withdraw(
            w3,
            chain,
            account,
            result["signature"],
            zex_withdraw,
            Web3.to_checksum_address(result["nonce"]),
            logger,
        )
        await upsert_chain_last_withdraw_nonce(
            chain_id=chain.chain_id, nonce=sa_withdraw_nonce + 1
        )


async def send_withdraw(
    w3: AsyncWeb3,
    chain: ChainConfig,
    account: LocalAccount,
    signature: str,
    withdraw_request: WithdrawRequest,
    signature_nonce: ChecksumAddress,
    logger: logging.Logger | ChainLoggerAdapter = logger,
):
    vault = w3.eth.contract(address=chain.vault_address, abi=VAULT_ABI)
    nonce = await w3.eth.get_transaction_count(account.address)
    withdraw_hash = get_withdraw_hash(withdraw_request)
    signed_data = get_signed_data(SA_SHIELD_PRIVATE_KEY, hexstr=withdraw_hash)
    logger.debug(f"Signed Withdraw data is: {signed_data}")
    tx = await vault.functions.withdraw(
        withdraw_request.token_address,
        withdraw_request.amount,
        withdraw_request.recipient,
        withdraw_request.nonce,
        signature,
        signature_nonce,
        signed_data,
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
            last_withdraw_nonce = await get_last_withdraw_nonce(chain.chain_id)
            await process_withdraw_sa(
                w3=w3,
                client=client,
                account=account,
                chain=chain,
                sa_withdraw_nonce=last_withdraw_nonce + 1,
                dkg_party=dkg_party,
                logger=_logger,
            )
        except ZexAPIError as e:
            _logger.error(f"Error at sending deposit to Zex: {e}")
            continue
        except (web3.exceptions.ContractCustomError,) as e:
            _logger.error(
                f"Contract Error, error: {e.message} , decoded_error: {decode_custom_error_data(e.message, VAULT_ABI)}"
            )

            await upsert_chain_last_withdraw_nonce(
                chain_id=chain.chain_id, nonce=last_withdraw_nonce + 1
            )

        except web3.exceptions.Web3Exception as e:
            _logger.error(f"Web3Error: {e}")
            await asyncio.sleep(60)
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
