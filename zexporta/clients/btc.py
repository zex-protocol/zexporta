from typing import Any, Optional

import httpx

from zexporta.custom_types import BTCConfig


class BTCClientError(Exception):
    """Base exception for BTCAsyncClient errors."""

    pass


class BTCRequestError(BTCClientError):
    """Exception raised for errors during HTTP requests."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class BTCConnectionError(BTCClientError):
    """Exception raised for connection-related errors."""

    pass


class BTCTimeoutError(BTCClientError):
    """Exception raised when a request times out."""

    pass


class BTCResponseError(BTCClientError):
    """Exception raised for invalid or unexpected responses."""

    pass


class BTCAsyncClient:
    def __init__(self, base_url: str, indexer_url: str):
        self.base_url = base_url
        self.block_book_base_url = indexer_url
        self.client = httpx.AsyncClient()

    async def _request(
        self,
        method: str = "GET",
        url: str = "",
        params: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict:
        try:
            response = await self.client.request(
                method, url, params=params, data=data, timeout=15
            )
            response.raise_for_status()
            return response.json()
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

    async def get_block_by_number(self, number: int) -> dict:
        url = f"{self.block_book_base_url}api/v2/block-index/{number}"
        return await self._request("GET", url)

    async def get_tx_by_hash(self, tx_hash: str) -> dict:
        url = f"{self.block_book_base_url}api/v2/tx/{tx_hash}"
        return await self._request("GET", url)

    async def get_tx_specific(self, tx_hash: str) -> dict:
        url = f"{self.block_book_base_url}api/v2/tx-specific/{tx_hash}"
        return await self._request("GET", url)

    async def get_address_details(
        self, address: str, details: str | None = "txids"
    ) -> dict:
        url = f"{self.block_book_base_url}api/v2/address/{address}"
        params = {"details": details}
        return await self._request("GET", url, params=params)

    async def get_utxo(self, address: str, confirmed: bool = True) -> dict:
        url = f"{self.block_book_base_url}api/v2/utxo/{address}"
        params = {"confirmed": str(confirmed).lower()}
        return await self._request("GET", url, params=params)

    async def get_block_by_identifier(self, identifier) -> dict:
        url = f"{self.block_book_base_url}api/v2/block/{identifier}"
        return await self._request("GET", url)

    async def send_tx(self, hex_tx_data: str) -> dict:
        url = f"{self.block_book_base_url}api/v2/sendtx/{hex_tx_data}"
        resp = await self._request("GET", url)
        return resp and resp["result"]

    async def get_latest_block(self) -> dict:
        number = await self.get_latest_block_number()
        return await self.get_block_by_identifier(number)

    async def get_latest_block_number(self) -> int:
        url = f"{self.base_url}"
        data = {"id": "test", "method": "getblockchaininfo", "params": []}
        resp = await self._request("POST", url, data=data)
        return resp and resp["result"]["blocks"]


_btc = None


def get_btc_async_client(chain: BTCConfig) -> BTCAsyncClient:
    global _btc
    if _btc is None:
        _btc = BTCAsyncClient(
            base_url=chain.private_rpc, indexer_url=chain.private_indexer_rpc
        )
    return _btc
