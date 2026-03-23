#!/usr/bin/env python3
"""
Test Case Generator - 基于 skill 分析生成测试案例集
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from constants import TestStatus, VERSION


class TestCaseGenerator:
    """生成针对不同维度的测试案例集"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.skill_md = skill_path / 'SKILL.md'
        self.frontmatter = {}
        self.body = ""
        self.triggers = []
        self._case_counter = 0  # 用于生成唯一 ID
    
    def _generate_case_id(self, prefix: str) -> str:
        """生成唯一的案例 ID"""
        self._case_counter += 1
        return f"{prefix}_{self._case_counter}"
    
    def generate(self, skill_test_result: Dict = None, max_cases: int = 20) -> Dict[str, Any]:
        """生成测试案例集"""
        # 解析 SKILL.md
        self._parse_skill_md()
        
        # 提取触发词
        self.triggers = self._extract_triggers()
        
        # 生成各类测试案例
        cases = []
        
        # 1. 命中率测试
        hit_cases = self._generate_hit_rate_cases()
        cases.extend(hit_cases)
        
        # 2. 成功率测试
        success_cases = self._generate_success_rate_cases()
        cases.extend(success_cases)
        
        # 3. 边界测试
        boundary_cases = self._generate_boundary_cases()
        cases.extend(boundary_cases)
        
        # 4. 异常测试
        exception_cases = self._generate_exception_cases()
        cases.extend(exception_cases)
        
        # 限制数量
        cases = cases[:max_cases]
        
        # 按维度分组
        by_dimension = {}
        for case in cases:
            dim = case.get('dimension', 'unknown')
            if dim not in by_dimension:
                by_dimension[dim] = []
            by_dimension[dim].append(case)
        
        # 构建测试案例集
        test_cases_data = {
            'version': VERSION,
            'generated_at': datetime.now().isoformat(),
            'skill_name': self.skill_path.name,
            'skill_path': str(self.skill_path),
            'total': len(cases),
            'cases': cases,
            'by_dimension': by_dimension,
            'metadata': {
                'triggers_found': len(self.triggers),
                'triggers': self.triggers[:10],  # 前10个
                'skill_test_score': skill_test_result.get('overall_score', 0) if skill_test_result else 0
            },
            'execution': {
                'status': TestStatus.PENDING,  # pending, running, completed
                'started_at': None,
                'completed_at': None,
                'progress': {
                    'total': len(cases),
                    'completed': 0,
                    'passed': 0,
                    'failed': 0,
                    'errors': 0
                }
            }
        }
        
        return test_cases_data
    
    def _parse_skill_md(self):
        """解析 SKILL.md"""
        if not self.skill_md.exists():
            return
        
        content = self.skill_md.read_text(encoding='utf-8')
        
        # 解析 frontmatter
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
    
    def _extract_triggers(self) -> List[str]:
        """提取触发词"""
        triggers = []
        
        # 从 description 提取
        desc = self.frontmatter.get('description', '')
        
        # 查找引号中的短语
        quoted = re.findall(r'["\']([^"\']{2,30})["\']', desc)
        triggers.extend(quoted)
        
        # 查找中文触发词模式
        chinese_patterns = [
            r'触发词[：:]\s*["\']?([^"\']+)["\']?',
            r'用于[：:]\s*["\']?([^"\']+)["\']?',
        ]
        for pattern in chinese_patterns:
            matches = re.findall(pattern, desc)
            triggers.extend(matches)
        
        # 清理去重
        triggers = list(set([t.strip() for t in triggers if len(t.strip()) >= 2]))
        return triggers[:10]  # 最多10个
    
    def _generate_hit_rate_cases(self) -> List[Dict]:
        """生成命中率测试案例"""
        cases = []
        
        for trigger in self.triggers[:5]:  # 前5个触发词
            # 精确匹配
            cases.append({
                'id': self._generate_case_id('hit_exact'),
                'dimension': 'hit_rate',
                'type': 'exact_match',
                'input': trigger,
                'expected': 'activate',
                'description': f'精确触发: {trigger}',
                'weight': 1.0,
                'status': TestStatus.PENDING,
                'result': None
            })
            
            # 模糊匹配（添加上下文）
            cases.append({
                'id': self._generate_case_id('hit_fuzzy'),
                'dimension': 'hit_rate',
                'type': 'fuzzy_match',
                'input': f'请帮我{trigger}',
                'expected': 'activate',
                'description': f'模糊触发: 请帮我{trigger}',
                'weight': 0.8,
                'status': TestStatus.PENDING,
                'result': None
            })
        
        # 负面测试
        cases.append({
            'id': self._generate_case_id('hit_negative'),
            'dimension': 'hit_rate',
            'type': 'negative',
            'input': '今天天气怎么样',
            'expected': 'not_activate',
            'description': '负面测试: 无关输入不应触发',
            'weight': 0.5,
            'status': TestStatus.PENDING,
            'result': None
        })
        
        return cases
    
    def _generate_success_rate_cases(self) -> List[Dict]:
        """生成成功率测试案例"""
        cases = []
        
        # 正常场景
        if self.triggers:
            cases.append({
                'id': self._generate_case_id('success_normal'),
                'dimension': 'success_rate',
                'type': 'normal',
                'input': self.triggers[0],
                'expected': 'success',
                'description': '正常场景: 标准用法',
                'weight': 1.0,
                'status': TestStatus.PENDING,
                'result': None
            })
        
        # 带参数
        cases.append({
            'id': self._generate_case_id('success_with_args'),
            'dimension': 'success_rate',
            'type': 'with_args',
            'input': f'{self.triggers[0] if self.triggers else "测试"} ./my-skill/',
            'expected': 'success',
            'description': '带参数: 标准参数用法',
            'weight': 0.9,
            'status': TestStatus.PENDING,
            'result': None
        })
        
        return cases
    
    def _generate_boundary_cases(self) -> List[Dict]:
        """生成边界测试案例"""
        cases = []
        
        # 空输入
        cases.append({
            'id': self._generate_case_id('boundary_empty'),
            'dimension': 'boundary',
            'type': 'empty_input',
            'input': '',
            'expected': 'graceful_handling',
            'description': '边界: 空输入处理',
            'weight': 0.6,
            'status': TestStatus.PENDING,
            'result': None
        })
        
        # 超长输入
        cases.append({
            'id': self._generate_case_id('boundary_long'),
            'dimension': 'boundary',
            'type': 'long_input',
            'input': '测试' * 100,
            'expected': 'graceful_handling',
            'description': '边界: 超长输入处理',
            'weight': 0.6,
            'status': TestStatus.PENDING,
            'result': None
        })
        
        return cases
    
    def _generate_exception_cases(self) -> List[Dict]:
        """生成异常测试案例"""
        cases = []
        
        # 无效路径
        cases.append({
            'id': self._generate_case_id('exception_invalid_path'),
            'dimension': 'exception',
            'type': 'invalid_path',
            'input': f'{self.triggers[0] if self.triggers else "测试"} /不存在的路径/',
            'expected': 'error_handled',
            'description': '异常: 无效路径处理',
            'weight': 0.7,
            'status': TestStatus.PENDING,
            'result': None
        })
        
        return cases


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: test_case_generator.py <skill-path>")
        sys.exit(1)
    
    skill_path = Path(sys.argv[1])
    generator = TestCaseGenerator(skill_path)
    result = generator.generate()
    
    print(json.dumps(result, ensure_ascii=False, indent=2))