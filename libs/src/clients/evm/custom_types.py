from typing import Any, ClassVar

from eth_typing import ChainId, ChecksumAddress
from pydantic import Field

from clients.custom_types import ChainConfig, Transfer


class EVMTransfer(Transfer):
    def __eq__(self, value: Any) -> bool:
        if isinstance(value, EVMTransfer):
            return self.tx_hash == value.tx_hash
        return NotImplemented

    def __gt__(self, value: Any) -> bool:
        if isinstance(value, EVMTransfer):
            return self.tx_hash > value.tx_hash
        return NotImplemented


class EVMConfig(ChainConfig):
    chain_id: ChainId
    poa: bool = Field(default=False)
    vault_address: ChecksumAddress
    native_decimal: int
    transfer_class: ClassVar[type[EVMTransfer]] = EVMTransfer
