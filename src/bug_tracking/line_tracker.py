"""
Tracks line numbers through multiple file versions using diff mappings
"""

from typing import List, Optional, Dict
from ..models import FileVersion, LineMapping, LineHistory, BugSignature, BugMatch
from .bug_signature import compute_diff_and_mapping
from ..diff.matcher import normalized_levenshtein, cosine_similarity, combined_similarity


def track_line_backward(
    line_num: int,
    line_mappings: List[LineMapping]
) -> LineHistory:
    """Follow a line number backward through multiple versions"""
    history = LineHistory()
    current_line = line_num
    
    # Start with newest version
    if line_mappings:
        newest_version = line_mappings[0].new_version
        history.add_version(newest_version, current_line)
    
    # Walk through mappings (newest to oldest)
    for mapping in line_mappings:
        old_line = mapping.get_old_line(current_line)
        
        if old_line is None:
            # Line was inserted in this version
            history.introduction_version = mapping.new_version
            break
        
        # Add to history
        history.add_version(mapping.old_version, old_line)
        current_line = old_line
    
    # If traced all the way back, introduction is at earliest version
    if history.introduction_version is None and history.evolution:
        history.introduction_version = history.evolution[-1][0]
    
    return history


def track_lines_backward(
    line_numbers: List[int],
    line_mappings: List[LineMapping]
) -> Dict[int, LineHistory]:
    """Track multiple lines backward through versions"""
    histories = {}
    for line_num in line_numbers:
        histories[line_num] = track_line_backward(line_num, line_mappings)
    return histories


def find_bug_in_version(
    file_version: FileVersion,
    bug_signature: BugSignature,
    threshold: float = 0.7
) -> Optional[BugMatch]:
    """Search for bug signature in a file version"""
    if bug_signature.is_empty():
        return None
    
    buggy_lines = bug_signature.buggy_lines_normalized
    num_buggy = len(buggy_lines)
    
    if num_buggy == 0:
        return None
    
    file_lines = file_version.preprocessed
    
    if len(file_lines) < num_buggy:
        return None
    
    best_match = None
    best_score = 0.0
    
    # Sliding window search
    for start_idx in range(len(file_lines) - num_buggy + 1):
        window = file_lines[start_idx:start_idx + num_buggy]
        
        # Calculate similarity for each line pair
        line_scores = []
        for i, (bug_line, window_line) in enumerate(zip(buggy_lines, window)):
            if not bug_line.strip() and not window_line.strip():
                # Both empty lines indicates a perfect match
                line_scores.append(1.0)
            elif not bug_line.strip() or not window_line.strip():
                # One empty, one not indicates no match
                line_scores.append(0.0)
            else:
                score = normalized_levenshtein(bug_line, window_line)
                line_scores.append(score)
        
        # Average similarity across all lines
        if line_scores:
            avg_score = sum(line_scores) / len(line_scores)
            
            # Boost score if context matches
            context_boost = _calculate_context_boost(
                file_version, start_idx, num_buggy, bug_signature
            )
            
            final_score = 0.8 * avg_score + 0.2 * context_boost
            
            if final_score > best_score and final_score >= threshold:
                best_score = final_score
                best_match = BugMatch(
                    version=file_version.version,
                    line_numbers=list(range(start_idx, start_idx + num_buggy)),
                    matched_lines=[file_version.lines[i] for i in range(start_idx, start_idx + num_buggy)],
                    confidence=final_score
                )
    
    return best_match


def _calculate_context_boost(
    file_version: FileVersion,
    start_idx: int,
    num_lines: int,
    bug_signature: BugSignature
) -> float:
    """Calculate context similarity boost for a potential match"""
    scores = []
    
    # Check context before
    if bug_signature.context_before:
        context_start = max(0, start_idx - len(bug_signature.context_before))
        file_context_before = file_version.lines[context_start:start_idx]
        
        if file_context_before:
            # Compare context
            file_ctx_str = " ".join(file_context_before)
            sig_ctx_str = " ".join(bug_signature.context_before)
            scores.append(cosine_similarity(file_ctx_str, sig_ctx_str))
    
    # Check context after
    if bug_signature.context_after:
        context_end = min(len(file_version.lines), start_idx + num_lines + len(bug_signature.context_after))
        file_context_after = file_version.lines[start_idx + num_lines:context_end]
        
        if file_context_after:
            file_ctx_str = " ".join(file_context_after)
            sig_ctx_str = " ".join(bug_signature.context_after)
            scores.append(cosine_similarity(file_ctx_str, sig_ctx_str))
    
    return sum(scores) / len(scores) if scores else 0.5


def find_bug_introduction(
    file_versions: List[FileVersion],
    bug_signature: BugSignature,
    threshold: float = 0.7
) -> tuple:
    """Find when bug was introduced by searching backward through versions"""
    matches_by_version: Dict[int, BugMatch] = {}
    introduction_version = None
    
    # Search from newest to oldest
    for file_version in file_versions:
        match = find_bug_in_version(file_version, bug_signature, threshold)
        
        if match:
            matches_by_version[file_version.version] = match
        else:
            # Bug not found in this version
            # If we had matches before, bug was introduced in version after this
            if matches_by_version:
                # Get oldest version where bug was found
                oldest_with_bug = min(matches_by_version.keys())
                introduction_version = oldest_with_bug
            break
    
    # If bug found in all versions, it was in initial version
    if introduction_version is None and matches_by_version:
        introduction_version = min(matches_by_version.keys())
    
    return introduction_version, matches_by_version


def calculate_trace_confidence(
    bug_signature: BugSignature,
    matches: Dict[int, BugMatch],
    introduction_version: int,
    fix_version: int
) -> float:
    """Calculate confidence score for the bug trace"""
    if not matches:
        return 0.0
    
    # Factor 1: Match quality (average confidence)
    match_confidences = [m.confidence for m in matches.values()]
    match_quality = sum(match_confidences) / len(match_confidences)
    
    # Factor 2: Trace clarity (consistency of matches)
    if len(match_confidences) > 1:
        variance = sum((c - match_quality) ** 2 for c in match_confidences) / len(match_confidences)
        trace_clarity = max(0, 1 - variance)
    else:
        trace_clarity = 1.0
    
    # Factor 3: Signature strength (More buggy lines = stronger)
    signature_strength = min(1.0, len(bug_signature.buggy_lines) / 5)
    
    # Factor 4: Trace completeness
    trace_completeness = 1.0 if introduction_version is not None else 0.5
    
    # Weighted combination
    confidence = (
        0.4 * match_quality +
        0.3 * trace_clarity +
        0.2 * signature_strength +
        0.1 * trace_completeness
    )
    
    return min(1.0, max(0.0, confidence))