"""数据库操作服务"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.models.database import Conversation, Message, KnowledgeDocument, Base
from app.models.schemas import Message as MessageSchema


class DatabaseService:
    """数据库服务"""

    @staticmethod
    async def save_message(
        db: AsyncSession,
        message: MessageSchema
    ):
        """保存消息到数据库"""
        try:
            # 创建消息记录
            db_message = Message(
                id=message.id,
                conversation_id=message.id.split('_')[0] if '_' in message.id else f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
                created_at=datetime.now()
            )

            # 情绪信息
            if message.sentiment:
                db_message.sentiment_score = message.sentiment.score
                db_message.sentiment_level = message.sentiment.level
                db_message.sentiment_triggers = message.sentiment.triggers
                db_message.sentiment_keywords = message.sentiment.keywords

            # 意图信息（从metadata获取）
            if message.metadata:
                db_message.intent_type = message.metadata.get('intent')
                db_message.router_decision = message.metadata.get('router_decision')
                db_message.response_time = message.metadata.get('responseTime')

            db.add(db_message)
            await db.commit()

            logger.info(f"Message saved to database: {message.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_conversation_messages(
        db: AsyncSession,
        conversation_id: str,
        limit: int = 100
    ):
        """获取会话的所有消息（按时间顺序）"""
        try:
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.timestamp.asc())  # 按时间顺序
                .limit(limit)
            )
            messages = result.scalars().all()
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    @staticmethod
    async def get_recent_conversations(
        db: AsyncSession,
        time_range: str = "day",
        limit: int = 50
    ):
        """获取最近的会话列表

        Args:
            time_range: 时间范围 - day, week, month
            limit: 返回数量
        """
        try:
            # 计算时间范围
            time_map = {
                "day": timedelta(days=1),
                "week": timedelta(weeks=1),
                "month": timedelta(days=30)
            }
            time_delta = time_map.get(time_range, timedelta(days=1))
            start_time = datetime.now() - time_delta

            # 查询会话
            result = await db.execute(
                select(Conversation)
                .where(Conversation.created_at >= start_time)
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
            )
            conversations = result.scalars().all()

            return conversations
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []

    @staticmethod
    async def get_conversation_stats(
        db: AsyncSession,
        time_range: str = "day"
    ):
        """获取会话统计信息"""
        try:
            time_map = {
                "day": timedelta(days=1),
                "week": timedelta(weeks=1),
                "month": timedelta(days=30)
            }
            time_delta = time_map.get(time_range, timedelta(days=1))
            start_time = datetime.now() - time_delta

            # 总会话数
            total_result = await db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.created_at >= start_time)
            )
            total_conversations = total_result.scalar() or 0

            # 总消息数
            messages_result = await db.execute(
                select(func.count(Message.id))
                .where(Message.created_at >= start_time)
            )
            total_messages = messages_result.scalar() or 0

            # 转人工统计
            handoff_result = await db.execute(
                select(func.count(Conversation.id))
                .where(and_(
                    Conversation.created_at >= start_time,
                    Conversation.status == "handed_off"
                ))
            )
            handoff_count = handoff_result.scalar() or 0

            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "handoff_count": handoff_count,
                "handoff_rate": round(handoff_count / total_conversations * 100, 2) if total_conversations > 0 else 0
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "handoff_count": 0,
                "handoff_rate": 0
            }

    @staticmethod
    async def add_knowledge_document(
        db: AsyncSession,
        doc_id: str,
        title: str,
        content: str,
        category: str = None,
        tags: list = None,
        source: str = "manual"
    ):
        """添加知识文档"""
        try:
            doc = KnowledgeDocument(
                id=doc_id,
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                source=source,
                is_active=True
            )
            db.add(doc)
            await db.commit()
            logger.info(f"Knowledge document added: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def get_knowledge_documents(
        db: AsyncSession,
        category: str = None,
        is_active: bool = True,
        limit: int = 100
    ):
        """获取知识文档列表"""
        try:
            query = select(KnowledgeDocument).where(KnowledgeDocument.is_active == is_active)

            if category:
                query = query.where(KnowledgeDocument.category == category)

            query = query.order_by(KnowledgeDocument.created_at.desc()).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get knowledge: {e}")
            return []

    @staticmethod
    async def update_knowledge_document(
        db: AsyncSession,
        doc_id: str,
        title: str = None,
        content: str = None,
        category: str = None,
        tags: list = None
    ):
        """更新知识文档"""
        try:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
            )
            doc = result.scalar_one_or_none()

            if not doc:
                return False

            if title is not None:
                doc.title = title
            if content is not None:
                doc.content = content
            if category is not None:
                doc.category = category
            if tags is not None:
                doc.tags = tags

            doc.updated_at = datetime.now()
            await db.commit()
            logger.info(f"Knowledge document updated: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update knowledge: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def delete_knowledge_document(
        db: AsyncSession,
        doc_id: str
    ):
        """删除知识文档（软删除）"""
        try:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
            )
            doc = result.scalar_one_or_none()

            if not doc:
                return False

            doc.is_active = False
            doc.updated_at = datetime.now()
            await db.commit()
            logger.info(f"Knowledge document deleted: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete knowledge: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def search_knowledge_documents(
        db: AsyncSession,
        keyword: str,
        limit: int = 20
    ):
        """搜索知识文档"""
        try:
            result = await db.execute(
                select(KnowledgeDocument)
                .where(
                    and_(
                        KnowledgeDocument.is_active == True,
                        (KnowledgeDocument.title.contains(keyword)) |
                        (KnowledgeDocument.content.contains(keyword))
                    )
                )
                .order_by(KnowledgeDocument.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []


# 全局数据库服务实例
database_service = DatabaseService()
