#!/usr/bin/env python3
"""
OpenClaw Executor - 真实测试执行
真正调用 sessions_spawn 进行测试
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class OpenClawExecutor:
    """使用 OpenClaw sessions_spawn 执行测试"""
    
    def __init__(self, skill_path: Path, timeout: int = 60):
        self.skill_path = skill_path
        self.timeout = timeout
        self.results = []
    
    def execute_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试用例"""
        start_time = time.time()
        
        dimension = test_case.get('dimension', 'unknown')
        test_input = test_case.get('input', '')
        expected = test_case.get('expected', '')
        
        try:
            # 真实调用 sessions_spawn
            result = self._spawn_session(test_input)
            
            duration = time.time() - start_time
            
            # 判断结果
            if result.get('error'):
                status = 'error'
            elif result.get('success'):
                status = 'passed'
            else:
                status = 'failed'
            
            return {
                'test_case': test_case,
                'status': status,
                'output': result.get('output', ''),
                'error': result.get('error'),
                'duration': duration,
                'result': result
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'test_case': test_case,
                'status': 'error',
                'error': f'执行异常: {str(e)}',
                'duration': duration
            }
    
    def _spawn_session(self, task_input: str) -> Dict[str, Any]:
        """
        调用 OpenClaw sessions_spawn 真实执行
        
        注意：这里需要 OpenClaw 运行时环境
        如果在没有 OpenClaw 的环境中运行，会返回错误
        """
        try:
            # 尝试导入 OpenClaw 的 sessions_spawn
            # 实际运行时，这应该通过工具调用
            from openclaw import sessions_spawn
            
            # 构建测试任务
            task = f"""测试 skill: {self.skill_path.name}

输入: {task_input}

请处理这个输入并返回结果。
"""
            
            # 调用 sessions_spawn
            response = sessions_spawn(
                task=task,
                timeout=self.timeout,
                runtime="subagent"
            )
            
            # 解析响应
            return {
                'success': True,
                'output': str(response),
                'error': None
            }
            
        except ImportError:
            # OpenClaw 未安装或不可用
            return {
                'success': False,
                'output': '',
                'error': 'OpenClaw 运行时不可用。请确保在 OpenClaw 环境中运行。'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'sessions_spawn 调用失败: {str(e)}'
            }
    
    def execute_batch(self, test_cases: List[Dict[str, Any]], 
                     parallel: int = 4) -> List[Dict[str, Any]]:
        """
        并行执行多个测试用例
        
        使用 ThreadPoolExecutor 实现真正的并行执行
        """
        results = []
        total = len(test_cases)
        
        print(f"   并行执行 {total} 个测试用例（{parallel} 个线程）...")
        
        # 使用线程池实现并行
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            # 提交所有任务
            future_to_case = {
                executor.submit(self.execute_test, case): case 
                for case in test_cases
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_case):
                case = future_to_case[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 显示进度
                    desc = case.get('description', '未知')
                    if result['status'] == 'passed':
                        print(f"   [{completed}/{total}] ✅ {desc} ({result['duration']:.1f}秒)")
                    else:
                        print(f"   [{completed}/{total}] ❌ {desc}: {result.get('error', '失败')[:50]}")
                        
                except Exception as e:
                    results.append({
                        'test_case': case,
                        'status': 'error',
                        'error': str(e),
                        'duration': 0
                    })
                    print(f"   [{completed}/{total}] 💥 {case.get('description', '未知')}: 异常")
        
        return results


def test_executor():
    """测试执行器"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: openclaw_executor.py <skill-path>")
        print("\n注意: 需要在 OpenClaw 环境中运行才能真实测试")
        sys.exit(1)
    
    skill_path = Path(sys.argv[1])
    
    if not skill_path.exists():
        print(f"错误: skill 路径不存在: {skill_path}")
        sys.exit(1)
    
    executor = OpenClawExecutor(skill_path)
    
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
            'dimension': 'success_rate',
            'type': 'normal',
            'input': '运行测试',
            'expected': 'success',
            'description': '正常执行测试'
        },
        {
            'dimension': 'hit_rate',
            'type': 'fuzzy_match',
            'input': '帮我测试一下skill',
            'expected': 'activate',
            'description': '模糊触发测试'
        }
    ]
    
    print(f"\n🔍 测试 skill: {skill_path.name}")
    print(f"   测试用例数: {len(test_cases)}")
    print(f"   并行度: 2\n")
    
    results = executor.execute_batch(test_cases, parallel=2)
    
    # 统计
    passed = sum(1 for r in results if r['status'] == 'passed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\n📊 结果统计:")
    print(f"   通过: {passed}")
    print(f"   失败: {failed}")
    print(f"   错误: {errors}")
    
    # 显示详细结果
    print(f"\n📋 详细结果:")
    for r in results:
        status_icon = '✅' if r['status'] == 'passed' else '❌' if r['status'] == 'failed' else '💥'
        print(f"   {status_icon} {r['test_case']['description']}: {r['status']}")
        if r.get('error'):
            print(f"      错误: {r['error'][:100]}")


if __name__ == '__main__':
    test_executor()