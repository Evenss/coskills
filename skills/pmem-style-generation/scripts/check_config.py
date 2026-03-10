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
        for key in missing:
            print(key)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
