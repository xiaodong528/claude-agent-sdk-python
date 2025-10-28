"""Agent Runner - 在 E2B Sandbox 中运行 code/*.py 脚本

该模块提供核心功能，用于在 E2B Sandbox 中执行 AI 代码生成脚本。
保持 Sandbox 环境清洁，只包含 AI 生成的代码文件。
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from sandbox_manager import SandboxManager

# 加载环境变量
load_dotenv()


def _read_template_id() -> str:
    """读取 Template ID 配置文件

    Returns:
        Template ID 字符串

    Raises:
        FileNotFoundError: 如果 .template_id 文件不存在
        ValueError: 如果文件中没有找到 TEMPLATE_ID
    """
    template_id_file = Path(__file__).parent.parent / ".template_id"

    if not template_id_file.exists():
        raise FileNotFoundError(
            f"Template ID 文件不存在: {template_id_file}\n"
            "请先运行 build_template.py 构建 Template"
        )

    with open(template_id_file) as f:
        for line in f:
            if line.startswith("TEMPLATE_ID="):
                template_id = line.split("=")[1].strip()
                if template_id:
                    return template_id

    raise ValueError("未在 .template_id 文件中找到 TEMPLATE_ID")


async def run_code_in_sandbox(
    code_file: str,
    env_vars: Optional[dict] = None
) -> dict:
    """在 E2B Sandbox 中运行 code/*.py 脚本

    工作流程:
    1. 读取 Template ID
    2. 读取 code/{code_file} 的内容
    3. 创建 Sandbox
    4. 将代码文件复制到 Sandbox
    5. 执行代码文件
    6. 捕获输出并列出生成的文件

    Args:
        code_file: code/ 目录下的 Python 文件名，如 "calculator.py"
        env_vars: 传递给 Sandbox 的环境变量，如 {"ANTHROPIC_AUTH_TOKEN": "..."}

    Returns:
        执行结果字典，包含:
        - exit_code: 进程退出码
        - files: 生成的文件列表（不包括输入的 code_file）
        - stdout: 标准输出（如果启用捕获）
        - stderr: 错误输出（如果启用捕获）

    Raises:
        FileNotFoundError: 如果 code_file 不存在
        RuntimeError: 如果 Sandbox 创建或执行失败

    Example:
        >>> result = await run_code_in_sandbox(
        ...     code_file="calculator.py",
        ...     env_vars={"ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN")}
        ... )
        >>> print(f"退出码: {result['exit_code']}")
        >>> print(f"生成的文件: {result['files']}")
    """
    # 1. 读取 Template ID
    print("📋 读取 Template ID...")
    template_id = _read_template_id()
    print(f"✅ Template ID: {template_id}")

    # 2. 读取代码文件
    code_path = Path(__file__).parent / "code" / code_file
    if not code_path.exists():
        raise FileNotFoundError(
            f"代码文件不存在: {code_path}\n"
            f"请确保 src/code/{code_file} 文件存在"
        )

    print(f"📄 读取代码文件: {code_file}")
    code_content = code_path.read_text(encoding="utf-8")
    print(f"✅ 代码大小: {len(code_content)} 字节")

    # 3. 准备环境变量（合并默认环境变量）
    default_env_vars = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
        "ANTHROPIC_BASE_URL": os.getenv("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),
    }
    if env_vars:
        default_env_vars.update(env_vars)

    # 4. 创建 Sandbox 并执行
    result = {
        "exit_code": -1,
        "files": [],
        "stdout": "",
        "stderr": ""
    }

    async with SandboxManager(template_id, default_env_vars) as manager:
        # 5. 写入代码文件到 Sandbox
        target_path = f"/home/user/workspace/{code_file}"
        print(f"📤 上传代码到 Sandbox: {target_path}")
        await manager.sandbox.files.write(target_path, code_content)
        print("✅ 代码文件已上传")

        # 6. 执行代码
        print(f"\n🚀 执行代码: python {target_path}\n")
        print("=" * 50)

        # commands.run() 返回 CommandResult，直接包含 exit_code
        command_result = await manager.sandbox.commands.run(
            cmd=f"python {target_path}",
            on_stdout=lambda msg: print(f"[Agent] {msg}"),
            on_stderr=lambda msg: print(f"[Error] {msg}"),
            timeout=600  # 10 分钟超时（Agent 执行可能需要较长时间）
        )

        # 7. 获取退出码
        exit_code = command_result.exit_code
        result["exit_code"] = exit_code

        print("=" * 50)
        print(f"\n✅ 执行完成 (退出码: {exit_code})")

        # 8. 列出生成的文件
        print("\n📂 检查生成的文件...")
        try:
            files = await manager.sandbox.files.list("/home/user/workspace")
            generated_files = [
                f.name for f in files
                if not f.name.startswith('.') and f.name != code_file
            ]
            result["files"] = generated_files

            if generated_files:
                print("✅ 生成的文件:")
                for file in generated_files:
                    print(f"  - {file}")
            else:
                print("⚠️  未发现新生成的文件")
        except Exception as e:
            print(f"⚠️  列出文件时出错: {e}")

    return result


async def run_code_with_service(
    code_file: str,
    service_port: int,
    env_vars: Optional[dict] = None,
    wait_time: int = 3
) -> dict:
    """在 E2B Sandbox 中运行 code/*.py 脚本并获取服务 URL

    该函数专门用于运行启动 Web 服务的代码，会在执行后等待服务启动，
    然后返回可访问的外部 URL。Sandbox 不会自动关闭，以保持服务运行。

    Args:
        code_file: code/ 目录下的 Python 文件名，如 "calculator.py"
        service_port: 服务监听的端口号，如 3000
        env_vars: 传递给 Sandbox 的环境变量
        wait_time: 等待服务启动的时间（秒），默认 3 秒

    Returns:
        执行结果字典，包含:
        - exit_code: 进程退出码
        - files: 生成的文件列表
        - service_url: 服务的外部访问 URL（如果服务启动成功）
        - sandbox_id: Sandbox ID
        - keep_alive: 是否保持 Sandbox 运行

    Example:
        >>> result = await run_code_with_service(
        ...     code_file="calculator.py",
        ...     service_port=3000,
        ...     env_vars={"ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN")}
        ... )
        >>> print(f"服务地址: {result['service_url']}")
        >>> print("提示: Sandbox 将保持运行直到超时")
    """
    # 1. 读取 Template ID
    print("📋 读取 Template ID...")
    template_id = _read_template_id()
    print(f"✅ Template ID: {template_id}")

    # 2. 读取代码文件
    code_path = Path(__file__).parent / "code" / code_file
    if not code_path.exists():
        raise FileNotFoundError(
            f"代码文件不存在: {code_path}\n"
            f"请确保 src/code/{code_file} 文件存在"
        )

    print(f"📄 读取代码文件: {code_file}")
    code_content = code_path.read_text(encoding="utf-8")
    print(f"✅ 代码大小: {len(code_content)} 字节")

    # 3. 准备环境变量
    default_env_vars = {
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
        "ANTHROPIC_BASE_URL": os.getenv("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),
    }
    if env_vars:
        default_env_vars.update(env_vars)

    # 4. 创建 Sandbox（不使用 Context Manager，手动管理生命周期）
    manager = SandboxManager(template_id, default_env_vars)
    result = {
        "exit_code": -1,
        "files": [],
        "service_url": None,
        "sandbox_id": None,
        "keep_alive": True
    }

    try:
        await manager.start()
        result["sandbox_id"] = manager.sandbox.sandbox_id

        # 5. 写入代码文件到 Sandbox
        target_path = f"/home/user/workspace/{code_file}"
        print(f"📤 上传代码到 Sandbox: {target_path}")
        await manager.sandbox.files.write(target_path, code_content)
        print("✅ 代码文件已上传")

        # 6. 执行代码
        print(f"\n🚀 执行代码: python {target_path}\n")
        print("=" * 50)

        command_result = await manager.sandbox.commands.run(
            cmd=f"python {target_path}",
            on_stdout=lambda msg: print(f"[Agent] {msg}"),
            on_stderr=lambda msg: print(f"[Error] {msg}"),
            timeout=600  # 10 分钟超时（Agent 执行可能需要较长时间）
        )

        # 7. 获取退出码
        exit_code = command_result.exit_code
        result["exit_code"] = exit_code

        print("=" * 50)
        print(f"\n✅ 执行完成 (退出码: {exit_code})")

        # 8. 如果执行成功，等待服务启动并获取 URL
        if exit_code == 0:
            print(f"\n⏳ 等待服务启动 ({wait_time} 秒)...")
            import asyncio
            await asyncio.sleep(wait_time)

            # 获取服务 URL
            print(f"🌐 获取服务 URL (端口 {service_port})...")
            host = manager.sandbox.get_host(port=service_port)
            service_url = f"https://{host}"
            result["service_url"] = service_url

            print(f"✅ 服务 URL: {service_url}")

        # 9. 列出生成的文件
        print("\n📂 检查生成的文件...")
        try:
            files = await manager.sandbox.files.list("/home/user/workspace")
            generated_files = [
                f.name for f in files
                if not f.name.startswith('.') and f.name != code_file
            ]
            result["files"] = generated_files

            if generated_files:
                print("✅ 生成的文件:")
                for file in generated_files:
                    print(f"  - {file}")
            else:
                print("⚠️  未发现新生成的文件")
        except Exception as e:
            print(f"⚠️  列出文件时出错: {e}")

        # 10. 不关闭 Sandbox，保持服务运行
        print(f"\n💡 提示: Sandbox (ID: {result['sandbox_id']}) 将保持运行")
        print(f"   - 服务将持续可用直到 Sandbox 超时（默认 3600 秒）")
        print(f"   - 如需手动关闭，请使用 E2B Dashboard 或 API")

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        # 出错时关闭 Sandbox
        await manager.close()
        raise

    return result


# 便捷函数：直接运行（用于简单测试）
async def main():
    """测试函数：运行 calculator.py 示例"""
    result = await run_code_in_sandbox(
        code_file="calculator.py",
        env_vars={
            "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN")
        }
    )

    print(f"\n🎉 任务完成!")
    print(f"退出码: {result['exit_code']}")
    print(f"生成的文件数: {len(result['files'])}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
