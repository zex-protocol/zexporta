from dataclasses import dataclass

from web3 import Web3

from .abi import ERC20_ABI
from .custom_types import ChecksumAddress

type FunctionHash = str


class NotRecognizedSolidityFuncError(Exception):
    pass


class InvalidTxError(Exception):
    pass


@dataclass
class SolidityFunction:
    name: str
    inputs: list[dict[str, str]]


# Only transferFrom and transfer func input
@dataclass(kw_only=True)
class TransferTX:
    _to: ChecksumAddress
    _value: int
    _from: ChecksumAddress | None = None


def _parse_abi(abi: list[dict]) -> dict[FunctionHash, SolidityFunction]:
    function_selectors = {}
    for func in abi:
        if func["type"] == "function":
            func_name = func["name"]
            if func_name in ("transferFrom", "transfer"):
                input_types = [inp["type"] for inp in func["inputs"]]
                func_signature = f"{func_name}({','.join(input_types)})"
                func_selector = Web3.keccak(text=func_signature)[:4].hex()
                function_selectors[func_selector] = SolidityFunction(name=func_name, inputs=func["inputs"])
    return function_selectors


function_selectors = _parse_abi(ERC20_ABI)


def decode_transfer_tx(tx_input: str) -> TransferTX:
    function_selector = tx_input[:10]

    if function_selector in function_selectors:
        func_info = function_selectors[function_selector]
        func_inputs = func_info.inputs

        params_data = tx_input[10:]
        decoded_input_data = dict()
        try:
            for i, param in enumerate(func_inputs):
                param_type = param["type"]
                param_name = param["name"]
                param_data = params_data[i * 64 : (i + 1) * 64]
                if param_type == "address":
                    param_value = "0x" + param_data[-40:]
                    param_value = Web3.to_checksum_address(param_value)

                elif param_type.startswith("uint"):
                    param_value = int(param_data, 16)

                else:
                    param_value = param_data

                decoded_input_data[param_name] = param_value
        except ValueError as e:
            raise InvalidTxError(e) from e
        decoded_tx_input = TransferTX(**decoded_input_data)
        return decoded_tx_input
    else:
        raise NotRecognizedSolidityFuncError(f"Function {function_selector} is not recognized")
