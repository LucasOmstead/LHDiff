# Use PyDriller to extract old/new versions of modified files
# so we can build our 25-pair dataset with a mix of file types.

from pydriller import Repository # type: ignore
import os
from collections import defaultdict

# MUST CHANGE PATH TO REPO WHEN RUNNING ON A DIFFERENT MACHINE
REPO_PATH = "/Users/aleksavucak/Desktop/airflow"

print(f"[pairs.py] Using repo at: {REPO_PATH}")

# Where to save the pairs relative to LHDiff root
OUTPUT_DIR = "tests"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# How many file pairs to collect total
MAX_PAIRS = 50

# How many pairs PER EXTENSION we allow to enforce variety
EXT_LIMITS = {
    # The repo that was driller from is mostly Python, but don't let it dominate completely using constraints
    ".py": 15,
    ".html": 10,
    ".htm": 5,
    ".js": 10,
    ".ts": 5,
    ".tsx": 5,
    ".css": 5,
    ".scss": 5,
    ".yaml": 5,
    ".yml": 5,
    ".json": 5,
    ".sql": 5,
    ".sh": 5,
}

# For any extension not in EXT_LIMITS but we still want some of, you could define a default limit
# For now, we just skip unknown extensions
DEFAULT_LIMIT = 0 

pair_id = 1
ext_counts = defaultdict(int)

for commit in Repository(REPO_PATH).traverse_commits():
    for mod in commit.modified_files:
        # Only modified files, not added/deleted
        if mod.change_type.name != "MODIFY":
            continue

        # Need both before and after contents
        if mod.source_code_before is None or mod.source_code is None:
            continue

        _, ext = os.path.splitext(mod.filename)

        # If this extension isn't in our limits and DEFAULT_LIMIT == 0: skip
        limit = EXT_LIMITS.get(ext, DEFAULT_LIMIT)
        if limit == 0:
            continue

        # Respect per-extension cap
        if ext_counts[ext] >= limit:
            continue

        old_code = mod.source_code_before
        new_code = mod.source_code

        # Naming convention on the gathered 25 pairs follows:
            # test_case_001_old.py / test_case_001_new.py
        case_prefix = f"test_case_{pair_id}"
        old_path = os.path.join(OUTPUT_DIR, f"{case_prefix}_old{ext}")
        new_path = os.path.join(OUTPUT_DIR, f"{case_prefix}_new{ext}")

        with open(old_path, "w", encoding="utf-8") as f:
            f.write(old_code)
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(new_code)

        ext_counts[ext] += 1

        print(
            f"Saved {case_prefix} ({ext}) from commit {commit.hash[:8]}: "
            f"{mod.filename}"
        )
        pair_id += 1

        if pair_id > MAX_PAIRS:
            break

    if pair_id > MAX_PAIRS:
        break

print("Done.")
print("Per-extension counts:")
for e, c in sorted(ext_counts.items()):
    print(f"  {e}: {c}")