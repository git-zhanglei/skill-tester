#!/usr/bin/env python3
"""
智能测试生成器 - 基于 ML 启发式的高级测试用例生成
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class SmartTestGenerator:
    """基于 skill 分析生成智能测试用例"""
    
    def __init__(self, skill_path: Path, max_cases: int = 20):
        self.skill_path = skill_path
        self.max_cases = max_cases
        self.skill_md = skill_path / 'SKILL.md'
        self.frontmatter = {}
        self.body = ""
        
    def analyze(self) -> Dict[str, Any]:
        """带启发式的深度分析"""
        if not self.skill_md.exists():
            raise FileNotFoundError(f"SKILL.md 未找到于 {self.skill_path}")
        
        content = self.skill_md.read_text(encoding='utf-8')
        
        # 解析 frontmatter 和 body
        self._parse_content(content)
        
        # 分析复杂度
        complexity = self._analyze_complexity()
        
        # 识别风险区域
        risks = self._identify_risks()
        
        return {
            'name': self.frontmatter.get('name', 'unknown'),
            'description': self.frontmatter.get('description', ''),
            'complexity': complexity,
            'risks': risks,
            'recommendations': self._generate_recommendations(complexity, risks)
        }
    
    def _parse_content(self, content: str):
        """解析 frontmatter 和 body"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        self.frontmatter[key.strip()] = value.strip().strip('"\'')
                self.body = parts[2].strip()
        else:
            self.body = content
    
    def _analyze_complexity(self) -> Dict[str, Any]:
        """分析 skill 复杂度"""
        lines = self.body.split('\n')
        
        # 计算指标
        metrics = {
            'total_lines': len(lines),
            'code_blocks': len(re.findall(r'```', self.body)) // 2,
            'headings': len(re.findall(r'^#+ ', self.body, re.MULTILINE)),
            'tables': len(re.findall(r'\|.*\|', self.body)),
            'links': len(re.findall(r'\[.*?\]\(.*?\)', self.body)),
        }
        
        # 复杂度评分
        score = 0
        score += min(metrics['total_lines'] / 100, 5)  # 最多 5 分
        score += metrics['code_blocks'] * 0.5
        score += metrics['headings'] * 0.3
        score += metrics['tables'] * 0.2
        
        level = '简单'
        if score > 10:
            level = '复杂'
        elif score > 5:
            level = '中等'
        
        return {
            'score': round(score, 1),
            'level': level,
            'metrics': metrics
        }
    
    def _identify_risks(self) -> List[Dict[str, Any]]:
        """识别潜在风险区域"""
        risks = []
        
        # 检查 API key
        if re.search(r'api[_-]?key|token|credential', self.body, re.IGNORECASE):
            risks.append({
                'type': '认证',
                'severity': '高',
                'description': '需要 API key 或 token'
            })
        
        # 检查网络调用
        if re.search(r'curl|wget|http|requests', self.body, re.IGNORECASE):
            risks.append({
                'type': '网络',
                'severity': '中',
                'description': '依赖外部网络调用'
            })
        
        # 检查文件操作
        if re.search(r'open\(|read_file|write_file', self.body):
            risks.append({
                'type': '文件系统',
                'severity': '中',
                'description': '涉及文件系统操作'
            })
        
        # 检查复杂触发词
        triggers = self.frontmatter.get('description', '')
        if len(triggers) > 200:
            risks.append({
                'type': '触发词',
                'severity': '低',
                'description': '触发词描述较长，可能影响命中率'
            })
        
        return risks
    
    def _generate_recommendations(self, complexity: Dict, risks: List) -> List[str]:
        """基于分析生成建议"""
        recommendations = []
        
        if complexity['level'] == '复杂':
            recommendations.append("考虑将详细内容拆分到 references/ 目录")
        
        for risk in risks:
            if risk['type'] == '认证':
                recommendations.append("确保测试环境配置了有效的 API key")
            elif risk['type'] == '网络':
                recommendations.append("添加网络错误处理和重试机制")
            elif risk['type'] == '文件系统':
                recommendations.append("使用临时目录进行文件操作测试")
        
        return recommendations
    
    def generate(self) -> List[Dict[str, Any]]:
        """生成智能测试用例"""
        analysis = self.analyze()
        test_cases = []
        
        # 基于风险生成测试
        for risk in analysis['risks']:
            if risk['type'] == '认证':
                test_cases.append({
                    'dimension': 'success_rate',
                    'type': 'exception',
                    'input': '测试不带 API key',
                    'expected': '优雅错误处理',
                    'description': f"风险: {risk['description']}",
                    'priority': '高'
                })
            elif risk['type'] == '网络':
                test_cases.append({
                    'dimension': 'success_rate',
                    'type': 'exception',
                    'input': '网络超时场景',
                    'expected': '超时处理',
                    'description': f"风险: {risk['description']}",
                    'priority': '中'
                })
        
        # 基于复杂度生成测试
        if analysis['complexity']['level'] == '复杂':
            test_cases.append({
                'dimension': 'branch_coverage',
                'type': 'boundary',
                'input': '长输入测试',
                'expected': '正确处理',
                'description': '测试复杂 skill 的边界情况',
                'priority': '中'
            })
        
        return test_cases[:self.max_cases]


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("用法: smart_test_generator.py <skill-path>")
        sys.exit(1)
    
    generator = SmartTestGenerator(Path(sys.argv[1]))
    analysis = generator.analyze()
    test_cases = generator.generate()
    
    print("分析结果:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    print("\n生成的测试用例:")
    print(json.dumps(test_cases, indent=2, ensure_ascii=False))