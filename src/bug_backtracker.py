"""
bug_backtracker.py

Main API for bug backtracking feature.
Traces bugs from their fix commit back to the commit that introduced them.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
from .models import (
    CommitInfo, FileVersion, BugSignature, BugLineage, BugMatch,
    LineMapping, LineHistory,
    BugTraceError, FileVersionNotFound, NoBugFixFound, TraceIncomplete
)
from .commit_history import CommitHistory
from .file_version_loader import FileVersionLoader
from .bug_signature import extract_bug_signature, compute_diff_and_mapping
from .line_tracker import (
    find_bug_in_version, find_bug_introduction,
    track_line_backward, calculate_trace_confidence
)


class BugBacktracker:
    """
    Main API for bug backtracking feature.
    
    Traces bugs from their fix commit back to the commit that introduced them.
    
    Usage:
        backtracker = BugBacktracker(
            desc_file="path/to/desc.txt",
            files_directory="path/to/files/"
        )
        
        # Analyze all bug fixes for a file
        lineages = backtracker.analyze_file("auth")
        
        # Trace a specific bug fix
        lineage = backtracker.trace_single_bug("auth", bug_fix_version=5)
    """
    
    def __init__(self, desc_file: str, files_directory: str):
        """
        Initialize the backtracker.
        
        Args:
            desc_file: Path to desc.txt with commit messages
            files_directory: Directory containing file_v*.txt files
        """
        self.desc_file = desc_file
        self.files_directory = files_directory
        
        # Cache for loaded data
        self._commit_histories: Dict[str, CommitHistory] = {}
        self._version_loaders: Dict[str, FileVersionLoader] = {}
    
    def _get_commit_history(self, file_name: str) -> CommitHistory:
        """Get or create CommitHistory for a file."""
        if file_name not in self._commit_histories:
            self._commit_histories[file_name] = CommitHistory(
                self.desc_file, file_name
            )
        return self._commit_histories[file_name]
    
    def _get_version_loader(self, file_name: str) -> FileVersionLoader:
        """Get or create FileVersionLoader for a file."""
        if file_name not in self._version_loaders:
            self._version_loaders[file_name] = FileVersionLoader(
                self.files_directory, file_name
            )
        return self._version_loaders[file_name]
    
    def analyze_file(self, file_name: str, verbose: bool = True) -> List[BugLineage]:
        """
        Analyze all bug fixes in a file's history.
        
        Args:
            file_name: Base name of file (e.g., "auth" for auth_v0.txt)
            verbose: If True, suppress individual trace output (default: True)
            
        Returns:
            List of BugLineage objects, one per bug fix found
        """
        commit_history = self._get_commit_history(file_name)
        
        if not commit_history.has_bug_fixes():
            if verbose:
                print(f"\nNo bug fixes found in {file_name}")
            return []
        
        lineages = []
        bug_fix_commits = commit_history.get_bug_fix_commits()
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"ANALYZING FILE: {file_name}")
            print(f"Found {len(bug_fix_commits)} bug fix(es)")
            print(f"{'='*60}")
        
        for i, fix_commit in enumerate(bug_fix_commits, 1):
            if verbose:
                print(f"\n[Bug Fix {i}/{len(bug_fix_commits)}]")
            
            try:
                lineage = self.trace_single_bug(file_name, fix_commit.version)
                lineages.append(lineage)
            except BugTraceError as e:
                # Create a failed lineage entry
                lineage = BugLineage(
                    fix_commit=fix_commit,
                    fix_version=fix_commit.version,
                    signature=BugSignature([], [], [], [], [], "unknown", []),
                    introduction_commit=None,
                    introduction_version=-1,
                    introduction_lines=[],
                    confidence=0.0,
                    trace_complete=False,
                    error_message=str(e)
                )
                lineages.append(lineage)
                if verbose:
                    print(f"\n⚠️  Trace failed: {e}\n")
        
        return lineages
    
    def trace_single_bug(
        self,
        file_name: str,
        bug_fix_version: int,
        similarity_threshold: float = 0.7
    ) -> BugLineage:
        """
        Trace a specific bug fix back to its origin.
        
        Args:
            file_name: Base name of file (e.g., "auth" for auth_v0.txt)
            bug_fix_version: Version number of the bug fix commit
            similarity_threshold: Threshold for bug signature matching (0-1)
            
        Returns:
            BugLineage with complete trace
            
        Raises:
            FileVersionNotFound: If required file versions don't exist
            TraceIncomplete: If trace cannot be completed
        """
        commit_history = self._get_commit_history(file_name)
        version_loader = self._get_version_loader(file_name)
        
        # Get the fix commit info
        fix_commit = commit_history.get_commit_at_version(bug_fix_version)
        if fix_commit is None:
            # Create a placeholder commit if not found in desc.txt
            fix_commit = CommitInfo(
                version=bug_fix_version,
                message="(commit message not found)",
                file_name=file_name,
                is_bug_fix=True
            )
        
        # Load the fix version and the version before fix
        try:
            file_after_fix = version_loader.load_version(bug_fix_version)
            file_before_fix = version_loader.load_version(bug_fix_version - 1)
        except FileVersionNotFound as e:
            raise TraceIncomplete(f"Cannot load required versions: {e}")
        
        # Extract bug signature from the fix diff
        bug_signature = extract_bug_signature(file_before_fix, file_after_fix)
        
        if bug_signature.is_empty():
            # No buggy lines identified - might be an insertion-only fix
            return BugLineage(
                fix_commit=fix_commit,
                fix_version=bug_fix_version,
                signature=bug_signature,
                introduction_commit=None,
                introduction_version=-1,
                introduction_lines=[],
                confidence=0.0,
                trace_complete=False,
                error_message="No buggy lines identified in fix diff"
            )
        
        # Load all versions from 0 to before-fix for backward search
        versions_to_search = []
        for v in range(bug_fix_version - 1, -1, -1):  # newest to oldest
            try:
                versions_to_search.append(version_loader.load_version(v))
            except FileVersionNotFound:
                break  # Stop if we can't load earlier versions
        
        if not versions_to_search:
            raise TraceIncomplete("No versions available to search")
        
        # Find where bug was introduced
        introduction_version, matches_by_version = find_bug_introduction(
            versions_to_search, bug_signature, similarity_threshold
        )
        
        # Get introduction commit info
        introduction_commit = None
        if introduction_version is not None:
            introduction_commit = commit_history.get_commit_at_version(introduction_version)
        
        # Get introduction lines
        introduction_lines = []
        if introduction_version is not None and introduction_version in matches_by_version:
            introduction_lines = matches_by_version[introduction_version].line_numbers
        elif introduction_version == 0:
            # Bug was in initial version
            introduction_lines = bug_signature.line_numbers
        
        # Build versions_with_bug list
        versions_with_bug = sorted(
            matches_by_version.values(),
            key=lambda m: m.version
        )
        
        # Calculate confidence
        confidence = calculate_trace_confidence(
            bug_signature, matches_by_version,
            introduction_version, bug_fix_version
        )
        
        # Calculate commits between
        commits_between = 0
        if introduction_version is not None:
            commits_between = bug_fix_version - introduction_version
        
        lineage = BugLineage(
            fix_commit=fix_commit,
            fix_version=bug_fix_version,
            signature=bug_signature,
            introduction_commit=introduction_commit,
            introduction_version=introduction_version if introduction_version is not None else -1,
            introduction_lines=introduction_lines,
            versions_with_bug=versions_with_bug,
            confidence=confidence,
            commits_between=commits_between,
            trace_complete=introduction_version is not None
        )
        
        # Print results for user visibility
        self._print_trace_results(lineage)
        
        return lineage
    
    def batch_analyze(self, file_names: List[str]) -> Dict[str, List[BugLineage]]:
        """
        Analyze multiple files in batch.
        
        Args:
            file_names: List of file base names to analyze
            
        Returns:
            Dict mapping file_name -> List[BugLineage]
        """
        results = {}
        for file_name in file_names:
            try:
                results[file_name] = self.analyze_file(file_name)
            except Exception as e:
                results[file_name] = []
        return results
    
    def get_file_summary(self, file_name: str) -> str:
        """
        Get a summary of commits and bug fixes for a file.
        
        Args:
            file_name: Base name of file
            
        Returns:
            Human-readable summary string
        """
        commit_history = self._get_commit_history(file_name)
        version_loader = self._get_version_loader(file_name)
        
        lines = [
            f"File: {file_name}",
            f"Available versions: {version_loader.get_available_versions()}",
            "",
            commit_history.summary()
        ]
        
        return "\n".join(lines)
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._commit_histories.clear()
        for loader in self._version_loaders.values():
            loader.clear_cache()
        self._version_loaders.clear()
    
    def _print_trace_results(self, lineage: BugLineage) -> None:
        """Print trace results for user visibility."""
        print("\n" + "="*60)
        print("BUG TRACE RESULTS")
        print("="*60)
        
        # Bug fix info
        print(f"🔧 Bug Fix:")
        print(f"   Version: v{lineage.fix_version}")
        print(f"   Commit: {lineage.fix_commit.message}")
        
        # Bug introduction info
        print(f"\n🐛 Bug Introduction:")
        if lineage.introduction_version >= 0:
            print(f"   Version: v{lineage.introduction_version}")
            if lineage.introduction_commit:
                print(f"   Commit: {lineage.introduction_commit.message}")
            else:
                print(f"   Commit: (initial version)")
            if lineage.introduction_lines:
                print(f"   Lines: {lineage.introduction_lines}")
        else:
            print(f"   Not found (confidence too low)")
        
        # Summary stats
        print(f"\n📊 Summary:")
        print(f"   Confidence: {lineage.confidence:.1%}")
        print(f"   Commits Between: {lineage.commits_between}")
        print(f"   Trace Complete: {'Yes' if lineage.trace_complete else 'No'}")
        
        print("="*60 + "\n")


def backtrack_bug_to_origin(
    desc_file: str,
    files_directory: str,
    file_name: str,
    bug_fix_version: int
) -> BugLineage:
    """
    Convenience function to trace a single bug.
    
    Args:
        desc_file: Path to desc.txt
        files_directory: Directory with file versions
        file_name: Base name of file
        bug_fix_version: Version number of bug fix
        
    Returns:
        BugLineage with trace results
    """
    backtracker = BugBacktracker(desc_file, files_directory)
    return backtracker.trace_single_bug(file_name, bug_fix_version)


# Main entry point for testing
if __name__ == "__main__":
    print("Bug Backtracker Module")
    print("=" * 40)
    print("Usage:")
    print("  from src.bug_backtracker import BugBacktracker")
    print()
    print("  backtracker = BugBacktracker('desc.txt', 'files/')")
    print("  lineages = backtracker.analyze_file('auth')")
    print()
    print("  for lineage in lineages:")
    print("      print(lineage.summary())")

