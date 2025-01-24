from abc import ABC, abstractmethod

from zexporta.custom_types import (
    Address,
    BlockNumber,
    ChainConfig,
    Transfer,
    TxHash,
)
from zexporta.utils.logger import ChainLoggerAdapter


class BaseClientError(Exception):
    """Base exception for ChainAsyncClient errors."""


class ChainAsyncClient(ABC):
    @abstractmethod
    def __init__(self, chain: ChainConfig):
        """Initialize with Chain chain configuration"""
        self.chain = chain

    @abstractmethod
    async def client(self):
        """Get or create an async client connection"""

    @abstractmethod
    async def get_transfer_by_tx_hash(
        self, tx_hash: TxHash
    ) -> Transfer | list[Transfer]:
        """Retrieve transfer details by transaction hash"""

    @abstractmethod
    async def get_finalized_block_number(self) -> BlockNumber:
        """Get the latest finalized block number"""

    @abstractmethod
    async def get_token_decimals(self, token_address: Address) -> int:
        """Get decimals for a token contract"""

    @abstractmethod
    async def is_transaction_successful(
        self, tx_hash: TxHash, logger: ChainLoggerAdapter
    ) -> bool:
        """Check if transaction was successful"""

    @abstractmethod
    async def get_block_tx_hash(
        self, block_number: BlockNumber, **kwargs
    ) -> list[TxHash]:
        """Get all transaction hashes in a block"""

    @abstractmethod
    async def get_latest_block_number(self) -> BlockNumber:
        """Get latest block number"""

    @abstractmethod
    async def extract_transfer_from_block(
        self,
        block_number: BlockNumber,
        logger: ChainLoggerAdapter,
        **kwargs,
    ) -> list[Transfer]:
        """Get block transfers"""
