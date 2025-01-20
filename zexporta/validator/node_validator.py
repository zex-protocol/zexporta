import logging

from pyfrost.network.abstract import Validators

from zexporta.custom_types import ChainSymbol, SaDepositSchema
from zexporta.utils.logger import ChainLoggerAdapter

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
        chain = CHAINS_CONFIG[ChainSymbol(data["chain_symbol"]).value]
        _logger = ChainLoggerAdapter(logger, chain.chain_symbol)
        if method == "deposit":
            return deposit(chain, SaDepositSchema(**data), _logger)

        if method == "withdraw":
            sa_withdraw_nonce = data["sa_withdraw_nonce"]
            return withdraw(chain, sa_withdraw_nonce, logger=_logger)

        raise NotImplementedError()
