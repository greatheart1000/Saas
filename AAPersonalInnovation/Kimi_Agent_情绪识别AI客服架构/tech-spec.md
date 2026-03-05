# AI客服Agent系统 - 技术规格文档

## 组件清单

### shadcn/ui 组件
- `button` - 按钮交互
- `card` - 卡片容器
- `input` - 输入框
- `textarea` - 多行文本
- `badge` - 状态标签
- `progress` - 进度条
- `separator` - 分隔线
- `scroll-area` - 滚动区域
- `avatar` - 头像
- `tooltip` - 提示框
- `dialog` - 对话框
- `sheet` - 侧边抽屉
- `collapsible` - 可折叠面板
- `tabs` - 标签页
- `slider` - 滑块

### 自定义组件

| 组件名 | 用途 | 位置 |
|-------|------|------|
| ChatMessage | 聊天消息气泡 | components/ChatMessage.tsx |
| ChatInput | 消息输入框 | components/ChatInput.tsx |
| SentimentMonitor | 情绪监控面板 | components/SentimentMonitor.tsx |
| RouterPanel | 路由决策面板 | components/RouterPanel.tsx |
| AgentStatus | Agent状态卡片 | components/AgentStatus.tsx |
| WorkflowVisualizer | 工作流可视化 | components/WorkflowVisualizer.tsx |
| HandoffModal | 转人工模态框 | components/HandoffModal.tsx |
| SentimentBadge | 情绪状态徽章 | components/SentimentBadge.tsx |
| AgentNode | Agent工作流节点 | components/AgentNode.tsx |

### 自定义Hooks

| Hook名 | 用途 | 位置 |
|-------|------|------|
| useSentimentAnalyzer | 情绪分析逻辑 | hooks/useSentimentAnalyzer.ts |
| useRouterAgent | 路由决策逻辑 | hooks/useRouterAgent.ts |
| useConversationAgent | 对话管理 | hooks/useConversationAgent.ts |
| useHandoff | 转人工流程 | hooks/useHandoff.ts |
| useChat | 聊天状态管理 | hooks/useChat.ts |

---

## 动画实现方案

| 动画 | 库 | 实现方式 | 复杂度 |
|-----|---|---------|-------|
| 页面入场动画 | Framer Motion | AnimatePresence + motion.div | 中 |
| 消息滑入 | Framer Motion | motion.div with initial/animate | 低 |
| 情绪分数变化 | Framer Motion | animate number value | 低 |
| 状态脉冲 | CSS | @keyframes pulse | 低 |
| 打字机动画 | CSS | @keyframes bounce | 低 |
| 工作流连线 | CSS | @keyframes dash | 中 |
| 节点发光 | CSS | box-shadow transition | 低 |
| 模态框缩放 | Framer Motion | scale + opacity | 低 |
| 滚动触发 | Framer Motion | whileInView | 低 |

---

## 项目文件结构

```
/mnt/okcomputer/output/app/
├── src/
│   ├── components/
│   │   ├── ChatMessage.tsx
│   │   ├── ChatInput.tsx
│   │   ├── SentimentMonitor.tsx
│   │   ├── RouterPanel.tsx
│   │   ├── AgentStatus.tsx
│   │   ├── WorkflowVisualizer.tsx
│   │   ├── HandoffModal.tsx
│   │   ├── SentimentBadge.tsx
│   │   └── AgentNode.tsx
│   ├── hooks/
│   │   ├── useSentimentAnalyzer.ts
│   │   ├── useRouterAgent.ts
│   │   ├── useConversationAgent.ts
│   │   ├── useHandoff.ts
│   │   └── useChat.ts
│   ├── types/
│   │   └── index.ts
│   ├── lib/
│   │   ├── utils.ts
│   │   ├── sentimentRules.ts
│   │   └── mockResponses.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── components/ui/     # shadcn/ui 组件
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 依赖安装

```bash
# 动画库
npm install framer-motion

# 图标库
npm install lucide-react

# 工具库
npm install uuid
npm install @types/uuid --save-dev
```

---

## 类型定义

```typescript
// types/index.ts

export type SentimentLevel = 'normal' | 'warning' | 'critical';

export interface SentimentResult {
  score: number;           // 0-100
  level: SentimentLevel;
  triggers: string[];      // 触发因素
  keywords: string[];      // 检测到的关键词
}

export type IntentType = 'handoff_request' | 'query' | 'greeting' | 'complaint' | 'unknown';

export interface IntentResult {
  type: IntentType;
  confidence: number;
  entities?: Record<string, string>;
}

export type RouterDecision = 'continue' | 'empathetic' | 'handoff';

export interface RouterResult {
  decision: RouterDecision;
  reason: string;
  priority: number;
}

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  sentiment?: SentimentResult;
  metadata?: {
    responseTime?: number;
    strategy?: string;
  };
}

export type AgentType = 'conversation' | 'sentiment' | 'router';

export interface AgentState {
  type: AgentType;
  status: 'idle' | 'processing' | 'completed' | 'error';
  currentTask?: string;
}

export type HandoffStatus = 'idle' | 'queued' | 'assigned' | 'connected' | 'cancelled';

export interface HandoffState {
  status: HandoffStatus;
  queuePosition?: number;
  estimatedWaitTime?: number;
  agentName?: string;
  agentAvatar?: string;
}
```

---

## 核心算法

### 情绪分析算法

```typescript
// lib/sentimentRules.ts

export const SENTIMENT_RULES = {
  // 显式转人工指令
  explicitHandoff: [
    '转人工', '找真人', '人工客服', '人工服务',
    '我要投诉', '找你们领导', '叫你们经理'
  ],
  
  // 负面情绪词
  negativeWords: {
    strong: ['垃圾', '废物', '骗子', '坑人', '倒闭', '投诉', '举报'],
    medium: ['差', '慢', '烂', '气', '烦', '失望', '不满'],
    light: ['不好', '不行', '不对', '问题', '错误']
  },
  
  // 标点权重
  punctuation: {
    multipleExclamation: 10,  // !!!
    multipleQuestion: 8,      // ???
    allCaps: 15               // 全大写
  },
  
  // 重复提问检测
  repetition: {
    threshold: 3,             // 重复3次
    score: 20
  }
};

export function calculateSentiment(
  message: string, 
  history: Message[]
): SentimentResult {
  let score = 0;
  const triggers: string[] = [];
  const keywords: string[] = [];
  const lowerMsg = message.toLowerCase();
  
  // 1. 检测显式指令
  if (SENTIMENT_RULES.explicitHandoff.some(w => lowerMsg.includes(w))) {
    score = 100;
    triggers.push('显式转人工请求');
    keywords.push('转人工');
    return { score, level: 'critical', triggers, keywords };
  }
  
  // 2. 检测负面情绪词
  SENTIMENT_RULES.negativeWords.strong.forEach(word => {
    if (lowerMsg.includes(word)) {
      score += 30;
      keywords.push(word);
    }
  });
  
  SENTIMENT_RULES.negativeWords.medium.forEach(word => {
    if (lowerMsg.includes(word)) {
      score += 15;
      keywords.push(word);
    }
  });
  
  // 3. 检测标点
  if (/!{2,}/.test(message)) {
    score += SENTIMENT_RULES.punctuation.multipleExclamation;
    triggers.push('强烈情绪标点');
  }
  
  // 4. 检测重复
  const repeatCount = history.filter(m => 
    m.role === 'user' && 
    similarity(m.content, message) > 0.8
  ).length;
  
  if (repeatCount >= SENTIMENT_RULES.repetition.threshold) {
    score += SENTIMENT_RULES.repetition.score;
    triggers.push(`重复提问${repeatCount}次`);
  }
  
  // 确定等级
  let level: SentimentLevel = 'normal';
  if (score >= 71) level = 'critical';
  else if (score >= 41) level = 'warning';
  
  return { 
    score: Math.min(score, 100), 
    level, 
    triggers, 
    keywords 
  };
}
```

### 路由决策算法

```typescript
// hooks/useRouterAgent.ts

export function makeRoutingDecision(
  sentiment: SentimentResult,
  intent: IntentResult
): RouterResult {
  // 最高优先级: 显式转人工
  if (intent.type === 'handoff_request' || sentiment.score >= 80) {
    return {
      decision: 'handoff',
      reason: intent.type === 'handoff_request' 
        ? '用户明确要求转人工'
        : `情绪分数过高 (${sentiment.score})`,
      priority: 1
    };
  }
  
  // 中等级别: 安抚策略
  if (sentiment.score >= 60 || sentiment.level === 'warning') {
    return {
      decision: 'empathetic',
      reason: `检测到负面情绪 (${sentiment.score}分)`,
      priority: 2
    };
  }
  
  // 默认: 继续对话
  return {
    decision: 'continue',
    reason: '情绪正常，继续标准流程',
    priority: 3
  };
}
```

---

## 状态管理

使用 React Context + useReducer 管理全局状态:

```typescript
// context/ChatContext.tsx

interface ChatState {
  messages: Message[];
  sentiment: SentimentResult | null;
  routerDecision: RouterResult | null;
  handoffState: HandoffState;
  agents: AgentState[];
}

type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'UPDATE_SENTIMENT'; payload: SentimentResult }
  | { type: 'UPDATE_ROUTER'; payload: RouterResult }
  | { type: 'UPDATE_HANDOFF'; payload: HandoffState }
  | { type: 'UPDATE_AGENT'; payload: AgentState };
```

---

## 性能优化

1. **消息虚拟滚动**: 大量消息时使用 react-window
2. **情绪分析防抖**: 用户输入停止500ms后分析
3. **记忆化**: useMemo/useCallback 缓存计算结果
4. **懒加载**: 工作流可视化组件延迟加载
