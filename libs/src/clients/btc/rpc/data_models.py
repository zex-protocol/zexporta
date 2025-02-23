from pydantic import BaseModel

from clients.custom_types import Value


class AddressDetails(BaseModel):
    page: int | None = None
    totalPages: int | None = None
    itemsOnPage: int | None = None
    address: str
    balance: int
    totalReceived: int
    totalSent: int
    unconfirmedBalance: int | None = None
    unconfirmedTxs: int | None = None
    txs: int | None = None
    txids: list[str] | None = None


# Model for Unspent (Unspent Transaction Outputs)
class Unspent(BaseModel):
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
    value: Value | None = None
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
    blockHash: str | None
    blockHeight: int | None
    confirmations: int
    blockTime: int | None
    value: Value
    valueIn: Value
    fees: Value


# Response for getting block by identifier (including multiple pages)
class Block(BaseModel):
    page: int | None = None
    totalPages: int | None = None
    itemsOnPage: int | None = None
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
