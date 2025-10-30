# 最佳实践和性能优化

## 概述

本文档提供 E2B Template + Claude Agent SDK 的最佳实践、性能优化策略和生产环境部署建议。

## 1. Template 设计最佳实践

### 1.1 分层构建策略

```python
# ✅ 推荐：按变化频率分层
template = (
    Template()
    # 第 1 层：基础镜像（几乎不变）
    .from_base_image()  # 使用默认镜像

    # 第 2 层：系统依赖（很少变化）
    .run_commands([
        "apt-get update",
        "apt-get install -y build-essential curl git"
    ])

    # 第 3 层：运行时环境（偶尔变化）
    .run_commands([
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs"
    ])

    # 第 4 层：全局工具（较少变化）
    .run_commands([
        "npm install -g @anthropic-ai/claude-code"
    ])

    # 第 5 层：应用依赖（经常变化）
    .run_commands([
        "pip install claude-agent-sdk anthropic"
    ])

    # 第 6 层：配置（最常变化）
    .set_envs({"APP_ENV": "production"})
)

# ❌ 避免：所有命令混在一起
template = Template().run_commands([
    "apt-get update && apt-get install -y build-essential && npm install -g claude-code && pip install claude-agent-sdk"
])
```

**原因**: Docker 层缓存机制，频繁变化的层放在后面可以加速构建。

### 1.2 依赖安装优化

```python
# ✅ 推荐：批量安装相关依赖
template = Template().run_commands([
    # 系统包批量安装
    "apt-get update && apt-get install -y curl git vim build-essential",

    # Python 包批量安装（使用镜像）
    "pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple",
    "pip install --no-cache-dir claude-agent-sdk anthropic httpx",

    # npm 包批量安装
    "npm config set registry https://registry.npmmirror.com",
    "npm install -g @anthropic-ai/claude-code typescript"
])

# ❌ 避免：逐个安装依赖
template = (
    Template()
    .run_commands(["apt-get update"])
    .run_commands(["apt-get install -y curl"])
    .run_commands(["apt-get install -y git"])
    .run_commands(["pip install claude-agent-sdk"])
    .run_commands(["pip install anthropic"])
)
```

### 1.3 缓存和镜像优化

```python
# 中国用户推荐配置
template = (
    Template()
    .from_base_image()  # 使用默认镜像

    # 配置 APT 镜像
    .run_commands([
        """sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list""",
        "apt-get update"
    ])

    # 配置 npm 镜像
    .run_commands([
        "npm config set registry https://registry.npmmirror.com",
        "npm config set disturl https://npmmirror.com/dist"
    ])

    # 配置 pip 镜像
    .run_commands([
        "pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple",
        "pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn"
    ])

    # 减少缓存体积
    .run_commands([
        "apt-get clean",
        "rm -rf /var/lib/apt/lists/*",
        "npm cache clean --force",
        "pip cache purge"
    ])
)
```

### 1.4 环境变量管理

```python
import os

# ✅ 推荐：敏感信息在运行时传递
template = Template().set_envs({
    # 非敏感配置：可以放在 Template 中
    "APP_ENV": "production",
    "LOG_LEVEL": "INFO",
    "WORKSPACE_DIR": "/home/user/workspace",

    # 敏感信息：不要硬编码
    # "API_KEY": "sk-xxx"  # ❌ 不要这样做
})

# 运行时传递敏感信息
sandbox = await AsyncSandbox.create(
    template="template-id",
    env_vars={
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
        "DATABASE_URL": os.getenv("DATABASE_URL")
    }
)

# ✅ 更好：使用 .env 文件管理
from dotenv import load_dotenv
load_dotenv()

env_vars = {
    "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
    "CUSTOM_CONFIG": os.getenv("CUSTOM_CONFIG", "default_value")
}
```

## 2. Sandbox 管理最佳实践

### 2.1 生命周期管理

```python
# ✅ 推荐：使用 Context Manager
async def good_lifecycle():
    async with AsyncSandbox.create("template-id") as sandbox:
        # 使用 Sandbox
        result = await sandbox.run_code("python", "print('Hello')")
        # 自动清理

# ❌ 避免：忘记关闭
async def bad_lifecycle():
    sandbox = await AsyncSandbox.create("template-id")
    result = await sandbox.run_code("python", "print('Hello')")
    # 忘记 await sandbox.close() - 资源泄漏！

# ✅ 推荐：带异常处理
async def robust_lifecycle():
    sandbox = None
    try:
        sandbox = await AsyncSandbox.create("template-id")
        result = await sandbox.run_code("python", "print('Hello')")
        return result
    except Exception as e:
        print(f"错误: {e}")
        raise
    finally:
        if sandbox:
            await sandbox.close()
```

### 2.2 资源限制和超时

```python
# ✅ 推荐：设置合理的超时
sandbox = await AsyncSandbox.create(
    template="template-id",
    timeout=3600  # 1 小时，根据任务复杂度调整
)

# 任务级超时
try:
    result = await asyncio.wait_for(
        sandbox.run_code("python", long_running_code),
        timeout=300  # 5 分钟
    )
except asyncio.TimeoutError:
    print("任务超时")
    # 清理资源

# ✅ 推荐：监控资源使用
async def monitor_resource():
    sandbox = await AsyncSandbox.create("template-id")
    start_time = time.time()

    try:
        result = await sandbox.run_code("python", code)
        duration = time.time() - start_time

        if duration > 60:
            print(f"⚠️  任务耗时过长: {duration:.2f}s")

        return result
    finally:
        await sandbox.close()
```

### 2.3 错误处理和重试

```python
from tenacity import retry, stop_after_attempt, wait_exponential

# ✅ 推荐：使用 tenacity 进行智能重试
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry_error_callback=lambda retry_state: print(f"重试失败: {retry_state.outcome}")
)
async def create_sandbox_with_retry(template_id):
    """创建 Sandbox（带重试）"""
    try:
        sandbox = await AsyncSandbox.create(template_id)
        # 健康检查
        result = await sandbox.run_code("bash", "echo 'health_check'")
        if result.exit_code != 0:
            raise RuntimeError("健康检查失败")
        return sandbox
    except Exception as e:
        print(f"创建失败: {e}")
        raise

# ✅ 推荐：区分可重试和不可重试的错误
async def smart_error_handling():
    try:
        sandbox = await AsyncSandbox.create("template-id")
        return sandbox
    except ConnectionError as e:
        # 网络错误 - 可以重试
        print(f"网络错误，可以重试: {e}")
        raise
    except ValueError as e:
        # 配置错误 - 不应该重试
        print(f"配置错误，请检查参数: {e}")
        raise
    except Exception as e:
        # 未知错误 - 谨慎处理
        print(f"未知错误: {e}")
        raise
```

### 2.4 并发控制

```python
import asyncio
from asyncio import Semaphore

# ✅ 推荐：限制并发 Sandbox 数量
async def controlled_parallel_execution(tasks, max_concurrent=5):
    """控制并发数量的并行执行"""

    semaphore = Semaphore(max_concurrent)

    async def execute_with_semaphore(task):
        async with semaphore:
            async with AsyncSandbox.create("template-id") as sandbox:
                return await sandbox.run_code("python", task)

    results = await asyncio.gather(*[
        execute_with_semaphore(task) for task in tasks
    ], return_exceptions=True)

    return results

# ❌ 避免：无限制并发
async def uncontrolled_parallel():
    # 如果有 1000 个任务，会同时创建 1000 个 Sandbox！
    tasks = [create_and_run(task) for task in range(1000)]
    await asyncio.gather(*tasks)
```

## 3. Agent 集成最佳实践

### 3.1 Agent 配置优化

```python
# ✅ 推荐：根据任务类型配置工具
def get_agent_options(task_type: str):
    """根据任务类型返回优化的 Agent 配置"""

    if task_type == "code_generation":
        return ClaudeAgentOptions(
            allowed_tools=["Bash", "Write", "Read", "Glob"],
            permission_mode="bypassPermissions",
            cwd="/home/user/workspace"
        )

    elif task_type == "code_analysis":
        return ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            permission_mode="bypassPermissions",
            cwd="/home/user/workspace"
        )

    elif task_type == "data_processing":
        return ClaudeAgentOptions(
            allowed_tools=["Bash", "Read", "Write"],
            permission_mode="bypassPermissions",
            cwd="/home/user/workspace"
        )

    else:
        # 默认配置
        return ClaudeAgentOptions(
            allowed_tools=["Bash", "Read", "Write"],
            permission_mode="bypassPermissions"
        )

# 使用
options = get_agent_options("code_generation")
```

### 3.2 任务分解策略

```python
# ✅ 推荐：复杂任务分解为小步骤
async def decomposed_task_execution(runner: AgentRunner):
    """将复杂任务分解为多个步骤"""

    steps = [
        {
            "name": "项目初始化",
            "query": "Create project structure with necessary directories"
        },
        {
            "name": "依赖配置",
            "query": "Create requirements.txt with necessary dependencies"
        },
        {
            "name": "代码实现",
            "query": "Implement the main application logic"
        },
        {
            "name": "测试编写",
            "query": "Create unit tests for the application"
        }
    ]

    for step in steps:
        print(f"📝 执行: {step['name']}")

        task = AgentTask(
            query=step['query'],
            allowed_tools=["Bash", "Write", "Read", "Glob"]
        )

        result = await runner.run_task(task)

        if not result.success:
            print(f"❌ 步骤失败: {step['name']}")
            break

        print(f"✅ 完成: {step['name']}")

# ❌ 避免：一次性执行过于复杂的任务
bad_query = """
Create a complete e-commerce platform with user authentication,
product catalog, shopping cart, payment integration, admin panel,
email notifications, and mobile app - all in one go
"""
```

### 3.3 输出处理和日志

```python
import logging
from datetime import datetime

# ✅ 推荐：结构化日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def logged_agent_execution(runner, task):
    """带结构化日志的 Agent 执行"""

    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"[{task_id}] 开始执行任务")
    logger.info(f"[{task_id}] Query: {task.query[:100]}...")

    start_time = time.time()

    try:
        result = await runner.run_task(task)

        duration = time.time() - start_time

        logger.info(f"[{task_id}] 任务完成")
        logger.info(f"[{task_id}] 耗时: {duration:.2f}s")
        logger.info(f"[{task_id}] 成功: {result.success}")
        logger.info(f"[{task_id}] 生成文件: {len(result.generated_files)}")

        return result

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[{task_id}] 任务失败: {e}")
        logger.error(f"[{task_id}] 耗时: {duration:.2f}s")
        raise

# ✅ 推荐：保存执行记录
async def save_execution_record(task, result):
    """保存任务执行记录"""

    record = {
        "timestamp": datetime.now().isoformat(),
        "query": task.query,
        "success": result.success,
        "exit_code": result.exit_code,
        "generated_files": result.generated_files,
        "stdout": result.stdout[:1000],  # 只保存前1000字符
        "stderr": result.stderr[:1000]
    }

    # 保存到文件或数据库
    import json
    with open(f"logs/task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(record, f, indent=2)
```

## 4. 性能优化

### 4.1 Sandbox 复用

```python
# ✅ 推荐：复用 Sandbox 执行多个任务
async def reuse_sandbox():
    """复用 Sandbox 提高效率"""

    async with AsyncSandbox.create("template-id") as sandbox:
        # 执行多个独立任务
        tasks = [
            "print('Task 1')",
            "print('Task 2')",
            "print('Task 3')"
        ]

        for i, code in enumerate(tasks, 1):
            result = await sandbox.run_code("python", code)
            print(f"Task {i}: {result.stdout}")

    # 比每次创建新 Sandbox 快 10-20 倍

# ❌ 避免：每个任务都创建新 Sandbox
async def create_every_time():
    for i, code in enumerate(tasks, 1):
        async with AsyncSandbox.create("template-id") as sandbox:
            result = await sandbox.run_code("python", code)
            print(f"Task {i}: {result.stdout}")
    # 创建开销太大！
```

### 4.2 Sandbox 池模式

```python
from asyncio import Queue

class SandboxPool:
    """Sandbox 连接池"""

    def __init__(self, template_id: str, pool_size: int = 5):
        self.template_id = template_id
        self.pool_size = pool_size
        self.pool: Queue = Queue(maxsize=pool_size)
        self.active_sandboxes = []

    async def initialize(self):
        """初始化连接池"""
        print(f"初始化 Sandbox 池 (大小: {self.pool_size})...")

        for i in range(self.pool_size):
            sandbox = await AsyncSandbox.create(self.template_id)
            self.active_sandboxes.append(sandbox)
            await self.pool.put(sandbox)
            print(f"  [{i+1}/{self.pool_size}] Sandbox 已创建")

        print("✅ Sandbox 池初始化完成")

    async def acquire(self) -> AsyncSandbox:
        """获取一个 Sandbox"""
        return await self.pool.get()

    async def release(self, sandbox: AsyncSandbox):
        """释放 Sandbox 回池中"""
        await self.pool.put(sandbox)

    async def close_all(self):
        """关闭所有 Sandbox"""
        print("正在关闭所有 Sandbox...")

        for sandbox in self.active_sandboxes:
            try:
                await sandbox.close()
            except Exception as e:
                print(f"关闭失败: {e}")

        print("✅ 所有 Sandbox 已关闭")


# 使用示例
async def use_sandbox_pool():
    """使用 Sandbox 池"""

    pool = SandboxPool("template-id", pool_size=3)

    try:
        await pool.initialize()

        # 并发执行任务
        async def execute_task(task_id):
            sandbox = await pool.acquire()
            try:
                result = await sandbox.run_code("python", f"print('Task {task_id}')")
                print(result.stdout)
            finally:
                await pool.release(sandbox)

        # 执行 10 个任务，但只用 3 个 Sandbox
        await asyncio.gather(*[
            execute_task(i) for i in range(10)
        ])

    finally:
        await pool.close_all()
```

### 4.3 缓存策略

```python
from functools import lru_cache
import hashlib

# ✅ 推荐：缓存不变的结果
class CachedAgentRunner:
    """带缓存的 Agent 运行器"""

    def __init__(self):
        self.result_cache = {}

    def _cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()

    async def run_with_cache(self, runner, task: AgentTask):
        """带缓存的任务执行"""

        cache_key = self._cache_key(task.query)

        # 检查缓存
        if cache_key in self.result_cache:
            print("✅ 使用缓存结果")
            return self.result_cache[cache_key]

        # 执行任务
        result = await runner.run_task(task)

        # 只缓存成功的结果
        if result.success:
            self.result_cache[cache_key] = result

        return result

# ✅ 推荐：Template ID 缓存
@lru_cache(maxsize=1)
def load_template_id():
    """缓存 Template ID 避免重复读取"""
    with open(".template_id") as f:
        for line in f:
            if line.startswith("TEMPLATE_ID="):
                return line.split("=")[1].strip()
    return None
```

### 4.4 批量处理优化

```python
# ✅ 推荐：批量处理小任务
async def batch_processing(tasks, batch_size=10):
    """批量处理任务"""

    results = []

    # 分批处理
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        print(f"处理批次 {i//batch_size + 1}/{(len(tasks)-1)//batch_size + 1}")

        # 并行处理当前批次
        batch_results = await asyncio.gather(*[
            execute_task(task) for task in batch
        ])

        results.extend(batch_results)

        # 批次间短暂休息
        if i + batch_size < len(tasks):
            await asyncio.sleep(1)

    return results
```

## 5. 安全性最佳实践

### 5.1 敏感信息保护

```python
# ✅ 推荐：使用环境变量
import os
from dotenv import load_dotenv

load_dotenv()

# 从环境变量读取敏感信息
ANTHROPIC_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not ANTHROPIC_TOKEN:
    raise ValueError("缺少 ANTHROPIC_AUTH_TOKEN 环境变量")

# ✅ 推荐：不要记录敏感信息
def safe_log(message: str, token: str = None):
    """安全的日志记录"""
    if token and token in message:
        # 脱敏处理
        safe_message = message.replace(token, "***REDACTED***")
        logger.info(safe_message)
    else:
        logger.info(message)

# ❌ 避免：硬编码或打印敏感信息
API_KEY = "sk-1234567890abcdef"  # 不要这样做！
print(f"Using API key: {API_KEY}")  # 不要打印敏感信息！
```

### 5.2 输入验证

```python
# ✅ 推荐：验证用户输入
def validate_task_query(query: str) -> bool:
    """验证任务查询的安全性"""

    # 检查长度
    if len(query) > 10000:
        raise ValueError("查询过长")

    # 检查危险命令
    dangerous_patterns = [
        "rm -rf /",
        "mkfs",
        "dd if=",
        "fork bomb",
        ":(){ :|:& };:"
    ]

    query_lower = query.lower()
    for pattern in dangerous_patterns:
        if pattern in query_lower:
            raise ValueError(f"检测到危险命令: {pattern}")

    return True

# 使用
try:
    validate_task_query(user_input)
    # 继续执行
except ValueError as e:
    print(f"输入验证失败: {e}")
```

### 5.3 资源限制

```python
# ✅ 推荐：限制资源使用
sandbox = await AsyncSandbox.create(
    template="template-id",
    timeout=3600,  # 1 小时超时
    # 注意：E2B 在 Template 构建时设置 CPU 和内存限制
)

# ✅ 推荐：监控文件系统使用
async def check_disk_usage(sandbox):
    """检查磁盘使用情况"""
    result = await sandbox.run_code("bash", "df -h /home/user/workspace | tail -1")

    # 解析输出检查使用率
    if "100%" in result.stdout:
        print("⚠️  磁盘空间已满")
        return False

    return True
```

## 6. 生产环境部署

### 6.1 配置管理

```python
# ✅ 推荐：使用配置类
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductionConfig:
    """生产环境配置"""

    # E2B 配置
    template_id: str
    e2b_api_key: str

    # Anthropic 配置
    anthropic_token: str
    anthropic_base_url: str = "https://api.anthropic.com"

    # 性能配置
    sandbox_pool_size: int = 5
    max_concurrent_tasks: int = 10
    task_timeout: int = 3600

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = "app.log"

    # 重试配置
    max_retries: int = 3
    retry_delay: int = 2

    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            template_id=os.getenv("TEMPLATE_ID"),
            e2b_api_key=os.getenv("E2B_API_KEY"),
            anthropic_token=os.getenv("ANTHROPIC_AUTH_TOKEN"),
            anthropic_base_url=os.getenv(
                "ANTHROPIC_BASE_URL",
                "https://api.anthropic.com"
            ),
            sandbox_pool_size=int(os.getenv("SANDBOX_POOL_SIZE", "5")),
            max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
        )

# 使用
config = ProductionConfig.from_env()
```

### 6.2 监控和告警

```python
# ✅ 推荐：添加监控指标
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Metrics:
    """性能指标"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_duration: float = 0.0
    errors: list = field(default_factory=list)

    def record_success(self, duration: float):
        """记录成功任务"""
        self.total_tasks += 1
        self.successful_tasks += 1
        self.total_duration += duration

    def record_failure(self, error: str, duration: float):
        """记录失败任务"""
        self.total_tasks += 1
        self.failed_tasks += 1
        self.total_duration += duration
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "error": error
        })

    def get_stats(self):
        """获取统计信息"""
        return {
            "total_tasks": self.total_tasks,
            "success_rate": self.successful_tasks / max(self.total_tasks, 1),
            "avg_duration": self.total_duration / max(self.total_tasks, 1),
            "recent_errors": self.errors[-10:]  # 最近10个错误
        }

# 使用
metrics = Metrics()

start_time = time.time()
try:
    result = await runner.run_task(task)
    metrics.record_success(time.time() - start_time)
except Exception as e:
    metrics.record_failure(str(e), time.time() - start_time)

# 定期输出指标
print(json.dumps(metrics.get_stats(), indent=2))
```

### 6.3 健康检查

```python
# ✅ 推荐：实现健康检查端点
async def health_check():
    """系统健康检查"""

    checks = {
        "e2b_connection": False,
        "template_available": False,
        "anthropic_api": False
    }

    try:
        # 检查 E2B 连接
        sandbox = await asyncio.wait_for(
            AsyncSandbox.create("template-id"),
            timeout=10
        )
        checks["e2b_connection"] = True
        checks["template_available"] = True
        await sandbox.close()

    except asyncio.TimeoutError:
        checks["e2b_connection"] = False
    except Exception as e:
        print(f"健康检查失败: {e}")

    # 检查 Anthropic API（可选）
    # ...

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

## 7. 成本优化

### 7.1 按需创建策略

```python
# ✅ 推荐：按需创建，及时销毁
async def cost_efficient_execution(tasks):
    """成本效率高的执行模式"""

    for task in tasks:
        # 只在需要时创建
        async with AsyncSandbox.create("template-id") as sandbox:
            result = await sandbox.run_code("python", task)
            # 任务完成立即销毁

        # 任务间短暂休息（避免频繁创建）
        await asyncio.sleep(0.5)
```

### 7.2 复用 vs 销毁权衡

```python
# 根据任务类型选择策略
async def smart_sandbox_strategy(tasks, task_type):
    """智能 Sandbox 策略"""

    if task_type == "batch_small_tasks":
        # 小任务批量处理 - 复用 Sandbox
        async with AsyncSandbox.create("template-id") as sandbox:
            for task in tasks:
                await sandbox.run_code("python", task)

    elif task_type == "independent_large_tasks":
        # 大任务独立处理 - 每次创建
        for task in tasks:
            async with AsyncSandbox.create("template-id") as sandbox:
                await sandbox.run_code("python", task)

    elif task_type == "continuous_service":
        # 持续服务 - 使用 Sandbox 池
        pool = SandboxPool("template-id", pool_size=3)
        await pool.initialize()
        # 长期运行...
```

## 8. 总结

本章涵盖了完整的最佳实践：

**Template 设计**:
- ✅ 分层构建和缓存优化
- ✅ 依赖管理和镜像加速
- ✅ 环境变量安全管理

**Sandbox 管理**:
- ✅ 生命周期管理和资源控制
- ✅ 错误处理和重试策略
- ✅ 并发控制和限流

**Agent 集成**:
- ✅ 配置优化和任务分解
- ✅ 日志记录和监控
- ✅ 结果缓存

**性能优化**:
- ✅ Sandbox 复用和连接池
- ✅ 批量处理优化
- ✅ 缓存策略

**安全性**:
- ✅ 敏感信息保护
- ✅ 输入验证
- ✅ 资源限制

**生产部署**:
- ✅ 配置管理
- ✅ 监控和告警
- ✅ 健康检查
- ✅ 成本优化

下一章将介绍常见问题和故障排查。
