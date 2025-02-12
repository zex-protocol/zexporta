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
    to_address = withdraw_request.recipient

    amounts = []
    input_amount = 0
    utxos_script_pubkeys = []
    inputs = []
    for utxo in utxos:
        amounts.append(utxo.amount)  # should be satoshi
        input_amount += utxo.amount
        utxos_script_pubkeys.append(P2trAddress(utxo.address).to_script_pub_key())
        inputs.append(TxInput(txid=utxo.tx_hash, txout_index=utxo.index))

    # create transaction output
    txOut1 = TxOutput(send_amount, P2wpkhAddress(to_address).to_script_pub_key())
    txOut2 = TxOutput(
        input_amount - send_amount, P2trAddress(change_address).to_script_pub_key()
    )

    # create transaction without change output - if at least a single input is
    # segwit we need to set has_segwit=True
    tx = Transaction(inputs, [txOut1, txOut2], has_segwit=True)
    tx_digests = tx.get_transaction_taproot_digest(
        0, utxos_script_pubkeys, amounts, 0, sighash=TAPROOT_SIGHASH_ALL
    )
    return tx, tx_digests


def calculate_fee(
    recipient: str,
    amount: int,
    change_address: str,
    utxos: list[UTXO],
    sat_per_byte: int,
) -> int:
    amounts = []
    input_amount = 0
    utxos_script_pubkeys = []
    inputs = []
    for utxo in utxos:
        amounts.append(utxo.amount)  # should be satoshi
        input_amount += utxo.amount
        utxos_script_pubkeys.append(P2trAddress(utxo.address).to_script_pub_key())
        inputs.append(TxInput(txid=utxo.tx_hash, txout_index=utxo.index))

    # create transaction output
    txOut1 = TxOutput(amount, P2wpkhAddress(recipient).to_script_pub_key())
    txOut2 = TxOutput(
        input_amount - amount, P2trAddress(change_address).to_script_pub_key()
    )

    # create transaction without change output - if at least a single input is
    # segwit we need to set has_segwit=True
    fee_calculator_tx = Transaction(inputs, [txOut1, txOut2], has_segwit=True)
    tx_size = fee_calculator_tx.get_size() + (
        30 * len(utxos)
    )  # add signature size (ceil of size actual size is less)
    return tx_size * sat_per_byte
