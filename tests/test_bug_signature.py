"""
Test suite for bug_signature.py

Tests bug signature extraction from bug fix diffs.
"""

import sys
import os
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import FileVersion
from src.diff.preprocessing import preprocess_lines
from src.bug_tracking.bug_signature import extract_bug_signature, build_line_mapping, compute_diff_and_mapping


class TestBugSignatureExtraction(unittest.TestCase):
    """Test extract_bug_signature function."""
    
    def create_file_version(self, version: int, lines: list) -> FileVersion:
        """Helper to create a FileVersion."""
        preprocessed = preprocess_lines(lines)
        return FileVersion(
            version=version,
            file_path=f"test_v{version}.txt",
            lines=lines,
            preprocessed=preprocessed
        )
    
    def test_extract_deletion_signature(self):
        """Test extracting signature from deletion fix."""
        before = self.create_file_version(1, [
            "def calculate(x, y):",
            "    result = x + y  # BUG: should be *",
            "    return result"
        ])
        
        after = self.create_file_version(2, [
            "def calculate(x, y):",
            "    result = x * y",
            "    return result"
        ])
        
        signature = extract_bug_signature(before, after)
        
        self.assertFalse(signature.is_empty())
        self.assertGreater(len(signature.buggy_lines), 0)
        self.assertIn("modification", signature.fix_type.lower())
        self.assertGreater(len(signature.line_numbers), 0)
    
    def test_extract_modification_signature(self):
        """Test extracting signature from modification fix."""
        before = self.create_file_version(1, [
            "if x == null:  # BUG: should be != null",
            "    return True"
        ])
        
        after = self.create_file_version(2, [
            "if x != null:",
            "    return True"
        ])
        
        signature = extract_bug_signature(before, after)
        
        self.assertFalse(signature.is_empty())
        self.assertEqual(signature.fix_type, "modification")
        self.assertEqual(len(signature.buggy_lines), 1)
    
    def test_extract_deletion_only_signature(self):
        """Test extracting signature from deletion-only fix."""
        before = self.create_file_version(1, [
            "def old_function():",
            "    pass  # BUG: should be removed",
            "def new_function():",
            "    pass"
        ])
        
        after = self.create_file_version(2, [
            "def new_function():",
            "    pass"
        ])
        
        signature = extract_bug_signature(before, after)
        
        self.assertFalse(signature.is_empty())
        self.assertIn("deletion", signature.fix_type.lower())
        self.assertGreater(len(signature.buggy_lines), 0)
    
    def test_extract_insertion_fix(self):
        """Test extracting signature from insertion fix."""
        before = self.create_file_version(1, [
            "def calculate(x, y):",
            "    return x + y"
        ])
        
        after = self.create_file_version(2, [
            "def calculate(x, y):",
            "    if x is None:  # FIX: add null check",
            "        return 0",
            "    return x + y"
        ])
        
        signature = extract_bug_signature(before, after)
        
        # Insertion-only fixes might have empty signature
        # (no buggy lines, just missing code)
        self.assertIsNotNone(signature)
        self.assertIn("insertion", signature.fix_type.lower())
    
    def test_extract_context(self):
        """Test that context is extracted correctly."""
        before = self.create_file_version(1, [
            "def helper():",
            "    pass",
            "def calculate(x, y):",
            "    result = x + y  # BUG",
            "    return result",
            "def main():",
            "    pass"
        ])
        
        after = self.create_file_version(2, [
            "def helper():",
            "    pass",
            "def calculate(x, y):",
            "    result = x * y",
            "    return result",
            "def main():",
            "    pass"
        ])
        
        signature = extract_bug_signature(before, after, context_window=2)
        
        # Should have context before and after
        self.assertGreater(len(signature.context_before), 0)
        self.assertGreater(len(signature.context_after), 0)
    
    def test_empty_signature_for_identical_files(self):
        """Test that identical files produce empty signature."""
        lines = ["def test():", "    pass"]
        before = self.create_file_version(1, lines)
        after = self.create_file_version(2, lines)
        
        signature = extract_bug_signature(before, after)
        
        self.assertTrue(signature.is_empty())


class TestLineMapping(unittest.TestCase):
    """Test build_line_mapping function."""
    
    def test_build_mapping_exact_matches(self):
        """Test building mapping with exact matches."""
        diff_ops = ['1:1', '2:2', '3:3']
        mapping = build_line_mapping(diff_ops, 0, 1)
        
        self.assertEqual(mapping.exact_matches[1], 1)
        self.assertEqual(mapping.exact_matches[2], 2)
        self.assertEqual(mapping.exact_matches[3], 3)
        self.assertEqual(len(mapping.exact_matches), 3)
    
    def test_build_mapping_similarity_matches(self):
        """Test building mapping with similarity matches."""
        diff_ops = ['1:1', '2~3', '4:4']
        mapping = build_line_mapping(diff_ops, 0, 1)
        
        self.assertEqual(mapping.exact_matches[1], 1)
        self.assertEqual(mapping.similarity_matches[3], 2)
        self.assertEqual(mapping.exact_matches[4], 4)
    
    def test_build_mapping_deletions(self):
        """Test building mapping with deletions."""
        diff_ops = ['1:1', '2-', '3:2']
        mapping = build_line_mapping(diff_ops, 0, 1)
        
        self.assertIn(2, mapping.deletions)
        self.assertEqual(mapping.exact_matches[1], 1)
        self.assertEqual(mapping.exact_matches[2], 3)
    
    def test_build_mapping_insertions(self):
        """Test building mapping with insertions."""
        diff_ops = ['1:1', '2+', '2:3']
        mapping = build_line_mapping(diff_ops, 0, 1)
        
        self.assertIn(2, mapping.insertions)
        self.assertEqual(mapping.exact_matches[1], 1)
        self.assertEqual(mapping.exact_matches[3], 2)
    
    def test_build_mapping_complex(self):
        """Test building mapping with complex diff."""
        diff_ops = ['1:1', '2-', '3~2', '4:4', '5+']
        mapping = build_line_mapping(diff_ops, 0, 1)
        
        self.assertEqual(mapping.exact_matches[1], 1)
        self.assertIn(2, mapping.deletions)
        self.assertEqual(mapping.similarity_matches[2], 3)
        self.assertEqual(mapping.exact_matches[4], 4)
        self.assertIn(5, mapping.insertions)


class TestComputeDiffAndMapping(unittest.TestCase):
    """Test compute_diff_and_mapping function."""
    
    def create_file_version(self, version: int, lines: list) -> FileVersion:
        """Helper to create a FileVersion."""
        preprocessed = preprocess_lines(lines)
        return FileVersion(
            version=version,
            file_path=f"test_v{version}.txt",
            lines=lines,
            preprocessed=preprocessed
        )
    
    def test_compute_diff_and_mapping(self):
        """Test computing diff and mapping together."""
        before = self.create_file_version(1, [
            "def test():",
            "    x = 5",
            "    return x"
        ])
        
        after = self.create_file_version(2, [
            "def test():",
            "    x = 10",
            "    return x"
        ])
        
        diff_ops, mapping = compute_diff_and_mapping(before, after)
        
        self.assertIsNotNone(diff_ops)
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.old_version, 1)
        self.assertEqual(mapping.new_version, 2)
        self.assertGreater(len(diff_ops), 0)
    
    def test_compute_diff_identical_files(self):
        """Test computing diff for identical files."""
        lines = ["def test():", "    pass"]
        before = self.create_file_version(1, lines)
        after = self.create_file_version(2, lines)
        
        diff_ops, mapping = compute_diff_and_mapping(before, after)
        
        # Should have matches, no deletions/insertions
        self.assertIsNotNone(diff_ops)
        self.assertIsNotNone(mapping)


def run_all_tests():
    """Run all bug signature tests."""
    print("=" * 60)
    print("Running Bug Signature Tests")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestBugSignatureExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestLineMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestComputeDiffAndMapping))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    if result.wasSuccessful():
        print("✓ All bug signature tests passed!")
        print("=" * 60)
        return True
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return False


if __name__ == "__main__":
    run_all_tests()

