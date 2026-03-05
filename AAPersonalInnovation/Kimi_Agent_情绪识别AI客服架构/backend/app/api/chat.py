"""聊天API路由"""
from datetime import datetime
from time import time

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.agents.orchestrator import orchestrator
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Document,
    ErrorResponse,
    IntentResult,
    RouterDecision,
    SentimentResult,
)
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """发送消息并获取AI回复"""
    start_time = time()

    try:
        # 初始化编排器
        await orchestrator.initialize()

        # 处理消息
        workflow_state = await orchestrator.process_message(
            message=request.message,
            session_id=request.session_id or f"session_{int(time())}",
            user_id=request.user_id,
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
async def get_history(session_id: str):
    """获取会话历史"""
    try:
        from app.services.memory_service import memory_service

        messages = await memory_service.get_short_term_memory(session_id)

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
        from app.services.memory_service import memory_service

        await memory_service.clear_session_memory(session_id)

        return {"message": "History cleared", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{session_id}")
async def get_summary(session_id: str):
    """获取会话摘要"""
    try:
        from app.services.memory_service import memory_service

        messages = await memory_service.get_short_term_memory(session_id)

        if not messages:
            return {"session_id": session_id, "summary": "暂无对话记录"}

        summary = await memory_service.summarize_conversation(session_id, messages)

        return summary.model_dump()
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
