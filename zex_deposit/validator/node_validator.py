import asyncio
from hashlib import sha256

from eth_typing import ChainId
from pyfrost.network.abstract import Validators

from utils.zex_deposit import encode_zex_deposit, DEPOSIT_OPERATION
from .transfer import get_users_transfers
from .config import VALIDATED_IPS, CHAINS_CONFIG, ZEX_ENDODE_VERSION


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
        method = input_data['method']
        data = input_data['data']
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
                "users_transfers": users_transfers,
            }
        }
