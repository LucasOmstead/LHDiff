"""
diff - preprocessing, similarity matching, and diff algorithms.
"""

from .preprocessing import preprocess_line, preprocess_lines, preprocess_file
from .matcher import match_lines, normalized_levenshtein, cosine_similarity, levenshtein, combined_similarity, get_context
from .diff import get_diff
from .diff_hybrid import get_diff_hybrid, get_diff_with_hash, hash_diff

__all__ = [
    'preprocess_line', 'preprocess_lines', 'preprocess_file',
    'match_lines', 'normalized_levenshtein', 'cosine_similarity',
    'levenshtein', 'combined_similarity', 'get_context',
    'get_diff', 'get_diff_hybrid', 'get_diff_with_hash', 'hash_diff',
]

