import struct

from web3 import Web3

from zexporta.custom_types import (
    Deposit,
    EVMWithdrawRequest,
)

DEPOSIT_OPERATION = "d"


def encode_zex_deposit(
    *,
    version: int,
    operation_type: str,
    deposits: list[Deposit],
    chain_symbol: str,
) -> bytes:
    # Encode the header
    header = struct.pack(
        ">B1s3sH",  # > for big-endian, B for uint8, s for char[], Q for uint64, H for uint16
        version,
        operation_type.encode(),
        chain_symbol.lower().encode(),
        len(deposits),
    )

    # Encode each deposit
    deposit_data = b""
    for deposit in deposits:
        deposit_data += struct.pack(
            ">66s 42s 32s B I Q B",  # I for uint32, d for double, I for uint32, s for bytes
            deposit.transfer.tx_hash.encode(),
            deposit.transfer.token.encode(),  # must be token address
            deposit.transfer.value.to_bytes(32, "big"),
            deposit.decimals,
            deposit.sa_timestamp,
            deposit.user_id,
            0,
        )

    # Combine header, deposits
    return header + deposit_data


def get_evm_withdraw_hash(withdraw_request: EVMWithdrawRequest):
    return (
        Web3.solidity_keccak(
            ["address", "address", "uint256", "uint256", "uint256"],
            [
                withdraw_request.recipient,
                withdraw_request.token_address,
                withdraw_request.amount,
                withdraw_request.nonce,
                withdraw_request.chain_id,
            ],
        )
        .hex()
        .replace("0x", "")
    )
