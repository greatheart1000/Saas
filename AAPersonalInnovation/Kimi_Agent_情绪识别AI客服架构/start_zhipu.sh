#!/bin/bash
# 快速启动脚本 - 智谱AI版本

echo "========================================"
echo "  AI客服系统 - 智谱AI GLM-5 版本"
echo "========================================"
echo ""

# 检查Python版本
echo "[1] 检查Python环境..."
python3 --version

# 检查依赖
echo ""
echo "[2] 检查依赖安装..."
python3 -c "import fastapi" 2>/dev/null && echo "✅ fastapi已安装" || echo "⚠️  fastapi未安装"
python3 -c "import openai" 2>/dev/null && echo "✅ openai已安装" || echo "⚠️  openai未安装"
python3 -c "import pymysql" 2>/dev/null && echo "✅ pymysql已安装" || echo "⚠️  pymysql未安装"

# 检查配置文件
echo ""
echo "[3] 检查配置文件..."
if [ -f "backend/.env" ]; then
    echo "✅ .env配置文件存在"
    grep -q "LLM_PROVIDER=zhipu" backend/.env && echo "✅ 智谱AI配置正确" || echo "⚠️  LLM provider未设置为zhipu"
else
    echo "❌ .env配置文件不存在"
fi

# 检查数据库
echo ""
echo "[4] 检查数据库连接..."
mysql -uroot -p123456 -e "USE kimi_cs; SELECT COUNT(*) as doc_count FROM knowledge_documents;" 2>/dev/null && echo "✅ 数据库连接正常" || echo "⚠️  数据库连接失败"

echo ""
echo "========================================"
echo "📝 启动选项："
echo "========================================"
echo ""
echo "选项1: 测试智谱AI配置"
echo "  cd backend && python3 test_zhipu.py"
echo ""
echo "选项2: 启动API服务"
echo "  cd backend && python3 -m app.api.main"
echo ""
echo "选项3: 访问前端界面"
echo "  对话监控: http://localhost:8000/static/conversations.html"
echo "  知识库管理: http://localhost:8000/static/knowledge.html"
echo "  API文档: http://localhost:8000/docs"
echo ""

# 如果传入参数 "test"，则运行测试
if [ "$1" == "test" ]; then
    echo "========================================"
    echo "🧪 运行智谱AI测试..."
    echo "========================================"
    cd backend && python3 test_zhipu.py
fi

# 如果传入参数 "start"，则启动服务
if [ "$1" == "start" ]; then
    echo "========================================"
    echo "🚀 启动API服务..."
    echo "========================================"
    cd backend && python3 -m app.api.main
fi

echo ""
echo "========================================"
