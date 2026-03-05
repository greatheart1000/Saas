"""知识库管理API"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from loguru import logger

from app.models.schemas import Document
from app.services.rag_service import rag_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/add")
async def add_knowledge(
    texts: list[str],
    ids: list[str] | None = None,
    metadatas: list[dict] | None = None,
):
    """添加知识到知识库"""
    try:
        await rag_service.initialize()

        if ids is None:
            ids = [f"doc_{int(datetime.now().timestamp() * 1000)}_{i}" for i in range(len(texts))]

        success = await rag_service.add_knowledge(texts, ids, metadatas)

        if success:
            return {
                "message": f"Successfully added {len(texts)} documents to knowledge base",
                "count": len(texts),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add documents")

    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库"""
    try:
        # 读取文件内容
        content = await file.read()

        # 根据文件类型处理
        if file.filename.endswith(".txt"):
            text = content.decode("utf-8")
        elif file.filename.endswith(".pdf"):
            # 这里需要添加PDF解析逻辑
            text = "PDF解析功能待实现"
        elif file.filename.endswith(".md"):
            text = content.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # 添加到知识库
        await rag_service.initialize()
        doc_id = f"doc_{file.filename}"
        success = await rag_service.add_knowledge(
            texts=[text],
            ids=[doc_id],
            metadatas=[{"filename": file.filename, "uploaded_at": datetime.now().isoformat()}],
        )

        if success:
            return {
                "message": "Document uploaded successfully",
                "doc_id": doc_id,
                "filename": file.filename,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to upload document")

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_knowledge(query: str, top_k: int = 5, method: str = "hybrid"):
    """搜索知识库"""
    try:
        await rag_service.initialize()

        if method == "hybrid":
            result = await rag_service.hybrid_search(query, top_k=top_k)
        elif method == "vector":
            result = await rag_service.vector_search(query, top_k=top_k)
        elif method == "bm25":
            result = await rag_service.bm25_search(query, top_k=top_k)
        else:
            raise HTTPException(status_code=400, detail="Invalid search method")

        return {
            "query": query,
            "method": method,
            "documents": [doc.model_dump() for doc in result.documents],
            "total_found": result.total_found,
        }

    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_knowledge_base():
    """清空知识库"""
    try:
        await rag_service.initialize()
        success = await rag_service.clear_knowledge_base()

        if success:
            return {"message": "Knowledge base cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear knowledge base")

    except Exception as e:
        logger.error(f"Error clearing knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_knowledge_stats():
    """获取知识库统计信息"""
    try:
        from app.services.vector_store import vector_store
        from app.services.bm25_store import bm25_store

        await rag_service.initialize()

        vector_count = await vector_store.get_collection_count()
        bm25_count = await bm25_store.get_document_count()

        return {
            "vector_documents": vector_count,
            "bm25_documents": bm25_count,
            "total_documents": max(vector_count, bm25_count),
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 避免循环导入
from datetime import datetime
