# 常见问题和故障排查

## 概述

本文档收集了使用 E2B Template + Claude Agent SDK 时的常见问题、错误诊断方法和解决方案。

## 1. Template 构建问题

### 1.1 E2B_API_KEY 未设置

**错误信息**:
```
❌ 错误：缺少必需的环境变量
   缺失: E2B_API_KEY
```

**原因**: 未配置 E2B API 密钥

**解决方案**:
```bash
# 1. 访问 E2B Dashboard 获取 API Key
# https://e2b.dev/dashboard

# 2. 创建 .env 文件
cat > .env << EOF
E2B_API_KEY=your_e2b_api_key_here
EOF

# 3. 确保 .env 文件被加载
# 在 Python 代码中
from dotenv import load_dotenv
load_dotenv()
```

### 1.2 Template 构建超时

**错误信息**:
```
TimeoutError: Template build timed out after 600 seconds
```

**原因**:
- 依赖安装过慢（网络问题）
- 依赖包过大
- E2B 服务繁忙

**解决方案**:

```python
# 方案 1: 使用国内镜像加速（推荐给中国用户）
template = (
    Template()
    .from_base_image()  # 使用默认镜像

    # 配置 pip 镜像
    .run_commands([
        "pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple"
    ])

    # 配置 npm 镜像
    .run_commands([
        "npm config set registry https://registry.npmmirror.com"
    ])

    # 然后安装依赖
    .run_commands([
        "pip install claude-agent-sdk",
        "npm install -g @anthropic-ai/claude-code"
    ])
)

# 方案 2: 减少依赖数量
# 只安装必需的依赖，避免安装大型库

# 方案 3: 分批安装
template = (
    Template()
    .from_base_image()  # 使用默认镜像

    # 第一批：小型依赖
    .run_commands([
        "pip install python-dotenv httpx"
    ])

    # 第二批：大型依赖
    .run_commands([
        "pip install claude-agent-sdk"
    ])
)
```

### 1.3 依赖安装失败

**错误信息**:
```
[Build Log] ERROR: Could not find a version that satisfies the requirement claude-agent-sdk
[Build Log] ERROR: No matching distribution found for claude-agent-sdk
```

**原因**:
- 包名拼写错误
- 包不存在或版本不可用
- PyPI 连接问题

**解决方案**:

```python
# 1. 验证包名是否正确
# 访问 https://pypi.org/project/claude-agent-sdk/

# 2. 指定版本号
template = Template().run_commands([
    "pip install claude-agent-sdk==0.1.3"  # 指定确切版本
])

# 3. 使用 --no-cache-dir 避免缓存问题
template = Template().run_commands([
    "pip install --no-cache-dir claude-agent-sdk"
])

# 4. 检查 Python 版本兼容性
template = (
    Template()
    .from_base_image()  # 使用默认镜像
    .run_commands([
        "pip install claude-agent-sdk"
    ])
)
```

### 1.4 权限错误

**错误信息**:
```
[Build Log] permission denied while trying to connect to the Docker daemon
```

**原因**: Docker 权限配置问题（通常不应该出现在 E2B Cloud）

**解决方案**:
- 这个错误通常出现在本地 Docker 构建
- 在 E2B Cloud 上不应该出现此问题
- 如果出现，请联系 E2B 支持

## 2. Sandbox 创建和管理问题

### 2.1 Sandbox 创建失败

**错误信息**:
```
ConnectionError: Failed to create sandbox
```

**原因**:
- 网络连接问题
- E2B 服务暂时不可用
- API Key 无效
- Template ID 不存在

**诊断步骤**:

```python
# 1. 验证 API Key
import os
print(f"API Key set: {bool(os.getenv('E2B_API_KEY'))}")

# 2. 测试网络连接
import httpx
async with httpx.AsyncClient() as client:
    try:
        response = await client.get("https://api.e2b.dev/health")
        print(f"E2B API Status: {response.status_code}")
    except Exception as e:
        print(f"Network error: {e}")

# 3. 验证 Template ID
template_id = "your-template-id"
print(f"Template ID: {template_id}")
print(f"Template ID length: {len(template_id)}")  # 应该是合理长度

# 4. 使用重试机制
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def create_with_retry():
    return await AsyncSandbox.create("template-id")
```

### 2.2 Sandbox 创建过慢

**症状**: Sandbox 创建时间过长（>30秒）

**原因**:
- Template 镜像过大
- E2B 服务负载高
- 网络延迟

**解决方案**:

```python
# 1. 优化 Template 大小
# - 移除不必要的依赖
# - 清理缓存文件
template = (
    Template()
    .from_base_image()  # 使用默认镜像
    .run_commands([
        "pip install claude-agent-sdk",
        # 清理缓存
        "pip cache purge",
        "apt-get clean",
        "rm -rf /var/lib/apt/lists/*"
    ])
)

# 2. 使用 Sandbox 池预创建
pool = SandboxPool("template-id", pool_size=5)
await pool.initialize()  # 提前创建

# 3. 添加超时和监控
import asyncio

start_time = time.time()
try:
    sandbox = await asyncio.wait_for(
        AsyncSandbox.create("template-id"),
        timeout=60  # 60 秒超时
    )
    duration = time.time() - start_time
    print(f"Sandbox created in {duration:.2f}s")
except asyncio.TimeoutError:
    print("❌ Sandbox creation timeout")
```

### 2.3 Sandbox 意外关闭

**错误信息**:
```
RuntimeError: Sandbox connection closed unexpectedly
```

**原因**:
- Sandbox 超时被自动关闭
- 内存或 CPU 限制被触发
- 进程崩溃

**解决方案**:

```python
# 1. 增加超时时间
sandbox = await AsyncSandbox.create(
    template="template-id",
    timeout=7200  # 2 小时
)

# 2. 捕获异常并重建
async def resilient_operation():
    max_retries = 3

    for attempt in range(max_retries):
        try:
            sandbox = await AsyncSandbox.create("template-id")
            result = await sandbox.run_code("python", code)
            await sandbox.close()
            return result

        except RuntimeError as e:
            print(f"Sandbox closed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2)
            else:
                raise

# 3. 监控 Sandbox 状态
async def monitor_sandbox(sandbox):
    """定期检查 Sandbox 是否还在运行"""
    while True:
        try:
            # 发送心跳
            result = await sandbox.run_code("bash", "echo 'heartbeat'")
            if result.exit_code != 0:
                print("⚠️  Sandbox 响应异常")
                break
            await asyncio.sleep(30)  # 每 30 秒检查一次
        except Exception as e:
            print(f"❌ Sandbox 连接丢失: {e}")
            break
```

### 2.4 文件操作失败

**错误信息**:
```
FileNotFoundError: [Errno 2] No such file or directory: '/home/user/workspace/file.txt'
```

**原因**:
- 路径错误
- 文件未创建
- 权限问题

**解决方案**:

```python
# 1. 验证路径存在
async def safe_read(sandbox, file_path):
    """安全的文件读取"""
    # 检查文件是否存在
    exists = await sandbox.files.exists(file_path)

    if not exists:
        print(f"❌ 文件不存在: {file_path}")

        # 列出目录内容
        dir_path = os.path.dirname(file_path)
        files = await sandbox.files.list(dir_path)
        print(f"目录 {dir_path} 中的文件:")
        for f in files:
            print(f"  - {f.name}")

        return None

    # 读取文件
    return await sandbox.files.read(file_path)

# 2. 使用绝对路径
# ✅ 正确
file_path = "/home/user/workspace/output/result.txt"

# ❌ 避免相对路径
file_path = "result.txt"  # 可能导致路径问题

# 3. 确保目录存在
await sandbox.files.make_dir("/home/user/workspace/output")
await sandbox.files.write("/home/user/workspace/output/file.txt", "content")
```

## 3. Agent 执行问题

### 3.1 Agent 初始化失败

**错误信息**:
```
[Error] Failed to initialize Claude Agent SDK
[Error] Authentication error: Invalid API token
```

**原因**:
- API Token 未设置或无效
- 网络无法访问 Claude API
- API Token 格式错误

**诊断和解决**:

```python
# 1. 验证 Token 是否设置
import os

token = os.getenv("ANTHROPIC_AUTH_TOKEN")
print(f"Token set: {bool(token)}")
if token:
    print(f"Token starts with: {token[:10]}...")  # 只显示前10个字符

# 2. 在 Sandbox 创建时传递 Token
sandbox = await AsyncSandbox.create(
    template="template-id",
    env_vars={
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
        # 确保 Token 被正确传递
    }
)

# 3. 测试 Token 有效性
import anthropic

try:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"))
    # 测试 API 调用
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=10,
        messages=[{"role": "user", "content": "test"}]
    )
    print("✅ API Token 有效")
except Exception as e:
    print(f"❌ API Token 无效: {e}")

# 4. 检查智谱 AI 配置（如果使用）
# 确保 ANTHROPIC_BASE_URL 正确设置
base_url = "https://open.bigmodel.cn/api/anthropic"
print(f"Base URL: {base_url}")
```

### 3.2 Agent 任务执行超时

**错误信息**:
```
asyncio.TimeoutError: Task execution timeout
```

**原因**:
- 任务过于复杂
- Claude API 响应慢
- 工具执行时间长

**解决方案**:

```python
# 1. 增加超时时间
task = AgentTask(
    query="Complex task...",
    allowed_tools=["Bash", "Write"],
    timeout=1800  # 30 分钟
)

# 2. 分解复杂任务
async def decomposed_execution():
    """将大任务分解为小任务"""

    subtasks = [
        "Step 1: Initialize project",
        "Step 2: Create files",
        "Step 3: Run tests"
    ]

    for i, subtask in enumerate(subtasks, 1):
        print(f"执行子任务 {i}/{len(subtasks)}")

        task = AgentTask(
            query=subtask,
            allowed_tools=["Bash", "Write"],
            timeout=300  # 每个子任务 5 分钟
        )

        result = await runner.run_task(task)

        if not result.success:
            print(f"❌ 子任务 {i} 失败")
            break

# 3. 使用进度监控
async def monitored_execution():
    """带进度监控的执行"""

    start_time = time.time()
    timeout = 600  # 10 分钟

    async def check_timeout():
        """超时检查"""
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                print(f"⚠️  任务执行超过 {timeout} 秒")
                break

            print(f"[{int(elapsed)}s] 任务运行中...")
            await asyncio.sleep(30)

    # 并行执行任务和超时检查
    monitor_task = asyncio.create_task(check_timeout())

    try:
        result = await runner.run_task(task)
        return result
    finally:
        monitor_task.cancel()
```

### 3.3 工具调用失败

**错误信息**:
```
[Error] Tool execution failed: Bash command returned non-zero exit code
```

**原因**:
- 工具参数错误
- 权限不足
- 依赖缺失

**解决方案**:

```python
# 1. 验证工具配置
agent_options = ClaudeAgentOptions(
    allowed_tools=[
        "Bash",      # 确保拼写正确
        "Read",
        "Write",
        "Glob",
        "Grep"
    ],
    permission_mode="bypassPermissions",  # 在 Sandbox 中使用
    cwd="/home/user/workspace"  # 确保工作目录存在
)

# 2. 检查依赖是否安装
async def verify_dependencies(sandbox):
    """验证必要的依赖"""

    checks = {
        "python": "python --version",
        "pip": "pip --version",
        "npm": "npm --version",
        "claude-code": "claude-code --version"
    }

    for name, command in checks.items():
        result = await sandbox.run_code("bash", command)
        if result.exit_code == 0:
            print(f"✅ {name}: {result.stdout.strip()}")
        else:
            print(f"❌ {name}: 未安装")

# 在运行 Agent 前验证
await verify_dependencies(sandbox)

# 3. 捕获和记录工具错误
agent_script = """
import asyncio
import sys
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    try:
        options = ClaudeAgentOptions(
            allowed_tools=["Bash", "Write"],
            permission_mode="bypassPermissions"
        )

        async with ClaudeSDKClient(options) as client:
            await client.query("Create a test file")

            async for message in client.receive_response():
                print(message, flush=True)

    except Exception as e:
        print(f"❌ Agent error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

asyncio.run(main())
"""
```

### 3.4 输出截断或丢失

**症状**: Agent 输出不完整或没有输出

**原因**:
- 缓冲区问题
- 输出处理不当
- 进程提前退出

**解决方案**:

```python
# 1. 使用 flush=True 强制刷新输出
agent_script = """
import sys

print("Message", flush=True)  # 强制刷新
sys.stdout.flush()  # 显式刷新
"""

# 2. 正确处理输出流
class OutputCapture:
    """输出捕获器"""

    def __init__(self):
        self.stdout_lines = []
        self.stderr_lines = []

    def handle_stdout(self, line: str):
        """处理标准输出"""
        print(f"[OUT] {line}")
        self.stdout_lines.append(line)

    def handle_stderr(self, line: str):
        """处理错误输出"""
        print(f"[ERR] {line}")
        self.stderr_lines.append(line)

    def get_output(self):
        """获取完整输出"""
        return {
            "stdout": '\n'.join(self.stdout_lines),
            "stderr": '\n'.join(self.stderr_lines)
        }

# 使用
capture = OutputCapture()

process = await sandbox.start_process(
    cmd="python agent_task.py",
    on_stdout=capture.handle_stdout,
    on_stderr=capture.handle_stderr
)

await process.wait()
output = capture.get_output()

# 3. 检查进程退出状态
exit_code = await process.wait()
if exit_code != 0:
    print(f"⚠️  进程异常退出: {exit_code}")
    print(f"stderr: {capture.get_output()['stderr']}")
```

## 4. 性能问题

### 4.1 执行速度慢

**症状**: Agent 任务执行时间过长

**诊断和优化**:

```python
# 1. 添加性能分析
import time

async def profile_execution(runner, task):
    """性能分析执行"""

    timings = {}

    # Sandbox 创建时间
    start = time.time()
    await runner.start()
    timings['sandbox_creation'] = time.time() - start

    # Agent 初始化时间
    start = time.time()
    # ... Agent 初始化 ...
    timings['agent_init'] = time.time() - start

    # 任务执行时间
    start = time.time()
    result = await runner.run_task(task)
    timings['task_execution'] = time.time() - start

    # 清理时间
    start = time.time()
    await runner.close()
    timings['cleanup'] = time.time() - start

    print("性能分析:")
    for phase, duration in timings.items():
        print(f"  {phase}: {duration:.2f}s")

    return result

# 2. 优化策略
# - 复用 Sandbox（避免重复创建）
# - 使用 Sandbox 池
# - 减少不必要的工具调用
# - 优化任务查询（更明确的指令）
```

### 4.2 内存使用过高

**症状**: 进程内存占用持续增长

**解决方案**:

```python
# 1. 及时清理资源
async def memory_efficient_execution():
    """内存高效的执行模式"""

    for i in range(100):
        # 每次循环创建和销毁
        async with AsyncSandbox.create("template-id") as sandbox:
            result = await sandbox.run_code("python", task)
            # Sandbox 自动清理

        # 短暂休息，让 GC 工作
        if i % 10 == 0:
            await asyncio.sleep(0.1)

# 2. 限制并发数量
from asyncio import Semaphore

semaphore = Semaphore(5)  # 最多 5 个并发

async def controlled_execution(task):
    async with semaphore:
        async with AsyncSandbox.create("template-id") as sandbox:
            return await sandbox.run_code("python", task)

# 3. 监控内存使用
import psutil

def log_memory():
    """记录内存使用"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.2f} MB")

# 定期调用
log_memory()
```

## 5. 调试技巧

### 5.1 启用详细日志

```python
import logging

# 启用调试日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# E2B SDK 日志
logging.getLogger('e2b').setLevel(logging.DEBUG)

# Claude Agent SDK 日志
logging.getLogger('claude_agent_sdk').setLevel(logging.DEBUG)
```

### 5.2 交互式调试

```python
# 在 Sandbox 中运行交互式 Python
async def interactive_debug():
    """交互式调试"""

    async with AsyncSandbox.create("template-id") as sandbox:
        # 进入交互式 shell
        print("进入交互式模式，输入 'exit' 退出")

        while True:
            command = input(">>> ")

            if command.lower() == 'exit':
                break

            result = await sandbox.run_code("python", command)
            print(result.stdout)
            if result.stderr:
                print(f"Error: {result.stderr}")
```

### 5.3 保存失败现场

```python
async def save_failure_snapshot(sandbox, task, error):
    """保存失败时的现场信息"""

    snapshot_dir = f"debug_snapshots/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(snapshot_dir, exist_ok=True)

    # 保存任务信息
    with open(f"{snapshot_dir}/task.json", "w") as f:
        json.dump({
            "query": task.query,
            "allowed_tools": task.allowed_tools,
            "error": str(error)
        }, f, indent=2)

    # 保存 Sandbox 文件
    try:
        files = await sandbox.files.list("/home/user/workspace")
        for file_info in files:
            if file_info.name.endswith(('.py', '.txt', '.log')):
                content = await sandbox.files.read(f"/home/user/workspace/{file_info.name}")
                with open(f"{snapshot_dir}/{file_info.name}", "w") as f:
                    f.write(content)
    except Exception as e:
        print(f"无法保存文件: {e}")

    print(f"失败现场已保存到: {snapshot_dir}")
```

## 6. 获取帮助

### 6.1 查看文档

- **E2B 文档**: https://e2b.dev/docs
- **Claude Agent SDK**: 项目 README 和示例
- **本技术方案**: `examples/demo/docs/` 目录

### 6.2 社区支持

- **E2B Discord**: https://discord.gg/U7KEcGErtQ
- **GitHub Issues**:
  - E2B: https://github.com/e2b-dev/e2b
  - Claude Agent SDK: 项目 GitHub Issues

### 6.3 日志收集

报告问题时，请提供：

```python
# 收集诊断信息
async def collect_diagnostic_info():
    """收集诊断信息"""

    info = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": sys.platform,
        "environment": {
            "E2B_API_KEY_SET": bool(os.getenv("E2B_API_KEY")),
            "ANTHROPIC_TOKEN_SET": bool(os.getenv("ANTHROPIC_AUTH_TOKEN")),
        },
        "packages": {
            "e2b": e2b.__version__ if hasattr(e2b, '__version__') else "unknown",
            # 添加其他包版本
        }
    }

    # 保存到文件
    with open("diagnostic_info.json", "w") as f:
        json.dump(info, f, indent=2)

    print("诊断信息已保存到 diagnostic_info.json")
```

## 7. 总结

本章涵盖了常见问题的诊断和解决方案：

**Template 问题**:
- ✅ API Key 配置
- ✅ 构建超时和依赖安装
- ✅ 权限和版本兼容性

**Sandbox 问题**:
- ✅ 创建失败和超时
- ✅ 连接丢失和文件操作
- ✅ 资源管理

**Agent 问题**:
- ✅ 初始化和认证
- ✅ 任务执行超时
- ✅ 工具调用和输出处理

**性能问题**:
- ✅ 执行速度优化
- ✅ 内存管理

**调试工具**:
- ✅ 日志配置
- ✅ 交互式调试
- ✅ 现场保存

遇到问题时的建议流程：
1. 检查错误信息和日志
2. 查找本文档中的类似问题
3. 尝试提供的解决方案
4. 收集诊断信息
5. 寻求社区帮助

通过系统的问题排查和这些解决方案，大多数问题都可以得到快速解决。
