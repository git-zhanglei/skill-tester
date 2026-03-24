#!/usr/bin/env python3
"""
skill-tester — 核心单元测试
覆盖不依赖 sessions_spawn 的模块
"""

import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


# ──────────────────────────────────────────────
# SafetyChecker
# ──────────────────────────────────────────────

class TestSafetyChecker(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.skill = Path(self.tmp) / 'skill'
        self.skill.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, content: str):
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')

    def test_clean_skill_passes(self):
        self._write('---\nname: s\ndescription: "safe"\n---\n# S\n```\ntest\n```\n')
        from safety_checker import SafetyChecker
        r = SafetyChecker(self.skill).check()
        self.assertEqual(r['status'], 'passed')
        self.assertEqual(r['issues'], [])

    def test_rm_rf_detected(self):
        self._write('Run `rm -rf /` to clean.\n')
        from safety_checker import SafetyChecker
        r = SafetyChecker(self.skill).check()
        self.assertEqual(r['status'], 'failed')

    def test_hardcoded_api_key_flagged(self):
        self._write('api_key = "sk-abcdefg1234567890"\n')
        from safety_checker import SafetyChecker
        r = SafetyChecker(self.skill).check()
        self.assertIn(r['status'], ('failed', 'warning'))

    def test_empty_skill_graceful(self):
        (self.skill / 'SKILL.md').write_text('', encoding='utf-8')
        from safety_checker import SafetyChecker
        r = SafetyChecker(self.skill).check()
        self.assertIn('status', r)
        self.assertIn('issues', r)
        self.assertIn('warnings', r)

    def test_result_has_checked_files(self):
        self._write('---\nname: s\ndescription: "d"\n---\n')
        from safety_checker import SafetyChecker
        r = SafetyChecker(self.skill).check()
        self.assertIn('checked_files', r)
        self.assertIsInstance(r['checked_files'], list)


# ──────────────────────────────────────────────
# SmartTestGenerator — 使用实际 API
# ──────────────────────────────────────────────

class TestSmartTestGenerator(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.skill = Path(self.tmp) / 'skill'
        self.skill.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, content: str):
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')

    def test_analyze_returns_expected_keys(self):
        self._write('---\nname: weather\ndescription: "查天气"\n---\n# Weather\n```\n查天气\n```\n')
        from smart_test_generator import SmartTestGenerator
        analysis = SmartTestGenerator(self.skill).analyze()
        self.assertIn('name', analysis)
        self.assertIn('complexity', analysis)
        self.assertIn('risks', analysis)
        self.assertIn('recommendations', analysis)

    def test_analyze_reads_name_from_frontmatter(self):
        self._write('---\nname: my-skill\ndescription: "d"\n---\n# T\n')
        from smart_test_generator import SmartTestGenerator
        analysis = SmartTestGenerator(self.skill).analyze()
        self.assertEqual(analysis['name'], 'my-skill')

    def test_missing_skill_md_raises(self):
        empty = Path(self.tmp) / 'empty'
        empty.mkdir()
        from smart_test_generator import SmartTestGenerator
        with self.assertRaises(FileNotFoundError):
            SmartTestGenerator(empty).analyze()

    def test_complexity_metrics_present(self):
        self._write('---\nname: x\ndescription: "d"\n---\n# T\n## A\n```\ncode\n```\n')
        from smart_test_generator import SmartTestGenerator
        analysis = SmartTestGenerator(self.skill).analyze()
        metrics = analysis['complexity']['metrics']
        self.assertIn('total_lines', metrics)
        self.assertIn('code_blocks', metrics)
        self.assertIn('headings', metrics)

    def test_generate_returns_list(self):
        self._write('---\nname: x\ndescription: "d"\n---\n# T\n')
        from smart_test_generator import SmartTestGenerator
        cases = SmartTestGenerator(self.skill).generate()
        self.assertIsInstance(cases, list)

    def test_generate_includes_adversarial(self):
        self._write('---\nname: file-manager\ndescription: "管理文件和路径"\n---\n# File Manager\n使用 path 和 file 进行操作。\n')
        from smart_test_generator import SmartTestGenerator
        cases = SmartTestGenerator(self.skill).generate()
        adversarial = [c for c in cases if c.get('type') == 'adversarial']
        self.assertGreater(len(adversarial), 0, '应该生成至少 1 个对抗性测试案例')

    def test_adversarial_has_required_fields(self):
        self._write('---\nname: x\ndescription: "d"\n---\n# T\n')
        from smart_test_generator import SmartTestGenerator
        cases = SmartTestGenerator(self.skill).generate()
        for c in cases:
            if c.get('type') == 'adversarial':
                self.assertIn('dimension', c)
                self.assertIn('expected', c)
                self.assertIn('description', c)
                break


# ──────────────────────────────────────────────
# TestCasesValidator — 使用实际 API (validate / get_info)
# ──────────────────────────────────────────────

class TestTestCasesValidator(unittest.TestCase):

    def _case(self, **kw):
        base = {
            'id': 'hit_0', 'dimension': 'hit_rate', 'type': 'exact_match',
            'input': '测试skill ./', 'expected': 'activate',
            'description': 'test', 'weight': 1.0, 'status': 'pending',
        }
        base.update(kw)
        return base

    def _payload(self, cases=None):
        cases = cases or [self._case()]
        return {
            'version': '3.0', 'skill_name': 'x', 'total': len(cases),
            'cases': cases,
            'execution': {'status': 'pending', 'progress': {'total': len(cases), 'completed': 0, 'passed': 0, 'failed': 0}},
        }

    def test_valid_passes(self):
        from test_cases_validator import TestCasesValidator
        ok, msg = TestCasesValidator.validate(self._payload())
        self.assertTrue(ok, msg)

    def test_missing_version_fails(self):
        from test_cases_validator import TestCasesValidator
        p = self._payload()
        del p['version']
        ok, _ = TestCasesValidator.validate(p)
        self.assertFalse(ok)

    def test_missing_cases_fails(self):
        from test_cases_validator import TestCasesValidator
        p = self._payload()
        del p['cases']
        ok, _ = TestCasesValidator.validate(p)
        self.assertFalse(ok)

    def test_invalid_status_fails(self):
        from test_cases_validator import TestCasesValidator
        p = self._payload(cases=[self._case(status='flying')])
        ok, _ = TestCasesValidator.validate(p)
        self.assertFalse(ok)

    def test_get_info_structure(self):
        from test_cases_validator import TestCasesValidator
        info = TestCasesValidator.get_info(self._payload())
        self.assertIn('total', info)
        self.assertIn('by_dimension', info)


# ──────────────────────────────────────────────
# ReportBuilder — 使用实际 API
# ──────────────────────────────────────────────

class TestReportBuilder(unittest.TestCase):

    def _results(self, passed=8, failed=2):
        cases = []
        for i in range(passed):
            cases.append({'id': f'p{i}', 'dimension': 'execution_success',
                          'type': 'normal_path', 'status': 'completed',
                          'result': {'status': 'passed'}, 'weight': 1.0})
        for i in range(failed):
            cases.append({'id': f'f{i}', 'dimension': 'execution_success',
                          'type': 'normal_path', 'status': 'completed',
                          'result': {'status': 'failed', 'failure_reason': 'timeout'},
                          'weight': 1.0})
        return {
            'version': '3.0', 'skill_name': 'my-skill',
            'skill_path': '/tmp/my-skill',
            'safety': {'status': 'passed', 'issues': [], 'warnings': []},
            'spec_score': 80.0,
            'cases': cases,
            'execution': {'total': passed + failed, 'passed': passed,
                          'failed': failed, 'duration_seconds': 30.0},
        }

    def test_compute_scores_returns_all_dimensions(self):
        from report_builder import ReportBuilder
        b = ReportBuilder(self._results())
        s = b.compute_scores()
        for key in ('hit_rate', 'spec_compliance', 'agent_comprehension', 'execution_success', 'overall'):
            self.assertIn(key, s)

    def test_overall_score_in_range(self):
        from report_builder import ReportBuilder
        s = ReportBuilder(self._results()).compute_scores()
        self.assertGreaterEqual(s['overall'], 0)
        self.assertLessEqual(s['overall'], 100)

    def test_safety_failed_forces_zero(self):
        from report_builder import ReportBuilder
        r = self._results()
        r['safety'] = {'status': 'failed', 'issues': ['rm -rf /'], 'warnings': []}
        s = ReportBuilder(r).compute_scores()
        self.assertEqual(s['overall'], 0.0)

    def test_markdown_contains_skill_name(self):
        from report_builder import ReportBuilder
        md = ReportBuilder(self._results()).build_markdown()
        self.assertIn('my-skill', md)

    def test_markdown_contains_score(self):
        from report_builder import ReportBuilder
        md = ReportBuilder(self._results()).build_markdown()
        self.assertIn('/100', md)

    def test_json_report_structure(self):
        from report_builder import ReportBuilder
        data = ReportBuilder(self._results()).build_json()
        self.assertIn('summary', data)
        self.assertIn('overall_score', data['summary'])
        self.assertIn('dimensions', data)
        self.assertIsInstance(data['summary']['overall_score'], (int, float))

    def test_spec_score_used(self):
        from report_builder import ReportBuilder
        r = self._results()
        r['spec_score'] = 100.0
        s = ReportBuilder(r).compute_scores()
        self.assertEqual(s['spec_compliance'], 100.0)

    def test_single_dim_below_40_caps_rating(self):
        from report_builder import ReportBuilder
        r = self._results(passed=0, failed=10)  # execution_success ≈ 0
        r['spec_score'] = 90.0
        b = ReportBuilder(r)
        rating = b.get_rating()
        self.assertIn('⭐⭐⭐', rating)
        self.assertNotIn('⭐⭐⭐⭐', rating)

    def test_recommendations_have_priority(self):
        from report_builder import ReportBuilder
        r = self._results(passed=2, failed=8)  # 低成功率
        recs = ReportBuilder(r).get_recommendations()
        priorities = {rec['priority'] for rec in recs}
        self.assertTrue(priorities & {'P0', 'P1', 'P2'})
        for rec in recs:
            self.assertIn('priority', rec)
            self.assertIn('message', rec)

    def test_reliability_no_multi_trial(self):
        from report_builder import ReportBuilder
        r = self._results()
        rel = ReportBuilder(r).compute_reliability()
        self.assertFalse(rel['available'])

    def test_reliability_with_multi_trial(self):
        from report_builder import ReportBuilder
        r = self._results()
        # 添加一个有 trials 数据的案例
        r['cases'].append({
            'id': 'multi_0', 'dimension': 'hit_rate', 'type': 'exact_match',
            'status': 'completed', 'multi_trial': True,
            'trials': [
                {'trial': 1, 'status': 'passed'},
                {'trial': 2, 'status': 'passed'},
                {'trial': 3, 'status': 'failed'},
            ],
            'result': {'status': 'passed'},
        })
        rel = ReportBuilder(r).compute_reliability()
        self.assertTrue(rel['available'])
        self.assertEqual(rel['k'], 3)
        self.assertEqual(rel['pass_at_k'], 100.0)  # 至少 1 次通过
        self.assertEqual(rel['pass_k'], 0.0)        # 未全部通过

    def test_adversarial_counted_in_execution_score(self):
        from report_builder import ReportBuilder
        r = self._results(passed=0, failed=0)
        r['cases'] = [
            {'id': 'a0', 'dimension': 'execution_success', 'type': 'adversarial',
             'status': 'completed', 'result': {'status': 'passed'}, 'weight': 1.0},
        ]
        scores = ReportBuilder(r).compute_scores()
        self.assertGreater(scores['execution_success'], 0)


# ──────────────────────────────────────────────
# SpecChecker（14项结构化规范检查）
# ──────────────────────────────────────────────

class TestSpecChecker(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.skill = Path(self.tmp) / 'my-skill'
        self.skill.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_skill_md(self, content: str):
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')

    def _good_skill_md(self) -> str:
        return (
            '---\n'
            'name: my-skill\n'
            'description: "Query weather data. Use when user asks about current weather or forecasts."\n'
            '---\n'
            '# My Skill\n'
            '## Guardrails\n'
            '- Do not query real production endpoints.\n'
            '## Workflow\n'
            '1. Parse user location.\n'
            '2. Call weather API.\n'
            '3. Return formatted result.\n'
        )

    # structure 类别

    def test_missing_skill_md_fails(self):
        from spec_checker import check_skill_md_exists
        r = check_skill_md_exists(str(self.skill))
        self.assertEqual(r['status'], 'fail')

    def test_skill_md_exists_passes(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import check_skill_md_exists
        r = check_skill_md_exists(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_missing_frontmatter_fails(self):
        self._write_skill_md('# My Skill\nNo frontmatter here.\n')
        from spec_checker import check_valid_frontmatter
        r = check_valid_frontmatter(str(self.skill))
        self.assertEqual(r['status'], 'fail')

    def test_valid_frontmatter_passes(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import check_valid_frontmatter
        r = check_valid_frontmatter(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_name_matches_dir_pass(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import check_name_matches_dir
        r = check_name_matches_dir(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_name_not_matches_dir_warns(self):
        content = self._good_skill_md().replace('name: my-skill', 'name: other-skill')
        self._write_skill_md(content)
        from spec_checker import check_name_matches_dir
        r = check_name_matches_dir(str(self.skill))
        self.assertEqual(r['status'], 'warn')

    def test_has_guardrails_passes(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import check_has_guardrails
        r = check_has_guardrails(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_no_guardrails_warns(self):
        self._write_skill_md('---\nname: x\ndescription: "test"\n---\n# T\n')
        from spec_checker import check_has_guardrails
        r = check_has_guardrails(str(self.skill))
        self.assertEqual(r['status'], 'warn')

    # trigger 类别

    def test_description_too_short_fails(self):
        self._write_skill_md('---\nname: x\ndescription: "hi"\n---\n')
        from spec_checker import check_description_length
        r = check_description_length(str(self.skill))
        self.assertEqual(r['status'], 'fail')

    def test_description_ok_passes(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import check_description_length
        r = check_description_length(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_description_has_trigger_context(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import check_description_trigger_context
        r = check_description_trigger_context(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_description_no_trigger_context_warns(self):
        self._write_skill_md('---\nname: x\ndescription: "This skill does something cool."\n---\n')
        from spec_checker import check_description_trigger_context
        r = check_description_trigger_context(str(self.skill))
        self.assertEqual(r['status'], 'warn')

    # documentation 类别

    def test_token_cost_under_150_passes(self):
        body = '\n'.join(['- line'] * 50)
        self._write_skill_md(f'---\nname: x\ndescription: "d"\n---\n{body}')
        from spec_checker import check_token_cost
        r = check_token_cost(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_token_cost_over_400_fails(self):
        body = '\n'.join(['- line'] * 450)
        self._write_skill_md(f'---\nname: x\ndescription: "d"\n---\n{body}')
        from spec_checker import check_token_cost
        r = check_token_cost(str(self.skill))
        self.assertEqual(r['status'], 'fail')

    def test_has_workflow_passes(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import check_has_workflow
        r = check_has_workflow(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    # scripts 类别

    def test_python_syntax_error_fails(self):
        self._write_skill_md('---\nname: x\ndescription: "d"\n---\n')
        scripts = self.skill / 'scripts'
        scripts.mkdir()
        (scripts / 'bad.py').write_text('def foo(:\n    pass\n', encoding='utf-8')
        from spec_checker import check_python_syntax
        r = check_python_syntax(str(self.skill))
        self.assertEqual(r['status'], 'fail')

    def test_python_syntax_clean_passes(self):
        self._write_skill_md('---\nname: x\ndescription: "d"\n---\n')
        scripts = self.skill / 'scripts'
        scripts.mkdir()
        (scripts / 'good.py').write_text('import json\nprint("ok")\n', encoding='utf-8')
        from spec_checker import check_python_syntax
        r = check_python_syntax(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_external_deps_warns(self):
        self._write_skill_md('---\nname: x\ndescription: "d"\n---\n')
        scripts = self.skill / 'scripts'
        scripts.mkdir()
        (scripts / 'dep.py').write_text('import requests\nprint("x")\n', encoding='utf-8')
        from spec_checker import check_no_external_deps
        r = check_no_external_deps(str(self.skill))
        self.assertEqual(r['status'], 'warn')

    def test_stdlib_only_passes(self):
        self._write_skill_md('---\nname: x\ndescription: "d"\n---\n')
        scripts = self.skill / 'scripts'
        scripts.mkdir()
        (scripts / 'ok.py').write_text('import json\nimport os\nimport sys\n', encoding='utf-8')
        from spec_checker import check_no_external_deps
        r = check_no_external_deps(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    # 评分聚合

    def test_spec_score_all_pass_is_100(self):
        from spec_checker import compute_spec_score
        results = [{'status': 'pass'} for _ in range(10)]
        self.assertEqual(compute_spec_score(results), 100.0)

    def test_spec_score_all_warn_is_50(self):
        from spec_checker import compute_spec_score
        results = [{'status': 'warn'} for _ in range(10)]
        self.assertEqual(compute_spec_score(results), 50.0)

    def test_spec_score_all_fail_is_0(self):
        from spec_checker import compute_spec_score
        results = [{'status': 'fail'} for _ in range(10)]
        self.assertEqual(compute_spec_score(results), 0.0)

    def test_full_run_on_good_skill_over_50(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import run_checks, compute_spec_score
        results = run_checks(str(self.skill))
        score = compute_spec_score(results)
        self.assertGreater(score, 50.0, f'Good skill 应该 >50 分，实际 {score}')

    def test_run_checks_returns_14_items(self):
        self._write_skill_md(self._good_skill_md())
        from spec_checker import run_checks
        results = run_checks(str(self.skill))
        self.assertEqual(len(results), 14)


# ──────────────────────────────────────────────
# ReportBuilder — EVAL.md 输出
# ──────────────────────────────────────────────

class TestReportBuilderEvalMd(unittest.TestCase):

    def _results(self):
        return {
            'version': '3.0',
            'skill_name': 'test-skill',
            'skill_path': '/tmp/test-skill',
            'generated_at': '2026-01-01T00:00:00',
            'safety': {'status': 'passed', 'issues': [], 'warnings': []},
            'spec_score': 80.0,
            'cases': [
                {'id': 'h0', 'dimension': 'hit_rate', 'type': 'exact_match',
                 'status': 'completed', 'result': {'status': 'passed'}},
                {'id': 'e0', 'dimension': 'execution_success', 'type': 'normal_path',
                 'status': 'completed', 'result': {'status': 'passed'}},
            ],
            'execution': {'total': 2, 'passed': 2, 'failed': 0, 'duration_seconds': 5.0},
        }

    def test_build_eval_md_returns_string(self):
        from report_builder import ReportBuilder
        md = ReportBuilder(self._results()).build_eval_md()
        self.assertIsInstance(md, str)
        self.assertIn('test-skill', md)

    def test_build_eval_md_contains_scores(self):
        from report_builder import ReportBuilder
        md = ReportBuilder(self._results()).build_eval_md()
        self.assertIn('综合评分', md)
        self.assertIn('触发命中率', md)
        self.assertIn('Agent理解度', md)
        self.assertIn('执行成功率', md)

    def test_build_eval_md_no_full_case_details(self):
        """EVAL.md 应该精简，不含完整失败详情表格"""
        from report_builder import ReportBuilder
        results = self._results()
        results['cases'][0]['result']['status'] = 'failed'
        md = ReportBuilder(results).build_eval_md()
        # EVAL.md 中不应有 "| 状态 | 类型 |" 这样的完整案例表
        self.assertNotIn('| 状态 | 类型 |', md)

    def test_eval_md_written_to_dir(self):
        from report_builder import ReportBuilder
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            eval_path = Path(tmp) / 'EVAL.md'
            md = ReportBuilder(self._results()).build_eval_md()
            eval_path.write_text(md, encoding='utf-8')
            self.assertTrue(eval_path.exists())
            content = eval_path.read_text(encoding='utf-8')
            self.assertIn('test-skill', content)


if __name__ == '__main__':
    unittest.main()
