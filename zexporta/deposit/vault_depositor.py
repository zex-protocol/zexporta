import asyncio
import logging
import logging.config

import sentry_sdk
import web3.exceptions
from clients.evm import get_evm_async_client
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3

from zexporta.custom_types import (
    ChecksumAddress,
    Deposit,
    DepositStatus,
    EVMConfig,
)
from zexporta.db.deposit import find_deposit_by_status, upsert_deposit
from zexporta.utils.abi import FACTORY_ABI, USER_DEPOSIT_ABI
from zexporta.utils.logger import ChainLoggerAdapter, get_logger_config

from .config import (
    CHAINS_CONFIG,
    EVM_NATIVE_TOKEN_ADDRESS,
    LOGGER_PATH,
    SENTRY_DNS,
    USER_DEPOSIT_FACTORY_ADDRESS,
    WITHDRAWER_PRIVATE_KEY,
)

logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/vault_depositor.log"))
logger = logging.getLogger(__name__)


async def deploy_contract(
    w3: AsyncWeb3,
    account: LocalAccount,
    factory_address: ChecksumAddress,
    salt: int,
    logger: logging.Logger | ChainLoggerAdapter = logger,
):
    factory_contract = w3.eth.contract(address=factory_address, abi=FACTORY_ABI)
    nonce = await w3.eth.get_transaction_count(account.address)
    deploy_tx = await factory_contract.functions.deploy(salt).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
        }
    )

    signed_tx = account.sign_transaction(deploy_tx)
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)

    # Decode the Deployed event from the receipt logs
    deployed_event = factory_contract.events.Deployed()
    events = deployed_event.process_receipt(receipt)

    if events:
        contract_address = events[0]["args"]["addr"]
        logger.info(f"Deployed contract address: {contract_address}")
    else:
        raise ValueError("Deployed event not found in transaction logs")


async def transfer_token(
    w3: AsyncWeb3,
    account: LocalAccount,
    deposit: Deposit,
    logger: logging.Logger | ChainLoggerAdapter = logger,
) -> Deposit:
    user_deposit = w3.eth.contract(address=deposit.transfer.to, abi=USER_DEPOSIT_ABI)  # type: ignore
    nonce = await w3.eth.get_transaction_count(account.address)
    logger.info(f"to: {deposit.transfer.token}")
    if deposit.transfer.token == EVM_NATIVE_TOKEN_ADDRESS:
        logger.info("Creating transferNativeToken tx.")
        tx = await user_deposit.functions.transferNativeToken(
            deposit.transfer.value
        ).build_transaction({"from": account.address, "nonce": nonce})
    else:
        logger.info("Creating transferERC20 token tx.")
        tx = await user_deposit.functions.transferERC20(
            deposit.transfer.token, deposit.transfer.value
        ).build_transaction({"from": account.address, "nonce": nonce})
    signed_tx = account.sign_transaction(tx)
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    logger.info(f"Transaction Hash: {tx_hash.hex()}")
    await w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info("Method called successfully.")
    deposit.status = DepositStatus.SUCCESSFUL
    return deposit


async def withdraw(chain: EVMConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
    while True:
        try:
            deposits = await find_deposit_by_status(
                chain, status=DepositStatus.VERIFIED
            )
            if len(deposits) == 0:
                _logger.debug("Deposit not found.")
                continue
            w3 = get_evm_async_client(chain).client
            account = w3.eth.account.from_key(WITHDRAWER_PRIVATE_KEY)

            for deposit in deposits:
                is_contract = (await w3.eth.get_code(deposit.transfer.to)) != b""  # type: ignore
                if not is_contract:
                    _logger.info(
                        f"Contract: {deposit.transfer.to} not found! Deploying a new one ..."
                    )
                    await deploy_contract(
                        w3,
                        account,
                        w3.to_checksum_address(USER_DEPOSIT_FACTORY_ADDRESS),
                        deposit.user_id,
                        logger=_logger,
                    )
                try:
                    deposit = await transfer_token(w3, account, deposit, logger=_logger)
                except web3.exceptions.ContractCustomError as e:
                    _logger.error(
                        f"Error while trying to transfer ERC20 to contract {deposit.transfer.to} , error: {e}"
                    )

                await upsert_deposit(chain=chain, deposit=deposit)

        except ValueError as e:
            _logger.error(
                f"Can not deploy contract for {deposit.transfer.to}, error: {e}"
            )

        finally:
            await asyncio.sleep(10)


async def main():
    loop = asyncio.get_running_loop()
    tasks = [
        loop.create_task(withdraw(chain))
        for chain in CHAINS_CONFIG.values()
        if isinstance(chain, EVMConfig)
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentry_sdk.init(
        dsn=SENTRY_DNS,
    )
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
