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
        print("参考 .env.example 文件获取配置模板。")
        sys.exit(1)


def save_template_id(template_id: str, alias: str):
    """保存 Template ID 到文件"""
    template_info = f"""# E2B Template 信息
# 此文件由 build_template.py 自动生成

TEMPLATE_ID={template_id}
TEMPLATE_ALIAS={alias}
"""

    # 保存到 .template_id 文件
    with open("../.template_id", "w") as f:
        f.write(template_info)

    print(f"\n✅ Template ID 已保存到 ../.template_id 文件")


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
        # 存储 Template ID (从构建日志中提取)
        captured_template_id = None

        def log_capture(log_entry):
            """捕获构建日志并提取 Template ID"""
            nonlocal captured_template_id
            # 默认日志处理
            default_build_logger()(log_entry)
            # 尝试从日志中提取 Template ID
            if hasattr(log_entry, 'message'):
                msg = log_entry.message
                if 'Template created with ID:' in msg:
                    # 提取 ID，格式: "Template created with ID: xxx, Build ID:"
                    parts = msg.split('Template created with ID:')
                    if len(parts) > 1:
                        id_part = parts[1].split(',')[0].strip()
                        captured_template_id = id_part

        # 执行构建
        Template.build(
            template,
            alias=template_alias,
            cpu_count=cpu_count,
            memory_mb=memory_mb,
            on_build_logs=log_capture  # 使用自定义日志捕获器
        )

        # 显示结果
        print("\n" + "=" * 60)
        print("✅ Template 构建成功！")
        print("=" * 60)
        print(f"\n📦 Template 信息:")
        if captured_template_id:
            print(f"   Template ID: {captured_template_id}")
            print(f"   别名: {template_alias}")

            # 保存 Template ID
            save_template_id(captured_template_id, template_alias)

            # 使用说明
            print(f"\n📝 使用此 Template 创建 Sandbox:")
            print(f"\n   Python 代码:")
            print(f"   ```python")
            print(f"   from e2b import Sandbox")
            print(f"   sandbox = Sandbox(template='{captured_template_id}')")
            print(f"   # 或使用别名")
            print(f"   sandbox = Sandbox(template='{template_alias}')")
            print(f"   ```")

            print(f"\n   命令行:")
            print(f"   ```bash")
            print(f"   e2b sandbox create {captured_template_id}")
            print(f"   ```")
        else:
            print(f"   别名: {template_alias}")
            print(f"   注意: 无法自动提取 Template ID")
            print(f"   请查看上方构建日志或访问 E2B Dashboard")

        return captured_template_id

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Template 构建失败")
        print("=" * 60)
        print(f"\n错误信息: {str(e)}")
        print("\n💡 排查建议:")
        print("   1. 检查 E2B_API_KEY 是否正确")
        print("   2. 检查网络连接是否正常")
        print("   3. 访问 https://e2b.dev/dashboard 查看账户状态")
        sys.exit(1)


if __name__ == "__main__":
    build_template()
