#!/usr/bin/env python3
"""
AIPEXBASE 项目自动创建工具

可以作为命令行脚本运行，也可以作为 Python 模块导入使用。

=== 命令行使用 ===

1. 配置环境变量：
    cp .env.example .env
    # 编辑 .env 文件设置必要的配置项

2. 运行脚本：
    python aipexbase.py [项目名称] [项目描述]

示例：
    python aipexbase.py                          # 使用默认项目名称
    python aipexbase.py "我的项目"                # 指定项目名称
    python aipexbase.py "我的项目" "项目描述"      # 指定名称和描述

=== Python 模块使用 ===

导入：
    from scripts.aipexbase import (
        AIPEXBASEClient,          # 主客户端类
        create_client_from_env,   # 工厂函数：从环境变量创建客户端
        create_project,           # 便捷函数：快速创建项目
        ProjectCreationResult,    # 结果数据类
        AIPEXBASEError,           # 基础异常类
        AuthenticationError,      # 认证异常
        APIError,                 # API 异常
        ConfigurationError        # 配置异常
    )

方式 1: 使用便捷函数（最简单，推荐）
    result = create_project("我的项目", "项目描述")
    print(f"App ID: {result.app_id}")
    print(f"Token: {result.api_key}")
    print(f"MCP URL: {result.mcp_url}")

方式 2: 使用工厂函数创建客户端
    client = create_client_from_env()
    result = client.create_project_complete(
        project_name="我的项目",
        description="项目描述",
        api_key_name="生产环境密钥"
    )

方式 3: 完全自定义
    client = AIPEXBASEClient("http://server:8080")
    client.login("admin@example.com", "password")
    result = client.create_project_complete(
        project_name="我的项目",
        description="项目描述",
        api_key_expire="2025-12-31 23:59:59"
    )

集成到你的应用：
    from scripts.aipexbase import create_project, APIError

    try:
        result = create_project(f"user_{user_id}_project", "用户项目")

        # 保存到数据库
        save_to_db(user_id, {
            'app_id': result.app_id,
            'token': result.api_key,
            'mcp_url': result.mcp_url
        })

        return result.api_key
    except APIError as e:
        logger.error(f"创建项目失败: {e}")
        raise

=== 异常处理 ===

增强的异常系统提供结构化错误信息：

**异常类层次：**
- AIPEXBASEError          - 基础异常类，所有异常的父类
  - AuthenticationError   - 认证失败（登录、token 等）
  - APIError             - API 调用失败
  - ConfigurationError   - 配置错误（环境变量等）

**错误码系统：**
- 1xxx: 认证相关（1001=登录失败, 1002=凭证无效, 1003=Token缺失, 1004=Token过期）
- 2xxx: API相关（2001=请求失败, 2002=响应无效, 2003=超时, 2004=连接错误, 2005=Key未找到）
- 3xxx: 配置相关（3001=环境变量缺失, 3002=配置值无效）
- 4xxx/5xxx: HTTP错误

**异常属性：**
- code: 错误码（ErrorCode 枚举）
- message: 错误消息
- http_status: HTTP 状态码（如适用）
- context: 上下文信息（如 email、app_id 等）
- details: 详细信息（如 request、response）
- original_error: 原始异常对象

**使用示例：**

基本捕获：
    try:
        client.login(email, password)
    except AuthenticationError as e:
        print(f"登录失败: {e}")  # 格式化输出：[1001] 登录失败 - email=user@example.com

详细信息：
    try:
        result = client.create_project_complete("项目名称")
    except APIError as e:
        print(f"错误码: {e.code.value}")
        print(f"HTTP状态: {e.http_status}")
        print(f"上下文: {e.context}")
        print(f"详细信息: {e.details}")
        # JSON序列化
        error_json = e.to_json(indent=2)
        logger.error(error_json)

捕获所有异常：
    try:
        result = create_project("项目")
    except AIPEXBASEError as e:
        # 统一处理所有 AIPEXBASE 异常
        print(f"操作失败: {e}")
        if e.original_error:
            print(f"原因: {e.original_error}")

=== 功能说明 ===

1. 从环境变量或 .env 文件读取配置
2. 自动登录获取 JWT token
3. 创建应用/项目
4. 生成 API Key (Token)
5. 构建 MCP 服务器配置
6. 返回结构化的结果数据类

=== 环境变量配置 ===

必填：
    AIPEXBASE_BASE_URL          - 服务器地址
    AIPEXBASE_ADMIN_EMAIL       - 管理员邮箱
    AIPEXBASE_ADMIN_PASSWORD    - 管理员密码

可选：
    AIPEXBASE_API_KEY_NAME      - API Key 名称（默认：MCP 专用密钥）
    AIPEXBASE_API_KEY_DESC      - API Key 描述
    AIPEXBASE_API_KEY_EXPIRE    - 过期时间（格式：YYYY-MM-DD HH:mm:ss）
    AIPEXBASE_OUTPUT_FILE       - 输出文件路径（默认：mcp_config.json）
    AIPEXBASE_VERBOSE           - 详细输出（默认：false）
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    from colorama import init, Fore, Style
    from dotenv import load_dotenv
except ImportError as e:
    print(f"错误: 缺少必要的依赖库 - {e}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)

# 初始化 colorama
init(autoreset=True)


# ============================================================================
# 错误码枚举
# ============================================================================

class ErrorCode(str, Enum):
    """
    错误码枚举

    错误码分类：
    - 1xxx: 认证相关错误
    - 2xxx: API调用相关错误
    - 3xxx: 配置相关错误
    - 4xxx/5xxx: HTTP相关错误
    - 9xxx: 未知错误
    """
    # 认证相关 (1xxx)
    AUTH_LOGIN_FAILED = "1001"
    AUTH_INVALID_CREDENTIALS = "1002"
    AUTH_TOKEN_MISSING = "1003"
    AUTH_TOKEN_EXPIRED = "1004"

    # API调用相关 (2xxx)
    API_REQUEST_FAILED = "2001"
    API_INVALID_RESPONSE = "2002"
    API_TIMEOUT = "2003"
    API_CONNECTION_ERROR = "2004"
    API_KEY_NOT_FOUND = "2005"
    API_APP_CREATION_FAILED = "2006"

    # 配置相关 (3xxx)
    CONFIG_MISSING_ENV = "3001"
    CONFIG_INVALID_VALUE = "3002"

    # HTTP相关 (4xxx/5xxx)
    HTTP_4XX_ERROR = "4000"
    HTTP_5XX_ERROR = "5000"
    HTTP_UNKNOWN_ERROR = "4999"

    # 未知错误 (9xxx)
    UNKNOWN_ERROR = "9999"


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class ProjectCreationResult:
    """
    项目创建结果数据类

    Attributes:
        app_id: 应用ID
        app_name: 应用名称
        api_key: API Key (token)，用于 MCP 连接
        api_key_name: API Key 显示名称
        mcp_url: MCP 服务器连接 URL（完整的 SSE 端点）
        mcp_config: MCP 配置字典，可直接写入配置文件
        app_info: 完整的应用信息字典
        api_key_info: 完整的 API Key 信息字典

    Example:
        >>> result = client.create_project_complete("我的项目")
        >>> print(f"Token: {result.api_key}")
        >>> print(f"MCP URL: {result.mcp_url}")
    """
    app_id: str
    app_name: str
    api_key: str
    api_key_name: str
    mcp_url: str
    mcp_config: Dict[str, Any]
    app_info: Dict[str, Any] = field(repr=False)
    api_key_info: Dict[str, Any] = field(repr=False)


# ============================================================================
# 异常类定义
# ============================================================================

class AIPEXBASEError(Exception):
    """
    AIPEXBASE 基础异常类（增强版）

    功能：
    - 错误码系统
    - 结构化错误信息存储
    - HTTP状态码支持
    - 原始异常链
    - JSON序列化
    - 格式化输出

    Attributes:
        code: 错误码（ErrorCode枚举）
        message: 错误消息
        details: 详细信息字典
        http_status: HTTP状态码（如果适用）
        original_error: 原始异常对象
        context: 额外上下文信息

    Example:
        >>> raise AIPEXBASEError(
        ...     code=ErrorCode.API_REQUEST_FAILED,
        ...     message="请求失败",
        ...     http_status=500,
        ...     context={'url': 'http://...', 'method': 'POST'}
        ... )
    """

    # 默认错误码和消息模板（子类可覆盖）
    default_code: ErrorCode = ErrorCode.UNKNOWN_ERROR
    default_message: str = "发生了未知错误"

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[ErrorCode] = None,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初始化异常

        Args:
            message: 错误消息（可选，默认使用类的 default_message）
            code: 错误码（可选，默认使用类的 default_code）
            http_status: HTTP状态码
            details: 详细信息字典
            original_error: 原始异常对象
            context: 额外上下文信息（如URL、方法名等）
            **kwargs: 其他扩展字段
        """
        # 使用提供的或默认的错误消息和错误码
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.http_status = http_status
        self.details = details or {}
        self.original_error = original_error
        self.context = context or {}

        # 存储额外的kwargs以便扩展
        self.extra = kwargs

        # 调用父类构造函数
        super().__init__(self.message)

    def __str__(self) -> str:
        """字符串表示（用于日志）"""
        parts = [f"[{self.code.value}] {self.message}"]

        if self.http_status:
            parts.append(f"(HTTP {self.http_status})")

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"- {context_str}")

        if self.original_error:
            parts.append(f"- Caused by: {type(self.original_error).__name__}: {self.original_error}")

        return " ".join(parts)

    def __repr__(self) -> str:
        """开发者友好的表示"""
        return (
            f"{self.__class__.__name__}("
            f"code={self.code.value!r}, "
            f"message={self.message!r}, "
            f"http_status={self.http_status!r})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于JSON序列化）

        Returns:
            包含所有错误信息的字典
        """
        result = {
            'error_type': self.__class__.__name__,
            'code': self.code.value,
            'message': self.message,
        }

        if self.http_status:
            result['http_status'] = self.http_status

        if self.details:
            result['details'] = self.details

        if self.context:
            result['context'] = self.context

        if self.original_error:
            result['original_error'] = {
                'type': type(self.original_error).__name__,
                'message': str(self.original_error)
            }

        if self.extra:
            result['extra'] = self.extra

        return result

    def to_json(self, **kwargs) -> str:
        """
        转换为JSON字符串

        Args:
            **kwargs: 传递给 json.dumps 的参数

        Returns:
            JSON字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)


class AuthenticationError(AIPEXBASEError):
    """
    认证失败异常

    用于登录失败、token缺失/过期等场景

    Example:
        >>> raise AuthenticationError(
        ...     "登录失败：邮箱或密码错误",
        ...     code=ErrorCode.AUTH_INVALID_CREDENTIALS,
        ...     context={'email': 'user@example.com'}
        ... )
    """
    default_code = ErrorCode.AUTH_LOGIN_FAILED
    default_message = "认证失败"


class APIError(AIPEXBASEError):
    """
    API 调用异常

    用于API请求失败、响应异常等场景

    Attributes:
        request_data: 请求数据
        response_data: 响应数据
        endpoint: API端点

    Example:
        >>> raise APIError(
        ...     "API请求失败",
        ...     code=ErrorCode.API_REQUEST_FAILED,
        ...     http_status=500,
        ...     endpoint="/admin/application",
        ...     request_data={'name': 'test'},
        ...     response_data={'code': 1, 'message': 'error'}
        ... )
    """
    default_code = ErrorCode.API_REQUEST_FAILED
    default_message = "API调用失败"

    def __init__(
        self,
        message: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        # 将API特定字段添加到context
        context = kwargs.pop('context', {})
        if endpoint:
            context['endpoint'] = endpoint

        details = kwargs.pop('details', {})
        if request_data:
            details['request'] = request_data
        if response_data:
            details['response'] = response_data

        super().__init__(
            message=message,
            context=context,
            details=details,
            **kwargs
        )

        # 也存储为实例属性以便访问
        self.endpoint = endpoint
        self.request_data = request_data
        self.response_data = response_data


class ConfigurationError(AIPEXBASEError):
    """
    配置错误异常

    用于环境变量缺失、配置值无效等场景

    Example:
        >>> raise ConfigurationError(
        ...     "缺少必要的环境变量: AIPEXBASE_BASE_URL",
        ...     code=ErrorCode.CONFIG_MISSING_ENV,
        ...     context={'missing_vars': ['AIPEXBASE_BASE_URL']}
        ... )
    """
    default_code = ErrorCode.CONFIG_MISSING_ENV
    default_message = "配置错误"


# ============================================================================
# 便捷构造函数
# ============================================================================

def from_requests_error(error: Exception, endpoint: str = "") -> APIError:
    """
    从 requests 异常创建 APIError

    Args:
        error: requests 异常对象
        endpoint: API端点

    Returns:
        APIError实例

    Example:
        >>> try:
        ...     response = requests.get(url)
        ... except requests.exceptions.Timeout as e:
        ...     raise from_requests_error(e, endpoint="/api/users")
    """
    if isinstance(error, requests.exceptions.Timeout):
        return APIError(
            message=f"请求超时: {endpoint}",
            code=ErrorCode.API_TIMEOUT,
            endpoint=endpoint,
            original_error=error
        )
    elif isinstance(error, requests.exceptions.ConnectionError):
        return APIError(
            message="连接失败: 无法连接到服务器",
            code=ErrorCode.API_CONNECTION_ERROR,
            endpoint=endpoint,
            original_error=error
        )
    elif isinstance(error, requests.exceptions.HTTPError):
        http_status = error.response.status_code if error.response else None
        response_text = error.response.text if error.response else ""
        return APIError(
            message=f"HTTP错误 {http_status}: {response_text}",
            code=ErrorCode.HTTP_4XX_ERROR if http_status and http_status < 500 else ErrorCode.HTTP_5XX_ERROR,
            http_status=http_status,
            endpoint=endpoint,
            original_error=error
        )
    else:
        return APIError(
            message=str(error),
            code=ErrorCode.API_REQUEST_FAILED,
            endpoint=endpoint,
            original_error=error
        )


def from_api_response(response_data: Dict[str, Any], endpoint: str = "") -> APIError:
    """
    从API响应创建 APIError

    Args:
        response_data: API响应字典（包含 code 和 message 字段）
        endpoint: API端点

    Returns:
        APIError实例

    Example:
        >>> result = {'code': 1, 'message': '参数错误'}
        >>> raise from_api_response(result, endpoint="/admin/login")
    """
    error_msg = response_data.get('message', '未知API错误')
    return APIError(
        message=f"API错误: {error_msg}",
        code=ErrorCode.API_INVALID_RESPONSE,
        endpoint=endpoint,
        response_data=response_data
    )


class AIPEXBASEClient:
    """AIPEXBASE API 客户端"""

    def __init__(self, base_url: str):
        """
        初始化客户端

        Args:
            base_url: AIPEXBASE 服务器地址
        """
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        require_auth: bool = False
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法 (GET/POST/DELETE)
            endpoint: API 端点
            data: 请求数据
            require_auth: 是否需要认证

        Returns:
            响应 JSON 数据

        Raises:
            APIError: 请求失败时抛出异常
        """
        url = f"{self.base_url}{endpoint}"
        headers = {}

        if require_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            result = response.json()

            # 检查业务状态码
            if result.get('code') != 0:
                raise from_api_response(result, endpoint=endpoint)

            return result

        except requests.exceptions.Timeout as e:
            raise from_requests_error(e, endpoint=endpoint)
        except requests.exceptions.ConnectionError as e:
            raise from_requests_error(e, endpoint=endpoint)
        except requests.exceptions.HTTPError as e:
            raise from_requests_error(e, endpoint=endpoint)
        except json.JSONDecodeError as e:
            raise APIError(
                message="服务器返回了无效的 JSON 响应",
                code=ErrorCode.API_INVALID_RESPONSE,
                endpoint=endpoint,
                original_error=e
            )

    def login(self, email: str, password: str) -> str:
        """
        管理员登录

        Args:
            email: 管理员邮箱
            password: 管理员密码

        Returns:
            JWT token
        """
        print(f"{Fore.CYAN}→ 正在登录...")

        data = {
            'email': email,
            'password': password
        }

        result = self._make_request('POST', '/admin/login', data)
        self.token = result.get('data')

        if not self.token:
            raise AuthenticationError(
                "登录失败: 未返回 token",
                code=ErrorCode.AUTH_LOGIN_FAILED,
                context={'email': email}
            )

        print(f"{Fore.GREEN}✓ 登录成功")
        return self.token

    def create_application(self, name: str, description: str = '') -> Dict[str, Any]:
        """
        创建应用

        Args:
            name: 应用名称
            description: 应用描述

        Returns:
            应用信息 (包含 appId)
        """
        print(f"{Fore.CYAN}→ 正在创建应用: {name}")

        data = {
            'name': name,
            'appName': name
        }

        if description:
            data['description'] = description

        result = self._make_request('POST', '/admin/application', data, require_auth=True)
        app_info = result.get('data')

        if not app_info or not app_info.get('appId'):
            raise APIError(
                "创建应用失败: 未返回 appId",
                code=ErrorCode.API_APP_CREATION_FAILED,
                endpoint="/admin/application",
                request_data=data
            )

        print(f"{Fore.GREEN}✓ 应用创建成功")
        print(f"  应用ID: {Fore.YELLOW}{app_info['appId']}")
        print(f"  应用名称: {app_info['appName']}")
        print(f"  状态: {app_info['status']}")

        return app_info

    def create_api_key(
        self,
        app_id: str,
        name: str,
        description: str = '',
        expire_at: str = ''
    ) -> bool:
        """
        创建 API Key

        Args:
            app_id: 应用ID
            name: API Key 名称
            description: API Key 描述
            expire_at: 过期时间 (格式: YYYY-MM-DD HH:mm:ss)

        Returns:
            是否创建成功
        """
        print(f"{Fore.CYAN}→ 正在生成 API Key...")

        data = {
            'name': name,
            'description': description,
            'expireAt': expire_at
        }

        endpoint = f'/admin/application/config/apikeys/{app_id}/save'
        result = self._make_request('POST', endpoint, data, require_auth=True)

        success = result.get('data', False)
        if not success:
            raise APIError(
                "创建 API Key 失败",
                code=ErrorCode.API_REQUEST_FAILED,
                endpoint=endpoint,
                request_data=data,
                context={'app_id': app_id}
            )

        print(f"{Fore.GREEN}✓ API Key 生成成功")
        return True

    def get_api_keys(self, app_id: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        查询 API Key 列表

        Args:
            app_id: 应用ID
            page: 页码
            page_size: 每页数量

        Returns:
            API Key 列表数据
        """
        print(f"{Fore.CYAN}→ 正在查询 API Key 详情...")

        data = {
            'current': page,
            'pageSize': page_size
        }

        endpoint = f'/admin/application/config/apikeys/{app_id}/page'
        result = self._make_request('POST', endpoint, data, require_auth=True)

        return result.get('data', {})

    def create_project_complete(
        self,
        project_name: str,
        description: str = '',
        api_key_name: str = 'MCP 专用密钥',
        api_key_description: str = '用于 MCP 工具调用的 API 密钥',
        api_key_expire: str = '',
        mcp_server_name: str = 'aipexbase-mcp-server',
        verbose: bool = True
    ) -> ProjectCreationResult:
        """
        完整的项目创建流程（一站式方法）

        包含：创建应用 → 生成 API Key → 查询 Key 详情 → 构建 MCP 配置

        Args:
            project_name: 项目名称
            description: 项目描述
            api_key_name: API Key 显示名称
            api_key_description: API Key 描述
            api_key_expire: API Key 过期时间（格式: YYYY-MM-DD HH:mm:ss）
            mcp_server_name: MCP 服务器名称
            verbose: 是否显示详细输出

        Returns:
            ProjectCreationResult: 项目创建结果数据类

        Raises:
            APIError: API 调用失败
            AuthenticationError: 未认证或认证过期

        Example:
            >>> client = AIPEXBASEClient("http://localhost:8080")
            >>> client.login("admin@example.com", "password")
            >>> result = client.create_project_complete("我的项目", "项目描述")
            >>> print(f"Token: {result.api_key}")
        """
        # 检查是否已登录
        if not self.token:
            raise AuthenticationError("未登录，请先调用 login() 方法")

        # 1. 创建应用
        if verbose:
            print()
        app_info = self.create_application(project_name, description)
        app_id = app_info['appId']

        # 2. 生成 API Key
        if verbose:
            print()
        self.create_api_key(
            app_id=app_id,
            name=api_key_name,
            description=api_key_description,
            expire_at=api_key_expire
        )

        # 3. 查询 API Key 详情
        if verbose:
            print()
        api_keys_data = self.get_api_keys(app_id)
        records = api_keys_data.get('records', [])

        if not records:
            raise APIError("未找到生成的 API Key")

        # 获取最新创建的 API Key
        latest_key = records[0]
        key_name = latest_key['keyName']

        if verbose:
            print(f"{Fore.GREEN}✓ API Key 查询成功")
            print(f"  Key 名称: {latest_key['name']}")
            print(f"  Key 值: {Fore.YELLOW}{key_name}")
            print(f"  状态: {latest_key['status']}")
            print(f"  过期时间: {latest_key['expireAt']}")

        # 4. 生成 MCP 配置
        mcp_base_url = get_mcp_base_url(self.base_url)
        mcp_url = f"{mcp_base_url}/mcp/sse?token={key_name}"
        mcp_config = {
            'mcpServers': {
                mcp_server_name: {
                    'url': mcp_url
                }
            }
        }

        # 5. 构建并返回结果
        return ProjectCreationResult(
            app_id=app_id,
            app_name=app_info['appName'],
            api_key=key_name,
            api_key_name=latest_key['name'],
            mcp_url=mcp_url,
            mcp_config=mcp_config,
            app_info=app_info,
            api_key_info=latest_key
        )


def load_env_config() -> Dict[str, Any]:
    """
    从环境变量加载配置

    优先从 .env 文件加载，如果不存在则使用系统环境变量

    Returns:
        配置字典

    Raises:
        ValueError: 缺少必要的环境变量时抛出
    """
    # 尝试加载 .env 文件
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"{Fore.CYAN}→ 已加载 .env 文件")
    else:
        print(f"{Fore.YELLOW}→ 未找到 .env 文件，使用系统环境变量")

    # 读取配置
    config = {
        'server': {
            'base_url': os.getenv('AIPEXBASE_BASE_URL', '')
        },
        'admin': {
            'email': os.getenv('AIPEXBASE_ADMIN_EMAIL', ''),
            'password': os.getenv('AIPEXBASE_ADMIN_PASSWORD', '')
        },
        'api_key': {
            'name': os.getenv('AIPEXBASE_API_KEY_NAME', 'MCP 专用密钥'),
            'description': os.getenv('AIPEXBASE_API_KEY_DESC', '用于 MCP 工具调用的 API 密钥'),
            'expire_at': os.getenv('AIPEXBASE_API_KEY_EXPIRE', '')
        },
        'output': {
            'mcp_config_file': os.getenv('AIPEXBASE_OUTPUT_FILE', 'mcp_config.json'),
            'show_full_response': os.getenv('AIPEXBASE_VERBOSE', 'false').lower() == 'true'
        }
    }

    # 验证必要的配置项
    required_fields = [
        ('server', 'base_url', 'AIPEXBASE_BASE_URL'),
        ('admin', 'email', 'AIPEXBASE_ADMIN_EMAIL'),
        ('admin', 'password', 'AIPEXBASE_ADMIN_PASSWORD')
    ]

    missing_fields = []
    for section, field, env_var in required_fields:
        if not config.get(section, {}).get(field):
            missing_fields.append(env_var)

    if missing_fields:
        raise ValueError(
            f"缺少必要的环境变量: {', '.join(missing_fields)}\n"
            f"请创建 .env 文件或设置环境变量（参考 .env.example）"
        )

    return config


def get_mcp_base_url(base_url: str) -> str:
    """
    从 base_url 中提取 MCP 基础 URL（去掉 /baas-api 等 API 前缀）

    Args:
        base_url: 完整的 API base URL，如 http://host:port/baas-api

    Returns:
        MCP 基础 URL，如 http://host:port
    """
    base_url = base_url.rstrip('/')
    # 去掉 /baas-api 后缀
    if base_url.endswith('/baas-api'):
        return base_url[:-9]
    return base_url


def generate_mcp_config(base_url: str, api_key: str, server_name: str = 'aipexbase-mcp-server') -> Dict[str, Any]:
    """
    生成 MCP 服务器配置

    Args:
        base_url: 服务器地址
        api_key: API Key (keyName)
        server_name: MCP 服务器名称

    Returns:
        MCP 配置字典
    """
    mcp_base_url = get_mcp_base_url(base_url)
    mcp_url = f"{mcp_base_url}/mcp/sse?token={api_key}"

    return {
        'mcpServers': {
            server_name: {
                'url': mcp_url
            }
        }
    }


# ============================================================================
# 便捷 API 函数
# ============================================================================

def create_client_from_env(env_file: Optional[str] = None, auto_login: bool = True) -> AIPEXBASEClient:
    """
    从环境变量创建客户端并自动登录

    优先从 .env 文件加载，如果不存在则使用系统环境变量。

    Args:
        env_file: .env 文件路径（可选，默认为脚本目录下的 .env）
        auto_login: 是否自动登录（默认 True）

    Returns:
        AIPEXBASEClient: 已登录的客户端实例

    Raises:
        ConfigurationError: 缺少必要的环境变量
        AuthenticationError: 登录失败

    Example:
        >>> client = create_client_from_env()
        >>> result = client.create_project_complete("我的项目")
    """
    # 加载环境变量
    if env_file:
        env_path = Path(env_file)
    else:
        env_path = Path(__file__).parent / '.env'

    if env_path.exists():
        load_dotenv(env_path)

    # 读取配置
    base_url = os.getenv('AIPEXBASE_BASE_URL', '')
    email = os.getenv('AIPEXBASE_ADMIN_EMAIL', '')
    password = os.getenv('AIPEXBASE_ADMIN_PASSWORD', '')

    # 验证必要配置
    missing = []
    if not base_url:
        missing.append('AIPEXBASE_BASE_URL')
    if not email:
        missing.append('AIPEXBASE_ADMIN_EMAIL')
    if not password:
        missing.append('AIPEXBASE_ADMIN_PASSWORD')

    if missing:
        raise ConfigurationError(
            f"缺少必要的环境变量: {', '.join(missing)}\n"
            f"请创建 .env 文件或设置环境变量（参考 .env.example）"
        )

    # 创建客户端
    client = AIPEXBASEClient(base_url)

    # 自动登录
    if auto_login:
        try:
            client.login(email, password)
        except Exception as e:
            raise AuthenticationError(f"登录失败: {e}")

    return client


def create_project(
    project_name: str,
    description: str = '',
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ProjectCreationResult:
    """
    便捷函数：快速创建项目

    自动从环境变量创建客户端、登录并创建项目。

    Args:
        project_name: 项目名称
        description: 项目描述
        config: 配置字典（可选，用于覆盖环境变量配置）
        **kwargs: 传递给 create_project_complete 的其他参数

    Returns:
        ProjectCreationResult: 项目创建结果

    Raises:
        ConfigurationError: 配置错误
        AuthenticationError: 认证失败
        APIError: API 调用失败

    Example:
        >>> # 最简单的用法（从 .env 读取配置）
        >>> result = create_project("我的项目", "项目描述")
        >>> print(f"Token: {result.api_key}")

        >>> # 自定义配置
        >>> result = create_project(
        ...     "我的项目",
        ...     api_key_name="生产环境密钥",
        ...     api_key_expire="2025-12-31 23:59:59"
        ... )
    """
    # 创建客户端并登录
    client = create_client_from_env()

    # 从环境变量或配置读取 API Key 配置
    if config is None:
        config = {}

    api_key_config = {
        'api_key_name': kwargs.pop('api_key_name', os.getenv('AIPEXBASE_API_KEY_NAME', 'MCP 专用密钥')),
        'api_key_description': kwargs.pop('api_key_description', os.getenv('AIPEXBASE_API_KEY_DESC', '用于 MCP 工具调用的 API 密钥')),
        'api_key_expire': kwargs.pop('api_key_expire', os.getenv('AIPEXBASE_API_KEY_EXPIRE', '')),
        'mcp_server_name': kwargs.pop('mcp_server_name', 'aipexbase-mcp-server'),
        'verbose': kwargs.pop('verbose', os.getenv('AIPEXBASE_VERBOSE', 'false').lower() == 'true')
    }

    # 创建项目
    return client.create_project_complete(
        project_name=project_name,
        description=description,
        **api_key_config,
        **kwargs
    )


def main():
    """命令行入口（向后兼容）"""
    parser = argparse.ArgumentParser(
        description='AIPEXBASE 项目自动创建脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'project_name',
        nargs='?',
        default=None,
        help='项目名称 (可选，默认: AI项目_时间戳)'
    )
    parser.add_argument(
        'description',
        nargs='?',
        default='',
        help='项目描述 (可选)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出'
    )

    args = parser.parse_args()

    # 生成默认项目名称（如果未提供）
    if not args.project_name:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_name = f"AI项目_{timestamp}"
        print(f"{Fore.YELLOW}→ 未指定项目名称，使用默认值: {project_name}\n")
    else:
        project_name = args.project_name

    description = args.description or ''

    print(f"{Fore.CYAN}{Style.BRIGHT}=== AIPEXBASE 项目自动创建工具 ==={Style.RESET_ALL}\n")

    try:
        # 1. 加载配置
        config = load_env_config()
        print(f"{Fore.GREEN}✓ 配置加载成功\n")

        # 2. 创建客户端并登录（使用新 API）
        client = create_client_from_env()
        print()

        # 3. 创建项目（使用新的高级 API）
        api_key_config = config.get('api_key', {})
        result = client.create_project_complete(
            project_name=project_name,
            description=description,
            api_key_name=api_key_config.get('name', 'MCP 专用密钥'),
            api_key_description=api_key_config.get('description', '用于 MCP 工具调用的 API 密钥'),
            api_key_expire=api_key_config.get('expire_at', ''),
            verbose=True
        )
        print()

        # 4. 保存 MCP 配置文件
        output_config = config.get('output', {})
        output_filename = output_config.get('mcp_config_file', 'mcp_config.json')

        # 确保保存到脚本所在目录
        script_dir = Path(__file__).parent
        output_file = script_dir / output_filename

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.mcp_config, f, indent=2, ensure_ascii=False)

        print(f"{Fore.GREEN}✓ MCP 配置已保存到: {Fore.YELLOW}{output_file}\n")

        # 5. 输出配置内容
        print(f"{Fore.CYAN}{Style.BRIGHT}=== MCP 服务器配置 ==={Style.RESET_ALL}")
        print(json.dumps(result.mcp_config, indent=2, ensure_ascii=False))
        print()

        print(f"{Fore.GREEN}{Style.BRIGHT}✓ 所有操作完成！{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}下一步操作:")
        print(f"  1. 将 {output_file} 中的配置添加到你的 AI IDE 的 MCP 配置中")
        print(f"  2. 重启 AI IDE 以加载 MCP 服务器")
        print(f"  3. 现在你可以使用 MCP 工具操作 AIPEXBASE 了！")

    except ConfigurationError as e:
        print(f"{Fore.RED}✗ 配置错误: {e}")
        sys.exit(1)
    except AuthenticationError as e:
        print(f"{Fore.RED}✗ 认证错误: {e}")
        sys.exit(1)
    except APIError as e:
        print(f"{Fore.RED}✗ API 错误: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"{Fore.RED}✗ 文件错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}✗ 错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
