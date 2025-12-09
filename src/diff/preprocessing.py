# preprocessing.py
# Normalize source code lines before matching

import re


def preprocess_line(line: str) -> str:
    """Normalize a single line of source code for matching"""
    # Strip whitespace
    line = line.strip()

    # Tabs to spaces
    line = line.replace("\t", " ")

    # Lowercase
    line = line.lower()

    # Remove inline comments
    line = re.split(r'//|#', line)[0].strip()

    if not line:
        return ""

    # Add spaces around operators
    line = re.sub(r'([=+\-*/<>])', r' \1 ', line)

    # Collapse multiple spaces
    line = re.sub(r'\s+', ' ', line)

    # Remove trailing semicolons
    line = line.rstrip(" ;")

    return line


def preprocess_lines(lines):
    """Apply preprocess_line to a list of lines"""
    return [preprocess_line(line) for line in lines]


def preprocess_file(path: str, encoding: str = "utf-8"):
    """Load file and return list of preprocessed lines"""
    with open(path, "r", encoding=encoding) as f:
        raw_lines = f.readlines()
    return preprocess_lines(raw_lines)


if __name__ == "__main__":
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