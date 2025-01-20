from pydantic import BaseModel

from zexporta.custom_types import ChainSymbol, ChecksumAddress


class MonitoringToken(BaseModel):
    symbol: str
    chain_symbol: ChainSymbol
    amount: int
    address: ChecksumAddress
    decimal: int
