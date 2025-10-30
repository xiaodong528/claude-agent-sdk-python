"""E2B Template 定义"""

import os
from dotenv import load_dotenv
from e2b import Template, wait_for_timeout

# 加载 .env 文件
load_dotenv()

template = (
    Template()
    # 基础镜像（使用默认）
    .from_base_image()

    # 使用 sudo 安装全局 npm 包
    .run_cmd("sudo npm install -g @anthropic-ai/claude-code")

    # 设置用户
    .set_user("user")

    # 工作目录
    .set_workdir("/home/user")

    # 安装 Claude Agent SDK（以 user 用户身份）
    .run_cmd("pip install claude-agent-sdk")
    .run_cmd("pip install anthropic")

    # 环境变量配置（从 .env 文件动态加载）
    .set_envs({
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
        "ANTHROPIC_BASE_URL": os.getenv("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),
        "ANTHROPIC_DEFAULT_OPUS_MODEL": os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", "GLM-4.6"),
        "ANTHROPIC_DEFAULT_SONNET_MODEL": os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "GLM-4.6"),
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL", "GLM-4.5-Air"),
        "WORKSPACE_DIR": "/home/user"
    })

    # 启动命令：检查工具版本
    .set_start_cmd(
        """
        echo "=== Environment Version Check ===" && \
        python --version && \
        node --version
        """,
        wait_for_timeout(5_000)
    )
)

__all__ = ["template"]
