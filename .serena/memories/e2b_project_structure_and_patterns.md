# E2B Project Structure and Patterns

## 项目概述
E2B Sandbox + Claude Agent SDK 集成项目，用于在 E2B 沙箱环境中运行 Claude Agent SDK。

## 目录结构

```
claude-agent-sdk-python/
├── examples/demo/e2b_project/          # E2B 项目目录
│   ├── .env.example                     # 环境变量模板
│   └── .gitignore                       # Git 忽略规则
│
├── demo/e2b-sandbox-claude-agent-sdk/  # 文档和配置目录
│   └── docs/
│       └── quick-start-workflow.md     # 快速开始工作流文档
│
├── e2b.Dockerfile                       # E2B Dockerfile（包含模型配置）
└── examples/quick_start.py              # SDK 快速开始示例

```

## 环境变量配置

### 必需的环境变量（6个）

1. **E2B_API_KEY**: E2B 平台 API 密钥
   - 获取地址: https://e2b.dev/dashboard
   - 用途: 访问 E2B Sandbox API

2. **ANTHROPIC_AUTH_TOKEN**: Anthropic API Token（智谱AI代理）
   - 获取地址: https://open.bigmodel.cn
   - 用途: 通过智谱AI访问 Claude API

3. **ANTHROPIC_BASE_URL**: Anthropic API 基础 URL
   - 值: `https://open.bigmodel.cn/api/anthropic`
   - 用途: 指定智谱AI代理端点

4. **ANTHROPIC_DEFAULT_OPUS_MODEL**: Opus 模型配置
   - 值: `GLM-4.6`
   - 用途: 映射 Claude Opus 到智谱AI模型

5. **ANTHROPIC_DEFAULT_SONNET_MODEL**: Sonnet 模型配置
   - 值: `GLM-4.6`
   - 用途: 映射 Claude Sonnet 到智谱AI模型

6. **ANTHROPIC_DEFAULT_HAIKU_MODEL**: Haiku 模型配置
   - 值: `GLM-4.5-Air`
   - 用途: 映射 Claude Haiku 到智谱AI模型

### 环境变量文件位置

- **模板文件**: `examples/demo/e2b_project/.env.example`
- **实际配置**: `examples/demo/e2b_project/.env` (用户需手动创建)

## 快速开始工作流

文档位置: `demo/e2b-sandbox-claude-agent-sdk/docs/quick-start-workflow.md`

### 5步工作流概览

1. **项目初始化** (5 分钟)
   - 创建项目目录
   - 配置环境变量（6个）
   - 设置 Git 忽略规则

2. **定义 Template** (5 分钟)
   - 创建 `template.py`
   - 使用 E2B Template Python API
   - 配置基础镜像和依赖

3. **构建 Template** (10 分钟)
   - 创建 `build_template.py`
   - 执行构建获取 Template ID
   - 保存到 `.template_id`

4. **实现 Sandbox 管理器** (5 分钟)
   - 创建 `sandbox_manager.py`
   - 长期运行模式支持
   - 生命周期管理

5. **集成 Claude Agent SDK** (5 分钟)
   - 创建 `agent_runner.py`
   - 在沙箱中执行 Agent 任务
   - 文件生成和验证

## 安全配置

### .gitignore 规则

项目级别 (`examples/demo/e2b_project/.gitignore`):
```
.env
.template_id
__pycache__/
*.pyc
```

仓库级别 (根目录 `.gitignore`):
```
# E2B Project files
examples/demo/e2b_project/.env
examples/demo/e2b_project/.template_id
demo/e2b-sandbox-claude-agent-sdk/.env
demo/e2b-sandbox-claude-agent-sdk/.template_id
```

### 敏感文件保护
- `.env` - 包含 API 密钥，绝不提交
- `.template_id` - 构建生成的 Template ID
- 建议文件权限: `chmod 600 .env`

## 智谱AI集成模式

### 模型映射策略
```
Claude Model        → 智谱AI Model
-------------------   ---------------
claude-opus-*       → GLM-4.6
claude-sonnet-*     → GLM-4.6
claude-haiku-*      → GLM-4.5-Air
```

### API 端点配置
- Base URL: `https://open.bigmodel.cn/api/anthropic`
- 认证方式: Bearer Token (ANTHROPIC_AUTH_TOKEN)
- 兼容性: Anthropic API v1 接口

## 开发模式

### 本地开发
```bash
cd examples/demo/e2b_project
cp .env.example .env
# 编辑 .env 填入真实密钥
python build_template.py
python agent_runner.py
```

### 环境验证
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required_vars = ['E2B_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 
                 'ANTHROPIC_BASE_URL', 'ANTHROPIC_DEFAULT_OPUS_MODEL',
                 'ANTHROPIC_DEFAULT_SONNET_MODEL', 'ANTHROPIC_DEFAULT_HAIKU_MODEL']
for var in required_vars:
    print(f'{'✅' if os.getenv(var) else '❌'} {var}')
"
```

## 依赖关系

### Python 依赖
- `e2b` - E2B Sandbox SDK
- `python-dotenv` - 环境变量管理
- `anthropic` - Anthropic/Claude API 客户端

### 系统要求
- Python 3.8+
- npm (用于安装 Claude Code CLI)
- Git (版本控制)

## 最佳实践

1. **环境变量管理**
   - 始终使用 `.env.example` 作为模板
   - 定期轮换 API 密钥
   - 使用环境变量验证脚本

2. **版本控制**
   - 提交 `.env.example`，不提交 `.env`
   - 提交 `.gitignore` 确保规则生效
   - `.template_id` 可以提交（非敏感信息）

3. **安全性**
   - 设置 `.env` 文件权限为 600
   - 使用专用密钥，不共享生产密钥
   - 定期检查 Git 历史确保无泄露

## 故障排查

### 常见问题

1. **构建超时**
   - 使用国内镜像加速
   - 增加超时时间配置

2. **Agent 初始化失败**
   - 验证 ANTHROPIC_AUTH_TOKEN 有效性
   - 检查网络连接到智谱AI

3. **找不到 Template ID**
   - 检查 `.template_id` 文件是否存在
   - 重新运行 `build_template.py`

## 参考资源

- E2B 官方文档: https://e2b.dev/docs
- 智谱AI API: https://open.bigmodel.cn
- Claude Agent SDK: 本项目 `src/` 目录
- 快速开始示例: `examples/quick_start.py`
