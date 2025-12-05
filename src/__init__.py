"""
LHDiff source package.

Contains preprocessing, matching, and bug backtracking utilities for diff computation.
"""

# Core diff functionality
from .diff import (
    preprocess_line, preprocess_lines, preprocess_file,
    match_lines, normalized_levenshtein, cosine_similarity
)

# Bug tracking functionality
from .bug_tracking import (
    BugDetector, parse_commit_messages,
    extract_bug_signature, build_line_mapping,
    BugBacktracker, backtrack_bug_to_origin,
    CommitHistory, FileVersionLoader,
    find_bug_in_version, track_line_backward
)

# Models (shared data structures)
from .models import (
    CommitInfo, FileVersion, BugSignature, BugLineage, BugMatch,
    LineMapping, LineHistory,
    BugTraceError, FileVersionNotFound, NoBugFixFound, TraceIncomplete
)

__all__ = [
    # Preprocessing
    'preprocess_line', 'preprocess_lines', 'preprocess_file',
    # Matching
    'match_lines', 'normalized_levenshtein', 'cosine_similarity',
    # Bug detection
    'BugDetector', 'parse_commit_messages',
    # Models
    'CommitInfo', 'FileVersion', 'BugSignature', 'BugLineage', 'BugMatch',
    'LineMapping', 'LineHistory',
    # Exceptions
    'BugTraceError', 'FileVersionNotFound', 'NoBugFixFound', 'TraceIncomplete',
    # Bug backtracking
    'CommitHistory', 'FileVersionLoader',
    'extract_bug_signature', 'build_line_mapping',
    'find_bug_in_version', 'track_line_backward',
    'BugBacktracker', 'backtrack_bug_to_origin',
]

