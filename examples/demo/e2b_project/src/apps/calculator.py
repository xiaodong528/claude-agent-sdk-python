"""计算器应用运行器

该脚本调用 agent_runner 在 E2B Sandbox 中执行 code/calculator.py,
使用 Claude Agent SDK 生成一个简单的计算器应用。

使用方法:
    python src/apps/calculator.py

环境要求:
    - E2B_API_KEY: E2B API 密钥
    - ANTHROPIC_AUTH_TOKEN: Anthropic API 令牌
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径，以便导入 agent_runner
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_runner import run_code_in_sandbox


async def main():
    """运行计算器应用生成器"""
    print("=" * 60)
    print("🧮 计算器应用生成器")
    print("=" * 60)
    print()

    # 检查环境变量
    anthropic_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    if not anthropic_token:
        print("❌ 错误: 缺少 ANTHROPIC_AUTH_TOKEN 环境变量")
        print("请在 .env 文件中配置或设置环境变量")
        sys.exit(1)

    e2b_key = os.getenv("E2B_API_KEY")
    if not e2b_key:
        print("❌ 错误: 缺少 E2B_API_KEY 环境变量")
        print("请在 .env 文件中配置或设置环境变量")
        sys.exit(1)

    print("✅ 环境变量检查通过\n")

    try:
        # 调用 agent_runner 执行 code/calculator.py
        result = await run_code_in_sandbox(
            code_file="calculator.py",
            env_vars={
                "ANTHROPIC_AUTH_TOKEN": anthropic_token
            }
        )

        # 显示结果
        print("\n" + "=" * 60)
        print("📊 执行结果")
        print("=" * 60)
        print(f"✅ 退出码: {result['exit_code']}")

        if result['exit_code'] == 0:
            print("✅ 应用生成成功!")
        else:
            print("⚠️  应用生成过程出现问题")

        if result['files']:
            print(f"\n📂 生成的文件 ({len(result['files'])} 个):")
            for file in result['files']:
                print(f"  - {file}")
        else:
            print("\n⚠️  未发现生成的文件")

        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n❌ 文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
