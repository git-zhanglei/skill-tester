#!/usr/bin/env python3
"""
Test Executor - 并行测试执行
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from openclaw_executor import OpenClawExecutor
from error_analyzer import ErrorAnalyzer


class TestExecutor:
    """使用线程池并行执行测试"""
    
    def __init__(self, skill_path: Path, test_cases: List[Dict], 
                 parallel: int = 4, timeout: int = 60,
                 env_vars: Optional[Dict[str, str]] = None):
        self.skill_path = skill_path
        self.test_cases = test_cases
        self.parallel = parallel
        self.timeout = timeout
        self.env_vars = env_vars or {}
        self.results = []
    
    def execute(self) -> Dict[str, Any]:
        """并行执行所有测试用例"""
        print(f"   使用 {self.parallel} 个线程执行 {len(self.test_cases)} 个测试用例...")
        
        # 使用真实执行器
        executor_backend = OpenClawExecutor(
            self.skill_path, 
            timeout=self.timeout
        )
        
        # 初始化错误分析器
        error_analyzer = ErrorAnalyzer(self.skill_path)
        
        # 执行批量测试
        raw_results = executor_backend.execute_batch(self.test_cases, self.parallel)
        
        # 分析失败测试的错误
        self.results = []
        for result in raw_results:
            if result['status'] in ['failed', 'error'] and result.get('error'):
                # 添加详细错误分析
                test_case = result.get('test_case', {})
                diagnosis = error_analyzer.analyze(result['error'], test_case)
                result['error_analysis'] = diagnosis
                result['error_formatted'] = error_analyzer.format_diagnosis(diagnosis)
            self.results.append(result)
        
        # 计算统计
        completed = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'passed')
        failed = sum(1 for r in self.results if r['status'] == 'failed')
        errors = sum(1 for r in self.results if r['status'] == 'error')
        
        # 计算指标
        total = len(self.test_cases)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # 计算各维度指标
        dimensions = {}
        for dim in ['hit_rate', 'success_rate', 'branch_coverage', 'tool_accuracy']:
            dim_results = [r for r in self.results 
                          if r.get('test_case', {}).get('dimension') == dim]
            if dim_results:
                dim_passed = sum(1 for r in dim_results if r['status'] == 'passed')
                dimensions[dim] = {
                    'total': len(dim_results),
                    'passed': dim_passed,
                    'rate': dim_passed / len(dim_results) * 100
                }
        
        # 简化：只保留核心指标
        # 总分 = 成功率（因为真实执行下这是最可靠的指标）
        overall_score = success_rate
        
        return {
            'total': total,
            'completed': completed,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': success_rate,
            'dimensions': dimensions,
            'overall_score': overall_score,
            'results': self.results
        }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: test_executor.py <skill-path>")
        sys.exit(1)
    
    skill_path = Path(sys.argv[1])
    
    # 测试用例
    test_cases = [
        {
            'dimension': 'hit_rate',
            'type': 'exact_match',
            'input': '测试skill',
            'expected': 'activate',
            'description': '精确触发测试'
        },
        {
            'dimension': 'hit_rate',
            'type': 'fuzzy_match',
            'input': '帮我测试一下skill',
            'expected': 'activate',
            'description': '模糊触发测试'
        },
        {
            'dimension': 'success_rate',
            'type': 'normal',
            'input': '运行测试',
            'expected': 'success',
            'description': '正常执行测试'
        }
    ]
    
    print(f"\n🔍 测试 skill: {skill_path.name}")
    print(f"   测试用例数: {len(test_cases)}")
    print(f"   并行度: 2\n")
    
    executor = TestExecutor(
        skill_path=skill_path,
        test_cases=test_cases,
        parallel=2
    )
    
    result = executor.execute()
    
    print(f"\n📊 结果:")
    print(f"   总计: {result['total']}")
    print(f"   通过: {result['passed']}")
    print(f"   失败: {result['failed']}")
    print(f"   错误: {result['errors']}")
    print(f"   成功率: {result['success_rate']:.1f}%")
    print(f"   总分: {result['overall_score']:.1f}/100")