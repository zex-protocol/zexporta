from functools import lru_cache

import pymongo

from .config import MONGO_DBNAME, MONGO_HOST, MONGO_PORT


@lru_cache()
def get_db_connection():
    client = pymongo.AsyncMongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
    return client[MONGO_DBNAME]
