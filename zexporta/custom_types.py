from abc import ABC
from enum import StrEnum
from typing import Annotated, Any

from eth_typing import BlockNumber as EvmBlockNumber
from eth_typing import ChainId, ChecksumAddress
from pydantic import BaseModel, Field, PlainSerializer


def convert_int_to_str(value: int) -> str:
    return str(value)


type Value = Annotated[int, PlainSerializer(convert_int_to_str, when_used="json")]
type Timestamp = int | float
type UserId = int
type TxHash = str
type Address = str | ChecksumAddress
type BlockNumber = EvmBlockNumber | int
type URL = str


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


class ChainConfig(BaseModel, ABC):
    private_rpc: URL
    chain_symbol: ChainSymbol
    finalize_block_count: int | None = Field(default=15)
    delay: int | float = Field(default=3)
    batch_block_size: int = Field(default=5)


class EVMConfig(ChainConfig):
    chain_id: ChainId
    poa: bool = Field(default=False)
    vault_address: ChecksumAddress


class BTCConfig(ChainConfig):
    private_indexer_rpc: URL


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
    value: Value
    chain_symbol: ChainSymbol
    token: Address
    to: Address
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


class BTCTransfer(BaseModel):
    tx_hash: TxHash
    value: Value
    chain_symbol: ChainSymbol
    token: Address
    to: Address
    sa_timestamp: Timestamp | None = None
    block_number: BlockNumber
    index: int

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
    chain_symbol: ChainSymbol
    finalized_block_number: BlockNumber


class Deposit(Transfer):
    user_id: UserId
    decimals: int
    status: DepositStatus


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
