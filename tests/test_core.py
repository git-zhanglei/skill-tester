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
from unittest.mock import patch
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
# SandboxChecker
# ──────────────────────────────────────────────

class TestSandboxChecker(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.skill = Path(self.tmp) / 'skill'
        self.skill.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_skill(self, content: str):
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')

    def test_simple_skill_is_sandbox_compatible(self):
        self._write_skill('---\nname: s\ndescription: "本地纯文本处理"\n---\n# S\n')
        from sandbox_checker import SandboxChecker
        result = SandboxChecker(self.skill).check()
        self.assertEqual(result['status'], 'sandbox_compatible')
        self.assertTrue(result['sandbox_testable'])

    def test_env_dependency_marks_incompatible(self):
        self._write_skill('---\nname: s\ndescription: "使用 OPENAI_API_KEY 调用接口"\n---\n# S\n')
        from sandbox_checker import SandboxChecker
        result = SandboxChecker(self.skill).check()
        self.assertEqual(result['status'], 'sandbox_incompatible')
        caps = {d.get('capability') for d in result.get('dependencies', [])}
        self.assertIn('environment_variables', caps)

    def test_network_dependency_marks_incompatible(self):
        self._write_skill('---\nname: s\ndescription: "调用 https://api.example.com 获取数据"\n---\n# S\n')
        from sandbox_checker import SandboxChecker
        result = SandboxChecker(self.skill).check()
        self.assertEqual(result['status'], 'sandbox_incompatible')
        caps = {d.get('capability') for d in result.get('dependencies', [])}
        self.assertIn('network_access', caps)


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

    def test_default_max_cases_is_30(self):
        self._write('---\nname: x\ndescription: "d"\n---\n# T\n')
        from smart_test_generator import SmartTestGenerator
        g = SmartTestGenerator(self.skill)
        self.assertEqual(g.max_cases, 30)

    def test_generate_respects_max_cases_limit(self):
        self._write('---\nname: x\ndescription: "当用户说「测试skill」时触发。"\n---\n# T\n')
        from smart_test_generator import SmartTestGenerator
        generator = SmartTestGenerator(self.skill, max_cases=3)

        fake_hit = [
            {'id': f'h{i}', 'dimension': 'hit_rate', 'type': 'exact_match', 'input': 'x',
             'expected': 'activate', 'description': 'd', 'priority': '中', 'weight': 1.0, 'status': 'pending'}
            for i in range(5)
        ]
        fake_comp = [
            {'id': f'c{i}', 'dimension': 'agent_comprehension', 'type': 'outcome_check', 'input': 'x',
             'expected': 'ok', 'description': 'd', 'priority': '中', 'weight': 1.0, 'status': 'pending'}
            for i in range(2)
        ]
        fake_exec = [
            {'id': f'e{i}', 'dimension': 'execution_success', 'type': 'normal_path', 'input': 'x',
             'expected': 'ok', 'description': 'd', 'priority': '中', 'weight': 1.0, 'status': 'pending'}
            for i in range(4)
        ]

        with patch.object(generator, '_generate_hit_rate_cases', return_value=fake_hit), \
             patch.object(generator, '_generate_comprehension_cases', return_value=fake_comp), \
             patch.object(generator, '_generate_execution_cases', return_value=fake_exec):
            cases = generator.generate()

        self.assertEqual(len(cases), 3, '生成结果必须受 max_cases 限制')

    def test_generate_includes_categorized_dimensions(self):
        self._write(
            '---\n'
            'name: skill-tester\n'
            'description: "当用户说「测试skill」「评估skill」时触发。"\n'
            '---\n'
            '# T\n'
        )
        from smart_test_generator import SmartTestGenerator
        cases = SmartTestGenerator(self.skill).generate()
        dims = {c.get('dimension') for c in cases}
        self.assertIn('hit_rate', dims)
        self.assertIn('agent_comprehension', dims)
        self.assertIn('execution_success', dims)

    def test_hit_rate_uses_synonyms_and_negative_intents(self):
        self._write(
            '---\n'
            'name: skill-tester\n'
            'description: "当用户说「测试skill」时触发。"\n'
            '---\n'
            '# T\n'
        )
        from smart_test_generator import SmartTestGenerator
        cases = SmartTestGenerator(self.skill).generate()
        fuzzy = [c for c in cases if c.get('dimension') == 'hit_rate' and c.get('type') == 'fuzzy_match']
        negative = [c for c in cases if c.get('dimension') == 'hit_rate' and c.get('type') == 'negative_test']
        self.assertGreater(len(fuzzy), 0, '应生成同义词/衍生词的模糊命中案例')
        self.assertGreater(len(negative), 0, '应生成非同义负样本案例')
        self.assertTrue(all(c.get('expected') == 'activate' for c in fuzzy))
        self.assertTrue(all(c.get('expected') == 'not_activate' for c in negative))

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
                self.assertIn('id', c)
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
        self.assertEqual(r['status'], 'pass')

    def test_no_guardrails_warns_when_risky(self):
        self._write_skill_md(
            '---\nname: x\ndescription: "执行数据库删除操作"\n---\n# T\n'
            '该技能会删除生产数据库中的记录。\n'
        )
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

    def test_no_workflow_passes_when_simple(self):
        self._write_skill_md('---\nname: x\ndescription: "简单问答 skill"\n---\n# T\n只返回固定文案。\n')
        from spec_checker import check_has_workflow
        r = check_has_workflow(str(self.skill))
        self.assertEqual(r['status'], 'pass')

    def test_no_workflow_warns_when_complex(self):
        body = '\n'.join([f'- line {i}' for i in range(140)])
        self._write_skill_md(
            '---\nname: x\ndescription: "该技能分三个阶段执行，先解析再执行最后汇总"\n---\n'
            f'# T\n{body}\n'
        )
        from spec_checker import check_has_workflow
        r = check_has_workflow(str(self.skill))
        self.assertEqual(r['status'], 'warn')

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


# ── 早期终止实时检测 ──

class TestEarlyExitDetection(unittest.TestCase):
    """测试 record 中的实时早期终止检测"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cases_file = Path(self.tmp) / 'cases.json'

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write_cases(self, cases):
        data = {
            'version': '3.0', 'skill_name': 'test',
            'total': len(cases), 'cases': cases,
            'execution': {'status': 'pending', 'progress': {'total': len(cases), 'completed': 0, 'passed': 0, 'failed': 0}},
        }
        self.cases_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def _make_case(self, case_id, status='pending', result_status=None, outcome=''):
        c = {'id': case_id, 'dimension': 'execution_success', 'type': 'normal_path',
             'input': 'test', 'expected': 'ok', 'description': 'test',
             'weight': 1.0, 'status': status}
        if result_status:
            c['status'] = 'completed'
            c['result'] = {'status': result_status, 'outcome': outcome}
        return c

    def test_no_early_exit_when_mixed_results(self):
        cases = [
            self._make_case('c0', result_status='passed'),
            self._make_case('c1', result_status='failed', outcome='超时'),
            self._make_case('c2', result_status='passed'),
            self._make_case('c3'),  # pending
        ]
        self._write_cases(cases)
        from parallel_test_runner import TestCoordinator
        coord = TestCoordinator(str(self.cases_file))
        result = coord.record('c3', 'failed', outcome='超时')
        self.assertTrue(result['recorded'])
        self.assertNotIn('early_exit_recommended', result)

    def test_early_exit_on_3_consecutive_same_reason(self):
        cases = [
            self._make_case('c0', result_status='failed', outcome='Skill未被激活，子Agent未触发'),
            self._make_case('c1', result_status='failed', outcome='目标Skill未触发，未激活'),
            self._make_case('c2'),  # pending — will record as failed
            self._make_case('c3'),  # pending
        ]
        self._write_cases(cases)
        from parallel_test_runner import TestCoordinator
        coord = TestCoordinator(str(self.cases_file))
        result = coord.record('c2', 'failed', outcome='Skill未被激活')
        self.assertTrue(result['recorded'])
        self.assertTrue(result.get('early_exit_recommended', False))
        self.assertIn('skill_not_activated', result.get('early_exit_reason', ''))


# ── 多行 YAML 解析 ──

class TestMultilineYaml(unittest.TestCase):
    """测试 smart_test_generator 对多行 description 的解析"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.skill = Path(self.tmp) / 'skill'
        self.skill.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_multiline_description_parsed(self):
        content = '---\nname: test\ndescription: >\n  这是一个\n  多行描述\n---\n# T\n'
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')
        from smart_test_generator import SmartTestGenerator
        gen = SmartTestGenerator(self.skill)
        gen.analyze()
        self.assertIn('多行描述', gen.frontmatter.get('description', ''))

    def test_quoted_description_with_colon(self):
        content = '---\nname: test\ndescription: "用于查询天气：支持多城市"\n---\n# T\n'
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')
        from smart_test_generator import SmartTestGenerator
        gen = SmartTestGenerator(self.skill)
        gen.analyze()
        desc = gen.frontmatter.get('description', '')
        self.assertIn('查询天气', desc)
        self.assertIn('多城市', desc)


# ── 命令提取 ──

class TestCommandExtraction(unittest.TestCase):
    """测试 smart_test_generator 从 SKILL.md 正文提取命令"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.skill = Path(self.tmp) / 'skill'
        self.skill.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_extract_cli_commands(self):
        content = (
            '---\nname: test\ndescription: "测试"\n---\n# T\n'
            '## 用法\n'
            '```bash\n'
            'python3 cli.py search <keyword>\n'
            'python3 cli.py publish <product_id>\n'
            '```\n'
        )
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')
        from smart_test_generator import SmartTestGenerator
        gen = SmartTestGenerator(self.skill)
        gen.analyze()
        cmds = gen._extract_commands()
        subcmds = [c.get('subcmd') for c in cmds]
        self.assertIn('search', subcmds)
        self.assertIn('publish', subcmds)

    def test_extract_markdown_list_commands(self):
        content = (
            '---\nname: test\ndescription: "测试"\n---\n# T\n'
            '## 命令\n'
            '- `search <keyword>` — 搜索商品\n'
            '- `publish <id>` — 发布商品\n'
        )
        (self.skill / 'SKILL.md').write_text(content, encoding='utf-8')
        from smart_test_generator import SmartTestGenerator
        gen = SmartTestGenerator(self.skill)
        gen.analyze()
        cmds = gen._extract_commands()
        subcmds = [c.get('subcmd') for c in cmds]
        self.assertIn('search', subcmds)
        self.assertIn('publish', subcmds)


# ── 修复建议 ──

class TestFixSuggestions(unittest.TestCase):
    """测试报告中的修复建议生成"""

    def test_hit_rate_exact_match_suggestion(self):
        from report_builder import ReportBuilder
        r = {
            'version': '3.0', 'skill_name': 'test', 'skill_path': '/tmp/test',
            'safety': {'status': 'passed', 'issues': [], 'warnings': []},
            'spec_score': 80.0,
            'cases': [
                {'id': 'h0', 'dimension': 'hit_rate', 'type': 'exact_match',
                 'input': '搜索商品', 'status': 'completed',
                 'result': {'status': 'failed', 'outcome': '未触发'}},
            ],
            'execution': {'total': 1, 'passed': 0, 'failed': 1, 'duration_seconds': 5.0},
        }
        builder = ReportBuilder(r)
        fix = builder._suggest_fix(r['cases'][0])
        self.assertIn('搜索商品', fix)

    def test_execution_timeout_suggestion(self):
        from report_builder import ReportBuilder
        case = {'dimension': 'execution_success', 'type': 'normal_path',
                'result': {'status': 'failed', 'outcome': '执行超时'}}
        builder = ReportBuilder({'cases': [], 'safety': {}, 'spec_score': 0})
        fix = builder._suggest_fix(case)
        self.assertTrue('timeout' in fix.lower() or '超时' in fix)


if __name__ == '__main__':
    unittest.main()
