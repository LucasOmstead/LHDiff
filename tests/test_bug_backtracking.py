"""
test_bug_backtracking.py

Tests for the bug backtracking feature.
Based on real code example with null check bug.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import CommitInfo, FileVersion, BugSignature, BugLineage, LineMapping
from src.commit_history import CommitHistory
from src.file_version_loader import FileVersionLoader
from src.bug_signature import extract_bug_signature, build_line_mapping
from src.bug_backtracker import BugBacktracker, backtrack_bug_to_origin


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "bug_backtracking")
DESC_FILE = os.path.join(TEST_DATA_DIR, "desc.txt")


class TestCommitHistory(unittest.TestCase):
    
    def test_parse_commits(self):
        history = CommitHistory(DESC_FILE, "code")
        commits = history.get_commits()
        
        self.assertEqual(len(commits), 3)
        self.assertEqual(commits[0].version, 1)
    
    def test_identify_bug_fixes(self):
        history = CommitHistory(DESC_FILE, "code")
        bug_fixes = history.get_bug_fix_commits()
        
        self.assertEqual(len(bug_fixes), 1)
        self.assertEqual(bug_fixes[0].version, 3)


class TestFileVersionLoader(unittest.TestCase):
    
    def test_load_version(self):
        loader = FileVersionLoader(TEST_DATA_DIR, "code")
        version = loader.load_version(1)
        
        self.assertEqual(version.version, 1)
        self.assertGreater(len(version.lines), 0)
    
    def test_get_available_versions(self):
        loader = FileVersionLoader(TEST_DATA_DIR, "code")
        versions = loader.get_available_versions()
        
        self.assertEqual(versions, [1, 2, 3])


class TestBugSignature(unittest.TestCase):
    
    def test_extract_signature(self):
        loader = FileVersionLoader(TEST_DATA_DIR, "code")
        before = loader.load_version(2)
        after = loader.load_version(3)
        
        signature = extract_bug_signature(before, after)
        
        self.assertFalse(signature.is_empty())
        self.assertGreater(len(signature.buggy_lines), 0)


class TestLineMapping(unittest.TestCase):
    
    def test_build_mapping(self):
        diff_ops = ['0:0', '1~1', '2:2']
        mapping = build_line_mapping(diff_ops, 0, 1)
        
        self.assertEqual(mapping.exact_matches[0], 0)
        self.assertEqual(mapping.exact_matches[2], 2)
        self.assertEqual(mapping.similarity_matches[1], 1)


class TestBugBacktracker(unittest.TestCase):
    
    def test_analyze_file(self):
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
        
        # Bug introduced in v1 (report == null instead of != null)
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
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    run_tests()
