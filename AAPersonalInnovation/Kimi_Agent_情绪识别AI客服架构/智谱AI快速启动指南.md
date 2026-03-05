# 🚀 AI客服系统 - 智谱AI GLM-5 快速启动指南

## ✅ 当前系统状态

已完成配置：
- ✅ Python 3.13.9
- ✅ MySQL 8.0.45（已初始化，8条知识文档）
- ✅ 核心依赖已安装（fastapi, openai, pymysql等）
- ✅ 智谱AI GLM-5配置完成
- ✅ 数据库已初始化

---

## 🎯 立即启动（3步走）

### 步骤 1: 测试智谱AI配置

```bash
cd backend
python3 test_zhipu.py
```

**预期输出：**
```
🧪 智谱AI GLM-5 连接测试
========================================
✅ 连接成功！
回复: 我是一个由智谱AI开发的大型语言模型...
✅ JSON输出成功！
✅ 情绪分析成功！
✅ 所有测试通过！
```

### 步骤 2: 启动API服务

```bash
cd backend
python3 -m app.api.main
```

**预期输出：**
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 3: 访问前端界面

打开浏览器访问：

#### 💬 对话监控页面
```
http://localhost:8000/static/conversations.html
```
功能：查看最近对话、时间筛选、情绪分析、意图识别

#### 📚 知识库管理页面
```
http://localhost:8000/static/knowledge.html
```
功能：知识CRUD、搜索筛选、分类管理

#### 📖 API文档
```
http://localhost:8000/docs
```
功能：交互式API文档、接口测试

---

## 🔧 智谱AI配置说明

### 配置文件位置
- `.env` - 环境变量配置
- `backend/app/core/config.py` - 配置类定义

### 当前配置
```env
LLM_PROVIDER=zhipu
ZHIPU_API_KEY=b47777cc5e654fbf96265be5c5398097.lDBejVEPN5RGMlHu
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
ZHIPU_MODEL=glm-5
```

### LLM服务调用示例

```python
from app.services.llm_service import llm_service

# 初始化
await llm_service.initialize()

# 情绪分析
sentiment = await llm_service.detect_sentiment(
    message="这个产品质量太差了！",
    history=[]
)
# 返回: {"score": 0.8, "level": "critical", ...}

# 意图识别
intent = await llm_service.detect_intent(
    message="我要退款",
    history=[]
)
# 返回: {"type": "refund_related", "confidence": 0.9, ...}

# 生成回复
response = await llm_service.generate_response(
    query="如何申请退款？",
    context="退款流程知识...",
    sentiment={"level": "normal"},
    intent={"type": "query"},
    history=[]
)
```

---

## 📊 系统功能特性

### 核心AI能力
- ✅ **LLM意图识别** - 智谱AI GLM-5智能分析
- ✅ **情绪分析** - 多维度情绪评分（normal/warning/critical）
- ✅ **RAG混合检索** - ChromaDB向量 + BM25关键词
- ✅ **自动转人工** - 基于情绪、意图、复杂度智能路由
- ✅ **多轮对话记忆** - 可配置上下文窗口（5-20条消息）
- ✅ **自动摘要** - 15条消息或10分钟触发
- ✅ **5种客服人格** - 亲切、可爱、成熟、专业、幽默

### 数据持久化
- ✅ MySQL存储（root/123456）
- ✅ 消息按时间顺序存储
- ✅ 支持时间范围查询（今天/7天/30天）
- ✅ 会话、消息、知识库三表结构

### API接口
- `/api/v1/chat` - 聊天接口
- `/api/v1/knowledge/list` - 知识列表
- `/api/v1/knowledge/add` - 添加知识
- `/api/v1/knowledge/update/{id}` - 更新知识
- `/api/v1/knowledge/delete/{id}` - 删除知识
- `/api/v1/monitor/stats` - 监控统计
- `/api/v1/monitor/conversations` - 对话列表
- `/api/v1/monitor/messages/{conv_id}` - 消息详情

---

## 🧪 测试API接口

### 测试聊天接口
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想查询订单",
    "conversation_id": "test_conv_001",
    "user_id": "test_user_001"
  }'
```

### 测试知识库接口
```bash
# 查询知识列表
curl http://localhost:8000/api/v1/knowledge/list

# 添加知识
curl -X POST http://localhost:8000/api/v1/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试知识",
    "content": "这是测试内容",
    "category": "测试"
  }'
```

### 测试监控接口
```bash
# 查询统计信息
curl http://localhost:8000/api/v1/monitor/stats?time_range=day

# 查询对话列表
curl http://localhost:8000/api/v1/monitor/conversations?time_range=week&limit=10
```

---

## 🔄 LLM Provider切换

系统支持3个LLM提供商，可随时切换：

### 切换到Kimi
```env
# 修改 .env
LLM_PROVIDER=kimi
KIMI_API_KEY=your_kimi_api_key
```

### 切换到OpenAI
```env
# 修改 .env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
```

### 切换回智谱AI
```env
# 修改 .env
LLM_PROVIDER=zhipu
```

**切换后重启服务即可，无需修改代码。**

---

## ⚙️ 高级配置

### 上下文窗口配置
```env
# 不同任务的上下文消息数
CONTEXT_SENTIMENT_LIMIT=5    # 情绪分析
CONTEXT_INTENT_LIMIT=5       # 意图识别
CONTEXT_RESPONSE_LIMIT=10    # 生成回复
CONTEXT_SUMMARY_LIMIT=20     # 生成总结
```

### 自动摘要配置
```env
SUMMARY_TRIGGER_MESSAGE_COUNT=15  # 消息数阈值
SUMMARY_TRIGGER_TIME_MINUTES=10   # 时间间隔
SUMMARY_AUTO_SUMMARIZE=true       # 启用自动摘要
```

### Persona配置
```env
DEFAULT_PERSONA=friendly    # 默认人格
PERSONA_ENABLED=true        # 启用拟人化
```

可用人格类型：
- `friendly` - 亲切小助手（默认）
- `cute` - 元气少女（活泼可爱）
- `mature` - 稳重的顾问（成熟冷静）
- `professional` - 专家顾问（专业权威）
- `humorous` - 幽默达人（风趣幽默）

---

## 📝 常见问题

### Q1: 智谱AI连接失败？
**检查：**
```bash
# 1. 检查API key是否正确
cat backend/.env | grep ZHIPU_API_KEY

# 2. 运行测试脚本
cd backend && python3 test_zhipu.py

# 3. 检查网络连接
ping open.bigmodel.cn
```

### Q2: 数据库连接失败？
**检查：**
```bash
# 测试MySQL连接
mysql -uroot -p123456 -e "USE kimi_cs; SHOW TABLES;"

# 如果失败，重新初始化
python3 backend/init_db_simple.py
```

### Q3: 端口8000被占用？
**解决：**
```bash
# 查看占用进程
lsof -i:8000

# 杀死进程
kill -9 [PID]

# 或修改端口
# 编辑 .env: API_PORT=8001
```

### Q4: 前端页面无法访问？
**检查：**
```bash
# 确认API服务已启动
curl http://localhost:8000/health

# 检查静态文件
ls -la backend/static/
```

---

## 📚 相关文档

- `智谱AI配置说明.md` - 详细的配置说明
- `架构问题分析报告.md` - 系统架构分析
- `快速部署指南.md` - 原部署指南
- `backend/README.md` - 后端文档

---

## 🎉 启动完成

系统启动后，您可以：

1. **测试对话** - 使用API文档中的聊天接口
2. **管理知识** - 在知识库页面添加/编辑知识
3. **监控对话** - 在对话监控页面查看实时对话
4. **开发集成** - 参考API文档开发前端应用

---

**配置完成时间**: 2026-03-05
**LLM Provider**: 智谱AI GLM-5
**系统状态**: ✅ 已配置并准备就绪
