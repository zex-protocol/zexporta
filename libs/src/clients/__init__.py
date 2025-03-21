import asyncio
import logging
import time
from functools import lru_cache
from typing import Any, Callable, Coroutine, Iterable

from .abstract import ChainAsyncClient
from .btc import BTCAsyncClient, BTCConfig, compute_btc_address, get_btc_async_client
from .custom_types import Address, BlockNumber, ChainConfig, Transfer, TxHash, WithdrawRequest
from .evm import (
    EVMAsyncClient,
    EVMConfig,
    compute_create2_address,
    get_evm_async_client,
)

__all__ = [
    "get_async_client",
    "get_compute_address_function",
    "filter_blocks",
    "BTCAsyncClient",
    "EVMAsyncClient",
    "BTCConfig",
    "EVMConfig",
    "compute_btc_address",
    "ChainConfig",
    "ChainAsyncClient",
    "WithdrawRequest",
    "Transfer",
    "WithdrawRequest",
]


# FIXME: We are using `lru_cache` instead of a self-implemented singleton;
# perhaps we should consider changing this in the future for better clarity.
@lru_cache
def get_async_client(chain: ChainConfig, logger: logging.Logger | logging.LoggerAdapter) -> ChainAsyncClient:
    match chain:
        case EVMConfig():
            return get_evm_async_client(chain, logger)
        case BTCConfig():
            return get_btc_async_client(chain, logger)
        case _:
            raise NotImplementedError()


@lru_cache
def get_compute_address_function(chain: ChainConfig) -> Callable[[int], Address]:
    match chain:
        case EVMConfig():
            return compute_create2_address
        case BTCConfig():
            return compute_btc_address
    raise NotImplementedError()


async def _filter_blocks[T: (Transfer, TxHash)](
    blocks: Iterable[BlockNumber],
    fn: Callable[..., Coroutine[Any, Any, list[T]]],
    **kwargs,
) -> list[T]:
    tasks = [asyncio.create_task(fn(i, **kwargs)) for i in blocks]
    result = []
    for task in tasks:
        result.extend(await task)
    return result


async def filter_blocks[T: (Transfer, TxHash)](
    blocks_number: Iterable[BlockNumber],
    fn: Callable[..., Coroutine[Any, Any, list[T]]],
    max_delay_per_block_batch: int | float = 5,
    **kwargs,
) -> list[T]:
    start = time.monotonic()
    result = await _filter_blocks(blocks_number, fn, **kwargs)
    end = time.monotonic()
    await asyncio.sleep(max(max_delay_per_block_batch - (end - start), 0))
    return result
