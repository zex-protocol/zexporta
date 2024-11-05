import os

from dotenv import load_dotenv

load_dotenv()


INFURA_KEY = os.environ["INFURA_KEY"]
USER_DEPOSIT_FACTORY_ADDRESS = os.environ["USER_DEPOSIT_FACTORY_ADDRESS"]
USER_DEPOSIT_BYTECODE_HASH = os.environ["USER_DEPOSIT_BYTECODE_HASH"]
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
