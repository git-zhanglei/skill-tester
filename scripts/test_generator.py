#!/usr/bin/env python3
"""
测试生成器 - 分析 SKILL.md 并生成测试用例
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


class TestGenerator:
    """基于 skill 分析生成测试用例"""
    
    def __init__(self, skill_path: Path, max_cases: int = 20):
        self.skill_path = skill_path
        self.max_cases = max_cases
        self.skill_md = skill_path / 'SKILL.md'
        self.frontmatter = {}
        self.body = ""
        self.triggers = []
        self.tools = []
        self.workflows = []
    
    def analyze(self) -> Dict[str, Any]:
        """深度分析 SKILL.md"""
        if not self.skill_md.exists():
            raise FileNotFoundError(f"SKILL.md 未找到于 {self.skill_path}")
        
        content = self.skill_md.read_text(encoding='utf-8')
        
        # 解析 frontmatter
        self._parse_frontmatter(content)
        
        # 解析 body
        self.body = self._extract_body(content)
        
        # 提取触发词
        self.triggers = self._extract_triggers()
        
        # 提取工具
        self.tools = self._extract_tools()
        
        # 提取工作流
        self.workflows = self._extract_workflows()
        
        return {
            'name': self.frontmatter.get('name', 'unknown'),
            'description': self.frontmatter.get('description', ''),
            'triggers': self.triggers,
            'tools': self.tools,
            'workflows': self.workflows,
            'has_references': (self.skill_path / 'references').exists(),
            'has_scripts': (self.skill_path / 'scripts').exists(),
        }
    
    def generate(self) -> List[Dict[str, Any]]:
        """基于分析生成测试用例"""
        test_cases = []
        
        # 触发命中率测试
        trigger_tests = self._generate_trigger_tests()
        test_cases.extend(trigger_tests)
        
        # 成功率测试
        success_tests = self._generate_success_tests()
        test_cases.extend(success_tests)
        
        # 分支覆盖测试
        branch_tests = self._generate_branch_tests()
        test_cases.extend(branch_tests)
        
        # 工具准确度测试
        tool_tests = self._generate_tool_tests()
        test_cases.extend(tool_tests)
        
        # 限制测试用例数量
        return test_cases[:self.max_cases]
    
    def _parse_frontmatter(self, content: str):
        """解析 YAML frontmatter"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                if yaml:
                    try:
                        self.frontmatter = yaml.safe_load(parts[1]) or {}
                    except Exception:
                        self._parse_frontmatter_manual(parts[1])
                else:
                    self._parse_frontmatter_manual(parts[1])
    
    def _parse_frontmatter_manual(self, text: str):
        """yaml 不可用时手动解析 frontmatter"""
        for line in text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                self.frontmatter[key.strip()] = value.strip().strip('"\'')
    
    def _extract_body(self, content: str) -> str:
        """提取 body 内容（frontmatter 之后）"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content
    
    def _extract_triggers(self) -> List[str]:
        """从 description 和 body 提取触发词"""
        triggers = []
        
        # 从 description 提取
        desc = self.frontmatter.get('description', '')
        
        # 查找显式触发词列表
        trigger_patterns = [
            r"triggers?\s+on\s*:?\s*['\"]?([^'\"]+)['\"]?",
            r"触发词\s*:?\s*['\"]?([^'\"]+)['\"]?",
            r"用于\s*:?\s*['\"]?([^'\"]+)['\"]?",
        ]
        
        for pattern in trigger_patterns:
            matches = re.findall(pattern, desc, re.IGNORECASE)
            triggers.extend(matches)
        
        # 查找引号中的短语
        quoted = re.findall(r'["\']([^"\']{3,30})["\']', desc)
        triggers.extend(quoted)
        
        # 清理并去重
        triggers = [t.strip().strip("'\"") for t in triggers if len(t.strip()) > 2]
        return list(set(triggers))[:10]  # 最多 10 个
    
    def _extract_tools(self) -> List[str]:
        """从 body 提取工具引用"""
        tools = []
        
        # 查找工具模式
        tool_patterns = [
            r'`(\w+)`\s+tool',
            r'(sessions_spawn|message|exec|web_search)',
            r'(npm|pip|brew|apt)\s+(install|run)',
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, self.body)
            tools.extend(matches)
        
        return list(set(tools))[:10]
    
    def _extract_workflows(self) -> List[str]:
        """从 body 提取工作流步骤"""
        workflows = []
        
        # 查找编号列表
        steps = re.findall(r'^\d+\.\s+(.+)$', self.body, re.MULTILINE)
        workflows.extend(steps[:5])  # 最多 5 步
        
        return workflows
    
    def _generate_trigger_tests(self) -> List[Dict[str, Any]]:
        """生成触发命中率测试"""
        tests = []
        
        for trigger in self.triggers[:5]:  # 最多 5 个触发词
            # 精确匹配
            tests.append({
                'dimension': 'hit_rate',
                'type': 'exact_match',
                'input': trigger,
                'expected': 'activate',
                'description': f'精确触发: {trigger}',
                'weight': 1.0
            })
            
            # 模糊匹配（添加上下文）
            tests.append({
                'dimension': 'hit_rate',
                'type': 'fuzzy_match',
                'input': f'请帮我{trigger}',
                'expected': 'activate',
                'description': f'模糊触发: 请帮我{trigger}',
                'weight': 0.8
            })
        
        # 负面测试（不应触发）
        tests.append({
            'dimension': 'hit_rate',
            'type': 'negative',
            'input': '今天天气怎么样',
            'expected': 'not_activate',
            'description': '负面测试: 无关输入',
            'weight': 0.5
        })
        
        return tests
    
    def _generate_success_tests(self) -> List[Dict[str, Any]]:
        """生成成功率测试"""
        tests = []
        
        # 正常路径
        if self.triggers:
            tests.append({
                'dimension': 'success_rate',
                'type': 'normal',
                'input': self.triggers[0],
                'expected': 'success',
                'description': '正常路径: 标准用法',
                'weight': 1.0
            })
        
        # 异常处理
        tests.append({
            'dimension': 'success_rate',
            'type': 'exception',
            'input': '测试skill /不存在的路径/',
            'expected': 'error_handled',
            'description': '异常: 无效路径',
            'weight': 0.8
        })
        
        # 边界情况
        tests.append({
            'dimension': 'success_rate',
            'type': 'boundary',
            'input': '测试skill ./my-skill/ --parallel 100',
            'expected': 'success_or_warning',
            'description': '边界: 高并行度',
            'weight': 0.6
        })
        
        return tests
    
    def _generate_branch_tests(self) -> List[Dict[str, Any]]:
        """生成分支覆盖测试"""
        tests = []
        
        # 检查是否有可选参数
        if '--' in self.body:
            tests.append({
                'dimension': 'branch_coverage',
                'type': 'condition',
                'input': '测试带可选参数',
                'expected': 'optional_branch_executed',
                'description': '分支: 可选参数',
                'weight': 0.7
            })
        
        # 检查是否有 API key
        if 'api' in self.body.lower():
            tests.append({
                'dimension': 'branch_coverage',
                'type': 'condition',
                'input': '测试不带 API key',
                'expected': 'auth_branch_executed',
                'description': '分支: 认证流程',
                'weight': 0.8
            })
        
        return tests
    
    def _generate_tool_tests(self) -> List[Dict[str, Any]]:
        """生成工具准确度测试"""
        tests = []
        
        for tool in self.tools[:3]:  # 最多 3 个工具
            tests.append({
                'dimension': 'tool_accuracy',
                'type': 'tool_selection',
                'input': f'使用 {tool}',
                'expected': tool,
                'description': f'工具选择: {tool}',
                'weight': 1.0
            })
        
        return tests


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("用法: test_generator.py <skill-path>")
        sys.exit(1)
    
    generator = TestGenerator(Path(sys.argv[1]))
    analysis = generator.analyze()
    test_cases = generator.generate()
    
    print("分析结果:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    print(f"\n生成了 {len(test_cases)} 个测试用例:")
    print(json.dumps(test_cases, indent=2, ensure_ascii=False))