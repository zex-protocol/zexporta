import asyncio
from hashlib import sha256
import json

from pyfrost.network.sa import SA

from custom_types import ChainConfig, TransferStatus, UserTransfer
from db.transfer import find_transactions_by_status, upsert_verified_transfers, to_reorg
from utils.node_info import NodesInfo
from utils.encode_deposit import encode_zex_deposit, DEPOSIT_OPERATION
from .config import (
    CHAINS_CONFIG,
    DKG_JSON_PATH,
    DKG_NAME,
    SA_DELAY_SECOND,
    ZEX_ENDODE_VERSION,
)

nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=50)


def _parse_dkg_json() -> dict:
    with open(DKG_JSON_PATH, "r") as f:
        dkg_info = json.load(f)

    return dkg_info[DKG_NAME]


dkg_key = _parse_dkg_json()


async def deposit(chain: ChainConfig):
    while True:
        dkg_party = dkg_key["party"]
        nonces_response_task = asyncio.create_task(
            sa.request_nonces(dkg_party, number_of_nonces=1)
        )
        finalized_transfers_task = asyncio.create_task(
            find_transactions_by_status(
                chain_id=chain.chain_id, status=TransferStatus.FINALIZED
            )
        )
        await nonces_response_task
        await finalized_transfers_task
        finalized_transfers = finalized_transfers_task.result()
        nonces_response = nonces_response_task.result()
        nonces_for_sig = {}
        for id, nonce in nonces_response.items():
            nonces_for_sig[id] = nonce["data"][0]

        if not finalized_transfers:
            await asyncio.sleep(SA_DELAY_SECOND)
            continue
        from_block = finalized_transfers[0].block_number
        to_block = max(
            finalized_transfers[0].block_number,
            finalized_transfers[-1].block_number
            - 20,  # TODO: to ensure that validator rpcs finalized block number synchronized.
        )
        data = {
            "method": "deposit",
            "data": {
                "from_block": from_block,
                "to_block": to_block,
                "chain_id": chain.chain_id,
            },
        }

        sig = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)
        if sig.get("result") == "SUCCESSFUL":
            data = list(sig["signature_data_from_node"].values())[0]["users_transfers"]
            print(data)
            users_transfers = [UserTransfer(**user_transfer) for user_transfer in data]
            print(users_transfers)
            encoded_data = encode_zex_deposit(
                version=ZEX_ENDODE_VERSION,
                operation_type=DEPOSIT_OPERATION,
                chain_id=chain.chain_id,
                from_block=from_block,
                to_block=to_block,
                users_transfers=users_transfers,
            )
            hash_ = sha256(encoded_data).hexdigest()
            if hash_ != sig["message_hash"]:
                return
            await upsert_verified_transfers(users_transfers)
            await to_reorg(
                chain.chain_id, from_block, to_block, TransferStatus.FINALIZED
            )
        await asyncio.sleep(SA_DELAY_SECOND)


async def main(loop):
    _ = [loop.create_task(deposit(chain)) for chain in CHAINS_CONFIG.values()]


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()
