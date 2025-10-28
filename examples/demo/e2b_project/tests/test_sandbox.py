"""测试 Sandbox 管理器

快速验证 SandboxManager 的基本功能。
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 将 src 目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from sandbox_manager import SandboxManager

# 加载环境变量
load_dotenv()


async def test_basic_usage():
    """测试基本使用:Context Manager 模式"""

    # 读取 Template ID
    template_id = None
    template_path = os.path.join(os.path.dirname(__file__), "..", ".template_id")
    with open(template_path) as f:
        for line in f:
            if line.startswith("TEMPLATE_ID="):
                template_id = line.split("=")[1].strip()
                break

    if not template_id:
        print("❌ 错误: 未找到 Template ID")
        return

    print(f"📋 使用 Template ID: {template_id}\n")

    # 使用 Context Manager 模式
    async with SandboxManager(
        template_id=template_id,
        envs={
            "TEST_VAR": "Hello from test!"
        }
    ) as manager:

        print("=" * 50)
        print("测试 1: 执行简单的 Python 代码")
        print("=" * 50)

        result = await manager.execute_code(
            "python",
            "print('Hello from E2B Sandbox!')"
        )

        print(f"输出: {result.stdout}")
        print(f"退出码: {result.exit_code}")

        print("\n" + "=" * 50)
        print("测试 2: 执行带环境变量的代码")
        print("=" * 50)

        result = await manager.execute_code(
            "python",
            "import os; print(f'TEST_VAR = {os.getenv(\"TEST_VAR\")}')"
        )

        print(f"输出: {result.stdout}")
        print(f"退出码: {result.exit_code}")

        print("\n" + "=" * 50)
        print("测试 3: 执行 Bash 命令")
        print("=" * 50)

        result = await manager.execute_code(
            "bash",
            "echo 'Current directory:' && pwd && echo 'Python version:' && python --version && echo 'Node version:' && node --version && echo 'npm version:' && npm --version && echo 'claude version:' && claude --version && whoami"
        )

        print(f"输出: {result.stdout}")
        print(f"退出码: {result.exit_code}")

    print("\n✅ 所有测试完成！Sandbox 已自动关闭。")


async def test_manual_lifecycle():
    """测试手动生命周期管理"""

    template_id = None
    template_path = os.path.join(os.path.dirname(__file__), "..", ".template_id")
    with open(template_path) as f:
        for line in f:
            if line.startswith("TEMPLATE_ID="):
                template_id = line.split("=")[1].strip()
                break

    if not template_id:
        print("❌ 错误: 未找到 Template ID")
        return

    print("\n" + "=" * 50)
    print("测试手动生命周期管理")
    print("=" * 50)

    manager = SandboxManager(template_id)

    try:
        # 手动启动
        await manager.start()

        # 执行代码
        result = await manager.execute_code(
            "python",
            "print('Manual lifecycle test')"
        )

        print(f"输出: {result.stdout}")
        print(f"退出码: {result.exit_code}")

    finally:
        # 手动关闭
        await manager.close()

    print("✅ 手动生命周期测试完成！")


async def main():
    """运行所有测试"""
    print("🧪 开始测试 SandboxManager\n")

    try:
        # 测试 Context Manager 模式
        await test_basic_usage()

        # 测试手动生命周期
        await test_manual_lifecycle()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
