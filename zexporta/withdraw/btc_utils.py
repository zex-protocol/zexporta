from bitcoinutils.constants import TAPROOT_SIGHASH_ALL
from bitcoinutils.keys import P2trAddress, P2wpkhAddress
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis

from zexporta.custom_types import BTCWithdrawRequest


def get_simple_withdraw_tx(withdraw_request: BTCWithdrawRequest, change_address: str):
    utxos = withdraw_request.utxos
    to_address = withdraw_request.recipient
    send_amount = to_satoshis(withdraw_request.amount)

    # todo :: refactor & calculate fee
    fee_amount = 0
    change_address = P2trAddress(change_address)
    change_address_script_pubkey = change_address.to_script_pub_key()
    utxos_script_pubkeys = [change_address_script_pubkey] * len(utxos)
    to_address = P2wpkhAddress(to_address)

    txins = [TxInput(utxo.tx_hash, utxo.index) for utxo in utxos]
    amounts = [utxo.amount for utxo in utxos]

    first_amount = sum(amounts)

    txout1 = TxOutput(send_amount, to_address.to_script_pub_key())
    txout2 = TxOutput(
        first_amount - send_amount - fee_amount, change_address.to_script_pub_key()
    )

    tx = Transaction(txins, [txout1, txout2], has_segwit=True)
    tx_digests = [
        tx.get_transaction_taproot_digest(
            i, utxos_script_pubkeys, amounts, 0, sighash=TAPROOT_SIGHASH_ALL
        )
        for i in range(len(utxos))
    ]
    return tx, tx_digests
