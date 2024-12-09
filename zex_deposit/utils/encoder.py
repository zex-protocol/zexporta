import struct

from web3 import Web3

from zex_deposit.custom_types import (
    ChainConfig,
    UserTransfer,
    WithdrawRequest,
)

DEPOSIT_OPERATION = "d"


def encode_zex_deposit(
    *,
    version: int,
    operation_type: str,
    users_transfers: list[UserTransfer],
    chain: ChainConfig,
) -> bytes:
    # Encode the header
    header = struct.pack(
        ">B1s3sH",  # > for big-endian, B for uint8, s for char[], Q for uint64, H for uint16
        version,
        operation_type.encode(),
        chain.symbol.lower().encode(),
        len(users_transfers),
    )

    # Encode each deposit
    deposit_data = b""
    for deposit in users_transfers:
        deposit_data += struct.pack(
            ">66s 42s 32s B I Q B",  # I for uint32, d for double, I for uint32, s for bytes
            deposit.tx_hash.encode(),
            deposit.token.encode(),  # must be token address
            deposit.value.to_bytes(32, "big"),
            deposit.decimals,
            deposit.block_timestamp,
            deposit.user_id,
            0,
        )

    # Combine header, deposits
    return header + deposit_data


def get_withdraw_hash(withdraw_request: WithdrawRequest, chain: ChainConfig):
    return (
        Web3.solidity_keccak(
            ["address", "address", "uint256", "uint256", "uint256"],
            [
                withdraw_request.recipient,
                withdraw_request.token_address,
                withdraw_request.amount,
                withdraw_request.nonce,
                chain.chain_id,
            ],
        )
        .hex()
        .replace("0x", "")
    )
