#!/usr/bin/env python3
"""
Skill Certifier - 主入口
Usage: certifier.py <skill-path> [options]
"""

import argparse
import sys
import os
from pathlib import Path

# Add script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from safety_checker import SafetyChecker
from test_generator import TestGenerator
from test_executor import TestExecutor
from report_generator_cn import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Skill Certifier - skill 测试框架'
    )
    parser.add_argument('skill_path', help='skill 目录路径')
    parser.add_argument('--parallel', '-p', type=int, default=4,
                        help='并行测试线程数（默认：4）')
    parser.add_argument('--env', '-e', type=str,
                        help='环境变量（逗号分隔 KEY=VALUE）')
    parser.add_argument('--output', '-o', type=str, default='report.md',
                        help='输出报告文件（默认：report.md）')
    parser.add_argument('--format', '-f', type=str, default='markdown',
                        choices=['markdown', 'json'],
                        help='报告格式（默认：markdown）')
    parser.add_argument('--skip-safety', action='store_true',
                        help='跳过安全预检')
    parser.add_argument('--timeout', '-t', type=int, default=60,
                        help='每个测试用例超时时间，秒（默认：60）')
    parser.add_argument('--max-cases', '-m', type=int, default=10,
                        help='最大测试用例数（默认：10）')
    
    args = parser.parse_args()
    
    skill_path = Path(args.skill_path).resolve()
    
    if not skill_path.exists():
        print(f"错误：skill 路径不存在：{skill_path}", file=sys.stderr)
        sys.exit(1)
    
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        print(f"错误：SKILL.md 不存在于 {skill_path}", file=sys.stderr)
        sys.exit(1)
    
    # 解析环境变量
    env_vars = {}
    if args.env:
        for pair in args.env.split(','):
            if '=' in pair:
                key, value = pair.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    print(f"🔍 测试 skill：{skill_path.name}")
    print(f"   并行度：{args.parallel}")
    print(f"   超时：{args.timeout}秒")
    print(f"   最大用例数：{args.max_cases}")
    print()
    
    results = {
        'skill_name': skill_path.name,
        'skill_path': str(skill_path),
        'phases': {}
    }
    
    # 阶段 1: 安全预检
    if not args.skip_safety:
        print("=" * 50)
        print("阶段 1：安全预检")
        print("=" * 50)
        checker = SafetyChecker(skill_path)
        safety_result = checker.check()
        results['phases']['safety'] = safety_result
        
        if safety_result['status'] == 'failed':
            print("\n❌ 发现严重安全问题！")
            for issue in safety_result['issues']:
                print(f"   - {issue}")
            print("\n⚠️  由于安全问题，测试已停止。")
            sys.exit(2)
        elif safety_result['warnings']:
            print(f"\n⚠️  通过（{len(safety_result['warnings'])} 个警告）")
            for warning in safety_result['warnings'][:5]:  # 只显示前5个
                print(f"   - {warning}")
        else:
            print("\n✅ 通过，未发现安全问题")
        print()
    
    # 阶段 2: 深度分析
    print("=" * 50)
    print("阶段 2：深度分析")
    print("=" * 50)
    generator = TestGenerator(skill_path, max_cases=args.max_cases)
    analysis = generator.analyze()
    test_cases = generator.generate()
    results['phases']['analysis'] = analysis
    results['phases']['test_cases'] = test_cases
    print(f"\n✅ 分析完成")
    print(f"   触发词：{len(analysis.get('triggers', []))} 个")
    print(f"   生成测试用例：{len(test_cases)} 个")
    print()
    
    # 阶段 3: 多维度测试（真实执行）
    print("=" * 50)
    print("阶段 3：多维度测试（真实执行）")
    print("=" * 50)
    print("\n⚠️  注意：真实执行需要 OpenClaw 运行时环境")
    print("   如果未连接 OpenClaw，测试将返回错误\n")
    
    executor = TestExecutor(
        skill_path=skill_path,
        test_cases=test_cases,
        parallel=args.parallel,
        timeout=args.timeout,
        env_vars=env_vars
    )
    test_results = executor.execute()
    results['phases']['testing'] = test_results
    print()
    
    # 阶段 4: 报告生成
    print("=" * 50)
    print("阶段 4：报告生成")
    print("=" * 50)
    report_gen = ReportGenerator(results, format=args.format)
    report = report_gen.generate()
    
    # 写入报告
    output_path = Path(args.output)
    output_path.write_text(report, encoding='utf-8')
    print(f"\n✅ 报告已保存到：{output_path}")
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    # 安全评分
    if not args.skip_safety:
        safety = results['phases']['safety']
        if safety['status'] == 'passed':
            print(f"🔒 安全评分：✅ 通过")
        else:
            print(f"🔒 安全评分：⚠️ 警告 ({len(safety.get('warnings', []))} 个)")
    
    # 测试评分
    testing = results['phases']['testing']
    print(f"🎯 触发命中率：{testing.get('dimensions', {}).get('hit_rate', {}).get('rate', 0):.1f}%")
    print(f"✅ 任务成功率：{testing['success_rate']:.1f}%")
    print(f"📊 综合评分：{testing['overall_score']:.1f}/100")
    
    # 评级
    score = testing['overall_score']
    if score >= 80:
        rating = "⭐⭐⭐⭐⭐ 优秀"
    elif score >= 60:
        rating = "⭐⭐⭐⭐ 良好"
    elif score >= 40:
        rating = "⭐⭐⭐ 可接受"
    else:
        rating = "⭐⭐ 需要改进"
    
    print(f"🏆 评级：{rating}")
    
    # 退出码
    if score >= 60 and (args.skip_safety or results['phases']['safety']['status'] != 'failed'):
        print("\n✅ 测试通过")
        sys.exit(0)
    else:
        print("\n❌ 测试未通过")
        sys.exit(1)


if __name__ == '__main__':
    main()