#!/usr/bin/env python3
"""
列出 powermem 中所有已存储的 Style Profile

用法:
    python list_profiles.py [--format table|json] [--output file.json]
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "src"))

from _env_bootstrap import bootstrap_env

bootstrap_env()

from powermem import create_memory


def get_all_profiles(memory) -> list:
    """获取所有 Style Profile（从 metadata 读取）"""
    # 使用 filters 精确查找
    search_results = memory.get_all(
        user_id="style_owner",
        filters={"profile_type": "style_profile"},
    )
    
    # 从 metadata 提取 Profile
    profiles = []
    for item in search_results.get("results", []):
        metadata = item.get("metadata", {})
        if metadata.get("profile_type") == "style_profile":
            profiles.append({
                "id": item.get("id"),
                "profile": metadata
            })
    
    return profiles


def format_table(profiles: list) -> str:
    """格式化为表格输出"""
    if not profiles:
        return "未找到任何 Style Profile"
    
    # 表头
    lines = []
    lines.append("=" * 100)
    lines.append(f"{'Profile ID':<20} {'Profile Name':<20} {'Version':<10} {'Source':<50}")
    lines.append("=" * 100)
    
    # 表内容
    for item in profiles:
        profile = item["profile"]
        profile_id = profile.get("profile_id", "N/A")
        profile_name = profile.get("profile_name", "N/A")
        version = profile.get("version", "N/A")
        source = profile.get("source", "N/A")
        
        # 截断过长的 source
        if len(source) > 47:
            source = source[:44] + "..."
        
        lines.append(f"{profile_id:<20} {profile_name:<20} {version:<10} {source:<50}")
    
    lines.append("=" * 100)
    lines.append(f"\n共 {len(profiles)} 个 Profile")
    
    return "\n".join(lines)


def format_detailed_table(profiles: list) -> str:
    """格式化为详细表格，包含特征摘要"""
    if not profiles:
        return "未找到任何 Style Profile"
    
    lines = []
    
    for idx, item in enumerate(profiles, 1):
        profile = item["profile"]
        
        lines.append("=" * 100)
        lines.append(f"Profile {idx}: {profile.get('profile_name', 'N/A')}")
        lines.append("=" * 100)
        lines.append(f"  ID:      {profile.get('profile_id', 'N/A')}")
        lines.append(f"  版本:    {profile.get('version', 'N/A')}")
        lines.append(f"  来源:    {profile.get('source', 'N/A')}")
        
        features = profile.get("features", {})
        if features:
            lines.append("\n  特征摘要:")
            for key, value in features.items():
                # 格式化特征键名
                feature_name = key.replace("_", " ").title()
                lines.append(f"    • {feature_name}: {value}")
        
        lines.append("")
    
    lines.append(f"共 {len(profiles)} 个 Profile\n")
    
    return "\n".join(lines)


def format_json(profiles: list) -> str:
    """格式化为 JSON 输出"""
    output = {
        "total_count": len(profiles),
        "profiles": [item["profile"] for item in profiles]
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="列出所有 Style Profile")
    parser.add_argument("--format", choices=["table", "detailed", "json"], 
                       default="table", help="输出格式")
    parser.add_argument("--output", help="输出到文件（仅 JSON 格式）")
    
    args = parser.parse_args()
    
    # 创建 powermem 实例
    print("🔍 正在加载 Style Profiles...", file=sys.stderr)
    memory = create_memory()
    
    # 获取所有 Profile
    profiles = get_all_profiles(memory)
    
    # 格式化输出
    if args.format == "json":
        output = format_json(profiles)
        print(output)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\n✅ 已保存到 {args.output}", file=sys.stderr)
    
    elif args.format == "detailed":
        output = format_detailed_table(profiles)
        print(output)
    
    else:  # table
        output = format_table(profiles)
        print(output)


if __name__ == "__main__":
    main()
