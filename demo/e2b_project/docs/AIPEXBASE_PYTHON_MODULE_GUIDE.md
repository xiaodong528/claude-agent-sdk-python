# AIPEXBASE Python 模块使用指南

> **版本**: 1.0
> **文件**: `aipexbase.py`
> **用途**: AIPEXBASE 项目自动创建工具 - 可作为命令行脚本或 Python 模块使用

---

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [使用方式](#使用方式)
  - [命令行使用](#1-命令行使用)
  - [Python 模块使用](#2-python-模块使用)
  - [集成到其他系统](#3-集成到其他系统)
- [API 参考](#api-参考)
- [配置说明](#配置说明)
- [错误处理](#错误处理)
- [实际应用示例](#实际应用示例)
- [故障排查](#故障排查)

---

## 概述

### 功能介绍

`aipexbase.py` 是一个用于自动化创建和管理 AIPEXBASE 项目的工具模块,提供以下核心能力:

- 🔐 **自动认证**: 通过管理员凭证自动登录获取 JWT token
- 📦 **项目创建**: 自动创建应用/项目并生成配置
- 🔑 **密钥管理**: 自动生成和管理 API Key (Token)
- 🔧 **MCP 配置**: 自动构建 MCP 服务器配置
- 🎯 **结构化输出**: 返回结构化的项目创建结果
- ⚠️ **完善异常处理**: 分类错误码和结构化错误信息

### 核心特性

| 特性                   | 说明                                        |
| ---------------------- | ------------------------------------------- |
| **双模式运行**   | 支持命令行脚本和 Python 模块导入两种模式    |
| **环境变量配置** | 从 .env 文件或系统环境变量读取配置          |
| **便捷 API**     | 提供高级封装函数,一行代码创建项目           |
| **增强异常系统** | 分类错误码、结构化错误信息、JSON 序列化支持 |
| **会话管理**     | 自动管理 HTTP 会话和认证状态                |
| **彩色输出**     | 使用 colorama 提供友好的终端输出            |

### 适用场景

- ✅ **开发者工具**: 快速创建开发/测试环境
- ✅ **自动化脚本**: 批量创建项目或自动化工作流
- ✅ **SaaS 平台**: 集成到多租户 SaaS 应用中为用户自动创建项目
- ✅ **CI/CD 集成**: 在持续集成/部署流程中自动配置环境
- ✅ **管理后台**: 为管理系统提供项目创建 API

---

## 快速开始

### 1. 环境准备

**Python 版本要求**: Python 3.7+

### 2. 安装依赖

```bash
# 确保已安装以下 Python 包
pip install requests colorama python-dotenv

# 或者使用 requirements.txt (如果项目提供)
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件 (位于 `scripts/` 目录下):

```bash
# 必填配置
AIPEXBASE_BASE_URL=http://localhost:8080/baas-api
AIPEXBASE_ADMIN_EMAIL=admin@example.com
AIPEXBASE_ADMIN_PASSWORD=your_password

# 可选配置
AIPEXBASE_API_KEY_NAME=MCP 专用密钥
AIPEXBASE_API_KEY_DESC=用于 MCP 工具调用的 API 密钥
AIPEXBASE_API_KEY_EXPIRE=2025-12-31 23:59:59
AIPEXBASE_OUTPUT_FILE=mcp_config.json
AIPEXBASE_VERBOSE=false
```

### 4. 快速测试

```bash
# 命令行模式 - 使用默认项目名称
python scripts/aipexbase.py

# 或指定项目名称
python scripts/aipexbase.py "我的测试项目" "项目描述"
```

---

## 使用方式

### 1. 命令行使用

#### 基本语法

```bash
python aipexbase.py [项目名称] [项目描述] [选项]
```

#### 示例

```bash
# 使用默认项目名称 (AI项目_时间戳)
python aipexbase.py

# 指定项目名称
python aipexbase.py "我的项目"

# 指定项目名称和描述
python aipexbase.py "我的项目" "这是一个测试项目"

# 启用详细输出
python aipexbase.py "我的项目" "测试" --verbose
```

#### 输出

成功执行后会:

1. 创建应用并返回 `app_id`
2. 生成 API Key (token)
3. 构建 MCP 配置并保存到 `mcp_config.json`
4. 在终端打印彩色格式化的结果信息

---

### 2. Python 模块使用

#### 方式 1: 使用便捷函数 (推荐 - 最简单)

这是最简单的使用方式,一行代码即可创建项目:

```python
from scripts.aipexbase import create_project

# 从 .env 读取配置,自动登录并创建项目
result = create_project("我的项目", "项目描述")

# 访问结果
print(f"App ID: {result.app_id}")
print(f"Token: {result.api_key}")
print(f"MCP URL: {result.mcp_url}")
```

**适用场景**: 简单脚本、快速原型开发

---

#### 方式 2: 使用工厂函数创建客户端

提供更多控制,适合需要多次调用的场景:

```python
from scripts.aipexbase import create_client_from_env

# 从环境变量创建客户端(自动登录)
client = create_client_from_env()

# 创建项目
result = client.create_project_complete(
    project_name="我的项目",
    description="项目描述",
    api_key_name="生产环境密钥",
    api_key_expire="2025-12-31 23:59:59"
)

# 可以继续使用同一客户端创建多个项目
result2 = client.create_project_complete("另一个项目", "另一个描述")
```

**适用场景**: 需要批量创建项目、管理多个项目

---

#### 方式 3: 完全自定义

完全控制客户端配置和认证流程:

```python
from scripts.aipexbase import AIPEXBASEClient

# 创建客户端
client = AIPEXBASEClient("http://your-server:8080/baas-api")

# 手动登录
client.login("admin@example.com", "password")

# 创建应用
app_info = client.create_application("我的应用", "应用描述")
app_id = app_info['appId']

# 生成 API Key
client.create_api_key(
    app_id=app_id,
    name="我的密钥",
    description="密钥描述",
    expire_at="2025-12-31 23:59:59"
)

# 查询密钥详情
keys_data = client.get_api_keys(app_id)
```

**适用场景**:

- 需要精细控制每个步骤
- 与现有系统深度集成
- 自定义错误处理和重试逻辑

---

### 3. 集成到其他系统

#### 场景 1: SaaS 平台用户注册时自动创建项目

```python
from scripts.aipexbase import create_project, APIError
import logging

logger = logging.getLogger(__name__)

def on_user_register(user_id: int, username: str):
    """
    用户注册时自动为其创建 AIPEXBASE 项目
    """
    try:
        # 创建项目
        result = create_project(
            project_name=f"user_{user_id}_project",
            description=f"{username}的个人项目"
        )

        # 保存到数据库
        save_to_database({
            'user_id': user_id,
            'app_id': result.app_id,
            'api_token': result.api_key,
            'mcp_url': result.mcp_url
        })

        # 返回给用户
        return {
            'success': True,
            'token': result.api_key,
            'mcp_url': result.mcp_url
        }

    except APIError as e:
        logger.error(f"创建项目失败: {e.to_json()}")
        return {
            'success': False,
            'error': str(e)
        }
```

---

#### 场景 2: 批量创建多个项目

```python
from scripts.aipexbase import create_client_from_env, APIError
import time

def batch_create_projects(project_names: list):
    """
    批量创建多个项目
    """
    # 创建客户端(只登录一次)
    client = create_client_from_env()

    results = []
    for name in project_names:
        try:
            result = client.create_project_complete(
                project_name=name,
                description=f"批量创建的项目: {name}",
                verbose=False  # 关闭详细输出
            )
            results.append({
                'name': name,
                'status': 'success',
                'app_id': result.app_id,
                'token': result.api_key
            })
            time.sleep(0.5)  # 避免请求过快

        except APIError as e:
            results.append({
                'name': name,
                'status': 'failed',
                'error': str(e)
            })

    return results

# 使用示例
projects = ["项目A", "项目B", "项目C"]
results = batch_create_projects(projects)
print(results)
```

---

#### 场景 3: Flask/Django Web API 集成

```python
from flask import Flask, request, jsonify
from scripts.aipexbase import create_project, APIError, AuthenticationError

app = Flask(__name__)

@app.route('/api/projects/create', methods=['POST'])
def create_user_project():
    """
    RESTful API 端点: 创建用户项目
    """
    data = request.get_json()
    project_name = data.get('name')
    description = data.get('description', '')

    if not project_name:
        return jsonify({'error': '项目名称不能为空'}), 400

    try:
        result = create_project(project_name, description)

        return jsonify({
            'success': True,
            'data': {
                'app_id': result.app_id,
                'app_name': result.app_name,
                'api_key': result.api_key,
                'mcp_url': result.mcp_url
            }
        }), 201

    except AuthenticationError as e:
        return jsonify({
            'success': False,
            'error': '服务器认证失败',
            'details': e.to_dict()
        }), 500

    except APIError as e:
        return jsonify({
            'success': False,
            'error': 'API 调用失败',
            'details': e.to_dict()
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
```

---

## API 参考

### 核心类

#### `AIPEXBASEClient`

AIPEXBASE API 客户端类,提供底层 API 调用能力。

**初始化**

```python
client = AIPEXBASEClient(base_url: str)
```

| 参数         | 类型    | 说明                                                       |
| ------------ | ------- | ---------------------------------------------------------- |
| `base_url` | `str` | AIPEXBASE 服务器地址,如 `http://localhost:8080/baas-api` |

**主要方法**

##### `login(email, password) -> str`

管理员登录,获取 JWT token。

```python
token = client.login("admin@example.com", "password")
```

| 参数         | 类型    | 说明       |
| ------------ | ------- | ---------- |
| `email`    | `str` | 管理员邮箱 |
| `password` | `str` | 管理员密码 |

**返回**: JWT token 字符串
**异常**: `AuthenticationError` - 登录失败

---

##### `create_application(name, description='') -> Dict`

创建应用。

```python
app_info = client.create_application("我的应用", "应用描述")
```

| 参数            | 类型    | 说明           |
| --------------- | ------- | -------------- |
| `name`        | `str` | 应用名称       |
| `description` | `str` | 应用描述(可选) |

**返回**: 应用信息字典,包含 `appId`, `appName`, `status` 等字段
**异常**: `APIError` - API 调用失败

---

##### `create_api_key(app_id, name, description='', expire_at='') -> bool`

创建 API Key。

```python
success = client.create_api_key(
    app_id="123",
    name="我的密钥",
    description="密钥描述",
    expire_at="2025-12-31 23:59:59"
)
```

| 参数            | 类型    | 说明                                        |
| --------------- | ------- | ------------------------------------------- |
| `app_id`      | `str` | 应用 ID                                     |
| `name`        | `str` | API Key 名称                                |
| `description` | `str` | API Key 描述(可选)                          |
| `expire_at`   | `str` | 过期时间(可选,格式:`YYYY-MM-DD HH:mm:ss`) |

**返回**: `True` 表示创建成功
**异常**: `APIError` - 创建失败

---

##### `get_api_keys(app_id, page=1, page_size=10) -> Dict`

查询 API Key 列表。

```python
keys_data = client.get_api_keys(app_id="123")
records = keys_data.get('records', [])
```

| 参数          | 类型    | 说明                   |
| ------------- | ------- | ---------------------- |
| `app_id`    | `str` | 应用 ID                |
| `page`      | `int` | 页码(可选,默认 1)      |
| `page_size` | `int` | 每页数量(可选,默认 10) |

**返回**: 包含 `records` 列表的字典
**异常**: `APIError` - 查询失败

---

##### `create_project_complete(...) -> ProjectCreationResult`

一站式创建项目方法(推荐使用)。

```python
result = client.create_project_complete(
    project_name="我的项目",
    description="项目描述",
    api_key_name="MCP 专用密钥",
    api_key_description="密钥描述",
    api_key_expire="2025-12-31 23:59:59",
    mcp_server_name="aipexbase-mcp-server",
    verbose=True
)
```

| 参数                    | 类型     | 说明                   |
| ----------------------- | -------- | ---------------------- |
| `project_name`        | `str`  | 项目名称               |
| `description`         | `str`  | 项目描述(可选)         |
| `api_key_name`        | `str`  | API Key 显示名称(可选) |
| `api_key_description` | `str`  | API Key 描述(可选)     |
| `api_key_expire`      | `str`  | 过期时间(可选)         |
| `mcp_server_name`     | `str`  | MCP 服务器名称(可选)   |
| `verbose`             | `bool` | 是否显示详细输出(可选) |

**返回**: `ProjectCreationResult` 数据类
**异常**: `AuthenticationError`, `APIError`

---

### 工厂函数

#### `create_client_from_env(env_file=None, auto_login=True) -> AIPEXBASEClient`

从环境变量创建客户端并自动登录。

```python
client = create_client_from_env()
```

| 参数           | 类型     | 说明                                        |
| -------------- | -------- | ------------------------------------------- |
| `env_file`   | `str`  | .env 文件路径(可选,默认为脚本目录下的 .env) |
| `auto_login` | `bool` | 是否自动登录(可选,默认 True)                |

**返回**: 已登录的 `AIPEXBASEClient` 实例
**异常**: `ConfigurationError`, `AuthenticationError`

---

#### `create_project(project_name, description='', config=None, **kwargs) -> ProjectCreationResult`

便捷函数:快速创建项目。

```python
result = create_project("我的项目", "项目描述")
```

| 参数             | 类型     | 说明                                          |
| ---------------- | -------- | --------------------------------------------- |
| `project_name` | `str`  | 项目名称                                      |
| `description`  | `str`  | 项目描述(可选)                                |
| `config`       | `Dict` | 配置字典(可选,用于覆盖环境变量)               |
| `**kwargs`     | -        | 传递给 `create_project_complete` 的其他参数 |

**返回**: `ProjectCreationResult` 数据类
**异常**: `ConfigurationError`, `AuthenticationError`, `APIError`

---

### 数据类

#### `ProjectCreationResult`

项目创建结果数据类。

```python
@dataclass
class ProjectCreationResult:
    app_id: str              # 应用 ID
    app_name: str            # 应用名称
    api_key: str             # API Key (token)
    api_key_name: str        # API Key 显示名称
    mcp_url: str             # MCP 服务器连接 URL
    mcp_config: Dict         # MCP 配置字典
    app_info: Dict           # 完整应用信息
    api_key_info: Dict       # 完整 API Key 信息
```

**使用示例**:

```python
result = create_project("我的项目")

print(result.app_id)       # "app-123456"
print(result.api_key)      # "ak_xxxxxxxxx"
print(result.mcp_url)      # "http://host:port/mcp/sse?token=ak_xxx"
print(result.mcp_config)   # {'mcpServers': {...}}
```

---

### 异常体系

#### 异常层次结构

```
AIPEXBASEError (基类)
├── AuthenticationError    # 认证失败
├── APIError              # API 调用失败
└── ConfigurationError    # 配置错误
```

---

#### `AIPEXBASEError`

所有 AIPEXBASE 异常的基类。

**属性**:

| 属性               | 类型          | 说明                            |
| ------------------ | ------------- | ------------------------------- |
| `code`           | `ErrorCode` | 错误码枚举                      |
| `message`        | `str`       | 错误消息                        |
| `http_status`    | `int`       | HTTP 状态码(如适用)             |
| `context`        | `Dict`      | 上下文信息(如 email, app_id 等) |
| `details`        | `Dict`      | 详细信息(如 request, response)  |
| `original_error` | `Exception` | 原始异常对象                    |

**方法**:

- `to_dict() -> Dict`: 转换为字典
- `to_json(**kwargs) -> str`: 转换为 JSON 字符串

**使用示例**:

```python
try:
    result = create_project("项目")
except AIPEXBASEError as e:
    print(f"错误: {e}")                    # 格式化输出
    print(f"错误码: {e.code.value}")       # 获取错误码
    print(f"HTTP 状态: {e.http_status}")   # 获取 HTTP 状态
    print(f"上下文: {e.context}")          # 获取上下文

    # JSON 序列化
    error_json = e.to_json(indent=2)
    logger.error(error_json)
```

---

#### `AuthenticationError`

认证失败异常,用于登录失败、token 缺失/过期等场景。

**错误码**:

- `AUTH_LOGIN_FAILED` (1001): 登录失败
- `AUTH_INVALID_CREDENTIALS` (1002): 凭证无效
- `AUTH_TOKEN_MISSING` (1003): Token 缺失
- `AUTH_TOKEN_EXPIRED` (1004): Token 过期

**示例**:

```python
try:
    client.login(email, password)
except AuthenticationError as e:
    if e.code == ErrorCode.AUTH_INVALID_CREDENTIALS:
        print("用户名或密码错误")
    elif e.code == ErrorCode.AUTH_TOKEN_EXPIRED:
        print("会话已过期,请重新登录")
```

---

#### `APIError`

API 调用异常,用于 API 请求失败、响应异常等场景。

**错误码**:

- `API_REQUEST_FAILED` (2001): 请求失败
- `API_INVALID_RESPONSE` (2002): 响应无效
- `API_TIMEOUT` (2003): 请求超时
- `API_CONNECTION_ERROR` (2004): 连接错误
- `API_KEY_NOT_FOUND` (2005): Key 未找到
- `API_APP_CREATION_FAILED` (2006): 应用创建失败

**额外属性**:

- `endpoint`: API 端点
- `request_data`: 请求数据
- `response_data`: 响应数据

**示例**:

```python
try:
    result = client.create_application("项目名")
except APIError as e:
    print(f"API 错误: {e}")
    print(f"端点: {e.endpoint}")
    print(f"请求: {e.request_data}")
    print(f"响应: {e.response_data}")
```

---

#### `ConfigurationError`

配置错误异常,用于环境变量缺失、配置值无效等场景。

**错误码**:

- `CONFIG_MISSING_ENV` (3001): 环境变量缺失
- `CONFIG_INVALID_VALUE` (3002): 配置值无效

**示例**:

```python
try:
    client = create_client_from_env()
except ConfigurationError as e:
    print(f"配置错误: {e}")
    print(f"缺失的配置: {e.context.get('missing_vars')}")
```

---

### 错误码系统

#### 错误码分类

| 错误码范围 | 分类      | 说明                       |
| ---------- | --------- | -------------------------- |
| 1xxx       | 认证相关  | 登录、token 等认证问题     |
| 2xxx       | API 相关  | API 请求、响应、超时等问题 |
| 3xxx       | 配置相关  | 环境变量、配置值等问题     |
| 4xxx/5xxx  | HTTP 相关 | HTTP 状态码错误            |
| 9xxx       | 未知错误  | 未分类的错误               |

#### 完整错误码列表

```python
class ErrorCode(str, Enum):
    # 认证相关 (1xxx)
    AUTH_LOGIN_FAILED = "1001"
    AUTH_INVALID_CREDENTIALS = "1002"
    AUTH_TOKEN_MISSING = "1003"
    AUTH_TOKEN_EXPIRED = "1004"

    # API 相关 (2xxx)
    API_REQUEST_FAILED = "2001"
    API_INVALID_RESPONSE = "2002"
    API_TIMEOUT = "2003"
    API_CONNECTION_ERROR = "2004"
    API_KEY_NOT_FOUND = "2005"
    API_APP_CREATION_FAILED = "2006"

    # 配置相关 (3xxx)
    CONFIG_MISSING_ENV = "3001"
    CONFIG_INVALID_VALUE = "3002"

    # HTTP 相关 (4xxx/5xxx)
    HTTP_4XX_ERROR = "4000"
    HTTP_5XX_ERROR = "5000"
    HTTP_UNKNOWN_ERROR = "4999"

    # 未知错误 (9xxx)
    UNKNOWN_ERROR = "9999"
```

---

## 配置说明

### 环境变量详解

#### 必填配置

| 变量名                       | 说明                 | 示例                               |
| ---------------------------- | -------------------- | ---------------------------------- |
| `AIPEXBASE_BASE_URL`       | AIPEXBASE 服务器地址 | `http://localhost:8080/baas-api` |
| `AIPEXBASE_ADMIN_EMAIL`    | 管理员邮箱           | `admin@example.com`              |
| `AIPEXBASE_ADMIN_PASSWORD` | 管理员密码           | `your_password`                  |

#### 可选配置

| 变量名                       | 说明                                   | 默认值                           |
| ---------------------------- | -------------------------------------- | -------------------------------- |
| `AIPEXBASE_API_KEY_NAME`   | API Key 显示名称                       | `MCP 专用密钥`                 |
| `AIPEXBASE_API_KEY_DESC`   | API Key 描述                           | `用于 MCP 工具调用的 API 密钥` |
| `AIPEXBASE_API_KEY_EXPIRE` | 过期时间(格式:`YYYY-MM-DD HH:mm:ss`) | (永不过期)                       |
| `AIPEXBASE_OUTPUT_FILE`    | 输出文件路径                           | `mcp_config.json`              |
| `AIPEXBASE_VERBOSE`        | 详细输出(`true`/`false`)           | `false`                        |

---

### .env 文件示例

```bash
# ========================================
# AIPEXBASE 配置文件示例
# ========================================

# --- 必填配置 ---
AIPEXBASE_BASE_URL=http://localhost:8080/baas-api
AIPEXBASE_ADMIN_EMAIL=admin@example.com
AIPEXBASE_ADMIN_PASSWORD=your_secure_password

# --- 可选配置 ---
AIPEXBASE_API_KEY_NAME=MCP 专用密钥
AIPEXBASE_API_KEY_DESC=用于 MCP 工具调用的 API 密钥
AIPEXBASE_API_KEY_EXPIRE=2025-12-31 23:59:59
AIPEXBASE_OUTPUT_FILE=mcp_config.json
AIPEXBASE_VERBOSE=false

# --- 生产环境示例 ---
# AIPEXBASE_BASE_URL=https://api.example.com/baas-api
# AIPEXBASE_ADMIN_EMAIL=admin@production.com
# AIPEXBASE_ADMIN_PASSWORD=production_password
# AIPEXBASE_API_KEY_NAME=生产环境密钥
# AIPEXBASE_API_KEY_EXPIRE=2026-01-01 00:00:00
```

---

## 错误处理

### 基本捕获

```python
from scripts.aipexbase import create_project, AuthenticationError, APIError

try:
    result = create_project("我的项目")
    print(f"成功: {result.api_key}")

except AuthenticationError as e:
    print(f"认证失败: {e}")
    # 处理认证错误

except APIError as e:
    print(f"API 错误: {e}")
    # 处理 API 错误
```

---

### 详细错误信息

```python
try:
    result = client.create_project_complete("项目名称")

except APIError as e:
    # 访问结构化错误信息
    print(f"错误码: {e.code.value}")           # "2001"
    print(f"错误消息: {e.message}")            # "API请求失败"
    print(f"HTTP状态: {e.http_status}")       # 500
    print(f"端点: {e.endpoint}")              # "/admin/application"
    print(f"上下文: {e.context}")             # {'app_id': '123'}
    print(f"详细信息: {e.details}")           # {'request': {...}, 'response': {...}}

    # JSON 序列化
    error_json = e.to_json(indent=2)
    logger.error(error_json)
```

---

### 统一异常处理

```python
from scripts.aipexbase import AIPEXBASEError

try:
    result = create_project("项目")

except AIPEXBASEError as e:
    # 统一处理所有 AIPEXBASE 异常
    print(f"操作失败: {e}")
    print(f"错误类型: {e.__class__.__name__}")
    print(f"错误码: {e.code.value}")

    if e.original_error:
        print(f"原始错误: {e.original_error}")
```

---

### 错误重试逻辑

```python
import time
from scripts.aipexbase import create_project, APIError, ErrorCode

def create_project_with_retry(project_name: str, max_retries: int = 3):
    """
    带重试的项目创建
    """
    for attempt in range(max_retries):
        try:
            result = create_project(project_name)
            return result

        except APIError as e:
            # 只重试可恢复的错误
            if e.code in [ErrorCode.API_TIMEOUT, ErrorCode.API_CONNECTION_ERROR]:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"重试 {attempt + 1}/{max_retries} (等待 {wait_time}s)...")
                    time.sleep(wait_time)
                    continue
            # 其他错误直接抛出
            raise

    raise APIError("达到最大重试次数")

# 使用
result = create_project_with_retry("我的项目")
```

---

## 实际应用示例

### 示例 1: 命令行批量创建工具

创建 `batch_create.py`:

```python
#!/usr/bin/env python3
"""
批量创建 AIPEXBASE 项目的命令行工具
"""
import sys
from scripts.aipexbase import create_client_from_env, APIError

def batch_create(project_list_file: str):
    """
    从文件读取项目列表并批量创建

    文件格式 (每行一个项目):
    项目名称|项目描述
    """
    # 读取项目列表
    with open(project_list_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 创建客户端(只登录一次)
    print("正在登录...")
    client = create_client_from_env()
    print(f"成功! 开始创建 {len(lines)} 个项目...\n")

    results = []
    for i, line in enumerate(lines, 1):
        parts = line.strip().split('|')
        name = parts[0]
        desc = parts[1] if len(parts) > 1 else ''

        print(f"[{i}/{len(lines)}] 创建项目: {name}")
        try:
            result = client.create_project_complete(
                project_name=name,
                description=desc,
                verbose=False
            )
            results.append({
                'name': name,
                'status': 'success',
                'app_id': result.app_id,
                'token': result.api_key
            })
            print(f"  ✓ 成功 - Token: {result.api_key[:20]}...\n")

        except APIError as e:
            results.append({
                'name': name,
                'status': 'failed',
                'error': str(e)
            })
            print(f"  ✗ 失败: {e}\n")

    # 输出汇总
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n完成! 成功: {success_count}/{len(lines)}")

    # 保存结果到文件
    import json
    with open('batch_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("详细结果已保存到: batch_results.json")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python batch_create.py <项目列表文件>")
        sys.exit(1)

    batch_create(sys.argv[1])
```

**项目列表文件** (`projects.txt`):

```
电商系统|在线购物平台
内容管理系统|CMS 后台
用户反馈系统|收集用户意见
数据分析平台|BI 分析工具
```

**运行**:

```bash
python batch_create.py projects.txt
```

---

### 示例 2: FastAPI REST API

创建 `api_server.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scripts.aipexbase import create_project, APIError, AuthenticationError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AIPEXBASE 项目管理 API")

class ProjectRequest(BaseModel):
    name: str
    description: str = ""
    api_key_expire: str = ""

class ProjectResponse(BaseModel):
    success: bool
    app_id: str = None
    app_name: str = None
    api_key: str = None
    mcp_url: str = None
    error: str = None

@app.post("/projects", response_model=ProjectResponse)
async def create_new_project(request: ProjectRequest):
    """
    创建新项目
    """
    try:
        result = create_project(
            project_name=request.name,
            description=request.description,
            api_key_expire=request.api_key_expire
        )

        logger.info(f"项目创建成功: {result.app_id}")

        return ProjectResponse(
            success=True,
            app_id=result.app_id,
            app_name=result.app_name,
            api_key=result.api_key,
            mcp_url=result.mcp_url
        )

    except AuthenticationError as e:
        logger.error(f"认证失败: {e}")
        raise HTTPException(status_code=500, detail="服务器认证失败")

    except APIError as e:
        logger.error(f"API 错误: {e.to_json()}")
        return ProjectResponse(
            success=False,
            error=str(e)
        )

@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**运行**:

```bash
pip install fastapi uvicorn
python api_server.py
```

**测试 API**:

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "测试项目", "description": "API 测试"}'
```

---

### 示例 3: Django 管理命令

创建 `yourapp/management/commands/create_aipex_project.py`:

```python
from django.core.management.base import BaseCommand
from scripts.aipexbase import create_project, APIError

class Command(BaseCommand):
    help = '创建 AIPEXBASE 项目'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='项目名称')
        parser.add_argument('--description', type=str, default='', help='项目描述')
        parser.add_argument('--save-to-db', action='store_true', help='保存到数据库')

    def handle(self, *args, **options):
        name = options['name']
        description = options['description']
        save_to_db = options['save_to_db']

        self.stdout.write(f'正在创建项目: {name}')

        try:
            result = create_project(name, description)

            self.stdout.write(self.style.SUCCESS(
                f'项目创建成功!\n'
                f'App ID: {result.app_id}\n'
                f'Token: {result.api_key}\n'
                f'MCP URL: {result.mcp_url}'
            ))

            if save_to_db:
                # 保存到 Django 数据库
                from yourapp.models import AipexProject
                AipexProject.objects.create(
                    name=result.app_name,
                    app_id=result.app_id,
                    api_key=result.api_key,
                    mcp_url=result.mcp_url
                )
                self.stdout.write(self.style.SUCCESS('已保存到数据库'))

        except APIError as e:
            self.stdout.write(self.style.ERROR(f'创建失败: {e}'))
```

**运行**:

```bash
python manage.py create_aipex_project "我的项目" --description "测试" --save-to-db
```

---

## 故障排查

### 常见问题

#### 问题 1: 登录失败 - 401 Unauthorized

**症状**: `AuthenticationError: [1001] 登录失败`

**可能原因**:

- 邮箱或密码错误
- 账号被禁用
- 环境变量配置错误

**解决方法**:

1. 检查 `.env` 文件中的 `AIPEXBASE_ADMIN_EMAIL` 和 `AIPEXBASE_ADMIN_PASSWORD`
2. 确认账号在系统中存在且状态正常
3. 尝试通过浏览器登录管理后台验证凭证

---

#### 问题 2: 连接失败 - Connection Error

**症状**: `APIError: [2004] 连接失败: 无法连接到服务器`

**可能原因**:

- 服务器地址错误
- 服务器未启动
- 网络不通

**解决方法**:

1. 检查 `AIPEXBASE_BASE_URL` 是否正确
2. 确认 AIPEXBASE 后端服务已启动
3. 测试网络连通性: `curl -I <BASE_URL>`

---

#### 问题 3: 环境变量缺失

**症状**: `ConfigurationError: [3001] 缺少必要的环境变量`

**可能原因**:

- 未创建 `.env` 文件
- `.env` 文件位置错误
- 环境变量名拼写错误

**解决方法**:

1. 创建 `.env` 文件在 `scripts/` 目录下
2. 参照 `.env.example` 填写必要配置
3. 确认环境变量名称正确(区分大小写)

---

#### 问题 4: API 返回错误 - 业务异常

**症状**: `APIError: [2002] API错误: 参数错误`

**可能原因**:

- 项目名称包含非法字符
- 项目名称过长或为空
- 权限不足

**解决方法**:

1. 检查项目名称是否符合规范
2. 确认管理员账号有创建项目权限
3. 查看错误详情: `print(e.details)`

---

#### 问题 5: 依赖包缺失

**症状**: `ModuleNotFoundError: No module named 'requests'`

**解决方法**:

```bash
pip install requests colorama python-dotenv
```

---

### 调试技巧

#### 1. 启用详细输出

```python
# 方式 1: 环境变量
os.environ['AIPEXBASE_VERBOSE'] = 'true'

# 方式 2: 参数传递
result = client.create_project_complete(
    project_name="项目",
    verbose=True  # 启用详细输出
)
```

---

#### 2. 查看完整错误信息

```python
try:
    result = create_project("项目")
except Exception as e:
    # 打印完整异常堆栈
    import traceback
    traceback.print_exc()

    # 如果是 AIPEXBASE 异常,打印 JSON
    if isinstance(e, AIPEXBASEError):
        print(e.to_json(indent=2))
```

---

#### 3. 测试连接

创建 `test_connection.py`:

```python
from scripts.aipexbase import AIPEXBASEClient

# 测试连接和认证
client = AIPEXBASEClient("http://localhost:8080/baas-api")

try:
    token = client.login("admin@example.com", "password")
    print(f"✓ 连接成功! Token: {token[:20]}...")
except Exception as e:
    print(f"✗ 连接失败: {e}")
```

---

#### 4. 验证环境变量

创建 `check_env.py`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
env_file = Path(__file__).parent / '.env'
load_dotenv(env_file)

# 检查必要变量
required_vars = [
    'AIPEXBASE_BASE_URL',
    'AIPEXBASE_ADMIN_EMAIL',
    'AIPEXBASE_ADMIN_PASSWORD'
]

for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✓ {var}: {value[:20]}..." if len(value) > 20 else f"✓ {var}: {value}")
    else:
        print(f"✗ {var}: 未设置")
```

---

### 日志配置

#### 配置 Python logging

```python
import logging
from scripts.aipexbase import create_project

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aipexbase.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 捕获详细错误
try:
    result = create_project("项目")
except Exception as e:
    logger.exception("项目创建失败")
```

---

## 最佳实践

### 1. 使用环境变量管理配置

❌ **不推荐**: 硬编码凭证

```python
client = AIPEXBASEClient("http://localhost:8080")
client.login("admin@example.com", "hardcoded_password")  # 危险!
```

✅ **推荐**: 使用环境变量

```python
client = create_client_from_env()  # 从 .env 读取
```

---

### 2. 重用客户端实例

❌ **不推荐**: 每次都创建新客户端

```python
for name in project_names:
    client = create_client_from_env()  # 重复登录!
    result = client.create_project_complete(name)
```

✅ **推荐**: 重用客户端

```python
client = create_client_from_env()  # 登录一次
for name in project_names:
    result = client.create_project_complete(name)
```

---

### 3. 分类处理异常

❌ **不推荐**: 泛化捕获

```python
try:
    result = create_project("项目")
except Exception as e:
    print(f"错误: {e}")
```

✅ **推荐**: 分类处理

```python
try:
    result = create_project("项目")
except AuthenticationError as e:
    # 认证错误 -> 重新登录
    logger.error(f"认证失败,请检查凭证: {e}")
except APIError as e:
    # API 错误 -> 可能重试
    if e.code == ErrorCode.API_TIMEOUT:
        logger.warning(f"请求超时,建议重试: {e}")
    else:
        logger.error(f"API 调用失败: {e}")
```

---

### 4. 记录结构化日志

❌ **不推荐**: 简单字符串日志

```python
except APIError as e:
    logger.error(str(e))
```

✅ **推荐**: 结构化 JSON 日志

```python
except APIError as e:
    logger.error(e.to_json(indent=2))
    # 或者
    logger.error("API 错误", extra={
        'error_code': e.code.value,
        'http_status': e.http_status,
        'endpoint': e.endpoint,
        'context': e.context
    })
```

---

### 5. 设置合理的过期时间

❌ **不推荐**: 永不过期

```python
result = create_project("项目")  # API Key 永不过期
```

✅ **推荐**: 设置过期时间

```python
result = create_project(
    "项目",
    api_key_expire="2025-12-31 23:59:59"  # 1 年后过期
)
```

---

## 总结

### 核心要点

1. **双模式运行**: 命令行脚本 + Python 模块
2. **三种使用方式**: 便捷函数(最简单) > 工厂函数 > 完全自定义
3. **完善异常处理**: 分类错误码、结构化错误信息、JSON 序列化
4. **环境变量配置**: 从 .env 文件读取,支持多环境配置
5. **一站式 API**: `create_project_complete` 方法自动完成所有步骤

### 推荐使用流程

```python
# 1. 创建 .env 配置文件
# 2. 使用便捷函数快速创建
from scripts.aipexbase import create_project, APIError

try:
    result = create_project("我的项目", "项目描述")
    print(f"✓ 创建成功! Token: {result.api_key}")
except APIError as e:
    print(f"✗ 创建失败: {e}")
```

### 集成检查清单

- [ ] 安装依赖: `requests`, `colorama`, `python-dotenv`
- [ ] 创建 `.env` 配置文件
- [ ] 确认服务器地址和凭证正确
- [ ] 测试连接和认证
- [ ] 根据场景选择使用方式(便捷函数/工厂函数/自定义)
- [ ] 实现错误处理和重试逻辑
- [ ] 配置日志记录
- [ ] 测试完整流程

---

## 附录

### A. 环境变量完整配置模板

```bash
# ========================================
# AIPEXBASE 配置模板
# ========================================

# === 必填配置 ===
AIPEXBASE_BASE_URL=http://localhost:8080/baas-api
AIPEXBASE_ADMIN_EMAIL=admin@example.com
AIPEXBASE_ADMIN_PASSWORD=your_secure_password

# === 可选配置 ===
AIPEXBASE_API_KEY_NAME=MCP 专用密钥
AIPEXBASE_API_KEY_DESC=用于 MCP 工具调用的 API 密钥
AIPEXBASE_API_KEY_EXPIRE=2025-12-31 23:59:59
AIPEXBASE_OUTPUT_FILE=mcp_config.json
AIPEXBASE_VERBOSE=false

# === 多环境配置示例 ===

# 开发环境
# AIPEXBASE_BASE_URL=http://localhost:8080/baas-api

# 测试环境
# AIPEXBASE_BASE_URL=http://test-server:8080/baas-api

# 生产环境
# AIPEXBASE_BASE_URL=https://api.production.com/baas-api
# AIPEXBASE_ADMIN_EMAIL=admin@production.com
# AIPEXBASE_ADMIN_PASSWORD=production_password
```

---

### B. 错误码速查表

| 错误码 | 分类 | 说明         | 处理建议           |
| ------ | ---- | ------------ | ------------------ |
| 1001   | 认证 | 登录失败     | 检查邮箱和密码     |
| 1002   | 认证 | 凭证无效     | 确认账号状态       |
| 1003   | 认证 | Token 缺失   | 先调用 login()     |
| 1004   | 认证 | Token 过期   | 重新登录           |
| 2001   | API  | 请求失败     | 检查网络和服务器   |
| 2002   | API  | 响应无效     | 检查 API 兼容性    |
| 2003   | API  | 请求超时     | 增加超时时间或重试 |
| 2004   | API  | 连接错误     | 检查服务器地址     |
| 2005   | API  | Key 未找到   | 确认 API Key 存在  |
| 2006   | API  | 应用创建失败 | 检查权限和参数     |
| 3001   | 配置 | 环境变量缺失 | 创建 .env 文件     |
| 3002   | 配置 | 配置值无效   | 检查配置格式       |
| 4000   | HTTP | 4xx 错误     | 检查请求参数       |
| 5000   | HTTP | 5xx 错误     | 检查服务器状态     |
| 9999   | 未知 | 未知错误     | 查看详细日志       |

---

### C. 依赖包版本要求

```
requests>=2.25.0
colorama>=0.4.4
python-dotenv>=0.19.0
```

---
