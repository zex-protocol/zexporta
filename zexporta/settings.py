from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from web3 import Web3

load_dotenv()


class MongoConfig(BaseSettings):
    host: str = Field(validation_alias="HOST")
    port: int = Field(validation_alias="PORT")
    db_name: str = Field(default="transaction_database", validation_alias="DB_NAME")

    def get_uri(self) -> str:
        return f"mongodb://{self.host}:{self.port}/"


class DKGConfig(BaseSettings):
    json_path: str = Field(default="./zexporta/dkgs/dkgs.json", validation_alias="JSON_PATH")
    name: str = Field(default="ethereum", validation_alias="NAME")


class SentryConfig(BaseSettings):
    dsn: str = Field(validation_alias="DSN")


class ZexConfig(BaseSettings):
    base_url: str = Field(validation_alias="BASE_URL")
    encode_version: int = Field(validation_alias="ENCODE_VERSION")


class UserDepositConfig(BaseSettings):
    factory_address: str = Field(validation_alias="FACTORY_ADDRESS")
    bytecode_hash: str = Field(validation_alias="BYTECODE_HASH")


class WithdrawerConfig(BaseSettings):
    evm_private_key: str = Field(validation_alias="EVM_PRIVATE_KEY")


class BitcoinConfig(BaseSettings):
    rpc: str = Field(validation_alias="RPC")
    indexer: str = Field(validation_alias="INDEXER")
    group_pub_key: str = Field(validation_alias="GROUP_PUB_KEY")
    vault_address: str = Field(validation_alias="VAULT_ADDRESS")


class BSTConfig(BaseSettings):
    rpc: str = Field(validation_alias="RPC")
    chain_id: int = Field(validation_alias="CHAIN_ID")
    vault_address: str = Field(validation_alias="VAULT_ADDRESS")


class SEPConfig(BaseSettings):
    rpc: str = Field(validation_alias="RPC")
    chain_id: int = Field(validation_alias="CHAIN_ID")
    vault_address: str = Field(validation_alias="VAULT_ADDRESS")


class HOLConfig(BaseSettings):
    rpc: str = Field(validation_alias="RPC")
    chain_id: int = Field(validation_alias="CHAIN_ID")
    vault_address: str = Field(validation_alias="VAULT_ADDRESS")


class TelegramConfig(BaseSettings):
    base_url: str = Field(default="https://api.telegram.org", validation_alias="BASE_URL")
    bot_info: str = Field(validation_alias="BOT_INFO")
    chat_id: str = Field(validation_alias="CHAT_ID")
    thread_id: str | None = Field(default=None, validation_alias="THREAD_ID")


class NodeConfig(BaseSettings):
    private_key: str = Field(validation_alias="PRIVATE_KEY")
    id: str = Field(validation_alias="ID")


class SaConfig(BaseSettings):
    batch_block_number_size: int = Field(default=100, validation_alias="BATCH_BLOCK_NUMBER_SIZE")
    transactions_batch_size: int = Field(default=2, validation_alias="TRANSACTIONS_BATCH_SIZE")
    shield_private_key: str = Field(validation_alias="SHIELD_PRIVATE_KEY")


class MonitoringConfig(BaseSettings):
    bot_zex_user_id: int = Field(validation_alias="BOT_ZEX_USER_ID")
    bot_withdrawer_private_key: str = Field(validation_alias="BOT_WITHDRAWER_PRIVATE_KEY")


class ApplicationSettings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file_encoding="utf-8", env_nested_delimiter="__")
    env: str = Field(validation_alias="ENV")
    zex: ZexConfig = Field(validation_alias="ZEX")
    hol: HOLConfig = Field(validation_alias="HOL")
    sep: SEPConfig = Field(validation_alias="SEP")
    bst: BSTConfig = Field(validation_alias="BST")
    btc: BitcoinConfig = Field(validation_alias="BTC")
    withdrawer: WithdrawerConfig = Field(validation_alias="WITHDRAWER")
    user_deposit: UserDepositConfig = Field(validation_alias="USER_DEPOSIT")
    sentry: SentryConfig = Field(validation_alias="SENTRY")
    dkg: DKGConfig = Field(validation_alias="DKG")
    mongo: MongoConfig = Field(validation_alias="MONGO")
    telegram: TelegramConfig = Field(validation_alias="TELEGRAM")
    node: NodeConfig = Field(validation_alias="NODE")
    sa: SaConfig = Field(validation_alias="SA")
    monitoring: MonitoringConfig = Field(validation_alias="MONITORING")
    evm_native_token_address: str = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
    batch_block_number_size: int = Field(default=5, validation_alias="BATCH_BLOCK_NUMBER_SIZE")
    max_delay_per_block_batch: int = Field(default=3, validation_alias="MAX_DELAY_PER_BLOCK_BATCH")
    holder_private_key: str = Field(validation_alias="HOLDER_PRIVATE_KEY")


app_settings = ApplicationSettings.model_validate({})
