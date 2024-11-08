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
    }
]
