def neighbor_order(mesh, v, parent):
    manifold, ordered = mesh.fan(v)
    if manifold:
        start = parent if parent is not None else min(ordered, key=mesh.position_key)
        i = ordered.index(start)
        return ordered[i:] + ordered[:i]
    return ordered


def choose_root(mesh, candidates):
    def key(v):
        return (mesh.position_key(v), mesh.degree(v),
                min(mesh.position_key(w) for w in mesh.neighbors(v)))
    best = min(candidates, key=key)
    ties = [v for v in candidates if key(v) == key(best)]
    if len(ties) > 1:
        raise ValueError("racine ambigue")
    return best


def build_tree(mesh):
    remaining = {v for v in mesh.visible_vertices() if not not mesh.faces_with_v[v]}
    order: list[int] = []
    parent: dict[int, int | None] = {}
    while remaining:
        root = choose_root(mesh, remaining)
        parent[root] = None
        order.append(root)
        remaining.discard(root)
        stack = [iter(neighbor_order(mesh, root, None))]
        path = [root]
        while stack:
            for w in stack[-1]:
                if w in remaining:
                    parent[w] = path[-1]
                    order.append(w)
                    remaining.discard(w)
                    stack.append(iter(neighbor_order(mesh, w, path[-1])))
                    path.append(w)
                    break
            else:
                stack.pop()
                path.pop()
    return order, parent
