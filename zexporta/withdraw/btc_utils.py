from bitcoinutils.constants import TAPROOT_SIGHASH_ALL
from bitcoinutils.keys import P2trAddress, P2wpkhAddress
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis

from zexporta.custom_types import UTXO, BTCWithdrawRequest


class NotEnoughInputs(Exception):
    pass


def get_simple_withdraw_tx(
    withdraw_request: BTCWithdrawRequest,
    change_address: str,
    utxos: list[UTXO] | None = None,
):
    send_amount = to_satoshis(withdraw_request.amount)
    utxos = utxos or withdraw_request.utxos

    fee = calculate_fee(
        recipient=withdraw_request.recipient,
        change_address=change_address,
        amount=send_amount,
        sat_per_byte=withdraw_request.sat_per_byte,
        utxos=utxos,
    )

    utxos = withdraw_request.utxos
    to_address = withdraw_request.recipient
    send_amount = to_satoshis(withdraw_request.amount)
    change_address = P2trAddress(change_address)
    change_address_script_pubkey = change_address.to_script_pub_key()
    utxos_script_pubkeys = [change_address_script_pubkey] * len(utxos)
    to_address = P2wpkhAddress(to_address)

    txins = [TxInput(utxo.tx_hash, utxo.index) for utxo in utxos]
    amounts = [utxo.amount for utxo in utxos]

    input_amount = sum(amounts)
    txout1 = TxOutput(send_amount, to_address.to_script_pub_key())
    txout2 = TxOutput(
        input_amount - send_amount - fee, change_address.to_script_pub_key()
    )
    tx = Transaction(txins, [txout1, txout2], has_segwit=True)
    tx_digests = [
        tx.get_transaction_taproot_digest(
            i, utxos_script_pubkeys, amounts, 0, sighash=TAPROOT_SIGHASH_ALL
        )
        for i in range(len(utxos))
    ]
    return tx, tx_digests


def calculate_fee(
    recipient: str,
    amount: int,
    change_address: str,
    utxos: list[UTXO],
    sat_per_byte: int,
):
    to_address = P2wpkhAddress(recipient)
    change_address = P2trAddress(change_address)

    txins = [TxInput(utxo.tx_hash, utxo.index) for utxo in utxos]
    amounts = [utxo.amount for utxo in utxos]

    input_amount = sum(amounts)
    txout1 = TxOutput(amount, to_address.to_script_pub_key())

    fee_calculator_out = TxOutput(
        input_amount - amount, change_address.to_script_pub_key()
    )
    fee_calculator_tx = Transaction(
        txins, [txout1, fee_calculator_out], has_segwit=True
    )
    return fee_calculator_tx.get_size() * sat_per_byte
