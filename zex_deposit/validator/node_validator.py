import asyncio
from hashlib import sha256

from pyfrost.network.abstract import Validators

from zex_deposit.utils.encode_deposit import DEPOSIT_OPERATION, encode_zex_deposit

from .config import CHAINS_CONFIG, VALIDATED_IPS, ZEX_ENDODE_VERSION
from .transfer import get_users_transfers


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
        data = input_data["data"]
        chain_config = CHAINS_CONFIG[(data["chain_id"])]
        from_block = data["from_block"]
        to_block = data["to_block"]
        users_transfers = asyncio.run(
            get_users_transfers(
                chain=chain_config, from_block=from_block, to_block=to_block
            )
        )
        encoded_data = encode_zex_deposit(
            version=ZEX_ENDODE_VERSION,
            operation_type=DEPOSIT_OPERATION,
            chain_id=chain_config.chain_id,
            from_block=from_block,
            to_block=to_block,
            users_transfers=users_transfers,
        )
        return {
            "hash": sha256(encoded_data).hexdigest(),
            "data": {
                "users_transfers": [
                    user_transfer.model_dump() for user_transfer in users_transfers
                ],
            },
        }
