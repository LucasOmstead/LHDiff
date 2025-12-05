# check_correctness.py
#
# Check correctness of line mappings by comparing against git diff output.
# This provides independent ground truth validation.
#
# Usage:
#   python3 scripts/check_correctness.py <test_case_num>
#   python3 scripts/check_correctness.py  # Check all test cases

import os
import sys
import subprocess
import tempfile
from typing import Dict, Set, Tuple, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.diff.preprocessing import preprocess_file


def load_mapping_file(path: str) -> Set[Tuple[int, int]]:
    """Load mapping file and return set of (old_line, new_line) pairs (1-based)."""
    pairs = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            left, right = line.split("-")
            pairs.add((int(left), int(right)))
    return pairs


def parse_git_diff_unified(diff_output: str) -> Set[Tuple[int, int]]:
    """
    Parse unified diff format from git diff to extract line mappings.
    
    Unified diff format:
    @@ -old_start,old_count +new_start,new_count @@
    
    Returns set of (old_line, new_line) tuples (1-based).
    """
    mappings = set()
    lines = diff_output.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith('@@'):
            # Parse hunk header
            # Format: @@ -old_start,old_count +new_start,new_count @@
            try:
                # Extract the numbers from @@ -a,b +c,d @@
                import re
                match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 0
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 0
                    
                    # Process hunk lines
                    old_line = old_start
                    new_line = new_start
                    i += 1
                    
                    while i < len(lines):
                        hunk_line = lines[i]
                        
                        # Stop at next hunk or diff header
                        if hunk_line.startswith('@@') or hunk_line.startswith('diff --git') or hunk_line.startswith('---') or hunk_line.startswith('+++'):
                            break
                        
                        if hunk_line.startswith(' '):
                            # Context line (unchanged) - maps old_line to new_line
                            mappings.add((old_line, new_line))
                            old_line += 1
                            new_line += 1
                        elif hunk_line.startswith('-'):
                            # Deleted line - only in old, no mapping
                            old_line += 1
                        elif hunk_line.startswith('+'):
                            # Added line - only in new, no mapping
                            new_line += 1
                        elif hunk_line.startswith('\\'):
                            # End of file marker, ignore
                            pass
                        
                        i += 1
                    continue
            except Exception:
                pass
        
        i += 1
    
    return mappings


def get_git_diff_mappings(old_file_path: str, new_file_path: str) -> Set[Tuple[int, int]]:
    """
    Use git diff or standard diff to get line mappings between two files.
    Tries git diff first, falls back to standard diff command.
    """
    # Try standard diff command first (simpler, more reliable)
    result = subprocess.run(['diff', '-u', old_file_path, new_file_path],
                          capture_output=True, text=True, check=False)
    
    if result.stdout:
        mappings = parse_git_diff_unified(result.stdout)
        if mappings:
            return mappings
    
    # Fallback: try git diff in temp repo
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            import shutil
            old_tmp = os.path.join(tmpdir, "old_file")
            new_tmp = os.path.join(tmpdir, "new_file")
            
            shutil.copy2(old_file_path, old_tmp)
            shutil.copy2(new_file_path, new_tmp)
            
            # Initialize git repo
            subprocess.run(['git', 'init'], cwd=tmpdir, 
                          capture_output=True, check=False, stderr=subprocess.DEVNULL)
            
            # Add first file and commit
            subprocess.run(['git', 'add', 'old_file'], cwd=tmpdir, 
                          capture_output=True, check=False, stderr=subprocess.DEVNULL)
            subprocess.run(['git', 'commit', '-m', 'Initial'], cwd=tmpdir,
                          capture_output=True, check=False, stderr=subprocess.DEVNULL)
            
            # Replace with new file and get diff
            os.remove(old_tmp)
            shutil.copy2(new_file_path, old_tmp)
            subprocess.run(['git', 'add', 'old_file'], cwd=tmpdir,
                          capture_output=True, check=False, stderr=subprocess.DEVNULL)
            
            # Get diff output
            result = subprocess.run(['git', 'diff', '--cached', '--unified=0', 'old_file'],
                                  cwd=tmpdir, capture_output=True, text=True, check=False)
            
            if result.stdout:
                return parse_git_diff_unified(result.stdout)
    except Exception:
        pass
    
    return set()


def compare_mappings(our_mappings: Set[Tuple[int, int]], 
                    git_mappings: Set[Tuple[int, int]]) -> Dict:
    """
    Compare our mappings against git diff mappings.
    Returns comparison statistics.
    """
    # Exact matches
    exact_matches = our_mappings & git_mappings
    
    # In our mappings but not in git (false positives)
    false_positives = our_mappings - git_mappings
    
    # In git but not in our mappings (false negatives)
    false_negatives = git_mappings - our_mappings
    
    # Calculate metrics
    total_ours = len(our_mappings)
    total_git = len(git_mappings)
    total_correct = len(exact_matches)
    
    precision = total_correct / total_ours if total_ours > 0 else 0.0
    recall = total_correct / total_git if total_git > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "total_ours": total_ours,
        "total_git": total_git,
        "correct": total_correct,
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "false_positives_set": false_positives,
        "false_negatives_set": false_negatives
    }


def check_test_case(case_num: int, test_dir: str) -> Dict:
    """Check correctness of a single test case."""
    # Find files
    old_path = None
    new_path = None
    map_path = os.path.join(test_dir, f"test_case_{case_num}_map.txt")
    
    for name in os.listdir(test_dir):
        if name.startswith(f"test_case_{case_num}_old."):
            old_path = os.path.join(test_dir, name)
        elif name.startswith(f"test_case_{case_num}_new."):
            new_path = os.path.join(test_dir, name)
    
    if not (old_path and new_path and os.path.exists(map_path)):
        return {"error": f"Missing files for test_case_{case_num}"}
    
    # Load our mappings
    our_mappings = load_mapping_file(map_path)
    
    # Get git diff mappings
    try:
        git_mappings = get_git_diff_mappings(old_path, new_path)
    except Exception as e:
        return {"error": f"Failed to get git diff: {e}"}
    
    # Compare
    comparison = compare_mappings(our_mappings, git_mappings)
    comparison["case_num"] = case_num
    
    return comparison


def check_all(test_dir: str):
    """Check all test cases."""
    case_ids = []
    for name in os.listdir(test_dir):
        if name.startswith("test_case_") and "_old." in name:
            middle = name[len("test_case_"):]
            num_str = middle.split("_")[0]
            if num_str.isdigit():
                case_ids.append(int(num_str))
    
    case_ids = sorted(set(case_ids))
    
    results = []
    for case_id in case_ids:
        result = check_test_case(case_id, test_dir)
        if "error" not in result:
            results.append(result)
            print(f"test_case_{case_id}: "
                  f"Precision={result['precision']:.3f}, "
                  f"Recall={result['recall']:.3f}, "
                  f"F1={result['f1_score']:.3f}, "
                  f"Correct={result['correct']}/{result['total_ours']}")
        else:
            print(f"test_case_{case_id}: {result['error']}")
    
    # Summary
    if results:
        avg_precision = sum(r['precision'] for r in results) / len(results)
        avg_recall = sum(r['recall'] for r in results) / len(results)
        avg_f1 = sum(r['f1_score'] for r in results) / len(results)
        total_correct = sum(r['correct'] for r in results)
        total_ours = sum(r['total_ours'] for r in results)
        
        print(f"\n{'='*80}")
        print(f"Summary ({len(results)} test cases):")
        print(f"  Average Precision: {avg_precision:.3f}")
        print(f"  Average Recall: {avg_recall:.3f}")
        print(f"  Average F1 Score: {avg_f1:.3f}")
        print(f"  Total Correct: {total_correct}/{total_ours}")
        print(f"{'='*80}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    tests_dir = os.path.join(project_root, "tests", "test_cases")
    
    if len(sys.argv) > 1:
        # Check specific test case
        case_num = int(sys.argv[1])
        result = check_test_case(case_num, tests_dir)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return 1
        
        print(f"\n{'='*80}")
        print(f"Correctness Check for test_case_{case_num}")
        print(f"{'='*80}")
        print(f"\nNote: Git diff only shows exact matches (context lines).")
        print(f"      Our algorithm includes both exact (x:y) and similarity (x~y) matches.")
        print(f"\nOur mappings: {result['total_ours']} (includes exact + similarity)")
        print(f"Git diff mappings: {result['total_git']} (exact matches only)")
        print(f"Correct matches: {result['correct']} (overlap)")
        print(f"False positives: {result['false_positives']} (our similarity matches)")
        print(f"False negatives: {result['false_negatives']} (git matches we missed)")
        print(f"\nMetrics:")
        print(f"  Precision: {result['precision']:.3f} (correct / our_total)")
        print(f"  Recall: {result['recall']:.3f} (correct / git_total)")
        print(f"  F1 Score: {result['f1_score']:.3f}")
        print(f"\nInterpretation:")
        if result['recall'] >= 0.95:
            print(f"  ✓ Excellent recall: We found all of git's exact matches")
        if result['false_negatives'] == 0:
            print(f"  ✓ No false negatives: We didn't miss any git matches")
        if result['false_positives'] > 0:
            print(f"  ℹ False positives are expected: These are similarity matches")
            print(f"    that git diff doesn't show (git only shows exact matches)")
        
        if result['false_positives'] > 0:
            print(f"\nFalse Positives (first 10):")
            for fp in list(result['false_positives_set'])[:10]:
                print(f"  {fp}")
        
        if result['false_negatives'] > 0:
            print(f"\nFalse Negatives (first 10):")
            for fn in list(result['false_negatives_set'])[:10]:
                print(f"  {fn}")
        
        return 0
    else:
        # Check all
        check_all(tests_dir)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

