"""
loads file versions from disk (file_v0.txt, file_v1.txt, etc.).
handles preprocessing and caching.
"""

import os
from typing import List, Dict, Optional
from ..models import FileVersion, FileVersionNotFound
from ..diff.preprocessing import preprocess_lines


class FileVersionLoader:
    """loads file versions from disk. expects files named {base_name}_v{version}.txt"""
    
    def __init__(self, base_path: str, file_base_name: str):
        """initialize the loader."""
        self.base_path = base_path.rstrip('/')
        self.file_base_name = file_base_name
        
        #cache loaded versions
        self._cache: Dict[int, FileVersion] = {}
    
    def _get_file_path(self, version: int) -> str:
        """get the file path for a specific version."""
        filename = f"{self.file_base_name}_v{version}.txt"
        return os.path.join(self.base_path, filename)
    
    def version_exists(self, version: int) -> bool:
        """check if a version file exists."""
        return os.path.exists(self._get_file_path(version))
    
    def load_version(self, version: int, use_cache: bool = True) -> FileVersion:
        """load a file version from disk."""
        #check cache first
        if use_cache and version in self._cache:
            return self._cache[version]
        
        file_path = self._get_file_path(version)
        
        if not os.path.exists(file_path):
            raise FileVersionNotFound(f"Version {version} not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_lines = f.readlines()
            
            #strip newlines but preserve content
            lines = [line.rstrip('\n\r') for line in raw_lines]
            
            #preprocess for matching
            preprocessed = preprocess_lines(lines)
            
            file_version = FileVersion(
                version=version,
                file_path=file_path,
                lines=lines,
                preprocessed=preprocessed
            )
            
            #cache the result
            if use_cache:
                self._cache[version] = file_version
            
            return file_version
            
        except Exception as e:
            raise FileVersionNotFound(f"Error loading version {version}: {e}")
    
    def load_version_range(self, start: int, end: int) -> List[FileVersion]:
        """load multiple versions efficiently."""
        versions = []
        for v in range(start, end + 1):
            if self.version_exists(v):
                versions.append(self.load_version(v))
        return versions
    
    def get_available_versions(self) -> List[int]:
        """scan directory for all available versions."""
        versions = []
        
        #scan directory for files matching pattern
        for filename in os.listdir(self.base_path):
            if filename.startswith(f"{self.file_base_name}_v") and filename.endswith(".txt"):
                try:
                    #extract version number from filename
                    version_str = filename[len(self.file_base_name) + 2:-4]  #+2 for "_v", -4 for ".txt"
                    version = int(version_str)
                    versions.append(version)
                except ValueError:
                    continue
        
        return sorted(versions)
    
    def get_latest_version(self) -> int:
        """get the latest available version number."""
        versions = self.get_available_versions()
        return versions[-1] if versions else -1
    
    def clear_cache(self) -> None:
        """clear the version cache."""
        self._cache.clear()
    
    def preload_all(self) -> None:
        """preload all available versions into cache."""
        for v in self.get_available_versions():
            self.load_version(v)
    
    def __repr__(self) -> str:
        versions = self.get_available_versions()
        return f"FileVersionLoader(base={self.file_base_name}, versions={versions})"

