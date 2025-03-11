from zexporta.chain_config import CHAINS_CONFIG
from zexporta.settings import app_settings

# FIXME: we should fix this I did it since pylance said it is unused
CHAINS_CONFIG = CHAINS_CONFIG
DKG_JSON_PATH = app_settings.dkg.json_path
DKG_NAME = app_settings.dkg.name
SA_SHIELD_PRIVATE_KEY = app_settings.sa.shield_private_key
SENTRY_DNS = app_settings.sentry.dsn
WITHDRAWER_PRIVATE_KEY = app_settings.withdrawer.private_key

LOGGER_PATH = "/var/log/withdraw/"
WITHDRAW_DELAY_SECOND = 10
SA_TIMEOUT = 60
SA_DELAY_SECOND = 20
