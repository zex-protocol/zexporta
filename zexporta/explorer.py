from typing import Any, Callable, Coroutine

from clients import ChainAsyncClient, filter_blocks, get_async_client

from zexporta.custom_types import (
    Address,
    BlockNumber,
    ChainConfig,
    Deposit,
    DepositStatus,
    Timestamp,
    Transfer,
    UserId,
)
from zexporta.db.token import get_decimals, insert_token
from zexporta.utils.logger import ChainLoggerAdapter


def get_block_batches(
    from_block: BlockNumber,
    to_block: BlockNumber,
    *,
    batch_size: int = 5,
) -> list[tuple[BlockNumber, ...]]:
    block_batches = [
        tuple(j for j in range(i, min(to_block + 1, i + batch_size)))
        for i in range(from_block, to_block + 1, batch_size)
    ]
    return block_batches


async def explorer(
    chain: ChainConfig,
    from_block: BlockNumber,
    to_block: BlockNumber,
    accepted_addresses: dict[Address, UserId],
    extract_block_logic: Callable[..., Coroutine[Any, Any, list[Transfer]]],
    *,
    batch_size=5,
    max_delay_per_block_batch: int | float = 10,
    logger: ChainLoggerAdapter,
    **kwargs,
) -> list[Deposit]:
    result = []
    client = get_async_client(chain)
    block_batches = get_block_batches(from_block, to_block, batch_size=batch_size)
    for blocks_number in block_batches:
        logger.info(f"batch_blocks: {blocks_number}")
        transfers = await filter_blocks(
            blocks_number,
            extract_block_logic,
            max_delay_per_block_batch=max_delay_per_block_batch,
            logger=logger,
            **kwargs,
        )
        accepted_deposits = await get_accepted_deposits(
            client,
            chain,
            transfers,
            accepted_addresses=accepted_addresses,
            logger=logger,
        )
        result.extend(accepted_deposits)
    return result


async def get_token_decimals(
    client: ChainAsyncClient, chain_symbol: str, token_address: Address
) -> int:
    decimals = await get_decimals(chain_symbol, token_address)
    if decimals is None:
        decimals = await client.get_token_decimals(token_address)
        await insert_token(chain_symbol, token_address, decimals)
    return decimals


async def get_accepted_deposits(
    client: ChainAsyncClient,
    chain: ChainConfig,
    transfers: list[Transfer],
    accepted_addresses: dict[Address, UserId],
    logger: ChainLoggerAdapter,
    *,
    sa_timestamp: Timestamp | None = None,
    deposit_status: DepositStatus = DepositStatus.PENDING,
) -> list[Deposit]:
    result = []
    for transfer in transfers:
        if (user_id := accepted_addresses.get(transfer.to)) is not None:
            decimals = await get_token_decimals(
                client, chain.chain_symbol, transfer.token
            )
            if await client.is_transaction_successful(transfer.tx_hash, logger):
                result.append(
                    Deposit(
                        user_id=user_id,
                        decimals=decimals,
                        transfer=chain.transfer_class.model_validate(transfer),
                        status=deposit_status,
                        sa_timestamp=sa_timestamp,
                    )
                )

    return result
