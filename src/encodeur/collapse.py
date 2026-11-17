from dataclasses import dataclass

import numpy as np

from quadrics import collapse_cost


@dataclass
class Collapse:
    v_keep: int
    v_del: int
    w1: int                      # sommets opposés de l'arête dans M(i+1) (deviennent les cut-edges)
    w2: int
    del_neighbors: list[int]     # voisins de v_del dans M(i+1), ordre cyclique, v_keep en tête
    position: np.ndarray
    cost: float = 0.0


def undirected(a, b):
    return min(a, b), max(a, b)


def visible_edges(mesh):
    edges = set()
    for f in mesh.visible_faces():
        a, b, c = mesh.vertices_from_f(f)
        edges.add(undirected(a, b))
        edges.add(undirected(b, c))
        edges.add(undirected(c, a))
    return edges


def opposite_sides(mesh, v1, v2):
    sides = []
    # on regarde toutes les faces de l'arête (v1, v2) et on récupère les sommets opposés
    for w in mesh.opposite_vertices(v1, v2):
        for v in (v1, v2):
            for x in mesh.opposite_vertices(v, w):
                if x != v1 and x != v2:
                    # on a un quadrilatère (v1, v2, w, x), on récupère le côté opposé (w, x)
                    # sides = [(w, x), (x, w)] mais on ne garde que (min, max) pour éviter les doublons
                    sides.append(undirected(w, x))
    return sides


def half_edge_validity(mesh, v_keep, v_del):
    # 3ème sommets des triangles de l'arête (v_keep, v_del)
    opp = mesh.opposite_vertices(v_keep, v_del)
    # on a exactement deux w (w1 et w2), qui sont différents
    if len(opp) != 2 or opp[0] == opp[1]:
        return False, None, None
    w1, w2 = opp
    # contrainte 2 (condition de lien)
    if mesh.neighbors(v_keep) & mesh.neighbors(v_del) != {w1, w2}:
        return False, None, None
    return True, w1, w2


def apply_collapse(mesh, c):
    # parcours des faces contenant l'arête (v_keep, v_del) et suppression de ces faces
    for f in mesh.faces_of_edge(c.v_keep, c.v_del):
        mesh.remove_face(f)
    # faces incidentes à v_del : on remplace v_del par v_keep dans les faces restantes
    for f in list(mesh.faces_with_v[c.v_del]):
        mesh.replace_vertex_in_face(f, c.v_del, c.v_keep)
    mesh.remove_vertex(c.v_del)


def select_and_apply_batch(mesh, Q, max_collapses, strategy="qem", rng=None):
    if max_collapses <= 0:
        return []
    # contiendra le mesh original pour vérifier les conditions de lien
    orig = mesh.copy()

    # liste vide qui contient les collapses possibles
    candidates = []
    for a, b in visible_edges(orig):
        if orig.non_manifold[a] or orig.non_manifold[b]:
            continue
        for v_keep, v_del in ((a, b), (b, a)):
            if strategy == "qem":
                cost = collapse_cost(Q, orig, v_keep, v_del)
            elif strategy == "random":
                cost = rng.random()
            else:
                raise ValueError(f"stratégie inconnue : {strategy}")
            # on stocke le candidat avec son coût
            candidates.append((cost, v_keep, v_del))
    # tri des candidats par coût croissant (glouton)
    candidates.sort()
    # sommets déjà utilisés
    used: set[int] = set()
    # arêtes interdites
    blocked: set[tuple[int, int]] = set()
    selected: list[Collapse] = []
    # retrouver le sommet qui a absorbé un sommet supprimé v_del -> v_keep
    keeper: dict[int, int] = {}
    # parcours des candidats triés par coût croissant
    for cost, v_keep, v_del in candidates:
        # si le nombre maximal de collapses est atteint, on arrête
        if len(selected) >= max_collapses:
            break
        # contrainte 1 (au plus 2 sommets fusionnés en 1)
        if v_keep in used or v_del in used:
            continue
        edge = undirected(v_keep, v_del)
        # contrainte 3 (côtés opposés d'un quadrilatère) : la relation étant symétrique,
        # il suffit de vérifier que l'arête n'est opposée à aucune arête déjà sélectionnée
        if edge in blocked:
            continue
        ok, w1, w2 = half_edge_validity(mesh, v_keep, v_del)
        if not ok:
            continue
        # parcours les voisins dans l'ordre cyclique de v_del
        _, fan = orig.fan(v_del)
        # position de v_keep dans les voisins de v_del
        i = fan.index(v_keep)
        # on réagence l'ordre des voisins pour que v_keep soit en tête
        del_neighbors = fan[i:] + fan[:i]
        c = Collapse(v_keep, v_del, w1, w2, del_neighbors, orig.vertices[v_del].copy(), cost)
        apply_collapse(mesh, c)
        # on ajoute la quadrique de v_del à celle de v_keep pour le QEM
        if Q is not None:
            Q[v_keep] += Q[v_del]
        # contrainte 1 (au plus 2 sommets fusionnés en 1)
        used.update((v_keep, v_del))
        blocked.update(opposite_sides(orig, v_keep, v_del))
        keeper[v_del] = v_keep
        # ajoute le collapse à la liste des collapses sélectionnés
        selected.append(c)

    for c in selected:
        # si un collapse a supprimé un sommet opposé, on le remplace par le sommet qui l'a absorbé
        c.w1 = keeper.get(c.w1, c.w1)
        c.w2 = keeper.get(c.w2, c.w2)
    return selected
