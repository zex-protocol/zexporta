from decimal import Decimal
from typing import Any

import httpx

from clients.btc.exceptions import (
    BTCClientError,
    BTCConnectionError,
    BTCRequestError,
    BTCResponseError,
    BTCTimeoutError,
)
from clients.btc.rpc.data_models import AddressDetails, Block, Transaction, Unspent
from clients.custom_types import URL, BlockNumber, TxHash


class BTCAnkrAsyncClient:
    def __init__(
        self,
        base_url: URL,
        indexer_url: URL,
    ):
        self.base_url = base_url
        self.block_book_base_url = indexer_url
        self._client = httpx.AsyncClient()

    @property
    def client(self):
        if self._client.is_closed:
            self._client = httpx.AsyncClient()
        return self._client

    async def _request(
        self,
        method: str = "GET",
        url: str = "",
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        json_data: Any = None,  # Add json_data parameter
    ) -> dict[str, Any]:
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
                f"HTTP error occurred: {http_err.response.status_code} {http_err.response.text}",
                status_code=http_err.response.status_code,
            ) from http_err
        except httpx.ConnectError as conn_err:
            # Raised for connection-related errors
            raise BTCConnectionError(f"Connection error occurred: {conn_err}") from conn_err
        except httpx.TimeoutException as timeout_err:
            # Raised when a request times out
            raise BTCTimeoutError(f"Request timed out: {timeout_err}") from timeout_err
        except httpx.RequestError as req_err:
            # Base class for all other request-related errors
            raise BTCClientError(f"An error occurred while requesting {req_err.request.url!r}.") from req_err
        except ValueError as json_err:
            # Raised if response.json() fails
            raise BTCResponseError(f"Failed to parse JSON response: {json_err}") from json_err

    async def get_tx_by_hash(self, tx_hash: TxHash) -> Transaction:
        url = f"{self.block_book_base_url}/api/v2/tx/{tx_hash}"
        data = await self._request("GET", url)
        return Transaction.model_validate(data)

    async def get_address_details(self, address: str, details: str | None = "txids") -> AddressDetails:
        url = f"{self.block_book_base_url}/api/v2/address/{address}"
        params = {"details": details}
        data = await self._request("GET", url, params=params)
        return AddressDetails.model_validate(data)

    async def get_utxo(self, address: str, confirmed: bool = True) -> list[Unspent]:
        url = f"{self.block_book_base_url}/api/v2/utxo/{address}"
        params = {"confirmed": str(confirmed).lower()}
        data = await self._request("GET", url, params=params)
        return [Unspent.model_validate(i) for i in data]

    async def get_block_by_identifier(self, identifier: str | int) -> Block:
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
        return resp and resp["result"]  # type: ignore

    async def get_latest_block(self) -> Block:
        number = await self.get_latest_block_number()
        return await self.get_block_by_identifier(number)

    async def get_latest_block_number(self) -> BlockNumber:
        url = f"{self.base_url}"
        data = {"id": "test", "method": "getblockchaininfo", "params": []}
        headers = {
            "Content-Type": "application/json",
        }
        resp = await self._request("POST", url, headers=headers, json_data=data)
        return resp["result"]["blocks"]  # type: ignore

    async def get_fee_per_byte(self) -> int | Decimal:
        url = f"{self.base_url}"
        data = {"id": "test", "method": "estimatesmartfee", "params": [6]}
        headers = {
            "Content-Type": "application/json",
        }
        resp = await self._request("POST", url, headers=headers, json_data=data)
        fee_rate = resp and resp["result"] and Decimal(resp["result"]["feerate"]) * (10 ^ 8)
        if isinstance(fee_rate, Decimal):
            return fee_rate
        else:
            raise BTCResponseError("Cant get fee rate")
