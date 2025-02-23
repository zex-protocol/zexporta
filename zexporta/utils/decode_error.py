from eth_abi import decode
from eth_utils import decode_hex, keccak

from zexporta.utils.abi import FACTORY_ABI


# Decode custom error data
def decode_custom_error_data(response_error_data, contract_abi):
    try:
        # Ensure the error data is a valid hex string
        if response_error_data.startswith("0x"):
            response_error_data = response_error_data[2:]

        # Extract the error signature (first 4 bytes)
        error_signature_hash = response_error_data[:8]

        # Find the matching error in the ABI
        for entry in contract_abi:
            if entry["type"] == "error":
                # Compute the error signature
                error_signature = f"{entry['name']}({','.join(i['type'] for i in entry['inputs'])})"
                computed_hash = keccak(text=error_signature).hex()[:8]

                # Match the signature hash
                if error_signature_hash == computed_hash:
                    # Decode the data
                    encoded_data = decode_hex(response_error_data[8:])
                    decoded_values = decode([i["type"] for i in entry["inputs"]], encoded_data)

                    # Format the decoded error
                    return {
                        "error_name": entry["name"],
                        "decoded_values": {
                            input["name"]: value for input, value in zip(entry["inputs"], decoded_values)
                        },
                    }

        return {"error": "No matching error signature found in ABI"}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(decode_custom_error_data("0xf4d678b8", FACTORY_ABI))  # noqa: T201 FIXME
