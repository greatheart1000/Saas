"""监控API - 增强版（支持MySQL持久化）"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.database_service import database_service
from loguru import logger

router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.get("/stats")
async def get_system_stats(
    time_range: str = Query(default="day", description="时间范围: day, week, month"),
    db: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    try:
        stats = await database_service.get_conversation_stats(
            db=db,
            time_range=time_range
        )

        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_recent_conversations(
    time_range: str = Query(default="day", description="时间范围: day, week, month"),
    limit: int = Query(default=50, description="返回数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取最近的会话列表"""
    try:
        conversations = await database_service.get_recent_conversations(
            db=db,
            time_range=time_range,
            limit=limit
        )

        return {
            "sessions": [
                {
                    "id": conv.id,
                    "user_id": conv.user_id,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    "message_count": conv.message_count or 0,
                    "user_message_count": conv.user_message_count or 0,
                    "assistant_message_count": conv.assistant_message_count or 0,
                    "status": conv.status,
                    "persona": conv.persona,
                    "summary": conv.summary,
                    "sentiment_trend": conv.sentiment_trend
                }
                for conv in conversations
            ],
            "total": len(conversations)
        }
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情"""
    try:
        # 获取会话消息
        messages = await database_service.get_conversation_messages(
            db=db,
            conversation_id=session_id,
            limit=100
        )

        if not messages:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 统计信息
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]

        # 情绪统计
        sentiment_levels = {}
        for msg in user_messages:
            level = msg.sentiment_level or "normal"
            sentiment_levels[level] = sentiment_levels.get(level, 0) + 1

        # 获取会话信息
        from sqlalchemy import select
        from app.models.database import Conversation

        result = await db.execute(
            select(Conversation).where(Conversation.id == session_id)
        )
        conv = result.scalar_one_or_none()

        return {
            "session_id": session_id,
            "user_id": conv.user_id if conv else None,
            "created_at": conv.created_at.isoformat() if conv and conv.created_at else None,
            "message_count": len(messages),
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
            "sentiment_distribution": sentiment_levels,
            "status": conv.status if conv else "active",
            "persona": conv.persona if conv else None,
            "summary": conv.summary if conv else None,
            "key_facts": conv.key_facts if conv else [],
            "user_intent": conv.user_intent if conv else None,
            "sentiment_trend": conv.sentiment_trend if conv else None,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "sentiment": {
                        "score": msg.sentiment_score,
                        "level": msg.sentiment_level,
                        "triggers": msg.sentiment_triggers,
                        "keywords": msg.sentiment_keywords
                    } if msg.sentiment_score else None,
                    "intent": {
                        "type": msg.intent_type,
                        "confidence": msg.intent_confidence
                    } if msg.intent_type else None,
                    "router_decision": msg.router_decision
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error getting session detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除会话"""
    try:
        from sqlalchemy import delete
        from app.models.database import Message, Conversation

        # 删除消息
        await db.execute(
            delete(Message).where(Message.conversation_id == session_id)
        )

        # 删除会话
        await db.execute(
            delete(Conversation).where(Conversation.id == session_id)
        )

        await db.commit()

        return {"message": "会话已删除", "session_id": session_id}

    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
