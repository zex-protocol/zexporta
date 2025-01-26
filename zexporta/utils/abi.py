__all__ = ["ERC20_ABI"]

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_from", "type": "address"},
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
        "stateMutability": "view",
    },
    # Add other ERC20 functions if necessary
]

FACTORY_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "salt", "type": "uint256"}],
        "name": "deploy",
        "outputs": [
            {"internalType": "address", "name": "userDepositAddress", "type": "address"}
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "addr", "type": "address"},
            {"indexed": False, "name": "salt", "type": "uint256"},
        ],
        "name": "Deployed",
        "type": "event",
    },
]

USER_DEPOSIT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "_token", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"},
        ],
        "name": "transferERC20",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_amount", "type": "uint256"}],
        "name": "transferNativeToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

VAULT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenAddress_", "type": "address"},
            {"internalType": "uint256", "name": "amount_", "type": "uint256"},
            {"internalType": "address", "name": "recipient_", "type": "address"},
            {"internalType": "uint256", "name": "nonce_", "type": "uint256"},
            {"internalType": "uint256", "name": "signature_", "type": "uint256"},
            {
                "internalType": "address",
                "name": "nonceTimesGeneratorAddress_",
                "type": "address",
            },
            {"internalType": "bytes", "name": "shieldSignature_", "type": "bytes"},
        ],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "nonceIsUsed",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "Nonce", "type": "uint256"}],
        "name": "InvalidNonce",
        "type": "error",
    },
    {"inputs": [], "name": "InvalidSignature", "type": "error"},
    {"inputs": [], "name": "TokenTransferFailed", "type": "error"},
    {"inputs": [], "name": "ZeroAddress", "type": "error"},
]
