import logging
from abc import ABC, abstractmethod

from clients.custom_types import (
    BlockNumber,
    ChainConfig,
    Transfer,
    TxHash,
)


class BaseClientError(Exception):
    """Base exception for ChainAsyncClient errors."""


class ChainAsyncClient[_ChainT: ChainConfig, _ClientT, _TransferT: Transfer, _AddressT](ABC):
    def __init__(self, chain: _ChainT, logger: logging.Logger | logging.LoggerAdapter):
        """Initialize with Chain chain configuration"""
        self.chain = chain
        self.logger = logger

    @property
    @abstractmethod
    def client(self) -> _ClientT:
        """Get or create an async client connection"""

    @abstractmethod
    async def get_transfer_by_tx_hash(self, tx_hash: TxHash) -> _TransferT | list[_TransferT]:
        """Retrieve transfer details by transaction hash"""

    @abstractmethod
    async def get_finalized_block_number(self) -> BlockNumber:
        """Get the latest finalized block number"""

    @abstractmethod
    async def get_token_decimals(self, token_address: _AddressT) -> int:
        """Get decimals for a token contract"""

    @abstractmethod
    async def is_transaction_successful(self, tx_hash: TxHash) -> bool:
        """Check if transaction was successful"""

    @abstractmethod
    async def get_block_tx_hash(self, block_number: BlockNumber, **kwargs) -> list[TxHash]:
        """Get all transaction hashes in a block"""

    @abstractmethod
    async def get_latest_block_number(self) -> BlockNumber:
        """Get latest block number"""

    @abstractmethod
    async def extract_transfer_from_block(
        self,
        block_number: BlockNumber,
        **kwargs,
    ) -> list[_TransferT]:
        """Get block transfers"""
