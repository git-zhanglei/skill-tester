#!/usr/bin/env python3
"""
Test Coordinator — 配合 Agent 执行测试案例的协调工具

职责：执行计划生成 + 结果记录 + 统计汇总
【重要】实际测试执行（sessions_spawn）必须由 OpenClaw Agent 发起，
        本脚本不调用 sessions_spawn——那是 Tool，不是 Python 库。

用法：
  # 步骤 A：生成执行计划（Agent 用来获取纯净任务描述）
  python3 parallel_test_runner.py <cases_json> --prepare [--trials 3]

  # 步骤 B：Agent 每完成一个案例后，记录结果
  python3 parallel_test_runner.py <cases_json> --record <case_id> \\
      --status passed|failed|error [--outcome "输出摘要"] [--trial 1]

  # 步骤 C：所有案例执行完毕，生成汇总
  python3 parallel_test_runner.py <cases_json> --finalize
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from constants import DEFAULT_TIMEOUT, DEFAULT_PARALLEL, TestStatus, EARLY_EXIT_THRESHOLD, EARLY_EXIT_REASONS


# ─────────────────────────────────────────────────────────
# 评估提示语（告知 Agent 对每类案例如何评判）
# ─────────────────────────────────────────────────────────
EVALUATION_HINTS = {
    ('hit_rate', 'exact_match'):   '检查：子 Agent 的输出是否表明目标 Skill 被激活？',
    ('hit_rate', 'fuzzy_match'):   '检查：语义变体触发时，目标 Skill 是否被激活？',
    ('hit_rate', 'negative_test'): '检查：无关输入时，目标 Skill 是否正确地「未激活」？',
    ('agent_comprehension', 'outcome_check'): '检查：输出的实际结果是否符合 Skill 声明的预期产物？',
    ('agent_comprehension', 'format_check'):  '检查：输出格式是否符合 Skill 声明的格式规范？',
    ('execution_success', 'normal_path'):     '检查：正常输入下任务是否成功完成？',
    ('execution_success', 'boundary_case'):   '检查：边界输入是否被正确处理而不崩溃？',
    ('execution_success', 'error_handling'):  '检查：错误场景是否有清晰的错误提示？',
    ('execution_success', 'adversarial'):     '检查：越权/歧义/恶意输入是否被拒绝并给出说明？',
    ('execution_success', 'idempotency_check'): '检查：两次执行相同操作，结果是否一致？',
}


class TestCoordinator:
    """
    测试执行协调器

    只负责数据管理；不调用 sessions_spawn。
    sessions_spawn 由 OpenClaw Agent 直接调用。
    """

    def __init__(self, cases_file: str):
        self.cases_file = Path(cases_file)
        if not self.cases_file.exists():
            raise FileNotFoundError(f'测试案例文件不存在: {cases_file}')
        self.data: Dict[str, Any] = json.loads(self.cases_file.read_text(encoding='utf-8'))

    # ─────────────────────────────────────────────
    # 步骤 A：生成执行计划
    # ─────────────────────────────────────────────

    def prepare(self, trials: int = 3, dimension: Optional[str] = None) -> Dict[str, Any]:
        """
        为每个 pending 案例生成纯净的任务描述。

        「纯净」的含义：task_description 只包含用户请求，
        不含「测试」「Skill名」「预期结果」等会污染测试的信息。

        Args:
            trials:    multi_trial 案例的重复次数
            dimension: 若指定，只返回该维度的 pending 案例（切片测试）
        """
        tasks: List[Dict] = []
        for case in self.data.get('cases', []):
            if case.get('status', TestStatus.PENDING) != TestStatus.PENDING:
                continue  # 跳过已执行或进行中的
            if dimension and case.get('dimension') != dimension:
                continue  # 切片过滤：只返回指定维度

            dim   = case.get('dimension', '')
            typ   = case.get('type', '')
            trial_count = trials if case.get('multi_trial') else 1

            # ── 纯净任务描述：只给用户请求，不暴露测试意图 ──
            task_desc = (
                '你是一个正常工作中的 OpenClaw Agent。请处理以下用户请求：\n\n'
                f'{case.get("input", "")}'
            )

            tasks.append({
                'case_id':        case['id'],
                'dimension':      dim,
                'type':           typ,
                'grader_type':    case.get('grader_type', 'llm_rubric'),
                'multi_trial':    case.get('multi_trial', False),
                'trial_count':    trial_count,
                'task_description': task_desc,
                'expected':       case.get('expected'),
                'description':    case.get('description', ''),
                'evaluation_hint': EVALUATION_HINTS.get((dim, typ), '评估输出是否符合预期'),
            })

        multi_trial_count = sum(1 for t in tasks if t['multi_trial'])
        plan = {
            'cases_file':         str(self.cases_file),
            'skill_name':         self.data.get('skill_name', 'unknown'),
            'total_tasks':        len(tasks),
            'single_trial_tasks': len(tasks) - multi_trial_count,
            'multi_trial_tasks':  multi_trial_count,
            'default_trials':     trials,
            'tasks':              tasks,
            'note': (
                '重要：sessions_spawn 由 Agent 调用，传入 task_description；'
                '子 Agent 执行完成后，由主 Agent 对比实际输出与 expected 评估结果，'
                '再调用 --record 记录。'
            ),
        }
        return plan

    # ─────────────────────────────────────────────
    # 步骤 B：记录单条结果
    # ─────────────────────────────────────────────

    def record(self, case_id: str, status: str, outcome: str = '',
               trial: Optional[int] = None, session_id: str = '',
               tokens_in: int = 0, tokens_out: int = 0) -> Dict[str, Any]:
        """
        记录 Agent 对一个案例的评估结果。

        Args:
            case_id:    案例 ID
            status:     'passed' | 'failed' | 'error'
            outcome:    子 Agent 实际输出摘要（可选）
            trial:      多试验序号（multi_trial 案例专用，从 1 开始）
            tokens_in:  本次执行消耗的输入 token 数
            tokens_out: 本次执行消耗的输出 token 数

        Returns:
            dict: {"recorded": True/False, "case_id": ..., "status": ..., ...}
        """
        for case in self.data.get('cases', []):
            if case['id'] != case_id:
                continue

            now = datetime.now().isoformat()

            if trial is not None:
                # ── Multi-trial：累积 trials 列表 ──
                if 'trials' not in case:
                    case['trials'] = []
                case['trials'].append({
                    'trial':   trial,
                    'status':  status,
                    'outcome': outcome,
                    'session_id': session_id,
                    'tokens_in': tokens_in,
                    'tokens_out': tokens_out,
                    'recorded_at': now,
                })
                expected_trials = case.get('trial_count', 3)
                if len(case['trials']) >= expected_trials:
                    all_statuses = [t['status'] for t in case['trials']]
                    agg_status = (
                        TestStatus.PASSED
                        if any(s == TestStatus.PASSED for s in all_statuses)
                        else TestStatus.FAILED
                    )
                    case['status']       = TestStatus.COMPLETED
                    case['completed_at'] = now
                    case['result']       = {
                        'status':  agg_status,
                        'outcome': outcome,
                        'session_id': session_id,
                        'pass_at_k': sum(1 for s in all_statuses if s == TestStatus.PASSED),
                        'k':         expected_trials,
                        'tokens_in': sum(t.get('tokens_in', 0) for t in case['trials']),
                        'tokens_out': sum(t.get('tokens_out', 0) for t in case['trials']),
                    }
            else:
                # ── Single-trial ──
                case['status']       = TestStatus.COMPLETED
                case['completed_at'] = now
                case['result']       = {
                    'status': status,
                    'outcome': outcome,
                    'session_id': session_id,
                    'tokens_in': tokens_in,
                    'tokens_out': tokens_out,
                }

            self._save()

            result = {'recorded': True, 'case_id': case_id, 'status': status}

            # 实时早期终止检测
            completed = [c for c in self.data.get('cases', []) if c.get('status') == TestStatus.COMPLETED]
            early_exit = self._detect_early_exit(completed)
            if early_exit:
                # 在 JSON 中标记，Agent 下次 --prepare 或读取时能看到
                self.data.setdefault('execution', {})['early_exit_recommended'] = True
                self.data['execution']['early_exit_reason'] = early_exit
                self._save()
                result['early_exit_recommended'] = True
                result['early_exit_reason'] = early_exit

            return result

        return {'recorded': False, 'error': 'case_id not found'}  # case_id not found

    # ─────────────────────────────────────────────
    # 步骤 C：汇总并保存
    # ─────────────────────────────────────────────

    def finalize(self) -> Dict[str, Any]:
        """计算执行统计，更新 cases JSON 并返回摘要。"""
        cases     = self.data.get('cases', [])
        completed = [c for c in cases if c.get('status') == TestStatus.COMPLETED]
        passed_n  = sum(1 for c in completed if self._is_passed(c))
        failed_n  = len(completed) - passed_n
        pending_n = sum(1 for c in cases if c.get('status') == TestStatus.PENDING)

        # Token 汇总统计
        total_tokens_in  = sum((c.get('result') or {}).get('tokens_in', 0) for c in completed)
        total_tokens_out = sum((c.get('result') or {}).get('tokens_out', 0) for c in completed)
        avg_tokens_per_case = (
            round((total_tokens_in + total_tokens_out) / len(completed))
            if completed else 0
        )

        summary = {
            'total':           len(cases),
            'completed':       len(completed),
            'passed':          passed_n,
            'failed':          failed_n,
            'pending':         pending_n,
            'completion_rate': round(len(completed) / len(cases) * 100, 1) if cases else 0.0,
            'pass_rate':       round(passed_n / len(completed) * 100, 1) if completed else 0.0,
            'total_tokens_in':     total_tokens_in,
            'total_tokens_out':    total_tokens_out,
            'avg_tokens_per_case': avg_tokens_per_case,
            'finalized_at':    datetime.now().isoformat(),
        }

        # 早期终止检测：最近连续 N 个案例是否因同一根因失败
        early_exit = self._detect_early_exit(completed)
        if early_exit:
            summary['early_exit_recommended'] = True
            summary['early_exit_reason'] = early_exit

        exec_info = self.data.setdefault('execution', {})
        exec_info['status']     = 'completed' if not pending_n else 'partial'
        exec_info['summary']    = summary
        exec_info['total']      = summary['total']
        exec_info['passed']     = summary['passed']
        exec_info['failed']     = summary['failed']
        exec_info['duration_seconds'] = self._calc_duration()

        self._save()
        return summary

    # ─────────────────────────────────────────────
    # 工具方法
    # ─────────────────────────────────────────────

    def _is_passed(self, case: Dict) -> bool:
        if case.get('multi_trial') and case.get('trials'):
            return any(t.get('status') == TestStatus.PASSED for t in case['trials'])
        return (case.get('result') or {}).get('status') == TestStatus.PASSED

    def _detect_early_exit(self, completed: List[Dict]) -> Optional[str]:
        """检测是否应建议早期终止（最近连续 N 个案例因同一根因失败）"""
        if len(completed) < EARLY_EXIT_THRESHOLD:
            return None

        # 取最近 N 个已完成案例
        recent = completed[-EARLY_EXIT_THRESHOLD:]
        # 全部为 failed/error 才触发
        if not all(not self._is_passed(c) for c in recent):
            return None

        # 检查 outcome 中是否包含相似关键词
        outcomes = [
            (c.get('result') or {}).get('outcome', '') for c in recent
        ]
        for reason_key, keywords in EARLY_EXIT_REASONS.items():
            if all(
                any(kw in outcome for kw in keywords)
                for outcome in outcomes
            ):
                return reason_key

        return '连续失败（根因未分类）'

    def _calc_duration(self) -> float:
        exec_info = self.data.get('execution', {})
        start = exec_info.get('started_at')
        if not start:
            return 0.0
        try:
            from datetime import datetime as _dt
            return (_dt.now() - _dt.fromisoformat(start)).total_seconds()
        except Exception:
            return 0.0

    def _save(self) -> None:
        self.cases_file.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )


# ─────────────────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Test Coordinator — 配合 Agent 执行测试',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 生成执行计划
  python3 parallel_test_runner.py cases.json --prepare

  # 记录单次结果
  python3 parallel_test_runner.py cases.json --record hit_exact_0 --status passed \\
      --outcome "输出..." --session-id "session-123"

  # 记录多试验中的某次
  python3 parallel_test_runner.py cases.json --record hit_exact_0 --status passed \\
      --outcome "输出..." --session-id "session-123" --trial 2

  # 生成汇总
  python3 parallel_test_runner.py cases.json --finalize
''')
    parser.add_argument('cases_file', help='测试案例 JSON 文件路径')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',  action='store_true', help='生成执行计划')
    group.add_argument('--record',   metavar='CASE_ID',   help='记录单个案例结果')
    group.add_argument('--finalize', action='store_true', help='生成执行摘要')

    # --record 附属参数
    parser.add_argument('--status',  choices=['passed', 'failed', 'error'], help='案例结果状态')
    parser.add_argument('--outcome', default='', help='子 Agent 输出摘要（必填，建议包含原始输出摘要）')
    parser.add_argument('--trial',   type=int,   help='多试验序号（multi_trial 专用）')
    parser.add_argument('--session-id', default='', help='sessions_spawn 返回的会话 ID（必填）')
    parser.add_argument('--tokens-in',  type=int, default=0, help='本次执行消耗的输入 token 数')
    parser.add_argument('--tokens-out', type=int, default=0, help='本次执行消耗的输出 token 数')

    # --prepare 附属参数
    parser.add_argument('--trials', type=int, default=3, help='multi_trial 案例的重复次数（默认 3）')
    parser.add_argument('--dimension', type=str, default=None,
                        help='切片测试：只返回指定维度的 pending 案例（如 hit_rate, execution_success）')

    args = parser.parse_args()

    try:
        coord = TestCoordinator(args.cases_file)
    except FileNotFoundError as e:
        print(f'❌ {e}', file=sys.stderr)
        return 1

    if args.prepare:
        plan = coord.prepare(trials=args.trials, dimension=args.dimension)
        print(json.dumps(plan, ensure_ascii=False, indent=2))

    elif args.record:
        if not args.status:
            print('❌ --record 需要同时提供 --status', file=sys.stderr)
            return 1
        if not args.outcome.strip():
            print('❌ --record 必须提供非空 --outcome，禁止空结果写入', file=sys.stderr)
            return 1
        if not args.session_id.strip():
            print('❌ --record 必须提供 --session-id（来自 sessions_spawn 结果）', file=sys.stderr)
            return 1
        result = coord.record(
            case_id=args.record,
            status=args.status,
            outcome=args.outcome,
            trial=args.trial,
            session_id=args.session_id,
            tokens_in=args.tokens_in,
            tokens_out=args.tokens_out,
        )
        print(json.dumps(result, ensure_ascii=False))
        if not result.get('recorded'):
            return 1

    elif args.finalize:
        summary = coord.finalize()
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == '__main__':
    sys.exit(main())
