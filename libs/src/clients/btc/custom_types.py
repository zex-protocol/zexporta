# Model for Address Details
from typing import Any, ClassVar

from clients.custom_types import URL, ChainConfig, Transfer

type Address = str


class BTCTransfer(Transfer):
    to: Address
    index: int

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, BTCTransfer):
            return self.tx_hash == value.tx_hash and self.index == value.index
        return NotImplemented

    def __gt__(self, value: Any) -> bool:
        if isinstance(value, BTCTransfer):
            return self.tx_hash > value.tx_hash or (
                self.tx_hash == value.tx_hash and self.index > value.index
            )
        return NotImplemented


class BTCConfig(ChainConfig):
    private_indexer_rpc: URL
    transfer_class: ClassVar[type[BTCTransfer]] = BTCTransfer
