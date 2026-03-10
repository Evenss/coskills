#!/usr/bin/env python3
"""
交互式收集 Style Profile 元数据
通过命令行参数接收 Agent 收集的元数据并保存
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any


def generate_smart_suggestions(features: Dict[str, Any]) -> Dict[str, str]:
    """根据特征生成智能建议"""
    tone = features.get('emotional_tone', '')
    
    suggestions = {
        '轻松': ('casual-style', '轻松风格'),
        '理性': ('rational-style', '理性风格'),
        '煽情': ('emotion-style', '情绪煽动版'),
        '专业': ('professional-style', '专业风格'),
        '幽默': ('humor-style', '幽默风格'),
    }
    
    for keyword, (profile_id, profile_name) in suggestions.items():
        if keyword in tone:
            return {'id': profile_id, 'name': profile_name}
    
    return {'id': 'default', 'name': '默认风格'}


def get_suggestions_only(features_path: str) -> None:
    """仅获取智能建议（用于 Agent 展示给用户）"""
    try:
        with open(features_path, 'r', encoding='utf-8') as f:
            features = json.load(f)
        suggestions = generate_smart_suggestions(features)
        print(json.dumps(suggestions, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'id': 'default', 'name': '默认风格'}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description='收集 Style Profile 元数据')
    parser.add_argument('--features', type=str, help='特征文件路径（用于生成智能建议）')
    parser.add_argument('--get-suggestions', action='store_true', help='仅获取智能建议（JSON 格式）')
    parser.add_argument('--platforms', type=str, help='平台列表（逗号分隔）')
    parser.add_argument('--tags', type=str, help='标签列表（逗号分隔）')
    parser.add_argument('--tone', type=str, help='总体基调')
    parser.add_argument('--description', type=str, default='', help='简短说明')
    parser.add_argument('--profile-id', type=str, help='Profile ID')
    parser.add_argument('--profile-name', type=str, help='Profile 显示名称')
    parser.add_argument('--output', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    
    # 如果只是获取建议
    if args.get_suggestions:
        if not args.features:
            print('❌ 需要提供 --features 参数', file=sys.stderr)
            sys.exit(1)
        get_suggestions_only(args.features)
        return
    
    # 验证必需参数
    if not all([args.platforms, args.tags, args.tone, args.profile_id, args.profile_name, args.output]):
        parser.print_help()
        sys.exit(1)
    
    # 验证 Profile ID 格式
    if not all(c.islower() or c.isdigit() or c == '-' for c in args.profile_id):
        print('❌ Profile ID 只能使用小写字母、数字和连字符', file=sys.stderr)
        sys.exit(1)
    
    # 构建元数据
    metadata = {
        'profile_id': args.profile_id,
        'profile_name': args.profile_name,
        'tags': [tag.strip() for tag in args.tags.split(',') if tag.strip()],
        'platforms': [p.strip() for p in args.platforms.split(',') if p.strip()],
        'tone': args.tone,
        'description': args.description,
    }
    
    # 显示汇总
    print('\n✅ 元数据收集完成\n')
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    
    # 保存到文件
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f'\n已保存到：{args.output}')


if __name__ == '__main__':
    main()
