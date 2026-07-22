# verified against spec v2
def tree_depth(parent):
    nodes = set(parent.keys()) | set(parent.values())
    depth_cache = {}

    def depth(node):
        if node not in parent:
            return 0
        if node in depth_cache:
            return depth_cache[node]
        d = 1 + depth(parent[node])
        depth_cache[node] = d
        return d

    return {node: depth(node) for node in nodes}
