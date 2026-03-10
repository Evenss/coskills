#!/usr/bin/env python3
"""
智能匹配 Style Profile（Human-in-the-loop）
使用混合匹配策略：同义词词典（精确匹配） + Embedding 语义匹配

用法:
    python match_profile.py --intent "写篇小红书，轻松点"
    python match_profile.py --intent "专业的技术文章" --output /tmp/selected_profile.json
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


# ============ 同义词词典 ============
SYNONYM_DICT = {
    "platform": {
        "小红书": ["xhs", "xiaohongshu", "小红薯", "redbook", "red book"],
        "微信公众号": ["公众号", "微信", "wechat", "weixin", "wx"],
        "推特": ["twitter", "x", "x.com", "tweet"],
        "知乎": ["zhihu"],
        "微博": ["weibo"],
        "抖音": ["douyin", "tiktok"],
        "b站": ["bilibili", "哔哩哔哩", "B站"]
    },
    "style_tags": {
        "幽默": ["有趣", "风趣", "搞笑", "诙谐", "好玩", "逗趣"],
        "专业": ["严谨", "正式", "学术", "权威", "专家"],
        "轻松": ["随意", "休闲", "轻快", "活泼", "轻盈", "放松"],
        "简洁": ["简练", "简明", "精炼", "凝练"],
        "详细": ["详尽", "细致", "深入", "全面", "完整"],
        "生动": ["形象", "鲜活", "活灵活现", "栩栩如生"],
        "理性": ["客观", "冷静", "中立", "克制"],
        "感性": ["情感", "温暖", "动情", "煽情", "抒情"],
        "文艺": ["文学", "诗意", "雅致", "优美"],
        "口语": ["白话", "大白话", "说人话", "接地气"]
    },
    "tone": {
        "激情": ["热情", "热烈", "澎湃", "激昂"],
        "平和": ["温和", "淡定", "平静", "沉稳"],
        "犀利": ["尖锐", "辛辣", "锋利", "直接"],
        "温柔": ["柔和", "温暖", "体贴"]
    }
}


def normalize_term(text: str, category: str = "all") -> set:
    """
    规范化词语，返回所有可能的同义词集合
    
    Args:
        text: 要规范化的文本
        category: 词典类别 ("platform", "style_tags", "tone", "all")
    
    Returns:
        包含原词和所有同义词的集合（小写）
    """
    text_lower = text.lower()
    synonyms = {text_lower}
    
    # 确定要搜索的类别
    categories = [category] if category != "all" else SYNONYM_DICT.keys()
    
    for cat in categories:
        for canonical, variants in SYNONYM_DICT.get(cat, {}).items():
            # 检查文本是否包含规范词或任一同义词
            all_variants = [canonical.lower()] + [v.lower() for v in variants]
            if any(variant in text_lower or text_lower in variant for variant in all_variants):
                synonyms.add(canonical.lower())
                synonyms.update([v.lower() for v in variants])
    
    return synonyms


def list_all_profiles(memory) -> list:
    """获取所有 Profile"""
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


def match_profiles(user_intent: str, all_profiles: list, memory) -> list:
    """
    混合匹配 Profile：同义词规则匹配 + Embedding 语义匹配
    
    Args:
        user_intent: 用户意图描述
        all_profiles: 所有可用的 Profile 列表
        memory: powermem 实例
    
    Returns:
        按分数排序的匹配结果列表
    """
    intent_lower = user_intent.lower()
    
    # ========== 第一步：规则匹配（高权重） ==========
    rule_matches = {}
    
    for profile in all_profiles:
        profile_id = profile.get("profile_id", "")
        score = 0
        reasons = []
        
        # 1. 平台匹配（权重 10，使用同义词）
        platforms = profile.get("suitable_platforms", [])
        for platform in platforms:
            platform_synonyms = normalize_term(platform, "platform")
            if any(syn in intent_lower for syn in platform_synonyms):
                score += 10
                reasons.append(f"适合{platform}平台")
                break  # 避免重复计分
        
        # 2. 标签匹配（权重 5，使用同义词）
        tags = profile.get("tags", [])
        matched_tags = []
        for tag in tags:
            tag_synonyms = normalize_term(tag, "style_tags")
            if any(syn in intent_lower for syn in tag_synonyms):
                score += 5
                matched_tags.append(tag)
        if matched_tags:
            reasons.append(f"风格特点：{', '.join(matched_tags)}")
        
        # 3. 基调匹配（权重 3，使用同义词）
        tone = profile.get("tone", "")
        if tone:
            tone_synonyms = normalize_term(tone, "tone")
            if any(syn in intent_lower for syn in tone_synonyms):
                score += 3
                reasons.append(f"基调：{tone}")
        
        # 4. 名称模糊匹配（权重 2）
        profile_name = profile.get("profile_name", "")
        if any(word in profile_name for word in user_intent.split()):
            score += 2
            reasons.append("名称匹配")
        
        # 5. profile_id 精确匹配（权重 15）
        if profile_id in intent_lower:
            score += 15
            reasons.append("ID匹配")
        
        rule_matches[profile_id] = {
            "profile": profile,
            "rule_score": score,
            "reasons": reasons
        }
    
    # ========== 第二步：语义匹配（使用 powermem 向量搜索） ==========
    try:
        semantic_results = memory.search(
            query=user_intent,
            user_id="style_owner",
            filters={"profile_type": "style_profile"},
            limit=len(all_profiles)
        )
        
        semantic_scores = {}
        for item in semantic_results.get("results", []):
            metadata = item.get("metadata", {})
            profile_id = metadata.get("profile_id", "")
            if profile_id:
                # 向量相似度转换为分数（权重系数 3）
                similarity = item.get("score", 0)
                semantic_scores[profile_id] = similarity * 3
    
    except Exception as e:
        print(f"⚠️  语义匹配失败（将仅使用规则匹配）: {e}", file=sys.stderr)
        semantic_scores = {}
    
    # ========== 第三步：合并评分 ==========
    final_matches = []
    
    for profile_id, rule_data in rule_matches.items():
        total_score = rule_data["rule_score"]
        reasons = rule_data["reasons"].copy()
        
        # 加上语义分数
        if profile_id in semantic_scores:
            semantic_score = semantic_scores[profile_id]
            total_score += semantic_score
            if semantic_score > 0.5:  # 只显示有意义的语义匹配
                reasons.append(f"语义相似度 {semantic_score/3:.2f}")
        
        final_matches.append({
            "profile": rule_data["profile"],
            "score": total_score,
            "reasons": reasons if reasons else ["语义匹配"]
        })
    
    # 按总分排序
    final_matches.sort(key=lambda x: x["score"], reverse=True)
    return final_matches


def interactive_select(matches: list, all_profiles: list) -> dict:
    """交互式选择"""
    if matches and matches[0]["score"] > 0:
        print("\n🎯 根据您的需求，推荐以下风格：\n")
        display_list = matches[:5]
    else:
        print("\n⚠️  未找到精确匹配，以下是所有可用风格：\n")
        display_list = matches[:10] if matches else []
    
    for i, match in enumerate(display_list, 1):
        profile = match["profile"]
        print(f"{i}. [{profile['profile_id']}] {profile['profile_name']}")
        if match["reasons"]:
            print(f"   匹配原因：{', '.join(match['reasons'])}")
        if profile.get("description"):
            print(f"   说明：{profile['description']}")
        if profile.get("tags"):
            print(f"   标签：{', '.join(profile['tags'])}")
        if profile.get("suitable_platforms"):
            print(f"   平台：{', '.join(profile['suitable_platforms'])}")
        print()
    
    print("请选择要使用的风格（输入序号），或输入 0 退出：")
    choice = input("> ").strip()
    
    try:
        idx = int(choice)
        if idx == 0:
            return None
        idx -= 1
        
        if 0 <= idx < len(display_list):
            return display_list[idx]["profile"]
        else:
            print("❌ 无效选择")
            return None
    except (ValueError, IndexError):
        print("❌ 无效输入")
        return None


def main():
    parser = argparse.ArgumentParser(description="智能匹配 Style Profile")
    parser.add_argument("--intent", required=True, help="用户意图描述")
    parser.add_argument("--output", help="输出选定的 Profile 到 JSON 文件")
    parser.add_argument("--non-interactive", action="store_true", 
                       help="非交互模式，直接返回最匹配的")
    
    args = parser.parse_args()
    
    memory = create_memory()
    
    # 获取所有 Profile
    all_profiles = list_all_profiles(memory)
    
    if not all_profiles:
        print("❌ 您还没有创建任何风格 Profile，请先运行 style-extraction", file=sys.stderr)
        sys.exit(1)
    
    # 智能匹配（传入 memory 实例用于语义搜索）
    matches = match_profiles(args.intent, all_profiles, memory)
    
    # 选择 Profile
    if args.non_interactive:
        selected = matches[0]["profile"] if matches else all_profiles[0]
        print(f"自动选择：[{selected['profile_id']}] {selected['profile_name']}", file=sys.stderr)
    else:
        selected = interactive_select(matches, all_profiles)
        if not selected:
            print("已取消", file=sys.stderr)
            sys.exit(0)
    
    # 输出结果
    result = {
        "success": True,
        "profile_id": selected["profile_id"],
        "profile_name": selected["profile_name"],
        "profile": selected
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已选择：[{selected['profile_id']}] {selected['profile_name']}", file=sys.stderr)


if __name__ == "__main__":
    main()
