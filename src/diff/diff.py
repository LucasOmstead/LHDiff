from typing import List 

def reconstruct_from_trace(old_file_text, new_file_text, trace):
    edits = []
    x, y = len(old_file_text), len(new_file_text)

    #backtrack through trace from last D
    for D in reversed(range(len(trace))):
        if D == 0:
            #at D=0, only snake (matches) from origin
            while x > 0 and y > 0:
                edits.append(f"{x}:{y}")
                x -= 1
                y -= 1
            break
        
        #V is state before this edit (at D-1)
        V = trace[D - 1]
        k = x - y

        #determine predecessor diagonal
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

        #snake backwards (matches)
        while x > x_prev and y > y_prev:
            edits.append(f"{x}:{y}")
            x -= 1
            y -= 1

        #add edit that changed D
        if op == "insert":
            y -= 1
            edits.append(f"{y+1}+")
        elif op == "delete":
            x -= 1
            edits.append(f"{x+1}-")

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
            #k = diagonal, insertion raises by 1, deletion lowers by 1
            #frontier[k] = max x reachable with <= D ops on diagonal k
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