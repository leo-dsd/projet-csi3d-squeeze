import math

from prediction import predict
from tree import neighbor_order


def write_batch(mesh_i, collapses, order, parent):
    # dict associant chaque sommet conservé à son collapse
    split_of = {c.v_keep: c for c in collapses}
    # indique où retrouver un ancien voisin lui-même supprimé
    keeper = {c.v_del: c.v_keep for c in collapses}
    # liste des v_del
    deleted = set(keeper)
    # booléen par sommet de order : True si c'est un split-vertex, False sinon
    marks: list[bool] = []
    splits: list[dict] = []
    for v in order:
        # on récupère le collapse associé à v (None si ce n'est pas un split-vertex)
        c = split_of.get(v)
        # si un collapse existe on passe v à True, sinon à False
        marks.append(c is not None)
        if c is None:
            continue
        # on utilise le parent pour retrouver l'ordre cyclique des voisins de v
        numbering = neighbor_order(mesh_i, v, parent[v])
        # correspondance voisin : index dans numbering
        index = {w: i for i, w in enumerate(numbering)}
        # les 2 côtés de l'éventail sont les 2 sommets opposés à l'arête (v_keep, v_del)
        c1, c2 = sorted((index[c.w1], index[c.w2]))
        # on récupère les voisins strictement entre c1 et c2 (en suivant l'ordre horaire)
        inner = set(numbering[c1 + 1:c2])
        # on récup les voisins de v_del (ou leur nouvelle valeur s'ils ont été suppr), on enlève w1 et w2 car appartiennent aux 2 v
        moved = {keeper.get(m, m) for m in c.del_neighbors[1:]} - {c.w1, c.w2}
        # vérifie la bonne direction de l'éventail
        if moved == inner:
            direction = True
        else:
            direction = False
        # on récupère les anciens voisins de v_del qui sont encore dans Mi
        old_neighbors = [m for m in c.del_neighbors if m not in deleted]
        # on estime la position de v_del à partir de ses anciens voisins (dans Mi) et on calcule l'erreur
        v_est = predict(mesh_i.vertices, old_neighbors)
        error = c.position - v_est
        splits.append({
            "cut_edges": (c1, c2),
            "direction": direction,
            "error": (float(error[0]), float(error[1]), float(error[2])),
        })
    return {"marks": marks, "splits": splits}


def connectivity_bits(mesh_i, collapses, n_marks):
    bits = n_marks
    for c in collapses:
        d = mesh_i.degree(c.v_keep)
        bits += 1 + math.ceil(math.log2(d * (d - 1) // 2))
    return bits
