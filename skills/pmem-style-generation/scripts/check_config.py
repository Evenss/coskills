#!/usr/bin/env python3
"""
配置完整性检测脚本
检测必需的配置项是否已填写，如果缺失则提示 Agent 进行交互式配置
"""

import os
import sys
from pathlib import Path

# 导入 bootstrap 模块
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _env_bootstrap import bootstrap_env

def get_required_config_items():
    """返回必需配置项定义，供其他模块复用。"""
    return {
        "LLM_API_KEY": "LLM API密钥",
        "EMBEDDING_API_KEY": "Embedding API密钥",
    }


def format_required_config_items(items=None):
    """格式化必需配置项为可读字符串。"""
    if items is None:
        items = get_required_config_items()
    return "\n".join(f"  - {key}: {desc}" for key, desc in items.items())


def get_missing_config_items(items=None):
    """返回缺失的配置项列表。"""
    if items is None:
        items = get_required_config_items()
    missing = []
    for key, desc in items.items():
        value = os.getenv(key, "")
        if not value or value == "your_api_key_here":
            missing.append((key, desc))
    return missing


def main():
    # 执行环境自举，加载配置
    bootstrap_env()

    required = get_required_config_items()
    missing = get_missing_config_items(required)

    if missing:
        print("⚠️  检测到以下配置项缺失或未设置:\n")
        print(format_required_config_items(dict(missing)))
        print(f"\n📝 共享配置文件位置: {Path(__file__).resolve().parents[2] / 'pmem-config' / 'pmem-key.env'}")
        print("\n请提供这些配置项，或按 Ctrl+C 退出后手动编辑共享配置文件")
        return 1

    print("✅ 配置检测通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
