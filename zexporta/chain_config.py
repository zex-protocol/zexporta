from web3 import Web3

from zexporta.db.utxo import populate_deposits_utxos
from zexporta.settings import app_settings

from .custom_types import (
    BTCConfig,
    ChainConfig,
    ChainId,
    ChainSymbol,
    EVMConfig,
)

CHAINS_CONFIG: dict[str, ChainConfig] = {
    ChainSymbol.HOL.value: EVMConfig(
        private_rpc=app_settings.hol.rpc,
        native_decimal=18,
        chain_symbol=ChainSymbol.HOL.value,
        finalize_block_count=1,
        delay=1,
        batch_block_size=20,
        vault_address=Web3.to_checksum_address("0x72E46E170342E4879b0Ea8126389111D4275173D"),
        chain_id=ChainId(app_settings.hol.chain_id),
    ),
    ChainSymbol.SEP.value: EVMConfig(
        private_rpc=app_settings.sep.rpc,
        native_decimal=18,
        chain_symbol=ChainSymbol.SEP.value,
        finalize_block_count=1,
        delay=1,
        batch_block_size=20,
        vault_address=Web3.to_checksum_address("0x72E46E170342E4879b0Ea8126389111D4275173D"),
        chain_id=ChainId(app_settings.sep.chain_id),
    ),
    ChainSymbol.BST.value: EVMConfig(
        private_rpc=app_settings.bst.rpc,
        native_decimal=18,
        chain_symbol=ChainSymbol.BST.value,
        finalize_block_count=1,
        poa=True,
        delay=1,
        batch_block_size=30,
        vault_address=Web3.to_checksum_address("0x72E46E170342E4879b0Ea8126389111D4275173D"),
        chain_id=ChainId(app_settings.bst.chain_id),
    ),
    ChainSymbol.BTC.value: BTCConfig(
        private_rpc=app_settings.btc.rpc,
        private_indexer_rpc=app_settings.btc.indexer,
        chain_symbol=ChainSymbol.BTC.value,
        finalize_block_count=1,
        delay=60,
        batch_block_size=5,
        vault_address="",
        deposit_finalizer_middleware=(populate_deposits_utxos,),
    ),
}
