#!/usr/bin/env python3
"""
Integration Tests for Skill Certifier
Test the full pipeline
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from safety_checker import SafetyChecker
from test_generator import TestGenerator
from qualitative_reviewers import ReviewerSuite
from openclaw_executor import MockExecutor
from report_generator import ReportGenerator


class TestFullPipeline(unittest.TestCase):
    """Test the complete certification pipeline"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.skill_path = Path(self.temp_dir) / 'test-skill'
        self.skill_path.mkdir()
        
        # Create a sample skill
        skill_md = self.skill_path / 'SKILL.md'
        skill_md.write_text("""---
name: test-skill
description: "A test skill. Use when user says 'test' or '测试'."
---

# Test Skill

This is a test skill for unit testing.

## Usage

```
test
测试
```

## Examples

- "test" - Run the test
- "测试" - Chinese trigger

## Requirements

None
""")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_safety_phase(self):
        """Test Phase 1: Safety check"""
        checker = SafetyChecker(self.skill_path)
        result = checker.check()
        
        self.assertEqual(result['status'], 'passed')
    
    def test_analysis_phase(self):
        """Test Phase 2: Deep analysis"""
        generator = TestGenerator(self.skill_path, max_cases=10)
        analysis = generator.analyze()
        
        self.assertEqual(analysis['name'], 'test-skill')
        self.assertIn('triggers', analysis)
        self.assertGreater(len(analysis['triggers']), 0)
    
    def test_test_generation(self):
        """Test Phase 2: Test case generation"""
        generator = TestGenerator(self.skill_path, max_cases=5)
        generator.analyze()
        test_cases = generator.generate()
        
        self.assertGreater(len(test_cases), 0)
        
        # Check test case structure
        for tc in test_cases:
            self.assertIn('dimension', tc)
            self.assertIn('input', tc)
            self.assertIn('expected', tc)
    
    def test_execution_phase(self):
        """Test Phase 3: Test execution"""
        generator = TestGenerator(self.skill_path, max_cases=5)
        generator.analyze()
        test_cases = generator.generate()
        
        executor = MockExecutor(self.skill_path)
        results = executor.execute_batch(test_cases)
        
        self.assertEqual(len(results), len(test_cases))
        
        for r in results:
            self.assertIn('status', r)
            self.assertIn(r['status'], ['passed', 'failed', 'error'])
    
    def test_qualitative_phase(self):
        """Test Phase 4: Qualitative evaluation"""
        suite = ReviewerSuite(self.skill_path)
        result = suite.evaluate()
        
        self.assertIn('structure', result)
        self.assertIn('usefulness', result)
        self.assertIn('domain', result)
        
        for key in ['structure', 'usefulness', 'domain']:
            self.assertIn('verdict', result[key])
            self.assertIn('score', result[key])
            self.assertGreaterEqual(result[key]['score'], 0)
            self.assertLessEqual(result[key]['score'], 100)
    
    def test_report_generation(self):
        """Test Phase 5: Report generation"""
        results = {
            'skill_name': 'test-skill',
            'phases': {
                'safety': {
                    'status': 'passed',
                    'issues': [],
                    'warnings': [],
                    'checked_files': ['SKILL.md']
                },
                'testing': {
                    'total': 10,
                    'passed': 8,
                    'failed': 2,
                    'errors': 0,
                    'success_rate': 80.0,
                    'overall_score': 80.0,
                    'dimensions': {
                        'hit_rate': {'total': 5, 'passed': 5, 'rate': 100.0},
                        'success_rate': {'total': 3, 'passed': 2, 'rate': 66.7}
                    },
                    'results': []
                },
                'qualitative': {
                    'structure': {'verdict': '✅ Good', 'score': 85, 'findings': [], 'recommendations': []},
                    'usefulness': {'verdict': '✅ Good', 'score': 80, 'findings': [], 'recommendations': []},
                    'domain': {'verdict': '⚠️ Acceptable', 'score': 70, 'findings': ['No tools'], 'recommendations': ['Add tools']}
                }
            }
        }
        
        generator = ReportGenerator(results)
        report = generator.generate()
        
        self.assertIn('test-skill', report)
        self.assertIn('80.0/100', report)
        self.assertIn('Safety', report)
        self.assertIn('Quantitative', report)
        self.assertIn('Qualitative', report)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_missing_skill_md(self):
        """Test handling of missing SKILL.md"""
        skill_path = Path(self.temp_dir) / 'empty-skill'
        skill_path.mkdir()
        
        generator = TestGenerator(skill_path)
        
        with self.assertRaises(FileNotFoundError):
            generator.analyze()
    
    def test_empty_skill_md(self):
        """Test handling of empty SKILL.md"""
        skill_path = Path(self.temp_dir) / 'empty-skill'
        skill_path.mkdir()
        
        skill_md = skill_path / 'SKILL.md'
        skill_md.write_text('')
        
        checker = SafetyChecker(skill_path)
        result = checker.check()
        
        # Should handle gracefully
        self.assertIn('status', result)
    
    def test_invalid_yaml_frontmatter(self):
        """Test handling of invalid YAML"""
        skill_path = Path(self.temp_dir) / 'invalid-skill'
        skill_path.mkdir()
        
        skill_md = skill_path / 'SKILL.md'
        skill_md.write_text("""---
name: [invalid yaml
description: missing quote
---

# Test
""")
        
        # Should not crash
        from qualitative_reviewers import ReviewerSuite
        suite = ReviewerSuite(skill_path)
        result = suite.evaluate()
        
        self.assertIn('structure', result)


if __name__ == '__main__':
    unittest.main()