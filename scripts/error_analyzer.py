#!/usr/bin/env python3
"""
Error Analyzer v3 — skill-tester 专用错误诊断器
将测试执行中出现的错误字符串，匹配到已知类别并给出修复指导。
"""

import re
from typing import Dict, Any
from pathlib import Path


class ErrorAnalyzer:
    """分析测试错误并提供详细诊断"""

    ERROR_PATTERNS: Dict[str, Dict] = {

        'skill_path_not_found': {
            'patterns': [
                r'SKILL\.md.*not found',
                r'skill.*路径.*不存在',
                r'No such file.*SKILL',
                r'FileNotFoundError',
            ],
            'category': '路径错误',
            'suggestion': '确认 skill_path 参数指向一个包含 SKILL.md 的目录',
            'fix_steps': [
                '检查路径是否正确：ls <skill_path>/SKILL.md',
                '如路径含空格，用引号包裹',
                '确认目标 Skill 已正确解压/克隆到本地',
            ],
            'doc_link': 'references/troubleshooting.md',
        },

        'safety_check_blocked': {
            'patterns': [
                r'safety.*failed',
                r'安全检查.*失败',
                r'dangerous.*pattern',
                r'硬编码.*密码',
                r'credential.*detected',
            ],
            'category': '安全检查阻断',
            'suggestion': '目标 Skill 存在危险模式或硬编码凭证，必须先修复',
            'fix_steps': [
                '运行 python3 scripts/safety_checker.py <skill_path> 查看详细问题',
                '移除脚本中的硬编码 API Key、密码、token',
                '用环境变量替代，通过 os.environ.get() 在脚本中读取',
                '修复后重新运行 safety_checker.py 确认通过',
            ],
            'doc_link': 'references/safety-checker.md',
        },

        'openclaw_unavailable': {
            'patterns': [
                r'OPENCLAW_AVAILABLE',
                r'sessions_spawn.*not.*available',
                r'OpenClaw.*不可用',
                r'openclaw_not_available',
            ],
            'category': 'OpenClaw 环境不可用',
            'suggestion': '步骤 4 的执行需要在 OpenClaw Agent 环境中运行',
            'fix_steps': [
                '确认已在 OpenClaw 环境中（不是本地 Python 脚本直接运行）',
                '检查 OPENCLAW_AVAILABLE 环境变量是否已设置',
                '在 OpenClaw Agent 中执行，Agent 会自动调用 sessions_spawn',
                '参见 SKILL.md 步骤 4 的执行说明',
            ],
            'doc_link': 'SKILL.md',
        },

        'spec_score_low': {
            'patterns': [
                r'spec_score.*[0-3]\d',
                r'规范.*得分.*低',
                r'token_cost.*fail',
                r'valid_frontmatter.*fail',
            ],
            'category': '规范得分不达标',
            'suggestion': '运行 spec_checker.py --verbose 查看具体失败项',
            'fix_steps': [
                'python3 scripts/spec_checker.py <skill_path> --verbose',
                '修复所有 ❌ 项（如 frontmatter 缺失、行数过多）',
                '处理 ⚠️ 项（如无 Guardrails 章节、description 无触发语境）',
                '目标：spec_score ≥ 70',
            ],
            'doc_link': 'references/test-cases.md',
        },

        'test_generation_empty': {
            'patterns': [
                r'no.*test.*cases',
                r'cases.*empty',
                r'测试案例.*为空',
                r'generate.*0.*cases',
            ],
            'category': '测试案例生成失败',
            'suggestion': '目标 SKILL.md 描述不足，Agent 无法泛化出测试案例',
            'fix_steps': [
                '检查目标 SKILL.md 是否有 description、触发词、预期输出说明',
                '至少提供 2-3 个使用示例',
                '声明 Skill 的预期输出格式或结果',
            ],
            'doc_link': 'references/test-cases.md',
        },

        'session_timeout': {
            'patterns': [
                r'timeout',
                r'timed.*out',
                r'超时',
                r'TimeoutError',
            ],
            'category': '执行超时',
            'suggestion': '增大 --timeout 参数，或检查目标 Skill 的性能问题',
            'fix_steps': [
                '增加超时：--timeout 120（默认 60 秒）',
                '检查目标 Skill 是否有阻塞调用（如同步等待网络）',
                '对慢 Skill 单独设置较大 timeout',
                '查看 references/troubleshooting.md 了解超时调试方法',
            ],
            'doc_link': 'references/troubleshooting.md',
        },

        'results_file_not_found': {
            'patterns': [
                r'results.*json.*not.*found',
                r'报告.*文件.*不存在',
                r'report_builder.*FileNotFoundError',
            ],
            'category': '报告文件缺失',
            'suggestion': '步骤 4 完成后，results JSON 文件才能生成；确认步骤 4 已成功执行',
            'fix_steps': [
                '确认步骤 4 的所有案例均已通过 --record 记录',
                '执行 --finalize 生成完整 results JSON',
                '检查文件路径参数是否正确传入 report_builder.py',
            ],
            'doc_link': 'references/report-template.md',
        },

        'spec_checker_crash': {
            'patterns': [
                r'spec_checker.*crash',
                r'检查崩溃',
                r'spec_checker.*Error',
            ],
            'category': 'spec_checker 崩溃',
            'suggestion': '目标 Skill 的 scripts/ 中可能有无法读取的文件',
            'fix_steps': [
                'python3 scripts/spec_checker.py <skill_path> --verbose',
                '检查 scripts/ 目录下是否有编码异常的 .py 文件',
                '确认 SKILL.md 以 UTF-8 编码保存',
            ],
            'doc_link': 'references/troubleshooting.md',
        },
    }

    def __init__(self, skill_path: Path):
        self.skill_path = skill_path

    def analyze(self, error: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """匹配错误字符串，返回详细诊断"""
        error_lower = error.lower()
        for error_type, cfg in self.ERROR_PATTERNS.items():
            for pat in cfg['patterns']:
                if re.search(pat, error_lower, re.IGNORECASE):
                    return self._build_diagnosis(error_type, cfg, error, test_case)
        return self._build_generic_diagnosis(error, test_case)

    def _build_diagnosis(self, error_type: str, cfg: Dict,
                         original: str, test_case: Dict) -> Dict[str, Any]:
        return {
            'error_type':    error_type,
            'category':      cfg['category'],
            'original_error': original,
            'suggestion':    cfg['suggestion'],
            'fix_steps':     cfg['fix_steps'],
            'doc_link':      cfg['doc_link'],
            'severity':      self._severity(error_type, test_case),
            'test_context':  {
                'dimension': test_case.get('dimension'),
                'input':     test_case.get('input'),
                'expected':  test_case.get('expected'),
            },
        }

    def _build_generic_diagnosis(self, error: str, test_case: Dict) -> Dict[str, Any]:
        return {
            'error_type':    'unknown',
            'category':      '未知错误',
            'original_error': error,
            'suggestion':    '查看 references/troubleshooting.md 获取调试指南',
            'fix_steps': [
                '检查完整错误日志',
                '运行 python3 verify.py 确认工程文件完整',
                '参见 references/troubleshooting.md',
            ],
            'doc_link': 'references/troubleshooting.md',
            'severity':  'medium',
            'test_context': {
                'dimension': test_case.get('dimension'),
                'input':     test_case.get('input'),
                'expected':  test_case.get('expected'),
            },
        }

    @staticmethod
    def _severity(error_type: str, test_case: Dict) -> str:
        critical = {'safety_check_blocked', 'skill_path_not_found'}
        high     = {'openclaw_unavailable', 'spec_score_low', 'test_generation_empty'}
        if error_type in critical:
            return 'critical'
        if error_type in high or test_case.get('dimension') == 'hit_rate':
            return 'high'
        return 'medium'

    def format_diagnosis(self, diagnosis: Dict[str, Any]) -> str:
        """格式化为人类可读文本"""
        lines = [
            f'❌ 错误类型：{diagnosis["category"]}',
            f'   原始错误：{diagnosis["original_error"][:100]}',
            f'   严重程度：{diagnosis["severity"].upper()}',
            '',
            f'💡 建议：{diagnosis["suggestion"]}',
            '',
            '🔧 修复步骤：',
        ]
        for i, step in enumerate(diagnosis['fix_steps'], 1):
            lines.append(f'   {i}. {step}')
        lines += ['', f'📖 参考文档：{diagnosis["doc_link"]}']
        ctx = diagnosis.get('test_context', {})
        if ctx.get('input'):
            lines += ['', '📝 测试上下文：',
                      f'   输入：\'{ctx["input"]}\'',
                      f'   预期：{ctx["expected"]}']
        return '\n'.join(lines)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('用法: error_analyzer.py <skill-path>')
        sys.exit(1)

    analyzer = ErrorAnalyzer(Path(sys.argv[1]))
    demo_errors = [
        ('SKILL.md not found', {'dimension': 'hit_rate', 'input': 'test', 'expected': 'activate'}),
        ('safety check failed: dangerous pattern detected',
         {'dimension': 'execution_success', 'input': 'rm -rf /', 'expected': 'reject'}),
        ('OpenClaw 不可用，sessions_spawn not available',
         {'dimension': 'execution_success', 'input': 'run task', 'expected': 'success'}),
        ('timeout after 60s', {'dimension': 'agent_comprehension', 'input': 'slow task', 'expected': 'output'}),
    ]
    sep = '=' * 60
    for err, tc in demo_errors:
        diag = analyzer.analyze(err, tc)
        print(analyzer.format_diagnosis(diag))
        print(f'\n{sep}\n')
