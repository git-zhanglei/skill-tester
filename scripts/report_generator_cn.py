#!/usr/bin/env python3
"""
Report Generator (Chinese) - Generate comprehensive test reports in Chinese
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class ReportGenerator:
    """Generate test reports in various formats"""
    
    # 中文翻译映射
    TRANSLATIONS = {
        'hit_rate': '触发命中率',
        'success_rate': '任务成功率',
        'branch_coverage': '分支覆盖率',
        'tool_accuracy': '工具调用准确率',
        'error_handling': '错误处理',
        'structure': '结构评审',
        'usefulness': '实用性评审',
        'domain': '领域评审',
        'exact_match': '精确匹配',
        'fuzzy_match': '模糊匹配',
        'negative': '负面测试',
        'normal': '正常场景',
        'exception': '异常处理',
        'boundary': '边界测试',
        'cli_command': 'CLI命令',
        'cli_help': 'CLI帮助',
        'boundary_empty': '空参数边界',
        'faq_question': 'FAQ问题',
        'security_injection': '命令注入防护',
        'security_traversal': '路径遍历防护',
        'security_sql': 'SQL注入防护',
        'passed': '通过',
        'failed': '失败',
        'error': '错误',
        'unknown': '未知',
        'critical': '严重',
        'high': '高',
        'medium': '中',
        'low': '低',
    }
    
    def __init__(self, results: Dict[str, Any], format: str = 'markdown'):
        self.results = results
        self.format = format
        self.skill_name = results.get('skill_name', 'unknown')
        self.phases = results.get('phases', {})
    
    def _t(self, key: str) -> str:
        """Translate key to Chinese"""
        return self.TRANSLATIONS.get(key, key)
    
    def generate(self) -> str:
        """Generate report in specified format"""
        if self.format == 'json':
            return self._generate_json()
        else:
            return self._generate_markdown()
    
    def _generate_json(self) -> str:
        """Generate JSON report"""
        report = {
            'skill_name': self.skill_name,
            'timestamp': datetime.now().isoformat(),
            'summary': self._get_summary(),
            'phases': self.phases
        }
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _generate_markdown(self) -> str:
        """Generate Chinese Markdown report"""
        lines = []
        
        # Header
        lines.extend(self._generate_header())
        lines.append('')
        
        # Executive Summary
        lines.extend(self._generate_executive_summary())
        lines.append('')
        
        # Safety Pre-screen
        if 'safety' in self.phases:
            lines.extend(self._generate_safety_section())
            lines.append('')
        
        # Quantitative Metrics
        if 'testing' in self.phases:
            lines.extend(self._generate_quantitative_section())
            lines.append('')
        
        # Qualitative Assessment
        if 'qualitative' in self.phases:
            lines.extend(self._generate_qualitative_section())
            lines.append('')
        
        # Test Details
        if 'testing' in self.phases:
            lines.extend(self._generate_test_details())
            lines.append('')
        
        # Optimization Suggestions
        lines.extend(self._generate_suggestions())
        lines.append('')
        
        # Conclusion
        lines.extend(self._generate_conclusion())
        lines.append('')
        
        # Footer
        lines.append('---')
        lines.append('')
        lines.append('*报告由 Skill Certifier v1.0.0 生成*')
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Generate report header"""
        score = self._get_overall_score()
        recommendation = self._get_recommendation()
        
        return [
            f'# Skill 测试报告: {self.skill_name}',
            '',
            f'**生成时间:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'**总体评分:** {score:.1f}/100',
            f'**评级建议:** {recommendation}',
        ]
    
    def _generate_executive_summary(self) -> List[str]:
        """Generate executive summary"""
        score = self._get_overall_score()
        
        if score >= 80:
            summary = "该 skill 质量优秀，可以投入生产使用。"
        elif score >= 60:
            summary = "该 skill 质量良好，功能稳定，但仍有改进空间。"
        elif score >= 40:
            summary = "该 skill 基本可用，但需要修复一些问题才能达到生产标准。"
        else:
            summary = "该 skill 需要重大改进才能投入使用。"
        
        lines = [
            '## 1. 执行摘要',
            '',
            summary,
            '',
            '### 关键指标',
            '',
            '| 指标 | 得分 | 状态 |',
            '|------|------|------|',
        ]
        
        lines.append(f'| 总体评分 | {score:.1f}/100 | {"✅" if score >= 60 else "⚠️"} |')
        
        if 'safety' in self.phases:
            safety_passed = self.phases['safety'].get('passed', False)
            lines.append(f'| 安全检测 | {"通过" if safety_passed else "未通过"} | {"✅" if safety_passed else "❌"} |')
        
        if 'testing' in self.phases:
            testing = self.phases['testing']
            dimensions = testing.get('dimensions', {})
            
            for dim_key in ['hit_rate', 'success_rate']:
                if dim_key in dimensions:
                    rate = dimensions[dim_key].get('rate', 0)
                    lines.append(f'| {self._t(dim_key)} | {rate:.1f}% | {"✅" if rate >= 80 else "⚠️"} |')
        
        lines.append('')
        return lines
    
    def _generate_safety_section(self) -> List[str]:
        """Generate safety pre-screen section"""
        safety = self.phases['safety']
        
        lines = [
            '## 2. 安全预检',
            '',
        ]
        
        if safety.get('passed'):
            lines.append('✅ **通过** - 未发现安全问题')
        else:
            lines.append('❌ **未通过** - 发现安全问题')
        
        lines.append('')
        
        warnings = safety.get('warnings', [])
        if warnings:
            lines.append(f'### ⚠️ 警告 ({len(warnings)}个)')
            lines.append('')
            for warning in warnings[:10]:
                if isinstance(warning, dict):
                    lines.append(f'- [{warning.get("file", "unknown")}] {warning.get("message", "")}')
                else:
                    lines.append(f'- {warning}')
            if len(warnings) > 10:
                lines.append(f'- ... 还有 {len(warnings) - 10} 个警告')
            lines.append('')
        
        return lines
    
    def _generate_quantitative_section(self) -> List[str]:
        """Generate quantitative metrics section"""
        testing = self.phases['testing']
        dimensions = testing.get('dimensions', {})
        
        lines = [
            '## 3. 量化指标',
            '',
        ]
        
        metrics = [
            ('hit_rate', '触发命中率', 25),
            ('success_rate', '任务成功率', 30),
            ('branch_coverage', '分支覆盖率', 20),
            ('tool_accuracy', '工具调用准确率', 15),
            ('error_handling', '错误处理', 10),
        ]
        
        for idx, (dim_key, dim_title, weight) in enumerate(metrics, 1):
            if dim_key in dimensions:
                dim_data = dimensions[dim_key]
                lines.append(f'### 3.{idx} {dim_title} (权重: {weight}%)')
                lines.append('')
                
                rate = dim_data.get('rate', 0)
                score = rate * weight / 100
                lines.append(f'**得分:** {score:.1f}/{weight}')
                lines.append('')
                lines.append('| 测试类型 | 总数 | 通过 | 通过率 |')
                lines.append('|----------|------|------|--------|')
                lines.append(f'| 总体 | {dim_data.get("total", 0)} | {dim_data.get("passed", 0)} | {rate:.1f}% |')
                lines.append('')
        
        return lines
    
    def _generate_qualitative_section(self) -> List[str]:
        """Generate qualitative assessment section"""
        lines = [
            '## 4. 质量评估',
            '',
        ]
        
        qualitative = self.phases['qualitative']
        
        reviewers = [
            ('structure', '结构评审', 'SKILL.md 格式、渐进式披露'),
            ('usefulness', '实用性评审', '清晰度、可操作性、示例'),
            ('domain', '领域评审', '技术正确性、最佳实践'),
        ]
        
        for idx, (key, title, desc) in enumerate(reviewers, 1):
            if key in qualitative:
                data = qualitative[key]
                lines.append(f'### 4.{idx} {title}')
                lines.append('')
                lines.append(f'** verdict:** {data.get("verdict", "N/A")}')
                lines.append(f'**得分:** {data.get("score", 0)}/100')
                lines.append('')
                
                findings = data.get('findings', [])
                if findings:
                    lines.append('**发现问题:**')
                    for finding in findings:
                        lines.append(f'- {finding}')
                    lines.append('')
                
                recommendations = data.get('recommendations', [])
                if recommendations:
                    lines.append('**改进建议:**')
                    for rec in recommendations:
                        lines.append(f'- {rec}')
                    lines.append('')
        
        return lines
    
    def _generate_test_details(self) -> List[str]:
        """Generate test details section"""
        lines = [
            '## 5. 测试详情',
            '',
        ]
        
        testing = self.phases['testing']
        results = testing.get('results', [])
        
        # All test cases table
        lines.append('### 5.1 所有测试用例')
        lines.append('')
        lines.append('| 序号 | 测试描述 | 维度 | 类型 | 输入 | 期望 | 状态 | 耗时 |')
        lines.append('|------|----------|------|------|------|------|------|------|')
        
        for idx, test in enumerate(results, 1):
            test_case = test.get('test_case', {})
            desc = test_case.get('description', '未知')[:25]
            dimension = self._t(test_case.get('dimension', '未知'))[:10]
            test_type = self._t(test_case.get('type', '未知'))[:12]
            input_str = test_case.get('input', '')[:20]
            expected = test_case.get('expected', '')[:8]
            status = '✅' if test.get('status') == 'passed' else '❌'
            duration = f"{test.get('duration', 0):.2f}s"
            
            lines.append(f"| {idx} | {desc} | {dimension} | {test_type} | `{input_str}` | {expected} | {status} | {duration} |")
        
        lines.append('')
        lines.append('**图例:** ✅ 通过 | ❌ 失败')
        lines.append('')
        
        # Failed tests detail
        failed_tests = [r for r in results if r.get('status') != 'passed']
        if failed_tests:
            lines.append('### 5.2 失败测试详情')
            lines.append('')
            for test in failed_tests:
                test_case = test.get('test_case', {})
                lines.append(f"**{test_case.get('description', '未知')}")
                lines.append(f"- 测试维度: {self._t(test_case.get('dimension', '未知'))}")
                lines.append(f"- 测试类型: {self._t(test_case.get('type', '未知'))}")
                lines.append(f"- 测试输入: `{test_case.get('input', '')}`")
                lines.append(f"- 期望结果: {test_case.get('expected', '')}")
                lines.append(f"- 实际状态: {self._t(test.get('status', '未知'))}")
                lines.append(f"- 执行耗时: {test.get('duration', 0):.3f}s")
                
                if test.get('error'):
                    lines.append(f"- 错误信息: `{test.get('error')[:200]}`")
                
                if test.get('error_analysis'):
                    analysis = test['error_analysis']
                    lines.append('')
                    lines.append('**错误分析:**')
                    lines.append(f"- 错误类型: {analysis.get('category', '未知')}")
                    lines.append(f"- 严重程度: {self._t(analysis.get('severity', 'medium')).upper()}")
                    lines.append(f"- 处理建议: {analysis.get('suggestion', 'N/A')}")
                    lines.append('')
                    lines.append('**修复步骤:**')
                    for i, step in enumerate(analysis.get('fix_steps', []), 1):
                        lines.append(f"  {i}. {step}")
                    lines.append(f"- 参考文档: {analysis.get('doc_link', 'N/A')}")
                
                lines.append('')
        
        return lines
    
    def _generate_suggestions(self) -> List[str]:
        """Generate optimization suggestions"""
        lines = [
            '## 6. 优化建议',
            '',
        ]
        
        testing = self.phases['testing']
        results = testing.get('results', [])
        failed_tests = [r for r in results if r.get('status') != 'passed']
        
        if failed_tests:
            lines.append('### 高优先级')
            lines.append('')
            for idx, test in enumerate(failed_tests, 1):
                test_case = test.get('test_case', {})
                lines.append(f'{idx}. **测试失败: {test_case.get("description", "未知")}**')
                lines.append(f'   - 影响: 状态为 {test.get("status", "未知")}')
                lines.append(f'   - 建议: 修复实现以处理: {test_case.get("input", "")[:50]}')
                lines.append('')
        
        return lines
    
    def _generate_conclusion(self) -> List[str]:
        """Generate conclusion"""
        score = self._get_overall_score()
        
        if score >= 80:
            conclusion = f"该 skill **{self.skill_name}** 质量优秀，评分为 {score:.1f}/100。可以投入生产使用。"
        elif score >= 60:
            conclusion = f"该 skill **{self.skill_name}** 质量良好，评分为 {score:.1f}/100。功能可用，但建议处理优化建议以提升可靠性。"
        elif score >= 40:
            conclusion = f"该 skill **{self.skill_name}** 基本可用，评分为 {score:.1f}/100。需要修复一些问题才能达到生产标准。"
        else:
            conclusion = f"该 skill **{self.skill_name}** 需要重大改进，评分为 {score:.1f}/100。不建议投入生产使用。"
        
        return [
            '## 7. 结论',
            '',
            conclusion,
            '',
        ]
    
    def _get_overall_score(self) -> float:
        """Get overall score"""
        if 'testing' in self.phases:
            return self.phases['testing'].get('overall_score', 0)
        return 0
    
    def _get_recommendation(self) -> str:
        """Get recommendation text"""
        score = self._get_overall_score()
        
        if score >= 80:
            return '⭐⭐⭐⭐⭐ 优秀 - 可投入生产'
        elif score >= 60:
            return '⭐⭐⭐⭐ 良好 - 建议小幅改进'
        elif score >= 40:
            return '⭐⭐⭐ 可接受 - 需要改进'
        elif score >= 20:
            return '⭐⭐ 需改进 - 不建议生产使用'
        else:
            return '⭐ 不合格 - 需要重大改进'
    
    def _get_summary(self) -> Dict[str, Any]:
        """Get summary for JSON report"""
        return {
            'overall_score': self._get_overall_score(),
            'recommendation': self._get_recommendation(),
            'total_phases': len(self.phases),
            'passed_phases': sum(1 for p in self.phases.values() if p.get('passed', False))
        }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: report_generator.py <results-json-file>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        results = json.load(f)
    
    generator = ReportGenerator(results)
    print(generator.generate())