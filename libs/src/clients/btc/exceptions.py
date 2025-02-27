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
