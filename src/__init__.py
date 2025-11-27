"""
LHDiff source package.

Contains preprocessing and matching utilities for diff computation.
"""

from .preprocessing import preprocess_line, preprocess_lines, preprocess_file

__all__ = ['preprocess_line', 'preprocess_lines', 'preprocess_file']

