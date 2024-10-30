import struct

from custom_types import BlockNumber, ChainConfig, TransferStatus, UserTransfer
from db.address import get_active_address, insert_new_adderss_to_db
from utils.web3 import (
    Observer,
    async_web3_factory,
    extract_transfer_from_block,
    get_finalized_block_number,
)


class NotFinalizedBlockError(Exception):
    "Raise when a block number is bigger then current finalized block"


async def get_users_transfers(
    chain: ChainConfig, from_block: BlockNumber | int, to_block: BlockNumber | int
):
    w3 = await async_web3_factory(chain=chain)
    finalized_block_number = await get_finalized_block_number(w3)
    if to_block > finalized_block_number:
        raise NotFinalizedBlockError(
            f"to_block: {to_block} is not finalized, finalized_block: {finalized_block_number}"
        )
    observer = Observer(chain=chain)
    await insert_new_adderss_to_db()
    accepted_addresses = await get_active_address()
    users_transfers = await observer.observe(
        w3,
        from_block=from_block,
        to_block=to_block,
        accepted_addresses=accepted_addresses,
        extract_block_logic=extract_transfer_from_block,
        transfer_status=TransferStatus.FINALIZED,
    )
    return sorted(users_transfers)


def encode_zex_transfers(
    *,
    version: int,
    operation_type: str,
    users_transfers: list[UserTransfer],
    chain: ChainConfig,
    from_block: BlockNumber | int,
    to_block: BlockNumber | int,
) -> bytes:
    # Encode the header
    header = struct.pack(
        ">B1s3sQQH",  # > for big-endian, B for uint8, s for char[], Q for uint64, H for uint16
        version,
        operation_type.encode(),
        chain.chain_id.name.lower().encode(),
        from_block,
        to_block,
        len(users_transfers),
    )

    # Encode each deposit
    deposit_data = b""
    for deposit in users_transfers:
        deposit_data += struct.pack(
            ">20s d I I",  # I for uint32, d for double, I for uint32, s for bytes
            deposit.token,  # must be token address
            deposit.value,
            deposit.observed_at,  # TODO: use deposit time instead
            deposit.user_id,
        )

    # Combine header, deposits
    return header + deposit_data
