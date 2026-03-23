#!/usr/bin/env python3
"""
Constants - 常量定义
"""

from pathlib import Path

# 版本
VERSION = "2.0.0"

# 输出目录
OUTPUT_BASE_DIR = Path.home() / '.skill-certifier'
TEST_CASES_DIR = OUTPUT_BASE_DIR / 'test-cases'
REPORTS_DIR = OUTPUT_BASE_DIR / 'reports'
RESULTS_DIR = OUTPUT_BASE_DIR / 'results'

# 错误类型
class ErrorType:
    OPENCLAW_NOT_AVAILABLE = 'openclaw_not_available'
    NOT_IMPLEMENTED = 'not_implemented'
    CALL_EXCEPTION = 'call_exception'
    EXECUTION_EXCEPTION = 'execution_exception'
    TIMEOUT = 'timeout'
    SKILL_ERROR = 'skill_error'

# 测试状态
class TestStatus:
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    PASSED = 'passed'
    FAILED = 'failed'
    ERROR = 'error'

# 维度名称映射
DIMENSION_NAMES = {
    'hit_rate': '触发命中率',
    'success_rate': '任务成功率',
    'boundary': '边界测试',
    'exception': '异常处理'
}

# 默认配置
DEFAULT_PARALLEL = 4
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_CASES = 20

# 版本兼容性
MIN_SUPPORTED_VERSION = "2.0.0"
CURRENT_VERSION = VERSION

# 初始化目录
def init_directories():
    """初始化所有输出目录"""
    TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 不自动初始化，由调用方在使用时显式调用
# init_directories()  # 延迟初始化，避免导入时副作用