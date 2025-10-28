"""Agent Runner 测试

测试 agent_runner 模块的核心功能。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_runner import run_code_in_sandbox, _read_template_id


async def test_read_template_id():
    """测试 1: 读取 Template ID"""
    print("\n" + "=" * 50)
    print("测试 1: 读取 Template ID")
    print("=" * 50)

    try:
        template_id = _read_template_id()
        print(f"✅ Template ID: {template_id}")
        assert template_id, "Template ID 不能为空"
        print("✅ 测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise


async def test_run_simple_code():
    """测试 2: 运行简单的测试脚本"""
    print("\n" + "=" * 50)
    print("测试 2: 运行简单的测试脚本")
    print("=" * 50)

    # 创建一个简单的测试脚本
    test_code = '''"""简单测试脚本"""
print("Hello from test script!")
print("Test completed successfully")
'''

    test_file = Path(__file__).parent.parent / "src" / "code" / "test_simple.py"
    test_file.write_text(test_code, encoding="utf-8")
    print(f"✅ 创建测试文件: {test_file.name}")

    try:
        result = await run_code_in_sandbox(
            code_file="test_simple.py",
            env_vars={
                "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN")
            }
        )

        print(f"\n退出码: {result['exit_code']}")
        assert result['exit_code'] == 0, f"退出码应为 0，实际为 {result['exit_code']}"
        print("✅ 测试通过")

    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
            print(f"🧹 清理测试文件: {test_file.name}")


async def test_file_not_found():
    """测试 3: 测试文件不存在的错误处理"""
    print("\n" + "=" * 50)
    print("测试 3: 文件不存在错误处理")
    print("=" * 50)

    try:
        await run_code_in_sandbox(
            code_file="non_existent_file.py",
            env_vars={
                "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN")
            }
        )
        print("❌ 测试失败: 应该抛出 FileNotFoundError")
        assert False, "应该抛出异常"
    except FileNotFoundError as e:
        print(f"✅ 正确捕获错误: {e}")
        print("✅ 测试通过")


async def test_calculator_generation():
    """测试 4: 运行计算器生成脚本（需要 API 配额）"""
    print("\n" + "=" * 50)
    print("测试 4: 计算器应用生成（可选）")
    print("=" * 50)

    # 检查是否有 ANTHROPIC_AUTH_TOKEN
    if not os.getenv("ANTHROPIC_AUTH_TOKEN"):
        print("⚠️  跳过: 缺少 ANTHROPIC_AUTH_TOKEN")
        print("✅ 测试跳过")
        return

    # 询问用户是否运行（避免消耗 API 配额）
    print("⚠️  此测试会调用 Claude API，消耗配额")
    print("建议: 手动运行 python src/apps/calculator.py 进行完整测试")
    print("✅ 测试跳过 (避免自动消耗 API 配额)")


async def main():
    """运行所有测试"""
    print("=" * 50)
    print("🧪 Agent Runner 测试套件")
    print("=" * 50)

    tests = [
        test_read_template_id,
        test_run_simple_code,
        test_file_not_found,
        test_calculator_generation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"错误: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    # 总结
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 总计: {passed + failed}")
    print("=" * 50)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
