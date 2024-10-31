from datetime import datetime
from enum import Enum, auto
from typing import TypeAlias

from pydantic import BaseModel, Field
from eth_typing import URI, BlockNumber, ChainId, ChecksumAddress

Value: TypeAlias = int
Timestamp: TypeAlias = int | float
UserId: TypeAlias = int
TxHash: TypeAlias = str


class ChainConfig(BaseModel):
    private_rpc: URI | str
    chain_id: ChainId


class TransferStatus(Enum):
    PENDING = auto()
    FINALIZED = auto()
    VERIFIED = auto()
    REORG = auto()
    REJECTED = auto()


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


class UserTransfer(RawTransfer):
    user_id: UserId

    class Config:
        use_enum_values = True

    def __eq__(self, value: "UserTransfer") -> bool:
        return self.tx_hash == value.tx_hash

    def __gt__(self, value: "UserTransfer") -> bool:
        return self.tx_hash > value.tx_hash


class UserAddress(BaseModel):
    user_id: UserId
    address: ChecksumAddress
    is_active: bool = Field(default=True)
