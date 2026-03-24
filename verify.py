#!/usr/bin/env python3
"""
验证 Skill Certifier v3 安装
检查所有核心组件是否存在
"""

import sys
from pathlib import Path


def verify():
    """验证安装"""

    print("🔍 验证 skill-certifier v3 安装...\n")

    skill_dir = Path(__file__).parent

    checks = {
        # 核心文档
        "SKILL.md":                skill_dir / "SKILL.md",
        # references/
        "配置参考":                 skill_dir / "references" / "config.md",
        "测试案例指南":              skill_dir / "references" / "test-cases.md",
        "执行器指南":                skill_dir / "references" / "executors.md",
        "评审器指南":                skill_dir / "references" / "reviewers.md",
        "安全检查指南":              skill_dir / "references" / "safety-checker.md",
        "报告模板":                 skill_dir / "references" / "report-template.md",
        "故障排查":                 skill_dir / "references" / "troubleshooting.md",
        "CI/CD 指南":               skill_dir / "references" / "ci-cd.md",
        # scripts/
        "安全检查器":                skill_dir / "scripts" / "safety_checker.py",
        "规范检查器":                skill_dir / "scripts" / "spec_checker.py",
        "测试案例生成器":             skill_dir / "scripts" / "smart_test_generator.py",
        "执行协调器":                skill_dir / "scripts" / "parallel_test_runner.py",
        "报告生成器":                skill_dir / "scripts" / "report_builder.py",
        "测试案例校验器":             skill_dir / "scripts" / "test_cases_validator.py",
        "错误分析器":                skill_dir / "scripts" / "error_analyzer.py",
        "进度报告器":                skill_dir / "scripts" / "progress.py",
        "常量定义":                 skill_dir / "scripts" / "constants.py",
    }

    all_good = True

    for name, path in checks.items():
        if path.exists():
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} — 缺失: {path.relative_to(skill_dir)}")
            all_good = False

    print()

    if all_good:
        print("🎉 所有组件验证成功！")
        print("\n你现在可以使用：")
        print("  测试skill ./my-skill/")
        return 0
    else:
        print("⚠️  某些组件缺失，请重新安装。")
        return 1


if __name__ == '__main__':
    sys.exit(verify())
