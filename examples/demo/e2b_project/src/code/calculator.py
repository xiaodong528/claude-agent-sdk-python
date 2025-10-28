"""计算器应用生成器 - 在 E2B Sandbox 中运行

该脚本使用 Claude Agent SDK 生成一个简单的 Python 计算器应用。
生成的文件将包括:
- calculator.py: 包含基本算术运算函数
- README.md: 使用说明文档

该脚本由 apps/calculator.py 通过 agent_runner 在 Sandbox 中执行。
"""

import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock


async def main():
    """主函数: 使用 Claude Agent SDK 生成计算器应用"""

    # 配置 Agent 选项
    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Read", "Write", "Glob"],
        permission_mode="bypassPermissions",  # Sandbox 中跳过权限确认
        cwd="/home/user/workspace"
    )

    # 创建 Agent 客户端并执行任务
    async with ClaudeSDKClient(options) as client:
        # 发送任务查询
        await client.query("""
创建一个简单的 Python 计算器应用:

1. 创建 calculator.py 文件，包含以下函数:
   - add(a, b): 加法
   - subtract(a, b): 减法
   - multiply(a, b): 乘法
   - divide(a, b): 除法（处理除零错误）

2. 每个函数都要添加完整的 docstrings，说明参数、返回值和可能的异常

3. 创建 README.md 文件，包含:
   - 应用简介
   - 函数使用示例
   - 注意事项

请确保代码简洁、清晰，符合 Python 最佳实践。
        """)

        # 接收并处理响应
        async for message in client.receive_response():
            # 只打印文本内容，避免打印过多元数据
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, flush=True)
            else:
                # 其他消息类型也打印（用于调试）
                print(message, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
