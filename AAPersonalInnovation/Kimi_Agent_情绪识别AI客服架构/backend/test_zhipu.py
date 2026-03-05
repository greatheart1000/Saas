"""测试智谱AI GLM-5调用"""
import asyncio
from openai import AsyncOpenAI
from app.core.config import settings


async def test_zhipu_connection():
    """测试智谱AI连接和调用"""

    print("=" * 60)
    print("🧪 智谱AI GLM-5 连接测试")
    print("=" * 60)

    print(f"\n配置信息:")
    print(f"  Provider: {settings.llm_provider}")
    print(f"  API Key: {settings.llm_api_key[:20]}...")
    print(f"  Base URL: {settings.llm_base_url}")
    print(f"  Model: {settings.llm_model}")

    try:
        # 初始化客户端
        client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

        print("\n[测试1] 简单对话测试...")
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},
                {"role": "user", "content": "请用一句话介绍你自己"}
            ],
            top_p=0.7,
            temperature=0.9
        )

        result = response.choices[0].message.content
        print(f"✅ 连接成功！")
        print(f"回复: {result}")

        print("\n[测试2] JSON格式输出测试...")
        response_json = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "你是一个情绪分析专家。返回JSON格式结果。"},
                {"role": "user", "content": "分析这句话的情绪：我很满意这个服务！"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result_json = response_json.choices[0].message.content
        print(f"✅ JSON输出成功！")
        print(f"结果: {result_json}")

        print("\n[测试3] 情绪分析功能测试...")

        system_prompt = """你是一个情绪分析专家。分析用户消息的情绪状态。

返回JSON格式：
{
    "score": 0-1之间的浮点数，表示情绪强度（0=平静，1=极度愤怒/不满），
    "level": "normal" | "warning" | "critical",
    "triggers": ["触发因素1", "触发因素2"],
    "keywords": ["关键词1", "关键词2"],
    "confidence": 0-1之间的置信度
}

判断标准：
- normal (0-0.4): 情绪平稳，正常咨询
- warning (0.4-0.7): 情绪略显不耐烦或不满
- critical (0.7-1.0): 情绪严重不满，愤怒，需要立即处理"""

        response_sentiment = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "这个产品质量太差了，我要退款！"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        sentiment_result = response_sentiment.choices[0].message.content
        print(f"✅ 情绪分析成功！")
        print(f"结果: {sentiment_result}")

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！智谱AI GLM-5配置正确！")
        print("=" * 60)

        await client.close()

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_service():
    """测试LLM服务封装"""

    print("\n\n" + "=" * 60)
    print("🧪 LLM服务集成测试")
    print("=" * 60)

    try:
        from app.services.llm_service import llm_service

        # 初始化服务
        await llm_service.initialize()
        print("✅ LLM服务初始化成功")

        # 测试情绪分析
        print("\n[测试] 情绪分析...")
        sentiment = await llm_service.detect_sentiment(
            message="这个产品质量太差了，我要退款！",
            history=[]
        )
        print(f"✅ 情绪分析结果: {sentiment}")

        # 测试意图识别
        print("\n[测试] 意图识别...")
        intent = await llm_service.detect_intent(
            message="我想查询一下我的订单状态",
            history=[]
        )
        print(f"✅ 意图识别结果: {intent}")

        print("\n" + "=" * 60)
        print("✅ LLM服务测试通过！")
        print("=" * 60)

        await llm_service.close()

        return True

    except Exception as e:
        print(f"\n❌ LLM服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试1: 直接调用智谱AI
    print("\n📋 开始测试...\n")

    success1 = asyncio.run(test_zhipu_connection())

    # 测试2: 通过LLM服务调用
    success2 = asyncio.run(test_llm_service())

    if success1 and success2:
        print("\n\n🎉 所有测试完成！系统已准备就绪！")
        print("\n下一步:")
        print("  1. 启动API服务: cd backend && python3 -m app.api.main")
        print("  2. 访问前端: http://localhost:8000/static/conversations.html")
    else:
        print("\n\n⚠️  部分测试失败，请检查配置")
