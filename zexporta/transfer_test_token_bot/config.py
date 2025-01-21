import os

from web3 import Web3

from zexporta.config import ChainId

from .custom_types import TestToken

LOGGER_PATH = "/var/log/transfer_test_token_bot/"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

HOLDER_PRIVATE_KEY = os.environ["HOLDER_PRIVATE_KEY"]

TEST_TOKENS = [
    TestToken(
        symbol="zUSDT",
        chain_id=ChainId(17000),  # Holesky
        amount=int(20e6),  # 20 zUSDT
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    TestToken(
        symbol="zUSDT",
        chain_id=ChainId(97),  # BSC Testnet
        amount=int(20e6),  # 20 zUSDT
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    TestToken(
        symbol="zUSDT",
        chain_id=ChainId(11155111),  # Sepolia
        amount=int(20e6),  # 20 zUSDT
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    TestToken(
        symbol="zEIGEN",
        chain_id=ChainId(17000),  # Holesky
        amount=int(15e18),  # 15 zEIGEN
        address=Web3.to_checksum_address("0x219f1708400bE5b8cC47A56ed2f18536F5Da7EF4"),
        decimal=18,
    ),
    TestToken(
        symbol="zEIGEN",
        chain_id=ChainId(97),  # BSC Testnet
        amount=int(15e18),  # 20 zEIGEN
        address=Web3.to_checksum_address("0x219f1708400bE5b8cC47A56ed2f18536F5Da7EF4"),
        decimal=18,
    ),
    TestToken(
        symbol="zEIGEN",
        chain_id=ChainId(11155111),  # Sepolia
        amount=int(15e18),  # 20 zEIGEN
        address=Web3.to_checksum_address("0x219f1708400bE5b8cC47A56ed2f18536F5Da7EF4"),
        decimal=18,
    ),
    TestToken(
        symbol="zWBTC",
        chain_id=ChainId(17000),  # Holesky
        amount=10000,  # 10000 satoshi
        address=Web3.to_checksum_address("0x9d84f6e4D734c33C2B6e7a5211780499A71aEf6A"),
        decimal=8,
    ),
    TestToken(
        symbol="zWBTC",
        chain_id=ChainId(97),  # BSC Testnet
        amount=10000,  # 10000 satoshi
        address=Web3.to_checksum_address("0x9d84f6e4D734c33C2B6e7a5211780499A71aEf6A"),
        decimal=8,
    ),
    TestToken(
        symbol="zWBTC",
        chain_id=ChainId(11155111),  # Sepolia
        amount=10000,  # 10000 satoshi
        address=Web3.to_checksum_address("0x9d84f6e4D734c33C2B6e7a5211780499A71aEf6A"),
        decimal=8,
    ),
]
