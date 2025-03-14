from functools import lru_cache

import pymongo

from zexporta.settings import app_settings


@lru_cache()
def get_db_connection():
    client = pymongo.AsyncMongoClient(app_settings.mongo.get_uri())
    return client[app_settings.mongo.db_name]
