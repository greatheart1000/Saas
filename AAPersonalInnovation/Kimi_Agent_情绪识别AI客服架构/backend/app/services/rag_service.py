"""RAG服务 - 混合检索和重排序"""
from typing import Optional

from loguru import logger

from app.core.config import settings
from app.core.redis import redis_client
from app.models.schemas import Document, RetrievalResult
from app.services.bm25_store import bm25_store
from app.services.llm_service import llm_service
from app.services.modelscope_embedding import modelscope_embedding
from app.services.vector_store import vector_store


class RAGService:
    """RAG检索增强生成服务"""

    def __init__(self):
        self._initialized = False
        self.embedding_service = None
        self.embedding_type = None

    async def initialize(self):
        """初始化RAG服务"""
        if self._initialized:
            return

        # 确保依赖服务已初始化
        await vector_store.initialize()
        await bm25_store.initialize()
        await llm_service.initialize()

        # 尝试初始化国产 BGE 模型 (通过 ModelScope)
        try:
            await modelscope_embedding.initialize()
            self.embedding_service = modelscope_embedding
            self.embedding_type = "modelscope"
            logger.info("✓ Using 国产 BGE model (via ModelScope)")
        except Exception as e:
            logger.warning(f"✗ Failed to load BGE model from ModelScope: {e}")
            logger.warning("Embedding service not available. Only BM25 search will work.")

        self._initialized = True
        logger.info("RAG service initialized")

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        alpha: Optional[float] = None,
    ) -> RetrievalResult:
        """混合检索：向量 + BM25"""
        if not self._initialized:
            await self.initialize()

        alpha = alpha or settings.rag_hybrid_alpha

        try:
            # 1. 获取查询向量
            if self.embedding_service:
                if self.embedding_type == "modelscope":
                    query_embedding = self.embedding_service.encode(query)
                else:
                    query_embedding = await self.embedding_service.encode(query)
            else:
                logger.warning("No embedding service available, using BM25 only")
                return await self.bm25_search(query, top_k)

            # 2. 向量检索
            vector_results = await vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # 获取更多候选用于重排
            )

            # 3. BM25检索
            bm25_results = await bm25_store.search(query=query, top_k=top_k * 2)

            # 4. 结果融合
            fused_results = self._fuse_results(
                vector_results=vector_results,
                bm25_results=bm25_results,
                alpha=alpha,
            )

            # 5. 取top-k
            final_results = sorted(fused_results, key=lambda x: x.score or 0, reverse=True)[
                :top_k
            ]

            # 6. 过滤低分结果
            filtered_results = [
                doc
                for doc in final_results
                if doc.score and doc.score >= settings.rag_score_threshold
            ]

            logger.info(
                f"Hybrid search: query='{query}', vector={len(vector_results)}, "
                f"bm25={len(bm25_results)}, final={len(filtered_results)}"
            )

            return RetrievalResult(
                documents=filtered_results,
                query=query,
                retrieval_method="hybrid",
                total_found=len(filtered_results),
            )
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return RetrievalResult(
                documents=[],
                query=query,
                retrieval_method="hybrid",
                total_found=0,
            )

    def _fuse_results(
        self,
        vector_results: list[Document],
        bm25_results: list[Document],
        alpha: float = 0.5,
    ) -> list[Document]:
        """融合向量检索和BM25检索结果"""
        # 使用文档ID去重
        fused_dict: dict[str, Document] = {}

        # 添加向量检索结果
        for doc in vector_results:
            if doc.id:
                fused_dict[doc.id] = Document(
                    id=doc.id,
                    content=doc.content,
                    metadata=doc.metadata,
                    score=(doc.score or 0) * alpha,
                )

        # 融合BM25结果
        for doc in bm25_results:
            if doc.id:
                if doc.id in fused_dict:
                    # 文档已存在，融合分数
                    existing = fused_dict[doc.id]
                    existing.score = (existing.score or 0) + (doc.score or 0) * (
                        1 - alpha
                    )
                else:
                    # 新文档
                    fused_dict[doc.id] = Document(
                        id=doc.id,
                        content=doc.content,
                        metadata=doc.metadata,
                        score=(doc.score or 0) * (1 - alpha),
                    )

        return list(fused_dict.values())

    async def vector_search(self, query: str, top_k: int = 5) -> RetrievalResult:
        """纯向量检索"""
        if not self._initialized:
            await self.initialize()

        try:
            if not self.embedding_service:
                logger.warning("No embedding service available")
                return RetrievalResult(
                    documents=[],
                    query=query,
                    retrieval_method="vector",
                    total_found=0,
                )

            # 获取查询向量
            if self.embedding_type == "modelscope":
                query_embedding = self.embedding_service.encode(query)
            else:
                query_embedding = await self.embedding_service.encode(query)

            results = await vector_store.search(query_embedding=query_embedding, top_k=top_k)

            return RetrievalResult(
                documents=results,
                query=query,
                retrieval_method="vector",
                total_found=len(results),
            )
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return RetrievalResult(
                documents=[],
                query=query,
                retrieval_method="vector",
                total_found=0,
            )

    async def bm25_search(self, query: str, top_k: int = 5) -> RetrievalResult:
        """纯BM25检索"""
        if not self._initialized:
            await self.initialize()

        try:
            results = await bm25_store.search(query=query, top_k=top_k)

            return RetrievalResult(
                documents=results,
                query=query,
                retrieval_method="bm25",
                total_found=len(results),
            )
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
            return RetrievalResult(
                documents=[],
                query=query,
                retrieval_method="bm25",
                total_found=0,
            )

    async def retrieve_with_rerank(
        self,
        query: str,
        top_k: int = 5,
        rerank: bool = True,
    ) -> RetrievalResult:
        """带重排序的检索"""
        # 先进行混合检索
        result = await self.hybrid_search(query, top_k=top_k * 3 if rerank else top_k)

        if not rerank or len(result.documents) == 0:
            return result

        # TODO: 实现重排序（需要额外的reranker模型）
        # 这里暂时使用简单的相关性评分

        return result

    async def format_context(self, documents: list[Document]) -> str:
        """格式化检索结果为上下文"""
        if not documents:
            return "抱歉，没有找到相关信息。"

        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[信息{i}] {doc.content}")

        return "\n\n".join(context_parts)

    async def add_knowledge(
        self,
        texts: list[str],
        ids: list[str],
        metadatas: Optional[list[dict]] = None,
    ) -> bool:
        """添加知识到向量库和BM25索引"""
        if not self._initialized:
            await self.initialize()

        try:
            # 1. 生成 embeddings (如果有可用的 embedding service)
            embeddings = None
            if self.embedding_service:
                try:
                    if self.embedding_type == "modelscope":
                        embeddings = self.embedding_service.encode_batch(texts)
                    else:
                        embeddings = await self.embedding_service.encode_batch(texts)
                except Exception as e:
                    logger.warning(f"Failed to generate embeddings: {e}. Using BM25 only.")

            # 2. 添加到向量库 (仅当有 embeddings 时)
            if embeddings is not None:
                try:
                    await vector_store.add_documents(texts, ids, metadatas, embeddings)
                except Exception as e:
                    logger.warning(f"Failed to add to vector store: {e}. Using BM25 only.")
            else:
                logger.info("Skipping vector store (no embeddings available)")

            # 3. 添加到BM25索引 (总是可用)
            documents = [
                Document(id=id_, content=text, metadata=metadata or {})
                for id_, text, metadata in zip(ids, texts, metadatas or [{}] * len(texts))
            ]
            await bm25_store.add_documents(documents)

            # 2. 添加到BM25索引
            documents = [
                Document(id=id_, content=text, metadata=metadata or {})
                for id_, text, metadata in zip(ids, texts, metadatas or [{}] * len(texts))
            ]
            await bm25_store.add_documents(documents)

            # 3. 清除缓存
            cache_key = f"rag_cache:{hash(tuple(texts))}"
            await redis_client.delete(cache_key)

            logger.info(f"Added {len(texts)} documents to knowledge base")
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return False

    async def clear_knowledge_base(self) -> bool:
        """清空知识库"""
        try:
            await vector_store.clear_collection()
            await bm25_store.clear()

            # 清除所有缓存
            # await redis_client.delete("bm25_index")

            logger.info("Knowledge base cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return False


# 全局RAG服务实例
rag_service = RAGService()


async def get_rag_service() -> RAGService:
    """FastAPI依赖注入：获取RAG服务"""
    await rag_service.initialize()
    return rag_service
