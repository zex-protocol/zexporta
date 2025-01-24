import web3.exceptions
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing import HexStr
from pydantic import ValidationError
from web3 import AsyncHTTPProvider, AsyncWeb3, Web3
from web3.middleware.geth_poa import async_geth_poa_middleware
from web3.types import TxData

from zexporta.config import USER_DEPOSIT_BYTECODE_HASH, USER_DEPOSIT_FACTORY_ADDRESS
from zexporta.custom_types import (
    BlockNumber,
    ChecksumAddress,
    EVMConfig,
    EVMTransfer,
    TxHash,
)
from zexporta.utils.abi import ERC20_ABI
from zexporta.utils.logger import ChainLoggerAdapter
from zexporta.utils.transfer_decoder import (
    InvalidTxError,
    NotRecognizedSolidityFuncError,
    decode_transfer_tx,
)

from .abstract import BaseClientError, ChainAsyncClient


class EVMClientError(BaseClientError):
    """Base exception for EVMAsyncClient errors."""


class EVMTransferNotFound(EVMClientError):
    """Exception raised for transfer not found"""


class EVMTransferNotValid(EVMClientError):
    """Exception raised for transfer not found"""


class EVMBlockNotFound(EVMClientError):
    """Exception raised for transfer not found"""


class EVMAsyncClient(ChainAsyncClient):
    def __init__(self, chain: EVMConfig):
        self.chain = chain
        self._w3 = None

    @property
    def client(self) -> AsyncWeb3:
        if self._w3 is not None:
            return self._w3
        w3 = AsyncWeb3(AsyncHTTPProvider(self.chain.private_rpc))
        if self.chain.poa:
            w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
        self._w3 = w3
        return self._w3

    async def get_transfer_by_tx_hash(self, tx_hash: TxHash) -> EVMTransfer:
        try:
            tx = await self.client.eth.get_transaction(HexStr(tx_hash))
        except web3.exceptions.TransactionNotFound as e:
            raise EVMTransferNotFound(
                f"Transfer with tx_hash: {tx_hash} not found"
            ) from e
        return self._parse_transfer(tx)

    async def get_finalized_block_number(self) -> BlockNumber:
        if self.chain.finalize_block_count is None:
            finalized_block = await self.client.eth.get_block("finalized")
            return finalized_block.number  # type: ignore

        finalized_block_number = (
            await self.get_latest_block_number()
        ) - self.chain.finalize_block_count
        return finalized_block_number

    async def get_token_decimals(self, token_address: ChecksumAddress) -> int:
        min_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function",
            }
        ]

        contract = self.client.eth.contract(address=token_address, abi=min_abi)
        decimals = await contract.functions.decimals().call()
        return decimals

    async def is_transaction_successful(
        self, tx_hash: TxHash, logger: ChainLoggerAdapter
    ) -> bool:
        try:
            receipt = await self.client.eth.get_transaction_receipt(HexStr(tx_hash))
            return receipt["status"] == 1
        except web3.exceptions.TransactionNotFound as e:
            logger.error(f"TransactionNotFound: {e}")
        return False

    async def get_block_tx_hash(
        self, block_number: BlockNumber, **kwargs
    ) -> list[TxHash]:
        block = await self.client.eth.get_block(block_number)
        return [tx_hash.hex() for tx_hash in block.transactions]  # type: ignore

    async def get_latest_block_number(self) -> BlockNumber:
        return await self.client.eth.get_block_number()

    async def extract_transfer_from_block(
        self,
        block_number: BlockNumber,
        logger: ChainLoggerAdapter,
        **kwargs,
    ) -> list[EVMTransfer]:
        logger.debug(f"Observing block number {block_number} start")
        try:
            block = await self.client.eth.get_block(
                block_number, full_transactions=True
            )
        except web3.exceptions.BlockNotFound as e:
            raise EVMBlockNotFound(
                f"Block not found: {block_number}, error: {e}"
            ) from e
        result = []
        for tx in block.transactions:  # type: ignore
            try:
                transfer = self._parse_transfer(tx)
                if transfer is None:
                    continue
                result.append(transfer)
            except NotRecognizedSolidityFuncError:
                ...
            except EVMTransferNotValid as e:
                logger.exception(f"EVMTransferNotValid, {e}")
        logger.debug(f"Observing block number {block_number} end")
        return result

    def _parse_transfer(self, tx: TxData) -> EVMTransfer:
        try:
            decoded_input = decode_transfer_tx(tx["input"].hex())  # type: ignore
            return EVMTransfer(
                tx_hash=tx["hash"].hex(),  # type: ignore
                block_number=tx["blockNumber"],  # type: ignore
                chain_symbol=self.chain.chain_symbol,
                to=decoded_input._to,
                value=decoded_input._value,
                token=tx["to"],  # type: ignore
            )
        except (
            InvalidTxError,
            web3.exceptions.TransactionNotFound,
            ValidationError,
        ) as e:
            raise EVMTransferNotValid(
                f"Transfer with tx_hash {tx} is not valid."  # type: error
            ) from e


_async_clients: dict[str, EVMAsyncClient] = {}


def get_evm_async_client(chain: EVMConfig) -> EVMAsyncClient:
    if client := _async_clients.get(chain.chain_symbol.value):
        return client
    client = EVMAsyncClient(chain)
    _async_clients[chain.chain_symbol.value] = client
    return client


def compute_create2_address(salt: int) -> ChecksumAddress:
    deployer_address = USER_DEPOSIT_FACTORY_ADDRESS
    bytecode_hash = HexStr(USER_DEPOSIT_BYTECODE_HASH)

    deployer_address = Web3.to_checksum_address(deployer_address)
    contract_address = Web3.keccak(
        b"\xff"
        + Web3.to_bytes(hexstr=deployer_address)
        + salt.to_bytes(32, "big")
        + Web3.to_bytes(hexstr=bytecode_hash)
    ).hex()[-40:]
    return Web3.to_checksum_address(contract_address)


def get_signed_data(
    private_key, *, primitive: bytes | None = None, hexstr: str | None = None
) -> str:
    signable = encode_defunct(primitive=primitive, hexstr=hexstr)  # type: ignore
    signed_message = Account.sign_message(signable, private_key)
    return signed_message.signature.hex()


async def get_ERC20_balance(
    w3: AsyncWeb3, contract_address: ChecksumAddress, wallet_address: ChecksumAddress
):
    contract = w3.eth.contract(address=contract_address, abi=ERC20_ABI)

    balance = await contract.functions.balanceOf(wallet_address).call()

    return balance
