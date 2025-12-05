"""
LHDiff source package.

Contains preprocessing, matching, and bug backtracking utilities for diff computation.
"""

from .preprocessing import preprocess_line, preprocess_lines, preprocess_file
from .matcher import match_lines, normalized_levenshtein, cosine_similarity
from .bug_detector import BugDetector, parse_commit_messages
from .models import (
    CommitInfo, FileVersion, BugSignature, BugLineage, BugMatch,
    LineMapping, LineHistory,
    BugTraceError, FileVersionNotFound, NoBugFixFound, TraceIncomplete
)
from .commit_history import CommitHistory
from .file_version_loader import FileVersionLoader
from .bug_signature import extract_bug_signature, build_line_mapping
from .line_tracker import find_bug_in_version, track_line_backward
from .bug_backtracker import BugBacktracker, backtrack_bug_to_origin

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

