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

from agent_runner import run_code_with_service


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
        # 调用 agent_runner 执行 code/calculator.py 并启动 Web 服务
        result = await run_code_with_service(
            code_file="calculator.py",
            service_port=3000,  # 前端服务端口
            env_vars={
                "ANTHROPIC_AUTH_TOKEN": anthropic_token
            },
            wait_time=5  # 等待 5 秒让服务完全启动
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

        # 显示服务 URL
        if result.get('service_url'):
            print("\n" + "=" * 60)
            print("🌐 Web 服务信息")
            print("=" * 60)
            print(f"✅ 前端地址: {result['service_url']}")
            print(f"✅ Sandbox ID: {result['sandbox_id']}")
            print("\n💡 使用提示:")
            print("  1. 在浏览器中打开上述地址访问计算器应用")
            print("  2. Sandbox 将保持运行约 1 小时（3600 秒）")
            print("  3. 服务超时后会自动关闭")
            print("=" * 60)
        else:
            print("\n⚠️  未获取到服务 URL")

        print()

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
