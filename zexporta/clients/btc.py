from typing import Any

import httpx
from pydantic import BaseModel

from zexporta.custom_types import BTCConfig


# Model for Address Details
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
    vout: int
    value: str | int
    height: int
    confirmations: int
    coinbase: bool | None = None


# Common Model for all Transaction outputs (vout)
class Vout(BaseModel):
    value: int | float
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
    value: int | float
    valueIn: int | float
    fees: int | float


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


class BTCClientError(Exception):
    """Base exception for BTCAsyncClient errors."""


class BTCRequestError(BTCClientError):
    """Exception raised for errors during HTTP requests."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BTCConnectionError(BTCClientError):
    """Exception raised for connection-related errors."""


class BTCTimeoutError(BTCClientError):
    """Exception raised when a request times out."""


class BTCResponseError(BTCClientError):
    """Exception raised for invalid or unexpected responses."""


class BTCAsyncClient:
    def __init__(
        self,
        base_url: str = "https://rpc.ankr.com/btc",
        indexer_url: str = "https://rpc.ankr.com/http/btc_blockbook",
    ):
        self.base_url = base_url
        self.block_book_base_url = indexer_url
        self.client = httpx.AsyncClient()

    async def _request(
        self,
        method: str = "GET",
        url: str = "",
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: Any | None = None,
        json_data: Any | None = None,  # Add json_data parameter
    ) -> dict:
        try:
            # Choose between data and json based on the request
            request_kwargs = {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "timeout": 15,
            }
            if json_data is not None:
                request_kwargs["json"] = json_data
            elif data is not None:
                request_kwargs["data"] = data

            response = await self.client.request(**request_kwargs)
            response.raise_for_status()
            resp = response.json()

            if isinstance(resp, dict) and resp.get("error"):
                raise BTCRequestError(f"Ankr error occurred: {resp.get('error')}")
            return resp
        except httpx.HTTPStatusError as http_err:
            # Raised for non-2xx responses
            raise BTCRequestError(
                f"HTTP error occurred: {http_err.response.status_code} {http_err.response.reason_phrase}",
                status_code=http_err.response.status_code,
            ) from http_err
        except httpx.ConnectError as conn_err:
            # Raised for connection-related errors
            raise BTCConnectionError(
                f"Connection error occurred: {conn_err}"
            ) from conn_err
        except httpx.TimeoutException as timeout_err:
            # Raised when a request times out
            raise BTCTimeoutError(f"Request timed out: {timeout_err}") from timeout_err
        except httpx.RequestError as req_err:
            # Base class for all other request-related errors
            raise BTCClientError(
                f"An error occurred while requesting {req_err.request.url!r}."
            ) from req_err
        except ValueError as json_err:
            # Raised if response.json() fails
            raise BTCResponseError(
                f"Failed to parse JSON response: {json_err}"
            ) from json_err

    async def get_tx_by_hash(self, tx_hash: str) -> Transaction:
        url = f"{self.block_book_base_url}/api/v2/tx/{tx_hash}"
        data = await self._request("GET", url)
        return Transaction.model_validate(data)

    async def get_address_details(
        self, address: str, details: str | None = "txids"
    ) -> AddressDetails:
        url = f"{self.block_book_base_url}/api/v2/address/{address}"
        params = {"details": details}
        data = await self._request("GET", url, params=params)
        return AddressDetails.model_validate(data)

    async def get_utxo(self, address: str, confirmed: bool = True) -> list[UTXO]:
        url = f"{self.block_book_base_url}/api/v2/utxo/{address}"
        params = {"confirmed": str(confirmed).lower()}
        data = await self._request("GET", url, params=params)
        return [UTXO.model_validate(i) for i in data]

    async def get_block_by_identifier(self, identifier) -> Block:
        page = 1
        all_txs = []  # List to store all transactions across pages
        while True:
            url = f"{self.block_book_base_url}/api/v2/block/{identifier}"
            params = {"page": page}
            response = await self._request("GET", url, params=params)
            data = response
            txs = response.get("txs", [])
            all_txs.extend(txs)  # Add the current page's txs to the overall list

            total_pages = response.get("totalPages", 1)
            if page >= total_pages:
                break  # Exit the loop if we've reached the last page

            page += 1  # Move to the next page
        data["txs"] = all_txs
        return Block.model_validate(data)

    async def send_tx(self, hex_tx_data: str) -> str | None:
        url = f"{self.block_book_base_url}/api/v2/sendtx/{hex_tx_data}"
        resp = await self._request("GET", url)
        return resp and resp["result"]

    async def get_latest_block(self) -> Block:
        number = await self.get_latest_block_number()
        return await self.get_block_by_identifier(number)

    async def get_latest_block_number(self) -> int | None:
        url = f"{self.base_url}"
        data = {"id": "test", "method": "getblockchaininfo", "params": []}
        headers = {
            "Content-Type": "application/json",
        }
        resp = await self._request("POST", url, headers=headers, json_data=data)
        return resp and resp["result"]["blocks"]


_btc = None


def get_btc_async_client(chain: BTCConfig) -> BTCAsyncClient:
    global _btc
    if _btc is None:
        _btc = BTCAsyncClient(
            base_url=chain.private_rpc, indexer_url=chain.private_indexer_rpc
        )
    return _btc
