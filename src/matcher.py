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
    """Compute Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    # DP table with only two rows
    prev = list(range(len(b) + 1))
    curr = [0] * (len(b) + 1)

    for i, ca in enumerate(a, start=1):
        curr[0] = i
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr[j] = min(
                prev[j] + 1,       # deletion
                curr[j - 1] + 1,   # insertion
                prev[j - 1] + cost # substitution
            )
        prev, curr = curr, prev

    return prev[len(b)]


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

def combined_similarity(line_a: str, line_b: str,
                        ctx_a: str, ctx_b: str,
                        alpha: float = 0.6) -> float:
    """
    Combine content (Levenshtein) and context (cosine) similarities.

    combined = alpha * content_sim + (1 - alpha) * context_sim
    """
    content_sim = normalized_levenshtein(line_a, line_b)
    context_sim = cosine_similarity(ctx_a, ctx_b)
    return alpha * content_sim + (1.0 - alpha) * context_sim


# --------------------------
# Main matching logic
# --------------------------

def match_lines(old_lines, new_lines, context_window=4,
                similarity_threshold=0.6):
    """
    Given two lists of preprocessed lines (old_lines, new_lines),
    return a list of (old_idx, new_idx) mappings (1-based indices).

    Steps:
    1. Use difflib to find equal blocks -> anchor mappings.
    2. For non-equal regions, match remaining old lines to new lines
       via combined content+context similarity.
    """

    # Mapping from old index (0-based) -> new index (0-based)
    mapping = {}
    used_new = set()

    sm = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    opcodes = sm.get_opcodes()

    unmatched_blocks = []  # store (old_range, new_range) for non-'equal' blocks

    # 1) First pass: take 'equal' blocks as exact matches
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            # Direct 1-1 mapping for each line in the equal block
            for off in range(i2 - i1):
                old_idx = i1 + off
                new_idx = j1 + off
                mapping[old_idx] = new_idx
                used_new.add(new_idx)
        else:
            # Save changed region to process later
            unmatched_blocks.append(((i1, i2), (j1, j2)))

    # 2) Second pass: process unmatched blocks using similarity
    for (i1, i2), (j1, j2) in unmatched_blocks:
        old_range = list(range(i1, i2))
        new_range = list(range(j1, j2))

        for old_idx in old_range:
            if old_idx in mapping:
                # Already matched via an 'equal' region
                continue

            best_new = None
            best_score = 0.0

            line_a = old_lines[old_idx]
            ctx_a = get_context(old_lines, old_idx, window=context_window)

            for new_idx in new_range:
                if new_idx in used_new:
                    continue

                line_b = new_lines[new_idx]
                ctx_b = get_context(new_lines, new_idx, window=context_window)

                score = combined_similarity(line_a, line_b, ctx_a, ctx_b)

                if score > best_score:
                    best_score = score
                    best_new = new_idx

            # Accept mapping only if similarity is above threshold
            if best_new is not None and best_score >= similarity_threshold:
                mapping[old_idx] = best_new
                used_new.add(best_new)

    # 3) Convert mapping dict (0-based) -> sorted list of (1-based) tuples
    result = []
    for old_idx in sorted(mapping.keys()):
        new_idx = mapping[old_idx]
        result.append((old_idx + 1, new_idx + 1))

    return result


# Note: This module is used by diff_hybrid.py for similarity-based matching
# Run tests via: python3 run_tests.py

