from typing import TypeAlias

from pydantic import BaseModel
from eth_typing import URI, ChainId

Value: TypeAlias = int
Timestamp: TypeAlias = int | float
UserId: TypeAlias = int
TxHash: TypeAlias = str


class ChainConfig(BaseModel):
    private_rpc: URI | str
    chain_id: ChainId
