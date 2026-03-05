"""数据库初始化脚本"""
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
import uuid
from datetime import datetime

# 数据库配置
DB_USER = "root"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "kimi_cs"

# 同步引擎用于创建数据库
SYNC_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"

# 异步引擎
ASYNC_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def create_database():
    """创建数据库"""
    try:
        import pymysql
        connection = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor()

        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ 数据库 '{DB_NAME}' 创建成功")

        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        return False


async def create_tables():
    """创建表"""
    try:
        from app.models.database_models import Base

        # 使用同步引擎创建表
        from sqlalchemy import create_engine
        engine = create_engine(SYNC_DATABASE_URL + f"/{DB_NAME}", echo=True)

        Base.metadata.create_all(engine)
        print("✅ 数据表创建成功")

        engine.dispose()
        return True
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def insert_sample_knowledge():
    """插入示例知识文档"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.database_models import KnowledgeDocument

        engine = create_engine(SYNC_DATABASE_URL + f"/{DB_NAME}", echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        # 检查是否已有数据
        existing = session.query(KnowledgeDocument).count()
        if existing > 0:
            print(f"⚠️  数据库已有 {existing} 条知识文档，跳过插入")
            session.close()
            engine.dispose()
            return True

        # 插入示例知识文档
        sample_docs = [
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="订单查询方法",
                content="订单查询方法：1. 登录官网，点击右上角'我的订单' 2. 输入订单号或手机号查询 3. 查看订单状态和物流信息。也可以在手机App中查询。",
                category="订单",
                tags=["订单", "查询", "常见问题"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="物流查询",
                content="物流查询：在订单详情页可以看到实时物流信息。支持快递公司包括顺丰、中通、圆通等。发货后1-2天可查到物流信息。",
                category="物流",
                tags=["物流", "快递", "配送"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="退款流程",
                content="退款流程：1. 在订单详情页点击'申请退款' 2. 选择退款原因 3. 提交申请 4. 等待审核（1-3个工作日）5. 退款到账（3-5个工作日）。审核通过后原路返回。",
                category="退款",
                tags=["退款", "退货", "流程"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="退款到账时间",
                content="退款到账时间：审核通过后，原支付方式退款需3-5个工作日。支付宝/微信退款会自动退回支付账户。银行卡退款可能需要5-7个工作日。",
                category="退款",
                tags=["退款", "到账", "时间"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="发货时间",
                content="发货时间：现货商品下单后24小时内发货。预售商品按商品页面标注的时间发货。大件商品如家具可能需要3-5天准备时间。",
                category="物流",
                tags=["发货", "时间", "物流"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="修改订单",
                content="修改订单：未发货的订单可以联系客服修改收货地址和联系方式。已发货的订单无法修改，请联系快递公司修改。",
                category="订单",
                tags=["修改", "收货地址"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="质量问题退货",
                content="质量问题退货：收到商品后如有质量问题，支持7天无理由退货。在订单详情页申请退货，上传问题照片，我们会安排快递上门取件。",
                category="售后",
                tags=["退货", "质量问题", "7天无理由"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="客服工作时间",
                content="客服工作时间：在线客服7x24小时为您服务。人工客服工作时间是9:00-22:00。其他时间为智能客服服务。",
                category="客服",
                tags=["客服", "工作时间"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="投诉渠道",
                content="投诉渠道：如对服务不满意，可以通过以下渠道投诉：1. 在线客服转人工 2. 客服热线400-123-4567 3. 官方邮箱complaint@example.com",
                category="投诉",
                tags=["投诉", "客服热线"],
                source="manual"
            ),
            KnowledgeDocument(
                id=f"kb_{uuid.uuid4().hex[:8]}",
                title="发票开具",
                content="发票开具：订单完成后，可以在订单详情页申请开具电子发票，发票类型可选择增值税普通发票或专用发票。",
                category="订单",
                tags=["发票", "电子发票"],
                source="manual"
            ),
        ]

        for doc in sample_docs:
            session.add(doc)

        session.commit()
        print(f"✅ 插入了 {len(sample_docs)} 条示例知识文档")

        session.close()
        engine.dispose()
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
    print(f"  用户: {DB_USER}")
    print(f"  数据库: {DB_NAME}")

    # 步骤1: 创建数据库
    print("\n[1/3] 创建数据库...")
    if not create_database():
        print("\n❌ 数据库初始化失败！请检查：")
        print("  1. MySQL是否已启动")
        print("  2. 用户名密码是否正确（root/123456）")
        print("  3. MySQL是否运行在localhost:3306")
        return

    # 步骤2: 创建表
    print("\n[2/3] 创建数据表...")
    if not await create_tables():
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
    print(f"  1. 启动API服务: cd backend && python -m app.api.main")
    print(f"  2. 访问对话监控: http://localhost:8000/static/conversations.html")
    print(f"  3. 访问知识库管理: http://localhost:8000/static/knowledge.html")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
