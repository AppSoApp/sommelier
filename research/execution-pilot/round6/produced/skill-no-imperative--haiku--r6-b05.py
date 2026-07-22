def is_reachable(graph, start, end):
    if start == end:
        return True
    visited = {start}
    stack = [start]
    while stack:
        node = stack.pop()
        for nxt in graph.get(node, []):
            if nxt == end:
                return True
            if nxt not in visited:
                visited.add(nxt)
                stack.append(nxt)
    return False
