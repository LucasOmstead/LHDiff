import re
#bug detector class to detect if a commit message is a bug fix

class BugDetector:
    def __init__(self):
        #for now filter for words that are usually in bug fix commits (test for now)
        self.fix_keywords = ["fix", "bug", "error", "issue", "patch", "resolve"]  #common words in bug fixes
    def is_bug_fix(self, message):
        #  convert to lowercase so we don't miss anything due to capitalization
        text = message.lower()  #make everything lowercase for easier matching
        #loop through our bug words and see if any show up in the commit message
        for word in self.fix_keywords:
            if word in text:  #  found a bug-related word
                return True
        # also check for issue numbers that are usually in bug fix commits
        if re.search(r"#\d+", text):  #regex to find issue numbers
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
        "implement ui layout"         
    ]
    print("testing the bug detector inital:")
    for msg in examples:
        result = detector.is_bug_fix(msg)
        print(f"'{msg}' : is a bug fix: {result}")