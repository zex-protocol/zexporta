import asyncio
import json
import logging
import logging.config

import sentry_sdk
import web3.exceptions
from bitcoinutils.keys import PrivateKey
from bitcoinutils.transactions import TxWitnessInput
from bitcoinutils.utils import to_satoshis
from clients import BTCAsyncClient, ChainAsyncClient, get_async_client
from clients.evm import EVMAsyncClient, get_signed_data
from eth_typing import ChecksumAddress
from pyfrost.network.sa import SA
from web3 import Web3
from zellular import Zellular

from zexporta.config import (
    BTC_WITHDRAWER_PRIVATE_KEY,
    EVM_WITHDRAWER_PRIVATE_KEY,
    SEQUENCER_APP_NAME,
    SEQUENCER_BASE_URL,
)
from zexporta.custom_types import (
    UTXO,
    BTCConfig,
    BTCWithdrawRequest,
    ChainConfig,
    EVMConfig,
    EVMWithdrawRequest,
    UtxoStatus,
    WithdrawRequest,
    WithdrawStatus,
)
from zexporta.db.utxo import find_utxo_by_status, upsert_utxo
from zexporta.db.withdraw import find_withdraws_by_status, upsert_withdraw
from zexporta.utils.abi import VAULT_ABI
from zexporta.utils.decode_error import decode_custom_error_data
from zexporta.utils.dkg import parse_dkg_json
from zexporta.utils.encoder import get_evm_withdraw_hash
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config
from zexporta.utils.node_info import NodesInfo
from zexporta.utils.zex_api import (
    ZexAPIError,
)
from zexporta.withdraw.btc_utils import (
    NotEnoughInputs,
    calculate_fee,
    get_simple_withdraw_tx,
)

from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    LOGGER_PATH,
    SA_DELAY_SECOND,
    SA_SHIELD_PRIVATE_KEY,
    SA_TIMEOUT,
    SENTRY_DNS,
)


class WithdrawDifferentHashError(Exception):
    """Raise when validator hash is different from sa hash"""


class ValidatorResultError(Exception):
    """Raise when validator result is not successful"""


logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/sa.log"))
logger = logging.getLogger(__name__)

nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=SA_TIMEOUT)
dkg_key = parse_dkg_json(DKG_JSON_PATH, DKG_NAME)


async def check_validator_data(
    chain: ChainConfig,
    zex_withdraw: WithdrawRequest,
    validator_hash: str,
):
    match chain:
        case EVMConfig():
            withdraw_hash = get_evm_withdraw_hash(zex_withdraw)
        case BTCConfig():
            tx, _ = get_simple_withdraw_tx(zex_withdraw, chain.vault_address)
            withdraw_hash = tx.to_hex()
        case _:
            raise NotImplementedError
    if withdraw_hash != validator_hash:
        raise WithdrawDifferentHashError(
            f"validator_hash: {validator_hash}, withdraw_hash: {withdraw_hash}"
        )


async def process_withdraw_sa(
    chain: EVMConfig,
    withdraw_request: WithdrawRequest,
    dkg_party,
    logger: ChainLoggerAdapter,
):
    client = get_async_client(chain)
    match chain:
        case EVMConfig():
            _process_sa = process_evm_withdraw_sa
        case BTCConfig():
            _process_sa = process_btc_withdraw_sa
        case _:
            raise NotImplementedError

    await _process_sa(
        client=client,
        chain=chain,
        withdraw_request=withdraw_request,
        dkg_party=dkg_party,
        logger=logger,
    )


async def process_evm_withdraw_sa(
    client: EVMAsyncClient,
    chain: EVMConfig,
    withdraw_request: EVMWithdrawRequest,
    dkg_party,
    logger: ChainLoggerAdapter,
):
    nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce["data"][0]

    data = {
        "method": "withdraw",
        "data": {
            "chain_symbol": chain.chain_symbol,
            "sa_withdraw_nonce": withdraw_request.nonce,
        },
    }
    logger.debug(f"Zex withdraw request is: {withdraw_request}")
    result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
    logger.debug(f"Validator results is: {result}")

    if result.get("result") == "SUCCESSFUL":
        validator_hash = result["message_hash"]
        await check_validator_data(
            chain=chain, zex_withdraw=withdraw_request, validator_hash=validator_hash
        )
        data = list(result["signature_data_from_node"].values())[0]
        await send_evm_withdraw(
            client,
            chain,
            result["signature"],
            withdraw_request,
            Web3.to_checksum_address(result["nonce"]),
            logger,
        )
    else:
        raise ValidatorResultError(result)


async def send_evm_withdraw(
    client: EVMAsyncClient,
    chain: EVMConfig,
    signature: str,
    withdraw_request: EVMWithdrawRequest,
    signature_nonce: ChecksumAddress,
    logger: logging.Logger | ChainLoggerAdapter = logger,
):
    w3 = client.client
    account = w3.eth.account.from_key(EVM_WITHDRAWER_PRIVATE_KEY)
    vault = w3.eth.contract(address=chain.vault_address, abi=VAULT_ABI)
    nonce = await w3.eth.get_transaction_count(account.address)
    withdraw_hash = get_evm_withdraw_hash(withdraw_request)
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
    withdraw_request.tx_hash = tx_hash.hex()
    await w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Method called successfully. Transaction Hash: {tx_hash.hex()}")


async def get_utxos_for_withdraw(
    withdraw_request: BTCWithdrawRequest, change_address: str
) -> list[UTXO]:
    inputs = []
    amount = 0
    withdraw_amount = to_satoshis(withdraw_request.amount)
    utxos = await find_utxo_by_status(status=UtxoStatus.UNSPENT)
    for utxo in utxos:
        inputs.append(utxo)
        amount += utxo.amount
        fee = calculate_fee(
            recipient=withdraw_request.recipient,
            change_address=change_address,
            amount=withdraw_amount,
            sat_per_byte=withdraw_request.sat_per_byte,
            utxos=inputs,
        )
        if amount >= fee + withdraw_amount:
            return inputs
    else:
        raise NotEnoughInputs


async def process_btc_withdraw_sa(
    client: BTCAsyncClient,
    chain: BTCConfig,
    withdraw_request: BTCWithdrawRequest,
    dkg_party,
    logger: ChainLoggerAdapter,
):
    if withdraw_request.status == WithdrawStatus.PROCESSING:
        if withdraw_request.utxos is None:
            withdraw_request.sat_per_byte = client.client.get_fee_per_byte()
            utxos = get_utxos_for_withdraw(
                withdraw_request, change_address=chain.vault_address
            )
            for utxo in utxos:
                utxo.status = UtxoStatus.SPEND
                await upsert_utxo(utxo)
            withdraw_request.utxos = utxos
            await upsert_withdraw(withdraw_request)

        data = {
            "operation": "withdraw_tx_data",
            "data": withdraw_request.json(),
        }

        zellular = Zellular(SEQUENCER_APP_NAME, SEQUENCER_BASE_URL)
        index = zellular.send([data], blocking=True)
        withdraw_request.status = WithdrawStatus.PENDING
        withdraw_request.zellular_index = index
        await upsert_withdraw(withdraw_request)
        logger.info(f"sequencer updated with index:{index}, data:{data}")

    else:
        nonces_response = await sa.request_nonces(dkg_party, number_of_nonces=1)
        nonces_for_sig = {}
        for id, nonce in nonces_response.items():
            nonces_for_sig[id] = nonce["data"][0]

        data = {
            "method": "withdraw",
            "data": withdraw_request.json(),
        }
        logger.debug(f"Zex withdraw request is: {withdraw_request}")
        result = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
        logger.debug(f"Validator results is: {result}")

        if result.get("result") == "SUCCESSFUL":
            validator_hash = result["message_hash"]
            await check_validator_data(
                chain=chain,
                zex_withdraw=withdraw_request,
                validator_hash=validator_hash,
            )
            await send_btc_withdraw(
                client,
                chain,
                withdraw_request,
                result,
                logger,
            )
        else:
            raise ValidatorResultError(result)


async def send_btc_withdraw(
    client: ChainAsyncClient,
    chain: BTCConfig,
    withdraw_request: BTCWithdrawRequest,
    group_sign: dict,
    logger: logging.Logger | ChainLoggerAdapter = logger,
):
    assert group_sign is not None
    btc = client.client

    to_address = withdraw_request.recipient
    amount = withdraw_request.amount
    logging.info(f"Sending: {amount}, to:{to_address}")

    tx, tx_digests = get_simple_withdraw_tx(
        withdraw_request,
        chain.vault_address,
    )

    private = PrivateKey.from_bytes(BTC_WITHDRAWER_PRIVATE_KEY)

    for i, utxo in withdraw_request.utxos:
        sig = private.sign_taproot_input(tx, i, utxo.script, utxo.amount)
        tx.witnesses.append(TxWitnessInput([sig, utxo.address]))

    raw_tx = tx.serialize()
    logging.info(f"Raw tx: {raw_tx}")

    resp = await btc.send_tx(raw_tx)
    logger.info(
        f"Transaction Info: {json.dumps({'raw_tx': raw_tx, 'tx_hash': resp.text}, indent=4)}"
    )


async def withdraw(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)

    while True:
        try:
            dkg_party = dkg_key["party"]
            withdraws_request = await find_withdraws_by_status(
                [WithdrawStatus.PENDING, WithdrawStatus.PROCESSING], chain.chain_id
            )
            if len(withdraws_request) == 0:
                _logger.debug(
                    f"No {WithdrawStatus.PENDING.value} has been found to process ..."
                )
                continue
            for withdraw_request in withdraws_request:
                try:
                    await process_withdraw_sa(
                        chain=chain,
                        withdraw_request=withdraw_request,
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
                    withdraw_request.status = WithdrawStatus.REJECTED
                    await upsert_withdraw(withdraw_request)

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
                    _logger.error(f"Timeout occurred continue after 1 min, error {e}")
                    await asyncio.sleep(60)
                    continue
                except ValidatorResultError as e:
                    _logger.error(f"Validator result is not successful, error {e}")
                except WithdrawDifferentHashError as e:
                    _logger.error(
                        f"data that process in zex is different from validators: {e}"
                    )
                    withdraw_request.status = WithdrawStatus.REJECTED
                    await upsert_withdraw(withdraw_request)
                else:
                    withdraw_request.status = WithdrawStatus.SUCCESSFUL
                    await upsert_withdraw(withdraw_request)
        finally:
            await asyncio.sleep(SA_DELAY_SECOND)


async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(withdraw(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
