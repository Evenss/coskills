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

# 执行环境自举，加载配置
env_file = bootstrap_env()

# 定义必需的配置项
required = {
    "LLM_API_KEY": "LLM API密钥",
    "EMBEDDING_API_KEY": "Embedding API密钥",
}

# 检测缺失的配置项
missing = []
for key, desc in required.items():
    value = os.getenv(key, "")
    if not value or value == "your_api_key_here":
        missing.append((key, desc))

if missing:
    print("⚠️  检测到以下配置项缺失或未设置:\n")
    for key, desc in missing:
        print(f"  - {key}: {desc}")
    print(f"\n📝 共享配置文件位置: {Path(__file__).resolve().parents[2] / 'pmem-config' / 'pmem-key.env'}")
    print("\n请提供这些配置项，或按 Ctrl+C 退出后手动编辑共享配置文件")
    sys.exit(1)

print("✅ 配置检测通过")
sys.exit(0)
