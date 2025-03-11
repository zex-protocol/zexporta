from zexporta.chain_config import CHAINS_CONFIG
from zexporta.custom_types import EnvEnum
from zexporta.settings import app_settings

CHAINS_CONFIG = CHAINS_CONFIG
ENVIRONMENT = app_settings.env
SENTRY_DNS = app_settings.sentry.dsn
ZEX_ENCODE_VERSION = app_settings.zex.encode_version

LOGGER_PATH = "/var/log/validator/validator.log"

if EnvEnum.PROD == ENVIRONMENT:
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
else:
    VALIDATED_IPS = {
        "172.20.0.4": [
            "/pyfrost/v1/dkg/round1",
            "/pyfrost/v1/dkg/round2",
            "/pyfrost/v1/dkg/round3",
            "/pyfrost/v1/sign",
            "/pyfrost/v1/generate-nonces",
        ],
        "172.20.0.5": [
            "/pyfrost/v1/dkg/round1",
            "/pyfrost/v1/dkg/round2",
            "/pyfrost/v1/dkg/round3",
            "/pyfrost/v1/sign",
            "/pyfrost/v1/generate-nonces",
        ],
    }
PRIVATE_KEY = app_settings.node.private_key
