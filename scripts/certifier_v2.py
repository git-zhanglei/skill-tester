#!/usr/bin/env python3
"""
Skill Certifier V2 - 新流程
1. 内置 skill test 验证
2. 生成测试案例集
3. 用户确认
4. 并行执行
5. 生成报告
"""

import argparse
import sys
import os
import json
import signal
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 初始化目录
from constants import init_directories
init_directories()

from constants import (
    VERSION, TEST_CASES_DIR, REPORTS_DIR,
    DEFAULT_PARALLEL, DEFAULT_TIMEOUT, DEFAULT_MAX_CASES
)
from skill_test_runner import SkillTestRunner
from test_case_generator import TestCaseGenerator
from parallel_test_runner import ParallelTestRunner
from report_builder import ReportBuilder
from test_cases_validator import TestCasesValidator


def main():
    parser = argparse.ArgumentParser(
        description='Skill Certifier V2 - 新版测试流程'
    )
    parser.add_argument('skill_path', help='skill 目录路径')
    parser.add_argument('--parallel', '-p', type=int, default=DEFAULT_PARALLEL,
                        help=f'并行测试线程数（默认：{DEFAULT_PARALLEL}）')
    parser.add_argument('--timeout', '-t', type=int, default=DEFAULT_TIMEOUT,
                        help=f'每个测试用例超时时间（默认：{DEFAULT_TIMEOUT}秒）')
    parser.add_argument('--test-cases', '-c', type=str,
                        help='使用已有的测试案例集文件')
    parser.add_argument('--skip-skill-test', action='store_true',
                        help='跳过内置 skill test')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='自动确认，不询问用户（非交互式环境必需）')
    parser.add_argument('--resume', '-r', action='store_true',
                        help='恢复中断的测试（使用 --test-cases 指定）')
    
    args = parser.parse_args()
    
    skill_path = Path(args.skill_path).resolve()
    
    # 设置信号处理
    interrupted = False
    checkpoint_file = None
    
    def signal_handler(signum, frame):
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            print("\n\n⚠️  收到中断信号，正在保存进度...")
            if checkpoint_file and checkpoint_file.exists():
                print(f"💾 进度已保存到: {checkpoint_file}")
                print(f"💡 使用以下命令恢复测试:")
                print(f"   skill-certifier {skill_path} --test-cases {checkpoint_file}")
        sys.exit(130)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if not skill_path.exists():
        print(f"❌ [E001] 错误：skill 路径不存在：{skill_path}", file=sys.stderr)
        print("   帮助: 请检查路径是否正确，或运行 'skill-certifier --help' 查看用法", file=sys.stderr)
        sys.exit(1)
    
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        print(f"❌ [E002] 错误：SKILL.md 不存在于 {skill_path}", file=sys.stderr)
        print("   帮助: 确保 skill 目录包含 SKILL.md 文件", file=sys.stderr)
        sys.exit(1)
    
    if skill_md.stat().st_size == 0:
        print(f"❌ [E002] 错误：SKILL.md 文件为空", file=sys.stderr)
        sys.exit(1)
    
    skill_name = skill_path.name
    
    print("\n" + "=" * 60)
    print(f"🔍 Skill Certifier V2 - 测试 {skill_name}")
    print("=" * 60)
    
    # ============================================================
    # 阶段 0: 内置 Skill Test 验证
    # ============================================================
    if not args.skip_skill_test:
        print("\n📋 阶段 0: 内置 Skill Test 验证")
        print("-" * 60)
        
        skill_test_runner = SkillTestRunner(skill_path)
        skill_test_result = skill_test_runner.run()
        
        print(f"\n✅ 初次扫描完成")
        print(f"   安全状态: {skill_test_result.get('safety', '未知')}")
        print(f"   可用性: {skill_test_result.get('usability', '未知')}")
        print(f"   结构评分: {skill_test_result.get('structure_score', 0)}/100")
        
        # 如果安全测试失败，停止
        if skill_test_result.get('safety') == 'failed':
            print("\n❌ 安全测试失败，停止测试")
            print(f"   问题: {skill_test_result.get('safety_issues', [])}")
            sys.exit(2)
        
        print(f"\n📝 初次扫描结论:")
        print(f"   {skill_test_result.get('summary', '无')}")
    else:
        skill_test_result = {}
        print("\n⏭️  跳过内置 Skill Test")
    
    # ============================================================
    # 阶段 1: 生成测试案例集
    # ============================================================
    print("\n" + "=" * 60)
    print("📋 阶段 1: 生成测试案例集")
    print("=" * 60)
    
    # 检查是否已有测试案例集
    test_cases_file = None
    if args.test_cases:
        test_cases_file = Path(args.test_cases)
        if test_cases_file.exists():
            print(f"\n📁 使用已有测试案例集: {test_cases_file}")
            with open(test_cases_file, 'r', encoding='utf-8') as f:
                test_cases_data = json.load(f)
            
            # 验证测试案例集
            is_valid, error = TestCasesValidator.validate(test_cases_data)
            if not is_valid:
                print(f"❌ 测试案例集验证失败: {error}")
                sys.exit(1)
            
            print("✅ 测试案例集验证通过")
        else:
            print(f"❌ 测试案例集不存在: {test_cases_file}")
            sys.exit(1)
    else:
        # 生成新的测试案例集
        generator = TestCaseGenerator(skill_path)
        test_cases_data = generator.generate(
            skill_test_result=skill_test_result,
            max_cases=20
        )
        
        # 保存到统一的输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)
        test_cases_file = TEST_CASES_DIR / f"{skill_name}-{timestamp}.json"
        
        with open(test_cases_file, 'w', encoding='utf-8') as f:
            json.dump(test_cases_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 测试案例集已生成并保存")
        print(f"   文件: {test_cases_file}")
    
    # 显示测试案例集
    print(f"\n📊 测试案例集概览:")
    print(f"   总计: {test_cases_data.get('total', 0)} 个测试案例")
    
    for dimension, cases in test_cases_data.get('by_dimension', {}).items():
        print(f"   - {dimension}: {len(cases)} 个")
    
    print(f"\n📝 测试案例详情:")
    for i, case in enumerate(test_cases_data.get('cases', [])[:5], 1):  # 显示前5个
        print(f"   {i}. [{case.get('dimension', '未知')}] {case.get('description', '无描述')}")
        print(f"      输入: {case.get('input', '无')[:50]}")
    
    if len(test_cases_data.get('cases', [])) > 5:
        print(f"      ... 还有 {len(test_cases_data['cases']) - 5} 个")
    
    # ============================================================
    # 阶段 2: 用户确认
    # ============================================================
    print("\n" + "=" * 60)
    print("📋 阶段 2: 用户确认")
    print("=" * 60)
    
    print(f"\n⚠️  即将开始执行测试:")
    print(f"   - Skill: {skill_name}")
    print(f"   - 测试案例数: {test_cases_data.get('total', 0)}")
    print(f"   - 并行度: {args.parallel}")
    print(f"   - 超时: {args.timeout}秒/案例")
    print(f"   - 测试案例集文件: {test_cases_file}")
    
    # 用户确认（如果未使用 --yes 参数且是交互式终端）
    is_interactive = sys.stdin.isatty()
    
    if not args.yes and is_interactive:
        print(f"\n❓ 是否开始执行测试？")
        print("   [Y] 是 - 开始执行测试")
        print("   [N] 否 - 退出，稍后可以使用 --test-cases 参数重新执行")
        print("   [S] 显示完整测试案例集")
        
        while True:
            try:
                choice = input("\n请输入选择 [Y/N/S]: ").strip().upper()
                
                if choice == 'Y':
                    print("\n✅ 用户确认，开始执行测试")
                    break
                elif choice == 'N':
                    print(f"\n⏹️  用户取消测试")
                    print(f"💡 稍后可以使用以下命令重新执行:")
                    print(f"   测试skill {skill_path} --test-cases {test_cases_file}")
                    sys.exit(0)
                elif choice == 'S':
                    # 显示完整测试案例集
                    print("\n" + "=" * 60)
                    print("📋 完整测试案例集")
                    print("=" * 60)
                    for i, case in enumerate(test_cases_data.get('cases', []), 1):
                        print(f"\n{i}. [{case.get('dimension', '未知')}] {case.get('description', '无描述')}")
                        print(f"   ID: {case.get('id', '无')}")
                        print(f"   类型: {case.get('type', '无')}")
                        print(f"   输入: {case.get('input', '无')}")
                        print(f"   预期: {case.get('expected', '无')}")
                        print(f"   权重: {case.get('weight', 1.0)}")
                    print("\n" + "=" * 60)
                    print("❓ 是否开始执行测试？")
                    print("   [Y] 是 - 开始执行测试")
                    print("   [N] 否 - 退出")
                else:
                    print("   无效输入，请输入 Y、N 或 S")
            except (KeyboardInterrupt, EOFError):
                print("\n\n⏹️  用户中断")
                sys.exit(0)
    elif not is_interactive and not args.yes:
        # 非交互式环境且未使用 --yes，报错退出
        print("\n❌ 错误：检测到非交互式环境，请使用 --yes 参数显式确认")
        print("   示例: 测试skill {skill_path} --yes")
        sys.exit(1)
    else:
        print("\n✅ 自动确认（--yes 模式），开始执行测试")
    
    # ============================================================
    # 阶段 3: 并行执行测试
    # ============================================================
    print("\n" + "=" * 60)
    print("📋 阶段 3: 并行执行测试")
    print("=" * 60)
    
    runner = ParallelTestRunner(
        skill_path=skill_path,
        test_cases_data=test_cases_data,
        parallel=args.parallel,
        timeout=args.timeout
    )
    
    execution_result = runner.run()
    
    # 更新测试案例集状态
    test_cases_data['execution'] = execution_result
    test_cases_data['completed_at'] = datetime.now().isoformat()
    
    # 保存更新后的测试案例集
    with open(test_cases_file, 'w', encoding='utf-8') as f:
        json.dump(test_cases_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 测试执行完成")
    print(f"   通过: {execution_result.get('passed', 0)}")
    print(f"   失败: {execution_result.get('failed', 0)}")
    print(f"   错误: {execution_result.get('errors', 0)}")
    print(f"   成功率: {execution_result.get('success_rate', 0):.1f}%")
    
    # ============================================================
    # 阶段 4: 生成最终报告
    # ============================================================
    print("\n" + "=" * 60)
    print("📋 阶段 4: 生成最终报告")
    print("=" * 60)
    
    report_builder = ReportBuilder(
        skill_name=skill_name,
        skill_test_result=skill_test_result,
        test_cases_data=test_cases_data,
        execution_result=execution_result
    )
    
    report = report_builder.build()
    
    # 保存报告到统一输出目录
    report_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"{skill_name}-{report_timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已生成")
    print(f"   文件: {report_file}")
    
    # 显示报告摘要
    print(f"\n📊 最终测试结果:")
    print(f"   安全评分: {report_builder.get_safety_rating()}")
    print(f"   触发命中率: {report_builder.get_hit_rate():.1f}%")
    print(f"   任务成功率: {report_builder.get_success_rate():.1f}%")
    print(f"   综合评分: {report_builder.get_overall_score():.1f}/100")
    print(f"   评级: {report_builder.get_rating()}")
    
    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60)
    
    # 退出码
    if report_builder.get_overall_score() >= 60:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()