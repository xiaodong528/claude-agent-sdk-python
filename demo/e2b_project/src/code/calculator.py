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
        system_prompt={
            "type": "preset",
            "preset": "claude_code"
        },
        permission_mode="bypassPermissions",  # Sandbox 中跳过权限确认
        cwd="/home/user/workspace" ,
        mcp_servers=""
    )

    # 创建 Agent 客户端并执行任务
    async with ClaudeSDKClient(options) as client:
        # 发送任务查询
        await client.query("""
创建一个带 Web 前端的计算器应用:

1. 创建 index.html 文件:
   - 美观的计算器界面（使用原生 HTML + CSS + JavaScript）
   - 实现加减乘除运算功能
   - 支持键盘输入（数字键和运算符）
   - 显示计算历史记录
   - 响应式设计，适配不同屏幕
   - 使用现代化的 CSS 样式（渐变、阴影、圆角）

2. 启动 Web 服务:
   - 使用 Python 的 http.server 模块在 3000 端口启动服务
   - 确保服务在后台持续运行（使用 nohup 或 & 后台运行）
   - 服务启动后打印确认消息

3. 创建 README.md 文件:
   - 应用说明
   - 功能列表
   - 访问方式（本地和远程）
   - 使用截图或功能演示

要求:
- 界面美观、现代化
- 代码简洁、注释清晰
- 完成后立即启动服务并保持运行
- 使用中文回复所有消息
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
