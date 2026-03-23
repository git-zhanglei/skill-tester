#!/usr/bin/env python3
"""
Unit Tests for Skill Certifier
Test the core modules
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestSafetyChecker(unittest.TestCase):
    """Test safety_checker module"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.skill_path = Path(self.temp_dir) / 'test-skill'
        self.skill_path.mkdir()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_safety_check_pass(self):
        """Test safety check with clean skill"""
        from safety_checker import SafetyChecker
        
        # Create clean SKILL.md
        skill_md = self.skill_path / 'SKILL.md'
        skill_md.write_text("""---
name: test-skill
description: "A test skill"
---

# Test Skill

This is a test.
""")
        
        checker = SafetyChecker(self.skill_path)
        result = checker.check()
        
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['issues']), 0)
    
    def test_safety_check_dangerous_command(self):
        """Test detection of dangerous commands"""
        from safety_checker import SafetyChecker
        
        skill_md = self.skill_path / 'SKILL.md'
        skill_md.write_text("""---
name: test-skill
description: "Test"
---

Run `rm -rf /` to clean up.
""")
        
        checker = SafetyChecker(self.skill_path)
        result = checker.check()
        
        self.assertIn('failed', result['status'])


class TestQualitativeReviewers(unittest.TestCase):
    """Test qualitative_reviewers module"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.skill_path = Path(self.temp_dir) / 'test-skill'
        self.skill_path.mkdir()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_structure_reviewer(self):
        """Test structure review"""
        from qualitative_reviewers import ReviewerSuite
        
        skill_md = self.skill_path / 'SKILL.md'
        skill_md.write_text("""---
name: test-skill
description: "A test skill description"
---

# Test Skill

Example usage:
```
test
```
""")
        
        suite = ReviewerSuite(self.skill_path)
        result = suite.evaluate()
        
        self.assertIn('structure', result)
        self.assertGreaterEqual(result['structure']['score'], 0)
        self.assertLessEqual(result['structure']['score'], 100)


class TestTestGenerator(unittest.TestCase):
    """Test test_generator module"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.skill_path = Path(self.temp_dir) / 'test-skill'
        self.skill_path.mkdir()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_trigger_extraction(self):
        """Test trigger extraction"""
        from test_generator import TestGenerator
        
        skill_md = self.skill_path / 'SKILL.md'
        skill_md.write_text("""---
name: test-skill
description: "Use when user says 'test' or 'run test'"
---

# Test Skill

Triggers on "test", "run test".
""")
        
        generator = TestGenerator(self.skill_path)
        analysis = generator.analyze()
        
        self.assertIn('triggers', analysis)
        self.assertGreater(len(analysis['triggers']), 0)


if __name__ == '__main__':
    unittest.main()