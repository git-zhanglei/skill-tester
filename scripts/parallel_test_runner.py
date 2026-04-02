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
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from constants import DEFAULT_TIMEOUT, TestStatus, EARLY_EXIT_THRESHOLD, EARLY_EXIT_REASONS, RESULTS_DIR


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

# 确定性检查规则（不依赖 LLM 判断）
# 返回 (should_apply: bool, passed: bool, reason: str)
DETERMINISTIC_RULES = {
    ('hit_rate', 'exact_match'): {
        'check': 'skill_name_in_output',
        'description': '检查子 Agent 输出中是否提及目标 Skill 的关键操作',
    },
    ('hit_rate', 'negative_test'): {
        'check': 'skill_name_not_in_output',
        'description': '检查子 Agent 输出中不应包含目标 Skill 的特征操作',
    },
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
        self._batch_dir: Optional[Path] = None

    def _get_batch_dir(self) -> Path:
        """获取当前测试批次的 results 子目录，按 {skill_name}-{timestamp} 命名。"""
        if self._batch_dir and self._batch_dir.exists():
            return self._batch_dir

        skill_name = self.data.get('skill_name', 'unknown')
        # 从 cases 文件名提取时间戳（如 test-cases-xxx-20260402.json → 20260402）
        # 或使用 execution.started_at
        batch_id = self.data.get('execution', {}).get('batch_id', '')
        if not batch_id:
            # 从文件名提取日期部分，加上当前时分秒
            now = datetime.now()
            batch_id = f'{skill_name}-{now.strftime("%Y%m%d_%H%M%S")}'
            self.data.setdefault('execution', {})['batch_id'] = batch_id
            self._save()

        batch_dir = RESULTS_DIR / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        self._batch_dir = batch_dir
        return batch_dir

    def _save_agent_output(self, case_id: str, agent_output: str,
                           session_id: str = '', trial: Optional[int] = None,
                           tokens_in: int = 0, tokens_out: int = 0) -> Optional[str]:
        """将子 Agent 的完整输出保存到 results 批次目录下的独立 JSON 文件。"""
        if not agent_output:
            return None

        batch_dir = self._get_batch_dir()
        filename = f'{case_id}_trial{trial}.json' if trial is not None else f'{case_id}.json'
        filepath = batch_dir / filename

        result_data = {
            'case_id': case_id,
            'session_id': session_id,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'agent_output': agent_output,
            'recorded_at': datetime.now().isoformat(),
        }
        if trial is not None:
            result_data['trial'] = trial

        filepath.write_text(
            json.dumps(result_data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        return str(filepath)

    # ─────────────────────────────────────────────
    # 步骤 A：生成执行计划
    # ─────────────────────────────────────────────

    def prepare(self, trials: int = 3, dimension: Optional[str] = None,
                phase: Optional[str] = None) -> Dict[str, Any]:
        """
        为每个 pending 案例生成纯净的任务描述。

        「纯净」的含义：task_description 只包含用户请求，
        不含「测试」「Skill名」「预期结果」等会污染测试的信息。

        Args:
            trials:    multi_trial 案例的重复次数
            dimension: 若指定，只返回该维度的 pending 案例（切片测试）
            phase:     若指定，只返回该 phase 的 pending 案例（phase_a/phase_b/phase_c）
        """
        # 确定目标 phase
        target_phase = phase
        phases = self.data.get('phases')
        if phases and not target_phase:
            target_phase = phases.get('current', 'phase_a')

        # 如果目标 phase 处于 blocked 状态，输出提示并返回空
        if phases and target_phase and target_phase in phases:
            phase_info = phases[target_phase]
            if isinstance(phase_info, dict) and phase_info.get('status') == 'blocked':
                blocked_by = phase_info.get('blocked_by', '')
                return {
                    'cases_file': str(self.cases_file),
                    'skill_name': self.data.get('skill_name', 'unknown'),
                    'total_tasks': 0,
                    'tasks': [],
                    'note': f'阶段 {target_phase} 当前为 blocked 状态（被 {blocked_by} 阻断），'
                            f'请先完成前置阶段后调用 --advance-phase 推进。',
                }

        tasks: List[Dict] = []
        for case in self.data.get('cases', []):
            if case.get('status', TestStatus.PENDING) != TestStatus.PENDING:
                continue  # 跳过已执行或进行中的
            if dimension and case.get('dimension') != dimension:
                continue  # 切片过滤：只返回指定维度
            # phase 过滤：只返回目标 phase 的案例
            if target_phase:
                case_phase = case.get('phase', 'phase_a')
                if case_phase != target_phase:
                    continue

            dim   = case.get('dimension', '')
            typ   = case.get('type', '')
            trial_count = trials if case.get('multi_trial') else 1

            # ── 纯净任务描述：只给用户请求，不暴露测试意图 ──
            task_desc = (
                '你是一个正常工作中的 OpenClaw Agent。请处理以下用户请求：\n\n'
                f'{case.get("input", "")}'
            )

            task_entry = {
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
            }

            # 附加确定性检查规则（如果有）
            det_rule = DETERMINISTIC_RULES.get((dim, typ))
            if det_rule:
                task_entry['deterministic_rule'] = det_rule

            tasks.append(task_entry)

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
               tokens_in: int = 0, tokens_out: int = 0,
               agent_output: str = '') -> Dict[str, Any]:
        """
        记录 Agent 对一个案例的评估结果。

        Args:
            case_id:      案例 ID
            status:       'passed' | 'failed' | 'error'
            outcome:      主 Agent 的评估摘要（一句话总结）
            trial:        多试验序号（multi_trial 案例专用，从 1 开始）
            session_id:   sessions_spawn 返回的会话 ID
            tokens_in:    本次执行消耗的输入 token 数
            tokens_out:   本次执行消耗的输出 token 数
            agent_output: 子 Agent 返回的完整消息文本（保存到 results 目录）

        Returns:
            dict: {"recorded": True/False, "case_id": ..., "status": ..., ...}
        """
        for case in self.data.get('cases', []):
            if case['id'] != case_id:
                continue

            now = datetime.now().isoformat()

            # 保存子 Agent 完整输出到独立文件
            output_path = self._save_agent_output(
                case_id=case_id, agent_output=agent_output,
                session_id=session_id, trial=trial,
                tokens_in=tokens_in, tokens_out=tokens_out,
            )

            if trial is not None:
                # ── Multi-trial：累积 trials 列表 ──
                if 'trials' not in case:
                    case['trials'] = []
                trial_entry = {
                    'trial':   trial,
                    'status':  status,
                    'outcome': outcome,
                    'session_id': session_id,
                    'tokens_in': tokens_in,
                    'tokens_out': tokens_out,
                    'recorded_at': now,
                }
                case['trials'].append(trial_entry)
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
                case['result'] = {
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

        # 计算 skipped 案例（处于 blocked phase 中的案例）
        phases = self.data.get('phases', {})
        skipped_count = 0
        for case in cases:
            case_phase = case.get('phase', 'phase_a')
            if case_phase in phases and isinstance(phases[case_phase], dict):
                if phases[case_phase].get('status') == 'blocked':
                    skipped_count += 1

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
            'skipped_count':   skipped_count,
            'completion_rate': round(len(completed) / len(cases) * 100, 1) if cases else 0.0,
            'pass_rate':       round(passed_n / len(completed) * 100, 1) if completed else 0.0,
            'total_tokens_in':     total_tokens_in,
            'total_tokens_out':    total_tokens_out,
            'avg_tokens_per_case': avg_tokens_per_case,
            'finalized_at':    datetime.now().isoformat(),
        }

        # phases 状态
        if phases:
            summary['phases'] = phases

        # coverage_note
        if skipped_count > 0:
            summary['coverage_note'] = f'部分测试：{skipped_count} 个案例因依赖未就绪被跳过'

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
    # 分阶段执行：推进 & 依赖验证
    # ─────────────────────────────────────────────

    def advance_phase(self) -> Dict[str, Any]:
        """
        推进到下一个阶段：
        1. 检查当前 phase 所有案例是否完成
        2. 完成则标记 completed，检查下一个 phase 前置条件
        3. 满足则推进，不满足则输出阻断原因
        """
        phases = self.data.get('phases')
        if not phases:
            return {'advanced': False, 'reason': 'JSON 中没有 phases 结构'}

        current = phases.get('current', 'phase_a')
        phase_order = ['phase_a', 'phase_b', 'phase_c']

        if current not in phase_order:
            return {'advanced': False, 'reason': f'未知的当前阶段: {current}'}

        current_idx = phase_order.index(current)

        # 检查当前 phase 的案例是否都已完成（phase_b 没有案例，直接跳过检查）
        if current != 'phase_b':
            current_cases = [
                c for c in self.data.get('cases', [])
                if c.get('phase', 'phase_a') == current
            ]
            pending = [c for c in current_cases if c.get('status', 'pending') == 'pending']
            if pending:
                return {
                    'advanced': False,
                    'reason': f'{current} 还有 {len(pending)} 个案例未完成',
                    'pending_ids': [c['id'] for c in pending],
                }

        # 标记当前 phase 为 completed
        if current in phases and isinstance(phases[current], dict):
            phases[current]['status'] = 'completed'

        # 确定下一个 phase
        if current_idx >= len(phase_order) - 1:
            phases['current'] = current  # 已是最后一个
            self._save()
            return {'advanced': False, 'reason': '所有阶段已完成', 'all_completed': True}

        next_phase = phase_order[current_idx + 1]
        next_info = phases.get(next_phase, {})

        # 检查前置条件
        blocked_by = next_info.get('blocked_by', '')
        if blocked_by:
            blocker_info = phases.get(blocked_by, {})
            if isinstance(blocker_info, dict) and blocker_info.get('status') != 'completed':
                self._save()
                return {
                    'advanced': False,
                    'reason': f'{next_phase} 被 {blocked_by} 阻断（状态: {blocker_info.get("status", "unknown")}）',
                }

        # phase_c 额外要求：dependencies.all_verified == true
        if next_phase == 'phase_c':
            deps = self.data.get('dependencies', {})
            if not deps.get('all_verified', False):
                self._save()
                return {
                    'advanced': False,
                    'reason': f'phase_c 要求所有依赖已验证（all_verified=true），当前为 {deps.get("all_verified", False)}',
                }

        # 推进
        if isinstance(next_info, dict):
            next_info['status'] = 'pending'
        phases['current'] = next_phase
        self._save()
        return {'advanced': True, 'from': current, 'to': next_phase}

    def verify_dependency(self, dep_id: str) -> Dict[str, Any]:
        """
        验证单个依赖项：
        1. 从 dependencies.items 中查找
        2. 执行 verify_command（subprocess，timeout 10s）
        3. 检查输出是否包含 verify_expect
        4. 更新 status 并检查 all_verified
        """
        deps = self.data.get('dependencies', {})
        items = deps.get('items', [])

        target = None
        for item in items:
            if item.get('id') == dep_id:
                target = item
                break

        if target is None:
            return {'verified': False, 'error': f'依赖 {dep_id} 未找到'}

        verify_cmd = target.get('verify_command', '')
        verify_expect = target.get('verify_expect', '')

        if not verify_cmd:
            return {'verified': False, 'error': f'依赖 {dep_id} 没有 verify_command'}

        try:
            result = subprocess.run(
                verify_cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            output = result.stdout + result.stderr
            if verify_expect:
                # 支持三种匹配模式：
                # 1. 纯字符串 in 匹配
                # 2. 正则匹配（verify_expect 含 .* 或 \d 等元字符时）
                # 3. JSON 值匹配（如 "ak_configured": true）
                matched = False
                # 先尝试直接包含
                if verify_expect in output:
                    matched = True
                # 再尝试正则
                if not matched:
                    try:
                        if re.search(verify_expect, output):
                            matched = True
                    except re.error:
                        pass
                # 再尝试 JSON 值匹配：将 "key.*true" 转为检查 JSON 中 key=true
                if not matched:
                    try:
                        parsed = json.loads(output.strip()) if output.strip().startswith('{') else None
                        if parsed and isinstance(parsed, dict):
                            # 从 verify_expect 提取 key 和 expected value
                            kv_match = re.match(r'^(\w+).*?(true|false|configured|ok)$',
                                                verify_expect, re.IGNORECASE)
                            if kv_match:
                                key, val = kv_match.group(1), kv_match.group(2).lower()
                                actual = parsed.get(key) if key in parsed else \
                                         parsed.get('data', {}).get(key)
                                if actual is not None:
                                    matched = str(actual).lower() == val
                    except Exception:
                        pass
                target['status'] = 'verified' if matched else 'failed'
            else:
                # 无 verify_expect，命令成功执行即为 verified
                target['status'] = 'verified' if result.returncode == 0 else 'failed'
        except subprocess.TimeoutExpired:
            target['status'] = 'failed'
            output = 'TIMEOUT'
        except Exception as e:
            target['status'] = 'failed'
            output = str(e)

        # 检查是否所有依赖都 verified
        all_verified = all(
            item.get('status') == 'verified' for item in items
        ) if items else False
        deps['all_verified'] = all_verified

        self._save()
        return {
            'dep_id': dep_id,
            'status': target['status'],
            'output': output[:500],
            'all_verified': all_verified,
        }

    def verify_all_deps(self) -> Dict[str, Any]:
        """对所有 unverified 依赖执行验证"""
        deps = self.data.get('dependencies', {})
        items = deps.get('items', [])
        results = []
        for item in items:
            if item.get('status') != 'verified':
                r = self.verify_dependency(item['id'])
                results.append(r)
        return {
            'verified_count': sum(1 for r in results if r.get('status') == 'verified'),
            'failed_count': sum(1 for r in results if r.get('status') == 'failed'),
            'all_verified': deps.get('all_verified', False),
            'details': results,
        }

    def phase_status(self) -> Dict[str, Any]:
        """返回当前 phases 状态"""
        phases = self.data.get('phases', {})
        deps = self.data.get('dependencies', {})
        return {
            'phases': phases,
            'dependencies': {
                'total': len(deps.get('items', [])),
                'verified': sum(1 for i in deps.get('items', []) if i.get('status') == 'verified'),
                'all_verified': deps.get('all_verified', False),
            },
        }

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
    group.add_argument('--advance-phase', action='store_true', help='推进到下一阶段')
    group.add_argument('--verify-dep', metavar='DEP_ID', help='验证单个依赖项')
    group.add_argument('--verify-all-deps', action='store_true', help='验证所有未验证的依赖')
    group.add_argument('--phase-status', action='store_true', help='输出当前 phases 状态')

    # --record 附属参数
    parser.add_argument('--status',  choices=['passed', 'failed', 'error'], help='案例结果状态')
    parser.add_argument('--outcome', default='', help='子 Agent 输出摘要（或用 --outcome-file）')
    parser.add_argument('--outcome-file', type=str, help='从文件读取 outcome（替代 --outcome）')
    parser.add_argument('--agent-output', default='', help='子 Agent 返回的完整消息文本（保存到 results 目录）')
    parser.add_argument('--agent-output-file', type=str, help='从文件读取 agent-output（替代 --agent-output，读取后自动删除临时文件）')
    parser.add_argument('--trial',   type=int,   help='多试验序号（multi_trial 专用）')
    parser.add_argument('--session-id', default='', help='sessions_spawn 返回的会话 ID（必填）')
    parser.add_argument('--tokens-in',  type=int, default=0, help='本次执行消耗的输入 token 数')
    parser.add_argument('--tokens-out', type=int, default=0, help='本次执行消耗的输出 token 数')

    # --prepare 附属参数
    parser.add_argument('--trials', type=int, default=3, help='multi_trial 案例的重复次数（默认 3）')
    parser.add_argument('--dimension', type=str, default=None,
                        help='切片测试：只返回指定维度的 pending 案例（如 hit_rate, execution_success）')
    parser.add_argument('--phase', type=str, default=None,
                        choices=['phase_a', 'phase_b', 'phase_c'],
                        help='按阶段过滤：只返回指定 phase 的 pending 案例')

    args = parser.parse_args()

    try:
        coord = TestCoordinator(args.cases_file)
    except FileNotFoundError as e:
        print(f'❌ {e}', file=sys.stderr)
        return 1

    if args.prepare:
        plan = coord.prepare(trials=args.trials, dimension=args.dimension,
                             phase=args.phase)
        print(json.dumps(plan, ensure_ascii=False, indent=2))

    elif args.record:
        if not args.status:
            print('❌ --record 需要同时提供 --status', file=sys.stderr)
            return 1

        # outcome 可以从 --outcome 或 --outcome-file 获取
        outcome = args.outcome
        if args.outcome_file:
            outcome_path = Path(args.outcome_file)
            if outcome_path.exists():
                outcome = outcome_path.read_text(encoding='utf-8').strip()
            else:
                print(f'❌ --outcome-file 文件不存在: {args.outcome_file}', file=sys.stderr)
                return 1

        if not outcome.strip():
            print('❌ --record 必须提供非空 --outcome 或 --outcome-file', file=sys.stderr)
            return 1

        # session-id 在 error 状态时可选
        if not args.session_id.strip() and args.status != 'error':
            print('❌ --record 必须提供 --session-id（error 状态除外）', file=sys.stderr)
            return 1

        # agent_output 可以从 --agent-output 或 --agent-output-file 获取
        agent_output = args.agent_output
        if args.agent_output_file:
            ao_path = Path(args.agent_output_file)
            if ao_path.exists():
                agent_output = ao_path.read_text(encoding='utf-8').strip()
                # 读取后删除临时文件
                try:
                    ao_path.unlink()
                except OSError:
                    pass
            else:
                print(f'❌ --agent-output-file 文件不存在: {args.agent_output_file}', file=sys.stderr)
                return 1

        result = coord.record(
            case_id=args.record,
            status=args.status,
            outcome=outcome,
            trial=args.trial,
            session_id=args.session_id,
            tokens_in=args.tokens_in,
            tokens_out=args.tokens_out,
            agent_output=agent_output,
        )
        print(json.dumps(result, ensure_ascii=False))
        if not result.get('recorded'):
            return 1

    elif args.finalize:
        summary = coord.finalize()
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    elif args.advance_phase:
        result = coord.advance_phase()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.verify_dep:
        result = coord.verify_dependency(args.verify_dep)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.verify_all_deps:
        result = coord.verify_all_deps()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.phase_status:
        result = coord.phase_status()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == '__main__':
    sys.exit(main())
