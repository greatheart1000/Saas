"""本地 Embedding 服务 - 使用 sentence-transformers"""
# 必须在导入任何 transformers/sentence_transformers 之前设置
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_CACHE"] = str(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../models")))

from functools import lru_cache
from typing import Any

import torch
from loguru import logger
import sentence_transformers
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class LocalEmbedding:
    """本地文本向量化服务"""

    def __init__(self):
        self.model: SentenceTransformer | None = None
        self.device: str = settings.embedding_device
        self.model_name: str = "BAAI/bge-m3"
        self._initialized = False
        self._load_failed = False  # 标记是否加载失败

    async def initialize(self):
        """初始化模型"""
        if self._initialized or self._load_failed:
            return

        try:
            logger.info(f"Loading local embedding model: {self.model_name}")

            # 加载模型到指定设备 (使用镜像源)
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=True,
            )

            # 测试模型
            test_embedding = self.model.encode("测试", show_progress_bar=False)
            logger.info(
                f"Local embedding model loaded successfully. "
                f"Dimension: {len(test_embedding)}, Device: {self.device}"
            )

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to load local embedding model: {e}")
            self._load_failed = True
            raise  # 抛出异常,让调用方使用备选方案

    def encode(
        self,
        text: str,
        normalize: bool = True,
    ) -> list[float]:
        """编码单条文本"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        try:
            # BGE-M3 推荐的指令前缀
            if normalize:
                text = f"为这个句子生成表示以用于检索相关文章：{text}"

            embedding = self.model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=False,
            )

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise

    def encode_batch(
        self,
        texts: list[str],
        normalize: bool = True,
        batch_size: int | None = None,
    ) -> list[list[float]]:
        """批量编码文本"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        try:
            # 添加指令前缀
            if normalize:
                texts = [
                    f"为这个句子生成表示以用于检索相关文章：{t}"
                    for t in texts
                ]

            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                batch_size=batch_size or settings.embedding_batch_size,
                show_progress_bar=False,
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            raise

    def get_dimension(self) -> int:
        """获取向量维度"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")

        return self.model.get_sentence_embedding_dimension()


# 全局实例
local_embedding = LocalEmbedding()


@lru_cache
def get_local_embedding() -> LocalEmbedding:
    """获取本地 embedding 服务单例"""
    return local_embedding
