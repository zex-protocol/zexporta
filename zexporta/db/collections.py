import os

from pymongo import AsyncMongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")  # noqa: B904 FIXME

client = AsyncMongoClient(MONGO_URI)
db = client["transaction_database"]
