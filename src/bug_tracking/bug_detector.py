import re

# Utilities to parse commit messages from a text file and detect which messages are likely bug fixes based on 
# keywords, prefixes, and issue references
def parse_commit_messages(file_path, target_file_name=None):
    """
    Read a simple commit log file and group messages by file name.

    The expected format is blocks separated by blank lines, where each block
    starts with a line like:
        <file_name>:
    followed by the commit message body.
    """
    commits = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split commits on double newlines so each block represents 1 entry
    entries = content.split('\n\n')
    for entry in entries:
        entry = entry.strip()
        if not entry or ':' not in entry:
            continue
        # Split only on the first colon to separate file name from message text
        parts = entry.split(':', 1)
        if len(parts) != 2:
            continue
        file_name = parts[0].strip()
        message = parts[1].strip()
        # Accumulate all messages belonging to the same file
        if file_name not in commits:
            commits[file_name] = []
        commits[file_name].append(message)
    
    # Optionally returns only the messages for a single file
    if target_file_name:
        return commits.get(target_file_name, [])
    return commits

class BugDetector:
    def __init__(self):
        # Keywords commonly found in bug fix commits
        self.fix_keywords = [
            "fix", "bug", "error", "issue", "patch", "resolve",
            "crash", "fatal", "critical", "urgent", "security", "vulnerability",
            "hotfix", "bugfix", "defect", "fault", "broken", "broke", "fail", "failure",
            "regression", "revert", "corrupt", "incorrect", "wrong",
            "prevent", "avoid", "stop", "block",
            "leak", "overflow", "underflow",
            "hang", "freeze",
            "undefined",
            "exception",
            "typo", "spelling",
            "repair", "correct", "amend", "rectify"
        ]
        
        # Conventional commit prefixes for bug fixes
        self.conventional_prefixes = [
            "fix:", "fix(", "hotfix:", "hotfix(", 
            "bugfix:", "bugfix(", "perf:", "perf(",
            "revert:", "revert(", "security:", "security("
        ]
    def is_bug_fix(self, message):
        # Lowercase for case-insensitive matching
        text = message.lower()
        
        # Check conventional commit prefix
        for prefix in self.conventional_prefixes:
            if text.startswith(prefix):
                return True
        
        # Check for bug-related keywords
        for word in self.fix_keywords:
            if word in text:
                return True
        # Check for issue numbers
        if re.search(r"#\d+", text):
            return True
        # Check for action words with issue numbers
        if re.search(r"(closes|fixes|resolves|fixed|resolved)\s+#?\d+", text):
            return True
        # No bug indicators found
        return False


if __name__ == "__main__":
    # Simple self-test demonstrating how the BugDetector class behaves
    detector = BugDetector()
    examples = [
        "fix crash on login",
        "add new feature",
        "resolve issue #234",
        "implement ui layout",
        "fix: resolve null pointer exception in user service",
        "fix(auth): prevent memory leak in session handler",
        "hotfix: critical security vulnerability in payment module",
        "bugfix(api): correct broken endpoint for user data",
        "perf: fix slow query causing timeout",
        "revert: rollback changes that broke production",
        "fixes #456 - crash when clicking submit button",
        "resolves issue with incorrect validation logic",
        "prevent overflow in buffer handling",
        "correct typo causing failure",
        "docs: add installation instructions",
        "feat: implement new dashboard",
        "test: add unit tests for validator",
        "refactor: extract helper functions",
        "repair broken link in navigation",
        "urgent hotfix for production crash",
    ]
    print("Testing BugDetector:")
    for msg in examples:
        result = detector.is_bug_fix(msg)
        print(f"'{msg}' : {result}")
    
    print("\n" + "="*60)
    print("Testing parse_commit_messages:")
    test_data = """auth:
initial authentication module

auth:
add login functionality

auth:
fix: resolve null pointer in login

user:
create user model

user:
add user validation

auth:
refactor authentication flow

auth:
hotfix: critical security issue in token generation"""
    
    # Write a temporary test file and feed it through the parser
    with open("test_commits.txt", "w") as f:
        f.write(test_data)
    
    all_commits = parse_commit_messages("test_commits.txt")
    print(f"\nAll commits: {all_commits}")
    
    auth_commits = parse_commit_messages("test_commits.txt", "auth")
    print(f"\nauth commits: {auth_commits}")
    
    user_commits = parse_commit_messages("test_commits.txt", "user")
    print(f"\nuser commits: {user_commits}")
    
    import os
    # Clean up the temporary file after the demonstration run
    os.remove("test_commits.txt")