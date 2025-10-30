# E2B Template API 使用指南

## 概述

本文档详细介绍如何使用 E2B Template Python API 创建和管理 Sandbox 模板，完全替代传统的 Dockerfile 方式。

## 1. Template API 基础

### 1.1 核心概念

**Template** 是 E2B Sandbox 的蓝图，定义了：
- 基础镜像
- 依赖和软件包
- 环境变量
- 启动命令
- 文件系统配置

### 1.2 安装依赖

```bash
# 安装 E2B Python SDK
pip install e2b python-dotenv

# 创建环境变量文件
cat > .env << EOF
E2B_API_KEY=your_e2b_api_key
ANTHROPIC_AUTH_TOKEN=your_anthropic_token
EOF
```

### 1.3 获取 E2B API Key

1. 访问 [E2B Dashboard](https://e2b.dev/dashboard)
2. 注册/登录账号
3. 在 Settings → API Keys 中创建新的 API Key
4. 将 API Key 保存到 `.env` 文件

## 2. Template API 完整参考

### 2.1 核心方法

#### `from_base_image(image: Optional[str] = None)`

设置基础 Docker 镜像。如果不提供参数，使用 E2B 默认镜像。

```python
from e2b import Template

# 使用默认镜像（推荐）
template = Template().from_base_image()

# 也可以使用默认镜像
template = Template().from_base_image()

# 使用默认镜像
template = Template().from_base_image()
```

**可用的 E2B 官方镜像**:
- `e2bdev/code-interpreter:latest` - 包含 Python、Jupyter、常用数据科学库
- `e2bdev/desktop:latest` - 包含图形界面支持
- `ubuntu:22.04` - 标准 Ubuntu 系统

#### `run_cmd(command: str)`

执行单个 shell 命令安装依赖或配置环境。可以多次调用以链式执行命令。

```python
# 单个命令
template = Template().run_cmd("apt-get update")

# 多个命令（推荐：链式调用，每次一个命令）
template = (
    Template()
    # 系统依赖
    .run_cmd("apt-get update")
    .run_cmd("apt-get install -y curl git vim")

    # Node.js 工具
    .run_cmd("npm install -g @anthropic-ai/claude-code")

    # Python 包
    .run_cmd("pip install claude-agent-sdk")
    .run_cmd("pip install anthropic")
    .run_cmd("pip install requests")
)

# 使用国内镜像加速（中国用户推荐）
template = (
    Template()
    .run_cmd("pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")
    .run_cmd("pip install claude-agent-sdk")
)
```

#### `set_envs(envs: Dict[str, str])`

设置环境变量。推荐使用 python-dotenv 从 .env 文件动态加载敏感信息。

```python
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

template = Template().set_envs({
    # 从 .env 文件动态加载（敏感信息）
    "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
    "ANTHROPIC_BASE_URL": os.getenv("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),

    # 模型配置（也可以从 .env 加载）
    "ANTHROPIC_DEFAULT_SONNET_MODEL": os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "GLM-4.6"),

    # 应用配置（静态值）
    "APP_ENV": "production",
    "LOG_LEVEL": "INFO"
})
```

#### `set_start_cmd(cmd: str, wait_strategy: WaitStrategy)`

设置 Sandbox 启动时执行的命令。

```python
from e2b import Template, wait_for_timeout, wait_for_port

# 版本检查（推荐用于开发环境）
template = Template().set_start_cmd(
    """
    echo "=== Environment Version Check ===" && \
    python --version && \
    pip --version && \
    node --version && \
    npm --version
    """,
    wait_for_timeout(5_000)  # 等待 5 秒
)

# 等待端口策略（适合 Web 服务）
template = Template().set_start_cmd(
    "python -m http.server 8000",
    wait_for_port(8000, timeout=10_000)  # 等待端口 8000 就绪
)

# 后台服务（不等待）
template = Template().set_start_cmd(
    "nohup python service.py &",
    wait_for_timeout(1_000)
)
```

#### `copy_files(source: str, dest: str)`

从本地复制文件到镜像中。

```python
# 复制单个文件
template = Template().copy_files(
    "./config.json",
    "/app/config.json"
)

# 复制整个目录
template = Template().copy_files(
    "./src",
    "/app/src"
)

# 复制多个文件（链式调用）
template = (
    Template()
    .copy_files("./requirements.txt", "/app/requirements.txt")
    .copy_files("./src", "/app/src")
    .copy_files("./config", "/app/config")
)
```

#### `set_workdir(path: str)`

设置工作目录。

```python
template = (
    Template()
    .from_base_image()  # 使用默认镜像
    .set_user("user")  # 设置用户
    .set_workdir("/home/user/workspace")  # 后续命令都在此目录执行
    .run_cmd("pip install flask")  # 在 /home/user/workspace 目录下执行
)
```

### 2.2 链式 API 调用

Template API 支持链式调用，推荐按照以下顺序组织：

```python
import os
from dotenv import load_dotenv
from e2b import Template, wait_for_timeout

# 加载 .env 文件
load_dotenv()

template = (
    Template()
    # 1. 基础镜像
    .from_base_image()  # 使用默认镜像

    # 2. 设置用户
    .set_user("user")

    # 3. 工作目录
    .set_workdir("/home/user/workspace")

    # 4. 系统级依赖
    .run_cmd("apt-get update")
    .run_cmd("apt-get install -y build-essential")

    # 5. 运行时环境
    .run_cmd("npm install -g @anthropic-ai/claude-code")

    # 6. 应用依赖
    .run_cmd("pip install claude-agent-sdk")
    .run_cmd("pip install anthropic")

    # 7. 复制文件（如果需要）
    .copy_files("./config", "/home/user/workspace/config")

    # 8. 环境变量（从 .env 动态加载）
    .set_envs({
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
        "ANTHROPIC_BASE_URL": os.getenv("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),
        "WORKSPACE_DIR": "/home/user/workspace"
    })

    # 9. 启动命令（版本检查）
    .set_start_cmd(
        """echo "=== Version Check ===" && python --version && pip --version && node --version""",
        wait_for_timeout(5_000)
    )
)
```

## 3. 完整示例：Claude Agent SDK Template

### 3.1 项目结构

```
project/
├── template.py              # Template 定义
├── build_template.py        # 构建脚本
├── .env                     # 环境变量
└── .gitignore              # Git 忽略文件
```

### 3.2 `template.py` - Template 定义

```python
"""
E2B Template 定义：Claude Agent SDK 运行环境

这个 Template 创建了一个包含以下组件的 Sandbox 环境：
- Claude Code CLI
- Claude Agent SDK
- Python 运行时
- 必要的环境变量配置（从 .env 文件动态加载）
"""

import os
from dotenv import load_dotenv
from e2b import Template, wait_for_timeout

# 加载 .env 文件
load_dotenv()

# 定义 Template
template = (
    Template()
    # 基础镜像（使用默认）
    .from_base_image()

    # 设置用户
    .set_user("user")

    # 工作目录
    .set_workdir("/home/user/workspace")

    # 安装 Claude Code CLI
    .run_cmd("npm install -g @anthropic-ai/claude-code")

    # 安装 Claude Agent SDK
    .run_cmd("pip install claude-agent-sdk")
    .run_cmd("pip install anthropic")

    # 环境变量配置（从 .env 文件动态加载）
    .set_envs({
        "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
        "ANTHROPIC_BASE_URL": os.getenv("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic"),
        "ANTHROPIC_DEFAULT_OPUS_MODEL": os.getenv("ANTHROPIC_DEFAULT_OPUS_MODEL", "GLM-4.6"),
        "ANTHROPIC_DEFAULT_SONNET_MODEL": os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "GLM-4.6"),
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": os.getenv("ANTHROPIC_DEFAULT_HAIKU_MODEL", "GLM-4.5-Air"),
        "WORKSPACE_DIR": "/home/user/workspace"
    })

    # 启动命令：检查工具版本
    .set_start_cmd(
        """
        echo "=== Environment Version Check ===" && \
        python --version && \
        pip --version && \
        node --version && \
        npm --version && \
        claude --version && \
        python -c "import claude_agent_sdk; print(f'Claude Agent SDK: {claude_agent_sdk.__version__}')"
        """,
        wait_for_timeout(5_000)
    )
)

# 导出供 build_template.py 使用
__all__ = ["template"]
```

### 3.3 `build_template.py` - 构建脚本

```python
"""
E2B Template 构建脚本

运行此脚本以构建和注册 Template 到 E2B Cloud。
构建完成后会生成 Template ID，用于创建 Sandbox。

使用方法:
    python build_template.py

环境变量:
    E2B_API_KEY - E2B API 密钥（必需）
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from e2b import Template, default_build_logger

# 加载环境变量
load_dotenv()

# 导入 Template 定义
from template import template


def validate_environment():
    """验证必需的环境变量"""
    required_vars = ["E2B_API_KEY"]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ 错误：缺少必需的环境变量")
        print(f"   缺失: {', '.join(missing_vars)}")
        print("\n请在 .env 文件中设置这些变量。")
        sys.exit(1)


def save_template_id(template_id: str, alias: str):
    """保存 Template ID 到文件"""
    template_info = f"""# E2B Template 信息
# 此文件由 build_template.py 自动生成

TEMPLATE_ID={template_id}
TEMPLATE_ALIAS={alias}
"""

    # 保存到 .template_id 文件
    with open(".template_id", "w") as f:
        f.write(template_info)

    print(f"\n✅ Template ID 已保存到 .template_id 文件")


def build_template():
    """构建 E2B Template"""

    print("🚀 开始构建 E2B Template...")
    print("=" * 60)

    # 验证环境
    validate_environment()

    # 设置构建参数
    template_alias = "claude-agent-sandbox"
    cpu_count = 2
    memory_mb = 2048

    print(f"\n📋 构建配置:")
    print(f"   别名: {template_alias}")
    print(f"   CPU: {cpu_count} 核")
    print(f"   内存: {memory_mb} MB")
    print("\n" + "=" * 60)

    try:
        # 执行构建
        result = Template.build(
            template,
            alias=template_alias,
            cpu_count=cpu_count,
            memory_mb=memory_mb,
            on_build_logs=default_build_logger()  # 实时显示构建日志
        )

        # 显示结果
        print("\n" + "=" * 60)
        print("✅ Template 构建成功！")
        print("=" * 60)
        print(f"\n📦 Template 信息:")
        print(f"   Template ID: {result.template_id}")
        print(f"   别名: {result.alias}")

        # 保存 Template ID
        save_template_id(result.template_id, result.alias)

        # 使用说明
        print(f"\n📝 使用此 Template 创建 Sandbox:")
        print(f"\n   Python 代码:")
        print(f"   ```python")
        print(f"   from e2b import Sandbox")
        print(f"   sandbox = Sandbox('{result.template_id}')")
        print(f"   # 或使用别名")
        print(f"   sandbox = Sandbox('{result.alias}')")
        print(f"   ```")

        print(f"\n   命令行:")
        print(f"   ```bash")
        print(f"   e2b sandbox create {result.template_id}")
        print(f"   ```")

        return result

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Template 构建失败")
        print("=" * 60)
        print(f"\n错误信息: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    build_template()
```

### 3.4 `.env` - 环境变量配置

```bash
# E2B API 密钥
# 从 https://e2b.dev/dashboard 获取
E2B_API_KEY=your_e2b_api_key_here

# Anthropic API Token（运行时传递给 Sandbox）
# 从智谱 AI 获取
ANTHROPIC_AUTH_TOKEN=your_anthropic_token_here
```

### 3.5 `.gitignore` - Git 忽略文件

```
# 环境变量文件
.env
.template_id

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db
```

## 4. 构建和部署 Template

### 4.1 本地构建流程

```bash
# 1. 克隆项目并进入目录
cd your-project

# 2. 安装依赖
pip install e2b python-dotenv

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys

# 4. 运行构建脚本
python build_template.py
```

**预期输出**:
```
🚀 开始构建 E2B Template...
============================================================

📋 构建配置:
   别名: claude-agent-sandbox
   CPU: 2 核
   内存: 2048 MB

============================================================
[Build Log] Step 1/8 : FROM e2bdev/code-interpreter:latest
[Build Log] ---> Using cache
[Build Log] Step 2/8 : WORKDIR /home/user/workspace
[Build Log] ---> Using cache
[Build Log] Step 3/8 : RUN npm install -g @anthropic-ai/claude-code
[Build Log] ---> Running in abc123def456
[Build Log] + @anthropic-ai/claude-code@1.0.0
[Build Log] ---> abc123def456
[Build Log] Step 4/8 : RUN pip install claude-agent-sdk
[Build Log] ---> Running in xyz789abc123
[Build Log] Successfully installed claude-agent-sdk-0.1.0
[Build Log] ---> xyz789abc123
...

============================================================
✅ Template 构建成功！
============================================================

📦 Template 信息:
   Template ID: 172m9tbyjat0ss16v9e8
   别名: claude-agent-sandbox

✅ Template ID 已保存到 .template_id 文件
```

### 4.2 读取已构建的 Template ID

```python
# 方法 1: 从文件读取
def load_template_id():
    """从 .template_id 文件加载 Template ID"""
    with open(".template_id") as f:
        for line in f:
            if line.startswith("TEMPLATE_ID="):
                return line.split("=")[1].strip()
    return None

template_id = load_template_id()

# 方法 2: 使用 python-dotenv
from dotenv import dotenv_values

config = dotenv_values(".template_id")
template_id = config["TEMPLATE_ID"]

# 方法 3: 直接使用别名
template_alias = "claude-agent-sandbox"
```

### 4.3 更新 Template

```python
"""更新现有 Template"""

# 修改 template.py 中的配置
template = (
    Template()
    .from_base_image()  # 使用默认镜像
    .set_user("user")
    .set_workdir("/home/user/workspace")
    # 添加新的依赖
    .run_cmd("pip install pandas")
    .run_cmd("pip install numpy")
    .run_cmd("pip install matplotlib")  # 新增数据科学库
    .set_envs({
        "NEW_CONFIG": "value"  # 新增配置
    })
)

# 重新运行构建（会创建新版本）
python build_template.py

# E2B 会自动处理版本管理，别名指向最新版本
```

## 5. Template 最佳实践

### 5.1 分层构建策略

```python
# ✅ 推荐：按变化频率分层
template = (
    Template()
    # 第 1 层：基础镜像和用户设置（几乎不变）
    .from_base_image()  # 使用默认镜像
    .set_user("user")
    .set_workdir("/home/user/workspace")

    # 第 2 层：系统依赖（偶尔变化）
    .run_cmd("apt-get update")
    .run_cmd("apt-get install -y build-essential git")

    # 第 3 层：运行时环境（较少变化）
    .run_cmd("npm install -g @anthropic-ai/claude-code")

    # 第 4 层：应用依赖（经常变化）
    .run_cmd("pip install claude-agent-sdk")

    # 第 5 层：配置（最常变化）
    .set_envs({"CONFIG": "value"})
)

# ❌ 避免：所有操作混在一起
template = Template().run_cmd("apt-get update && npm install -g claude-code && pip install claude-agent-sdk")
```

### 5.2 使用镜像加速

```python
# 中国用户推荐配置
template = (
    Template()
    .from_base_image()  # 使用默认镜像
    .set_user("user")
    .set_workdir("/home/user/workspace")

    # 配置 npm 淘宝镜像
    .run_cmd("npm config set registry https://registry.npmmirror.com")

    # 配置 pip 清华镜像
    .run_cmd("pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")

    # 然后安装依赖
    .run_cmd("npm install -g @anthropic-ai/claude-code")
    .run_cmd("pip install claude-agent-sdk")
)
```

### 5.3 敏感信息管理

```python
import os
from dotenv import load_dotenv

# ❌ 错误：硬编码敏感信息
template = Template().set_envs({
    "API_KEY": "sk-1234567890abcdef"  # 不安全！会被提交到 Git
})

# ✅ 推荐：从 .env 文件加载
load_dotenv()

template = Template().set_envs({
    "API_KEY": os.getenv("API_KEY", ""),  # 从 .env 文件读取
    "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN", ""),
    "APP_ENV": "production"
})

# ✅ 或者：在 Sandbox 创建时传递
# template.py 中不设置敏感信息
load_dotenv()

template = Template().set_envs({
    "APP_ENV": "production"  # 只设置非敏感配置
})

# 在创建 Sandbox 时传递（见下一章）
sandbox = await AsyncSandbox.create(
    template=template_id,
    env_vars={
        "API_KEY": os.getenv("API_KEY")  # 运行时传递
    }
)
```

### 5.4 错误处理

```python
from e2b import Template
import sys

def safe_build_template():
    """安全的 Template 构建函数"""
    try:
        result = Template.build(
            template,
            alias="my-template",
            cpu_count=2,
            memory_mb=2048,
            on_build_logs=default_build_logger()
        )

        print(f"✅ 构建成功: {result.template_id}")
        return result

    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("提示: 检查 Template 定义是否正确")
        sys.exit(1)

    except ConnectionError as e:
        print(f"❌ 网络错误: {e}")
        print("提示: 检查网络连接和 E2B_API_KEY")
        sys.exit(1)

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        print("提示: 查看完整错误栈进行调试")
        sys.exit(1)
```

## 6. 常见配置场景

### 6.1 数据科学环境

```python
template = (
    Template()
    .from_base_image()  # 使用默认镜像，已包含基础库
    .set_user("user")
    .set_workdir("/home/user/workspace")
    .run_cmd("pip install pandas")
    .run_cmd("pip install numpy")
    .run_cmd("pip install matplotlib")
    .run_cmd("pip install seaborn")
    .run_cmd("pip install scikit-learn")
    .set_envs({
        "JUPYTER_ENABLE_LAB": "yes"
    })
)
```

### 6.2 Web 开发环境

```python
template = (
    Template()
    .from_base_image()  # 使用默认镜像
    .set_user("user")
    .set_workdir("/home/user/workspace")

    # 安装 Node.js
    .run_cmd("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -")
    .run_cmd("apt-get install -y nodejs")

    # 安装 Python
    .run_cmd("apt-get install -y python3 python3-pip")

    # 安装框架
    .run_cmd("pip3 install flask")
    .run_cmd("pip3 install fastapi")
    .run_cmd("pip3 install uvicorn")
    .run_cmd("npm install -g next@latest")
)
```

### 6.3 机器学习环境

```python
template = (
    Template()
    .from_base_image()  # 使用默认镜像
    .set_user("user")
    .set_workdir("/home/user/workspace")
    .run_cmd("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
    .run_cmd("pip install transformers")
    .run_cmd("pip install datasets")
    .run_cmd("pip install accelerate")
    .run_cmd("pip install claude-agent-sdk")
    .set_envs({
        "TRANSFORMERS_CACHE": "/home/user/workspace/.cache/huggingface",
        "HF_HOME": "/home/user/workspace/.cache/huggingface"
    })
)
```

## 7. 调试和测试

### 7.1 本地验证 Template 定义

```python
"""测试 Template 定义是否正确"""

from template import template

def validate_template():
    """验证 Template 配置"""

    # 检查是否定义了基础镜像
    assert template._base_image is not None, "未设置基础镜像"

    # 检查是否有安装命令
    assert len(template._commands) > 0, "未设置安装命令"

    # 检查环境变量
    assert template._env_vars is not None, "未设置环境变量"

    print("✅ Template 定义验证通过")

if __name__ == "__main__":
    validate_template()
```

### 7.2 构建日志分析

```python
from e2b import Template

# 自定义日志处理器
def custom_build_logger():
    """自定义构建日志处理"""
    def logger(log_entry):
        # 只显示重要信息
        if "error" in log_entry.lower() or "failed" in log_entry.lower():
            print(f"❌ {log_entry}")
        elif "successfully" in log_entry.lower():
            print(f"✅ {log_entry}")
        # 其他日志可以忽略或记录到文件
        else:
            pass  # 静默

    return logger

# 使用自定义日志器
result = Template.build(
    template,
    on_build_logs=custom_build_logger()
)
```

## 8. 总结

本章介绍了 E2B Template API 的完整使用方法，包括：

- ✅ Template API 核心方法和参数
- ✅ 完整的 Claude Agent SDK Template 示例
- ✅ 本地构建和部署流程
- ✅ 最佳实践和常见配置
- ✅ 错误处理和调试技巧

下一章将介绍如何使用构建好的 Template 创建和管理 Sandbox。
