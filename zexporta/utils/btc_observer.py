import asyncio
import logging
from typing import Callable, Dict

from pydantic import BaseModel

from zexporta.clients import BTCAsyncClient
from zexporta.custom_types import (
    BlockNumber,
    BTCConfig,
    RawTransfer,
    UserId,
    UserTransfer,
)
from zexporta.utils.logger import ChainLoggerAdapter

logger = logging.getLogger(__name__)


class BTCObserver(BaseModel):
    chain: BTCConfig
    btc: BTCAsyncClient

    async def get_block_batches(
        self, from_block: int, to_block: int, block_sleep: int
    ) -> list[Dict]:
        block_batches = []
        for block_number in range(from_block, to_block + 1):
            block = await self.btc.get_block_by_identifier(block_number)
            block_batches.append(block)
            await asyncio.sleep(block_sleep)
        return block_batches

    async def get_latest_block_number(self):
        return await self.btc.get_latest_block_number()

    async def observe(
        self,
        from_block: BlockNumber | int,
        to_block: BlockNumber | int,
        accepted_addresses: dict[str, UserId],
        extract_block_logic: Callable,
        *,
        batch_size=5,
        max_delay_per_block_batch: int | float = 10,
        logger: logging.Logger | ChainLoggerAdapter = logger,
        **kwargs,
    ) -> list[UserTransfer]:
        result = []
        block_batches = await self.get_block_batches(
            from_block=from_block, to_block=to_block, block_sleep=self.chain.delay
        )
        for block in block_batches:
            logger.info(f"batch_blocks: {block}")
            transfers = extract_block_logic(from_block, block, self.chain.chain_id)
            accepted_transfers = await get_accepted_transfers(
                transfers, accepted_addresses
            )
            result.extend(accepted_transfers)
        return result


async def get_accepted_transfers(
    transfers: list[RawTransfer],
    accepted_addresses: dict[str, UserId],
) -> list[UserTransfer]:
    result = []
    for transfer in transfers:
        if (user_id := accepted_addresses.get(transfer.to)) is not None:
            result.append(
                UserTransfer(
                    user_id=user_id,
                    decimals=8,
                    **transfer.model_dump(mode="json"),
                )
            )
    return result
