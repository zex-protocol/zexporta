from clients.abstract import BaseClientError


class EVMClientError(BaseClientError):
    """Base exception for EVMAsyncClient errors."""


class EVMTransferNotFound(EVMClientError):
    """Exception raised for transfer not found"""


class EVMTransferNotValid(EVMClientError):
    """Exception raised for transfer not found"""


class EVMBlockNotFound(EVMClientError):
    """Exception raised for transfer not found"""
