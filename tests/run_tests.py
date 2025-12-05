"""
Test runner script to execute tests using test case files.

Run this script to test the full pipeline (preprocessing -> diff):
    python tests/run_tests.py
    or
    python -m tests.run_tests
"""

import sys
import os
import traceback

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main():
    """Run tests using test case files (full pipeline)."""
    print("=" * 60)
    print("LHDiff Test Suite - Test Case Files")
    print("=" * 60)
    
    try:
        # Import the test_integration module
        import test_integration
        
        # Run only the test case file tests
        success = test_integration.run_test_case_files()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        if success:
            print("✓ PASSED: Test case files")
            print("\nTotal: 1/1 test suites passed")
            print("=" * 60)
            print("🎉 All tests passed!")
            return 0
        else:
            print("✗ FAILED: Test case files")
            print("\nTotal: 0/1 test suites passed")
            print("=" * 60)
            print("❌ Some tests failed")
            return 1
            
    except ImportError as e:
        print(f"ERROR: Could not import test_integration: {e}")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"ERROR: Exception: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
