"""Jina AI 免费 Embedding 服务"""
from typing import Any

import httpx
from loguru import logger


class JinaEmbedding:
    """Jina AI 免费文本向量化服务"""

    def __init__(self):
        self.api_url = "https://api.jina.ai/v1/embeddings"
        self.model_name = "jina-embeddings-v3"
        self._initialized = False

    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return

        # Jina AI 免费API,无需key
        self._initialized = True
        logger.info("Jina AI embedding service initialized (free tier)")

    async def encode(self, text: str) -> list[float]:
        """编码单条文本"""
        if not self._initialized:
            await self.initialize()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    json={
                        "model": self.model_name,
                        "input": [text],
                        "encoding_type": "float",
                    },
                    headers={
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()

                data = response.json()
                return data["data"][0]["embedding"]

        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise

    async def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """批量编码文本"""
        if not self._initialized:
            await self.initialize()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    json={
                        "model": self.model_name,
                        "input": texts,
                        "encoding_type": "float",
                    },
                    headers={
                        "Content-Type": "application/json",
                    },
                )
                response.raise_for_status()

                data = response.json()
                return [item["embedding"] for item in data["data"]]

        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            raise


# 全局实例
jina_embedding = JinaEmbedding()
