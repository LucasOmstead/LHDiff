"""
test runner for the full pipeline (preprocessing -> diff).
outputs results to output.txt.
"""

import sys
import os
import traceback
import re
from collections import defaultdict

#add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

OUTPUT_FILE = "output.txt"


def find_all_test_cases(test_cases_dir):
    """find all test case pairs in test_cases directory."""
    test_cases = {}
    
    if not os.path.exists(test_cases_dir):
        return test_cases
    
    #group files by test case number
    old_files = defaultdict(dict)  #{case_num: {ext: path}}
    new_files = defaultdict(dict)   #{case_num: {ext: path}}
    
    for filename in os.listdir(test_cases_dir):
        #match pattern: test_case_N_old.ext or test_case_N_new.ext
        old_match = re.match(r'test_case_(\d+)_old\.(.+)', filename)
        new_match = re.match(r'test_case_(\d+)_new\.(.+)', filename)
        
        if old_match:
            case_num = int(old_match.group(1))
            ext = old_match.group(2)
            old_files[case_num][ext] = os.path.join(test_cases_dir, filename)
        elif new_match:
            case_num = int(new_match.group(1))
            ext = new_match.group(2)
            new_files[case_num][ext] = os.path.join(test_cases_dir, filename)
    
    #match pairs by case number and extension
    for case_num in sorted(set(old_files.keys()) & set(new_files.keys())):
        #try to match by extension
        for ext in old_files[case_num]:
            if ext in new_files[case_num]:
                test_cases[case_num] = (
                    old_files[case_num][ext],
                    new_files[case_num][ext],
                    ext
                )
                break
    
    return test_cases


def run_test_case(old_path, new_path):
    """run a single test case and return the diff result."""
    try:
        from src.diff.preprocessing import preprocess_file
        from src.diff.diff_hybrid import get_diff_hybrid
        
        old_lines = preprocess_file(old_path)
        new_lines = preprocess_file(new_path)
        
        old = [[line] for line in old_lines]
        new = [[line] for line in new_lines]
        
        result = get_diff_hybrid(old, new)
        
        #verify we got a valid diff result
        assert len(result) > 0, "Should have diff result"
        assert any(":" in r or "~" in r or "+" in r or "-" in r for r in result), "Should have changes"
        
        return result
    except FileNotFoundError as e:
        print(f"✗ Test case file not found: {e}")
        return None
    except Exception as e:
        print(f"✗ Error processing test case: {e}")
        return None


def main():
    """run tests using test case files."""
    try:
        print("=" * 60)
        print("LHDiff Test Suite - All Test Case Files")
        print("=" * 60)
        
        #get test cases directory
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_cases_dir = os.path.join(test_dir, 'test_cases')
        
        #find all test case pairs
        test_cases = find_all_test_cases(test_cases_dir)
        
        if not test_cases:
            print(f"✗ No test case files found in {test_cases_dir}")
            return 1
        
        print(f"Found {len(test_cases)} test case pairs")
        print("=" * 60)
        
        #prepare output
        output_lines = []
        results = {}
        success_count = 0
        fail_count = 0
        
        #write header explaining diff format
        output_lines.append("x:y = exact match (line x in old matches line y in new)")
        output_lines.append("")
        output_lines.append("x~y = similarity match (line x in old is similar to line y in new)")
        output_lines.append("")
        output_lines.append("x- = deletion (line x deleted from old)")
        output_lines.append("")
        output_lines.append("x+ = insertion (line x inserted in new)")
        output_lines.append("")
        output_lines.append("")
        
        #run all test cases
        for case_num in sorted(test_cases.keys()):
            old_path, new_path, ext = test_cases[case_num]
            print(f"Testing case {case_num} ({ext})...", end=" ")
            
            result = run_test_case(old_path, new_path)
            
            if result is not None:
                results[case_num] = result
                output_lines.append(f"Test case {case_num}:")
                output_lines.append("")
                output_lines.append(str(result))
                output_lines.append("")
                print(f"✓")
                success_count += 1
            else:
                print(f"✗")
                fail_count += 1
        
        #write to output.txt
        output_path = os.path.join(os.path.dirname(__file__), '..', OUTPUT_FILE)
        output_path = os.path.abspath(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"✓ Passed: {success_count}")
        print(f"✗ Failed: {fail_count}")
        print(f"Total: {len(test_cases)} test cases")
        print(f"\n✓ Results written to {OUTPUT_FILE}")
        print("=" * 60)
        
        if fail_count == 0:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"ERROR: Exception: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
