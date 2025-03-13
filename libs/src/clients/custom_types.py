from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Annotated, Any, Awaitable, Callable, ClassVar

from eth_typing import ChecksumAddress
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

type TxHash = str
type BlockNumber = int
type Address = str | ChecksumAddress
type URL = str
type Salt = int


def convert_int_to_str(value: int) -> str:
    return str(value)


type Value = Annotated[int, PlainSerializer(convert_int_to_str, when_used="json")]


class Transfer(BaseModel, ABC):
    model_config: ConfigDict = {"from_attributes": True}
    tx_hash: TxHash
    value: Value
    chain_symbol: str
    token: Address
    to: Address
    block_number: BlockNumber

    @abstractmethod
    def __eq__(self, value: Any) -> bool: ...

    @abstractmethod
    def __gt__(self, value: Any) -> bool: ...


class WithdrawStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESSFUL = "successful"
    REJECTED = "rejected"


class WithdrawRequest(BaseModel):
    model_config = {"extra": "ignore"}
    amount: Value
    recipient: Address
    tx_hash: TxHash | None = None
    status: WithdrawStatus = WithdrawStatus.PENDING
    chain_symbol: str
    nonce: int


class ChainConfig(BaseModel, ABC):
    vault_address: Address
    private_rpc: URL
    chain_symbol: str
    finalize_block_count: int | None = Field(default=15)
    delay: int | float = Field(default=3)
    batch_block_size: int = Field(default=5)
    transfer_class: ClassVar[type[Transfer]]
    deposit_finalizer_middleware: list[Callable[..., Awaitable[Any]]] | None = None  # Supports async functions
    withdraw_request_type: ClassVar[type[WithdrawRequest]]
