import logging

from pyfrost.network.abstract import Validators

from zex_deposit.utils.logger import ChainLoggerAdapter


from .config import CHAINS_CONFIG, VALIDATED_IPS
from .deposit import deposit
from .withdraw import withdraw

logger = logging.getLogger(__name__)


class NodeValidators(Validators):
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def caller_validator(sender_ip: str, method: str):
        if method in VALIDATED_IPS.get(str(sender_ip), []):
            return True
        return False

    @staticmethod
    def data_validator(input_data: dict):
        method = input_data["method"]
        data = input_data["data"]
        chain = CHAINS_CONFIG[(data["chain_id"])]
        _logger = ChainLoggerAdapter(logger, chain)
        if method == "deposit":
            return deposit(chain, data, _logger)

        if method == "withdraw":
            vault_nonce = data["vault_nonce"]
            return withdraw(chain, vault_nonce, logger=_logger)

        raise NotImplementedError()
