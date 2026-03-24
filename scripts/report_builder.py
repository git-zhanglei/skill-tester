#!/usr/bin/env python3
"""
Report Builder — 基于统一 results JSON 生成认证报告

输入 JSON 格式（由 Agent 在步骤 5 生成）：
{
  "version": "3.0",
  "skill_name": "my-skill",
  "skill_path": "...",
  "generated_at": "...",
  "safety": { "status": "passed/warning/failed", "issues": [], "warnings": [] },
  "spec_score": 85.0,
  "cases": [
    { "id": "...", "dimension": "...", "type": "...",
      "multi_trial": false,         # 可选，true 时有 trials 数组
      "trials": [                   # 多试验结果（可选）
        { "trial": 1, "status": "passed", "outcome": "...", "matches_expected": true }
      ],
      "status": "completed",
      "result": { "status": "passed/failed/error", "outcome": "...", "failure_reason": null } }
  ],
  "execution": { "total": 20, "passed": 18, "failed": 2, "duration_seconds": 45.3 }
}
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from constants import (
    DIMENSION_NAMES, DIMENSION_WEIGHTS,
    SCORE_EXCELLENT, SCORE_GOOD, SCORE_ACCEPTABLE
)


class ReportBuilder:
    """基于 results JSON 构建认证报告"""

    def __init__(self, results: Dict[str, Any]):
        self.results    = results
        self.skill_name = results.get('skill_name', 'unknown')
        self.safety     = results.get('safety', {'status': 'unknown', 'issues': [], 'warnings': []})
        self.spec_score = float(results.get('spec_score', 0.0))
        self.cases      = results.get('cases', [])
        self.execution  = results.get('execution', {})
        self._scores: Optional[Dict[str, float]] = None

    # ──────────────────────────────────────────────
    # 维度得分计算
    # ──────────────────────────────────────────────

    def compute_scores(self) -> Dict[str, float]:
        """计算四个维度得分，返回 dict，值域 0–100"""
        if self._scores is not None:
            return self._scores

        hit   = self._score_hit_rate()
        spec  = self.spec_score
        comp  = self._score_agent_comprehension()
        exec_ = self._score_execution_success()
        overall = hit * 0.25 + spec * 0.20 + comp * 0.25 + exec_ * 0.30

        if self.safety.get('status') == 'failed':
            overall = 0.0

        self._scores = {
            'hit_rate':            round(hit,     1),
            'spec_compliance':     round(spec,    1),
            'agent_comprehension': round(comp,    1),
            'execution_success':   round(exec_,   1),
            'overall':             round(overall, 1),
        }
        return self._scores

    def compute_reliability(self) -> Dict[str, Any]:
        """计算 pass@k / pass^k（仅 multi_trial 案例）"""
        multi = [c for c in self.cases if c.get('multi_trial') and c.get('trials')]
        if not multi:
            return {'available': False, 'pass_at_k': None, 'pass_k': None, 'k': None}

        k_set = set(len(c['trials']) for c in multi)
        k = max(k_set) if k_set else 3

        pass_at_k_count = 0
        pass_k_count    = 0
        for case in multi:
            trials = case['trials']
            statuses = [t.get('status', 'error') for t in trials]
            if any(s == 'passed' for s in statuses):
                pass_at_k_count += 1
            if all(s == 'passed' for s in statuses):
                pass_k_count += 1

        total = len(multi)
        return {
            'available': True,
            'k':         k,
            'total_critical_cases': total,
            'pass_at_k': round(pass_at_k_count / total * 100, 1) if total else 0.0,
            'pass_k':    round(pass_k_count    / total * 100, 1) if total else 0.0,
        }

    def _cases_by(self, dimension: str, type_: Optional[str] = None) -> List[Dict]:
        return [
            c for c in self.cases
            if c.get('dimension') == dimension
            and c.get('status') == 'completed'
            and (type_ is None or c.get('type') == type_)
        ]

    def _is_passed(self, case: Dict) -> bool:
        """判断案例是否通过（支持 multi_trial）"""
        if case.get('multi_trial') and case.get('trials'):
            return any(t.get('status') == 'passed' for t in case['trials'])
        return case.get('result', {}).get('status') == 'passed'

    def _score_hit_rate(self) -> float:
        exact    = self._cases_by('hit_rate', 'exact_match')
        fuzzy    = self._cases_by('hit_rate', 'fuzzy_match')
        negative = self._cases_by('hit_rate', 'negative_test')

        w_e = len(exact) * 0.4
        w_f = len(fuzzy) * 0.4
        w_n = len(negative) * 0.2
        total_w = w_e + w_f + w_n
        if total_w == 0:
            return 0.0

        p_e = sum(1 for c in exact    if self._is_passed(c))
        p_f = sum(1 for c in fuzzy    if self._is_passed(c))
        p_n = sum(1 for c in negative if self._is_passed(c))
        return (p_e * 0.4 + p_f * 0.4 + p_n * 0.2) / total_w * 100

    def _score_agent_comprehension(self) -> float:
        outcome = self._cases_by('agent_comprehension', 'outcome_check')
        fmt     = self._cases_by('agent_comprehension', 'format_check')
        # 向后兼容旧的 step_following / output_format 类型
        step    = self._cases_by('agent_comprehension', 'step_following')
        old_fmt = self._cases_by('agent_comprehension', 'output_format')
        all_    = outcome + fmt + step + old_fmt
        if not all_:
            return 100.0
        passed = sum(1 for c in all_ if self._is_passed(c))
        return passed / len(all_) * 100

    def _score_execution_success(self) -> float:
        normal     = self._cases_by('execution_success', 'normal_path')
        boundary   = self._cases_by('execution_success', 'boundary_case')
        error_h    = self._cases_by('execution_success', 'error_handling')
        adversarial = self._cases_by('execution_success', 'adversarial')

        w_n = len(normal)      * 0.40
        w_b = len(boundary)    * 0.25
        w_e = len(error_h)     * 0.20
        w_a = len(adversarial) * 0.15
        total_w = w_n + w_b + w_e + w_a
        if total_w == 0:
            return 0.0

        p_n = sum(1 for c in normal      if self._is_passed(c))
        p_b = sum(1 for c in boundary    if self._is_passed(c))
        p_e = sum(1 for c in error_h     if self._is_passed(c))
        p_a = sum(1 for c in adversarial if self._is_passed(c))
        return (p_n * 0.40 + p_b * 0.25 + p_e * 0.20 + p_a * 0.15) / total_w * 100

    # ──────────────────────────────────────────────
    # 评级与认证
    # ──────────────────────────────────────────────

    def get_rating(self) -> str:
        scores  = self.compute_scores()
        overall = scores['overall']

        if self.safety.get('status') == 'failed':
            return '❌ 不合格'

        min_dim = min(
            scores['hit_rate'], scores['spec_compliance'],
            scores['agent_comprehension'], scores['execution_success']
        )
        if min_dim < SCORE_ACCEPTABLE:
            return '⭐⭐⭐ 可接受（单维度不达标）'

        if overall >= SCORE_EXCELLENT:
            return '⭐⭐⭐⭐⭐ 优秀'
        if overall >= SCORE_GOOD:
            return '⭐⭐⭐⭐ 良好'
        if overall >= SCORE_ACCEPTABLE:
            return '⭐⭐⭐ 可接受'
        return '⭐⭐ 需改进'

    def get_badge(self) -> str:
        overall = self.compute_scores()['overall']
        if self.safety.get('status') == 'failed':
            return '—'
        if overall >= SCORE_EXCELLENT:
            return '🏆 Certified'
        if overall >= SCORE_GOOD:
            return '✅ Verified'
        return '🔄 Beta'

    # ──────────────────────────────────────────────
    # P0/P1/P2 优先级推荐
    # ──────────────────────────────────────────────

    def get_recommendations(self) -> List[Dict[str, str]]:
        """返回带 P0/P1/P2 优先级的推荐列表"""
        scores   = self.compute_scores()
        rel      = self.compute_reliability()
        recs: List[Dict[str, str]] = []

        def add(priority: str, message: str):
            recs.append({'priority': priority, 'message': message})

        # P0 — 必须修复
        if self.safety.get('status') == 'failed':
            add('P0', '安全检查失败，必须修复所有安全问题后才能发布')
        if scores['overall'] < SCORE_ACCEPTABLE:
            add('P0', f'综合评分 {scores["overall"]:.1f} 低于最低要求（40），Skill 不具备发布条件')
        for dim_key, label in [
            ('hit_rate',            '触发命中率'),
            ('spec_compliance',     'Skill规范程度'),
            ('agent_comprehension', 'Agent理解度'),
            ('execution_success',   '执行成功率'),
        ]:
            s = scores[dim_key]
            if s < SCORE_ACCEPTABLE:
                add('P0', f'{label}得分 {s:.1f} 低于 40，整体评级受限，优先修复')

        # P1 — 发布前应修复
        if self.safety.get('status') == 'warning':
            add('P1', '存在安全警告，建议在发布前消除')
        for dim_key, label, tip in [
            ('hit_rate',            '触发命中率',  '优化 description 的触发词描述，增加变体示例'),
            ('spec_compliance',     'Skill规范程度', '检查 frontmatter、行数、代码示例和结构'),
            ('agent_comprehension', 'Agent理解度',  '明确声明预期输出格式或结果，而非仅描述步骤'),
            ('execution_success',   '执行成功率',   '优先修复正常路径失败案例，再处理边界和异常'),
        ]:
            s = scores[dim_key]
            if SCORE_ACCEPTABLE <= s < SCORE_GOOD:
                add('P1', f'{label}得分 {s:.1f}（40–70），{tip}')

        if rel['available'] and rel['pass_k'] is not None and rel['pass_k'] < 50:
            add('P1', f'pass^3 可靠性仅 {rel["pass_k"]:.0f}%（<50%），Skill 行为不稳定，建议排查非确定性原因')

        # P2 — 持续改进
        for dim_key, label in [
            ('hit_rate',            '触发命中率'),
            ('agent_comprehension', 'Agent理解度'),
            ('execution_success',   '执行成功率'),
        ]:
            s = scores[dim_key]
            if SCORE_GOOD <= s < 85:
                add('P2', f'{label}得分 {s:.1f}（70–85），有提升空间')

        if rel['available'] and rel['pass_k'] is not None and 50 <= rel['pass_k'] < 80:
            add('P2', f'pass^3 可靠性 {rel["pass_k"]:.0f}%（50–80%），进一步提升稳定性')

        # 按优先级排序，P0 在前
        order = {'P0': 0, 'P1': 1, 'P2': 2}
        recs.sort(key=lambda r: order.get(r['priority'], 9))
        return recs[:8]  # 最多 8 条

    # ──────────────────────────────────────────────
    # 报告生成
    # ──────────────────────────────────────────────

    def build_markdown(self) -> str:
        scores  = self.compute_scores()
        rel     = self.compute_reliability()
        rating  = self.get_rating()
        badge   = self.get_badge()
        ts      = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total   = self.execution.get('total', len(self.cases))
        passed  = self.execution.get('passed', 0)
        failed  = self.execution.get('failed', 0)
        dur     = self.execution.get('duration_seconds', 0)

        safety_icon = {'passed': '✅ 通过', 'warning': '⚠️ 警告', 'failed': '❌ 失败'}.get(
            self.safety.get('status', ''), '？ 未知')

        rel_line = ''
        if rel['available']:
            rel_line = f"  可靠性: pass@{rel['k']}={rel['pass_at_k']:.0f}%  pass^{rel['k']}={rel['pass_k']:.0f}%"

        lines = [
            f'# Skill 认证报告：{self.skill_name}',
            '',
            f'**生成时间：** {ts}',
            f'**Skill 路径：** {self.results.get("skill_path", "—")}',
            '',
            '## 执行摘要',
            '',
            '```',
            f'╔════════════════════════════════════════════════════╗',
            f'║  {self.skill_name[:46]:<46}  ║',
            f'╠════════════════════════════════════════════════════╣',
            f'║  安全检查:     {safety_icon:<38}║',
            f'║  触发命中率:   {scores["hit_rate"]:>5.1f}%  (×25%)                        ║',
            f'║  Skill规范:    {scores["spec_compliance"]:>5.1f}%  (×20%)                        ║',
            f'║  Agent理解度:  {scores["agent_comprehension"]:>5.1f}%  (×25%)  [结果评估]          ║',
            f'║  执行成功率:   {scores["execution_success"]:>5.1f}%  (×30%)                        ║',
            f'║  综合评分:     {scores["overall"]:>5.1f}/100  {rating:<28}║',
            f'╠════════════════════════════════════════════════════╣',
            f'║  测试案例: {total:<4} 通过: {passed:<4} 失败: {failed:<4} 耗时: {dur:.0f}s      ║',
        ]
        if rel_line:
            lines.append(f'║ {rel_line:<52}║')
        lines += [
            f'║  认证状态: {badge:<42}║',
            f'╚════════════════════════════════════════════════════╝',
            '```',
            '',
        ]

        # 安全详情
        lines += ['## 安全检查', '']
        if self.safety.get('issues'):
            lines += ['### ❌ 严重问题', '']
            for issue in self.safety['issues']:
                lines.append(f'- {issue}')
            lines.append('')
        if self.safety.get('warnings'):
            lines += ['### ⚠️ 警告', '']
            for w in self.safety['warnings']:
                lines.append(f'- {w}')
            lines.append('')
        if not self.safety.get('issues') and not self.safety.get('warnings'):
            lines += ['✅ 未发现安全问题', '']

        # 可靠性（pass@k）
        if rel['available']:
            k = rel['k']
            lines += [
                '## 可靠性分析（pass@k）',
                '',
                f'Critical 案例（exact_match + normal_path）运行 {k} 次的统计结果：',
                '',
                f'| 指标 | 值 | 含义 |',
                f'|------|-----|------|',
                f'| pass@{k} | {rel["pass_at_k"]:.0f}% | 至少 1 次通过（能力验证） |',
                f'| pass^{k} | {rel["pass_k"]:.0f}% | 全部通过（可靠性验证） |',
                '',
            ]
            if rel['pass_k'] < 50:
                lines.append('> ⚠️ pass^k 低于 50%，建议在生产前提升 Skill 确定性。\n')

        # 各维度详情
        lines += ['## 维度详情', '']
        dim_order = [
            ('hit_rate',            '触发命中率 (×25%)'),
            ('spec_compliance',     'Skill规范程度 (×20%)'),
            ('agent_comprehension', 'Agent理解度 (×25%)'),
            ('execution_success',   '执行成功率 (×30%)'),
        ]
        for dim_key, dim_label in dim_order:
            dim_cases = [c for c in self.cases if c.get('dimension') == dim_key]
            completed = [c for c in dim_cases if c.get('status') == 'completed']
            passed_n  = sum(1 for c in completed if self._is_passed(c))
            score_val = scores.get(dim_key, 0.0)

            if dim_key == 'spec_compliance':
                lines += [f'### {dim_label}', '', f'**得分：{score_val:.1f}/100**（静态分析，不涉及测试案例）', '']
                continue

            lines += [
                f'### {dim_label}',
                '',
                f'**得分：{score_val:.1f}/100**  |  案例：{len(completed)}/{len(dim_cases)}  |  通过：{passed_n}',
                '',
                '| 状态 | 类型 | 描述 | 输入 | 可靠性 |',
                '|------|------|------|------|--------|',
            ]
            for c in dim_cases:
                passed_flag = self._is_passed(c) if c.get('status') == 'completed' else False
                r_status = 'passed' if passed_flag else (
                    c.get('result', {}).get('status', 'pending') if c.get('status') == 'completed' else '—'
                )
                icon = {'passed': '✅', 'failed': '❌', 'error': '💥'}.get(r_status, '⏳')
                desc = (c.get('description') or '')[:30]
                inp  = str(c.get('input', ''))[:30]
                # 多试验可靠性
                if c.get('multi_trial') and c.get('trials'):
                    k2 = len(c['trials'])
                    p_all = all(t.get('status') == 'passed' for t in c['trials'])
                    rel_str = f'pass^{k2}={"✅" if p_all else "❌"}'
                else:
                    rel_str = '—'
                lines.append(f'| {icon} | {c.get("type","—")} | {desc} | {inp} | {rel_str} |')
            lines.append('')

        # 失败详情
        failed_cases = [
            c for c in self.cases
            if c.get('status') == 'completed' and not self._is_passed(c)
        ]
        if failed_cases:
            lines += ['## 失败详情', '']
            for c in failed_cases[:10]:  # 最多展示 10 个
                r = c.get('result', {})
                lines += [
                    f'### [{c.get("id")}] {c.get("description","")}',
                    '',
                    f'- **输入：** `{c.get("input","")}`',
                    f'- **预期：** {c.get("expected","")}',
                    f'- **状态：** {r.get("status","")}',
                ]
                if r.get('outcome'):
                    lines.append(f'- **实际产物：** {r["outcome"]}')
                if r.get('failure_reason'):
                    lines.append(f'- **失败原因：** {r["failure_reason"]}')
                lines.append('')

        # P0/P1/P2 优化建议
        recs = self.get_recommendations()
        lines += ['## 优化建议', '']
        if recs:
            lines += [
                '| 优先级 | 建议 |',
                '|--------|------|',
            ]
            for r in recs:
                p = r['priority']
                icon_map = {'P0': '🔴 P0', 'P1': '🟡 P1', 'P2': '🟢 P2'}
                lines.append(f'| {icon_map.get(p, p)} | {r["message"]} |')
        else:
            lines.append('✅ 所有维度表现良好，暂无优化建议。')
        lines.append('')

        return '\n'.join(lines)

    # ──────────────────────────────────────────────
    # EVAL.md（随 Skill 版本管理的评估摘要）
    # ──────────────────────────────────────────────

    def build_eval_md(self) -> str:
        """
        生成写入 <skill_path>/EVAL.md 的评估摘要。
        精简版，不含失败详情，方便随 Skill 代码版本管理。
        参考 terwox/skill-evaluator 的 EVAL.md 输出风格。
        """
        scores = self.compute_scores()
        rel    = self.compute_reliability()
        rating = self.get_rating()
        badge  = self.get_badge()
        ts     = datetime.now().strftime('%Y-%m-%d')
        recs   = self.get_recommendations()

        safety_icon = {'passed': '✅ 通过', 'warning': '⚠️ 警告', 'failed': '❌ 失败'}.get(
            self.safety.get('status', ''), '？ 未知')

        lines = [
            f'# EVAL — {self.skill_name}',
            '',
            f'> 由 `skill-tester` 自动生成，最后更新：{ts}',
            '',
            '## 认证结果',
            '',
            f'| 项目 | 值 |',
            f'|------|----|',
            f'| 综合评分 | **{scores["overall"]:.1f}/100** |',
            f'| 评级 | {rating} |',
            f'| 认证状态 | {badge} |',
            f'| 安全检查 | {safety_icon} |',
            '',
            '## 维度得分',
            '',
            '| 维度 | 得分 | 权重 |',
            '|------|------|------|',
            f'| 触发命中率 | {scores["hit_rate"]:.1f} | 25% |',
            f'| Skill规范程度 | {scores["spec_compliance"]:.1f} | 20% |',
            f'| Agent理解度 | {scores["agent_comprehension"]:.1f} | 25% |',
            f'| 执行成功率 | {scores["execution_success"]:.1f} | 30% |',
            '',
        ]

        if rel['available']:
            k = rel['k']
            lines += [
                '## 可靠性',
                '',
                f'| 指标 | 值 |',
                f'|------|----|',
                f'| pass@{k}（能力） | {rel["pass_at_k"]:.0f}% |',
                f'| pass^{k}（稳定性） | {rel["pass_k"]:.0f}% |',
                '',
            ]

        if recs:
            lines += ['## 待改进项', '']
            for p in ('P0', 'P1', 'P2'):
                p_recs = [r for r in recs if r['priority'] == p]
                if not p_recs:
                    continue
                icon = {'P0': '🔴', 'P1': '🟡', 'P2': '🟢'}[p]
                lines.append(f'### {icon} {p}')
                lines.append('')
                for r in p_recs:
                    lines.append(f'- {r["message"]}')
                lines.append('')

        lines += [
            '---',
            '',
            f'*完整报告参见 `test-report-{self.skill_name}-*.md`*',
            '',
        ]
        return '\n'.join(lines)

    def build_json(self) -> Dict[str, Any]:
        scores = self.compute_scores()
        rel    = self.compute_reliability()
        return {
            'version':    '3.0',
            'skill_name': self.skill_name,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'safety_status': self.safety.get('status'),
                'overall_score': scores['overall'],
                'rating':        self.get_rating(),
                'badge':         self.get_badge(),
            },
            'dimensions': {
                k: {'score': scores[k], 'weight': int(DIMENSION_WEIGHTS.get(k, 0) * 100)}
                for k in ('hit_rate', 'spec_compliance', 'agent_comprehension', 'execution_success')
            },
            'reliability': rel,
            'test_summary': self.execution,
            'recommendations': self.get_recommendations(),
        }


# ──────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='skill-tester 报告生成器')
    parser.add_argument('results_file', help='统一 results JSON 文件路径')
    parser.add_argument('--output', '-o', help='输出 Markdown 报告路径（默认自动命名）')
    parser.add_argument('--json', action='store_true', help='同时输出 JSON 报告')
    parser.add_argument('--eval-md', metavar='SKILL_PATH',
                        help='将评估摘要写入 <SKILL_PATH>/EVAL.md（随 Skill 版本管理）')
    args = parser.parse_args()

    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f'❌ 文件不存在: {results_path}', file=sys.stderr)
        sys.exit(1)

    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    builder = ReportBuilder(results)
    scores  = builder.compute_scores()

    skill_name = results.get('skill_name', 'unknown')
    ts         = datetime.now().strftime('%Y%m%d_%H%M%S')
    md_path    = Path(args.output) if args.output else Path(f'test-report-{skill_name}-{ts}.md')

    md_path.write_text(builder.build_markdown(), encoding='utf-8')
    print(f'✅ Markdown 报告已生成: {md_path}')

    if args.json:
        json_path = md_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(builder.build_json(), f, ensure_ascii=False, indent=2)
        print(f'✅ JSON 报告已生成: {json_path}')

    if args.eval_md:
        eval_dir = Path(args.eval_md)
        if eval_dir.is_dir():
            eval_path = eval_dir / 'EVAL.md'
            eval_path.write_text(builder.build_eval_md(), encoding='utf-8')
            print(f'✅ EVAL.md 已写入: {eval_path}')
        else:
            print(f'⚠️ --eval-md 路径不是目录，跳过: {eval_dir}', file=sys.stderr)

    print(f'\n综合评分: {scores["overall"]:.1f}/100  {builder.get_rating()}')
    print(f'认证状态: {builder.get_badge()}')

    recs = builder.get_recommendations()
    p0   = [r for r in recs if r['priority'] == 'P0']
    if p0:
        print(f'\n🔴 P0 问题（必须修复）:')
        for r in p0:
            print(f'  - {r["message"]}')
