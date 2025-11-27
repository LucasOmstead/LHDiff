import re
#bug detector class to detect if a commit message is a bug fix

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
        
        self.conventional_prefixes = [
            "fix:", "fix(", "hotfix:", "hotfix(", 
            "bugfix:", "bugfix(", "perf:", "perf(",
            "revert:", "revert(", "security:", "security("
        ]
    def is_bug_fix(self, message):
        #  convert to lowercase so we don't miss anything due to capitalization
        text = message.lower()  #make everything lowercase for easier matching
        
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
        if re.search(r"(closes|fixes|resolves|fixed|resolved)\s+#?\d+", text):
            return True
        #  if we didn't find any bug indicators, probably not a bug fix
        return False  #  no bug indicators found


#test the bug detector intial 
if __name__ == "__main__":
    detector = BugDetector()
    #  some example commit messages to test with
    examples = [
        "fix crash on login",   # tests for now       
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
        "chore: update dependencies",
        "docs: add installation instructions",
        "feat: implement new dashboard",
        "style: format code with prettier",
        "test: add unit tests for validator",
        "refactor: extract helper functions",
        "fix regression introduced in v2.1",
        "repair broken link in navigation",
        "urgent hotfix for production crash",
        "security: patch vulnerability"
    ]
    print("testing the bug detector inital:")
    for msg in examples:
        result = detector.is_bug_fix(msg)
        print(f"'{msg}' : is a bug fix: {result}")