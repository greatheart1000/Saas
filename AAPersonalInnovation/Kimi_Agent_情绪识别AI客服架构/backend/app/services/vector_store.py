"""向量检索服务 - ChromaDB集成"""
import asyncio
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from app.core.config import settings
from app.models.schemas import Document


class VectorStore:
    """向量存储服务"""

    def __init__(self):
        self.client: Optional[chromadb.ClientAPI] = None
        self.collection: Optional[chromadb.Collection] = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化向量数据库"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            try:
                # 创建数据目录
                settings.data_dir.mkdir(parents=True, exist_ok=True)

                # 初始化Chroma客户端 (使用同步客户端)
                self.client = chromadb.Client(
                    settings=ChromaSettings(
                        is_persistent=True,
                        persist_directory=str(settings.chroma_persist_dir),
                        anonymized_telemetry=False,
                    )
                )

                # 获取或创建集合
                self.collection = await asyncio.to_thread(
                    self.client.get_or_create_collection,
                    name=settings.chroma_collection_name,
                    metadata={"hnsw:space": "cosine"},  # 使用余弦相似度
                )

                self._initialized = True
                logger.info(f"Vector store initialized: {settings.chroma_collection_name}")
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {e}")
                raise

    async def add_documents(
        self,
        documents: list[str],
        ids: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
        embeddings: Optional[list[list[float]]] = None,
    ) -> bool:
        """添加文档到向量库"""
        if not self._initialized:
            await self.initialize()

        try:
            kwargs = {
                "documents": documents,
                "ids": ids,
                "metadatas": metadatas,
            }

            # 如果提供了 embeddings，使用它们
            if embeddings is not None:
                kwargs["embeddings"] = embeddings

            await asyncio.to_thread(
                self.collection.add,
                **kwargs
            )
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[Document]:
        """向量相似度搜索"""
        if not self._initialized:
            await self.initialize()

        try:
            results = await asyncio.to_thread(
                self.collection.query,
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter,
            )

            documents = []
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0

                    # 将距离转换为相似度分数
                    score = 1.0 - distance

                    documents.append(
                        Document(
                            id=results["ids"][0][i] if results["ids"] else "",
                            content=doc,
                            metadata=metadata,
                            score=score,
                        )
                    )

            logger.info(f"Vector search returned {len(documents)} documents")
            return documents
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    async def delete_documents(self, ids: list[str]) -> bool:
        """删除文档"""
        if not self._initialized:
            await self.initialize()

        try:
            await asyncio.to_thread(self.collection.delete, ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    async def get_collection_count(self) -> int:
        """获取集合中的文档数量"""
        if not self._initialized:
            await self.initialize()

        try:
            count = await asyncio.to_thread(self.collection.count)
            return count
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            return 0

    async def clear_collection(self) -> bool:
        """清空集合"""
        if not self._initialized:
            await self.initialize()

        try:
            # 删除并重新创建集合
            await asyncio.to_thread(self.client.delete_collection, name=settings.chroma_collection_name)
            self.collection = await asyncio.to_thread(
                self.client.create_collection,
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Collection cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False

    async def close(self):
        """关闭连接"""
        if self.client:
            logger.info("Vector store closed")


# 全局向量存储实例
vector_store = VectorStore()


async def get_vector_store() -> VectorStore:
    """FastAPI依赖注入：获取向量存储"""
    await vector_store.initialize()
    return vector_store
