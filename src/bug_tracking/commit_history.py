"""
Manages commit history from desc.txt files
Parses commits and identifies bug fixes
"""

from typing import List, Dict, Optional
from ..models import CommitInfo, FileVersionNotFound, NoBugFixFound, InvalidDataFormat
from .bug_detector import BugDetector, parse_commit_messages


class CommitHistory:
    """Manages commit history for a file from desc.txt"""
    
    def __init__(self, desc_file_path: str, file_name: str):
        """Initialize with desc.txt path and target file name"""
        self.desc_file_path = desc_file_path
        self.file_name = file_name
        self.bug_detector = BugDetector()
        
        # Parse commits on initialization
        self._commits: List[CommitInfo] = []
        self._parse_commits()
    
    def _parse_commits(self) -> None:
        """Parse commits from desc.txt and build CommitInfo objects"""
        try:
            # Use existing parse_commit_messages function
            messages = parse_commit_messages(self.desc_file_path, self.file_name)
            
            if not messages:
                # No commits found for this file
                self._commits = []
                return
            
            # Build CommitInfo objects
                # Version 0 = initial state
                # Version 1 = after first commit
            for i, message in enumerate(messages):
                # Commits start at version 1
                version = i + 1
                is_bug_fix = self.bug_detector.is_bug_fix(message)
                
                commit = CommitInfo(
                    version=version,
                    message=message,
                    file_name=self.file_name,
                    is_bug_fix=is_bug_fix
                )
                self._commits.append(commit)
                
        except FileNotFoundError:
            raise InvalidDataFormat(f"desc.txt not found: {self.desc_file_path}")
        except Exception as e:
            raise InvalidDataFormat(f"Error parsing desc.txt: {e}")
    
    def get_commits(self) -> List[CommitInfo]:
        """Returns all commits in chronological order"""
        return self._commits.copy()
    
    def get_bug_fix_commits(self) -> List[CommitInfo]:
        """Returns only bug fix commits"""
        return [c for c in self._commits if c.is_bug_fix]
    
    def get_commit_at_version(self, version: int) -> Optional[CommitInfo]:
        """Get commit info for a specific version"""
        for commit in self._commits:
            if commit.version == version:
                return commit
        return None
    
    def get_latest_version(self) -> int:
        """Get the latest version number"""
        if not self._commits:
            return 0
        return self._commits[-1].version
    
    def get_version_count(self) -> int:
        """Get total number of versions (Including v0)"""
        return len(self._commits) + 1
    
    def has_bug_fixes(self) -> bool:
        """Check if there are any bug fix commits"""
        return any(c.is_bug_fix for c in self._commits)
    
    def get_commits_between(self, start_version: int, end_version: int) -> List[CommitInfo]:
        """Get commits between two versions (exclusive start, inclusive end)"""
        return [c for c in self._commits if start_version < c.version <= end_version]
    
    def __len__(self) -> int:
        return len(self._commits)
    
    def __repr__(self) -> str:
        bug_count = len(self.get_bug_fix_commits())
        return f"CommitHistory(file={self.file_name}, commits={len(self._commits)}, bug_fixes={bug_count})"
    
    def summary(self) -> str:
        """Generate a summary of the commit history"""
        lines = [
            f"Commit History for '{self.file_name}'",
            f"Total commits: {len(self._commits)}",
            f"Bug fixes: {len(self.get_bug_fix_commits())}",
            "-" * 40,
        ]
        
        for commit in self._commits:
            marker = " [BUG FIX]" if commit.is_bug_fix else ""
            lines.append(f"v{commit.version}: {commit.message}{marker}")
        
        return "\n".join(lines)