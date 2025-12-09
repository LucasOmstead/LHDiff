# generate_maps_from_output.py
#
# Parse output.txt from run_tests.py and create
# tests/test_case_N_map.txt files with ground-truth mappings.
#
# We treat:
#   'x:y' -> exact match -> include as mapping (x, y)
#   'x~y' -> similarity match -> include as mapping (x, y)
#   'x-'  -> deletion (ignore for mapping)
#   'x+'  -> insertion (ignore for mapping)

import os
import ast

OUTPUT_FILE = "output.txt"
TEST_DIR = "tests"


def parse_token(token: str):
    """
    Convert a token like '3:5' or '3~5' into a (3, 5) mapping.
    Ignore deletions ('3-') and insertions ('3+').
    Return None for non-mapping tokens.
    """
    token = token.strip().strip("'").strip('"')

    # Deletion or insertion: 'x-' or 'x+'
    if token.endswith("-") or token.endswith("+"):
        return None

    if "~" in token:
        left, right = token.split("~", 1)
    elif ":" in token:
        left, right = token.split(":", 1)
    else:
        return None

    try:
        i = int(left)
        j = int(right)
        return (i, j)
    except ValueError:
        return None


def main():
    if not os.path.exists(OUTPUT_FILE):
        print(f"[ERROR] {OUTPUT_FILE} not found. Run run_tests.py first.")
        return 1

    with open(OUTPUT_FILE, encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    case_num = 0
    created = 0

    while i < len(lines):
        line = lines[i].strip()
        # Look for lines like "Test case 1: "
        if line.startswith("Test case "):
            case_num += 1

            # Next non-empty line should be the Python list of tokens
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i >= len(lines):
                break

            list_str = lines[i].strip()

            try:
                tokens = ast.literal_eval(list_str)
            except Exception as e:
                print(f"[WARN] Could not parse token list for test case {case_num}: {e}")
                i += 1
                continue

            mappings = []
            for tok in tokens:
                pair = parse_token(tok)
                if pair is not None:
                    # Output is already 1-based, use directly
                    mappings.append(pair)

            # Write test_case_N_map.txt in tests/test_cases/
            map_path = os.path.join(TEST_DIR, "test_cases", f"test_case_{case_num}_map.txt")
            with open(map_path, "w", encoding="utf-8") as mf:
                for (a, b) in mappings:
                    mf.write(f"{a}-{b}\n")

            print(f"[OK] Wrote {len(mappings)} mappings to {map_path}")
            created += 1

        i += 1

    print(f"\nDone. Created {created} map files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())