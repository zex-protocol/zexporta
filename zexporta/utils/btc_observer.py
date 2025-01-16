import asyncio
import logging
from typing import Callable

from pydantic import BaseModel, ConfigDict

from zexporta.clients import BTCAsyncClient
from zexporta.clients.btc import Block
from zexporta.custom_types import (
    BlockNumber,
    BTCConfig,
    Deposit,
    DepositStatus,
    Transfer,
    UserId,
)
from zexporta.utils.logger import ChainLoggerAdapter

logger = logging.getLogger(__name__)


class BTCObserver(BaseModel):
    model_config: ConfigDict = {"arbitrary_types_allowed": True}
    chain: BTCConfig
    client: BTCAsyncClient

    async def get_block_batches(
        self, from_block: int, to_block: int, block_sleep: int
    ) -> list[Block]:
        block_batches = []
        for block_number in range(from_block, to_block + 1):
            block = await self.client.get_block_by_identifier(block_number)
            block_batches.append(block)
            await asyncio.sleep(block_sleep)
        return block_batches

    async def get_latest_block_number(self) -> int | None:
        return await self.client.get_latest_block_number()

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
    ) -> list[Deposit] | None:
        try:
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

        except Exception as e:
            logger.error(e)
            return None


async def get_accepted_transfers(
    transfers: list[Transfer],
    accepted_addresses: dict[str, UserId],
) -> list[Deposit]:
    result = []
    for transfer in transfers:
        if (user_id := accepted_addresses.get(transfer.to)) is not None:
            result.append(
                Deposit(
                    user_id=user_id,
                    decimals=8,
                    status=DepositStatus.PENDING,
                    **transfer.model_dump(mode="json"),
                )
            )
    return result
