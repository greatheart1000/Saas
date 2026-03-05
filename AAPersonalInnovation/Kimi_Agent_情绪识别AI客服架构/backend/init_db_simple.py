"""数据库初始化脚本 - 简化版（不依赖sqlalchemy）"""
import pymysql
import uuid
from datetime import datetime

# 数据库配置
DB_USER = "root"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "kimi_cs"


def create_database():
    """创建数据库"""
    try:
        print(f"连接到MySQL服务器 {DB_HOST}:{DB_PORT}...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        cursor = connection.cursor()

        # 创建数据库
        print(f"创建数据库 '{DB_NAME}'...")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        print(f"✅ 数据库 '{DB_NAME}' 创建成功")

        cursor.close()
        connection.close()
        return True

    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        print("\n请检查：")
        print("  1. MySQL是否已启动")
        print("  2. 用户名密码是否正确（root/123456）")
        print("  3. MySQL是否运行在localhost:3306")
        return False


def create_tables():
    """创建数据表"""
    try:
        print(f"\n连接到数据库 '{DB_NAME}'...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        cursor = connection.cursor()

        # 创建会话表
        print("创建数据表...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id VARCHAR(64) PRIMARY KEY COMMENT '会话ID',
                user_id VARCHAR(64) COMMENT '用户ID',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                message_count INT DEFAULT 0 COMMENT '消息数量',
                user_message_count INT DEFAULT 0 COMMENT '用户消息数',
                assistant_message_count INT DEFAULT 0 COMMENT 'AI消息数',
                status VARCHAR(20) DEFAULT 'active' COMMENT '状态',
                persona VARCHAR(20) COMMENT 'Persona类型',
                summary TEXT COMMENT '对话摘要',
                key_facts JSON COMMENT '关键信息',
                user_intent VARCHAR(100) COMMENT '用户意图',
                sentiment_trend VARCHAR(50) COMMENT '情绪趋势',
                handoff_reason TEXT COMMENT '转人工原因',
                handoff_time DATETIME COMMENT '转人工时间',
                metadata JSON COMMENT '元数据',
                INDEX idx_user_created (user_id, created_at),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✅ conversations 表创建成功")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id VARCHAR(64) PRIMARY KEY COMMENT '消息ID',
                conversation_id VARCHAR(64) NOT NULL COMMENT '会话ID',
                role VARCHAR(20) NOT NULL COMMENT '角色',
                content TEXT NOT NULL COMMENT '消息内容',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '消息时间戳',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                sentiment_score FLOAT COMMENT '情绪分数',
                sentiment_level VARCHAR(20) COMMENT '情绪等级',
                sentiment_triggers JSON COMMENT '情绪触发因素',
                sentiment_keywords JSON COMMENT '情绪关键词',
                intent_type VARCHAR(50) COMMENT '意图类型',
                intent_confidence FLOAT COMMENT '意图置信度',
                intent_entities JSON COMMENT '意图实体',
                router_decision VARCHAR(20) COMMENT '路由决策',
                router_reason TEXT COMMENT '决策原因',
                router_priority INT COMMENT '优先级',
                retrieved_docs JSON COMMENT '检索文档',
                metadata JSON COMMENT '元数据',
                response_time FLOAT COMMENT '响应时间',
                INDEX idx_conversation_timestamp (conversation_id, timestamp),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✅ messages 表创建成功")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id VARCHAR(64) PRIMARY KEY COMMENT '文档ID',
                title VARCHAR(200) NOT NULL COMMENT '标题',
                content TEXT NOT NULL COMMENT '内容',
                category VARCHAR(50) COMMENT '分类',
                tags JSON COMMENT '标签',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
                metadata JSON COMMENT '元数据',
                source VARCHAR(100) COMMENT '来源',
                source_file VARCHAR(255) COMMENT '源文件名',
                view_count INT DEFAULT 0 COMMENT '查看次数',
                use_count INT DEFAULT 0 COMMENT '使用次数',
                INDEX idx_category_active (category, is_active),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✅ knowledge_documents 表创建成功")

        connection.commit()
        cursor.close()
        connection.close()

        return True

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def insert_sample_knowledge():
    """插入示例知识文档"""
    try:
        print(f"\n插入示例知识文档...")

        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        cursor = connection.cursor()

        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM knowledge_documents WHERE is_active = TRUE")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  ⚠️  数据库已有 {count} 条知识文档，跳过插入")
            cursor.close()
            connection.close()
            return True

        # 示例知识文档
        knowledge_data = [
            ("订单查询方法", "订单", "订单查询方法：1. 登录官网，点击右上角'我的订单' 2. 输入订单号或手机号查询 3. 查看订单状态和物流信息。", ["订单", "查询", "常见问题"]),
            ("物流查询", "物流", "物流查询：在订单详情页可以看到实时物流信息。支持快递公司包括顺丰、中通、圆通等。发货后1-2天可查到物流信息。", ["物流", "快递", "配送"]),
            ("退款流程", "退款", "退款流程：1. 在订单详情页点击'申请退款' 2. 选择退款原因 3. 提交申请 4. 等待审核（1-3个工作日）5. 退款到账（3-5个工作日）。", ["退款", "退货", "流程"]),
            ("退款到账时间", "退款", "退款到账时间：审核通过后，原支付方式退款需3-5个工作日。支付宝/微信退款会自动退回支付账户。", ["退款", "到账", "时间"]),
            ("发货时间", "物流", "发货时间：现货商品下单后24小时内发货。预售商品按商品页面标注的时间发货。", ["发货", "时间", "物流"]),
            ("客服工作时间", "客服", "客服工作时间：在线客服7x24小时为您服务。人工客服工作时间是9:00-22:00。", ["客服", "工作时间"]),
            ("投诉渠道", "投诉", "投诉渠道：1. 在线客服转人工 2. 客服热线400-123-4567 3. 官方邮箱complaint@example.com", ["投诉", "客服热线"]),
            ("发票开具", "订单", "发票开具：订单完成后，可以在订单详情页申请开具电子发票。", ["发票", "电子发票"]),
        ]

        for i, (title, category, content, tags) in enumerate(knowledge_data, 1):
            doc_id = f"kb_{uuid.uuid4().hex[:8]}"
            tags_json = str(tags).replace("'", '"')  # 简化JSON处理

            cursor.execute("""
                INSERT INTO knowledge_documents (id, title, content, category, tags, source)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (doc_id, title, content, category, tags_json, "manual"))

            print(f"  ✅ {i}. {title}")

        connection.commit()
        cursor.close()
        connection.close()

        print(f"  ✅ 插入了 {len(knowledge_data)} 条示例知识文档")
        return True

    except Exception as e:
        print(f"❌ 插入示例数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI客服系统 - 数据库初始化")
    print("=" * 60)
    print(f"\n数据库配置:")
    print(f"  主机: {DB_HOST}:{DB_PORT}")
    print(f"  数据库: {DB_NAME}")
    print(f"  用户: {DB_USER}")
    print(f"  密码: {DB_PASSWORD}")

    # 步骤1: 创建数据库
    print("\n[1/3] 创建数据库...")
    if not create_database():
        return

    # 步骤2: 创建表
    print("\n[2/3] 创建数据表...")
    if not create_tables():
        return

    # 步骤3: 插入示例数据
    print("\n[3/3] 插入示例数据...")
    await insert_sample_knowledge()

    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print(f"\n数据库信息:")
    print(f"  主机: {DB_HOST}:{DB_PORT}")
    print(f"  数据库: {DB_NAME}")
    print(f"  用户: {DB_USER}")
    print(f"  表: conversations, messages, knowledge_documents")
    print(f"\n下一步:")
    print(f"  1. 启动API服务: cd backend && python3 -m app.api.main")
    print(f"  2. 对话监控: http://localhost:8000/static/conversations.html")
    print(f"  3. 知识库管理: http://localhost:8000/static/knowledge.html")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
