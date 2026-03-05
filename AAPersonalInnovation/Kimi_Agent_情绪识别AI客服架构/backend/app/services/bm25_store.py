"""BM25关键词检索服务"""
from collections import defaultdict
from typing import Optional

from loguru import logger
from rank_bm25 import BM25Okapi

from app.core.redis import redis_client
from app.models.schemas import Document


class BM25Store:
    """BM25检索服务"""

    def __init__(self):
        self.index: Optional[BM25Okapi] = None
        self.documents: dict[str, Document] = {}
        self.tokenized_docs: list[list[str]] = []
        self._initialized = False

    async def initialize(self):
        """初始化BM25索引"""
        if self._initialized:
            return

        # 尝试从Redis加载缓存
        cached_data = await redis_client.get("bm25_index")
        if cached_data:
            try:
                self.documents = {
                    k: Document(**v) if isinstance(v, dict) else v
                    for k, v in cached_data["documents"].items()
                }
                self.tokenized_docs = cached_data["tokenized_docs"]
                self.index = BM25Okapi(self.tokenized_docs)
                self._initialized = True
                logger.info("BM25 index loaded from cache")
                return
            except Exception as e:
                logger.warning(f"Failed to load BM25 from cache: {e}")

        self._initialized = True
        logger.info("BM25 store initialized")

    def _tokenize(self, text: str) -> list[str]:
        """简单的中文分词"""
        # 简单的按字符和空格分词，生产环境建议使用jieba
        import re

        # 移除标点符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        # 分词
        tokens = [t for t in text.split() if len(t) > 1]
        # 也添加单个字符（针对中文）
        chars = [c for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff']
        return tokens + chars

    async def add_documents(self, documents: list[Document]) -> bool:
        """添加文档到索引"""
        try:
            for doc in documents:
                if doc.id not in self.documents:
                    self.documents[doc.id] = doc
                    tokenized = self._tokenize(doc.content)
                    self.tokenized_docs.append(tokenized)

            # 重建索引
            self.index = BM25Okapi(self.tokenized_docs)

            # 缓存到Redis
            cache_data = {
                "documents": {k: v.model_dump() for k, v in self.documents.items()},
                "tokenized_docs": self.tokenized_docs,
            }
            await redis_client.set("bm25_index", cache_data, expire=86400)  # 24小时

            logger.info(f"Added {len(documents)} documents to BM25 index")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents to BM25: {e}")
            return False

    async def search(self, query: str, top_k: int = 5) -> list[Document]:
        """BM25搜索"""
        if not self._initialized:
            await self.initialize()

        if not self.index or len(self.tokenized_docs) == 0:
            logger.warning("BM25 index is empty")
            return []

        try:
            tokenized_query = self._tokenize(query)
            scores = self.index.get_scores(tokenized_query)

            # 获取top-k结果的索引
            import numpy as np

            top_indices = np.argsort(scores)[::-1][:top_k]

            results = []
            for idx in top_indices:
                if idx < len(self.tokenized_docs):
                    doc_id = list(self.documents.keys())[idx]
                    doc = self.documents[doc_id]
                    # 归一化分数
                    doc.score = float(min(scores[idx] / max(scores), 1.0)) if max(scores) > 0 else 0.0
                    results.append(doc)

            logger.info(f"BM25 search returned {len(results)} documents")
            return results
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id not in self.documents:
            return False

        try:
            del self.documents[doc_id]
            # 重建索引
            self.tokenized_docs = []
            for doc in self.documents.values():
                self.tokenized_docs.append(self._tokenize(doc.content))
            self.index = BM25Okapi(self.tokenized_docs)

            # 更新缓存
            cache_data = {
                "documents": {k: v.model_dump() for k, v in self.documents.items()},
                "tokenized_docs": self.tokenized_docs,
            }
            await redis_client.set("bm25_index", cache_data, expire=86400)

            logger.info(f"Deleted document {doc_id} from BM25 index")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    async def get_document_count(self) -> int:
        """获取文档数量"""
        return len(self.documents)

    async def clear(self) -> bool:
        """清空索引"""
        try:
            self.documents = {}
            self.tokenized_docs = []
            self.index = None
            await redis_client.delete("bm25_index")
            logger.info("BM25 index cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear BM25 index: {e}")
            return False


# 全局BM25存储实例
bm25_store = BM25Store()


async def get_bm25_store() -> BM25Store:
    """FastAPI依赖注入：获取BM25存储"""
    await bm25_store.initialize()
    return bm25_store
