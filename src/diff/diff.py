from typing import List 

def reconstruct_from_trace(old_file_text, new_file_text, trace):
    edits = []
    x, y = len(old_file_text), len(new_file_text)

    # backtrack through trace from the last D
    for D in reversed(range(len(trace))):
        if D == 0:
            # At D=0, only snake (matches) from origin, no edit operation
            while x > 0 and y > 0:
                edits.append(f"{x-1}:{y-1}")
                x -= 1
                y -= 1
            break
        
        # V is the state BEFORE this edit (at D-1)
        V = trace[D - 1]
        k = x - y

        # determine predecessor diagonal
        if k == -D or (k != D and V.get(k-1, -1) < V.get(k+1, -1)):
            k_prev = k + 1
            x_prev = V.get(k_prev, 0)
            y_prev = x_prev - k_prev
            op = "insert"
        else:
            k_prev = k - 1
            x_prev = V.get(k_prev, 0)
            y_prev = x_prev - k_prev
            op = "delete"

        # snake backwards (matches)
        while x > x_prev and y > y_prev:
            # each diagonal match adds "line_file_1:line_file_2"
            edits.append(f"{x-1}:{y-1}")
            x -= 1
            y -= 1

        # add the edit that changed D
        if op == "insert":
            y -= 1
            edits.append(f"{y}+")
        elif op == "delete":
            x -= 1
            edits.append(f"{x}-")

    edits.reverse()
    return edits

def get_diff(old_file_text: List[List[str]], new_file_text: List[List[str]]):
    mapping = []
    max_diffs = len(old_file_text) + len(new_file_text)
    frontier = {1: 0}
    trace = []
    for ops in range(max_diffs+1):
        V = {}
        for k in range(-ops, ops+1, 2):
            #k = the diagonal that we're following
            #each insertion raises the diagonal by 1 and each deletion lowers it by 1, so diagonal = num_insertions - num_deletions
            #any matching we do must be along the diagonal
            #frontier[k] = the maximum x value that you can reach with <= D operations and on a diagonal of k
            #to start (since we aren't on a diagonal) we can either move right (delete) or down (insert)
            #then we follow the diagonal
            if k == -ops or (k != ops and frontier.get(k-1, -1) < frontier.get(k+1, 0)):
                x = frontier.get(k+1, 0)
            else:
                x = frontier.get(k-1, 0) + 1
            y = x-k
            if y < 0:
                continue
            while x < len(old_file_text) and y < len(new_file_text) and old_file_text[x] == new_file_text[y]:
                x += 1
                y += 1
            V[k] = x
            
            if x >= len(old_file_text) and y >= len(new_file_text):
                trace.append(V.copy())
                return reconstruct_from_trace(old_file_text, new_file_text, trace)
        trace.append(V.copy())
        frontier = V