"""Tests for the bug backtracking feature"""

import unittest
import os
import sys

# Add the project root to sys.path so tests can import the src package when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import CommitInfo, FileVersion, BugSignature, BugLineage, LineMapping
from src.bug_tracking.commit_history import CommitHistory
from src.bug_tracking.file_version_loader import FileVersionLoader
from src.bug_tracking.bug_signature import extract_bug_signature, build_line_mapping
from src.bug_tracking.bug_backtracker import BugBacktracker, backtrack_bug_to_origin

# Paths to the synthetic test data used to exercise the bug backtracking logic
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "bug_backtracking")
DESC_FILE = os.path.join(TEST_DATA_DIR, "desc.txt")


class TestCommitHistory(unittest.TestCase):
    """Tests for parsing commit descriptions and identifying bug-fix commits"""

    def test_parse_commits(self):
        """CommitHistory should load all commits and preserve their version numbers"""
        history = CommitHistory(DESC_FILE, "code")
        commits = history.get_commits()
        
        self.assertEqual(len(commits), 3)
        self.assertEqual(commits[0].version, 1)
    
    def test_identify_bug_fixes(self):
        """CommitHistory should correctly flag which commits are bug fixes"""
        history = CommitHistory(DESC_FILE, "code")
        bug_fixes = history.get_bug_fix_commits()
        
        self.assertEqual(len(bug_fixes), 1)
        self.assertEqual(bug_fixes[0].version, 3)


class TestFileVersionLoader(unittest.TestCase):
    """Tests for loading file versions from the versioned test data directory"""
    
    def test_load_version(self):
        """FileVersionLoader should load the requested version with its contents"""
        loader = FileVersionLoader(TEST_DATA_DIR, "code")
        version = loader.load_version(1)
        
        self.assertEqual(version.version, 1)
        self.assertGreater(len(version.lines), 0)
    
    def test_get_available_versions(self):
        """FileVersionLoader should list all available version numbers in order"""
        loader = FileVersionLoader(TEST_DATA_DIR, "code")
        versions = loader.get_available_versions()
        
        self.assertEqual(versions, [1, 2, 3])


class TestBugSignature(unittest.TestCase):
    """Tests for computing bug signatures from a pair of file versions"""
    
    def test_extract_signature(self):
        """extract_bug_signature should detect at least one buggy line between versions"""
        loader = FileVersionLoader(TEST_DATA_DIR, "code")
        before = loader.load_version(2)
        after = loader.load_version(3)
        
        signature = extract_bug_signature(before, after)
        
        self.assertFalse(signature.is_empty())
        self.assertGreater(len(signature.buggy_lines), 0)


class TestLineMapping(unittest.TestCase):
    """Tests for constructing line mappings from diff operations."""
    
    def test_build_mapping(self):
        """build_line_mapping should correctly separate exact and similarity matches"""
        diff_ops = ['0:0', '1~1', '2:2']
        mapping = build_line_mapping(diff_ops, 0, 1)
        
        self.assertEqual(mapping.exact_matches[0], 0)
        self.assertEqual(mapping.exact_matches[2], 2)
        self.assertEqual(mapping.similarity_matches[1], 1)


class TestBugBacktracker(unittest.TestCase):
    """End-to-end tests for the BugBacktracker analysis on a sample file"""
    
    def test_analyze_file(self):
        """BugBacktracker should produce a single lineage with the correct fix commit"""
        backtracker = BugBacktracker(DESC_FILE, TEST_DATA_DIR)
        lineages = backtracker.analyze_file("code")
        
        self.assertEqual(len(lineages), 1)
        lineage = lineages[0]
        
        self.assertEqual(lineage.fix_version, 3)
        self.assertTrue(lineage.fix_commit.is_bug_fix)
    
    def test_trace_bug(self):
        backtracker = BugBacktracker(DESC_FILE, TEST_DATA_DIR)
        lineage = backtracker.trace_single_bug("code", bug_fix_version=3)
        
        self.assertEqual(lineage.fix_version, 3)
        self.assertIn("fix", lineage.fix_commit.message.lower())
        
        # Bug introduced in v1 
            # (report == null instead of != null)
        self.assertEqual(lineage.introduction_version, 1)
        self.assertGreater(lineage.confidence, 0.5)


class TestBugLineage(unittest.TestCase):
    
    def test_lineage_summary(self):
        backtracker = BugBacktracker(DESC_FILE, TEST_DATA_DIR)
        lineage = backtracker.trace_single_bug("code", bug_fix_version=3)
        
        summary = lineage.summary()
        
        self.assertIn("BUG LINEAGE REPORT", summary)
        self.assertIn("v3", summary)


class TestEdgeCases(unittest.TestCase):
    
    def test_nonexistent_file(self):
        history = CommitHistory(DESC_FILE, "nonexistent")
        commits = history.get_commits()
        self.assertEqual(len(commits), 0)


class TestAuthBug(unittest.TestCase):
    """Test bug backtracking for authentication with == vs equals() bug"""
    
    def test_auth_commits(self):
        history = CommitHistory(DESC_FILE, "auth")
        commits = history.get_commits()
        self.assertEqual(len(commits), 2)
    
    def test_auth_bug_fix(self):
        history = CommitHistory(DESC_FILE, "auth")
        bug_fixes = history.get_bug_fix_commits()
        # Should identify v2 as bug fix [== to equals()]
        self.assertTrue(any(commit.version == 2 for commit in bug_fixes))
    
    def test_auth_trace_bug(self):
        backtracker = BugBacktracker(DESC_FILE, TEST_DATA_DIR)
        lineage = backtracker.trace_single_bug("auth", bug_fix_version=2)
        
        self.assertEqual(lineage.fix_version, 2)
        # Bug introduced in v1 (Using [==] instead of [equals()])
        self.assertEqual(lineage.introduction_version, 1)
    
    def test_auth_extract_signature(self):
        loader = FileVersionLoader(TEST_DATA_DIR, "auth")
        before = loader.load_version(1)
        after = loader.load_version(2)
        
        signature = extract_bug_signature(before, after)
        self.assertFalse(signature.is_empty())


class TestListManagerBug(unittest.TestCase):
    """Test bug backtracking for list manager with bounds check bug"""
    
    def test_list_manager_commits(self):
        history = CommitHistory(DESC_FILE, "list_manager")
        commits = history.get_commits()
        self.assertEqual(len(commits), 4)
    
    def test_list_manager_bug_fix(self):
        history = CommitHistory(DESC_FILE, "list_manager")
        bug_fixes = history.get_bug_fix_commits()
        # Should identify v4 as bug fix (> to >= in bounds check)
        self.assertTrue(any(commit.version == 4 for commit in bug_fixes))
    
    def test_list_manager_trace_bug(self):
        backtracker = BugBacktracker(DESC_FILE, TEST_DATA_DIR)
        lineage = backtracker.trace_single_bug("list_manager", bug_fix_version=4)
        
        self.assertEqual(lineage.fix_version, 4)
        # Bug introduced in v3 (Using > instead of >= in bounds check)
        self.assertEqual(lineage.introduction_version, 3)
    
    def test_list_manager_versions(self):
        loader = FileVersionLoader(TEST_DATA_DIR, "list_manager")
        versions = loader.get_available_versions()
        self.assertEqual(versions, [1, 2, 3, 4])
    
    def test_list_manager_signature(self):
        loader = FileVersionLoader(TEST_DATA_DIR, "list_manager")
        before = loader.load_version(3)
        after = loader.load_version(4)
        
        signature = extract_bug_signature(before, after)
        self.assertFalse(signature.is_empty())
        # Should detect change in bounds check line
        self.assertGreater(len(signature.buggy_lines), 0)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestCommitHistory))
    suite.addTests(loader.loadTestsFromTestCase(TestFileVersionLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestBugSignature))
    suite.addTests(loader.loadTestsFromTestCase(TestLineMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestBugBacktracker))
    suite.addTests(loader.loadTestsFromTestCase(TestBugLineage))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthBug))
    suite.addTests(loader.loadTestsFromTestCase(TestListManagerBug))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    run_tests()