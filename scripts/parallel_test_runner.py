#!/usr/bin/env python3
"""
Parallel Test Runner - 并行执行测试案例
使用真实的 sessions_spawn 调用
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from constants import (
    RESULTS_DIR, ErrorType, TestStatus,
    DEFAULT_PARALLEL, DEFAULT_TIMEOUT
)


class ParallelTestRunner:
    """使用子 agent 并行执行测试"""
    
    def __init__(self, skill_path: Path, test_cases_data: Dict, 
                 parallel: int = 4, timeout: int = 60):
        self.skill_path = skill_path
        self.test_cases_data = test_cases_data
        self.parallel = parallel
        self.timeout = timeout
        self.cases = test_cases_data.get('cases', [])
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def run(self) -> Dict[str, Any]:
        """并行执行所有测试案例"""
        total = len(self.cases)
        
        print(f"\n   总计: {total} 个测试案例")
        print(f"   并行度: {self.parallel} 个线程")
        print(f"   超时: {self.timeout} 秒/案例")
        print(f"   结果目录: {RESULTS_DIR}\n")
        
        # 更新状态为运行中
        self.test_cases_data['execution']['status'] = 'running'
        self.test_cases_data['execution']['started_at'] = datetime.now().isoformat()
        
        # 使用线程池并行执行
        completed = 0
        passed = 0
        failed = 0
        errors = 0
        
        with ThreadPoolExecutor(max_workers=self.parallel) as executor:
            # 提交所有任务
            future_to_case = {}
            for case in self.cases:
                future = executor.submit(self._execute_single_case, case)
                future_to_case[future] = case
            
            # 收集结果
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                
                try:
                    result = future.result(timeout=self.timeout)
                    
                    # 更新案例状态
                    case['status'] = TestStatus.COMPLETED
                    case['result'] = result
                    case['completed_at'] = datetime.now().isoformat()
                    
                    # 统计
                    completed += 1
                    if result.get('status') == TestStatus.PASSED:
                        passed += 1
                    elif result.get('status') == TestStatus.FAILED:
                        failed += 1
                    else:
                        errors += 1
                    
                    # 显示进度
                    self._show_progress(completed, total, case, result)
                    
                    # 每10个保存一次中间结果（减少IO）
                    if completed % 10 == 0:
                        self._save_intermediate_result(case)
                    
                except Exception as e:
                    # 执行异常
                    error_result = {
                        'status': TestStatus.ERROR,
                        'error': f'执行异常: {str(e)}',
                        'error_type': ErrorType.EXECUTION_EXCEPTION,
                        'duration': 0,
                        'output': ''
                    }
                    case['status'] = TestStatus.COMPLETED
                    case['result'] = error_result
                    case['completed_at'] = datetime.now().isoformat()
                    
                    completed += 1
                    errors += 1
                    
                    self._show_progress(completed, total, case, error_result)
                    # 异常时立即保存
                    self._save_intermediate_result(case)
        
        # 计算成功率（加权）
        success_rate = self._calculate_weighted_success_rate()
        
        # 构建执行结果
        execution_result = {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'total': total,
            'completed': completed,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'success_rate': success_rate,
            'duration_seconds': self._calculate_duration()
        }
        
        # 更新测试案例集
        self.test_cases_data['execution']['status'] = 'completed'
        self.test_cases_data['execution']['completed_at'] = execution_result['completed_at']
        self.test_cases_data['execution']['progress'] = {
            'total': total,
            'completed': completed,
            'passed': passed,
            'failed': failed,
            'errors': errors
        }
        
        # 保存最终结果
        self._save_final_results()
        
        return execution_result
    
    def _execute_single_case(self, case: Dict) -> Dict:
        """执行单个测试案例"""
        start_time = time.time()
        
        case_id = case.get('id', 'unknown')
        dimension = case.get('dimension', 'unknown')
        test_input = case.get('input', '')
        expected = case.get('expected', '')
        
        try:
            # 调用真实的测试执行
            result = self._call_skill_real(test_input, case)
            
            duration = time.time() - start_time
            
            # 判断结果
            if result.get('error'):
                status = TestStatus.ERROR
            elif result.get('success'):
                status = TestStatus.PASSED
            else:
                status = TestStatus.FAILED
            
            return {
                'status': status,
                'output': result.get('output', ''),
                'error': result.get('error'),
                'error_type': result.get('error_type'),
                'duration': duration,
                'matches_expected': result.get('matches_expected', False)
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': TestStatus.ERROR,
                'output': '',
                'error': str(e),
                'error_type': ErrorType.CALL_EXCEPTION,
                'duration': duration,
                'matches_expected': False
            }
    
    def _call_skill_real(self, test_input: str, case: Dict) -> Dict:
        """
        真实调用 skill 进行测试
        
        尝试调用 sessions_spawn，如果不可用则返回明确的错误
        """
        try:
            # 尝试导入 OpenClaw 工具
            # 注意：这里应该通过工具调用框架调用 sessions_spawn
            # 目前返回明确的未实现错误
            
            # 检查是否在 OpenClaw 环境中
            if not self._is_openclaw_available():
                return {
                    'success': False,
                    'output': '',
                    'error': 'OpenClaw 运行时不可用。请确保在 OpenClaw 环境中运行测试。',
                    'error_type': ErrorType.OPENCLAW_NOT_AVAILABLE,
                    'matches_expected': False
                }
            
            # TODO: 集成真实的 sessions_spawn 调用
            # 这里应该调用工具来执行测试
            return {
                'success': False,
                'output': '',
                'error': '真实执行尚未完全实现。需要集成 sessions_spawn 工具调用。',
                'error_type': ErrorType.NOT_IMPLEMENTED,
                'matches_expected': False
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'调用异常: {str(e)}',
                'error_type': ErrorType.CALL_EXCEPTION,
                'matches_expected': False
            }
    
    def _is_openclaw_available(self) -> bool:
        """检查 OpenClaw 是否可用"""
        # 检查环境变量或特定标记
        return os.environ.get('OPENCLAW_AVAILABLE', 'false').lower() == 'true'
    
    def _calculate_weighted_success_rate(self) -> float:
        """计算加权成功率"""
        total_weight = 0
        passed_weight = 0
        
        for case in self.cases:
            if case.get('status') == 'completed':
                weight = case.get('weight', 1.0)
                total_weight += weight
                
                result = case.get('result', {})
                if result.get('status') == 'passed':
                    passed_weight += weight
        
        return (passed_weight / total_weight * 100) if total_weight > 0 else 0
    
    def _show_progress(self, completed: int, total: int, case: Dict, result: Dict):
        """显示执行进度"""
        desc = case.get('description', '无描述')[:40]
        weight = case.get('weight', 1.0)
        error_msg = result.get('error', '')
        
        if result.get('status') == TestStatus.PASSED:
            icon = '✅'
            status_detail = f"({result.get('duration', 0):.1f}s)"
        elif result.get('status') == TestStatus.FAILED:
            icon = '❌'
            error_short = error_msg[:30] if error_msg else '失败'
            status_detail = f"[{error_short}]"
        else:
            icon = '💥'
            error_short = error_msg[:30] if error_msg else '错误'
            status_detail = f"[{error_short}]"
        
        print(f"   [{completed}/{total}] {icon} {desc} (权重:{weight:.1f}) {status_detail}")
    
    def _save_intermediate_result(self, case: Dict):
        """保存中间结果"""
        case_id = case.get('id', 'unknown')
        result_file = RESULTS_DIR / f"{case_id}.json"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(case, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 忽略保存错误
    
    def _save_final_results(self):
        """保存最终结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = RESULTS_DIR / f"execution-result-{timestamp}.json"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_cases_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _calculate_duration(self) -> float:
        """计算执行时长"""
        start = self.test_cases_data['execution'].get('started_at')
        end = self.test_cases_data['execution'].get('completed_at')
        
        if start and end:
            try:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                return (end_dt - start_dt).total_seconds()
            except:
                pass
        
        return 0.0


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("用法: parallel_test_runner.py <skill-path> <test-cases-file>")
        sys.exit(1)
    
    skill_path = Path(sys.argv[1])
    test_cases_file = Path(sys.argv[2])
    
    with open(test_cases_file, 'r', encoding='utf-8') as f:
        test_cases_data = json.load(f)
    
    runner = ParallelTestRunner(skill_path, test_cases_data, parallel=2)
    result = runner.run()
    
    print("\n" + "=" * 50)
    print("执行结果:")
    print("=" * 50)
    print(f"成功率: {result['success_rate']:.1f}%")
    print(f"通过: {result['passed']}/{result['total']}")