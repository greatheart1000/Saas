#!/bin/bash
# 快速部署和启动脚本

echo "========================================"
echo "  AI客服系统 - 一键部署"
echo "========================================"
echo ""

# 检查MySQL
echo "[检查MySQL服务]"
if command -v mysql &> /dev/null; then
    echo "✅ MySQL已安装: $(mysql --version | head -1)"
else
    echo "❌ 请确保MySQL已启动"
fi

echo ""
echo "========================================"
echo "📝 手动部署步骤："
echo "========================================"
echo ""

echo "步骤1: 安装Python依赖"
echo "--------------------------------------"
cat << 'EOF'
pip install fastapi uvicorn sqlalchemy pymysql pydantic pydantic-settings
pip install redis python-dotenv loguru httpx
pip install langchain langchain-openai openai
pip install chromadb rank-bm25

# 或使用清华镜像（更快）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn sqlalchemy pymysql
EOF

echo ""
echo "步骤2: 初始化数据库"
echo "--------------------------------------"
echo "python3 backend/init_db.py"
echo ""

echo "步骤3: 启动API服务"
echo "--------------------------------------"
echo "cd backend"
echo "python3 -m app.api.main"
echo ""

echo "步骤4: 访问前端界面"
echo "--------------------------------------"
echo "对话监控: http://localhost:8000/static/conversations.html"
echo "知识库管理: http://localhost:8000/static/knowledge.html"
echo "API文档:   http://localhost:8000/docs"
echo ""

echo "========================================"
echo "⚠️  重要提示："
echo "========================================"
echo ""
echo "1. 确保 MySQL已启动，用户名为root，密码为123456"
echo "2. 确保Redis已启动（端口6379）"
echo "3. 首次运行需要初始化数据库"
echo ""

# 提供快速安装命令
echo "========================================"
echo "⚡ 快速安装命令（复制执行）"
echo "========================================"
echo ""
echo "# 安装基础依赖"
echo "pip install fastapi uvicorn sqlalchemy pymysql pydantic redis"
echo ""
echo "# 初始化数据库"
echo "python3 backend/init_db.py"
echo ""
echo "# 启动服务"
echo "cd backend && python3 -m app.api.main"
echo ""

echo "========================================"
