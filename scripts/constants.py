#!/usr/bin/env python3
"""
Constants - 常量定义
"""

from pathlib import Path

# 版本
VERSION = "3.0.0"
MIN_SUPPORTED_VERSION = "3.0"
CURRENT_VERSION       = VERSION  # 别名，保持向后兼容

# 输出目录（相对于当前工作目录，由 Agent 在运行时决定路径）
OUTPUT_BASE_DIR = Path.home() / '.skill-tester'
TEST_CASES_DIR = OUTPUT_BASE_DIR / 'test-cases'
REPORTS_DIR    = OUTPUT_BASE_DIR / 'reports'
RESULTS_DIR    = OUTPUT_BASE_DIR / 'results'

# 测试状态
class TestStatus:
    PENDING   = 'pending'
    RUNNING   = 'running'
    COMPLETED = 'completed'
    PASSED    = 'passed'
    FAILED    = 'failed'
    ERROR     = 'error'

# 错误类型
class ErrorType:
    OPENCLAW_NOT_AVAILABLE = 'openclaw_not_available'
    CALL_EXCEPTION         = 'call_exception'
    EXECUTION_EXCEPTION    = 'execution_exception'
    TIMEOUT                = 'timeout'
    SKILL_ERROR            = 'skill_error'

# V3 维度名称映射
DIMENSION_NAMES = {
    'hit_rate':            '触发命中率',
    'spec_compliance':     'Skill规范程度',
    'agent_comprehension': 'Agent理解度',
    'execution_success':   '执行成功率',
}

# V3 测试类型映射
TEST_TYPE_NAMES = {
    # hit_rate 维度
    'exact_match':   '精确触发',
    'fuzzy_match':   '模糊触发',
    'negative_test': '负面测试',
    # agent_comprehension 维度
    'outcome_check': '结果检验',
    'format_check':  '格式检验',
    # execution_success 维度
    'normal_path':    '正常路径',
    'boundary_case':  '边界条件',
    'error_handling': '异常处理',
    'adversarial':    '对抗性测试',
}

# V3 维度权重
DIMENSION_WEIGHTS = {
    'hit_rate':            0.25,
    'spec_compliance':     0.20,
    'agent_comprehension': 0.25,
    'execution_success':   0.30,
}

# 默认执行配置
DEFAULT_PARALLEL  = 4
DEFAULT_TIMEOUT   = 120
DEFAULT_MAX_CASES = 30   # 与 SKILL.md "质量优先，总数≤30" 一致

# 早期终止配置
EARLY_EXIT_THRESHOLD = 3  # 连续同因失败 N 次则建议终止

# 已知根因分类（用于早期终止检测）
EARLY_EXIT_REASONS = {
    'skill_not_activated': ['未触发', 'Skill未被激活', 'not_activate', '未激活', '没有触发'],
    'timeout':            ['超时', 'timeout', 'timed out', 'TIMEOUT'],
    'spawn_unavailable':  ['sessions_spawn', '不可用', 'unavailable', '无法调用'],
    'dependency_missing': ['依赖缺失', '环境变量未设置', 'API Key', '网络不可达', '权限不足'],
}

# 评分阈值
SCORE_EXCELLENT = 90
SCORE_GOOD      = 70
SCORE_ACCEPTABLE = 40


def init_directories():
    """初始化所有输出目录（延迟调用，避免导入时副作用）"""
    TEST_CASES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
