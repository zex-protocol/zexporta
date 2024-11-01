import struct

from eth_typing import ChainId

from custom_types import UserTransfer, BlockNumber

DEPOSIT_OPERATION = "d"


def encode_zex_deposit(
    *,
    version: int,
    operation_type: str,
    users_transfers: list[UserTransfer],
    chain_id: ChainId,
    from_block: BlockNumber | int,
    to_block: BlockNumber | int,
) -> bytes:
    # Encode the header
    header = struct.pack(
        ">B1s3sQQH",  # > for big-endian, B for uint8, s for char[], Q for uint64, H for uint16
        version,
        operation_type.encode(),
        chain_id.name.lower().encode(),
        from_block,
        to_block,
        len(users_transfers),
    )

    # Encode each deposit
    deposit_data = b""
    for deposit in users_transfers:
        deposit_data += struct.pack(
            ">20s d I I",  # I for uint32, d for double, I for uint32, s for bytes
            deposit.token.encode(),  # must be token address
            deposit.value,
            deposit.block_timestamp,
            deposit.user_id,
        )

    # Combine header, deposits
    return header + deposit_data
