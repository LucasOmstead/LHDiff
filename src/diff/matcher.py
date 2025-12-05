"""
matcher.py

Core line-matching logic for the project.

Expects preprocessed lines (e.g., via preprocess_line in preprocessing.py).

Public function:
    match_lines(old_lines, new_lines) -> list[(old_idx, new_idx)]

Indices are 1-based in the returned mappings to match assignment format.
"""

import difflib
import math
from collections import Counter


# --------------------------
# Levenshtein distance
# --------------------------

def levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings using 2D DP."""
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    m, n = len(a), len(b)
    
    # 2D DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Base cases: transforming empty string to/from prefix
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Fill the table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # deletion
                dp[i][j - 1] + 1,       # insertion
                dp[i - 1][j - 1] + cost # substitution
            )
    
    return dp[m][n]


def normalized_levenshtein(a: str, b: str) -> float:
    """Return similarity in [0,1] based on Levenshtein distance."""
    if not a and not b:
        return 1.0
    dist = levenshtein(a, b)
    max_len = max(len(a), len(b))
    return 1.0 - (dist / max_len)


# --------------------------
# Context / cosine similarity
# --------------------------

def get_context(lines, idx, window=4) -> str:
    """
    Build a context string for line at index idx (0-based),
    using up to 'window' lines above and below.
    """
    start = max(0, idx - window)
    end = min(len(lines), idx + window + 1)
    # Join all surrounding lines (excluding the line itself or including? here we include all)
    return " ".join(lines[start:end])


def cosine_similarity(text1: str, text2: str) -> float:
    """
    Compute cosine similarity between two strings treated as bags of words.
    Returns value in [0,1].
    """
    if not text1.strip() and not text2.strip():
        return 1.0
    if not text1.strip() or not text2.strip():
        return 0.0

    # Tokenize by whitespace
    words1 = text1.split()
    words2 = text2.split()

    c1 = Counter(words1)
    c2 = Counter(words2)

    # Dot product
    common = set(c1.keys()) & set(c2.keys())
    dot = sum(c1[w] * c2[w] for w in common)

    # Norms
    norm1 = math.sqrt(sum(v * v for v in c1.values()))
    norm2 = math.sqrt(sum(v * v for v in c2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


# --------------------------
# Combined similarity
# --------------------------



