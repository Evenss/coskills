#!/usr/bin/env python3
"""
记录文稿生成日志到 powermem（供 Reflection Skill 溯源归因）

用法:
    python log_generation.py --profile-id default --platform 小红书 --topic "AI改变写作的5个方式"
    python log_generation.py --list
    python log_generation.py --list --platform Twitter
"""

import sys
import json
import uuid
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "src"))

from _env_bootstrap import bootstrap_env

bootstrap_env()

from powermem import create_memory


def create_log_document(profile_id: str, platform: str, topic: str,
                        profile_version: str = None) -> tuple[str, dict]:
    """
    创建生成日志 metadata

    返回: (generation_id, metadata_dict)
    """
    generation_id = str(uuid.uuid4())[:8]  # 短 ID，方便用户引用
    now = datetime.utcnow().isoformat() + "Z"

    metadata = {
        "log_type": "generation_log",
        "generation_id": generation_id,
        "profile_id": profile_id,
        "profile_version": profile_version,
        "platform": platform,
        "topic": topic,
        "created_at": now,
        # 以下字段由 Reflection Skill 回填
        "performance_data": None,
        "reflection_at": None,
    }
    
    # memory 字段：简单的文本描述
    memory_text = f"生成日志 {generation_id}: 使用 {profile_id} 风格为 {platform} 平台创作《{topic}》"

    return generation_id, memory_text, metadata


def list_generation_logs(memory, platform: str = None, limit: int = 20) -> list:
    """列出生成日志"""
    filters = {"log_type": "generation_log"}
    if platform:
        filters["platform"] = platform
    
    results = memory.get_all(
        user_id="generation_logs",
        filters=filters,
        limit=limit
    )

    logs = []
    for item in results.get("results", []):
        metadata = item.get("metadata", {})
        if metadata.get("log_type") == "generation_log":
            metadata["_memory_id"] = item.get("id")
            logs.append(metadata)

    # 按时间倒序
    logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return logs


def main():
    parser = argparse.ArgumentParser(description="记录文稿生成日志")
    parser.add_argument("--profile-id", help="使用的 Profile ID")
    parser.add_argument("--profile-version", help="Profile 版本号")
    parser.add_argument("--platform", help="发布平台（Twitter、小红书、公众号等）")
    parser.add_argument("--topic", help="本次创作的核心主题（一句话）")
    parser.add_argument("--output", help="输出日志 ID 到 JSON 文件")
    parser.add_argument("--list", action="store_true", help="列出历史生成日志")

    args = parser.parse_args()

    memory = create_memory()

    # 列出历史日志
    if args.list:
        logs = list_generation_logs(memory, platform=args.platform)
        if not logs:
            print("暂无生成日志")
            return

        print(f"\n{'='*80}")
        print(f"{'生成ID':<12} {'平台':<10} {'Profile':<18} {'主题':<30} {'时间'}")
        print(f"{'='*80}")
        for log in logs:
            created_at = log.get("created_at", "")[:16].replace("T", " ")
            print(
                f"{log.get('generation_id', ''):<12} "
                f"{log.get('platform', ''):<10} "
                f"{log.get('profile_id', ''):<18} "
                f"{log.get('topic', '')[:28]:<30} "
                f"{created_at}"
            )
        print(f"{'='*80}")
        print(f"\n共 {len(logs)} 条记录")
        return

    # 记录新日志
    if not args.profile_id or not args.platform or not args.topic:
        print("❌ 记录日志需要提供 --profile-id、--platform 和 --topic", file=sys.stderr)
        sys.exit(1)

    generation_id, memory_text, metadata = create_log_document(
        profile_id=args.profile_id,
        platform=args.platform,
        topic=args.topic,
        profile_version=args.profile_version
    )

    memory.add(memory_text, user_id="generation_logs", metadata=metadata, infer=False)

    result = {
        "success": True,
        "generation_id": generation_id,
        "profile_id": args.profile_id,
        "platform": args.platform,
        "topic": args.topic,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 生成日志已记录", file=sys.stderr)
    print(f"   生成 ID: {generation_id}", file=sys.stderr)
    print(f"   (请将此 ID 告知用户，Reflection Skill 将凭此 ID 追踪效果)", file=sys.stderr)


if __name__ == "__main__":
    main()
