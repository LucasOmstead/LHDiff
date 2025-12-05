"""
diff_hybrid.py - combines myers (exact) with similarity-based matching.

output format:
- 'x:y' = exact match
- 'x~y' = similarity match  
- 'x-' = deletion
- 'x+' = insertion
"""

from typing import List
from .diff import get_diff as get_diff_exact
from .matcher import match_lines
import hashlib


def get_diff_hybrid(old_file_text: List[List[str]], new_file_text: List[List[str]], 
                   similarity_threshold=0.6, use_similarity=True):
    """hybrid diff: exact matches first, then similarity matching for remaining lines."""
    #convert List[List[str]] to List[str] for similarity matching
    old_lines = [line[0] if isinstance(line, list) and len(line) > 0 else str(line) for line in old_file_text]
    new_lines = [line[0] if isinstance(line, list) and len(line) > 0 else str(line) for line in new_file_text]
    
    #get exact matches using myers algorithm
    exact_diff = get_diff_exact(old_file_text, new_file_text)
    
    #extract exact matches and track matched lines
    exact_matches = {}
    old_matched = set()
    new_matched = set()
    
    for op in exact_diff:
        if ':' in op:
            #exact match (convert 1-based to 0-based)
            old_idx, new_idx = map(int, op.split(':'))
            old_idx_0based = old_idx - 1
            new_idx_0based = new_idx - 1
            exact_matches[old_idx_0based] = new_idx_0based
            old_matched.add(old_idx_0based)
            new_matched.add(new_idx_0based)
        elif op.endswith('-'):
            #deletion (convert to 0-based)
            old_idx_1based = int(op[:-1])
            old_idx = old_idx_1based - 1
        elif op.endswith('+'):
            #insertion (convert to 0-based)
            new_idx_1based = int(op[:-1])
            new_idx = new_idx_1based - 1
    
    #use similarity matching for unmatched lines
    similarity_matches = {}
    
    if use_similarity:
        unmatched_old_indices = [i for i in range(len(old_lines)) if i not in old_matched]
        unmatched_new_indices = [i for i in range(len(new_lines)) if i not in new_matched]
        
        if unmatched_old_indices and unmatched_new_indices:
            unmatched_old_lines = [old_lines[i] for i in unmatched_old_indices]
            unmatched_new_lines = [new_lines[i] for i in unmatched_new_indices]
            
            matcher_results = match_lines(unmatched_old_lines, unmatched_new_lines, 
                                        similarity_threshold=similarity_threshold)
            
            #convert back to original indices
            for old_1based, new_1based in matcher_results:
                if old_1based <= len(unmatched_old_indices) and new_1based <= len(unmatched_new_indices):
                    old_idx_0based = unmatched_old_indices[old_1based - 1]
                    new_idx_0based = unmatched_new_indices[new_1based - 1]
                    similarity_matches[old_idx_0based] = new_idx_0based
                    old_matched.add(old_idx_0based)
                    new_matched.add(new_idx_0based)
    
    #build final result
    result = []
    
    for old_idx in range(len(old_lines)):
        if old_idx in exact_matches:
            new_idx = exact_matches[old_idx]
            result.append(f"{old_idx+1}:{new_idx+1}")
        elif old_idx in similarity_matches:
            new_idx = similarity_matches[old_idx]
            result.append(f"{old_idx+1}~{new_idx+1}")
        elif old_idx not in old_matched:
            result.append(f"{old_idx+1}-")
    
    #add insertions
    for new_idx in range(len(new_lines)):
        if new_idx not in new_matched:
            result.append(f"{new_idx+1}+")
    
    return result


def hash_diff(diff_result: List[str]) -> str:
    """generate md5 hash of diff result."""
    diff_str = '|'.join(diff_result)
    return hashlib.md5(diff_str.encode()).hexdigest()


def get_diff_with_hash(old_file_text: List[List[str]], new_file_text: List[List[str]], 
                      similarity_threshold=0.6, use_similarity=True):
    """get diff result with hash."""
    diff_result = get_diff_hybrid(old_file_text, new_file_text, 
                                 similarity_threshold, use_similarity)
    diff_hash = hash_diff(diff_result)
    return {"diff": diff_result, "hash": diff_hash}

