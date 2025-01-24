from typing import Any

import redis


class RedisInterface:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,  # Automatically decode responses to str
        )

    def set_value(self, key: str, value: Any, expiry: int | None = None) -> bool:
        return bool(self.redis_client.set(key, value, ex=expiry))

    def get_value(self, key: str) -> Any:
        return self.redis_client.get(key)

    def delete_key(self, key: str) -> bool:
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError:
            return False


redis_interface = RedisInterface("redis")
