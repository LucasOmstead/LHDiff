"""Test suite for bug_detector.py"""

import sys
import os
import tempfile
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bug_tracking.bug_detector import BugDetector, parse_commit_messages


class TestBugDetector(unittest.TestCase):
    """Test BugDetector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = BugDetector()
    
    def test_bug_fix_keywords(self):
        """Test detection of bug fix keywords"""
        bug_fix_messages = [
            "fix crash on login",
            "resolve bug in authentication",
            "patch security vulnerability",
            "fix error handling",
            "resolve issue with validation",
            "hotfix for production crash",
            "bugfix: correct null pointer",
            "fix memory leak",
            "resolve critical issue",
            "repair broken functionality"
        ]
        
        for msg in bug_fix_messages:
            with self.subTest(msg=msg):
                self.assertTrue(
                    self.detector.is_bug_fix(msg),
                    f"Should detect bug fix: '{msg}'"
                )
    
    def test_non_bug_fix_messages(self):
        """Test that non-bug-fix messages are not detected"""
        non_bug_messages = [
            "add new feature",
            "implement ui layout",
            "docs: add installation instructions",
            "feat: implement new dashboard",
            "test: add unit tests",
            "refactor: extract helper functions",
            "update dependencies",
            "improve performance",
            "add comments to code"
        ]
        
        for msg in non_bug_messages:
            with self.subTest(msg=msg):
                self.assertFalse(
                    self.detector.is_bug_fix(msg),
                    f"Should NOT detect bug fix: '{msg}'"
                )
    
    def test_conventional_commit_prefixes(self):
        """Test conventional commit format prefixes"""
        conventional_fixes = [
            "fix: resolve null pointer exception",
            "fix(auth): prevent memory leak",
            "hotfix: critical security vulnerability",
            "bugfix(api): correct broken endpoint",
            "perf: fix slow query",
            "revert: rollback changes",
            "security: patch vulnerability"
        ]
        
        for msg in conventional_fixes:
            with self.subTest(msg=msg):
                self.assertTrue(
                    self.detector.is_bug_fix(msg),
                    f"Should detect conventional fix: '{msg}'"
                )
    
    def test_issue_numbers(self):
        """Test detection of issue numbers"""
        issue_messages = [
            "fixes #123",
            "resolves #456",
            "closes issue #789",
            "fixed #234",
            "resolved #567"
        ]
        
        for msg in issue_messages:
            with self.subTest(msg=msg):
                self.assertTrue(
                    self.detector.is_bug_fix(msg),
                    f"Should detect issue number: '{msg}'"
                )
    
    def test_case_insensitive(self):
        """Test that detection is case-insensitive"""
        self.assertTrue(self.detector.is_bug_fix("FIX CRASH"))
        self.assertTrue(self.detector.is_bug_fix("Fix Bug"))
        self.assertTrue(self.detector.is_bug_fix("BUGFIX"))
        self.assertTrue(self.detector.is_bug_fix("HotFix"))
    
    def test_edge_cases(self):
        """Test edge cases"""
        # Empty message
        self.assertFalse(self.detector.is_bug_fix(""))

        #Note: keyword-based detector will match "bug" in "bug tracking"
        # More sophisticated detection would need context understanding


class TestParseCommitMessages(unittest.TestCase):
    """Test parse_commit_messages function"""
    
    def test_parse_single_file(self):
        """Test parsing commits for a single file"""
        test_data = """auth:
initial authentication module

auth:
add login functionality

auth:
fix: resolve null pointer in login

user:
create user model"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            auth_commits = parse_commit_messages(temp_path, "auth")
            self.assertEqual(len(auth_commits), 3)
            self.assertIn("initial authentication module", auth_commits)
            self.assertIn("add login functionality", auth_commits)
            self.assertIn("fix: resolve null pointer in login", auth_commits)
        finally:
            os.unlink(temp_path)
    
    def test_parse_all_files(self):
        """Test parsing commits for all files"""
        test_data = """auth:
initial auth

auth:
fix bug

user:
create user

user:
add validation"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            all_commits = parse_commit_messages(temp_path)
            self.assertIn("auth", all_commits)
            self.assertIn("user", all_commits)
            self.assertEqual(len(all_commits["auth"]), 2)
            self.assertEqual(len(all_commits["user"]), 2)
        finally:
            os.unlink(temp_path)
    
    def test_parse_empty_file(self):
        """Test parsing empty file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            commits = parse_commit_messages(temp_path)
            self.assertEqual(commits, {})
        finally:
            os.unlink(temp_path)
    
    def test_parse_malformed_entries(self):
        """Test parsing with malformed entries"""
        test_data = """auth:
valid entry

invalid entry without colon

auth:
another valid entry

:entry with no filename"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_data)
            temp_path = f.name
        
        try:
            commits = parse_commit_messages(temp_path, "auth")
            # Should only parse valid entries
            self.assertEqual(len(commits), 2)
        finally:
            os.unlink(temp_path)
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file"""
        with self.assertRaises(FileNotFoundError):
            parse_commit_messages("nonexistent_file.txt", "auth")


def run_all_tests():
    """Run all bug detector tests"""
    print("=" * 60)
    print("Running Bug Detector Tests")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBugDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestParseCommitMessages))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    if result.wasSuccessful():
        print("All bug detector tests passed")
        print("=" * 60)
        return True
    else:
        print("Some tests failed")
        print("=" * 60)
        return False


if __name__ == "__main__":
    run_all_tests()