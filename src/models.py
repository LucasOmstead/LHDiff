"""
models.py

Data models for bug backtracking feature

Contains dataclasses for commits, file versions, bug signatures, and lineage tracking
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple


@dataclass
class CommitInfo:
    """Represents a single commit in the mock git history"""
    # Version number (0, 1, 2, ...)
    version: int
    # Commit message
    message: str
    # File this commit belongs to
    file_name: str
    # Whether this is a bug fix commit
    is_bug_fix: bool = False
    
    def __repr__(self) -> str:
        fix_marker = " [BUG FIX]" if self.is_bug_fix else ""
        return f"CommitInfo(v{self.version}: '{self.message}'{fix_marker})"


@dataclass
class FileVersion:
    """Represents a file at a specific version"""
    version: int
    # Path to file_vN.txt
    file_path: str
    # File content (raw lines)
    lines: List[str]
    # Normalized content for matching
    preprocessed: List[str]
    
    def __len__(self) -> int:
        return len(self.lines)
    
    def __repr__(self) -> str:
        return f"FileVersion(v{self.version}, {len(self.lines)} lines)"


@dataclass
class BugSignature:
    """
    Represents the 'buggy code' pattern extracted from a bug fix

    Used to search backward through history to find where bug was introduced
    """
    # Lines that were changed/deleted in the fix (The buggy code)
    # Raw buggy code
    buggy_lines: List[str]
    # Preprocessed for matching
    buggy_lines_normalized: List[str]
    
    # Line numbers in the pre-fix version
    line_numbers: List[int]
    
    # Context for better matching
    # Lines before the bug
    context_before: List[str]
    # Lines after the bug
    context_after: List[str]
    
    # Type of fix
        # "deletion", "modification", "insertion_fix", "complex"
    fix_type: str
    
    # Diff operations that represent the fix
    fix_operations: List[str]
    
    def __repr__(self) -> str:
        return f"BugSignature({self.fix_type}, {len(self.buggy_lines)} buggy lines at {self.line_numbers})"
    
    def is_empty(self) -> bool:
        """Check if signature has no buggy lines (Possible false positive)"""
        return len(self.buggy_lines) == 0


@dataclass
class BugMatch:
    """Represents finding the bug signature in a specific version"""
    version: int
    # Where bug was found
    line_numbers: List[int]
    # The actual matched lines
    matched_lines: List[str]
    # Match confidence (0-1)
    confidence: float
    
    def __repr__(self) -> str:
        return f"BugMatch(v{self.version}, lines {self.line_numbers}, conf={self.confidence:.2f})"


@dataclass
class LineMapping:
    """Maps line numbers between two consecutive versions"""
    old_version: int
    new_version: int
    
    # Mappings: new_line_num -> old_line_num
    # x:y matches
    exact_matches: Dict[int, int] = field(default_factory=dict)
    # x~y matches
    similarity_matches: Dict[int, int] = field(default_factory=dict)
    
    # Track operations
    # Lines deleted from old
    deletions: Set[int] = field(default_factory=set)
    # Lines inserted in new
    insertions: Set[int] = field(default_factory=set)
    
    def get_old_line(self, new_line: int) -> Optional[int]:
        """
        Get the corresponding old line number for a new line number

        Returns None if the line was inserted (Didn't exist before)
        """
        if new_line in self.exact_matches:
            return self.exact_matches[new_line]
        if new_line in self.similarity_matches:
            return self.similarity_matches[new_line]
        if new_line in self.insertions:
            return None
        return None
    
    def get_new_line(self, old_line: int) -> Optional[int]:
        """
        Get the corresponding new line number for an old line number

        Returns None if the line was deleted
        """
        if old_line in self.deletions:
            return None
        # Reverse lookup
        for new, old in self.exact_matches.items():
            if old == old_line:
                return new
        for new, old in self.similarity_matches.items():
            if old == old_line:
                return new
        return None
    
    def __repr__(self) -> str:
        return f"LineMapping(v{self.old_version}->v{self.new_version}, {len(self.exact_matches)} exact, {len(self.similarity_matches)} similar)"


@dataclass
class LineHistory:
    """Tracks a line's evolution through multiple versions"""
    # List of (version, line_number) tuples, from newest to oldest
    evolution: List[Tuple[int, int]] = field(default_factory=list)
    
    # Version where line first appeared (was introduced)
    introduction_version: Optional[int] = None
    
    def add_version(self, version: int, line_num: int):
        """Add a version to the history"""
        self.evolution.append((version, line_num))
    
    def get_line_at_version(self, version: int) -> Optional[int]:
        """Get line number at a specific version"""
        for v, line in self.evolution:
            if v == version:
                return line
        return None
    
    def __repr__(self) -> str:
        if not self.evolution:
            return "LineHistory(empty)"
        path = " <- ".join([f"v{v}:L{l}" for v, l in self.evolution])
        return f"LineHistory({path})"


@dataclass
class BugLineage:
    """
    Complete trace of a bug from introduction to fix

    This is the main result returned by the backtracker
    """
    # Bug fix information
    fix_commit: CommitInfo
    fix_version: int
    
    # Bug signature extracted from the fix
    signature: BugSignature
    
    # Bug introduction information
    introduction_commit: Optional[CommitInfo]
    introduction_version: int
    introduction_lines: List[int]
    
    # Trace path (Versions where bug was found)
    versions_with_bug: List[BugMatch] = field(default_factory=list)
    
    # Line evolution through versions
    line_history: Optional[LineHistory] = None
    
    # Confidence score (0-1)
    confidence: float = 0.0
    
    # Metadata
    # How many commits between intro and fix
    commits_between: int = 0
    # Whether trace completed successfully
    trace_complete: bool = True
    # Error if trace failed
    error_message: Optional[str] = None
    
    def __repr__(self) -> str:
        if self.introduction_commit:
            return (f"BugLineage(fix=v{self.fix_version}, "
                   f"introduced=v{self.introduction_version}, "
                   f"confidence={self.confidence:.2f})")
        return f"BugLineage(fix=v{self.fix_version}, introduction=UNKNOWN)"
    
    def summary(self) -> str:
        """Generate a human-readable summary of the bug lineage"""
        lines = [
            "=" * 60,
            "BUG LINEAGE REPORT",
            "=" * 60,
            f"Bug Fix Commit (v{self.fix_version}):",
            f"  Message: {self.fix_commit.message}",
            f"  Fix Type: {self.signature.fix_type}",
            "",
        ]
        
        if self.introduction_commit:
            lines.extend([
                f"Bug Introduction (v{self.introduction_version}):",
                f"  Message: {self.introduction_commit.message}",
                f"  Lines: {self.introduction_lines}",
                "",
            ])
        else:
            lines.extend([
                f"Bug Introduction: v{self.introduction_version}",
                f"  Lines: {self.introduction_lines}",
                "",
            ])
        
        lines.extend([
            f"Commits Between: {self.commits_between}",
            f"Confidence: {self.confidence:.1%}",
            f"Trace Complete: {self.trace_complete}",
        ])
        
        if self.error_message:
            lines.append(f"Error: {self.error_message}")
        
        if self.versions_with_bug:
            lines.append("")
            lines.append("Bug Found In Versions:")
            for match in self.versions_with_bug:
                lines.append(f"  v{match.version}: lines {match.line_numbers} (conf={match.confidence:.2f})")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# Custom exceptions for bug tracking
class BugTraceError(Exception):
    """Base exception for bug tracing errors"""
    pass


class FileVersionNotFound(BugTraceError):
    """File version doesn't exist"""
    pass


class NoBugFixFound(BugTraceError):
    """No bug fix commits found for the file"""
    pass


class TraceIncomplete(BugTraceError):
    """Unable to complete trace (low confidence or missing data)"""
    pass


class InvalidDataFormat(BugTraceError):
    """Data format is invalid (desc.txt or file versions)"""
    pass