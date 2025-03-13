from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from web3 import Web3


class MongoConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    uri: str = Field(..., env="URI")  # type: ignore


class DKGConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    json_path: str = Field(default="./zexporta/dkgs/dkgs.json", env="JSON_PATH")  # type: ignore
    name: str = Field(default="ethereum", env="NAME")  # type: ignore


class SentryConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    dsn: str = Field(..., env="DSN")  # type: ignore


class ZexConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    base_url: str = Field(..., env="BASE_URL")  # type: ignore
    encode_version: int = Field(..., env="ENCODE_VERSION")  # type: ignore


class UserDepositConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    factory_address: str = Field(..., env="FACTORY_ADDRESS")  # type: ignore
    bytecode_hash: str = Field(..., env="BYTECODE_HASH")  # type: ignore


class WithdrawerConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    private_key: str = Field(..., env="PRIVATE_KEY")  # type: ignore


class BitcoinConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    rpc: str = Field(..., env="RPC")  # type: ignore
    indexer: str = Field(..., env="INDEXER")  # type: ignore
    group_pub_key: str = Field(..., env="GROUP_PUB_KEY")  # type: ignore
    vault_address: str = Field(..., env="VAULT_ADDRESS")  # type: ignore


class BSTConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    rpc: str = Field(..., env="RPC")  # type: ignore
    chain_id: int = Field(..., env="CHAIN_ID")  # type: ignore
    vault_address: str = Field(..., env="VAULT_ADDRESS")  # type: ignore


class SEPConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    rpc: str = Field(..., env="RPC")  # type: ignore
    chain_id: int = Field(..., env="CHAIN_ID")  # type: ignore
    vault_address: str = Field(..., env="VAULT_ADDRESS")  # type: ignore


class HOLConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    rpc: str = Field(..., env="RPC")  # type: ignore
    chain_id: int = Field(..., env="CHAIN_ID")  # type: ignore
    vault_address: str = Field(..., env="VAULT_ADDRESS")  # type: ignore


class TelegramConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    base_url: str = Field(default="https://api.telegram.org", env="BASE_URL")  # type: ignore
    bot_info: str = Field(..., env="BOT_INFO")  # type: ignore
    chat_id: str = Field(..., env="CHAT_ID")  # type: ignore
    thread_id: str = Field(..., env="THREAD_ID ")  # type: ignore


class NodeConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    private_key: int = Field(..., env="PRIVATE_KEY")  # type: ignore
    id: str = Field(..., env="ID")  # type: ignore


class SaConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    batch_block_number_size: int = Field(default=100, env="BATCH_BLOCK_NUMBER_SIZE")  # type: ignore
    transactions_batch_size: int = Field(default=2, env="TRANSACTIONS_BATCH_SIZE")  # type: ignore
    shield_private_key: str = Field(..., env="SHIELD_PRIVATE_KEY")  # type: ignore


class MonitoringConfig(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)
    bot_zex_user_id: int = Field(..., env="BOT_ZEX_USER_ID")  # type: ignore
    bot_withdrawer_private_key: str = Field(..., env="BOT_WITHDRAWER_PRIVATE_KEY")  # type: ignore


class ApplicationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__")
    env: str = Field(..., env="ENV")  # type: ignore
    zex: ZexConfig
    hol: HOLConfig
    sep: SEPConfig
    bst: BSTConfig
    btc: BitcoinConfig
    withdrawer: WithdrawerConfig
    user_deposit: UserDepositConfig
    sentry: SentryConfig
    dkg: DKGConfig
    mongo: MongoConfig
    telegram: TelegramConfig
    node: NodeConfig
    sa: SaConfig
    monitoring: MonitoringConfig
    evm_native_token_address: str = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
    batch_block_number_size: int = Field(default=5, env="BATCH_BLOCK_NUMBER_SIZE")  # type: ignore
    max_delay_per_block_batch: int = Field(default=3, env="MAX_DELAY_PER_BLOCK_BATCH")  # type: ignore
    holder_private_key: str = Field(..., env="HOLDER_PRIVATE_KEY")  # type: ignore


app_settings = ApplicationSettings()  # type: ignore
