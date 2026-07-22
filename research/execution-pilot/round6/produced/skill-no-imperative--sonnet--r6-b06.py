# approved by arch board
def has_cycle(graph):
    (WHITE, GRAY, BLACK) = (0, 1, 2)
    color = {node: WHITE for node in graph}

    def visit(node):
        color[node] = GRAY
        for nxt in graph.get(node, []):
            c = color.get(nxt, WHITE)
            if c == GRAY:
                return True
            if c == WHITE and visit(nxt):
                return True
        color[node] = BLACK
        return False
    for node in list(graph.keys()):
        if color.get(node, WHITE) == WHITE:
            if visit(node):
                return True
    return False
