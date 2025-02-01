from enum import StrEnum
from typing import Any

from clients.btc.custom_types import BTCConfig, BTCTransfer
from clients.custom_types import (
    Address,
    BlockNumber,
    ChainConfig,
    Transfer,
    TxHash,
    Value,
)
from clients.evm.custom_types import ChainId, ChecksumAddress, EVMConfig, EVMTransfer
from pydantic import BaseModel, Field


def convert_int_to_str(value: int) -> str:
    return str(value)


type Timestamp = int
type UserId = int


class EnvEnum(StrEnum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"


class ChainSymbol(StrEnum):
    SEP = "SEP"
    BST = "BST"
    HOL = "HOL"
    POL = "POL"
    BSC = "BSC"
    OPT = "OPT"
    BTC = "BTC"


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


class SaDepositSchema(BaseModel):
    txs_hash: list[TxHash]
    timestamp: Timestamp
    chain_symbol: str
    finalized_block_number: BlockNumber


class Deposit[T: (Transfer, EVMTransfer, BTCTransfer)](BaseModel):
    user_id: UserId
    decimals: int
    status: DepositStatus
    sa_timestamp: Timestamp | None = None
    transfer: T

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, Deposit):
            return self.transfer == value.transfer
        return NotImplemented

    def __gt__(self, value: Any) -> bool:
        if isinstance(value, Deposit):
            return self.transfer > value.transfer
        return NotImplemented


class UserAddress(BaseModel):
    user_id: UserId
    address: Address
    is_active: bool = Field(default=True)


class EVMWithdrawRequest(BaseModel):
    model_config = {"extra": "ignore"}
    token_address: ChecksumAddress
    amount: Value
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


__all__ = [
    "ZexUserAsset",
    "EVMWithdrawRequest",
    "UserAddress",
    "Deposit",
    "SaDepositSchema",
    "Token",
    "WithdrawStatus",
    "DepositStatus",
    "ChainSymbol",
    "EnvEnum",
    "BTCConfig",
    "EVMConfig",
    "ChainConfig",
    "TxHash",
    "Value",
    "ChecksumAddress",
    "Timestamp",
    "UserId",
    "BlockNumber",
    "Address",
    "EVMTransfer",
    "BTCTransfer",
    "Transfer",
]
