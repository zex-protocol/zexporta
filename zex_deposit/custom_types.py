from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, Field, computed_field
from eth_typing import URI, BlockNumber, ChainId, ChecksumAddress

Value: TypeAlias = int
Timestamp: TypeAlias = int | float
UserId: TypeAlias = int
TxHash: TypeAlias = str


class ChainConfig(BaseModel):
    private_rpc: URI | str
    chain_id: ChainId
    from_block: BlockNumber | int
    symbol: str
    finalize_block_count: int | None = Field(default=None)


class TransferStatus(Enum):
    PENDING = 1
    FINALIZED = 2
    VERIFIED = 3
    REORG = 4
    REJECTED = 5


class Token(BaseModel):
    token_address: ChecksumAddress
    decimals: int

    class Config:
        use_enum_values = True


class RawTransfer(BaseModel):
    tx_hash: TxHash
    status: TransferStatus
    chain_id: ChainId
    value: Value
    token: ChecksumAddress
    to: ChecksumAddress
    block_timestamp: Timestamp
    block_number: BlockNumber

    class Config:
        use_enum_values = True
        validate_default = True


class UserTransfer(RawTransfer):
    user_id: UserId
    decimals: int

    class Config:
        use_enum_values = True
        validate_default = True

    def __eq__(self, value: "UserTransfer") -> bool:
        return self.tx_hash == value.tx_hash

    def __gt__(self, value: "UserTransfer") -> bool:
        return self.tx_hash > value.tx_hash


class UserAddress(BaseModel):
    user_id: UserId
    address: ChecksumAddress
    is_active: bool = Field(default=True)
