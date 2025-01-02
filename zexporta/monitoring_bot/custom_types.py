from pydantic import BaseModel

from zexporta.custom_types import ChainId, ChecksumAddress


class MonitoringToke(BaseModel):
    symbol: str
    chain_id: ChainId
    amount: int
    address: ChecksumAddress
    decimal: int
