#!/usr/bin/env python3
"""
Skill Test Runner - 使用内置的 skill-test 进行初步验证
"""

import json
from pathlib import Path
from typing import Dict, Any

from safety_checker import SafetyChecker
from qualitative_reviewers import ReviewerSuite


class SkillTestRunner:
    """运行内置的 skill test 验证"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
    
    def run(self) -> Dict[str, Any]:
        """运行 skill test 并返回结果"""
        result = {
            'skill_name': self.skill_path.name,
            'timestamp': self._get_timestamp(),
            'safety': 'unknown',
            'safety_issues': [],
            'safety_warnings': [],
            'usability': 'unknown',
            'structure_score': 0,
            'usefulness_score': 0,
            'domain_score': 0,
            'overall_score': 0,
            'summary': '',
            'recommendations': []
        }
        
        # 1. 安全检查
        print("   🔒 运行安全检查...")
        safety_checker = SafetyChecker(self.skill_path)
        safety_result = safety_checker.check()
        
        result['safety'] = safety_result['status']
        result['safety_issues'] = safety_result.get('issues', [])
        result['safety_warnings'] = safety_result.get('warnings', [])
        
        if safety_result['status'] == 'failed':
            result['summary'] = f"安全测试失败：发现 {len(safety_result['issues'])} 个严重问题"
            result['recommendations'].append("修复安全问题后重新测试")
            return result
        
        # 2. 定性评审
        print("   📋 运行定性评审...")
        reviewer_suite = ReviewerSuite(self.skill_path)
        qualitative_result = reviewer_suite.evaluate()
        
        result['structure_score'] = qualitative_result['structure']['score']
        result['usefulness_score'] = qualitative_result['usefulness']['score']
        result['domain_score'] = qualitative_result['domain']['score']
        
        # 计算综合评分
        result['overall_score'] = (
            result['structure_score'] * 0.4 +
            result['usefulness_score'] * 0.4 +
            result['domain_score'] * 0.2
        )
        
        # 确定可用性
        if result['overall_score'] >= 70:
            result['usability'] = 'good'
        elif result['overall_score'] >= 50:
            result['usability'] = 'acceptable'
        else:
            result['usability'] = 'needs_improvement'
        
        # 生成总结
        result['summary'] = self._generate_summary(result)
        
        # 生成建议
        result['recommendations'] = self._generate_recommendations(
            qualitative_result, safety_result
        )
        
        return result
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _generate_summary(self, result: Dict[str, Any]) -> str:
        """生成测试总结"""
        parts = []
        
        # 安全状态
        if result['safety'] == 'passed':
            parts.append("✅ 安全检查通过")
        else:
            parts.append(f"⚠️ 安全检查通过（{len(result['safety_warnings'])} 个警告）")
        
        # 可用性
        if result['usability'] == 'good':
            parts.append("✅ 可用性良好")
        elif result['usability'] == 'acceptable':
            parts.append("⚠️ 可用性可接受")
        else:
            parts.append("❌ 可用性需要改进")
        
        # 综合评分
        parts.append(f"综合评分 {result['overall_score']:.1f}/100")
        
        return "；".join(parts)
    
    def _generate_recommendations(self, qualitative: Dict, safety: Dict) -> list:
        """生成优化建议"""
        recommendations = []
        
        # 安全建议
        if safety.get('warnings'):
            recommendations.append(f"处理 {len(safety['warnings'])} 个安全警告")
        
        # 结构建议
        structure = qualitative['structure']
        if structure['score'] < 70:
            recommendations.extend(structure.get('recommendations', [])[:2])
        
        # 实用性建议
        usefulness = qualitative['usefulness']
        if usefulness['score'] < 70:
            recommendations.extend(usefulness.get('recommendations', [])[:2])
        
        return recommendations[:5]  # 最多5条建议


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: skill_test_runner.py <skill-path>")
        sys.exit(1)
    
    skill_path = Path(sys.argv[1])
    runner = SkillTestRunner(skill_path)
    result = runner.run()
    
    print("\n" + "=" * 50)
    print("Skill Test 结果:")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))