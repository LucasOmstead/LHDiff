"""bug tracking and backtracking functionality."""

from .bug_detector import BugDetector, parse_commit_messages
from .bug_signature import extract_bug_signature, build_line_mapping, compute_diff_and_mapping
from .bug_backtracker import BugBacktracker, backtrack_bug_to_origin
from .commit_history import CommitHistory
from .file_version_loader import FileVersionLoader
from .line_tracker import (
    find_bug_in_version, find_bug_introduction,
    track_line_backward, track_lines_backward, calculate_trace_confidence
)

__all__ = [
    #bug detection
    'BugDetector', 'parse_commit_messages',
    #bug signature
    'extract_bug_signature', 'build_line_mapping', 'compute_diff_and_mapping',
    #bug backtracking
    'BugBacktracker', 'backtrack_bug_to_origin',
    #history management
    'CommitHistory', 'FileVersionLoader',
    #line tracking
    'find_bug_in_version', 'find_bug_introduction',
    'track_line_backward', 'track_lines_backward', 'calculate_trace_confidence',
]

