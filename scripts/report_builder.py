#!/usr/bin/env python3
"""
Report Builder - 基于测试案例集生成最终报告
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class ReportBuilder:
    """构建最终测试报告"""
    
    def __init__(self, skill_name: str, skill_test_result: Dict,
                 test_cases_data: Dict, execution_result: Dict):
        self.skill_name = skill_name
        self.skill_test_result = skill_test_result
        self.test_cases_data = test_cases_data
        self.execution_result = execution_result
    
    def build(self) -> str:
        """构建 Markdown 报告"""
        lines = []
        
        # 标题
        lines.append(f"# Skill 测试报告: {self.skill_name}")
        lines.append("")
        lines.append(f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 执行摘要
        lines.append("## 📊 执行摘要")
        lines.append("")
        lines.append(f"| 指标 | 结果 |")
        lines.append(f"|------|------|")
        lines.append(f"| 安全评分 | {self.get_safety_rating()} |")
        lines.append(f"| 触发命中率 | {self.get_hit_rate():.1f}% |")
        lines.append(f"| 任务成功率 | {self.get_success_rate():.1f}% |")
        lines.append(f"| 综合评分 | {self.get_overall_score():.1f}/100 |")
        lines.append(f"| 评级 | {self.get_rating()} |")
        lines.append("")
        
        # 详细结果
        lines.append("## 📋 详细结果")
        lines.append("")
        
        # 按维度分组显示
        by_dimension = {}
        for case in self.test_cases_data.get('cases', []):
            dim = case.get('dimension', 'unknown')
            if dim not in by_dimension:
                by_dimension[dim] = []
            by_dimension[dim].append(case)
        
        for dimension, cases in by_dimension.items():
            lines.append(f"### {self._translate_dimension(dimension)}")
            lines.append("")
            lines.append(f"**总计:** {len(cases)} 个测试案例")
            lines.append("")
            
            # 统计
            completed = sum(1 for c in cases if c.get('status') == 'completed')
            passed = sum(1 for c in cases if c.get('result', {}).get('status') == 'passed')
            rate = (passed / len(cases) * 100) if cases else 0
            
            lines.append(f"- 完成: {completed}/{len(cases)}")
            lines.append(f"- 通过: {passed}")
            lines.append(f"- 通过率: {rate:.1f}%")
            lines.append("")
            
            # 详细列表
            lines.append("| 状态 | 描述 | 输入 | 结果 |")
            lines.append("|------|------|------|------|")
            
            for case in cases:
                result = case.get('result', {})
                status = result.get('status', 'unknown')
                desc = case.get('description', '无描述')[:30]
                input_str = str(case.get('input', ''))[:30]
                
                if status == 'passed':
                    status_icon = '✅'
                elif status == 'failed':
                    status_icon = '❌'
                else:
                    status_icon = '💥'
                
                lines.append(f"| {status_icon} | {desc} | {input_str} | {status} |")
            
            lines.append("")
        
        # 失败详情
        failed_cases = [
            c for c in self.test_cases_data.get('cases', [])
            if c.get('result', {}).get('status') in ['failed', 'error']
        ]
        
        if failed_cases:
            lines.append("## ❌ 失败详情")
            lines.append("")
            
            for case in failed_cases:
                lines.append(f"### {case.get('description', '无描述')}")
                lines.append("")
                lines.append(f"- **输入:** `{case.get('input', '无')}`")
                lines.append(f"- **预期:** {case.get('expected', '无')}")
                
                result = case.get('result', {})
                lines.append(f"- **实际:** {result.get('status', 'unknown')}")
                
                if result.get('error'):
                    lines.append(f"- **错误:** {result['error'][:200]}")
                
                lines.append("")
        
        # 优化建议
        lines.append("## 💡 优化建议")
        lines.append("")
        
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        if not recommendations:
            lines.append("暂无优化建议，继续保持！")
        
        lines.append("")
        
        # 附录：原始数据
        lines.append("## 📎 附录")
        lines.append("")
        lines.append("### 测试元数据")
        lines.append("")
        lines.append(f"- **Skill 名称:** {self.skill_name}")
        lines.append(f"- **测试案例数:** {self.test_cases_data.get('total', 0)}")
        lines.append(f"- **执行时间:** {self.execution_result.get('duration_seconds', 0):.1f} 秒")
        lines.append(f"- **并行度:** {self.execution_result.get('parallel', 4)}")
        lines.append("")
        
        return '\n'.join(lines)
    
    def get_safety_rating(self) -> str:
        """获取安全评级"""
        safety = self.skill_test_result.get('safety', 'unknown')
        
        if safety == 'passed':
            return '✅ 通过'
        elif safety == 'warning':
            warnings = len(self.skill_test_result.get('safety_warnings', []))
            return f'⚠️ 警告 ({warnings} 个)'
        else:
            return '❌ 失败'
    
    def get_hit_rate(self) -> float:
        """获取触发命中率（加权计算）"""
        hit_cases = [
            c for c in self.test_cases_data.get('cases', [])
            if c.get('dimension') == 'hit_rate' and c.get('status') == 'completed'
        ]
        
        if not hit_cases:
            return 0.0
        
        # 加权计算
        total_weight = 0
        passed_weight = 0
        
        for case in hit_cases:
            weight = case.get('weight', 1.0)
            total_weight += weight
            
            result = case.get('result', {})
            if result.get('status') == 'passed':
                passed_weight += weight
        
        return (passed_weight / total_weight * 100) if total_weight > 0 else 0
    
    def get_success_rate(self) -> float:
        """获取任务成功率"""
        return self.execution_result.get('success_rate', 0.0)
    
    def get_overall_score(self) -> float:
        """获取综合评分"""
        # 基于成功率的评分
        success_score = self.get_success_rate()
        
        # 安全评分
        safety = self.skill_test_result.get('safety', 'unknown')
        safety_score = 100 if safety == 'passed' else 70 if safety == 'warning' else 0
        
        # 综合评分（成功率 70% + 安全 30%）
        overall = success_score * 0.7 + safety_score * 0.3
        
        return overall
    
    def get_rating(self) -> str:
        """获取评级"""
        score = self.get_overall_score()
        
        if score >= 80:
            return "⭐⭐⭐⭐⭐ 优秀"
        elif score >= 60:
            return "⭐⭐⭐⭐ 良好"
        elif score >= 40:
            return "⭐⭐⭐ 可接受"
        else:
            return "⭐⭐ 需要改进"
    
    def _translate_dimension(self, dimension: str) -> str:
        """翻译维度名称"""
        translations = {
            'hit_rate': '触发命中率',
            'success_rate': '任务成功率',
            'boundary': '边界测试',
            'exception': '异常处理'
        }
        return translations.get(dimension, dimension)
    
    def _generate_recommendations(self) -> list:
        """生成优化建议"""
        recommendations = []
        
        # 基于成功率
        success_rate = self.get_success_rate()
        if success_rate < 60:
            recommendations.append(f"任务成功率较低 ({success_rate:.1f}%)，建议检查核心功能")
        
        # 基于命中率
        hit_rate = self.get_hit_rate()
        if hit_rate < 80:
            recommendations.append(f"触发命中率较低 ({hit_rate:.1f}%)，建议优化触发词定义")
        
        # 基于安全
        if self.skill_test_result.get('safety') == 'warning':
            recommendations.append("存在安全警告，建议检查并修复")
        
        # 基于失败案例
        failed_cases = [
            c for c in self.test_cases_data.get('cases', [])
            if c.get('result', {}).get('status') == 'failed'
        ]
        if failed_cases:
            recommendations.append(f"有 {len(failed_cases)} 个测试案例失败，建议逐一排查")
        
        return recommendations[:5]  # 最多5条


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: report_builder.py <test-cases-file>")
        sys.exit(1)
    
    test_cases_file = Path(sys.argv[1])
    
    with open(test_cases_file, 'r', encoding='utf-8') as f:
        test_cases_data = json.load(f)
    
    builder = ReportBuilder(
        skill_name=test_cases_data.get('skill_name', 'unknown'),
        skill_test_result={},
        test_cases_data=test_cases_data,
        execution_result=test_cases_data.get('execution', {})
    )
    
    report = builder.build()
    print(report)