def subtree_sizes(parent):
    nodes = set(parent.keys()) | set(parent.values())
    children = {n: [] for n in nodes}
    for (child, p) in parent.items():
        children[p].append(child)
    sizes = {}

    def size(node):
        if node in sizes:
            return sizes[node]
        s = 1 + sum((size(c) for c in children[node]))
        sizes[node] = s
        return s
    for n in nodes:
        size(n)
    return sizes
