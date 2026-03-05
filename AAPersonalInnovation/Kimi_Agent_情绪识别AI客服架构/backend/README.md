# AI客服系统 - 后端API服务

基于RAG和Agent编排的智能客服系统，支持情绪识别、意图检测、知识检索和智能转人工。

## 🎯 核心特性

### ✅ 已实现（P0 + P1级别）

1. **LLM集成** - 支持Kimi/OpenAI
   - 真正的意图识别（使用LLM，非硬编码）
   - 真正的情绪分析（使用LLM，非硬编码）
   - 智能回复生成（基于上下文）

2. **RAG检索架构**
   - ✅ 向量检索（ChromaDB）
   - ✅ BM25关键词检索
   - ✅ 混合检索（向量+BM25融合）
   - ✅ 知识库管理

3. **智能记忆系统**
   - ✅ 短期记忆（最近N条消息）
   - ✅ 长期记忆（关键事实、摘要）
   - ✅ 会话总结（LLM生成）
   - ✅ 记忆检索和压缩

4. **Agent编排系统**
   - ✅ 多Agent协作（情绪、意图、检索、路由、对话）
   - ✅ 智能路由决策（使用LLM判断）
   - ✅ 基于LLM的转人工判断

5. **数据持久化**
   - ✅ Redis缓存（会话、记忆）
   - ✅ PostgreSQL支持（数据库模型已定义）

6. **监控Dashboard**
   - ✅ 实时会话监控
   - ✅ 对话历史查看
   - ✅ 指标统计（情绪分布、意图分布）

## 📦 安装部署

### 1. 环境要求

- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### 2. 安装依赖

```bash
cd backend
pip install -e .
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，配置必要的参数
```

### 4. 初始化数据库

```bash
# 创建数据库
createdb kimi_cs

# 运行迁移（TODO：实现Alembic迁移）
# alembic upgrade head
```

### 5. 启动服务

```bash
# 开发模式
python -m app.api.main

# 或使用uvicorn
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问服务

- API文档: http://localhost:8000/docs
- 监控Dashboard: http://localhost:8000/dashboard/monitor_dashboard.html
- 健康检查: http://localhost:8000/health

## 🔌 API使用示例

### 1. 发送消息

```bash
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想查询订单",
    "session_id": "test_session_001"
  }'
```

### 2. 获取会话历史

```bash
curl http://localhost:8000/api/v1/chat/history/test_session_001
```

### 3. 添加知识

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "订单查询方法：登录官网，进入我的订单页面",
      "退款流程：申请 -> 审核 -> 退款（3-5个工作日）"
    ],
    "ids": ["doc_001", "doc_002"]
  }'
```

### 4. 搜索知识库

```bash
curl "http://localhost:8000/api/v1/knowledge/search?query=如何退款&top_k=5&method=hybrid"
```

### 5. 获取系统统计

```bash
curl http://localhost:8000/api/v1/monitor/stats
```

## 📁 项目结构

```
backend/
├── app/
│   ├── api/                    # API路由
│   │   ├── chat.py            # 聊天API
│   │   ├── knowledge.py       # 知识库API
│   │   ├── monitor.py         # 监控API
│   │   └── main.py            # FastAPI主应用
│   ├── agents/                 # Agent编排
│   │   └── orchestrator.py    # 工作流编排器
│   ├── core/                   # 核心模块
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   └── redis.py           # Redis客户端
│   ├── models/                 # 数据模型
│   │   └── schemas.py         # Pydantic模型
│   ├── services/               # 业务服务
│   │   ├── llm_service.py     # LLM服务
│   │   ├── vector_store.py    # 向量存储
│   │   ├── bm25_store.py      # BM25检索
│   │   ├── rag_service.py     # RAG服务
│   │   └── memory_service.py  # 记忆管理
│   └── utils/                  # 工具函数
├── tests/                      # 测试
├── logs/                       # 日志
├── data/                       # 数据目录
│   └── chroma/                # 向量数据库
├── pyproject.toml             # 项目配置
├── .env.example               # 环境变量示例
├── README.md                  # 本文件
└── monitor_dashboard.html     # 监控Dashboard
```

## 🏗️ 架构说明

### Agent工作流

```
用户消息
  ↓
1. 情绪分析Agent（LLM）
  ↓
2. 意图识别Agent（LLM）
  ↓
3. 知识检索Agent（向量+BM25）
  ↓
4. 路由决策Agent（LLM判断是否转人工）
  ↓
5a. 继续AI → 对话Agent（基于RAG生成回复）
5b. 转人工 → 返回转人工信号
  ↓
6. 更新记忆（短期/长期）
  ↓
返回响应
```

### RAG检索流程

```
用户查询
  ↓
向量化（嵌入模型）
  ↓
并行检索:
  - 向量检索（ChromaDB）
  - BM25检索（关键词）
  ↓
结果融合（alpha混合）
  ↓
重排序（可选）
  ↓
返回Top-K文档
```

### 记忆管理

```
对话消息
  ↓
短期记忆（Redis，最近N条）
  ↓
达到阈值？
  ├─ 是 → LLM总结 → 长期记忆（Redis，7天）
  └─ 否 → 继续
```

## ⚙️ 配置说明

### LLM配置

支持两种Provider：

1. **Kimi（推荐）**
   ```env
   LLM_PROVIDER=kimi
   KIMI_API_KEY=your_kimi_api_key
   KIMI_MODEL=moonshot-v1-128k
   ```

2. **OpenAI**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4-turbo-preview
   ```

### RAG配置

```env
# 检索参数
RAG_TOP_K=5                           # 检索返回数量
RAG_SCORE_THRESHOLD=0.7               # 相似度阈值
RAG_HYBRID_ALPHA=0.5                  # 混合检索权重（向量alpha，BM25 1-alpha）

# 向量数据库
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=BAAI/bge-m3           # 嵌入模型（本地）
```

### 记忆配置

```env
MEMORY_SHORT_TERM_LIMIT=10            # 短期记忆保留消息数
MEMORY_LONG_TERM_LIMIT=100            # 长期记忆保留事实数
MEMORY_SUMMARY_THRESHOLD=20           # 触发总结的消息数阈值
```

### 转人工配置

```env
HANDOFF_SENTIMENT_THRESHOLD=0.7       # 情绪阈值
HANDOFF_COMPLEXITY_THRESHOLD=0.8      # 复杂度阈值
HANDOFF_REPEAT_THRESHOLD=3            # 重复提问次数阈值
```

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 带覆盖率
pytest --cov=app tests/

# 运行特定测试
pytest tests/test_chat.py
```

## 📊 监控

访问监控Dashboard查看：
- 实时会话列表
- 对话历史详情
- 情绪分布统计
- 意图分布统计
- 系统性能指标

Dashboard地址: http://localhost:8000/dashboard/monitor_dashboard.html

## 🔧 常见问题

### 1. ChromaDB初始化失败

```bash
# 确保数据目录存在
mkdir -p data/chroma
```

### 2. Redis连接失败

```bash
# 检查Redis是否运行
redis-cli ping

# 启动Redis
redis-server
```

### 3. LLM API调用失败

检查API密钥配置：
```bash
# 检查.env文件
cat .env | grep API_KEY
```

## 🚀 下一步计划

- [ ] 实现完整的数据库模型和迁移
- [ ] 添加重排序模型（Reranker）
- [ ] 实现真实的转人工队列系统
- [ ] 添加更多测试用例
- [ ] 性能优化和缓存策略
- [ ] 日志分析和监控告警
- [ ] Docker部署支持

## 📝 开发日志

- 2026-03-05: 完成P0+P1级别功能实现
  - ✅ LLM服务集成
  - ✅ RAG检索架构
  - ✅ 记忆管理系统
  - ✅ Agent编排系统
  - ✅ 监控Dashboard

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！
