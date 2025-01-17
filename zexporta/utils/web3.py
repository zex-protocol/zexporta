import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Iterable

import web3.exceptions
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_typing import HexStr
from pydantic import ValidationError
from web3 import AsyncHTTPProvider, AsyncWeb3, Web3
from web3.middleware.geth_poa import async_geth_poa_middleware

from zexporta.custom_types import (
    BlockNumber,
    ChainConfig,
    ChainId,
    ChecksumAddress,
    Timestamp,
    Transfer,
    TxHash,
)
from zexporta.utils.transfer_decoder import (
    InvalidTxError,
    NotRecognizedSolidityFuncError,
    decode_transfer_tx,
)

from .abi import ERC20_ABI

logger = logging.getLogger(__name__)

_w3_clients: dict[int, AsyncWeb3] = {}


async def async_web3_factory(chain: ChainConfig) -> AsyncWeb3:
    if w3 := _w3_clients.get(chain.chain_id.value):
        if await w3.is_connected():
            return w3

    w3 = AsyncWeb3(AsyncHTTPProvider(chain.private_rpc))
    if chain.poa:
        w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
    _w3_clients[chain.chain_id.value] = w3
    return w3


async def _filter_blocks[T: (Transfer, TxHash)](
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


async def filter_blocks[T: (Transfer, TxHash)](
    w3,
    blocks_number: Iterable[BlockNumber],
    fn: Callable[..., Coroutine[Any, Any, list[T]]],
    max_delay_per_block_batch: int | float = 5,
    **kwargs,
) -> list[T]:
    start = time.monotonic()
    result = await _filter_blocks(w3, blocks_number, fn, **kwargs)
    end = time.monotonic()
    await asyncio.sleep(max(max_delay_per_block_batch - (end - start), 0))
    return result


async def extract_transfer_from_block(
    w3: AsyncWeb3,
    block_number: BlockNumber,
    chain_id: ChainId,
    logger=logger,
    **kwargs,
) -> list[Transfer]:
    logger.debug(f"Observing block number {block_number} start")
    block = await w3.eth.get_block(block_number, full_transactions=True)
    result = []
    for tx in block.transactions:  # type: ignore
        try:
            decoded_input = decode_transfer_tx(tx.input.hex())
            result.append(
                Transfer(
                    tx_hash=tx.hash.hex(),
                    block_number=block_number,
                    chain_id=chain_id,
                    to=decoded_input._to,
                    value=decoded_input._value,
                    token=tx.to,
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


async def get_transfers_by_tx(
    w3: AsyncWeb3, tx_hash: TxHash, sa_timestamp: Timestamp
) -> Transfer | None:
    tx = await w3.eth.get_transaction(HexStr(tx_hash))
    w3.eth.get_transaction_receipt
    try:
        decoded_input = decode_transfer_tx(tx["input"].hex())  # type: ignore
        return Transfer(
            tx_hash=tx["hash"].hex(),  # type: ignore
            block_number=tx["blockNumber"],  # type: ignore
            chain_id=ChainId(tx["chainId"]),  # type: ignore
            to=decoded_input._to,
            value=decoded_input._value,
            token=tx["to"],  # type: ignore
            sa_timestamp=sa_timestamp,
        )
    except NotRecognizedSolidityFuncError:
        ...
    except InvalidTxError as e:
        logger.error(f"Invalid tx {tx}, error: {e}")
    except web3.exceptions.TransactionNotFound as e:
        logger.error(f"transaction not found {tx_hash} : {e}")
    except ValidationError as e:
        logger.error(f"Invalid transaction input, tx: {tx}, error {e}")
