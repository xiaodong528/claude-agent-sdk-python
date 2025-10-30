"""Sandbox 生命周期管理器

提供 E2B Sandbox 的创建、管理和资源清理功能，支持异步 Context Manager 模式。
"""

from typing import Optional
from e2b import AsyncSandbox


class SandboxManager:
    """长期运行的 Sandbox 管理器

    支持异步 Context Manager 模式，自动管理 Sandbox 生命周期。

    示例:
        async with SandboxManager(template_id, envs) as manager:
            result = await manager.execute_code("python", "print('Hello')")

    Attributes:
        template_id: E2B Template ID
        envs: 环境变量字典
        sandbox: AsyncSandbox 实例（启动后可用）
    """

    def __init__(self, template_id: str, envs: Optional[dict] = None):
        """初始化 Sandbox 管理器

        Args:
            template_id: E2B Template ID（如 "or5xvfgibxlz5u6oa6p1"）
            envs: 可选的环境变量字典，覆盖 Template 默认值
        """
        self.template_id = template_id
        self.envs = envs or {}
        self.sandbox: Optional[AsyncSandbox] = None

    async def __aenter__(self):
        """Context Manager 入口：自动启动 Sandbox"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 出口：自动关闭 Sandbox"""
        await self.close()

    async def start(self):
        """启动 Sandbox

        创建 AsyncSandbox 实例并初始化环境。

        Raises:
            Exception: Sandbox 创建失败时抛出
        """
        if self.sandbox is not None:
            print("⚠️ Sandbox 已经启动，跳过重复创建")
            return

        print(f"🚀 创建 Sandbox...")
        try:
            self.sandbox = await AsyncSandbox.create(
                template=self.template_id,
                envs=self.envs,
                timeout=3600  # 1小时超时
            )
            print(f"✅ Sandbox 已创建 (ID: {self.sandbox.sandbox_id})")
        except Exception as e:
            print(f"❌ Sandbox 创建失败: {e}")
            raise

    async def close(self):
        """关闭 Sandbox

        安全关闭 Sandbox 实例并释放所有资源。
        即使发生异常也会确保资源清理。
        """
        if self.sandbox is None:
            return

        try:
            await self.sandbox.kill()
            print("✅ Sandbox 已关闭")
        except Exception as e:
            print(f"⚠️ 关闭 Sandbox 时出错: {e}")
        finally:
            self.sandbox = None

    async def execute_code(self, language: str, code: str):
        """在 Sandbox 中执行代码

        Args:
            language: 代码语言（如 "python", "bash"）
            code: 要执行的代码字符串

        Returns:
            执行结果对象，包含 stdout, stderr, exit_code 属性

        Raises:
            RuntimeError: Sandbox 未启动时抛出

        示例:
            result = await manager.execute_code("python", "print('Hello')")
            print(result.stdout)  # "Hello\\n"
            print(result.exit_code)  # 0
        """
        if self.sandbox is None:
            raise RuntimeError("Sandbox 未启动，请先调用 start() 或使用 async with")

        # 根据语言构建执行命令
        if language.lower() == "python":
            # 使用 shlex.quote 避免 shell 转义问题
            import shlex
            cmd = f"python3 -c {shlex.quote(code)}"
        elif language.lower() == "bash":
            cmd = code
        else:
            # 其他语言直接当作 bash 命令执行
            cmd = f"{language} {code}"

        return await self.sandbox.commands.run(cmd, on_stdout=lambda data: print(data), on_stderr=lambda data: print(data))
