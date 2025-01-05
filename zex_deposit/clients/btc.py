from typing import Dict, Optional

import httpx

from zex_deposit.custom_types import ChainConfig


class BTCAsyncClient:
    def __init__(self, base_url: str, indexer_url: str):
        self.base_url = base_url
        self.block_book_base_url = indexer_url

    async def _request(
        self,
        method: str = "GET",
        url: str = "",
        params: Dict = None,
        data: Dict = None,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, params=params, data=data, timeout=15
            )
            response.raise_for_status()
            return response.json()

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
        self, address: str, details: Optional[str] = "txids"
    ) -> dict:
        url = f"{self.block_book_base_url}api/v2/address/{address}"
        params = {"details": details}
        return await self._request("GET", url, params=params)

    async def get_utxo(self, address: str, confirmed: bool = True) -> dict:
        url = f"{self.block_book_base_url}api/v2/utxo/{address}"
        params = {"confirmed": str(confirmed).lower()}
        return await self._request("GET", url, params=params)

    async def get_block_by_hash(self, block_hash: int) -> dict:
        url = f"{self.block_book_base_url}api/v2/block/{block_hash}"
        return await self._request("GET", url)

    async def send_tx(self, hex_tx_data: str) -> dict:
        url = f"{self.block_book_base_url}api/v2/sendtx/{hex_tx_data}"
        return await self._request("GET", url)

    async def get_latest_block(self) -> dict:
        number = await self.get_latest_block_number()
        return await self.get_block_by_number(number)

    async def get_latest_block_number(self) -> int:
        url = f"{self.base_url}"
        data = {"id": "test", "method": "getblockchaininfo", "params": []}
        resp = await self._request("POST", url, data=data)
        return resp and resp["result"]["blocks"]


_btc = None


def get_btc_async_client(chain: ChainConfig) -> BTCAsyncClient:
    global _btc
    if _btc is None:
        _btc = BTCAsyncClient(
            base_url=chain.private_rpc, indexer_url=chain.private_indexer_rpc
        )
    return _btc
