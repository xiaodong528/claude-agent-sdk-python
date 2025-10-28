import anyio
import pathlib
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)
async def memo_example():
    """开发简单的待办事项 Web 应用（包括前后端）"""
    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Edit", "Glob", "Grep", "Read", "TodoWrite", "Write"],
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": """
## 简单应用开发规范

### 代码质量
- 代码简洁、可读
- 无需添加注释

### UI 要求
- 使用原生 CSS 创建现代化、美观的界面（可以使用 CSS Grid/Flexbox）
- 响应式设计
- 良好的用户体验

### 部署要求
- 开发完成后启动所有服务
- 明确说明服务运行的端口号
- 提供启动命令
"""
        },
        permission_mode="bypassPermissions",
        continue_conversation=False,
        resume=None,
        cwd=pathlib.Path(__file__).parent,
        disallowed_tools=[],
        model=None,
        permission_prompt_tool_name=None,
        settings=None,
        add_dirs=[],
        env={},
        extra_args={},
        max_buffer_size=None,
        stderr=None,
        can_use_tool=None,
        hooks=None,
        user=None,
        include_partial_messages=False,
        fork_session=False,
        agents=None,
    )
    
    async with ClaudeSDKClient(options) as client:
        
        # 具体的项目需求
        await client.query("""
创建一个简单的待办事项（Todo List）Web 应用。

### 技术栈
- 前端：原生 HTML + CSS + JavaScript（不使用任何框架）
- 后端：FastAPI + SQLite
- 无需用户认证系统

### 功能需求（保持简单）
1. 待办事项 CRUD
   - 添加待办事项（仅标题和完成状态）
   - 查看待办事项列表
   - 标记完成/未完成
   - 删除待办事项

2. UI 要求
   - 单页应用，美观的卡片式布局
   - 输入框 + 添加按钮
   - 待办事项列表（带复选框和删除按钮）
   - 使用原生 CSS 美化界面（可以使用 CSS Grid/Flexbox）
   - 简单的动画效果

3. 简化要求
   - 无需登录注册
   - 无需分类标签
   - 无需搜索功能
   - 无需分页（简单列表即可）

开发完成后启动前后端服务，前端运行在localhost的8001端口，后端运行在localhost的8002端口，直到验证无误。！！！使用中文回复！！！
""")
        
        # 接收并打印响应
        async for message in client.receive_response():
            #print(message)
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)