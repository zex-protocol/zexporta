from typing import Any

from eth_typing import ChainId, ChecksumAddress
from pydantic import Field

from clients.custom_types import ChainConfig, Transfer, WithdrawRequest


class EVMTransfer(Transfer[ChecksumAddress]):
    def __eq__(self, value: Any) -> bool:
        if isinstance(value, EVMTransfer):
            return self.tx_hash == value.tx_hash
        return NotImplemented

    def __gt__(self, value: Any) -> bool:
        if isinstance(value, EVMTransfer):
            return self.tx_hash > value.tx_hash
        return NotImplemented


class EVMWithdrawRequest(WithdrawRequest):
    token_address: ChecksumAddress
    chain_id: ChainId


class EVMConfig(ChainConfig[EVMTransfer, EVMWithdrawRequest]):
    chain_id: ChainId
    poa: bool = Field(default=False)
    native_decimal: int
    transfer_class: type[EVMTransfer] = EVMTransfer
    withdraw_request_type: type[EVMWithdrawRequest] = EVMWithdrawRequest


__all__ = ["ChecksumAddress", "ChainId", "EVMConfig", "EVMTransfer", "EVMWithdrawRequest"]
