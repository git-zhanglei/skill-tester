#!/usr/bin/env python3
"""
Test Cases Validator - 验证测试案例集格式
"""

from typing import Dict, Any, Tuple
from constants import MIN_SUPPORTED_VERSION, CURRENT_VERSION


class TestCasesValidator:
    """验证测试案例集的结构和版本"""
    
    REQUIRED_FIELDS = ['version', 'skill_name', 'total', 'cases', 'execution']
    CASE_REQUIRED_FIELDS = ['id', 'dimension', 'type', 'input', 'expected', 'description', 'weight', 'status']
    
    @staticmethod
    def validate(test_cases_data: Dict) -> Tuple[bool, str]:
        """
        验证测试案例集
        
        Returns:
            (is_valid, error_message)
        """
        # 检查必需字段
        for field in TestCasesValidator.REQUIRED_FIELDS:
            if field not in test_cases_data:
                return False, f"缺少必需字段: {field}"
        
        # 检查版本兼容性
        version = test_cases_data.get('version', '0.0.0')
        if not TestCasesValidator._check_version_compatibility(version):
            return False, f"不兼容的版本: {version}，当前支持: >={MIN_SUPPORTED_VERSION}"
        
        # 检查 cases 数组
        cases = test_cases_data.get('cases', [])
        if not isinstance(cases, list):
            return False, "cases 必须是数组"
        
        if len(cases) != test_cases_data.get('total', 0):
            return False, f"cases 数量 ({len(cases)}) 与 total ({test_cases_data.get('total')}) 不匹配"
        
        # 检查每个 case
        for i, case in enumerate(cases):
            is_valid, error = TestCasesValidator._validate_case(case, i)
            if not is_valid:
                return False, error
        
        return True, "验证通过"
    
    @staticmethod
    def _validate_case(case: Dict, index: int) -> Tuple[bool, str]:
        """验证单个测试案例"""
        for field in TestCasesValidator.CASE_REQUIRED_FIELDS:
            if field not in case:
                return False, f"第 {index+1} 个测试案例缺少字段: {field}"
        
        # 检查 status 值
        valid_statuses = ['pending', 'running', 'completed']
        if case['status'] not in valid_statuses:
            return False, f"第 {index+1} 个测试案例的 status 无效: {case['status']}"
        
        # 如果已完成，检查 result
        if case['status'] == 'completed':
            if 'result' not in case:
                return False, f"第 {index+1} 个测试案例已完成但缺少 result"
            
            result = case['result']
            if 'status' not in result:
                return False, f"第 {index+1} 个测试案例的 result 缺少 status"
        
        return True, ""
    
    @staticmethod
    def _check_version_compatibility(version: str) -> bool:
        """检查版本兼容性"""
        try:
            v_parts = [int(x) for x in version.split('.')]
            min_parts = [int(x) for x in MIN_SUPPORTED_VERSION.split('.')]
            
            # 简单比较：主版本必须相同，次版本 >=
            if v_parts[0] != min_parts[0]:
                return False
            if v_parts[1] < min_parts[1]:
                return False
            return True
        except:
            return False
    
    @staticmethod
    def get_info(test_cases_data: Dict) -> Dict[str, Any]:
        """获取测试案例集信息摘要"""
        cases = test_cases_data.get('cases', [])
        
        total = len(cases)
        completed = sum(1 for c in cases if c.get('status') == 'completed')
        passed = sum(1 for c in cases if c.get('result', {}).get('status') == 'passed')
        failed = sum(1 for c in cases if c.get('result', {}).get('status') == 'failed')
        errors = sum(1 for c in cases if c.get('result', {}).get('status') == 'error')
        pending = total - completed
        
        # 按维度统计
        by_dimension = {}
        for case in cases:
            dim = case.get('dimension', 'unknown')
            if dim not in by_dimension:
                by_dimension[dim] = {'total': 0, 'completed': 0, 'passed': 0}
            by_dimension[dim]['total'] += 1
            if case.get('status') == 'completed':
                by_dimension[dim]['completed'] += 1
                if case.get('result', {}).get('status') == 'passed':
                    by_dimension[dim]['passed'] += 1
        
        return {
            'version': test_cases_data.get('version', 'unknown'),
            'skill_name': test_cases_data.get('skill_name', 'unknown'),
            'total': total,
            'pending': pending,
            'completed': completed,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'by_dimension': by_dimension
        }


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("用法: test_cases_validator.py <test-cases-file>")
        sys.exit(1)
    
    from pathlib import Path
    
    test_cases_file = Path(sys.argv[1])
    
    with open(test_cases_file, 'r', encoding='utf-8') as f:
        test_cases_data = json.load(f)
    
    is_valid, error = TestCasesValidator.validate(test_cases_data)
    
    if is_valid:
        print("✅ 测试案例集验证通过")
        info = TestCasesValidator.get_info(test_cases_data)
        print(f"\n信息摘要:")
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(f"❌ 验证失败: {error}")
        sys.exit(1)