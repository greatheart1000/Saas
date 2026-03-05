"""监控Dashboard API"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        from app.services.vector_store import vector_store
        from app.services.bm25_store import bm25_store
        from app.core.redis import redis_client

        # 获取知识库统计
        vector_count = await vector_store.get_collection_count()
        bm25_count = await bm25_store.get_document_count()

        # 简化实现：返回基本统计
        # 生产环境应该从数据库获取真实的会话统计
        stats = {
            "knowledge_base": {
                "vector_documents": vector_count,
                "bm25_documents": bm25_count,
                "total_documents": max(vector_count, bm25_count),
            },
            "system": {
                "status": "healthy",
                "uptime_hours": 1.0,  # 简化实现
                "llm_provider": "kimi",  # 从配置获取
            },
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-sessions")
async def get_recent_sessions(limit: int = 20, offset: int = 0):
    """获取最近的会话列表"""
    try:
        from app.core.redis import redis_client

        # 简化实现：从Redis获取会话列表
        # 生产环境应该从数据库查询

        # 获取所有短期记忆的key
        # 这里返回模拟数据
        sessions = []

        # 尝试从Redis获取真实数据
        cache_key = f"recent_sessions_list"
        cached = await redis_client.get(cache_key)

        if cached:
            sessions = cached
        else:
            # 返回空列表
            sessions = []

        return {
            "sessions": sessions[offset:offset + limit],
            "total": len(sessions),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error getting recent sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_detail(session_id: str):
    """获取会话详情"""
    try:
        from app.services.memory_service import memory_service

        # 获取会话消息
        messages = await memory_service.get_short_term_memory(session_id)

        # 获取会话摘要
        try:
            summary = await memory_service.summarize_conversation(session_id, messages)
        except:
            summary = None

        # 统计信息
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]

        # 情绪统计
        sentiment_levels = {}
        for msg in user_messages:
            if msg.sentiment:
                level = msg.sentiment.level
                sentiment_levels[level] = sentiment_levels.get(level, 0) + 1

        return {
            "session_id": session_id,
            "message_count": len(messages),
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
            "sentiment_distribution": sentiment_levels,
            "messages": [msg.model_dump() for msg in messages],
            "summary": summary.model_dump() if summary else None,
        }

    except Exception as e:
        logger.error(f"Error getting session detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics(
    start_date: str | None = None,
    end_date: str | None = None,
):
    """获取指标数据"""
    try:
        # 简化实现：返回模拟数据
        # 生产环境应该从数据库或时序数据库查询真实指标

        import random

        metrics = {
            "total_sessions": random.randint(50, 200),
            "total_messages": random.randint(500, 2000),
            "avg_session_length": random.randint(3, 15),
            "handoff_rate": round(random.uniform(0.05, 0.2), 2),
            "avg_response_time": round(random.uniform(0.5, 2.0), 2),
            "sentiment_distribution": {
                "normal": random.randint(60, 80),
                "warning": random.randint(15, 30),
                "critical": random.randint(2, 10),
            },
            "intent_distribution": {
                "query": random.randint(30, 50),
                "order_related": random.randint(15, 25),
                "shipping_related": random.randint(10, 20),
                "refund_related": random.randint(5, 15),
                "complaint": random.randint(3, 10),
                "technical_issue": random.randint(2, 8),
                "handoff_request": random.randint(1, 5),
            },
        }

        return metrics

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        from app.services.memory_service import memory_service

        await memory_service.clear_session_memory(session_id)

        return {"message": "Session deleted", "session_id": session_id}

    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
