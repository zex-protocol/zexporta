from pydantic import BaseModel

from zexporta.custom_types import ChainSymbol, ChecksumAddress


class BotToken(BaseModel):
    symbol: str
    chain_symbol: ChainSymbol
    amount: int
    address: ChecksumAddress
    decimal: int
