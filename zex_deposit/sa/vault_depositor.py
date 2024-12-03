import asyncio
import logging
import logging.config
import os

from web3 import AsyncWeb3
from eth_account.signers.local import LocalAccount


from zex_deposit.custom_types import (
    ChainConfig,
    TransferStatus,
    ChecksumAddress,
    UserTransfer,
)
from zex_deposit.utils.abi import FACTORY_ABI, USER_DEPOSIT_ABI
from zex_deposit.db.transfer import find_transactions_by_status, upsert_transfer
from zex_deposit.utils.web3 import async_web3_factory
from zex_deposit.utils.logger import ChainLoggerAdapter, get_logger_config

from .config import (
    CHAINS_CONFIG,
    LOGGER_PATH,
    USER_DEPOSIT_FACTORY_ADDRESS,
    WITHDRAWER_PRIVATE_KEY,
)


logging.config.dictConfig(get_logger_config(f"{LOGGER_PATH}/withdraw.log"))
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


async def transferERC20(
    w3: AsyncWeb3,
    account: LocalAccount,
    transfer: UserTransfer,
    logger: logging.Logger | ChainLoggerAdapter = logger,
):
    user_deposit = w3.eth.contract(address=transfer.to, abi=USER_DEPOSIT_ABI)
    nonce = await w3.eth.get_transaction_count(account.address)
    tx = await user_deposit.functions.transferERC20(
        transfer.token, transfer.value
    ).build_transaction({"from": account.address, "nonce": nonce})
    signed_tx = account.sign_transaction(tx)
    tx_hash = await w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    await w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Method called successfully. Transaction Hash: {tx_hash.hex()}")
    transfer = transfer.model_copy(update={"status": TransferStatus.WITHDRAW.value})
    await upsert_transfer(transfer)


async def withdraw(chain: ChainConfig):
    _logger = ChainLoggerAdapter(logger, chain.chain_id.name)
    while True:
        try:
            transfers = await find_transactions_by_status(
                status=TransferStatus.VERIFIED, chain_id=chain.chain_id
            )
            if len(transfers) == 0:
                _logger.debug("No transfer has been for withdrawing")
                continue
            w3 = await async_web3_factory(chain)
            account = w3.eth.account.from_key(WITHDRAWER_PRIVATE_KEY)

            for transfer in transfers:
                is_contract = (await w3.eth.get_code(transfer.to)) != b""
                if not is_contract:
                    _logger.info(
                        f"Contract: {transfer.to} not found! Deploying a new one ..."
                    )
                    await deploy_contract(
                        w3,
                        account,
                        w3.to_checksum_address(USER_DEPOSIT_FACTORY_ADDRESS),
                        transfer.user_id,
                        logger=_logger,
                    )

                await transferERC20(w3, account, transfer, logger=_logger)

        except ValueError as e:
            _logger.error(f"Can not deploy contract for {transfer.to}, error: {e}")
            exit(1)

        finally:
            await asyncio.sleep(10)


async def main():
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(withdraw(chain)) for chain in CHAINS_CONFIG.values()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
