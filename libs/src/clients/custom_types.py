from abc import ABC, abstractmethod
from typing import Annotated, Any, Hashable

from pydantic import BaseModel, Field, PlainSerializer

type TxHash = str
type BlockNumber = int
type URL = str
type Address = Any


def convert_int_to_str(value: int) -> str:
    return str(value)


type Value = Annotated[int, PlainSerializer(convert_int_to_str, when_used="json")]


class Transfer[_AddressT](BaseModel, ABC):
    model_config = {"from_attributes": True}
    tx_hash: TxHash
    value: Value
    chain_symbol: str
    token: _AddressT
    to: _AddressT
    block_number: BlockNumber

    @abstractmethod
    def __eq__(self, value: Any) -> bool: ...

    @abstractmethod
    def __gt__(self, value: Any) -> bool: ...


class ChainConfig[_TransferT: Transfer](BaseModel, Hashable, ABC):
    model_config = {"frozen": True}

    private_rpc: URL
    chain_symbol: str
    finalize_block_count: int | None = Field(default=15)
    delay: int | float = Field(default=3)
    batch_block_size: int = Field(default=5)
    transfer_class: type[_TransferT]
