# E2B Template 文档更新会话总结

## 会话时间
2025-10-28

## 任务概述
根据 `template.py` 的实际实现，系统性更新所有 E2B 项目文档，确保文档与代码完全一致。

## 完成的主要工作

### 1. Template.py 重构变更
**API 调用方式更新**：
- `from_base_image("e2bdev/code-interpreter:latest")` → `from_base_image()`（使用默认镜像）
- `run_commands([...])` → 多次调用 `.run_cmd(...)`（每次一个命令）

**用户和目录配置**：
- 添加 `.set_user("user")`（非特权用户模式）
- 工作目录：`/workspace` → `/home/user/workspace`

**环境变量管理**：
- 添加 `import os` 和 `from dotenv import load_dotenv`
- 添加 `load_dotenv()` 调用
- 使用 `os.getenv()` 动态加载 6 个环境变量：
  * ANTHROPIC_AUTH_TOKEN
  * ANTHROPIC_BASE_URL
  * ANTHROPIC_DEFAULT_OPUS_MODEL
  * ANTHROPIC_DEFAULT_SONNET_MODEL
  * ANTHROPIC_DEFAULT_HAIKU_MODEL
  * WORKSPACE_DIR

**启动命令更新**：
- 从 Jupyter 启动脚本 `/root/.jupyter/start-up.sh`
- 改为版本检查命令（检查 python、pip、node、npm、claude-code、claude-agent-sdk）

### 2. 更新的文档列表（共 7 个）

1. ✅ `quick-start-workflow.md` - 快速开始工作流程
   - 更新 Step 2 的 template.py 示例
   - 更新 Step 5 的 agent_runner.py 示例（cwd 和文件路径）
   - 更新验证点描述

2. ✅ `01-architecture.md` - 系统架构设计
   - 更新 1.2 Template 定义层示例（第 69-99 行）
   - 更新 2.4 Agent 集成层示例（第 214 行）
   - 更新 4.2 完整转换示例（第 325-365 行）

3. ✅ `02-template-guide.md` - Template API 使用指南
   - 更新 run_cmd() 方法说明和示例
   - 更新 set_envs() 示例（展示 dotenv 用法）
   - 更新 set_start_cmd() 示例（版本检查）
   - 更新 set_workdir() 示例
   - 更新 2.2 链式 API 调用完整示例（第 185-231 行）
   - 更新 3.2 template.py 完整示例（第 247-311 行）
   - 更新所有最佳实践示例

4. ✅ `03-sandbox-guide.md` - Sandbox 管理指南
   - 批量替换所有 /workspace 为 /home/user/workspace
   - 更新 cwd 参数
   - 更新文件系统操作示例

5. ✅ `04-agent-integration.md` - Agent 集成指南
   - 批量替换所有 /workspace 路径
   - 更新 agent_task.py 路径引用

6. ✅ `05-best-practices.md` - 最佳实践
   - 批量替换所有 /workspace 路径为 /home/user/workspace

7. ✅ `06-troubleshooting.md` - 故障排除指南
   - 批量替换所有 /workspace 路径为 /home/user/workspace

### 3. 标准 Template 代码模式

```python
import os
from dotenv import load_dotenv
from e2b import Template, wait_for_timeout

# 加载 .env 文件
load_dotenv()

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
```

### 4. 验证结果

最终验证通过（所有指标为 0 表示完全清除旧模式）：
- ✅ `from_base_image("...")` 带参数调用：**0 个**
- ✅ 旧的 `/workspace` 路径：**0 个**
- ✅ 新的 `/home/user/workspace` 路径：**66 处**
- ✅ `template.py` 使用 `from_base_image()`：**1 处**（正确）

## 重要技术发现

### 1. 安全性增强
- **非特权用户模式**：`.set_user("user")` 而非 root
- **动态配置**：使用 python-dotenv 避免硬编码敏感信息
- **环境隔离**：用户级工作目录 `/home/user/workspace`

### 2. API 设计模式
- **链式调用**：每个 `run_cmd()` 独立调用，提高可读性
- **默认参数**：`from_base_image()` 不带参数使用 E2B 默认镜像
- **显式配置**：所有关键配置都明确指定（用户、目录、环境变量）

### 3. 版本检查策略
启动时自动检查所有依赖版本，便于：
- 调试环境问题
- 验证安装完整性
- 记录运行时环境

### 4. 文档一致性原则
- 所有代码示例必须与 `template.py` 实际实现完全一致
- 环境变量配置统一展示 dotenv 加载模式
- 路径引用在所有文档中保持统一（/home/user/workspace）
- API 调用方式在所有示例中保持一致

## 工作方法论

### 系统化更新流程
1. **理解源代码**：读取 `template.py` 了解实际实现
2. **识别差异**：使用 grep 搜索所有需要更新的模式
3. **任务跟踪**：TodoWrite 工具跟踪 8 个任务进度
4. **逐个更新**：按文档优先级依次更新
5. **全局验证**：grep 验证旧模式是否完全清除
6. **修复遗漏**：处理验证中发现的边缘情况

### 批量编辑策略
- **简单替换**：使用 `sed` 批量替换路径（如 /workspace）
- **复杂代码块**：使用 Edit 工具手动更新
- **验证循环**：每次批量操作后立即验证

### 遇到的挑战和解决方案
1. **自动替换失败**：05-best-practices.md 的 sed 替换导致语法错误
   - 解决：使用 `git checkout` 恢复，手动更新关键部分
   
2. **文件修改冲突**：编辑时文件被 linter 修改
   - 解决：重新读取文件后再编辑

3. **遗漏路径**：验证发现 4 处遗漏的 /workspace
   - 解决：逐个检查并手动修复

## 项目结构理解

```
examples/demo/e2b_project/
├── docs/                           # 技术文档目录
│   ├── quick-start-workflow.md    # 快速入门（30分钟实现）
│   ├── 01-architecture.md         # 架构设计文档
│   ├── 02-template-guide.md       # Template API 详细指南
│   ├── 03-sandbox-guide.md        # Sandbox 管理指南
│   ├── 04-agent-integration.md    # Agent 集成指南
│   ├── 05-best-practices.md       # 最佳实践和优化
│   └── 06-troubleshooting.md      # 故障排除指南
├── template.py                     # Template 定义（源代码）
├── .env.example                    # 环境变量模板
├── .gitignore                      # Git 忽略配置
└── e2b_claude_agent_sdk.ipynb     # Jupyter Notebook 示例
```

## 下次会话参考

### 已完成工作
- ✅ 所有 7 个文档已更新完成
- ✅ 所有代码示例与 template.py 保持一致
- ✅ API 调用方式统一（from_base_image(), run_cmd()）
- ✅ 工作目录路径统一（/home/user/workspace）
- ✅ 环境变量加载统一（dotenv 模式）

### 关键文件路径
- Template 源码：`examples/demo/e2b_project/template.py`
- 文档目录：`examples/demo/e2b_project/docs/`
- 环境变量示例：`examples/demo/e2b_project/.env.example`

### 如果需要进一步工作
1. 实际构建和测试 Template（`python build_template.py`）
2. 创建和测试 Sandbox 管理器
3. 实现和测试 Agent 运行器
4. 验证整个工作流程的端到端功能

### 文档维护注意事项
- 任何 template.py 的修改都需要同步更新所有文档
- 保持代码示例的实际可运行性
- 环境变量配置应始终使用 dotenv 模式
- 路径引用必须保持一致性
