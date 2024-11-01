import json
import logging
import asyncio
from weakref import finalize

from eth_typing import ChainId
from web3 import Web3
from pyfrost.network.sa import SA


from utils.node_info import NodesInfo
from custom_types import TransferStatus
from db.transfer import find_transactions_by_status
from .config import DKG_JSON_PATH, DKG_NAME


nodes_info = NodesInfo()
sa = SA(nodes_info, default_timeout=50)


def _parse_dkg_json() -> dict:
    with open(DKG_JSON_PATH, "r") as f:
        dkg_info = json.load(f)

    return dkg_info[DKG_NAME]


dkg_key = _parse_dkg_json()


async def deposit():
    dkg_party = dkg_key["party"]
    nonces_response_task = asyncio.create_task(
        sa.request_nonces(dkg_party, number_of_nonces=1)
    )
    finalized_transfers_task = asyncio.create_task(
        find_transactions_by_status(
            chain_id=ChainId(11155111), status=TransferStatus.FINALIZED
        )
    )
    await nonces_response_task
    await finalized_transfers_task
    finalized_transfers = finalized_transfers_task.result()
    nonces_response = nonces_response_task.result()
    nonces_for_sig = {}
    for id, nonce in nonces_response.items():
        nonces_for_sig[id] = nonce['data'][0]

    if not finalized_transfers:
        return

    data = {
        "method": "deposit",
        "data": {
            "from_block": finalized_transfers[0].block_number,
            "to_block": max(
                finalized_transfers[0].block_number,
                finalized_transfers[-1].block_number - 20,
            ),  # TODO: to ensure that validator rpcs finalized block number synchronized.
            "chain_id": 11155111,
        },
    }

    sig = await sa.request_signature(dkg_key, nonces_for_sig, data, dkg_party)