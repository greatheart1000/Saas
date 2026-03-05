# API使用指南

## 快速开始

### 1. 启动服务

```bash
# 后端目录
cd backend

# 首次运行，初始化知识库
python quickstart.py

# 启动服务
python -m app.api.main
```

### 2. 访问地址

- API文档: http://localhost:8000/docs
- 监控Dashboard: http://localhost:8000/dashboard/monitor_dashboard.html
- 健康检查: http://localhost:8000/health

## 核心 API 端点

### 聊天相关

#### 发送消息

```bash
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想退款",
    "session_id": "user_001"
  }'
```

**响应示例:**
```json
{
  "message": "您好！我理解您需要退款。让我来帮您处理。请提供订单号，我会为您查询退款进度...",
  "session_id": "user_001",
  "sentiment": {
    "score": 0.3,
    "level": "normal",
    "triggers": [],
    "keywords": [],
    "confidence": 0.9
  },
  "intent": {
    "type": "refund_related",
    "confidence": 0.85,
    "entities": {}
  },
  "router_decision": {
    "decision": "continue",
    "reason": "情绪正常，继续AI处理",
    "priority": 3,
    "confidence": 0.8
  },
  "retrieved_docs": [],
  "should_handoff": false,
  "response_time": 1.23
}
```

#### 获取会话历史

```bash
curl http://localhost:8000/api/v1/chat/history/user_001
```

#### 获取会话摘要

```bash
curl http://localhost:8000/api/v1/chat/summary/user_001
```

#### 清除会话历史

```bash
curl -X DELETE http://localhost:8000/api/v1/chat/history/user_001
```

### 知识库相关

#### 添加知识

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "新的退款政策：审核时间缩短为1个工作日",
      "客服热线变更为：400-888-8888"
    ],
    "ids": ["doc_100", "doc_101"],
    "metadatas": [
      {"category": "政策", "updated": "2025-03-05"},
      {"category": "客服", "updated": "2025-03-05"}
    ]
  }'
```

#### 搜索知识库

```bash
# 混合检索（推荐）
curl "http://localhost:8000/api/v1/knowledge/search?query=如何退款&top_k=5&method=hybrid"

# 纯向量检索
curl "http://localhost:8000/api/v1/knowledge/search?query=退款流程&top_k=5&method=vector"

# 纯BM25检索
curl "http://localhost:8000/api/v1/knowledge/search?query=退款时间&top_k=5&method=bm25"
```

#### 获取知识库统计

```bash
curl http://localhost:8000/api/v1/knowledge/stats
```

#### 清空知识库

```bash
curl -X DELETE http://localhost:8000/api/v1/knowledge/clear
```

### 监控相关

#### 获取系统统计

```bash
curl http://localhost:8000/api/v1/monitor/stats
```

#### 获取最近会话

```bash
curl "http://localhost:8000/api/v1/monitor/recent-sessions?limit=20&offset=0"
```

#### 获取会话详情

```bash
curl http://localhost:8000/api/v1/monitor/session/user_001
```

#### 获取系统指标

```bash
curl "http://localhost:8000/api/v1/monitor/metrics"
```

#### 删除会话

```bash
curl -X DELETE http://localhost:8000/api/v1/monitor/session/user_001
```

## Python SDK 示例

```python
import httpx

class CustomerServiceClient:
    """AI客服客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_message(
        self,
        message: str,
        session_id: str,
        user_id: str = None
    ):
        """发送消息"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat/send",
            json={
                "message": message,
                "session_id": session_id,
                "user_id": user_id
            }
        )
        return response.json()

    async def get_history(self, session_id: str):
        """获取历史"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/chat/history/{session_id}"
        )
        return response.json()

    async def add_knowledge(
        self,
        texts: list[str],
        ids: list[str] = None,
        metadatas: list[dict] = None
    ):
        """添加知识"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/knowledge/add",
            json={
                "texts": texts,
                "ids": ids,
                "metadatas": metadatas
            }
        )
        return response.json()

    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        method: str = "hybrid"
    ):
        """搜索知识"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/knowledge/search",
            params={
                "query": query,
                "top_k": top_k,
                "method": method
            }
        )
        return response.json()

    async def close(self):
        """关闭连接"""
        await self.client.aclose()


# 使用示例
async def main():
    client = CustomerServiceClient()

    # 发送消息
    result = await client.send_message(
        message="我要退款",
        session_id="test_001"
    )
    print(f"AI回复: {result['message']}")
    print(f"情绪: {result['sentiment']['level']}")
    print(f"意图: {result['intent']['type']}")

    # 添加知识
    await client.add_knowledge(
        texts=["新的知识内容"],
        ids=["new_doc_001"]
    )

    # 搜索知识
    search_result = await client.search_knowledge(
        query="退款流程",
        top_k=3
    )
    print(f"找到 {search_result['total_found']} 条相关结果")

    await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## JavaScript/Node.js SDK 示例

```javascript
const axios = require('axios');

class CustomerServiceClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            timeout: 30000
        });
    }

    async sendMessage(message, sessionId, userId = null) {
        const response = await this.client.post('/api/v1/chat/send', {
            message,
            session_id: sessionId,
            user_id: userId
        });
        return response.data;
    }

    async getHistory(sessionId) {
        const response = await this.client.get(`/api/v1/chat/history/${sessionId}`);
        return response.data;
    }

    async addKnowledge(texts, ids = null, metadatas = null) {
        const response = await this.client.post('/api/v1/knowledge/add', {
            texts,
            ids,
            metadatas
        });
        return response.data;
    }

    async searchKnowledge(query, topK = 5, method = 'hybrid') {
        const response = await this.client.get('/api/v1/knowledge/search', {
            params: { query, top_k: topK, method }
        });
        return response.data;
    }
}

// 使用示例
async function main() {
    const client = new CustomerServiceClient();

    // 发送消息
    const result = await client.sendMessage('我要退款', 'test_001');
    console.log('AI回复:', result.message);
    console.log('情绪:', result.sentiment.level);
    console.log('意图:', result.intent.type);

    // 搜索知识
    const searchResult = await client.searchKnowledge('退款流程', 3);
    console.log(`找到 ${searchResult.total_found} 条相关结果`);
}

main().catch(console.error);
```

## 完整对话流程示例

```python
import asyncio
import httpx

async def conversation_demo():
    """完整对话演示"""
    client = httpx.AsyncClient()

    session_id = "demo_session_001"

    # 对话1: 问候
    print("\n=== 对话1 ===")
    print("用户: 你好")
    response = client.post(
        "http://localhost:8000/api/v1/chat/send",
        json={"message": "你好", "session_id": session_id}
    ).json()
    print(f"AI: {response['message']}")
    print(f"情绪: {response['sentiment']['level']} ({response['sentiment']['score']})")

    await asyncio.sleep(1)

    # 对话2: 查询订单
    print("\n=== 对话2 ===")
    print("用户: 我想查一下订单")
    response = client.post(
        "http://localhost:8000/api/v1/chat/send",
        json={"message": "我想查一下订单", "session_id": session_id}
    ).json()
    print(f"AI: {response['message']}")
    print(f"意图: {response['intent']['type']}")

    await asyncio.sleep(1)

    # 对话3: 投诉（测试情绪识别）
    print("\n=== 对话3 ===")
    print("用户: 你们的服务太差了，我要投诉！")
    response = client.post(
        "http://localhost:8000/api/v1/chat/send",
        json={"message": "你们的服务太差了，我要投诉！", "session_id": session_id}
    ).json()
    print(f"AI: {response['message']}")
    print(f"情绪: {response['sentiment']['level']} ({response['sentiment']['score']})")
    print(f"是否转人工: {response['should_handoff']}")

    await asyncio.sleep(1)

    # 查看会话摘要
    print("\n=== 会话摘要 ===")
    summary = client.get(
        f"http://localhost:8000/api/v1/chat/summary/{session_id}"
    ).json()
    print(f"摘要: {summary['summary']}")
    print(f"关键信息: {summary['key_facts']}")
    print(f"用户意图: {summary['user_intent']}")
    print(f"情绪趋势: {summary['sentiment_trend']}")

    client.close()


if __name__ == "__main__":
    asyncio.run(conversation_demo())
```

## 错误处理

所有API在出错时会返回标准的错误响应：

```json
{
  "error": "错误类型",
  "detail": "详细错误信息",
  "code": "ERROR_CODE"
}
```

常见错误码：
- `400`: 请求参数错误
- `500`: 服务器内部错误
- `503`: 服务不可用（LLM API调用失败等）

## 最佳实践

1. **session_id 管理**
   - 使用唯一ID标识每个用户会话
   - 同一用户多次对话使用相同session_id
   - 建议格式: `user_{user_id}_{timestamp}`

2. **错误重试**
   - 网络错误时自动重试（最多3次）
   - 指数退避策略
   - 记录失败日志

3. **缓存策略**
   - 知识库搜索结果可以缓存5分钟
   - 会话历史可以缓存1分钟
   - 使用Redis等缓存系统

4. **监控告警**
   - 定期检查 `/health` 端点
   - 监控响应时间
   - 跟踪转人工率

5. **性能优化**
   - 使用异步客户端
   - 批量操作合并请求
   - 长文本分段处理
