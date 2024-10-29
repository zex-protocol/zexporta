
from pyfrost.network.abstract import Validators

from .config import VALIDATED_IPS


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
       pass