"""知识库管理API - 增删改查"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.models.database import KnowledgeDocument
from app.services.database_service import database_service
from loguru import logger

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeAdd(BaseModel):
    """添加知识请求"""
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = []


class KnowledgeUpdate(BaseModel):
    """更新知识请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/list")
async def list_knowledge(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取知识文档列表"""
    try:
        documents = await database_service.get_knowledge_documents(
            db=db,
            category=category,
            is_active=True,
            limit=100
        )

        return {
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content,
                    "category": doc.category,
                    "tags": doc.tags or [],
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                    "view_count": doc.view_count or 0,
                    "use_count": doc.use_count or 0
                }
                for doc in documents
            ],
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Error listing knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_knowledge(
    data: KnowledgeAdd,
    db: AsyncSession = Depends(get_db)
):
    """添加知识文档"""
    try:
        doc_id = f"kb_{uuid.uuid4().hex[:8]}"

        success = await database_service.add_knowledge_document(
            db=db,
            doc_id=doc_id,
            title=data.title,
            content=data.content,
            category=data.category,
            tags=data.tags or [],
            source="manual"
        )

        if success:
            return {
                "message": "知识文档添加成功",
                "id": doc_id
            }
        else:
            raise HTTPException(status_code=500, detail="添加失败")

    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update/{doc_id}")
async def update_knowledge(
    doc_id: str,
    data: KnowledgeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新知识文档"""
    try:
        success = await database_service.update_knowledge_document(
            db=db,
            doc_id=doc_id,
            title=data.title,
            content=data.content,
            category=data.category,
            tags=data.tags
        )

        if success:
            return {"message": "更新成功", "id": doc_id}
        else:
            raise HTTPException(status_code=404, detail="文档不存在")

    except Exception as e:
        logger.error(f"Error updating knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{doc_id}")
async def delete_knowledge(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除知识文档（软删除）"""
    try:
        success = await database_service.delete_knowledge_document(
            db=db,
            doc_id=doc_id
        )

        if success:
            return {"message": "删除成功", "id": doc_id}
        else:
            raise HTTPException(status_code=404, detail="文档不存在")

    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_knowledge(
    keyword: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """搜索知识文档"""
    try:
        if category:
            # 先按分类筛选，再搜索
            docs = await database_service.get_knowledge_documents(
                db=db,
                category=category,
                is_active=True,
                limit=100
            )
            # 在结果中搜索关键词
            filtered = [
                doc for doc in docs
                if keyword.lower() in doc.title.lower() or keyword.lower() in doc.content.lower()
            ]
        else:
            docs = await database_service.search_knowledge_documents(
                db=db,
                keyword=keyword,
                limit=50
            )
            filtered = docs

        return {
            "keyword": keyword,
            "category": category,
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content,
                    "category": doc.category,
                    "tags": doc.tags or [],
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
                for doc in filtered
            ],
            "total": len(filtered)
        }
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_knowledge_stats(db: AsyncSession = Depends(get_db)):
    """获取知识库统计"""
    try:
        docs = await database_service.get_knowledge_documents(
            db=db,
            is_active=True,
            limit=1000
        )

        # 按分类统计
        category_stats = {}
        for doc in docs:
            cat = doc.category or "未分类"
            category_stats[cat] = category_stats.get(cat, 0) + 1

        return {
            "total": len(docs),
            "by_category": category_stats
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
