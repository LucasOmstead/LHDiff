from typing import List 

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


