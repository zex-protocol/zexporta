from pymongo import AsyncMongoClient

from .config import MONGO_URI

client = AsyncMongoClient(MONGO_URI)
db = client["transaction_database"]
