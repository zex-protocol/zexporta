from enum import StrEnum
from typing import Any

from eth_typing import URI, BlockNumber, ChainId, ChecksumAddress
from pydantic import BaseModel, Field

type Value = int
type Timestamp = int | float
type UserId = int
type TxHash = str


class EnvEnum(StrEnum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


class ChainConfig(BaseModel):
    private_rpc: URI | str
    chain_id: ChainId
    symbol: str
    poa: bool = Field(default=False)
    finalize_block_count: int = Field(default=15)
    delay: int | float = Field(default=3)
    batch_block_size: int = Field(default=5)
    vault_address: ChecksumAddress


class DepositStatus(StrEnum):
    PENDING = "pending"
    FINALIZED = "finalized"
    VERIFIED = "verified"
    SUCCESSFUL = "successful"
    REORG = "reorg"
    REJECTED = "rejected"


class WithdrawStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    REJECTED = "rejected"


class Token(BaseModel):
    model_config = {"extra": "ignore"}
    token_address: ChecksumAddress
    decimals: int


class Transfer(BaseModel):
    tx_hash: TxHash
    chain_id: ChainId
    value: Value
    token: ChecksumAddress
    to: ChecksumAddress
    sa_timestamp: Timestamp | None = None
    block_number: BlockNumber

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, Transfer):
            return self.tx_hash == value.tx_hash
        return NotImplemented

    def __gt__(self, value: Any) -> bool:
        if isinstance(value, Transfer):
            return self.tx_hash > value.tx_hash
        return NotImplemented


class SaDepositSchema(BaseModel):
    txs_hash: list[TxHash]
    timestamp: Timestamp
    chain_id: ChainId
    finalized_block_number: BlockNumber


class Deposit(Transfer):
    user_id: UserId
    decimals: int
    status: DepositStatus


class UserAddress(BaseModel):
    user_id: UserId
    address: ChecksumAddress
    is_active: bool = Field(default=True)


class WithdrawRequest(BaseModel):
    model_config = {"extra": "ignore"}
    token_address: ChecksumAddress
    amount: int
    recipient: ChecksumAddress
    nonce: int
    chain_id: ChainId
    tx_hash: TxHash | None = None
    status: WithdrawStatus = WithdrawStatus.PENDING


class ZexUserAsset(BaseModel):
    asset: str
    free: str
    locked: str
    freeze: str
    withdrawing: str
