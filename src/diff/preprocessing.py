# preprocessing.py
#
# Functions for normalizing source code lines before matching.
# This helps the matcher ignore irrelevant differences like whitespace,
# tabs, casing, and comments.

import re


def preprocess_line(line: str) -> str:
    """
    Normalize a single line of source code for line-matching.

    Steps:
    1. Strip leading/trailing whitespace
    2. Replace tabs with spaces
    3. Lowercase the line
    4. Remove inline comments (// or #)
    5. Add spaces around basic operators (=, +, -, *, /, <, >)
    6. Collapse multiple spaces into one
    7. Remove trailing semicolons/spaces

    Returns the normalized line as a string.
    """
    # 1. Strip whitespace
    line = line.strip()

    # 2. Normalize tabs → spaces
    line = line.replace("\t", " ")

    # 3. Lowercase
    line = line.lower()

    # 4. Remove inline comments (// or #)
    line = re.split(r'//|#', line)[0].strip()

    # If the line is now empty, return ""
    if not line:
        return ""

    # 5. Add spaces around basic operators
    line = re.sub(r'([=+\-*/<>])', r' \1 ', line)

    # 6. Collapse multiple spaces
    line = re.sub(r'\s+', ' ', line)

    # 7. Remove trailing punctuation/spaces (common: ; at end of statements)
    line = line.rstrip(" ;")

    return line


def preprocess_lines(lines):
    """
    Apply preprocess_line to a list of raw lines.
    Returns a new list of normalized lines.
    """
    return [preprocess_line(line) for line in lines]


def preprocess_file(path: str, encoding: str = "utf-8"):
    """
    Load a file and return a list of preprocessed lines.
    """
    with open(path, "r", encoding=encoding) as f:
        raw_lines = f.readlines()
    return preprocess_lines(raw_lines)


if __name__ == "__main__":
    # Quick manual test
    test_lines = [
        "   int Count = 5;   // number of items",
        "\treturn x+1;",
        "value=arr[i]+5",
        "   # this is a comment line",
    ]

    for original in test_lines:
        print(f"ORIG: {original!r}")
        print(f"NORM: {preprocess_line(original)!r}")
        print("-" * 40)