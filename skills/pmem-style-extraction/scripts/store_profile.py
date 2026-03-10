#!/usr/bin/env python3
"""
存储 Style Profile 到 powermem

支持三种模式:
- new: 创建新 Profile
- overwrite: 覆盖同名 Profile
- branch: 创建新分支（保留旧 Profile）

用法:
    python store_profile.py --features features.json --mode new --profile-id default --profile-name "默认风格" --source "来源"
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


def load_features(features_path: str) -> dict:
    """加载特征 JSON 文件"""
    with open(features_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_existing_profile(memory, profile_id: str) -> list:
    """查找已存在的 Profile（使用 metadata 精确过滤）"""
    results = memory.search(
        query="",
        user_id="style_owner",
        filters={
            "profile_type": "style_profile",
            "profile_id": profile_id
        },
        limit=10
    )
    
    return results.get("results", [])


def delete_profiles(memory, profile_items: list):
    """删除指定的 Profile 记录"""
    for item in profile_items:
        memory.delete(item["id"], user_id="style_owner")


def create_memory_text(features: dict, profile_name: str, source: str) -> str:
    """生成用于向量搜索的纯文本描述"""
    parts = [f"风格名称：{profile_name}"]
    
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
            parts.append(f"{label}：{value}")
    
    parts.append(f"来源：{source}")
    return "\n".join(parts)


def create_profile_metadata(features: dict, profile_id: str, profile_name: str, 
                           source: str, version: str = "1.0",
                           tags: list = None, platforms: list = None, 
                           tone: str = None, description: str = None) -> dict:
    """创建 Profile metadata"""
    now = datetime.utcnow().isoformat() + "Z"
    
    metadata = {
        "profile_type": "style_profile",
        "profile_id": profile_id,
        "profile_name": profile_name,
        "version": version,
        "source": source,
        "created_at": now,
        "updated_at": now,
        "features": features,
        # 新增匹配字段
        "tags": tags or [],
        "suitable_platforms": platforms or [],
        "tone": tone or "",
        "description": description or ""
    }
    
    return metadata


def increment_version(old_version: str) -> str:
    """递增版本号"""
    try:
        parts = old_version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return f"{major}.{minor + 1}"
    except:
        return "1.1"


def store_new_profile(memory, features: dict, profile_id: str, profile_name: str, 
                     source: str, tags: list = None, platforms: list = None,
                     tone: str = None, description: str = None) -> dict:
    """新建 Profile"""
    # 检查是否已存在
    existing = find_existing_profile(memory, profile_id)
    if existing:
        return {
            "success": False,
            "error": f"Profile ID '{profile_id}' 已存在，请使用 overwrite 或 branch 模式"
        }
    
    # 创建内存文本（向量搜索用）
    memory_text = create_memory_text(features, profile_name, source)
    
    # 创建 metadata（结构化数据）
    metadata = create_profile_metadata(
        features, profile_id, profile_name, source, "1.0",
        tags, platforms, tone, description
    )
    
    # 存储到 powermem
    memory.add(
        memory_text,
        user_id="style_owner",
        agent_id="extraction",
        metadata=metadata,
        infer=False
    )
    
    return {
        "success": True,
        "mode": "new",
        "profile_id": profile_id,
        "profile_name": profile_name,
        "version": "1.0"
    }


def store_overwrite_profile(memory, features: dict, profile_id: str, profile_name: str, 
                           source: str, tags: list = None, platforms: list = None,
                           tone: str = None, description: str = None) -> dict:
    """覆盖已有 Profile"""
    # 查找旧 Profile
    existing = find_existing_profile(memory, profile_id)
    
    if not existing:
        # 如果不存在，直接创建
        return store_new_profile(memory, features, profile_id, profile_name, source,
                                tags, platforms, tone, description)
    
    # 获取旧版本号
    old_metadata = existing[0].get("metadata", {})
    old_version = old_metadata.get("version", "1.0")
    new_version = increment_version(old_version)
    
    # 删除旧 Profile
    delete_profiles(memory, existing)
    
    # 创建内存文本
    memory_text = create_memory_text(features, profile_name, source)
    
    # 创建 metadata
    metadata = create_profile_metadata(
        features, profile_id, profile_name, source, new_version,
        tags, platforms, tone, description
    )
    
    # 存储新版本
    memory.add(
        memory_text,
        user_id="style_owner",
        agent_id="extraction",
        metadata=metadata,
        infer=False
    )
    
    return {
        "success": True,
        "mode": "overwrite",
        "profile_id": profile_id,
        "profile_name": profile_name,
        "old_version": old_version,
        "new_version": new_version,
        "replaced_count": len(existing)
    }


def store_branch_profile(memory, features: dict, profile_id: str, profile_name: str, 
                        source: str, tags: list = None, platforms: list = None,
                        tone: str = None, description: str = None) -> dict:
    """创建分支 Profile（不删除旧的）"""
    # 检查新 ID 是否已存在
    existing = find_existing_profile(memory, profile_id)
    if existing:
        return {
            "success": False,
            "error": f"分支 Profile ID '{profile_id}' 已存在，请使用不同的 profile_id"
        }
    
    # 创建内存文本
    memory_text = create_memory_text(features, profile_name, source)
    
    # 创建 metadata
    metadata = create_profile_metadata(
        features, profile_id, profile_name, source, "1.0",
        tags, platforms, tone, description
    )
    
    # 存储新分支
    memory.add(
        memory_text,
        user_id="style_owner",
        agent_id="extraction",
        metadata=metadata,
        infer=False
    )
    
    return {
        "success": True,
        "mode": "branch",
        "profile_id": profile_id,
        "profile_name": profile_name,
        "version": "1.0"
    }


def main():
    parser = argparse.ArgumentParser(description="存储 Style Profile 到 powermem")
    parser.add_argument("--features", required=True, help="特征 JSON 文件路径")
    parser.add_argument("--mode", required=True, choices=["new", "overwrite", "branch"], 
                       help="存储模式")
    parser.add_argument("--profile-id", required=True, help="Profile ID")
    parser.add_argument("--profile-name", required=True, help="Profile 显示名称")
    parser.add_argument("--source", required=True, help="来源标题或 URL")
    parser.add_argument("--output", help="输出结果到 JSON 文件（可选）")
    
    # 新增元数据参数
    parser.add_argument("--tags", help="风格标签，逗号分隔，如：轻松,口语化")
    parser.add_argument("--platforms", help="适合平台，逗号分隔，如：小红书,Twitter")
    parser.add_argument("--tone", help="总体基调，如：轻松愉快")
    parser.add_argument("--description", help="简短说明")
    
    args = parser.parse_args()
    
    # 加载特征
    features = load_features(args.features)
    
    # 解析元数据
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    platforms = [p.strip() for p in args.platforms.split(",")] if args.platforms else []
    
    # 创建 powermem 实例
    memory = create_memory()
    
    # 根据模式执行存储
    print(f"📝 正在以 {args.mode} 模式存储 Profile...", file=sys.stderr)
    
    if args.mode == "new":
        result = store_new_profile(memory, features, args.profile_id, 
                                  args.profile_name, args.source,
                                  tags, platforms, args.tone, args.description)
    elif args.mode == "overwrite":
        result = store_overwrite_profile(memory, features, args.profile_id, 
                                        args.profile_name, args.source,
                                        tags, platforms, args.tone, args.description)
    elif args.mode == "branch":
        result = store_branch_profile(memory, features, args.profile_id, 
                                     args.profile_name, args.source,
                                     tags, platforms, args.tone, args.description)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 输出友好提示
    if result.get("success"):
        print(f"\n✅ Profile 已成功存储", file=sys.stderr)
        print(f"   ID: {result['profile_id']}", file=sys.stderr)
        print(f"   名称: {result['profile_name']}", file=sys.stderr)
        print(f"   版本: {result['version']}", file=sys.stderr)
    else:
        print(f"\n❌ 存储失败: {result.get('error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
