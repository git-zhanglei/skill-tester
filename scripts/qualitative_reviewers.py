#!/usr/bin/env python3
"""
定性评审器 - 嵌入自 Skill Test
结构、实用性和领域评审器
"""

import re
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    yaml = None


class ReviewerSuite:
    """运行所有定性评审器"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.skill_md = skill_path / 'SKILL.md'
        self.content = ""
        self.frontmatter = {}
        self.body = ""
        
        if self.skill_md.exists():
            self.content = self.skill_md.read_text(encoding='utf-8')
            self._parse_content()
    
    def _parse_content(self):
        """解析 frontmatter 和 body"""
        if self.content.startswith('---'):
            parts = self.content.split('---', 2)
            if len(parts) >= 3:
                if yaml:
                    try:
                        self.frontmatter = yaml.safe_load(parts[1]) or {}
                    except Exception:
                        self.frontmatter = self._parse_frontmatter_manual(parts[1])
                else:
                    self.frontmatter = self._parse_frontmatter_manual(parts[1])
                self.body = parts[2].strip()
        else:
            self.body = self.content
    
    def _parse_frontmatter_manual(self, text: str) -> Dict[str, Any]:
        """yaml 不可用时手动解析 frontmatter"""
        result = {}
        for line in text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip().strip('"\'')
        return result
    
    def evaluate(self) -> Dict[str, Any]:
        """运行所有评审器"""
        return {
            'structure': self._structure_reviewer(),
            'usefulness': self._usefulness_reviewer(),
            'domain': self._domain_reviewer()
        }
    
    def _structure_reviewer(self) -> Dict[str, Any]:
        """评估 SKILL.md 结构"""
        findings = []
        recommendations = []
        score = 100
        
        # 检查 SKILL.md 长度
        lines = self.body.split('\n')
        if len(lines) > 500:
            findings.append(f"SKILL.md 有 {len(lines)} 行（建议 < 500）")
            recommendations.append("将内容拆分到 references/ 目录")
            score -= 10
        elif len(lines) > 80:
            findings.append(f"SKILL.md 有 {len(lines)} 行（考虑拆分到 references/）")
            recommendations.append("考虑将详细内容移到 references/")
            score -= 5
        
        # 检查 frontmatter
        if not self.frontmatter.get('name'):
            findings.append("frontmatter 中缺少 'name'")
            recommendations.append("在 frontmatter 中添加 'name' 字段")
            score -= 15
        
        if not self.frontmatter.get('description'):
            findings.append("frontmatter 中缺少 'description'")
            recommendations.append("在 frontmatter 中添加 'description' 字段")
            score -= 15
        
        # 检查渐进式披露
        has_references = (self.skill_path / 'references').exists()
        if len(lines) > 100 and not has_references:
            findings.append("SKILL.md 较大但没有 references/ 目录")
            recommendations.append("创建 references/ 目录存放详细内容")
            score -= 10
        
        # 检查冗余文件
        redundant_files = ['README.md', 'CHANGELOG.md', 'INSTALLATION.md', 'QUICK_REFERENCE.md']
        for rf in redundant_files:
            if (self.skill_path / rf).exists():
                findings.append(f"冗余文件: {rf}")
                recommendations.append(f"删除 {rf} - skill 不应有辅助文档")
                score -= 5
        
        # 检查正确标题
        if not re.search(r'^# ', self.body, re.MULTILINE):
            findings.append("缺少 H1 标题")
            recommendations.append("添加主标题使用 # ")
            score -= 10
        
        # 检查代码示例
        if '```' not in self.body:
            findings.append("未找到代码示例")
            recommendations.append("添加代码示例以提高清晰度")
            score -= 5
        
        # 确定结论
        if score >= 90:
            verdict = '✅ 优秀'
        elif score >= 70:
            verdict = '✅ 良好'
        elif score >= 50:
            verdict = '⚠️ 可接受'
        else:
            verdict = '❌ 需要改进'
        
        return {
            'verdict': verdict,
            'score': max(0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _usefulness_reviewer(self) -> Dict[str, Any]:
        """评估 skill 实用性"""
        findings = []
        recommendations = []
        score = 100
        
        desc = self.frontmatter.get('description', '')
        
        # 检查描述清晰度
        if len(desc) < 50:
            findings.append(f"描述太短（{len(desc)} 字符，建议 > 50）")
            recommendations.append("扩展描述以解释 skill 做什么")
            score -= 15
        elif len(desc) > 500:
            findings.append("描述很长（> 500 字符）")
            recommendations.append("保持描述简洁")
            score -= 5
        
        # 检查清晰触发词
        trigger_indicators = ['triggers on', 'use when', 'activate when', 'for:', '用于', '触发']
        has_trigger = any(ti in desc.lower() or ti in self.body.lower() 
                          for ti in trigger_indicators)
        if not has_trigger:
            findings.append("描述中无清晰触发条件")
            recommendations.append("添加触发条件（例如，'Use when...'）")
            score -= 15
        
        # 检查可执行指令
        action_words = ['run', 'execute', 'use', 'call', 'install', 'configure', '执行', '运行']
        has_actions = any(aw in self.body.lower() for aw in action_words)
        if not has_actions:
            findings.append("指令可能不可执行")
            recommendations.append("添加清晰的操作步骤")
            score -= 10
        
        # 检查示例
        example_indicators = ['example', '示例', 'for instance', 'e.g.', 'such as', '用法']
        has_examples = any(ei in self.body.lower() for ei in example_indicators)
        if not has_examples:
            findings.append("未提供示例")
            recommendations.append("添加用法示例")
            score -= 10
        
        # 检查前置条件
        prereq_indicators = ['prerequisite', 'requirement', 'need', '依赖', '需要', 'install']
        has_prereqs = any(pi in self.body.lower() for pi in prereq_indicators)
        if not has_prereqs and 'install' in self.body.lower():
            findings.append("提到安装但未列出前置条件")
            recommendations.append("列出前置条件和依赖")
            score -= 5
        
        # 确定结论
        if score >= 90:
            verdict = '✅ 优秀'
        elif score >= 70:
            verdict = '✅ 良好'
        elif score >= 50:
            verdict = '⚠️ 可接受'
        else:
            verdict = '❌ 需要改进'
        
        return {
            'verdict': verdict,
            'score': max(0, score),
            'findings': findings,
            'recommendations': recommendations
        }
    
    def _domain_reviewer(self) -> Dict[str, Any]:
        """评估领域正确性"""
        findings = []
        recommendations = []
        score = 100
        
        # 检查工具引用
        tool_patterns = [
            (r'`(\w+)`\s+tool', '工具引用'),
            (r'(npm|pip|brew|apt)\s+(install|run)', '包管理器'),
            (r'(curl|wget)\s+', '下载命令'),
        ]
        
        tools_found = []
        for pattern, desc in tool_patterns:
            matches = re.findall(pattern, self.body)
            tools_found.extend(matches)
        
        if not tools_found:
            findings.append("未引用特定工具")
            recommendations.append("提及使用的具体工具/API")
            score -= 5
        
        # 检查 API 引用
        api_patterns = [
            r'api[_-]?key',
            r'token',
            r'endpoint',
            r'https?://\S+',
        ]
        
        has_api = any(re.search(ap, self.body, re.IGNORECASE) for ap in api_patterns)
        if has_api:
            # 检查是否提到认证
            auth_indicators = ['auth', 'credential', 'login', 'key', 'token', '认证']
            has_auth = any(ai in self.body.lower() for ai in auth_indicators)
            if not has_auth:
                findings.append("使用 API 但未提供认证指导")
                recommendations.append("添加认证说明")
                score -= 10
        
        # 检查错误处理
        error_indicators = ['error', 'exception', 'fail', 'catch', 'try', '处理', '错误']
        has_error_handling = any(ei in self.body.lower() for ei in error_indicators)
        if not has_error_handling:
            findings.append("未提及错误处理")
            recommendations.append("添加错误处理指导")
            score -= 10
        
        # 检查版本固定（最佳实践）
        version_patterns = [
            r'@\d+\.\d+',  # @1.0.0
            r'==\d+\.\d+',  # ==1.0.0
        ]
        
        has_version_pinning = any(re.search(vp, self.body) for vp in version_patterns)
        if tools_found and not has_version_pinning:
            findings.append("依赖未固定版本")
            recommendations.append("固定依赖版本以确保可重现性")
            score -= 5
        
        # 确定结论
        if score >= 90:
            verdict = '✅ 优秀'
        elif score >= 70:
            verdict = '✅ 良好'
        elif score >= 50:
            verdict = '⚠️ 可接受'
        else:
            verdict = '❌ 需要改进'
        
        return {
            'verdict': verdict,
            'score': max(0, score),
            'findings': findings,
            'recommendations': recommendations
        }


def run_reviewers(skill_path: Path) -> Dict[str, Any]:
    """便捷函数运行所有评审器"""
    suite = ReviewerSuite(skill_path)
    return suite.evaluate()


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("用法: qualitative_reviewers.py <skill-path>")
        sys.exit(1)
    
    result = run_reviewers(Path(sys.argv[1]))
    print(json.dumps(result, indent=2, ensure_ascii=False))