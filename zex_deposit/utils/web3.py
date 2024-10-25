import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Iterable, TypeVar

from eth_typing import BlockNumber, ChecksumAddress, ChainId
from pydantic import BaseModel
from web3 import AsyncWeb3, AsyncHTTPProvider

from custom_types import ChainConfig, TxHash
from db.models import Transfer, TransferStatus
from utils.transfer_decoder import (
    decode_transfer_tx,
    NotRecognizedSolidityFuncError,
)

T = TypeVar("T")


class Observer(BaseModel):
    chain: ChainConfig

    async def get_block_batches(
        self,
        from_block: BlockNumber | int,
        to_block: BlockNumber | int,
        *,
        batch_size: int = 5,
    ) -> list[tuple[BlockNumber, ...]]:
        block_batches = [
            tuple(
                BlockNumber(j) for j in range(i, min(to_block + 1, i + batch_size + 1))
            )
            for i in range(from_block, to_block + 1, batch_size)
        ]
        return block_batches

    async def filter_valid_transfer(
        self, transfers: list[Transfer], valid_addresses: set[ChecksumAddress]
    ) -> tuple[Transfer, ...]:
        return tuple(filter(lambda transfer: transfer.to in valid_addresses, transfers))

    async def observe(
        self,
        w3: AsyncWeb3,
        from_block: BlockNumber | int,
        to_block: BlockNumber | int,
        valid_addresses: set[ChecksumAddress],
        extract_block_logic: Callable[..., Coroutine[Any, Any, list[Transfer]]],
        *,
        batch_size=5,
        max_delay_per_block_batch=10,
    ) -> list[Transfer]:
        result = []
        block_batches = await self.get_block_batches(
            from_block, to_block, batch_size=batch_size
        )
        for blocks_number in block_batches:
            transfers = await filter_blocks(
                w3,
                blocks_number,
                extract_block_logic,
                chain_id=self.chain.chain_id,
                max_delay_per_block_batch=max_delay_per_block_batch,
            )
            valid_transfers = await self.filter_valid_transfer(
                transfers, valid_addresses
            )
            result.append(valid_transfers)
        return result


async def async_web3_factory(chain: ChainConfig) -> AsyncWeb3:
    w3 = AsyncWeb3(AsyncHTTPProvider(chain.private_rpc))
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
    max_delay_per_block_batch=5,
    **kwargs,
) -> list[T]:
    start = time.time()
    result = await _filter_blocks(w3, blocks_number, fn, **kwargs)
    end = time.time()
    await asyncio.sleep(max(max_delay_per_block_batch - end - start, 0))
    return result


async def extract_transfer_from_block(
    w3: AsyncWeb3, block_number: BlockNumber, chain_id: ChainId, **kwargs
) -> list[Transfer]:
    logging.info(f"Observing block number {block_number} start")
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
                    status=TransferStatus.PENDING,
                    token=tx.to,
                )
            )
        except NotRecognizedSolidityFuncError as _:
            ...
    logging.info(f"Observing block number {block_number} end")
    return result


async def get_block_tx_hash(
    w3: AsyncWeb3, block_number: BlockNumber, **kwargs
) -> list[TxHash]:
    block = await w3.eth.get_block(block_number)
    return [tx_hash.hex() for tx_hash in block.transactions]  # type: ignore
