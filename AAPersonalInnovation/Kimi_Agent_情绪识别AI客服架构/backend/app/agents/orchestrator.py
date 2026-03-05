"""Agent编排系统 - LangGraph实现"""
from typing import Any, Optional

from langgraph.graph import StateGraph
from loguru import logger

from app.models.schemas import (
    AgentState,
    Document,
    IntentResult,
    Message,
    RouterDecision,
    SentimentResult,
    WorkflowState,
)
from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.services.rag_service import rag_service


class CustomerServiceOrchestrator:
    """客服Agent编排器"""

    def __init__(self):
        self.graph: Optional[StateGraph] = None
        self._initialized = False

    async def initialize(self):
        """初始化Agent编排器"""
        if self._initialized:
            return

        # 确保依赖服务已初始化
        await llm_service.initialize()
        await rag_service.initialize()
        await memory_service.initialize()

        # 构建工作流图
        self._build_workflow_graph()

        self._initialized = True
        logger.info("Agent orchestrator initialized")

    def _build_workflow_graph(self):
        """构建Agent工作流图"""
        # 这里简化实现，生产环境应该使用LangGraph
        # workflow = StateGraph(WorkflowState)
        # ... 定义节点和边

        logger.info("Workflow graph built")

    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> WorkflowState:
        """处理用户消息的完整流程"""
        try:
            # 1. 获取历史消息
            short_term_memory = await memory_service.get_short_term_memory(session_id)
            history = [
                {"role": msg.role, "content": msg.content} for msg in short_term_memory
            ]

            # 2. 情绪分析
            logger.info(f"Step 1: Analyzing sentiment for {session_id}")
            sentiment_data = await llm_service.detect_sentiment(message, history)
            sentiment = SentimentResult(**sentiment_data)

            # 3. 意图识别
            logger.info(f"Step 2: Detecting intent for {session_id}")
            intent_data = await llm_service.detect_intent(message, history)
            intent = IntentResult(**intent_data)

            # 4. 知识检索
            logger.info(f"Step 3: Retrieving knowledge for {session_id}")
            retrieval_result = await rag_service.hybrid_search(
                query=message,
                top_k=5,
            )

            # 5. 路由决策（是否转人工）
            logger.info(f"Step 4: Making routing decision for {session_id}")
            handoff_decision = await llm_service.should_handoff(
                message=message,
                sentiment=sentiment_data,
                intent=intent_data,
                history=history,
            )

            router_decision = RouterDecision(
                decision="handoff" if handoff_decision["should_handoff"] else "continue",
                reason=handoff_decision["reason"],
                priority=handoff_decision.get("priority", 3),
                confidence=handoff_decision.get("confidence", 0.5),
            )

            # 6. 生成回复
            if not handoff_decision["should_handoff"]:
                logger.info(f"Step 5: Generating AI response for {session_id}")

                # 获取长期记忆上下文
                memory_context = await memory_service.retrieve_relevant_memory(
                    session_id, message, user_id
                )

                # 格式化检索到的知识
                knowledge_context = await rag_service.format_context(
                    retrieval_result.documents
                )

                # 组合上下文
                full_context = f"""历史记忆:
{memory_context}

相关知识:
{knowledge_context}"""

                # 生成回复
                response = await llm_service.generate_response(
                    query=message,
                    context=full_context,
                    sentiment=sentiment_data,
                    intent=intent_data,
                    history=history,
                )
            else:
                response = "正在为您转接人工客服，请稍候..."

            # 7. 构建消息
            user_msg = Message(
                id=f"{session_id}_user_{len(short_term_memory) + 1}",
                role="user",
                content=message,
                timestamp=datetime.now(),
                sentiment=sentiment,
            )

            assistant_msg = Message(
                id=f"{session_id}_assistant_{len(short_term_memory) + 1}",
                role="assistant",
                content=response,
                timestamp=datetime.now(),
                metadata={
                    "intent": intent.type,
                    "sentiment_level": sentiment.level,
                    "router_decision": router_decision.decision,
                    "retrieved_docs": len(retrieval_result.documents),
                },
            )

            # 8. 更新记忆
            updated_messages = short_term_memory + [user_msg, assistant_msg]
            await memory_service.update_short_term_memory(session_id, updated_messages)

            # 9. 判断是否需要总结
            if await memory_service.should_summarize(session_id, len(updated_messages)):
                logger.info(f"Step 6: Summarizing conversation for {session_id}")
                summary = await memory_service.summarize_conversation(
                    session_id, updated_messages
                )
                await memory_service.update_long_term_memory(
                    session_id=session_id,
                    summary=summary.summary,
                    key_facts=summary.key_facts,
                    user_id=user_id,
                )

            # 10. 构建Agent状态
            agents = {
                "sentiment_agent": AgentState(
                    name="情绪分析Agent",
                    type="sentiment",
                    status="completed",
                    current_task="情绪分析",
                    result=sentiment.model_dump(),
                ),
                "intent_agent": AgentState(
                    name="意图识别Agent",
                    type="router",
                    status="completed",
                    current_task="意图识别",
                    result=intent.model_dump(),
                ),
                "retrieval_agent": AgentState(
                    name="知识检索Agent",
                    type="retrieval",
                    status="completed",
                    current_task="知识检索",
                    result={
                        "method": retrieval_result.retrieval_method,
                        "count": retrieval_result.total_found,
                    },
                ),
                "router_agent": AgentState(
                    name="路由决策Agent",
                    type="router",
                    status="completed",
                    current_task="路由决策",
                    result=router_decision.model_dump(),
                ),
                "conversation_agent": AgentState(
                    name="对话Agent",
                    type="conversation",
                    status="completed",
                    current_task="生成回复",
                    result={"response_length": len(response)},
                ),
            }

            # 11. 构建工作流状态
            workflow_state = WorkflowState(
                session_id=session_id,
                messages=updated_messages,
                agents=agents,
                current_step="completed",
                is_complete=True,
            )

            logger.info(f"Workflow completed for {session_id}")
            return workflow_state

        except Exception as e:
            logger.error(f"Error processing message for {session_id}: {e}")
            # 返回错误状态
            return WorkflowState(
                session_id=session_id,
                messages=[],
                agents={},
                current_step="error",
                is_complete=True,
            )

    async def get_agent_states(self, session_id: str) -> dict[str, AgentState]:
        """获取所有Agent状态"""
        # 这里可以从缓存或数据库获取实际的Agent状态
        # 简化实现返回默认状态
        return {
            "sentiment_agent": AgentState(
                name="情绪分析Agent", type="sentiment", status="idle"
            ),
            "intent_agent": AgentState(
                name="意图识别Agent", type="router", status="idle"
            ),
            "retrieval_agent": AgentState(
                name="知识检索Agent", type="retrieval", status="idle"
            ),
            "router_agent": AgentState(
                name="路由决策Agent", type="router", status="idle"
            ),
            "conversation_agent": AgentState(
                name="对话Agent", type="conversation", status="idle"
            ),
        }


# 全局Agent编排器实例
orchestrator = CustomerServiceOrchestrator()


async def get_orchestrator() -> CustomerServiceOrchestrator:
    """FastAPI依赖注入：获取Agent编排器"""
    await orchestrator.initialize()
    return orchestrator


# 避免循环导入
from datetime import datetime
