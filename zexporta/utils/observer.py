import logging
from typing import Any, Callable, Coroutine

import web3.exceptions
from eth_typing import HexStr
from pydantic import BaseModel, ConfigDict
from web3 import AsyncWeb3

from zexporta.custom_types import (
    BlockNumber,
    ChainSymbol,
    ChecksumAddress,
    Deposit,
    DepositStatus,
    EVMConfig,
    Transfer,
    UserId,
)
from zexporta.db.token import get_decimals, insert_token
from zexporta.utils.logger import ChainLoggerAdapter

from .web3 import filter_blocks
from .web3 import get_token_decimals as w3_get_token_decimals

logger = logging.getLogger(__name__)


def get_block_batches(
    from_block: BlockNumber | int,
    to_block: BlockNumber | int,
    *,
    batch_size: int = 5,
) -> list[tuple[BlockNumber, ...]]:
    block_batches = [
        tuple(BlockNumber(j) for j in range(i, min(to_block + 1, i + batch_size)))
        for i in range(from_block, to_block + 1, batch_size)
    ]
    return block_batches


class Observer(BaseModel):
    model_config: ConfigDict = {"arbitrary_types_allowed": True}
    chain: EVMConfig
    w3: AsyncWeb3

    async def observe(
        self,
        from_block: BlockNumber | int,
        to_block: BlockNumber | int,
        accepted_addresses: dict[ChecksumAddress, UserId],
        extract_block_logic: Callable[..., Coroutine[Any, Any, list[Transfer]]],
        *,
        batch_size=5,
        max_delay_per_block_batch: int | float = 10,
        logger: logging.Logger | ChainLoggerAdapter = logger,
        **kwargs,
    ) -> list[Deposit]:
        result = []
        block_batches = get_block_batches(from_block, to_block, batch_size=batch_size)
        for blocks_number in block_batches:
            logger.info(f"batch_blocks: {blocks_number}")
            transfers = await filter_blocks(
                self.w3,
                blocks_number,
                extract_block_logic,
                chain_symbol=self.chain.chain_symbol,
                max_delay_per_block_batch=max_delay_per_block_batch,
                logger=logger,
                **kwargs,
            )
            accepted_deposits = await get_accepted_deposits(
                self.w3, self.chain, transfers, accepted_addresses
            )
            result.extend(accepted_deposits)
        return result


async def get_token_decimals(
    w3: AsyncWeb3, chain_symbol: ChainSymbol, token_address: ChecksumAddress
) -> int:
    decimals = await get_decimals(chain_symbol, token_address)
    if decimals is None:
        decimals = await w3_get_token_decimals(w3, token_address)
        await insert_token(chain_symbol, token_address, decimals)
    return decimals


async def get_accepted_deposits(
    w3: AsyncWeb3,
    chain: EVMConfig,
    transfers: list[Transfer],
    accepted_addresses: dict[ChecksumAddress, UserId],
    deposit_status: DepositStatus = DepositStatus.PENDING,
) -> list[Deposit]:
    result = []
    for transfer in transfers:
        if (user_id := accepted_addresses.get(transfer.to)) is not None:
            decimals = await get_token_decimals(w3, chain.chain_symbol, transfer.token)
            try:
                receipt = await w3.eth.get_transaction_receipt(HexStr(transfer.tx_hash))
                if receipt["status"] == 1:
                    result.append(
                        Deposit(
                            user_id=user_id,
                            decimals=decimals,
                            **transfer.model_dump(mode="json"),
                            status=deposit_status,
                        )
                    )
            except web3.exceptions.TransactionNotFound as e:
                logger.error(f"TransactionNotFound: {e}")
    return result
