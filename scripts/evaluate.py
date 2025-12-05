# evaluate.py
#
# Evaluate src.matcher.match_lines() against ground-truth mapping files
# generated from output.txt.
#
# Dataset layout (inside tests/):
#   test_case_N_old.<any ext>
#   test_case_N_new.<same ext>
#   test_case_N_map.txt
#
# Each map file has lines "i-j" meaning:
#   line i in preprocessed old file corresponds to line j in preprocessed new file.

import os

from src.preprocessing import preprocess_file
from src.matcher import match_lines


def load_mapping_file(path):
    """
    Read a mapping file with lines like 'i-j'
    and return a set of (int(i), int(j)).
    """
    pairs = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            left, right = line.split("-")
            pairs.add((int(left), int(right)))
    return pairs


def find_test_case_ids(dataset_dir):
    """
    Find all N such that we have at least:
        test_case_N_old.*
        test_case_N_new.*
        test_case_N_map.txt
    """
    ids = set()
    for name in os.listdir(dataset_dir):
        # e.g., test_case_1_old.py, test_case_20_old.html, etc.
        if name.startswith("test_case_") and "_old." in name:
            middle = name[len("test_case_") :]   # "1_old.py"
            num_str = middle.split("_")[0]       # "1"
            ids.add(num_str)

    valid_ids = []
    for idx in sorted(ids, key=lambda x: int(x)):
        old_path = None
        new_path = None
        map_path = os.path.join(dataset_dir, f"test_case_{idx}_map.txt")

        # Find matching old/new files regardless of extension
        for name in os.listdir(dataset_dir):
            if name.startswith(f"test_case_{idx}_old."):
                old_path = os.path.join(dataset_dir, name)
            elif name.startswith(f"test_case_{idx}_new."):
                new_path = os.path.join(dataset_dir, name)

        if old_path and new_path and os.path.exists(map_path):
            valid_ids.append(idx)
        else:
            print(f"[WARN] Skipping test_case_{idx}: missing old/new/map")

    return valid_ids


def evaluate_dataset(dataset_dir):
    """
    Evaluate match_lines() on all test cases in dataset_dir.
    Prints per-case accuracy and returns overall accuracy.
    """
    case_ids = find_test_case_ids(dataset_dir)
    if not case_ids:
        print("[ERROR] No valid test cases found.")
        return 0.0

    total_correct = 0
    total_gt = 0

    print(f"Found {len(case_ids)} test cases in {dataset_dir}\n")

    for idx in case_ids:
        # Find old/new again (so we also know full paths)
        old_path = None
        new_path = None
        map_path = os.path.join(dataset_dir, f"test_case_{idx}_map.txt")

        for name in os.listdir(dataset_dir):
            if name.startswith(f"test_case_{idx}_old."):
                old_path = os.path.join(dataset_dir, name)
            elif name.startswith(f"test_case_{idx}_new."):
                new_path = os.path.join(dataset_dir, name)

        if not (old_path and new_path and os.path.exists(map_path)):
            print(f"[WARN] Skipping test_case_{idx}: missing files at evaluation time")
            continue

        # Preprocess files in the same way as run_tests.py
        old_lines = preprocess_file(old_path)
        new_lines = preprocess_file(new_path)

        # Run your matcher (this is what you're evaluating)
        pred_pairs = set(match_lines(old_lines, new_lines))

        # Load ground truth
        gt_pairs = load_mapping_file(map_path)

        correct = len(pred_pairs & gt_pairs)
        gt_count = len(gt_pairs)
        acc = correct / gt_count if gt_count > 0 else 0.0

        print(f"test_case_{idx}: {correct}/{gt_count} correct  (acc = {acc:.3f})")

        total_correct += correct
        total_gt += gt_count

    overall_acc = total_correct / total_gt if total_gt > 0 else 0.0
    print(f"\nOverall: {total_correct}/{total_gt} correct  (acc = {overall_acc:.3f})")
    return overall_acc


if __name__ == "__main__":
    tests_dir = os.path.join("tests")
    print("Evaluating tests/ ...")
    evaluate_dataset(tests_dir)