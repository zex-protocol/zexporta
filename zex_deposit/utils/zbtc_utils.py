import secrets

from bitcoinutils.constants import TAPROOT_SIGHASH_ALL
from bitcoinutils.keys import P2trAddress, P2wpkhAddress, PrivateKey, PublicKey
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from pyfrost.crypto_utils import code_to_pub


def get_taproot_address(public_key):
    public_key = code_to_pub(public_key)
    x_hex = hex(public_key.x)[2:].zfill(64)
    y_hex = hex(public_key.y)[2:].zfill(64)
    prefix = "02" if int(y_hex, 16) % 2 == 0 else "03"
    compressed_pubkey = prefix + x_hex
    public_key = PublicKey(compressed_pubkey)
    taproot_address = public_key.get_taproot_address()
    return taproot_address


def get_simple_withdraw_tx(from_address, utxos, to_address, send_amount, fee_amount):
    from_address = P2trAddress(from_address)
    first_script_pubkey = from_address.to_script_pub_key()
    utxos_script_pubkeys = [first_script_pubkey] * len(utxos)
    to_address = P2wpkhAddress(to_address)

    txins = [TxInput(utxo["txid"], utxo["vout"]) for utxo in utxos]
    amounts = [utxo["value"] for utxo in utxos]

    first_amount = sum(amounts)

    txout1 = TxOutput(send_amount, to_address.to_script_pub_key())
    txout2 = TxOutput(
        first_amount - send_amount - fee_amount, from_address.to_script_pub_key()
    )

    tx = Transaction(txins, [txout1, txout2], has_segwit=True)
    tx_digests = [
        tx.get_transaction_taproot_digest(
            i, utxos_script_pubkeys, amounts, 0, sighash=TAPROOT_SIGHASH_ALL
        )
        for i in range(len(utxos))
    ]
    return tx, tx_digests


def new_wallet() -> tuple[PrivateKey, P2wpkhAddress]:
    priv = PrivateKey.from_bytes(secrets.token_bytes(32))
    return priv, priv.get_public_key().get_segwit_address()
