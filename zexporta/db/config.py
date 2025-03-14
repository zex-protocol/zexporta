from zexporta.settings import app_settings

MONGO_URI = app_settings.mongo.get_uri()
USER_DEPOSIT_BYTECODE_HASH = app_settings.user_deposit.bytecode_hash
USER_DEPOSIT_FACTORY_ADDRESS = app_settings.user_deposit.factory_address
