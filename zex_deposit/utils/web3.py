import asyncio
import time
from typing import Any, Callable, Coroutine, Iterable, TypeVar

from eth_typing import BlockNumber
from web3 import AsyncWeb3, AsyncHTTPProvider

from custom_types import ChainConfig, TxHash

T = TypeVar("T")


async def async_web3_factory(chain: ChainConfig) -> AsyncWeb3:
    w3 = AsyncWeb3(AsyncHTTPProvider(chain.private_rpc))
    return w3


async def get_block_tx_hash(
    w3: AsyncWeb3, block_number: BlockNumber, **kwargs
) -> list[TxHash]:
    block = await w3.eth.get_block(block_number)
    return [tx_hash.hex() for tx_hash in block.transactions]  # type: ignore


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
    max_delay_per_block_batch=5,
    **kwargs,
) -> list[T]:
    start = time.time()
    result = await _filter_blocks(w3, blocks_number, fn, **kwargs)
    end = time.time()
    await asyncio.sleep(max(max_delay_per_block_batch - end - start, 0))
    return result
