# LHDiff

A line-based diff tool that uses the Myers diff algorithm to compute differences between two files. The tool includes preprocessing capabilities to normalize source code before comparison, making it robust to whitespace, case, and comment differences.

## Features

- **Myers Diff Algorithm**: Efficient O(ND) algorithm for computing the shortest edit script between two files
- **Code Normalization**: Preprocessing functions that normalize source code by:
  - Stripping whitespace and normalizing tabs
  - Converting to lowercase
  - Removing inline comments (`//` and `#`)
  - Normalizing operator spacing
  - Collapsing multiple spaces
- **Comprehensive Testing**: Full test suite covering edge cases, normal operations, and integration scenarios

## Project Structure

```
LHDiff/
├── diff.py                 # Myers diff algorithm implementation
├── app.py                  # Main application (to be implemented)
├── run_tests.py            # Test runner for all test suites
├── README.md               # Project documentation
├── .gitignore             # Git ignore rules
├── src/                   # Source package
│   ├── __init__.py        # Package initialization
│   ├── preprocessing.py   # Code normalization functions
│   └── matcher.py         # (Reserved for future use)
└── tests/                 # Test suite
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

### Basic Diff Algorithm

```python
from diff import get_diff

# Files are represented as List[List[str]]
# Each element is a list (can represent a line or tokens)
old_file = [["line1"], ["line2"], ["line3"]]
new_file = [["line1"], ["line2"], ["line3"], ["line4"]]

# Get the diff
result = get_diff(old_file, new_file)
# Result: ['0:0', '1:1', '2:2', '3+']
```

### Diff Output Format

The diff algorithm returns a list of edit operations:
- `"x:y"` - Match: line `x` in old file corresponds to line `y` in new file
- `"x+"` - Insertion: line `x` was inserted in the new file
- `"x-"` - Deletion: line `x` was deleted from the old file

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
from src.preprocessing import preprocess_file
from diff import get_diff

# Preprocess both files
old_lines = preprocess_file("old_file.py")
new_lines = preprocess_file("new_file.py")

# Convert to List[List[str]] format for diff algorithm
old = [[line] for line in old_lines]
new = [[line] for line in new_lines]

# Compute diff
diff = get_diff(old, new)
print(diff)
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

The diff algorithm implements the **Myers diff algorithm**, which:
- Finds the shortest edit script (minimum number of insertions/deletions)
- Uses dynamic programming with a frontier-based approach
- Has O(ND) time complexity where N is the sum of file lengths and D is the edit distance
- Tracks diagonal paths in the edit graph to find optimal matches

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

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
