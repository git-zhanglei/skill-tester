#!/usr/bin/env python3
"""
验证 Skill Certifier 安装
检查所有组件是否正确安装
"""

import sys
from pathlib import Path


def verify():
    """验证安装"""
    
    print("🔍 验证 skill-certifier 安装...\n")
    
    skill_dir = Path(__file__).parent
    
    checks = {
        "SKILL.md": skill_dir / "SKILL.md",
        "_meta.json": skill_dir / "_meta.json",
        "CLI 脚本": skill_dir / "skill-certifier",
        "主 certifier": skill_dir / "scripts" / "certifier.py",
        "安全检查器": skill_dir / "scripts" / "safety_checker.py",
        "测试生成器": skill_dir / "scripts" / "test_generator.py",
        "测试执行器": skill_dir / "scripts" / "test_executor.py",
        "定性评审器": skill_dir / "scripts" / "qualitative_reviewers.py",
        "中文报告生成器": skill_dir / "scripts" / "report_generator_cn.py",
        "报告模板": skill_dir / "references" / "report-template.md",
        "配置参考": skill_dir / "references" / "config.md",
        "测试用例指南": skill_dir / "references" / "test-cases.md",
        "执行器指南": skill_dir / "references" / "executors.md",
        "评审器指南": skill_dir / "references" / "reviewers.md",
        "安全检查指南": skill_dir / "references" / "safety-checker.md",
    }
    
    all_good = True
    
    for name, path in checks.items():
        if path.exists():
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} - 缺失")
            all_good = False
    
    print()
    
    if all_good:
        print("🎉 所有组件验证成功！")
        print("\n你现在可以使用：")
        print("  测试skill ./my-skill/")
        return 0
    else:
        print("⚠️  某些组件缺失。请重新安装。")
        return 1


if __name__ == '__main__':
    sys.exit(verify())