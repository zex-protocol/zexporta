from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from web3 import Web3


class MongoConfig(BaseSettings):
    uri: str = Field(..., env="URI")  # type: ignore

    class Config:
        env_prefix = "MONGO_"
        case_sensitive = True


class DKGConfig(BaseSettings):
    json_path: str = Field(default="./zexporta/dkgs/dkgs.json", env="JSON_PATH")  # type: ignore
    name: str = Field(default="ethereum", env="NAME")  # type: ignore

    class Config:
        env_prefix = "DKG_"
        case_sensitive = True


class SentryConfig(BaseSettings):
    dsn: str = Field(..., env="DSN")  # type: ignore

    class Config:
        env_prefix = "SENTRY_"
        case_sensitive = True


class ZexConfig(BaseModel):
    base_url: str = Field(..., env="BASE_URL")  # type: ignore
    encode_version: int = Field(..., env="ENCODE_VERSION")  # type: ignore

    class Config:
        env_prefix = "ZEX_"
        case_sensitive = True


class UserDepositConfig(BaseSettings):
    factory_address: str = Field(..., env="FACTORY_ADDRESS")  # type: ignore
    bytecode_hash: str = Field(..., env="BYTECODE_HASH")  # type: ignore

    class Config:
        env_prefix = "USER_DEPOSIT_"
        case_sensitive = True


class WithdrawerConfig(BaseSettings):
    private_key: str = Field(..., env="PRIVATE_KEY")  # type: ignore

    class Config:
        env_prefix = "WITHDRAWER_"
        case_sensitive = True


class BitcoinConfig(BaseSettings):
    rpc: str = Field(..., env="RPC")  # type: ignore
    indexer_rpc: str = Field(..., env="INDEXER")  # type: ignore
    group_pub_key: str = Field(..., env="GROUP_KEY_PUB")  # type: ignore

    class Config:
        env_prefix = "BTC_"
        case_sensitive = True


class BSTConfig(BaseSettings):
    rpc: str = Field(..., env="RPC")  # type: ignore
    chain_id: int = Field(..., env="CHAIN_ID")  # type: ignore

    class Config:
        env_prefix = "BST_"
        case_sensitive = True


class SEPConfig(BaseSettings):
    rpc: str = Field(..., env="RPC")  # type: ignore
    chain_id: int = Field(..., env="CHAIN_ID")  # type: ignore

    class Config:
        env_prefix = "SEP_"
        case_sensitive = True


class HOLConfig(BaseSettings):
    rpc: str = Field(..., env="RPC")  # type: ignore
    chain_id: int = Field(..., env="CHAIN_ID")  # type: ignore

    class Config:
        env_prefix = "HOL_"
        case_sensitive = True


class TelegramConfig(BaseSettings):
    base_url: str = Field(default="https://api.telegram.org", env="BASE_URL")  # type: ignore
    bot_info: str = Field(..., env="BOT_INFO")  # type: ignore
    chat_id: str = Field(..., env="CHAT_ID")  # type: ignore
    thread_id: str = Field(..., env="THREAD_ID ")  # type: ignore

    class Config:
        env_prefix = "TELEGRAM_"
        case_sensitive = True


class ApplicationConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    environment: str = Field(..., env="ENV")  # type: ignore
    sa_shield_private_key: str = Field(..., env="SA_SHIELD_PRIVATE_KEY")  # type: ignore
    zex: ZexConfig = ZexConfig()  # type: ignore
    hol: HOLConfig = HOLConfig()  # type: ignore
    sep: SEPConfig = SEPConfig()  # type: ignore
    bst: BSTConfig = BSTConfig()  # type: ignore
    bitcoin: BitcoinConfig = BitcoinConfig()  # type: ignore
    withdrawer: WithdrawerConfig = WithdrawerConfig()  # type: ignore
    user_deposit: UserDepositConfig = UserDepositConfig()  # type: ignore
    sentry: SentryConfig = SentryConfig()  # type: ignore
    dkg: DKGConfig = DKGConfig()  # type: ignore
    mongo: MongoConfig = MongoConfig()  # type: ignore
    node_private_key: int = Field(..., env="NODE_PRIVATE_KEY")  # type: ignore
    evm_native_token_address: str = Web3.to_checksum_address("0x0000000000000000000000000000000000000000")
    batch_block_number_size: int = Field(default=5, env="BATCH_BLOCK_NUMBER_SIZE")  # type: ignore
    max_delay_per_block_batch: int = Field(default=3, env="MAX_DELAY_PER_BLOCK_BATCH")  # type: ignore
    sa_batch_block_number_size: int = Field(default=100, env="SA_BATCH_BLOCK_NUMBER_SIZE")  # type: ignore
    sa_transactions_batch_size: int = Field(default=2, env="SA_TRANSACTIONS_BATCH_SIZE")  # type: ignore
    telegram: TelegramConfig = TelegramConfig()  # type: ignore
    holder_private_key: str = Field(..., env="HOLDER_PRIVATE_KEY")  # type: ignore
    monitoring_bot_zex_user_id: int = Field(..., env="MONITORING_BOT_ZEX_USER_ID")  # type: ignore
    monitoring_bot_withdrawer_private_key: str = Field(..., env="MONITORING_BOT_WITHDRAWER_PRIVATE_KEY")  # type: ignore


app_settings = ApplicationConfig()  # type: ignore
