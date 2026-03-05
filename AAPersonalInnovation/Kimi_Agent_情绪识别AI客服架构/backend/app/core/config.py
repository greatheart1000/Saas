"""应用配置管理 - 增强版"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用信息
    app_name: str = "Kimi Customer Service"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_version: str = "0.1.0"

    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    # 数据库
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kimi_cs"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 3600

    # ==================== 上下文窗口配置 ====================
    # 不同任务使用不同的上下文窗口大小
    context_sentiment_limit: int = Field(
        default=5,
        description="情绪分析时的上下文消息数"
    )
    context_intent_limit: int = Field(
        default=5,
        description="意图识别时的上下文消息数"
    )
    context_response_limit: int = Field(
        default=10,
        description="生成回复时的上下文消息数"
    )
    context_summary_limit: int = Field(
        default=20,
        description="生成总结时的上下文消息数"
    )
    context_max_tokens: int = Field(
        default=4000,
        description="最大上下文token数"
    )

    # ==================== 自动摘要配置 ====================
    summary_trigger_message_count: int = Field(
        default=15,
        description="触发自动摘要的消息数阈值"
    )
    summary_trigger_time_minutes: int = Field(
        default=10,
        description="触发自动摘要的时间间隔（分钟）"
    )
    summary_auto_summarize: bool = Field(
        default=True,
        description="是否启用自动摘要"
    )
    summary_preserve_key_messages: int = Field(
        default=3,
        description="摘要时保留的最近关键消息数"
    )

    # ==================== Persona拟人化配置 ====================
    # 默认Persona
    default_persona: str = Field(
        default="friendly",
        description="默认客服人格类型"
    )

    # 是否启用Persona
    persona_enabled: bool = Field(
        default=True,
        description="是否启用拟人化回复"
    )

    # 允许的Persona列表
    persona_allowed_types: list[str] = Field(
        default=["friendly", "cute", "mature", "professional", "humorous"],
        description="允许使用的Persona类型"
    )

    # LLM配置
    llm_provider: Literal["kimi", "openai", "zhipu"] = "zhipu"

    # 智谱AI (GLM-5)
    zhipu_api_key: str = ""
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    zhipu_model: str = "glm-5"
    zhipu_embedding_model: str = "embedding-v2"

    # Kimi
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "moonshot-v1-128k"
    kimi_embedding_model: str = "embedding-v2"

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-large"

    # 向量数据库
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "knowledge_base"

    # 嵌入模型
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32

    # RAG配置
    rag_top_k: int = 5
    rag_score_threshold: float = 0.7
    rag_rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rag_hybrid_alpha: float = 0.5

    # 记忆管理
    memory_short_term_limit: int = 10
    memory_long_term_limit: int = 100
    memory_summary_threshold: int = 20

    # Agent配置
    agent_max_iterations: int = 10
    agent_timeout: float = 30.0

    # 转人工配置
    handoff_sentiment_threshold: float = 0.7
    handoff_complexity_threshold: float = 0.8
    handoff_repeat_threshold: int = 3

    # 日志
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # 安全
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def llm_api_key(self) -> str:
        """根据provider返回对应的API key"""
        if self.llm_provider == "zhipu":
            return self.zhipu_api_key
        elif self.llm_provider == "kimi":
            return self.kimi_api_key
        return self.openai_api_key

    @property
    def llm_base_url(self) -> str:
        """根据provider返回对应的base URL"""
        if self.llm_provider == "zhipu":
            return self.zhipu_base_url
        elif self.llm_provider == "kimi":
            return self.kimi_base_url
        return self.openai_base_url

    @property
    def llm_model(self) -> str:
        """根据provider返回对应的模型"""
        if self.llm_provider == "zhipu":
            return self.zhipu_model
        elif self.llm_provider == "kimi":
            return self.kimi_model
        return self.openai_model

    @property
    def embedding_api_key(self) -> str:
        """根据provider返回对应的API key"""
        if self.llm_provider == "zhipu":
            return self.zhipu_api_key
        elif self.llm_provider == "kimi":
            return self.kimi_api_key
        return self.openai_api_key

    @property
    def embedding_base_url(self) -> str:
        """根据provider返回对应的base URL"""
        if self.llm_provider == "zhipu":
            return self.zhipu_base_url
        elif self.llm_provider == "kimi":
            return self.kimi_base_url
        return self.openai_base_url

    @property
    def embedding_model_name(self) -> str:
        """根据provider返回对应的模型"""
        if self.llm_provider == "zhipu":
            return self.zhipu_embedding_model
        elif self.llm_provider == "kimi":
            return self.kimi_embedding_model
        return self.openai_embedding_model

    @property
    def data_dir(self) -> Path:
        """数据目录"""
        return Path(__file__).parent.parent.parent / "data"

    @property
    def log_dir(self) -> Path:
        """日志目录"""
        return Path(__file__).parent.parent.parent / "logs"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
