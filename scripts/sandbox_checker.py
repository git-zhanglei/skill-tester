#!/usr/bin/env python3
"""
Sandbox Checker - 判断目标 Skill 是否适合在沙箱环境测试

设计目标：
1. 在“生成测试案例前”给出可沙箱执行判断
2. 若依赖关键能力（环境变量、外网、浏览器自动化等），明确给出风险告知
3. 输出机器可读 JSON，供主流程拼接到确认提示中
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any


class SandboxChecker:
    """基于启发式规则判断沙箱可测试性"""

    RULES = [
        {
            'id': 'env_vars',
            'capability': 'environment_variables',
            'label': '环境变量',
            'reason': '检测到环境变量依赖（如 API Key / Token），默认沙箱无法直接继承宿主机密钥',
            'patterns': [
                r'os\.environ',
                r'os\.getenv',
                r'process\.env',
                r'\b[A-Z][A-Z0-9_]*_(?:KEY|TOKEN|SECRET)\b',
                r'环境变量',
                r'api[_ -]?key',
            ],
        },
        {
            'id': 'network_access',
            'capability': 'network_access',
            'label': '网络访问',
            'reason': '检测到外部网络/API 依赖，沙箱通常禁网或网络受限',
            'patterns': [
                r'https?://',
                r'\bcurl\b',
                r'\bwget\b',
                r'\brequests\.',
                r'\burllib\.',
                r'\bfetch\s*\(',
                r'网络搜索',
                r'联网',
                r'websearch',
            ],
        },
        {
            'id': 'browser_tools',
            'capability': 'browser_tools',
            'label': '浏览器能力',
            'reason': '检测到浏览器/页面自动化依赖，沙箱环境通常不会默认开放浏览器能力',
            'patterns': [
                r'\bplaywright\b',
                r'\bchrome[-_ ]devtools\b',
                r'\bbrowser_(?:navigate|click|snapshot|search)\b',
                r'浏览器',
                r'网页',
            ],
        },
    ]

    SCAN_GLOBS = ('**/*.md', '**/*.py', '**/*.sh', '**/*.json', '**/*.yaml', '**/*.yml')

    def __init__(self, skill_path: Path):
        self.skill_path = skill_path

    def check(self) -> Dict[str, Any]:
        """执行检查，返回结构化结果"""
        if not self.skill_path.exists() or not self.skill_path.is_dir():
            return {
                'status': 'error',
                'sandbox_testable': False,
                'dependencies': [],
                'risk_notice': '目标路径无效，无法判断沙箱可测试性',
            }

        skill_md = self.skill_path / 'SKILL.md'
        if not skill_md.exists():
            return {
                'status': 'error',
                'sandbox_testable': False,
                'dependencies': [],
                'risk_notice': '缺少 SKILL.md，无法判断沙箱可测试性',
            }

        detections: Dict[str, Dict[str, Any]] = {}
        for rel_path, lineno, line in self._iter_text_lines():
            for rule in self.RULES:
                if self._line_matches(rule['patterns'], line):
                    entry = detections.setdefault(rule['id'], {
                        'capability': rule['capability'],
                        'label': rule['label'],
                        'reason': rule['reason'],
                        'evidence': [],
                    })
                    if len(entry['evidence']) < 3:
                        entry['evidence'].append(f'{rel_path}:{lineno}: {line.strip()[:120]}')

        dependencies = list(detections.values())
        sandbox_testable = len(dependencies) == 0
        labels = [d['label'] for d in dependencies]
        risk_notice = (
            '可在沙箱环境中执行测试'
            if sandbox_testable
            else f'待测试 Skill 依赖 {"、".join(labels)}，无法在沙箱中完整测试，可能影响本地环境'
        )

        return {
            'status': 'sandbox_compatible' if sandbox_testable else 'sandbox_incompatible',
            'sandbox_testable': sandbox_testable,
            'dependencies': dependencies,
            'risk_notice': risk_notice,
        }

    def _iter_text_lines(self):
        seen = set()
        for glob_pat in self.SCAN_GLOBS:
            for path in self.skill_path.glob(glob_pat):
                if not path.is_file():
                    continue
                if path in seen:
                    continue
                seen.add(path)
                # 跳过过大文件，避免误伤性能
                if path.stat().st_size > 1024 * 1024:
                    continue
                try:
                    content = path.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                rel = str(path.relative_to(self.skill_path))
                for lineno, line in enumerate(content.splitlines(), start=1):
                    yield rel, lineno, line

    def _line_matches(self, patterns: List[str], line: str) -> bool:
        return any(re.search(p, line, re.IGNORECASE) for p in patterns)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: sandbox_checker.py <skill-path>')
        sys.exit(1)

    checker = SandboxChecker(Path(sys.argv[1]))
    result = checker.check()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 可沙箱性结果只用于风险告知，不作为执行失败码
    if result.get('status') == 'error':
        sys.exit(1)
    sys.exit(0)
