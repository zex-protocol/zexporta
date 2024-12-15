import os

from zex_deposit.config import CHAINS_CONFIG, SENTRY_DNS, ZEX_ENCODE_VERSION

LOGGER_PATH = "/var/log/validator/validator.log"

VALIDATED_IPS = {
    "104.194.145.26": [
        "/pyfrost/v1/dkg/round1",
        "/pyfrost/v1/dkg/round2",
        "/pyfrost/v1/dkg/round3",
        "/pyfrost/v1/sign",
        "/pyfrost/v1/generate-nonces",
    ],
    "172.20.0.1": [
        "/pyfrost/v1/dkg/round1",
        "/pyfrost/v1/dkg/round2",
        "/pyfrost/v1/dkg/round3",
        "/pyfrost/v1/sign",
        "/pyfrost/v1/generate-nonces",
    ],
}

PRIVATE_KEY = int(os.environ["NODE_PRIVATE_KEY"])
