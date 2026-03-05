"""使用 ModelScope 加载国产 BGE Embedding 模型"""
import os
from functools import lru_cache
from typing import Any

from loguru import logger

from app.core.config import settings


class ModelScopeEmbedding:
    """使用 ModelScope 加载国产 BGE 模型"""

    def __init__(self):
        self.model = None
        self.device: str = settings.embedding_device
        # ModelScope 上的 BGE 模型 ID
        self.model_name = "Xorbits/bge-large-zh-v1.5"  # 中文 BGE 模型
        self._initialized = False
        self._load_failed = False

    async def initialize(self):
        """初始化模型"""
        if self._initialized or self._load_failed:
            return

        try:
            logger.info(f"Loading BGE model from ModelScope: {self.model_name}")

            # 动态导入 (避免未安装 modelscope 时报错)
            from sentence_transformers import SentenceTransformer

            # 设置 ModelScope 镜像
            os.environ["HF_ENDPOINT"] = "https://modelscope.cn/api"

            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                trust_remote_code=True,
            )

            # 测试模型
            test_embedding = self.model.encode("测试", show_progress_bar=False)
            logger.info(
                f"✓ BGE model loaded from ModelScope! "
                f"Dimension: {len(test_embedding)}, Device: {self.device}"
            )

            self._initialized = True

        except ImportError:
            logger.warning("ModelScope not installed. Installing...")
            logger.info("Run: pip install modelscope")
            self._load_failed = True
            raise

        except Exception as e:
            logger.error(f"Failed to load BGE model from ModelScope: {e}")
            self._load_failed = True
            raise

    def encode(
        self,
        text: str,
        normalize: bool = True,
    ) -> list[float]:
        """编码单条文本"""
        if not self.model:
            raise RuntimeError("ModelScope embedding model not initialized")

        try:
            # BGE 中文模型推荐指令
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
        batch_size: int = 32,
    ) -> list[list[float]]:
        """批量编码文本"""
        if not self.model:
            raise RuntimeError("ModelScope embedding model not initialized")

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
                batch_size=batch_size,
                show_progress_bar=False,
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Failed to encode batch: {e}")
            raise


# 全局实例
modelscope_embedding = ModelScopeEmbedding()
