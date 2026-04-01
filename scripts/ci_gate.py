#!/usr/bin/env python3
"""CI 质量门禁 — 读取报告 JSON 并根据阈值返回 exit code"""
import argparse, json, sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Skill 质量门禁')
    parser.add_argument('report', help='报告 JSON 文件路径')
    parser.add_argument('--min-overall', type=float, default=40.0,
                        help='综合评分最低阈值（默认 40.0）')
    parser.add_argument('--min-dimension', type=float, default=40.0,
                        help='各维度评分最低阈值（默认 40.0）')
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f'❌ 报告文件不存在: {report_path}', file=sys.stderr)
        sys.exit(1)

    data = json.loads(report_path.read_text(encoding='utf-8'))
    overall = data.get('summary', {}).get('overall_score', 0)
    dims = data.get('dimensions', {})

    failed = False
    if overall < args.min_overall:
        print(f'❌ 综合评分 {overall} < {args.min_overall}')
        failed = True

    for dim_key, dim_data in dims.items():
        score = dim_data.get('score', 0)
        if score < args.min_dimension:
            print(f'❌ {dim_key} 得分 {score} < {args.min_dimension}')
            failed = True

    if not failed:
        print(f'✅ 质量门禁通过（综合评分 {overall}）')

    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
