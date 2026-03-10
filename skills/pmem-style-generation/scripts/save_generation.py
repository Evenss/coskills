#!/usr/bin/env python3
"""
保存最终生成文稿到指定路径。

默认命名规则：
    outputs/{profile_id}_{generation_id}_{title}.md

用法:
    python save_generation.py \
      --profile-id xiaohongshu-casual \
      --log-json /tmp/generation_log.json \
      --title "AI 改变写作的 5 个方式" \
      --content-file /tmp/generated_body.md
"""

import re
import json
import argparse
from pathlib import Path


def sanitize_filename_part(text: str, fallback: str) -> str:
    """清洗文件名片段，保留中英文、数字、下划线和短横线。"""
    if not text:
        return fallback

    sanitized = re.sub(r"[^\w\u4e00-\u9fff\- ]+", "", text, flags=re.UNICODE)
    sanitized = re.sub(r"\s+", "_", sanitized).strip("_")
    return sanitized[:80] if sanitized else fallback


def main():
    parser = argparse.ArgumentParser(description="保存最终生成文稿")
    parser.add_argument("--profile-id", required=True, help="使用的 profile_id")
    parser.add_argument("--log-json", required=True, help="log_generation.py 输出的 JSON 文件路径")
    parser.add_argument("--title", required=True, help="文稿标题")
    parser.add_argument("--content-file", required=True, help="正文文件路径")
    parser.add_argument("--output-dir", default="outputs", help="输出目录（默认 outputs）")

    args = parser.parse_args()

    log_path = Path(args.log_json)
    content_path = Path(args.content_file)
    output_dir = Path(args.output_dir)

    if not log_path.exists():
        raise FileNotFoundError(f"日志文件不存在: {log_path}")
    if not content_path.exists():
        raise FileNotFoundError(f"正文文件不存在: {content_path}")

    with open(log_path, "r", encoding="utf-8") as f:
        log_data = json.load(f)

    generation_id = log_data.get("generation_id")
    if not generation_id:
        raise ValueError("日志文件缺少 generation_id 字段")

    profile_part = sanitize_filename_part(args.profile_id, "profile")
    title_part = sanitize_filename_part(args.title, "untitled")
    file_name = f"{profile_part}_{generation_id}_{title_part}.md"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / file_name

    content = content_path.read_text(encoding="utf-8")
    output_path.write_text(content, encoding="utf-8")

    result = {
        "success": True,
        "output_path": str(output_path.resolve()),
        "file_name": file_name,
        "generation_id": generation_id,
        "profile_id": args.profile_id,
        "title": args.title,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
