# runs the full diff algorithm pipeline and spits out a txt with line mappings
# compares old vs new versions of files and shows whats changed

import sys  # for exit codes and path stuff
import os  # file operations
import traceback  # for printing stack traces when things break

# need to add tests folder to path so imports work properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests')))

def main():
    # returns 0 if everything works, 1 if something breaks
    try:
        # run integration tests first before doing anything else
        import test_integration
        success = test_integration.run_test_case_files()
        # only continue if tests pass
        if success:
            print("PASSED: Test case files")
            # lazy imports - only load these if we actually need them
            import glob
            from src.preprocessing import preprocess_file  # cleans up the file content
            from diff_hybrid import get_diff_hybrid  # the actual diff logic
            test_dir = "tests"
            # grab all the old files, sorted so output is consistent
            old_files = sorted(glob.glob(f"{test_dir}/test_case_*_old.*"))
            # dump everything to output.txt
            with open("output.txt", "w") as f:
                # legend so people know what the symbols mean
                f.write("'x:y' = exact match (line x in old matches line y in new)\n")
                f.write("'x~y' = similarity match (line x in old is similar to line y in new)\n")
                f.write("'x-' = deletion (line x deleted from old)\n")
                f.write("'x+' = insertion (line x inserted in new)\n")
                f.write("\n")
                
                # go through each test case pair
                for i, old_file in enumerate(old_files, 1):
                    # figure out the matching new file by swapping the suffix
                    new_file = old_file.replace("_old.", "_new.")
                    
                    # skip if theres no matching new file
                    if os.path.exists(new_file):
                        # preprocess strips whitespace and normalizes stuff
                        old_lines = preprocess_file(old_file)
                        new_lines = preprocess_file(new_file)
                        # wrap each line in a list bc thats what diff_hybrid expects
                        old = []
                        for line in old_lines:
                            old.append([line])
                        new = []
                        for line in new_lines:
                            new.append([line])
                        # run the diff and get back the mapping
                        result = get_diff_hybrid(old, new)
                        # write results for this test case
                        f.write(f"Test case {i}:\n")
                        f.write(f"{result}\n")
                        f.write("\n")

            print("Generated: output.txt")
            return 0  # success
        else:
            # tests failed so dont bother running the rest
            print("FAILED: Test case files")
            return 1
    # something went wrong with imports
    except ImportError as e:
        print(f"ERROR: Could not import test_integration: {e}")
        traceback.print_exc()  # print full stack trace for debugging
        return 1
    # catch everything else
    except Exception as e:
        print(f"ERROR: Exception: {e}")
        traceback.print_exc()
        return 1

# only run if this file is executed directly, not imported
if __name__ == "__main__":
    sys.exit(main())
