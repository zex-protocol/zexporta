# Model for Address Details
from typing import Any, ClassVar

from pydantic import BaseModel

from clients.custom_types import URL, ChainConfig, Transfer, Value

type Address = str


class AddressDetails(BaseModel):
    page: int
    totalPages: int
    itemsOnPage: int
    address: str
    balance: int
    totalReceived: int
    totalSent: int
    unconfirmedBalance: int
    unconfirmedTxs: int
    txs: int
    txids: list[str]


# Model for UTXO (Unspent Transaction Outputs)
class UTXO(BaseModel):
    txid: str
    vout: Value
    value: Value
    height: int
    confirmations: int
    coinbase: bool | None = None


# Common Model for all Transaction outputs (vout)
class Vout(BaseModel):
    value: Value
    n: int
    addresses: list[str] | None = None
    isAddress: bool
    hex: str | None = None
    scriptPubKey: dict | None = None


# Common Model for all Transaction inputs (vin)
class Vin(BaseModel):
    sequence: int | None = None
    n: int | None = None
    isAddress: bool | None = None
    coinbase: str | None = None
    txinwitness: list[str] | None = None


# Model for Transaction Details
class Transaction(BaseModel):
    txid: str
    vin: list[Vin]
    vout: list[Vout]
    blockHash: str
    blockHeight: int
    confirmations: int
    blockTime: int
    vsize: int
    value: Value
    valueIn: Value
    fees: Value


# Response for getting block by identifier (including multiple pages)
class Block(BaseModel):
    page: int
    totalPages: int
    itemsOnPage: int
    hash: str
    previousBlockHash: str
    nextBlockHash: str | None = None
    height: int
    confirmations: int
    size: int
    time: int
    version: int
    merkleRoot: str
    nonce: str
    difficulty: str
    bits: str
    txCount: int
    txs: list[Transaction] | None = None


class BTCTransfer(Transfer):
    index: int

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, BTCTransfer):
            return self.tx_hash == value.tx_hash and self.index == value.index
        return NotImplemented

    def __gt__(self, value: Any) -> bool:
        if isinstance(value, BTCTransfer):
            return self.tx_hash > value.tx_hash or (
                self.tx_hash == value.tx_hash and self.index > value.index
            )
        return NotImplemented


class BTCConfig(ChainConfig):
    private_indexer_rpc: URL
    transfer_class: ClassVar[type[BTCTransfer]] = BTCTransfer
