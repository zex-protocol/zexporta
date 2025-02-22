from typing import Any

from clients import Transfer
from clients.custom_types import ChainConfig


class MockTransfer(Transfer):
    def __eq__(self, value: Any) -> bool:
        return isinstance(value, MockTransfer) and self.tx_hash == value.tx_hash

    def __gt__(self, value: Any) -> bool:
        return False


class MockChainConfig(ChainConfig):
    transfer_class: type[Transfer] = MockTransfer
