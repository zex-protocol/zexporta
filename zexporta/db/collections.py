import os

from pymongo import AsyncMongoClient

MONGO_URI = os.getenv(
    "MONGO_URI", "mongodb://mongodb:27017/"
)  # FIXME: due to circular import, We must move this config to configs in future

client = AsyncMongoClient(MONGO_URI)
db = client["transaction_database"]
