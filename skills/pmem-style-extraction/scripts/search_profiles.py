#!/usr/bin/env python3
"""
搜索 powermem 中的相似 Style Profile 并检测冲突

用法:
    python search_profiles.py --features /path/to/features.json --threshold 0.85
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


def load_features(features_path: str) -> dict:
    """加载特征 JSON 文件"""
    with open(features_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_features_summary(features: dict) -> str:
    """从特征对象创建用于向量搜索的摘要文本"""
    summary_parts = []
    for key, value in features.items():
        summary_parts.append(f"{value}")
    return " ".join(summary_parts)


def detect_semantic_conflict(old_value: str, new_value: str, memory) -> bool:
    """
    使用 LLM 检测两个特征值是否存在语义冲突
    
    注意：这里使用 powermem 的 LLM 集成来判断冲突
    """
    # 简化版本：使用关键词反义检测
    # 实际使用时应调用 LLM API 进行语义判断
    
    # 定义明显的反义词对
    conflict_pairs = [
        ("短句", "长句"),
        ("极简", "排比"),
        ("理性", "煽情"),
        ("克制", "热烈"),
        ("直接", "铺垫"),
        ("严肃", "幽默"),
        ("逻辑", "碎片"),
    ]
    
    for word1, word2 in conflict_pairs:
        if (word1 in old_value and word2 in new_value) or \
           (word2 in old_value and word1 in new_value):
            return True
    
    return False


def analyze_conflicts(new_features: dict, similar_profiles: list, memory) -> dict:
    """
    分析新特征与已有 Profile 的冲突
    
    返回格式:
    {
        "has_conflict": bool,
        "conflicts": [
            {
                "profile_id": "default",
                "profile_name": "默认风格",
                "conflicting_features": [
                    {
                        "feature": "narrative_rhythm",
                        "old_value": "短句为主",
                        "new_value": "长句排比"
                    }
                ]
            }
        ]
    }
    """
    conflicts = []
    
    for profile_data in similar_profiles:
        # 从 metadata 读取 Profile 信息
        metadata = profile_data.get("metadata", {})
        old_features = metadata.get("features", {})
        
        conflicting_features = []
        for feature_key, new_value in new_features.items():
            if feature_key in old_features:
                old_value = old_features[feature_key]
                if detect_semantic_conflict(old_value, new_value, memory):
                    conflicting_features.append({
                        "feature": feature_key,
                        "old_value": old_value,
                        "new_value": new_value
                    })
        
        if conflicting_features:
            conflicts.append({
                "profile_id": metadata.get("profile_id"),
                "profile_name": metadata.get("profile_name"),
                "similarity": profile_data["score"],
                "conflicting_features": conflicting_features
            })
    
    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": conflicts
    }


def main():
    parser = argparse.ArgumentParser(description="搜索相似 Style Profile 并检测冲突")
    parser.add_argument("--features", required=True, help="特征 JSON 文件路径")
    parser.add_argument("--threshold", type=float, default=0.85, help="相似度阈值")
    parser.add_argument("--output", help="输出结果到 JSON 文件（可选）")
    
    args = parser.parse_args()
    
    # 加载特征
    features = load_features(args.features)
    
    # 创建 powermem 实例
    memory = create_memory()
    
    # 生成搜索摘要
    query = create_features_summary(features)
    
    # 搜索相似 Profile
    print(f"🔍 正在搜索相似 Profile...", file=sys.stderr)
    search_results = memory.search(
        query,
        user_id="style_owner",
        filters={"profile_type": "style_profile"},
        limit=10
    )
    
    # 过滤出高相似度的结果
    similar_profiles = [
        item for item in search_results.get("results", [])
        if item["score"] >= args.threshold
    ]
    
    if not similar_profiles:
        result = {
            "similar_profiles_found": False,
            "has_conflict": False,
            "message": "未发现相似的 Style Profile"
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        return
    
    # 分析冲突
    print(f"✅ 发现 {len(similar_profiles)} 个相似 Profile，正在分析冲突...", file=sys.stderr)
    conflict_analysis = analyze_conflicts(features, similar_profiles, memory)
    
    # 组装结果
    result = {
        "similar_profiles_found": True,
        "similar_count": len(similar_profiles),
        "similar_profiles": [
            {
                "profile_id": p.get("metadata", {}).get("profile_id"),
                "profile_name": p.get("metadata", {}).get("profile_name"),
                "similarity": p["score"],
                "source": p.get("metadata", {}).get("source")
            }
            for p in similar_profiles
        ],
        **conflict_analysis
    }
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 输出友好提示
    if conflict_analysis["has_conflict"]:
        print(f"\n⚠️  检测到 {len(conflict_analysis['conflicts'])} 个冲突 Profile，需要人工仲裁", file=sys.stderr)
    else:
        print(f"\n✅ 未检测到冲突，可以安全写入", file=sys.stderr)


if __name__ == "__main__":
    main()
