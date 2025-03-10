from zexporta.chain_config import CHAIN_CONFIG
from zexporta.settings import app_settings

CHAINS_CONFIG = CHAIN_CONFIG

DKG_JSON_PATH = app_settings.dkg.json_path
DKG_NAME = app_settings.dkg.name
SA_SHIELD_PRIVATE_KEY = app_settings.sa_shield_private_key
SENTRY_DNS = app_settings.sentry.dsn
WITHDRAWER_PRIVATE_KEY = app_settings.withdrawer.private_key

LOGGER_PATH = "/var/log/withdraw/"
WITHDRAW_DELAY_SECOND = 10
SA_TIMEOUT = 60
SA_DELAY_SECOND = 20
