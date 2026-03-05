"""聊天API路由 - 增强版（支持Persona和上下文窗口）"""
from datetime import datetime
from time import time

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from app.agents.orchestrator import orchestrator
from app.core.persona import PersonaType, get_all_personas
from app.models.schemas import (
    ChatResponse,
    Document,
    ErrorResponse,
    IntentResult,
    RouterDecision,
    SentimentResult,
)
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequestEnhanced(BaseModel):
    """增强的聊天请求"""
    message: str
    session_id: str | None = None
    user_id: str | None = None
    persona: PersonaType | None = Field(
        default=None,
        description="客服人格类型（None则使用默认配置）"
    )
    context_limit: int | None = Field(
        default=None,
        description="上下文窗口大小（None则使用配置默认值）"
    )


@router.post("/send", response_model=ChatResponse)
async def send_message_enhanced(request: ChatRequestEnhanced):
    """发送消息并获取AI回复（增强版）

    支持参数：
    - message: 用户消息
    - session_id: 会话ID（可选）
    - user_id: 用户ID（可选）
    - persona: 客服人格类型（可选：friendly, cute, mature, professional, humorous）
    - context_limit: 上下文窗口大小（可选）
    """
    start_time = time()

    try:
        # 初始化编排器
        await orchestrator.initialize()

        # 处理消息（使用增强版）
        from app.agents.orchestrator_enhanced import orchestrator as orchestrator_enhanced

        workflow_state = await orchestrator_enhanced.process_message(
            message=request.message,
            session_id=request.session_id or f"session_{int(time())}",
            user_id=request.user_id,
            persona_type=request.persona,
            context_limit=request.context_limit,
        )

        # 提取最后一条助手消息
        assistant_messages = [msg for msg in workflow_state.messages if msg.role == "assistant"]
        if not assistant_messages:
            raise HTTPException(status_code=500, detail="Failed to generate response")

        last_message = assistant_messages[-1]

        # 提取情绪、意图、路由决策
        sentiment = (
            workflow_state.messages[-2].sentiment
            if len(workflow_state.messages) >= 2
            else SentimentResult(score=0, level="normal", triggers=[], keywords=[], confidence=0.5)
        )

        intent_agent = workflow_state.agents.get("intent_agent")
        intent = (
            IntentResult(**intent_agent.result)
            if intent_agent and intent_agent.result
            else IntentResult(type="unknown", confidence=0.5)
        )

        router_agent = workflow_state.agents.get("router_agent")
        router_decision = (
            RouterDecision(**router_agent.result)
            if router_agent and router_agent.result
            else RouterDecision(decision="continue", reason="默认流程", priority=3, confidence=0.5)
        )

        retrieval_agent = workflow_state.agents.get("retrieval_agent")
        retrieved_docs: list[Document] = []

        response_time = time() - start_time

        return ChatResponse(
            message=last_message.content,
            session_id=workflow_state.session_id,
            sentiment=sentiment,
            intent=intent,
            router_decision=router_decision,
            retrieved_docs=retrieved_docs,
            should_handoff=router_decision.decision == "handoff",
            response_time=response_time,
        )

    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    limit: int = Query(default=10, description="返回消息数量限制")
):
    """获取会话历史"""
    try:
        from app.services.memory_service_enhanced import memory_service

        messages = await memory_service.get_short_term_memory(session_id, limit=limit)

        return {
            "session_id": session_id,
            "messages": [msg.model_dump() for msg in messages],
            "message_count": len(messages),
        }
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """清除会话历史"""
    try:
        from app.services.memory_service_enhanced import memory_service

        await memory_service.clear_session_memory(session_id)

        return {"message": "History cleared", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{session_id}")
async def get_summary(session_id: str):
    """获取会话摘要"""
    try:
        from app.services.memory_service_enhanced import memory_service

        messages = await memory_service.get_short_term_memory(session_id)

        if not messages:
            return {"session_id": session_id, "summary": "暂无对话记录"}

        summary = await memory_service.summarize_conversation(session_id, messages)

        return summary.model_dump()
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Persona管理API ====================

@router.get("/personas")
async def list_personas():
    """获取所有可用的Persona类型"""
    personas = get_all_personas()

    return {
        "personas": [
            {
                "type": ptype,
                "name": persona.name,
                "description": persona.description,
                "response_style": persona.response_style,
            }
            for ptype, persona in personas.items()
        ],
        "default": "friendly",
        "enabled": True,
    }


@router.post("/set-persona")
async def set_persona(
    session_id: str,
    persona: PersonaType
):
    """为会话设置Persona（需要在前端维护session->persona的映射）

    注意：这是一个示例API，实际应该在session存储中维护
    """
    try:
        # 这里应该将session_id和persona的映射存储到数据库或Redis
        # 简化实现：只返回确认信息

        from app.core.redis import redis_client

        cache_key = f"session_persona:{session_id}"
        await redis_client.set(cache_key, persona, expire=86400)  # 24小时

        persona_config = get_persona(persona)

        return {
            "message": "Persona设置成功",
            "session_id": session_id,
            "persona": persona,
            "persona_name": persona_config.name,
            "description": persona_config.description,
        }
    except Exception as e:
        logger.error(f"Error setting persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/persona/{session_id}")
async def get_session_persona(session_id: str):
    """获取会话当前的Persona"""
    try:
        from app.core.redis import redis_client

        cache_key = f"session_persona:{session_id}"
        persona = await redis_client.get(cache_key)

        if persona:
            persona_config = get_persona(persona)
            return {
                "session_id": session_id,
                "persona": persona,
                "persona_name": persona_config.name,
                "description": persona_config.description,
            }
        else:
            return {
                "session_id": session_id,
                "persona": None,
                "message": "使用默认Persona",
            }
    except Exception as e:
        logger.error(f"Error getting persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))
