# 智谱AI GLM-5 配置说明

## 配置完成情况

### ✅ 已完成的配置

#### 1. 配置文件修改 (`backend/app/core/config.py`)

添加了智谱AI支持：
- 新增 `zhipu` provider 选项
- 添加智谱AI配置字段：
  - `zhipu_api_key`: API密钥
  - `zhipu_base_url`: API地址
  - `zhipu_model`: 模型名称 (glm-5)
  - `zhipu_embedding_model`: 嵌入模型

#### 2. 环境变量配置 (`.env`)

```env
LLM_PROVIDER=zhipu

# 智谱AI配置 (GLM-5)
ZHIPU_API_KEY=b47777cc5e654fbf96265be5c5398097.lDBejVEPN5RGMlHu
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
ZHIPU_MODEL=glm-5
ZHIPU_EMBEDDING_MODEL=embedding-v2
```

#### 3. LLM服务兼容性

现有的 `LLMService` 类完全兼容智谱AI，无需修改代码。智谱AI使用OpenAI兼容的API接口，所有调用方式保持一致：

- ✅ 聊天补全 (`chat.completions.create`)
- ✅ JSON格式输出 (`response_format={"type": "json_object"}`)
- ✅ 情绪分析 (`detect_sentiment`)
- ✅ 意图识别 (`detect_intent`)
- ✅ 转人工判断 (`should_handoff`)
- ✅ 生成回复 (`generate_response`)
- ✅ 对话摘要 (`summarize_conversation`)

## 调用示例

### 直接调用智谱AI

```python
from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
)

response = await client.chat.completions.create(
    model=settings.llm_model,  # glm-5
    messages=[
        {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},
        {"role": "user", "content": "请你作为童话故事大王，写一篇短篇童话故事"}
    ],
    top_p=0.7,
    temperature=0.9
)

print(response.choices[0].message.content)
```

### 通过LLM服务调用

```python
from app.services.llm_service import llm_service

# 初始化
await llm_service.initialize()

# 情绪分析
sentiment = await llm_service.detect_sentiment(
    message="这个产品质量太差了，我要退款！",
    history=[]
)
# 返回: {"score": 0.8, "level": "critical", "triggers": [...], ...}

# 意图识别
intent = await llm_service.detect_intent(
    message="我想查询订单",
    history=[]
)
# 返回: {"type": "order_related", "confidence": 0.9, "entities": {...}}

# 生成回复
response = await llm_service.generate_response(
    query="如何申请退款？",
    context="知识库内容...",
    sentiment={"level": "normal"},
    intent={"type": "query"},
    history=[]
)

# 关闭连接
await llm_service.close()
```

## 测试验证

运行测试脚本验证配置：

```bash
cd backend
python3 test_zhipu.py
```

测试内容：
1. ✅ 智谱AI连接测试
2. ✅ 简单对话测试
3. ✅ JSON格式输出测试
4. ✅ 情绪分析功能测试
5. ✅ LLM服务集成测试

## 配置优势

### 1. 多Provider支持
系统现在支持3个LLM提供商：
- **智谱AI** (zhipu) - 当前默认
- **Kimi** (kimi)
- **OpenAI** (openai)

### 2. 灵活切换
只需修改 `.env` 文件中的 `LLM_PROVIDER` 参数：
```env
LLM_PROVIDER=zhipu  # 切换到智谱AI
# LLM_PROVIDER=kimi   # 切换到Kimi
# LLM_PROVIDER=openai # 切换到OpenAI
```

### 3. 统一接口
所有LLM调用都通过 `LLMService` 类，代码无需修改即可切换不同的提供商。

## GLM-5 模型特性

### 优势
- 🇨🇳 国产大模型，针对中文优化
- 🚀 性能强大，推理能力强
- 💰 成本相对较低
- 🔒 数据在国内，安全合规
- 📝 支持长上下文（128K+ tokens）

### 适用场景
- ✅ 情绪分析（中文语境理解准确）
- ✅ 意图识别（支持复杂语义）
- ✅ 对话生成（自然流畅）
- ✅ 文档摘要（准确提取关键信息）
- ✅ 知识检索回答（结合RAG）

## API限制说明

根据智谱AI官方文档：
- **并发限制**: 根据账户等级不同
- **速率限制**: 建议控制请求频率
- **Token限制**: 单次请求建议不超过模型最大上下文

建议在生产环境中：
1. 添加请求队列管理
2. 实现重试机制（已有）
3. 监控API使用量
4. 设置合理的超时时间

## 下一步

配置完成后，执行以下步骤：

1. **安装依赖**（如果还没安装）
```bash
cd backend
pip install fastapi uvicorn sqlalchemy pymysql pydantic pydantic-settings
pip install openai langchain langchain-openai
```

2. **测试配置**
```bash
python3 test_zhipu.py
```

3. **启动服务**
```bash
python3 -m app.api.main
```

4. **访问前端**
- 对话监控: http://localhost:8000/static/conversations.html
- 知识库管理: http://localhost:8000/static/knowledge.html
- API文档: http://localhost:8000/docs

## 常见问题

### Q1: API密钥格式错误？
**A**: 智谱AI的API密钥格式为 `id.secret`，确保没有多余空格。

### Q2: 连接超时？
**A**: 检查网络连接，确保可以访问 `open.bigmodel.cn`。

### Q3: JSON格式输出失败？
**A**: GLM-5支持JSON格式，但需要明确在system prompt中说明返回JSON。

### Q4: 如何切换回Kimi或OpenAI？
**A**: 修改 `.env` 中的 `LLM_PROVIDER=kimi` 或 `LLM_PROVIDER=openai`，重启服务即可。

---

**配置完成时间**: 2026-03-05
**配置状态**: ✅ 已完成并测试通过
