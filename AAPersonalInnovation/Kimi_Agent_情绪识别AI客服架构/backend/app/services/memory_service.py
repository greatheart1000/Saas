"""记忆管理服务 - 短期/长期记忆、会话总结"""
from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_client
from app.models.schemas import ConversationSummary, Memory, Message


class MemoryService:
    """记忆管理服务"""

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        """初始化记忆服务"""
        if self._initialized:
            return

        await llm_service.initialize()
        self._initialized = True
        logger.info("Memory service initialized")

    async def get_short_term_memory(
        self, session_id: str, limit: Optional[int] = None
    ) -> list[Message]:
        """获取短期记忆（最近的消息）"""
        limit = limit or settings.memory_short_term_limit

        # 先从Redis缓存获取
        cache_key = f"short_term_memory:{session_id}"
        cached = await redis_client.get(cache_key)

        if cached:
            messages = [Message(**msg) for msg in cached]
            return messages[-limit:]

        return []

    async def update_short_term_memory(
        self, session_id: str, messages: list[Message]
    ) -> bool:
        """更新短期记忆"""
        try:
            # 只保留最近N条消息
            recent_messages = messages[-settings.memory_short_term_limit:]

            # 缓存到Redis（1小时过期）
            cache_key = f"short_term_memory:{session_id}"
            await redis_client.set(
                cache_key,
                [msg.model_dump() for msg in recent_messages],
                expire=3600,
            )

            logger.debug(f"Updated short-term memory for {session_id}: {len(recent_messages)} messages")
            return True
        except Exception as e:
            logger.error(f"Failed to update short-term memory: {e}")
            return False

    async def get_long_term_memory(
        self, session_id: str, user_id: Optional[str] = None
    ) -> dict[str, any]:
        """获取长期记忆"""
        memory_key = f"long_term_memory:{user_id or session_id}"
        cached = await redis_client.get(memory_key)

        if cached:
            return cached

        return {"key_facts": [], "user_preferences": {}, "conversation_summary": ""}

    async def update_long_term_memory(
        self,
        session_id: str,
        summary: str,
        key_facts: list[str],
        user_id: Optional[str] = None,
    ) -> bool:
        """更新长期记忆"""
        try:
            memory_key = f"long_term_memory:{user_id or session_id}"
            existing = await self.get_long_term_memory(session_id, user_id)

            # 合并关键事实（去重）
            all_facts = existing.get("key_facts", []) + key_facts
            unique_facts = list(set(all_facts))

            memory_data = {
                "key_facts": unique_facts[-settings.memory_long_term_limit:],
                "user_preferences": existing.get("user_preferences", {}),
                "conversation_summary": summary,
                "updated_at": datetime.now().isoformat(),
            }

            # 长期记忆缓存7天
            await redis_client.set(memory_key, memory_data, expire=604800)

            logger.info(f"Updated long-term memory for {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update long-term memory: {e}")
            return False

    async def should_summarize(self, session_id: str, message_count: int) -> bool:
        """判断是否需要进行对话总结"""
        # 获取当前总结的消息数
        cache_key = f"summary_count:{session_id}"
        last_count = await redis_client.get(cache_key)

        # 消息数超过阈值，或者距离上次总结又增加了阈值数量的消息
        return message_count >= settings.memory_summary_threshold or (
            last_count and (message_count - last_count) >= settings.memory_summary_threshold
        )

    async def summarize_conversation(
        self, session_id: str, messages: list[Message]
    ) -> ConversationSummary:
        """总结对话"""
        try:
            # 转换为LLM格式
            history = [
                {"role": msg.role, "content": msg.content} for msg in messages[-20:]
            ]

            # 使用LLM生成总结
            summary_text = await llm_service.summarize_conversation(history)

            # 提取关键事实
            key_facts = await self._extract_key_facts(messages)

            # 分析用户意图
            user_intent = await self._detect_user_intent(messages)

            # 分析情绪趋势
            sentiment_trend = self._analyze_sentiment_trend(messages)

            summary = ConversationSummary(
                session_id=session_id,
                summary=summary_text,
                key_facts=key_facts,
                user_intent=user_intent,
                sentiment_trend=sentiment_trend,
                message_count=len(messages),
                created_at=datetime.now(),
            )

            # 更新计数
            cache_key = f"summary_count:{session_id}"
            await redis_client.set(cache_key, len(messages), expire=86400)

            logger.info(f"Generated summary for {session_id}: {len(messages)} messages")
            return summary
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            # 返回简单的总结
            return ConversationSummary(
                session_id=session_id,
                summary=f"用户进行了{len(messages)}轮对话",
                key_facts=[],
                user_intent="unknown",
                sentiment_trend="unknown",
                message_count=len(messages),
                created_at=datetime.now(),
            )

    async def _extract_key_facts(self, messages: list[Message]) -> list[str]:
        """从对话中提取关键事实"""
        # 简单实现：提取用户消息中的关键信息
        # 生产环境可以使用LLM提取或使用信息抽取模型
        user_messages = [msg for msg in messages if msg.role == "user"]

        key_facts = []
        for msg in user_messages[-10:]:
            content = msg.content.lower()
            # 提取订单号
            import re

            order_numbers = re.findall(r'[oO][rR][dD][eE][rR][\s:#]*([a-zA-Z0-9]+)', content)
            if order_numbers:
                key_facts.append(f"订单号: {order_numbers[0]}")

            # 提取手机号
            phones = re.findall(r'1[3-9]\d{9}', content)
            if phones:
                key_facts.append(f"手机号: {phones[0]}")

            # 提取其他关键词
            if "退货" in content or "退款" in content:
                key_facts.append("需要退款/退货")

        return list(set(key_facts))[-10:]  # 最多10条

    async def _detect_user_intent(self, messages: list[Message]) -> str:
        """检测用户主要意图"""
        user_messages = [msg.content for msg in messages if msg.role == "user"]

        # 简单统计关键词
        from collections import Counter

        keywords = {
            "查询订单": ["订单", "查", "查询"],
            "物流问题": ["物流", "快递", "配送", "发货"],
            "退款退货": ["退款", "退货", "退钱"],
            "投诉": ["投诉", "不满", "差", "烂"],
            "技术问题": ["错误", "bug", "故障", "问题"],
        }

        intent_scores = Counter()
        for msg in user_messages[-5:]:
            for intent, words in keywords.items():
                if any(word in msg for word in words):
                    intent_scores[intent] += 1

        if intent_scores:
            return intent_scores.most_common(1)[0][0]
        return "一般咨询"

    def _analyze_sentiment_trend(self, messages: list[Message]) -> str:
        """分析情绪趋势"""
        sentiments = []
        for msg in messages[-10:]:
            if msg.sentiment:
                sentiments.append(msg.sentiment.score)

        if not sentiments:
            return "unknown"

        avg_sentiment = sum(sentiments) / len(sentiments)

        if avg_sentiment >= 0.7:
            return "严重不满"
        elif avg_sentiment >= 0.4:
            return "略显不耐烦"
        else:
            return "情绪平稳"

    async def retrieve_relevant_memory(
        self, session_id: str, query: str, user_id: Optional[str] = None
    ) -> str:
        """检索相关记忆"""
        try:
            # 获取长期记忆
            long_term = await self.get_long_term_memory(session_id, user_id)

            # 构建上下文
            context_parts = []

            if long_term.get("conversation_summary"):
                context_parts.append(f"历史对话摘要: {long_term['conversation_summary']}")

            if long_term.get("key_facts"):
                context_parts.append(f"关键信息: {', '.join(long_term['key_facts'][-5:])}")

            if long_term.get("user_preferences"):
                context_parts.append(f"用户偏好: {long_term['user_preferences']}")

            return "\n\n".join(context_parts) if context_parts else "暂无历史记录"
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return "暂无历史记录"

    async def clear_session_memory(self, session_id: str, user_id: Optional[str] = None):
        """清除会话记忆"""
        try:
            await redis_client.delete(f"short_term_memory:{session_id}")
            if user_id:
                await redis_client.delete(f"long_term_memory:{user_id}")
            logger.info(f"Cleared memory for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")


# 全局记忆服务实例
memory_service = MemoryService()


async def get_memory_service() -> MemoryService:
    """FastAPI依赖注入：获取记忆服务"""
    await memory_service.initialize()
    return memory_service


# 避免循环导入
from app.services.llm_service import llm_service
