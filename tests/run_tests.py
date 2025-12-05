"""
Test runner script to execute tests using test case files.

Run this script to test the full pipeline (preprocessing -> diff):
    python tests/run_tests.py
    or
    python -m tests.run_tests

Outputs results to output.txt for use by generate_maps.py
"""

import sys
import os
import traceback

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

OUTPUT_FILE = "output.txt"


def main():
    """Run tests using test case files (full pipeline)."""
    print("=" * 60)
    print("LHDiff Test Suite - Test Case Files")
    print("=" * 60)
    
    # Open output file for writing
    output_lines = []
    
    try:
        # Import the test_integration module
        import test_integration
        
        # Run only the test case file tests
        success = test_integration.run_test_case_files()
        
        # Collect test results for output.txt
        # Get results from test_case_file_1 and test_case_file_2
        result1 = test_integration.test_case_file_1()
        result2 = test_integration.test_case_file_2()
        
        # Write header explaining diff format
        output_lines.append("x:y = exact match (line x in old matches line y in new)")
        output_lines.append("")
        output_lines.append("x~y = similarity match (line x in old is similar to line y in new)")
        output_lines.append("")
        output_lines.append("x- = deletion (line x deleted from old)")
        output_lines.append("")
        output_lines.append("x+ = insertion (line x inserted in new)")
        output_lines.append("")
        output_lines.append("")  # Extra blank line before test cases
        
        # Write results in format expected by generate_maps.py
        if result1 is not None:
            output_lines.append("Test case 1:")
            output_lines.append("")  # Empty line
            output_lines.append(str(result1))
            output_lines.append("")  # Empty line
        
        if result2 is not None:
            output_lines.append("Test case 2:")
            output_lines.append("")  # Empty line
            output_lines.append(str(result2))
            output_lines.append("")  # Empty line
        
        # Write to output.txt
        output_path = os.path.join(os.path.dirname(__file__), '..', OUTPUT_FILE)
        output_path = os.path.abspath(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"\n✓ Results written to {OUTPUT_FILE}")
        
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
