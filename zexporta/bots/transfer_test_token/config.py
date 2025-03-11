from web3 import Web3

from zexporta.bots.custom_types import BotToken
from zexporta.custom_types import ChainSymbol
from zexporta.settings import app_settings

LOGGER_PATH = "."
MONGO_URI = app_settings.mongo.uri

HOLDER_PRIVATE_KEY = app_settings.holder_private_key

TEST_TOKENS = [
    BotToken(
        symbol="zUSDT",
        chain_symbol=ChainSymbol.HOL,  # Holesky
        amount=int(20e6),  # 20 zUSDT
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    BotToken(
        symbol="zUSDT",
        chain_symbol=ChainSymbol.BST,  # BSC Testnet
        amount=int(20e6),  # 20 zUSDT
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    BotToken(
        symbol="zUSDT",
        chain_symbol=ChainSymbol.SEP,  # Sepolia
        amount=int(20e6),  # 20 zUSDT
        address=Web3.to_checksum_address("0x325CCd77e71Ac296892ed5C63bA428700ec0f868"),
        decimal=6,
    ),
    BotToken(
        symbol="zEIGEN",
        chain_symbol=ChainSymbol.HOL,  # Holesky
        amount=int(15e18),  # 15 zEIGEN
        address=Web3.to_checksum_address("0x219f1708400bE5b8cC47A56ed2f18536F5Da7EF4"),
        decimal=18,
    ),
    BotToken(
        symbol="zEIGEN",
        chain_symbol=ChainSymbol.BST,  # BSC Testnet
        amount=int(15e18),  # 20 zEIGEN
        address=Web3.to_checksum_address("0x219f1708400bE5b8cC47A56ed2f18536F5Da7EF4"),
        decimal=18,
    ),
    BotToken(
        symbol="zEIGEN",
        chain_symbol=ChainSymbol.SEP,  # Sepolia
        amount=int(15e18),  # 20 zEIGEN
        address=Web3.to_checksum_address("0x219f1708400bE5b8cC47A56ed2f18536F5Da7EF4"),
        decimal=18,
    ),
    BotToken(
        symbol="zWBTC",
        chain_symbol=ChainSymbol.HOL,  # Holesky
        amount=10000,  # 10000 satoshi
        address=Web3.to_checksum_address("0x9d84f6e4D734c33C2B6e7a5211780499A71aEf6A"),
        decimal=8,
    ),
    BotToken(
        symbol="zWBTC",
        chain_symbol=ChainSymbol.BST,  # BSC Testnet
        amount=10000,  # 10000 satoshi
        address=Web3.to_checksum_address("0x9d84f6e4D734c33C2B6e7a5211780499A71aEf6A"),
        decimal=8,
    ),
    BotToken(
        symbol="zWBTC",
        chain_symbol=ChainSymbol.SEP,  # Sepolia
        amount=10000,  # 10000 satoshi
        address=Web3.to_checksum_address("0x9d84f6e4D734c33C2B6e7a5211780499A71aEf6A"),
        decimal=8,
    ),
]
