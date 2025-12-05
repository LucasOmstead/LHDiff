# LHDiff

A hybrid line-based diff tool that combines the Myers diff algorithm (exact matching) with similarity-based matching to compute differences between two files. The tool includes preprocessing capabilities to normalize source code before comparison, making it robust to whitespace, case, and comment differences.

## Features

- **Hybrid Diff Algorithm**: 
  - **Myers Algorithm**: Efficient O(ND) algorithm for exact line matching
  - **Similarity Matching**: Fuzzy matching using Levenshtein distance and cosine similarity for modified lines
  - **Two-Pass Approach**: Exact matches first, then similarity matching for remaining lines
- **Code Normalization**: Preprocessing functions that normalize source code by:
  - Stripping whitespace and normalizing tabs
  - Converting to lowercase
  - Removing inline comments (`//` and `#`)
  - Normalizing operator spacing
  - Collapsing multiple spaces
- **Hash Support**: Optional MD5 hashing of diff results for verification and identification
- **Comprehensive Testing**: Full test suite covering edge cases, normal operations, and integration scenarios

## Project Structure

```
LHDiff/
├── app.py                  # Main application (to be implemented)
├── README.md               # Project documentation
├── .gitignore             # Git ignore rules
├── src/                   # Source package
│   ├── __init__.py        # Package initialization
│   ├── models.py          # Shared data models
│   ├── diff/              # Core diff functionality
│   │   ├── __init__.py
│   │   ├── diff.py            # Myers diff algorithm (exact matching)
│   │   ├── diff_hybrid.py     # Hybrid diff (exact + similarity matching)
│   │   ├── preprocessing.py   # Code normalization functions
│   │   └── matcher.py         # Similarity-based line matching
│   └── bug_tracking/      # Bug tracking and backtracking
│       ├── __init__.py
│       ├── bug_detector.py      # Bug fix detection in commits
│       ├── bug_signature.py     # Bug signature extraction
│       ├── bug_backtracker.py   # Main bug backtracking API
│       ├── commit_history.py    # Commit history management
│       ├── file_version_loader.py  # File version loading
│       └── line_tracker.py       # Line tracking through history
└── tests/                 # Test suite
    ├── __init__.py
    ├── run_tests.py       # Test runner script
    ├── test_integration.py    # Full pipeline tests
    ├── test_bug_*.py      # Bug tracking tests
    └── test_case_*.txt    # Test case files
```
    ├── __init__.py        # Test package initialization
    ├── test_integration.py    # Full pipeline tests using test case files
    ├── test_case_1_old.txt    # Test case 1 - old version
    ├── test_case_1_new.txt    # Test case 1 - new version
    ├── test_case_2_old.txt    # Test case 2 - old version
    └── test_case_2_new.txt    # Test case 2 - new version
```

## Requirements

- Python 3.6+

No external dependencies required - uses only Python standard library.

## Usage

### Hybrid Diff Algorithm (Recommended)

```python
from src.diff import get_diff_hybrid, get_diff_with_hash

# Files are represented as List[List[str]]
# Each element is a list (can represent a line or tokens)
old_file = [["line1"], ["line2"], ["line3"]]
new_file = [["line1"], ["modified_line2"], ["line3"], ["line4"]]

# Get the diff with hybrid matching
result = get_diff_hybrid(old_file, new_file)
# Result: ['0:0', '1~1', '2:2', '3+']

# Get diff with hash
result_with_hash = get_diff_with_hash(old_file, new_file)
# Result: {'diff': ['0:0', '1~1', '2:2', '3+'], 'hash': 'a3f5b2c1...'}
```

### Diff Output Format

The hybrid diff algorithm returns a list of edit operations:
- `"x:y"` - **Exact match**: line `x` in old file exactly matches line `y` in new file
- `"x~y"` - **Similarity match**: line `x` in old file is similar to line `y` in new file (modified but similar)
- `"x+"` - **Insertion**: line `x` was inserted in the new file
- `"x-"` - **Deletion**: line `x` was deleted from the old file

### Basic Diff Algorithm (Exact Matching Only)

```python
from src.diff import get_diff

# Uses only Myers algorithm for exact matching
result = get_diff(old_file, new_file)
# Result: ['0:0', '1-', '1+', '2:2', '3+']  # Modified lines shown as deletion + insertion
```

### Preprocessing

```python
from src.preprocessing import preprocess_line, preprocess_lines, preprocess_file

# Normalize a single line
normalized = preprocess_line("   int Count = 5;   // comment")
# Result: "int count = 5"

# Normalize multiple lines
lines = ["int x = 5;", "return x+1;"]
normalized_lines = preprocess_lines(lines)

# Preprocess a file
normalized_lines = preprocess_file("path/to/file.py")
```

### Full Pipeline Example

```python
from src.diff import preprocess_file, get_diff_hybrid, get_diff_with_hash

# Preprocess both files
old_lines = preprocess_file("old_file.py")
new_lines = preprocess_file("new_file.py")

# Convert to List[List[str]] format for diff algorithm
old = [[line] for line in old_lines]
new = [[line] for line in new_lines]

# Compute hybrid diff (exact + similarity matching)
diff = get_diff_hybrid(old, new)
print(diff)
# Example: ['0:0', '1~1', '2:2', '3+']

# Or get diff with hash for verification
result = get_diff_with_hash(old, new)
print(f"Diff: {result['diff']}")
print(f"Hash: {result['hash']}")
```

### Similarity Threshold

You can adjust the similarity threshold for fuzzy matching:

```python
# Lower threshold = more permissive matching (default: 0.6)
result = get_diff_hybrid(old, new, similarity_threshold=0.5)

# Disable similarity matching (use only exact matching)
result = get_diff_hybrid(old, new, use_similarity=False)
```

## Testing

The project uses full pipeline tests that test the complete workflow from file input to diff output.

### Test Suite

**`test_integration.py`**: Full pipeline tests using test case files
- Tests the complete workflow: preprocessing → diff algorithm
- Uses test case files (`test_case_1_*.txt` and `test_case_2_*.txt`)
- Verifies the entire pipeline works correctly

### Running Tests

Run the full pipeline tests:
```bash
python3 run_tests.py
```

This will:
1. Load test case files from the `tests/` directory
2. Run preprocessing on both old and new files
3. Compute the diff using the Myers algorithm
4. Verify the results

### Test Case Files

The test suite uses two test case file pairs:

1. **`test_case_1_*.txt`**: Complex Python function changes
   - Tests function modifications, additions, and updates
   - Includes comment handling and code structure changes

2. **`test_case_2_*.txt`**: Simple C-style code changes
   - Tests variable removal and calculation changes
   - Tests basic code modifications

## Algorithm Details

### Hybrid Approach

The diff tool uses a **two-pass hybrid approach**:

1. **First Pass - Exact Matching (Myers Algorithm)**:
   - Finds exact line matches using the Myers diff algorithm
   - Efficient O(ND) time complexity
   - Uses dynamic programming with a frontier-based approach
   - Tracks diagonal paths in the edit graph to find optimal matches

2. **Second Pass - Similarity Matching**:
   - Processes unmatched lines from the first pass
   - Uses **Levenshtein distance** for character-level similarity
   - Uses **cosine similarity** for context-based matching (surrounding lines)
   - Combines both metrics with weighted scoring (default: 60% content, 40% context)
   - Only matches lines above a similarity threshold (default: 0.6)

### Benefits

- **More informative**: Modified lines shown as `x~y` instead of `x-` + `x+`
- **Better matching**: Handles moved/refactored code better
- **Backward compatible**: Can disable similarity matching to use only exact matching
- **Hash support**: Optional MD5 hashing for diff result verification

## Development

### Adding New Features

- **Preprocessing**: Add new normalization rules in `src/preprocessing.py`
- **Diff Algorithm**: The core algorithm is in `diff.py`
- **Application**: Main CLI/application logic should go in `app.py`

### Testing New Features

When adding new features:
1. Add unit tests to the appropriate test file
2. Add integration tests if the feature affects the pipeline
3. Run `python3 run_tests.py` to ensure all tests pass


