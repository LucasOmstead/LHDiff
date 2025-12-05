import re

def parse_commit_messages(file_path, target_file_name=None):
    commits = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    entries = content.split('\n\n')
    for entry in entries:
        entry = entry.strip()
        if not entry or ':' not in entry:
            continue
        parts = entry.split(':', 1)
        if len(parts) != 2:
            continue
        file_name = parts[0].strip()
        message = parts[1].strip()
        if file_name not in commits:
            commits[file_name] = []
        commits[file_name].append(message)
    
    if target_file_name:
        return commits.get(target_file_name, [])
    return commits

class BugDetector:
    def __init__(self):
        #for now filter for words that are usually in bug fix commits (test for now)
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
        ]  #common words in bug fixes
        
        #conventional commit format prefixes that indicate bug fixes
        self.conventional_prefixes = [
            "fix:", "fix(", "hotfix:", "hotfix(", 
            "bugfix:", "bugfix(", "perf:", "perf(",
            "revert:", "revert(", "security:", "security("
        ]
    def is_bug_fix(self, message):
        #  convert to lowercase so we don't miss anything due to capitalization
        text = message.lower()  #make everything lowercase for easier matching
        
        #check if message starts with conventional commit prefix
        for prefix in self.conventional_prefixes:
            if text.startswith(prefix):
                return True
        
        #loop through our bug words and see if any show up in the commit message
        for word in self.fix_keywords:
            if word in text:  #  found a bug-related word
                return True
        # also check for issue numbers that are usually in bug fix commits
        if re.search(r"#\d+", text):  #regex to find issue numbers
            return True
        #check for action words with issue numbers (fixes #123, resolves 456)
        if re.search(r"(closes|fixes|resolves|fixed|resolved)\s+#?\d+", text):
            return True
        #  if we didn't find any bug indicators, probably not a bug fix
        return False  #  no bug indicators found


if __name__ == "__main__":
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
    
    with open("test_commits.txt", "w") as f:
        f.write(test_data)
    
    all_commits = parse_commit_messages("test_commits.txt")
    print(f"\nAll commits: {all_commits}")
    
    auth_commits = parse_commit_messages("test_commits.txt", "auth")
    print(f"\nauth commits: {auth_commits}")
    
    user_commits = parse_commit_messages("test_commits.txt", "user")
    print(f"\nuser commits: {user_commits}")
    
    import os
    os.remove("test_commits.txt")