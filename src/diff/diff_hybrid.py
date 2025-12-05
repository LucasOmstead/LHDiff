"""
Hybrid diff algorithm combining Myers algorithm (exact matching) 
with similarity-based matching for modified lines.

Returns diff in format:
- 'x:y' = exact match (line x in old matches line y in new)
- 'x~y' = similarity match (line x in old is similar to line y in new)
- 'x-' = deletion (line x deleted from old)
- 'x+' = insertion (line x inserted in new)
"""

from typing import List
from .diff import get_diff as get_diff_exact
from .matcher import match_lines
import hashlib


def get_diff_hybrid(old_file_text: List[List[str]], new_file_text: List[List[str]], 
                   similarity_threshold=0.6, use_similarity=True):
    """
    Hybrid diff: exact matches first, then similarity matching for remaining lines.
    
    Args:
        old_file_text: List of lines (each line is a list of strings)
        new_file_text: List of lines (each line is a list of strings)
        similarity_threshold: Minimum similarity score (0-1) for fuzzy matching
        use_similarity: If False, only use exact matching (fallback to Myers only)
    
    Returns:
        List of diff operations in format: ['x:y', 'x~y', 'x-', 'x+']
    """
    # Convert List[List[str]] to List[str] for similarity matching
    old_lines = [line[0] if isinstance(line, list) and len(line) > 0 else str(line) for line in old_file_text]
    new_lines = [line[0] if isinstance(line, list) and len(line) > 0 else str(line) for line in new_file_text]
    
    # Step 1: Get exact matches using Myers algorithm
    exact_diff = get_diff_exact(old_file_text, new_file_text)
    
    # Extract exact matches and track which lines are matched
    exact_matches = {}  # old_idx -> new_idx (0-based)
    old_matched = set()
    new_matched = set()
    
    for op in exact_diff:
        if ':' in op:
            # Exact match: 'x:y' (1-based from get_diff_exact, convert to 0-based)
            old_idx, new_idx = map(int, op.split(':'))
            old_idx_0based = old_idx - 1
            new_idx_0based = new_idx - 1
            exact_matches[old_idx_0based] = new_idx_0based
            old_matched.add(old_idx_0based)
            new_matched.add(new_idx_0based)
        elif op.endswith('-'):
            # Deletion: 'x-' (1-based from get_diff_exact, convert to 0-based)
            old_idx_1based = int(op[:-1])
            old_idx = old_idx_1based - 1
            # Don't mark as matched yet - might be similar to something
        elif op.endswith('+'):
            # Insertion: 'x+' (1-based from get_diff_exact, convert to 0-based)
            new_idx_1based = int(op[:-1])
            new_idx = new_idx_1based - 1
            # Don't mark as matched yet - might be similar to something
    
    # Step 2: Use similarity matching for unmatched lines (if enabled)
    similarity_matches = {}  # old_idx -> new_idx (0-based)
    
    if use_similarity:
        # Find unmatched old and new lines
        unmatched_old_indices = [i for i in range(len(old_lines)) if i not in old_matched]
        unmatched_new_indices = [i for i in range(len(new_lines)) if i not in new_matched]
        
        if unmatched_old_indices and unmatched_new_indices:
            # Get similarity matches
            unmatched_old_lines = [old_lines[i] for i in unmatched_old_indices]
            unmatched_new_lines = [new_lines[i] for i in unmatched_new_indices]
            
            # Use matcher to find similar lines
            matcher_results = match_lines(unmatched_old_lines, unmatched_new_lines, 
                                        similarity_threshold=similarity_threshold)
            
            # Convert matcher results (1-based) back to original indices (0-based)
            for old_1based, new_1based in matcher_results:
                if old_1based <= len(unmatched_old_indices) and new_1based <= len(unmatched_new_indices):
                    old_idx_0based = unmatched_old_indices[old_1based - 1]
                    new_idx_0based = unmatched_new_indices[new_1based - 1]
                    similarity_matches[old_idx_0based] = new_idx_0based
                    old_matched.add(old_idx_0based)
                    new_matched.add(new_idx_0based)
    
    # Step 3: Build final result combining exact and similarity matches
    result = []
    
    # Process all old lines in order (convert to 1-based for output)
    for old_idx in range(len(old_lines)):
        if old_idx in exact_matches:
            # Exact match (convert to 1-based)
            new_idx = exact_matches[old_idx]
            result.append(f"{old_idx+1}:{new_idx+1}")
        elif old_idx in similarity_matches:
            # Similarity match (convert to 1-based)
            new_idx = similarity_matches[old_idx]
            result.append(f"{old_idx+1}~{new_idx+1}")
        elif old_idx not in old_matched:
            # Pure deletion (convert to 1-based)
            result.append(f"{old_idx+1}-")
    
    # Add pure insertions (convert to 1-based)
    for new_idx in range(len(new_lines)):
        if new_idx not in new_matched:
            result.append(f"{new_idx+1}+")
    
    return result


def hash_diff(diff_result: List[str]) -> str:
    """
    Generate a hash of the diff result for verification/identification.
    
    Args:
        diff_result: List of diff operations
    
    Returns:
        Hexadecimal hash string
    """
    diff_str = '|'.join(diff_result)
    return hashlib.md5(diff_str.encode()).hexdigest()


def get_diff_with_hash(old_file_text: List[List[str]], new_file_text: List[List[str]], 
                      similarity_threshold=0.6, use_similarity=True):
    """
    Get diff result with hash.
    
    Returns:
        Dictionary with 'diff' and 'hash' keys
    """
    diff_result = get_diff_hybrid(old_file_text, new_file_text, 
                                 similarity_threshold, use_similarity)
    diff_hash = hash_diff(diff_result)
    return {"diff": diff_result, "hash": diff_hash}

