import asyncio
import logging
from operator import add
import time
from typing import Any, Callable, Coroutine, Iterable, TypeVar

from eth_typing import HexStr
from pydantic import ValidationError
from web3 import AsyncHTTPProvider, AsyncWeb3, Web3
from web3.middleware.geth_poa import async_geth_poa_middleware

from zex_deposit.utils.abi import VAULT_ABI
from zex_deposit.custom_types import (
    BlockNumber,
    ChainConfig,
    ChainId,
    ChecksumAddress,
    RawTransfer,
    TransferStatus,
    TxHash,
)
from zex_deposit.utils.transfer_decoder import (
    InvalidTxError,
    NotRecognizedSolidityFuncError,
    decode_transfer_tx,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def async_web3_factory(chain: ChainConfig) -> AsyncWeb3:
    w3 = AsyncWeb3(AsyncHTTPProvider(chain.private_rpc))
    if chain.poa:
        w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
    return w3


async def _filter_blocks(
    w3: AsyncWeb3,
    blocks: Iterable[BlockNumber],
    fn: Callable[..., Coroutine[Any, Any, list[T]]],
    **kwargs,
) -> list[T]:
    tasks = [asyncio.create_task(fn(w3, BlockNumber(i), **kwargs)) for i in blocks]
    result = []
    for task in tasks:
        result.extend(await task)
    return result


async def filter_blocks(
    w3,
    blocks_number: Iterable[BlockNumber],
    fn: Callable[..., Coroutine[Any, Any, list[T]]],
    max_delay_per_block_batch: int | float = 5,
    **kwargs,
) -> list[T]:
    start = time.time()
    result = await _filter_blocks(w3, blocks_number, fn, **kwargs)
    end = time.time()
    await asyncio.sleep(max(max_delay_per_block_batch - (end - start), 0))
    return result


async def extract_transfer_from_block(
    w3: AsyncWeb3,
    block_number: BlockNumber,
    chain_id: ChainId,
    transfer_status: TransferStatus = TransferStatus.PENDING,
    logger=logger,
    **kwargs,
) -> list[RawTransfer]:
    logger.debug(f"Observing block number {block_number} start")
    block = await w3.eth.get_block(block_number, full_transactions=True)
    result = []
    for tx in block.transactions:  # type: ignore
        try:
            decoded_input = decode_transfer_tx(tx.input.hex())
            result.append(
                RawTransfer(
                    tx_hash=tx.hash.hex(),
                    block_number=block_number,
                    chain_id=chain_id,
                    to=decoded_input._to,
                    value=decoded_input._value,
                    status=transfer_status,
                    token=tx.to,
                    block_timestamp=block.timestamp,  # type: ignore
                )
            )
        except NotRecognizedSolidityFuncError as _:
            ...
        except InvalidTxError as e:
            logger.error(f"invalid tx {tx}, error: {e}")
        except ValidationError as e:
            logger.error(f"Invalid transaction input, tx: {tx}, error {e}")
    logger.debug(f"Observing block number {block_number} end")
    return result


async def get_block_tx_hash(
    w3: AsyncWeb3, block_number: BlockNumber, **kwargs
) -> list[TxHash]:
    block = await w3.eth.get_block(block_number)
    return [tx_hash.hex() for tx_hash in block.transactions]  # type: ignore


async def get_finalized_block_number(w3: AsyncWeb3, chain: ChainConfig) -> BlockNumber:
    if chain.finalize_block_count is None:
        finalized_block = await w3.eth.get_block("finalized")
        return finalized_block.number  # type: ignore

    finalized_block_number = chain.finalize_block_count + (
        await w3.eth.get_block_number()
    )
    return BlockNumber(finalized_block_number)


def compute_create2_address(deployer_address: str, salt: int, bytecode_hash: HexStr):
    deployer_address = Web3.to_checksum_address(deployer_address)
    contract_address = Web3.keccak(
        b"\xff"
        + Web3.to_bytes(hexstr=deployer_address)
        + salt.to_bytes(32, "big")
        + Web3.to_bytes(hexstr=bytecode_hash)
    ).hex()[-40:]
    return Web3.to_checksum_address(contract_address)


async def get_token_decimals(w3: AsyncWeb3, token_address: ChecksumAddress) -> int:
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

    contract = w3.eth.contract(address=token_address, abi=min_abi)
    decimals = await contract.functions.decimals().call()
    return decimals


async def get_vault_nonce(w3: AsyncWeb3, vault_address: ChecksumAddress) -> int:
    contract = w3.eth.contract(address=vault_address, abi=VAULT_ABI)
    return await contract.functions.nonce().call()
