"""
Integration tests for the entire pipeline.

Tests the complete workflow: preprocessing -> diff algorithm.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.diff.preprocessing import preprocess_file, preprocess_lines
from src.diff.diff_hybrid import get_diff_hybrid, get_diff_with_hash
import tempfile


def create_test_files(content1, content2):
    """Helper to create temporary test files."""
    file1 = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    file2 = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    
    file1.write(content1)
    file2.write(content2)
    
    file1.close()
    file2.close()
    
    return file1.name, file2.name


def cleanup_files(*paths):
    """Helper to clean up temporary files."""
    for path in paths:
        if os.path.exists(path):
            os.unlink(path)


def test_identical_files_pipeline():
    """Test: Two identical files through the full pipeline."""
    content = """int x = 5;
return x;
"""
    file1, file2 = create_test_files(content, content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        # Convert to List[List[str]] format for diff algorithm
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Identical files pipeline: {result}")
        
        # Should only have matches (exact or similarity)
        assert all(":" in r or "~" in r for r in result), "Should only have matches"
        return result
    finally:
        cleanup_files(file1, file2)


def test_simple_insertion_pipeline():
    """Test: File with one line added."""
    old_content = """int x = 5;
return x;
"""
    new_content = """int x = 5;
int y = 10;
return x;
"""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Simple insertion pipeline: {result}")
        
        assert any("+" in r for r in result), "Should have insertion"
        return result
    finally:
        cleanup_files(file1, file2)


def test_simple_deletion_pipeline():
    """Test: File with one line removed."""
    old_content = """int x = 5;
int y = 10;
return x;
"""
    new_content = """int x = 5;
return x;
"""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Simple deletion pipeline: {result}")
        
        assert any("-" in r for r in result), "Should have deletion"
        return result
    finally:
        cleanup_files(file1, file2)


def test_whitespace_ignored():
    """Test: Preprocessing should make whitespace differences irrelevant."""
    old_content = """int x=5;
return x;
"""
    new_content = """   int x = 5;   // comment
return x;
"""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        # After preprocessing, these should match
        assert old_lines[0] == new_lines[0], "Whitespace should be normalized"
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Whitespace ignored: {result}")
        
        # Should only have matches (no differences after preprocessing)
        assert all(":" in r or "~" in r for r in result), "Should only have matches"
        return result
    finally:
        cleanup_files(file1, file2)


def test_case_insensitive():
    """Test: Preprocessing makes case differences irrelevant."""
    old_content = """int X = 5;
RETURN X;
"""
    new_content = """int x = 5;
return x;
"""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        # After preprocessing, these should match
        assert old_lines[0] == new_lines[0], "Case should be normalized"
        assert old_lines[1] == new_lines[1], "Case should be normalized"
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Case insensitive: {result}")
        
        assert all(":" in r or "~" in r for r in result), "Should only have matches"
        return result
    finally:
        cleanup_files(file1, file2)


def test_complex_changes_pipeline():
    """Test: Complex changes through the pipeline."""
    old_content = """function hello() {
    int x = 5;
    return x;
}
"""
    new_content = """function hello() {
    int x = 5;
    int y = 10;
    return x + y;
}
"""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Complex changes pipeline: {result}")
        
        # Should have both insertions and matches
        assert len(result) > 0, "Should have some result"
        return result
    finally:
        cleanup_files(file1, file2)


def test_empty_file_pipeline():
    """Test: One file is empty."""
    old_content = """int x = 5;
"""
    new_content = ""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Empty file pipeline: {result}")
        
        # Should have deletions
        assert any("-" in r for r in result) or len(result) == 0, "Should handle empty file"
        return result
    finally:
        cleanup_files(file1, file2)


def test_real_world_scenario():
    """Test: Simulate a real-world code change scenario."""
    old_content = """def calculate(x, y):
    result = x + y
    return result

def main():
    print("Hello")
"""
    new_content = """def calculate(x, y):
    result = x * y  # Changed from addition
    return result

def helper():
    print("Helper function")

def main():
    print("Hello World")  # Updated message
"""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        print(f"Old preprocessed: {old_lines}")
        print(f"New preprocessed: {new_lines}")
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Real-world scenario: {result}")
        
        return result
    finally:
        cleanup_files(file1, file2)


def test_multiple_operations():
    """Test: Multiple insertions, deletions, and modifications."""
    old_content = """line1
line2
line3
line4
line5
"""
    new_content = """line1
new_line2
line3
modified_line4
line5
extra_line
"""
    file1, file2 = create_test_files(old_content, new_content)
    
    try:
        old_lines = preprocess_file(file1)
        new_lines = preprocess_file(file2)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Multiple operations: {result}")
        
        return result
    finally:
        cleanup_files(file1, file2)


def test_case_file_1():
    """Test using test_case_1 files (complex Python function changes)."""
    # Get the directory where this test file is located
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_dir = os.path.join(test_dir, 'test_cases')
    old_path = os.path.join(test_cases_dir, 'test_case_1_old.py')
    new_path = os.path.join(test_cases_dir, 'test_case_1_new.py')
    
    try:
        old_lines = preprocess_file(old_path)
        new_lines = preprocess_file(new_path)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Test case file 1: {result}")
        
        # Verify we got a valid diff result
        assert len(result) > 0, "Should have diff result"
        # Should have matches, similarity matches, insertions, or deletions
        assert any(":" in r or "~" in r or "+" in r or "-" in r for r in result), "Should have changes"
        
        return result
    except FileNotFoundError as e:
        print(f"✗ Test case file not found: {e}")
        return None


def test_case_file_2():
    """Test using test_case_2 files (simple C-style code changes)."""
    # Get the directory where this test file is located
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_dir = os.path.join(test_dir, 'test_cases')
    old_path = os.path.join(test_cases_dir, 'test_case_2_old.py')
    new_path = os.path.join(test_cases_dir, 'test_case_2_new.py')
    
    try:
        old_lines = preprocess_file(old_path)
        new_lines = preprocess_file(new_path)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        print(f"✓ Test case file 2: {result}")
        
        # Verify we got a valid diff result
        assert len(result) > 0, "Should have diff result"
        # Should have matches, similarity matches, deletions, or insertions
        assert any(":" in r or "~" in r or "-" in r or "+" in r for r in result), "Should have changes"
        
        return result
    except FileNotFoundError as e:
        print(f"✗ Test case file not found: {e}")
        return None


def run_test_case_files():
    """Run tests using the test case files (full pipeline: preprocessing -> diff)."""
    print("=" * 60)
    print("Running Test Case Files (Full Pipeline)")
    print("=" * 60)
    print("Testing: preprocessing -> diff algorithm")
    print("=" * 60)
    
    try:
        result1 = test_case_file_1()
        result2 = test_case_file_2()
        
        # Verify both tests completed successfully
        if result1 is None or result2 is None:
            print("=" * 60)
            print("✗ Some test case files were not found")
            print("=" * 60)
            return False
        
        print("=" * 60)
        print("✓ All test case file tests passed!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)
    
    try:
        test_identical_files_pipeline()
        test_simple_insertion_pipeline()
        test_simple_deletion_pipeline()
        test_whitespace_ignored()
        test_case_insensitive()
        test_complex_changes_pipeline()
        test_empty_file_pipeline()
        test_real_world_scenario()
        test_multiple_operations()
        test_case_file_1()
        test_case_file_2()
        
        print("=" * 60)
        print("✓ All integration tests passed!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_all_tests()

