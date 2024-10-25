from datetime import datetime
from enum import Enum, auto

from pydantic import BaseModel, Field
from eth_typing import BlockNumber, ChecksumAddress, ChainId

from custom_types import TxHash, Value, Timestamp, UserId


class TransferStatus(Enum):
    PENDING = auto()
    FINALIZED = auto()
    VERIFIED = auto()
    REORG = auto()
    REJECTED = auto()


class Transfer(BaseModel):
    tx_hash: TxHash
    status: TransferStatus
    chain_id: ChainId
    value: Value
    token: ChecksumAddress
    to: ChecksumAddress
    observed_at: Timestamp = Field(default_factory=lambda: datetime.now().timestamp())
    block_number: BlockNumber

    class Config:
        use_enum_values = True


class UserAddress(BaseModel):
    user_id: UserId
    address: ChecksumAddress
    is_active: bool = Field(default=True)
