#!/usr/bin/env python3
"""
从 powermem 拉取指定 Style Profile

用法:
    python fetch_profile.py --profile-id default
    python fetch_profile.py --profile-id emotion-style --output /tmp/active_profile.json
    python fetch_profile.py --list
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "src"))

from _env_bootstrap import bootstrap_env

bootstrap_env()

from powermem import create_memory


def find_profile_by_id(memory, profile_id: str) -> dict | None:
    """按 profile_id 精确查找 Profile（从 metadata 读取）"""
    results = memory.get_all(
        user_id="style_owner",
        filters={
            "profile_type": "style_profile",
            "profile_id": profile_id
        },
        limit=1
    )

    for item in results.get("results", []):
        metadata = item.get("metadata", {})
        if metadata.get("profile_id") == profile_id and \
           metadata.get("profile_type") == "style_profile":
            return metadata

    return None


def list_all_profiles(memory) -> list:
    """列出所有 Style Profile（从 metadata 读取）"""
    results = memory.get_all(
        user_id="style_owner",
        filters={"profile_type": "style_profile"},
    )

    profiles = []
    for item in results.get("results", []):
        metadata = item.get("metadata", {})
        if metadata.get("profile_type") == "style_profile":
            profiles.append(metadata)

    return profiles


def format_profile_for_compiler(profile: dict) -> str:
    """将 Profile 格式化为适合 Compiler Prompt 使用的文本"""
    features = profile.get("features", {})
    lines = [
        f"Profile ID: {profile.get('profile_id')}",
        f"Profile 名称: {profile.get('profile_name')}",
        f"版本: {profile.get('version')}",
        "",
        "## 风格特征",
    ]

    feature_labels = {
        "narrative_rhythm": "叙事节奏",
        "key_phrase_placement": "金句位置",
        "formatting_symbols": "排版符号",
        "punctuation_habits": "标点习惯",
        "paragraph_structure": "段落结构",
        "emotional_tone": "情感基调",
        "rhetorical_devices": "修辞手法",
        "opening_style": "开篇风格",
        "closing_style": "结尾风格",
    }

    for key, label in feature_labels.items():
        value = features.get(key)
        if value:
            lines.append(f"- {label}: {value}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="从 powermem 拉取 Style Profile")
    parser.add_argument("--profile-id", help="Profile ID（留空使用 default）")
    parser.add_argument("--output", help="输出 JSON 文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有可用 Profile")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                        help="输出格式（json=完整数据，text=Compiler 可读格式）")

    args = parser.parse_args()

    memory = create_memory()

    # 列出所有 Profile
    if args.list:
        profiles = list_all_profiles(memory)
        if not profiles:
            print("⚠️  未找到任何 Style Profile，请先运行 style-extraction skill", file=sys.stderr)
            sys.exit(1)

        print("\n可用的 Style Profile：\n")
        for p in profiles:
            print(f"  • [{p.get('profile_id')}] {p.get('profile_name')}  (版本 {p.get('version')})")
        print()
        return

    # 拉取指定 Profile
    profile_id = args.profile_id or "default"
    print(f"🔍 正在拉取 Profile: {profile_id}...", file=sys.stderr)

    profile = find_profile_by_id(memory, profile_id)

    if not profile:
        print(f"❌ 未找到 Profile: {profile_id}", file=sys.stderr)
        print("\n可用的 Profile：", file=sys.stderr)
        profiles = list_all_profiles(memory)
        for p in profiles:
            print(f"  • [{p.get('profile_id')}] {p.get('profile_name')}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ 已找到 Profile: {profile.get('profile_name')}", file=sys.stderr)

    # 格式化输出
    if args.format == "text":
        output_text = format_profile_for_compiler(profile)
        print(output_text)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_text)
    else:
        output_json = json.dumps(profile, ensure_ascii=False, indent=2)
        print(output_json)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)


if __name__ == "__main__":
    main()
