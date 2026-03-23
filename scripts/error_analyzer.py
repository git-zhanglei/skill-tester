#!/usr/bin/env python3
"""
Error Analyzer - Detailed error diagnosis and suggestions
"""

import re
from typing import Dict, Any, Optional
from pathlib import Path


class ErrorAnalyzer:
    """Analyze test errors and provide detailed diagnostics"""
    
    # Error patterns and their solutions
    ERROR_PATTERNS = {
        'trigger_not_found': {
            'patterns': [
                r'trigger.*not.*found',
                r'触发词.*未找到',
                r'keyword.*not.*match',
            ],
            'category': '配置错误',
            'suggestion': '检查 SKILL.md 中的触发词定义',
            'fix_steps': [
                '打开 SKILL.md',
                '查找 description 中的触发词列表',
                '确认测试输入是否在列表中',
                '如需添加，更新 description 和触发词文档'
            ],
            'doc_link': 'references/test-cases.md'
        },
        'api_key_missing': {
            'patterns': [
                r'AK.*not.*configured',
                r'API.*key.*missing',
                r'未配置.*AK',
                r'签名无效',
                r'401',
            ],
            'category': '认证错误',
            'suggestion': '配置 API 密钥',
            'fix_steps': [
                '获取 AK 密钥',
                '运行 configure 命令：cli.py configure YOUR_AK',
                '验证配置：cli.py check'
            ],
            'doc_link': 'references/capabilities/configure.md'
        },
        'shop_not_bound': {
            'patterns': [
                r'shop.*not.*bound',
                r'店铺未绑定',
                r'no.*shop.*found',
            ],
            'category': '配置错误',
            'suggestion': '绑定下游店铺',
            'fix_steps': [
                '打开 1688 AI版 APP',
                '进入「一键开店」',
                '完成店铺绑定',
                '重新运行命令'
            ],
            'doc_link': 'references/faq/new-store.md'
        },
        'rate_limited': {
            'patterns': [
                r'rate.*limit',
                r'限流',
                r'429',
                r'too.*many.*request',
            ],
            'category': '限流错误',
            'suggestion': '等待后重试',
            'fix_steps': [
                '等待 1-2 分钟',
                '降低请求频率',
                '检查是否有循环调用'
            ],
            'doc_link': 'references/common/error-handling.md'
        },
        'network_error': {
            'patterns': [
                r'network.*error',
                r'connection.*refused',
                r'timeout',
                r'网络错误',
                r'连接超时',
            ],
            'category': '网络错误',
            'suggestion': '检查网络连接',
            'fix_steps': [
                '检查网络连接',
                '确认 1688 API 可访问',
                '检查代理设置',
                '稍后重试'
            ],
            'doc_link': 'references/common/error-handling.md'
        },
        'invalid_parameter': {
            'patterns': [
                r'invalid.*parameter',
                r'参数错误',
                r'required.*argument',
                r'missing.*required',
            ],
            'category': '参数错误',
            'suggestion': '检查命令参数',
            'fix_steps': [
                '查看命令帮助：cli.py <command> --help',
                '确认所有必需参数已提供',
                '检查参数格式是否正确'
            ],
            'doc_link': 'references/capabilities/'
        },
        'command_not_found': {
            'patterns': [
                r'command.*not.*found',
                r'unknown.*command',
                r'未识别的命令',
            ],
            'category': '命令错误',
            'suggestion': '使用有效的命令',
            'fix_steps': [
                '查看可用命令：cli.py --help',
                '检查命令拼写',
                '确认 skill 已正确安装'
            ],
            'doc_link': 'SKILL.md'
        },
        'skill_not_activated': {
            'patterns': [
                r'skill.*not.*activated',
                r'未触发',
                r'no.*skill.*matched',
            ],
            'category': '触发错误',
            'suggestion': '检查触发词配置',
            'fix_steps': [
                '确认输入包含触发词',
                '检查触发词拼写',
                '查看 SKILL.md 中的触发词列表'
            ],
            'doc_link': 'SKILL.md'
        }
    }
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.skill_md = skill_path / 'SKILL.md'
    
    def analyze(self, error: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error and provide detailed diagnosis"""
        error_lower = error.lower()
        
        # Try to match error patterns
        for error_type, config in self.ERROR_PATTERNS.items():
            for pattern in config['patterns']:
                if re.search(pattern, error_lower, re.IGNORECASE):
                    return self._build_diagnosis(error_type, config, error, test_case)
        
        # Generic error if no pattern matched
        return self._build_generic_diagnosis(error, test_case)
    
    def _build_diagnosis(self, error_type: str, config: Dict, 
                         original_error: str, test_case: Dict) -> Dict[str, Any]:
        """Build detailed diagnosis for known error types"""
        return {
            'error_type': error_type,
            'category': config['category'],
            'original_error': original_error,
            'suggestion': config['suggestion'],
            'fix_steps': config['fix_steps'],
            'doc_link': config['doc_link'],
            'severity': self._calculate_severity(error_type, test_case),
            'test_context': {
                'dimension': test_case.get('dimension'),
                'input': test_case.get('input'),
                'expected': test_case.get('expected')
            }
        }
    
    def _build_generic_diagnosis(self, error: str, test_case: Dict) -> Dict[str, Any]:
        """Build generic diagnosis for unknown errors"""
        return {
            'error_type': 'unknown',
            'category': '未知错误',
            'original_error': error,
            'suggestion': '查看详细错误信息',
            'fix_steps': [
                '检查错误日志',
                '查看 SKILL.md 文档',
                '在测试环境复现问题',
                '联系 skill 维护者'
            ],
            'doc_link': 'references/common/error-handling.md',
            'severity': 'medium',
            'test_context': {
                'dimension': test_case.get('dimension'),
                'input': test_case.get('input'),
                'expected': test_case.get('expected')
            }
        }
    
    def _calculate_severity(self, error_type: str, test_case: Dict) -> str:
        """Calculate error severity based on type and context"""
        critical_errors = ['api_key_missing', 'shop_not_bound']
        high_errors = ['trigger_not_found', 'skill_not_activated', 'command_not_found']
        
        if error_type in critical_errors:
            return 'critical'
        elif error_type in high_errors:
            return 'high'
        elif test_case.get('dimension') == 'hit_rate':
            return 'high'  # Trigger issues are always high
        else:
            return 'medium'
    
    def format_diagnosis(self, diagnosis: Dict[str, Any]) -> str:
        """Format diagnosis for display"""
        lines = [
            f"❌ 错误类型: {diagnosis['category']}",
            f"   详细信息: {diagnosis['original_error'][:100]}",
            f"   严重程度: {diagnosis['severity'].upper()}",
            f"",
            f"💡 建议: {diagnosis['suggestion']}",
            f"",
            f"🔧 修复步骤:",
        ]
        
        for i, step in enumerate(diagnosis['fix_steps'], 1):
            lines.append(f"   {i}. {step}")
        
        lines.extend([
            f"",
            f"📖 参考文档: {diagnosis['doc_link']}",
        ])
        
        if diagnosis['test_context']['input']:
            lines.extend([
                f"",
                f"📝 测试上下文:",
                f"   输入: '{diagnosis['test_context']['input']}'",
                f"   期望: {diagnosis['test_context']['expected']}",
            ])
        
        return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: error_analyzer.py <skill-path>")
        sys.exit(1)
    
    analyzer = ErrorAnalyzer(Path(sys.argv[1]))
    
    # Test cases
    test_errors = [
        'Trigger not found: 铺货失败',
        'AK not configured',
        'Network timeout after 30s',
        'Unknown error occurred'
    ]
    
    print("Error Analysis Demo:")
    print("=" * 60)
    
    for error in test_errors:
        test_case = {'dimension': 'hit_rate', 'input': 'test', 'expected': 'activate'}
        diagnosis = analyzer.analyze(error, test_case)
        print(analyzer.format_diagnosis(diagnosis))
        print("\n" + "=" * 60 + "\n")