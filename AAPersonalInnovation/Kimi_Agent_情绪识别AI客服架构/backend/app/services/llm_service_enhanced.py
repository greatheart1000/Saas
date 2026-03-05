"""LLM服务 - 增强版（集成上下文窗口和Persona）"""
from typing import Any, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from loguru import logger
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.persona import (
    PersonaType,
    adapt_response_to_persona,
    format_persona_prompt,
    get_persona,
)


class LLMService:
    """LLM服务类 - 增强版"""

    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.langchain_llm: Optional[ChatOpenAI] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self._initialized = False

    async def initialize(self):
        """初始化LLM客户端"""
        if self._initialized:
            return

        try:
            # 初始化OpenAI客户端
            self.client = AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )

            # 初始化LangChain LLM
            self.langchain_llm = ChatOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                temperature=0.7,
                max_tokens=2000,
                timeout=settings.agent_timeout,
            )

            # 初始化Embeddings
            self.embeddings = OpenAIEmbeddings(
                api_key=settings.embedding_api_key,
                base_url=settings.embedding_base_url,
                model=settings.embedding_model_name,
            )

            self._initialized = True
            logger.info(f"LLM service initialized with provider: {settings.llm_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[dict[str, str]] = None,
    ) -> str:
        """聊天补全"""
        if not self.client:
            await self.initialize()

        try:
            kwargs: dict[str, Any] = {
                "model": settings.llm_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed_text(self, text: str) -> list[float]:
        """文本向量化"""
        if not self.embeddings:
            await self.initialize()

        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化"""
        if not self.embeddings:
            await self.initialize()

        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise

    async def detect_sentiment(
        self,
        message: str,
        history: list[dict],
        context_limit: Optional[int] = None
    ) -> dict:
        """使用LLM检测情绪

        Args:
            message: 用户消息
            history: 对话历史
            context_limit: 上下文窗口大小（None则使用配置默认值）
        """
        # 使用配置的上下文窗口大小
        limit = context_limit or settings.context_sentiment_limit

        system_prompt = """你是一个情绪分析专家。分析用户消息的情绪状态。

返回JSON格式：
{
    "score": 0-1之间的浮点数，表示情绪强度（0=平静，1=极度愤怒/不满），
    "level": "normal" | "warning" | "critical",
    "triggers": ["触发因素1", "触发因素2"],
    "keywords": ["关键词1", "关键词2"],
    "confidence": 0-1之间的置信度
}

判断标准：
- normal (0-0.4): 情绪平稳，正常咨询
- warning (0.4-0.7): 情绪略显不耐烦或不满
- critical (0.7-1.0): 情绪严重不满，愤怒，需要立即处理

注意：
- 要结合对话历史进行综合判断
- 单条消息可能看不出情绪，需要看上下文
- 用户重复提问通常是情绪不耐烦的信号"""

        messages = [
            {"role": "system", "content": system_prompt},
            *history[-limit:],  # 使用配置的上下文窗口
            {"role": "user", "content": message},
        ]

        response = await self.chat_completion(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        import json

        try:
            result = json.loads(response)
            logger.info(f"Sentiment analysis result (context={limit}): {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse sentiment response: {e}")
            # 返回默认值
            return {
                "score": 0.0,
                "level": "normal",
                "triggers": [],
                "keywords": [],
                "confidence": 0.5,
            }

    async def detect_intent(
        self,
        message: str,
        history: list[dict],
        context_limit: Optional[int] = None
    ) -> dict:
        """使用LLM识别意图

        Args:
            message: 用户消息
            history: 对话历史
            context_limit: 上下文窗口大小
        """
        limit = context_limit or settings.context_intent_limit

        system_prompt = """你是一个意图识别专家。识别用户消息的意图类型。

返回JSON格式：
{
    "type": "意图类型",
    "confidence": 0-1之间的置信度,
    "entities": {"实体名": "实体值"}
}

意图类型包括：
- greeting: 问候/打招呼
- handoff_request: 明确要求转人工
- query: 一般性查询
- complaint: 投诉/不满
- order_related: 订单相关问题
- shipping_related: 物流相关问题
- refund_related: 退款相关问题
- technical_issue: 技术问题
- unknown: 未知意图

重要：
- 要结合对话历史判断用户的真实意图
- 用户可能换种说法表达相同意图
- 识别关键实体（订单号、商品名等）"""

        messages = [
            {"role": "system", "content": system_prompt},
            *history[-limit:],
            {"role": "user", "content": message},
        ]

        response = await self.chat_completion(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        import json

        try:
            result = json.loads(response)
            logger.info(f"Intent detection result (context={limit}): {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent response: {e}")
            return {
                "type": "unknown",
                "confidence": 0.5,
                "entities": {},
            }

    async def should_handoff(
        self,
        message: str,
        sentiment: dict,
        intent: dict,
        history: list[dict],
    ) -> dict:
        """使用LLM判断是否需要转人工"""
        system_prompt = """你是一个客服路由专家。判断当前情况是否需要转接人工客服。

返回JSON格式：
{
    "should_handoff": true/false,
    "reason": "详细原因",
    "confidence": 0-1之间的置信度,
    "priority": 1/2/3 (1=最高优先级，2=中等，3=普通)
}

判断标准：
1. 用户明确要求转人工 → should_handoff=true, priority=1
2. 情绪严重不满（score>0.7）→ should_handoff=true, priority=1
3. 问题复杂度超过AI能力 → should_handoff=true, priority=2
4. 用户重复提问3次以上 → should_handoff=true, priority=2
5. 一般性查询，AI可以处理 → should_handoff=false, priority=3

考虑因素：
- 用户情绪状态
- 问题复杂度
- AI解决能力
- 历史对话情况"""

        context = f"""当前消息：{message}
情绪分析：{sentiment}
意图识别：{intent}
历史对话轮数：{len([m for m in history if m['role'] == 'user'])}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ]

        response = await self.chat_completion(
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        import json

        try:
            result = json.loads(response)
            logger.info(f"Handoff decision result: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse handoff response: {e}")
            return {
                "should_handoff": False,
                "reason": "判断失败，继续AI处理",
                "confidence": 0.5,
                "priority": 3,
            }

    async def generate_response(
        self,
        query: str,
        context: str,
        sentiment: dict,
        intent: dict,
        history: list[dict],
        persona_type: Optional[PersonaType] = None,
        context_limit: Optional[int] = None,
    ) -> str:
        """基于RAG生成回复

        Args:
            query: 用户查询
            context: 检索到的知识上下文
            sentiment: 情绪分析结果
            intent: 意图识别结果
            history: 对话历史
            persona_type: Persona类型（None则使用默认）
            context_limit: 上下文窗口大小
        """
        # 使用配置的上下文窗口
        limit = context_limit or settings.context_response_limit

        # 获取Persona
        if settings.persona_enabled:
            persona_type = persona_type or settings.default_persona
            persona = get_persona(persona_type)
        else:
            persona = None

        # 基础系统提示
        base_system_prompt = f"""你是一个专业的AI客服助手。你的职责是为用户提供友好、准确、富有同理心的回复。

回复原则：
1. 如果情绪critical，使用安抚性语言，表达理解和歉意
2. 如果情绪warning，使用温和友好的语言
3. 如果情绪normal，使用标准专业语言
4. 优先使用提供的知识库内容回答问题
5. 回复要简洁、准确、有帮助
6. 避免机械化的模板回复

当前用户情绪：{sentiment.get('level', 'normal')}
用户意图：{intent.get('type', 'unknown')}

知识库内容：
{context}

请基于以上信息生成回复。"""

        # 应用Persona
        if persona:
            system_prompt = format_persona_prompt(persona_type, base_system_prompt)
        else:
            system_prompt = base_system_prompt

        messages = [
            {"role": "system", "content": system_prompt},
            *history[-limit:],
            {"role": "user", "content": query},
        ]

        response = await self.chat_completion(messages=messages, temperature=0.7)

        # 根据Persona调整回复
        if persona and settings.persona_enabled:
            response = adapt_response_to_persona(response, persona_type)

        return response

    async def summarize_conversation(
        self,
        messages: list[dict],
        context_limit: Optional[int] = None
    ) -> str:
        """总结对话内容

        Args:
            messages: 对话消息列表
            context_limit: 上下文窗口大小
        """
        limit = context_limit or settings.context_summary_limit

        system_prompt = """你是一个对话总结专家。请将以下对话总结成简洁的摘要。

摘要应包含：
1. 用户的主要问题/需求
2. 涉及的关键信息（订单号、商品等）
3. 对话进展
4. 待解决问题（如果有）

摘要长度控制在100字以内。

如果对话较长，重点总结：
- 最新的问题和需求
- 是否已经解决
- 用户的情绪状态变化"""

        conversation = "\n".join(
            [f"{m['role']}: {m['content']}" for m in messages[-limit:]]
        )

        messages_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation},
        ]

        summary = await self.chat_completion(messages=messages_list, temperature=0.3)
        logger.info(f"Conversation summarized (context={limit}): {len(summary)} chars")
        return summary

    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()
        logger.info("LLM service closed")


# 全局LLM服务实例
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """FastAPI依赖注入：获取LLM服务"""
    await llm_service.initialize()
    return llm_service
