"""功能演示脚本 - 展示三个核心增强功能"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"


async def demo_context_window():
    """演示1：上下文窗口管理"""
    print("\n" + "=" * 60)
    print("📊 演示1：上下文窗口管理")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        session_id = "demo_context_window"

        # 模拟多轮对话
        conversations = [
            "你好",
            "我想查询订单",
            "订单号是12345",
            "发货了吗？",
            "什么时候能到？",
            "我想退款",
        ]

        print("\n💡 说明：系统会为不同任务使用不同的上下文窗口大小")
        print("  - 情绪分析：最近5条消息")
        print("  - 意图识别：最近5条消息")
        print("  - 生成回复：最近10条消息")
        print("  - 生成总结：最近20条消息")

        for i, msg in enumerate(conversations, 1):
            print(f"\n--- 对话轮次 {i} ---")
            print(f"用户: {msg}")

            # 发送消息（使用默认上下文窗口）
            response = await client.post(
                f"{BASE_URL}/chat/send",
                json={
                    "message": msg,
                    "session_id": session_id
                }
            )
            result = response.json()

            print(f"AI: {result['message'][:80]}...")
            print(f"上下文消息数: {len([m for m in result.get('history', [])])}")

        print("\n✅ 上下文窗口管理演示完成")


async def demo_auto_summary():
    """演示2：自动摘要功能"""
    print("\n" + "=" * 60)
    print("📝 演示2：自动摘要功能")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        session_id = "demo_auto_summary"

        print("\n💡 说明：系统会在以下情况自动触发摘要")
        print("  - 消息数达到阈值（默认15条）")
        print("  - 时间间隔达到阈值（默认10分钟）")

        # 模拟快速对话（触发消息数阈值）
        print("\n--- 模拟快速对话 ---")
        conversations = [
            "你好",
            "订单号12345发货了吗？",
            "什么时候到？",
            "我想改地址",
            "能帮我查一下吗？",
            "谢谢",
            "还有问题",
            "物流太慢了",
            "你们服务太差",
            "我要投诉",
            "赶紧处理",
            "到底什么时候到",
            "怎么还不发货",
            "我要退款",
            "不想等了",  # 第15条，触发摘要
        ]

        for i, msg in enumerate(conversations, 1):
            await client.post(
                f"{BASE_URL}/chat/send",
                json={"message": msg, "session_id": session_id}
            )
            if i % 5 == 0:
                print(f"已发送 {i} 条消息...")

        print("\n--- 查看自动生成的摘要 ---")
        response = await client.get(f"{BASE_URL}/chat/summary/{session_id}")
        summary = response.json()

        print(f"\n📋 对话摘要:")
        print(f"  {summary['summary']}")
        print(f"\n🔑 关键信息:")
        for fact in summary.get('key_facts', []):
            print(f"  - {fact}")
        print(f"\n🎯 用户意图: {summary['user_intent']}")
        print(f"😊 情绪趋势: {summary['sentiment_trend']}")
        print(f"📊 消息总数: {summary['message_count']}")

        print("\n✅ 自动摘要演示完成")


async def demo_persona():
    """演示3：Persona拟人化系统"""
    print("\n" + "=" * 60)
    print("🎭 演示3：Persona拟人化系统")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        print("\n💡 说明：系统提供5种不同的客服人格")
        print("  - friendly: 亲切友好")
        print("  - cute: 可爱热情")
        print("  - mature: 成熟冷静")
        print("  - professional: 专业严谨")
        print("  - humorous: 幽默风趣")

        # 查看所有Persona
        print("\n--- 获取所有Persona ---")
        response = await client.get(f"{BASE_URL}/chat/personas")
        personas = response.json()

        for p in personas['personas']:
            print(f"\n  🎭 {p['name']}")
            print(f"     描述: {p['description']}")
            print(f"     风格: {p['response_style']}")

        # 测试不同Persona的回复差异
        test_query = "我想退款"

        print(f"\n--- 测试不同Persona对同一查询的回复差异 ---")
        print(f"用户查询: {test_query}\n")

        for persona_type in ["friendly", "cute", "mature", "professional", "humorous"]:
            session_id = f"demo_persona_{persona_type}"

            # 发送消息
            response = await client.post(
                f"{BASE_URL}/chat/send",
                json={
                    "message": test_query,
                    "session_id": session_id,
                    "persona": persona_type
                }
            )
            result = response.json()

            # 获取Persona信息
            persona_info = next(
                (p for p in personas['personas'] if p['type'] == persona_type),
                None
            )

            print(f"【{persona_info['name'] if persona_info else persona_type}】")
            print(f"  回复: {result['message']}")
            print()

        print("✅ Persona拟人化演示完成")


async def demo_persona_session_level():
    """演示4：会话级别的Persona设置"""
    print("\n" + "=" * 60)
    print("🔧 演示4：会话级别的Persona设置")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        session_id = "demo_session_persona"

        print("\n💡 说明：可以为会话设置Persona，后续所有回复都使用该人格")

        # 设置Persona
        print("\n--- 设置会话Persona为 cute ---")
        response = await client.post(
            f"{BASE_URL}/chat/set-persona",
            json={
                "session_id": session_id,
                "persona": "cute"
            }
        )
        result = response.json()
        print(f"✅ {result['message']}")
        print(f"   Persona: {result['persona_name']}")
        print(f"   描述: {result['description']}")

        # 后续对话自动使用该Persona
        print("\n--- 后续对话自动使用可爱风格 ---")
        queries = ["你好", "订单到了吗？", "太慢了"]

        for msg in queries:
            response = await client.post(
                f"{BASE_URL}/chat/send",
                json={
                    "message": msg,
                    "session_id": session_id
                    # 不需要指定persona，自动使用会话设置的
                }
            )
            result = response.json()
            print(f"\n用户: {msg}")
            print(f"AI: {result['message']}")

        # 查看会话Persona
        print("\n--- 查看会话Persona ---")
        response = await client.get(f"{BASE_URL}/chat/persona/{session_id}")
        result = response.json()
        print(f"当前Persona: {result.get('persona', '未设置')}")

        print("\n✅ 会话级别Persona演示完成")


async def main():
    """运行所有演示"""
    print("\n" + "🎉" * 30)
    print("   AI客服系统 - 功能增强演示")
    print("🎉" * 30)

    try:
        # 演示1：上下文窗口管理
        await demo_context_window()

        # 等待一下
        await asyncio.sleep(2)

        # 演示2：自动摘要
        await demo_auto_summary()

        # 等待一下
        await asyncio.sleep(2)

        # 演示3：Persona拟人化
        await demo_persona()

        # 等待一下
        await asyncio.sleep(2)

        # 演示4：会话级别Persona
        await demo_persona_session_level()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)

        print("\n📚 更多信息请查看:")
        print("   - 配置文件: .env")
        print("   - 功能说明: 功能增强说明.md")
        print("   - API文档: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        print("\n请确保:")
        print("  1. API服务已启动 (python -m app.api.main)")
        print("  2. 已配置LLM API Key")
        print("  3. Redis和数据库已连接")


if __name__ == "__main__":
    asyncio.run(main())
