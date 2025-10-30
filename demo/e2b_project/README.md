# E2B + Claude Agent SDK 集成项目

## 项目简介

本项目演示如何将 Claude Agent SDK 与 E2B Sandbox 集成，实现 AI Agent 在隔离环境中安全执行代码生成任务。

**核心特性：**
- ✅ 使用 E2B Template Python API 定义 Sandbox 环境（替代 Dockerfile）
- ✅ 在 Sandbox 中运行 Claude Agent SDK 生成代码
- ✅ 支持 Web 服务模式，获取外部可访问 URL
- ✅ 完整的生命周期管理和错误处理

## 项目结构

```
e2b_project/
├── src/
│   ├── template.py              # E2B Template 定义
│   ├── build_template.py        # Template 构建脚本
│   ├── sandbox_manager.py       # Sandbox 生命周期管理
│   ├── agent_runner.py          # Agent 运行器（核心）
│   ├── code/                    # AI Agent 脚本（在 Sandbox 内执行）
│   │   ├── calculator.py        # 计算器应用生成器
│   │   └── memo.py              # 备忘录应用生成器
│   └── apps/                    # 应用运行器（在宿主机执行）
│       └── calculator.py        # 计算器应用运行器
├── docs/                        # 详细文档
│   ├── 01-architecture.md       # 架构设计
│   ├── 02-template-guide.md     # Template API 使用指南
│   ├── 03-sandbox-guide.md      # Sandbox 管理指南
│   ├── 04-agent-integration.md  # Agent 集成指南
│   ├── 05-best-practices.md     # 最佳实践
│   └── 06-troubleshooting.md    # 故障排除
├── tests/                       # 测试文件
├── .env.example                 # 环境变量示例
└── e2b_claude_agent_sdk.ipynb  # Jupyter 示例笔记本
```

## 快速开始

### 1. 环境准备

```bash
# 1. 克隆项目
cd examples/demo/e2b_project

# 2. 安装依赖
pip install e2b python-dotenv claude-agent-sdk

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys:
# - E2B_API_KEY: 从 https://e2b.dev/dashboard 获取
# - ANTHROPIC_AUTH_TOKEN: 从智谱 AI 获取
```

### 2. 构建 E2B Template

```bash
# 运行构建脚本
python src/build_template.py
```

**预期输出：**
```
🚀 开始构建 E2B Template...
============================================================
📋 构建配置:
   别名: claude-agent-sandbox
   CPU: 2 核
   内存: 2048 MB
...
✅ Template 构建成功！
Template ID: xxx...xxx
✅ Template ID 已保存到 .template_id 文件
```

### 3. 运行示例应用

#### 示例 1: 计算器 Web 应用（Web 服务模式）

```bash
# 运行计算器应用生成器
python src/apps/calculator.py
```

**功能：**
- AI Agent 在 Sandbox 中生成带 Web 前端的计算器应用
- 自动启动 HTTP 服务（端口 3000）
- 返回外部可访问的 URL（如 `https://xxx.e2b.dev`）

**预期输出：**
```
🧮 计算器应用生成器
============================================================
✅ 环境变量检查通过
📋 读取 Template ID...
✅ Template ID: xxx...xxx
📄 读取代码文件: calculator.py
✅ 代码大小: 2156 字节
🚀 创建 Sandbox...
✅ Sandbox 已创建 (ID: xxx)
📤 上传代码到 Sandbox...
✅ 代码文件已上传
🚀 执行代码: python /home/user/workspace/calculator.py
==================================================
[Agent] 正在创建计算器应用...
[Agent] 生成 index.html...
[Agent] 启动 HTTP 服务...
==================================================
✅ 执行完成 (退出码: 0)
⏳ 等待服务启动 (5 秒)...
🌐 获取服务 URL (端口 3000)...
✅ 服务 URL: https://xxx.e2b.dev
📂 检查生成的文件...
✅ 生成的文件:
  - index.html
  - README.md

============================================================
🌐 Web 服务信息
============================================================
✅ 前端地址: https://xxx.e2b.dev
✅ Sandbox ID: xxx
💡 使用提示:
  1. 在浏览器中打开上述地址访问计算器应用
  2. Sandbox 将保持运行约 1 小时（3600 秒）
  3. 服务超时后会自动关闭
============================================================
```

#### 示例 2: 直接运行 Agent 脚本（自动清理模式）

```python
import asyncio
from agent_runner import run_code_in_sandbox

async def main():
    result = await run_code_in_sandbox(
        code_file="calculator.py",
        env_vars={"ANTHROPIC_AUTH_TOKEN": "your_token"}
    )

    print(f"退出码: {result['exit_code']}")
    print(f"生成的文件: {result['files']}")

asyncio.run(main())
```

## 核心概念

### 1. Template（模板）

使用 Python API 定义 Sandbox 环境，替代传统 Dockerfile：

```python
# src/template.py
from e2b import Template, wait_for_timeout

template = (
    Template()
    .from_base_image()  # 使用默认基础镜像
    .set_user("user")
    .set_workdir("/home/user/workspace")
    .run_cmd("npm install -g @anthropic-ai/claude-code")
    .run_cmd("pip install claude-agent-sdk")
    .set_envs({"ANTHROPIC_BASE_URL": "..."})
    .set_start_cmd("echo 'Ready'", wait_for_timeout(5_000))
)
```

**优势：**
- 类型安全（Python 类型提示）
- 动态配置（从 .env 加载）
- IDE 支持（自动补全）
- Git 友好（纯 Python 代码）

### 2. Sandbox Manager（Sandbox 管理器）

简洁的 Sandbox 生命周期管理：

```python
# src/sandbox_manager.py
from e2b import AsyncSandbox

class SandboxManager:
    async def __aenter__(self):
        self.sandbox = await AsyncSandbox.create(self.template_id, envs=self.envs)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.sandbox.kill()
```

**使用方式：**
```python
async with SandboxManager(template_id, envs) as manager:
    # Sandbox 自动创建和清理
    await manager.sandbox.files.write("test.py", "print('Hello')")
    result = await manager.sandbox.commands.run("python test.py")
```

### 3. Agent Runner（Agent 运行器）

两种运行模式：

**模式 1: 自动清理模式**
```python
result = await run_code_in_sandbox("calculator.py")
# 执行完成后自动关闭 Sandbox
```

**模式 2: 服务模式**
```python
result = await run_code_with_service("calculator.py", service_port=3000)
# Sandbox 保持运行，返回服务 URL
print(result['service_url'])  # https://xxx.e2b.dev
```

### 4. Code Scripts（AI Agent 脚本）

在 Sandbox 内执行的 Python 脚本，使用 Claude Agent SDK：

```python
# src/code/calculator.py
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        allowed_tools=["Bash", "Read", "Write"],
        permission_mode="bypassPermissions"
    )

    async with ClaudeSDKClient(options) as client:
        await client.query("创建一个带 Web 前端的计算器应用")
        async for message in client.receive_response():
            print(message)
```

## 工作流程

```
1. 开发者 → 运行 apps/calculator.py
             ↓
2. agent_runner.py → 读取 code/calculator.py
             ↓
3. agent_runner.py → 创建 E2B Sandbox（使用 Template ID）
             ↓
4. agent_runner.py → 上传 code/calculator.py 到 Sandbox
             ↓
5. Sandbox 内部 → 执行 code/calculator.py
             ↓
6. code/calculator.py → 使用 Claude Agent SDK 生成代码
             ↓
7. Claude Agent SDK → 调用工具（Bash/Read/Write）生成文件
             ↓
8. agent_runner.py → 获取服务 URL
             ↓
9. 用户 → 访问 https://xxx.e2b.dev 查看生成的应用
```

## 文档导航

- **[01-architecture.md](docs/01-architecture.md)** - 系统架构设计和核心组件
- **[02-template-guide.md](docs/02-template-guide.md)** - E2B Template API 完整使用指南
- **[03-sandbox-guide.md](docs/03-sandbox-guide.md)** - Sandbox 管理和核心 API
- **[04-agent-integration.md](docs/04-agent-integration.md)** - Claude Agent SDK 集成详解
- **[05-best-practices.md](docs/05-best-practices.md)** - 最佳实践和性能优化
- **[06-troubleshooting.md](docs/06-troubleshooting.md)** - 常见问题和故障排除

## 常见问题

### 1. E2B_API_KEY 在哪里获取？

访问 [E2B Dashboard](https://e2b.dev/dashboard) → Settings → API Keys → 创建新 API Key

### 2. Template 构建需要多久？

首次构建约 3-5 分钟（需要安装依赖）。后续更新如果只改环境变量，构建速度会更快（利用缓存）。

### 3. Sandbox 超时时间是多少？

默认 3600 秒（1 小时）。可在创建时通过 `timeout` 参数调整：

```python
sandbox = await AsyncSandbox.create(template=template_id, timeout=7200)  # 2 小时
```

### 4. 如何调试 Agent 执行？

查看实时输出：
```python
result = await manager.sandbox.commands.run(
    cmd="python script.py",
    on_stdout=lambda msg: print(f"[OUT] {msg}"),
    on_stderr=lambda msg: print(f"[ERR] {msg}")
)
```

### 5. 生成的文件如何下载？

```python
content = await manager.sandbox.files.read("/home/user/workspace/file.txt")
with open("local_file.txt", "w") as f:
    f.write(content)
```

## 进阶使用

### 多任务并行执行

```python
tasks = [
    run_code_in_sandbox("task1.py"),
    run_code_in_sandbox("task2.py"),
    run_code_in_sandbox("task3.py"),
]

results = await asyncio.gather(*tasks)
```

### 自定义 Agent 配置

```python
# src/code/custom_agent.py
options = ClaudeAgentOptions(
    allowed_tools=["Bash", "Read", "Write", "Glob", "Grep"],
    permission_mode="bypassPermissions",
    cwd="/home/user/workspace",
    system_prompt={"type": "preset", "preset": "claude_code"},
    timeout=600_000  # 10 分钟
)
```

## 贡献指南

欢迎贡献代码、文档或报告问题！

1. Fork 项目
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 致谢

- [E2B](https://e2b.dev/) - 提供 Sandbox 运行环境
- [Anthropic](https://www.anthropic.com/) - Claude Agent SDK
- [智谱 AI](https://open.bigmodel.cn/) - GLM 模型支持

---

**需要帮助？** 请查看 [故障排除文档](docs/06-troubleshooting.md) 或提交 Issue。
