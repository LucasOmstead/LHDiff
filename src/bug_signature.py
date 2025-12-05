"""
bug_signature.py

Extracts bug signatures from bug fix diffs.
A bug signature represents the "buggy code" that was fixed,
used to search backward through history.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Tuple, Optional
from .models import FileVersion, BugSignature, LineMapping
from .preprocessing import preprocess_lines
from diff_hybrid import get_diff_hybrid


def extract_bug_signature(
    file_before_fix: FileVersion,
    file_after_fix: FileVersion,
    context_window: int = 3
) -> BugSignature:
    """
    Analyze the bug fix diff to identify what was buggy.
    
    Args:
        file_before_fix: FileVersion before the bug fix (contains bug)
        file_after_fix: FileVersion after the bug fix (bug is fixed)
        context_window: Number of lines before/after bug for context
        
    Returns:
        BugSignature object representing the buggy code pattern
    """
    # Convert to format expected by diff algorithm
    old_for_diff = [[line] for line in file_before_fix.preprocessed]
    new_for_diff = [[line] for line in file_after_fix.preprocessed]
    
    # Get hybrid diff
    diff_ops = get_diff_hybrid(old_for_diff, new_for_diff)
    
    # Parse diff to identify buggy lines
    buggy_line_numbers = []
    fix_type_counts = {"deletion": 0, "modification": 0, "insertion": 0}
    
    for op in diff_ops:
        if op.endswith('-'):
            # Deletion: line was removed (was buggy)
            line_num = int(op[:-1])
            buggy_line_numbers.append(line_num)
            fix_type_counts["deletion"] += 1
        elif '~' in op:
            # Modification: line was changed (was buggy)
            old_num, new_num = op.split('~')
            buggy_line_numbers.append(int(old_num))
            fix_type_counts["modification"] += 1
        elif op.endswith('+'):
            # Insertion: new line added (might be fix for missing code)
            fix_type_counts["insertion"] += 1
    
    # Determine fix type
    if fix_type_counts["modification"] > 0:
        fix_type = "modification"
    elif fix_type_counts["deletion"] > 0 and fix_type_counts["insertion"] > 0:
        fix_type = "complex"
    elif fix_type_counts["deletion"] > 0:
        fix_type = "deletion"
    elif fix_type_counts["insertion"] > 0:
        fix_type = "insertion_fix"
    else:
        fix_type = "unknown"
    
    # Extract buggy lines from before-fix file
    buggy_lines = []
    buggy_lines_normalized = []
    
    for line_num in buggy_line_numbers:
        if 0 <= line_num < len(file_before_fix.lines):
            buggy_lines.append(file_before_fix.lines[line_num])
            buggy_lines_normalized.append(file_before_fix.preprocessed[line_num])
    
    # Extract context
    context_before = []
    context_after = []
    
    if buggy_line_numbers:
        min_line = min(buggy_line_numbers)
        max_line = max(buggy_line_numbers)
        
        # Context before
        start = max(0, min_line - context_window)
        for i in range(start, min_line):
            if i < len(file_before_fix.lines):
                context_before.append(file_before_fix.lines[i])
        
        # Context after
        end = min(len(file_before_fix.lines), max_line + context_window + 1)
        for i in range(max_line + 1, end):
            if i < len(file_before_fix.lines):
                context_after.append(file_before_fix.lines[i])
    
    return BugSignature(
        buggy_lines=buggy_lines,
        buggy_lines_normalized=buggy_lines_normalized,
        line_numbers=buggy_line_numbers,
        context_before=context_before,
        context_after=context_after,
        fix_type=fix_type,
        fix_operations=diff_ops
    )


def build_line_mapping(
    diff_operations: List[str],
    old_version: int,
    new_version: int
) -> LineMapping:
    """
    Parse diff operations to create line number mapping.
    
    Args:
        diff_operations: List of diff ops from hybrid diff
        old_version: Version number of old file
        new_version: Version number of new file
        
    Returns:
        LineMapping object for translating line numbers
    """
    mapping = LineMapping(
        old_version=old_version,
        new_version=new_version
    )
    
    for op in diff_operations:
        if ':' in op and '~' not in op:
            # Exact match: "x:y"
            old_num, new_num = map(int, op.split(':'))
            mapping.exact_matches[new_num] = old_num
        elif '~' in op:
            # Similarity match: "x~y"
            old_num, new_num = map(int, op.split('~'))
            mapping.similarity_matches[new_num] = old_num
        elif op.endswith('-'):
            # Deletion: "x-"
            old_num = int(op[:-1])
            mapping.deletions.add(old_num)
        elif op.endswith('+'):
            # Insertion: "x+"
            new_num = int(op[:-1])
            mapping.insertions.add(new_num)
    
    return mapping


def compute_diff_and_mapping(
    file_old: FileVersion,
    file_new: FileVersion
) -> Tuple[List[str], LineMapping]:
    """
    Compute diff between two versions and build line mapping.
    
    Args:
        file_old: Older file version
        file_new: Newer file version
        
    Returns:
        Tuple of (diff_operations, LineMapping)
    """
    # Convert to format expected by diff algorithm
    old_for_diff = [[line] for line in file_old.preprocessed]
    new_for_diff = [[line] for line in file_new.preprocessed]
    
    # Get hybrid diff
    diff_ops = get_diff_hybrid(old_for_diff, new_for_diff)
    
    # Build line mapping
    mapping = build_line_mapping(diff_ops, file_old.version, file_new.version)
    
    return diff_ops, mapping

