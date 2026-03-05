"""Redis客户端管理"""
import json
from typing import Any, Optional

from loguru import logger
from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings


class RedisClient:
    """Redis客户端"""

    def __init__(self):
        self.pool = ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=50,
        )
        self.client: Optional[Redis] = None

    async def connect(self):
        """连接Redis"""
        self.client = Redis(connection_pool=self.pool)
        try:
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """断开Redis连接"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.client:
            return None
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> bool:
        """设置缓存"""
        if not self.client:
            return False
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await self.client.set(key, serialized, ex=expire or settings.redis_ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查key是否存在"""
        if not self.client:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


# 全局Redis客户端
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """FastAPI依赖注入：获取Redis客户端"""
    return redis_client
