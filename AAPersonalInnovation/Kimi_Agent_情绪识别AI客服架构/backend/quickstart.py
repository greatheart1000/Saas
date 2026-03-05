"""快速启动脚本 - 初始化知识库并启动服务"""
import asyncio
import sys
from pathlib import Path

from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag_service import rag_service
from app.services.llm_service import llm_service


async def initialize_knowledge_base():
    """初始化示例知识库"""
    logger.info("正在初始化知识库...")

    # 示例知识
    sample_knowledge = [
        {
            "text": "订单查询：登录官网后，点击右上角'我的订单'，即可查看所有订单状态。也可以在手机App中进入'我的'页面查看。",
            "metadata": {"category": "订单", "keywords": "订单查询,我的订单"}
        },
        {
            "text": "物流查询：在订单详情页可以看到物流信息。我们支持顺丰、中通、圆通等快递，发货后1-2天可查到物流信息。",
            "metadata": {"category": "物流", "keywords": "物流,快递,配送"}
        },
        {
            "text": "退款流程：1. 在订单详情页点击'申请退款' 2. 选择退款原因 3. 提交申请 4. 等待审核（1-3个工作日） 5. 退款到账（3-5个工作日）",
            "metadata": {"category": "退款", "keywords": "退款,退货,退款流程"}
        },
        {
            "text": "退款到账时间：审核通过后，原支付方式退款需3-5个工作日。如使用支付宝或微信，退款会自动退回支付账户。",
            "metadata": {"category": "退款", "keywords": "退款时间,到账"}
        },
        {
            "text": "发货时间：现货商品下单后24小时内发货，预售商品按商品页面标注的时间发货。大件商品如家具可能需要3-5天准备时间。",
            "metadata": {"category": "物流", "keywords": "发货时间,发货"}
        },
        {
            "text": "修改订单：未发货的订单可以联系客服修改收货地址和联系方式。已发货的订单无法修改，请联系快递公司。",
            "metadata": {"category": "订单", "keywords": "修改订单,收货地址"}
        },
        {
            "text": "取消订单：未发货的订单可以在订单详情页取消。已发货的订单需要先拒收快递，等商家收到退货后再申请退款。",
            "metadata": {"category": "订单", "keywords": "取消订单"}
        },
        {
            "text": "质量问题退货：收到商品后如有质量问题，支持7天无理由退货。请在订单详情页申请退货，上传问题照片，我们会安排快递上门取件。",
            "metadata": {"category": "售后", "keywords": "质量问题,退货,7天无理由"}
        },
        {
            "text": "客服工作时间：在线客服7x24小时为您服务。人工客服工作时间是9:00-22:00，其他时间为智能客服服务。",
            "metadata": {"category": "客服", "keywords": "客服,工作时间,人工客服"}
        },
        {
            "text": "投诉渠道：如对服务不满意，可以通过以下渠道投诉：1. 在线客服转人工 2. 客服热线400-123-4567 3. 官方邮箱投诉@example.com",
            "metadata": {"category": "投诉", "keywords": "投诉,客服热线,邮箱"}
        },
        {
            "text": "发票开具：订单完成后，可以在订单详情页申请开具电子发票，发票类型可选择增值税普通发票或专用发票。",
            "metadata": {"category": "发票", "keywords": "发票,电子发票,增值税"}
        },
        {
            "text": "优惠券使用：下单时在结算页面可以选择使用优惠券。每个订单只能使用一张优惠券，优惠券不可叠加使用。",
            "metadata": {"category": "优惠", "keywords": "优惠券,优惠,折扣"}
        },
        {
            "text": "积分获取：每消费1元可获得1积分，积分可以在下次购物时抵扣现金。100积分=1元。",
            "metadata": {"category": "积分", "keywords": "积分,会员"}
        },
        {
            "text": "账户安全：请保护好您的账户密码，不要轻易泄露给他人。如发现账户异常，请立即修改密码并联系客服。",
            "metadata": {"category": "安全", "keywords": "账户,密码,安全"}
        },
        {
            "text": "收货验货：收到快递时请先验货再签收。如发现外包装破损或商品缺失，请拒收并及时联系客服。",
            "metadata": {"category": "收货", "keywords": "验货,签收,拒收"}
        },
    ]

    try:
        await rag_service.initialize()

        # 清空旧数据
        await rag_service.clear_knowledge_base()

        # 添加新知识
        texts = [item["text"] for item in sample_knowledge]
        ids = [f"kb_{i:03d}" for i in range(len(texts))]
        metadatas = [item["metadata"] for item in sample_knowledge]

        success = await rag_service.add_knowledge(texts, ids, metadatas)

        if success:
            logger.success(f"✅ 知识库初始化完成，共添加 {len(texts)} 条知识")
        else:
            logger.error("❌ 知识库初始化失败")

    except Exception as e:
        logger.error(f"知识库初始化错误: {e}")


async def test_search():
    """测试搜索功能"""
    logger.info("正在测试搜索功能...")

    test_queries = [
        "怎么查询订单",
        "退款多久到账",
        "发货需要多久",
        "如何投诉",
    ]

    for query in test_queries:
        logger.info(f"\n🔍 测试查询: {query}")
        result = await rag_service.hybrid_search(query, top_k=3)

        logger.info(f"   找到 {result.total_found} 条相关结果:")
        for i, doc in enumerate(result.documents[:3], 1):
            logger.info(f"   [{i}] 相关度: {doc.score:.2f}")
            logger.info(f"       内容: {doc.content[:100]}...")


async def main():
    """主函数"""
    print("=" * 60)
    print("🚀 AI客服系统 - 快速启动")
    print("=" * 60)

    # 初始化知识库
    await initialize_knowledge_base()

    # 测试搜索
    await test_search()

    print("\n" + "=" * 60)
    print("✅ 初始化完成！")
    print("=" * 60)
    print("\n现在可以启动服务:")
    print("  python -m app.api.main")
    print("\n或使用uvicorn:")
    print("  uvicorn app.api.main:app --reload")
    print("\n服务启动后访问:")
    print("  📚 API文档: http://localhost:8000/docs")
    print("  📊 监控面板: http://localhost:8000/dashboard/monitor_dashboard.html")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
