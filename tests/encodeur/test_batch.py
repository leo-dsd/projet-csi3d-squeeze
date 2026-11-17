"""Batch écrit à la main pour l'octaèdre, après le collapse (4, 0) (4 reste, 0 disparaît).

Mi a 5 sommets : 1, 2, 3, 4, 5. Arbre sur Mi : ordre [1, 3, 5, 2, 4], parent de 4 = 2.
Numérotation des arêtes de 4 dans Mi, en partant du parent 2 : [2, 1, 3, 5].
- cut-edges : vers w1 = 2 (n° 0) et w2 = 3 (n° 2)  ->  (0, 2)
- 0 avait pour voisins 4, 3, 5, 2 : le seul qui repart vers 0 est 5 (n° 3), qui n'est pas
  strictement entre 0 et 2  ->  direction False
- prédiction : moyenne de 4, 3, 5, 2 = (0, 0, 0) ; 0 était en (1, 0, 0)  ->  erreur (1, 0, 0)
"""

from batch import connectivity_bits, write_batch
from collapse import Collapse, apply_collapse
from tree import build_tree


def batch_octaedre(octa):
    c = Collapse(v_keep=4, v_del=0, w1=2, w2=3, del_neighbors=[4, 3, 5, 2],
                 position=octa.vertices[0].copy())
    apply_collapse(octa, c)
    order, parent = build_tree(octa)
    return c, order, parent, write_batch(octa, [c], order, parent)


def test_arbre_sur_mi(octa):
    _, order, parent, _ = batch_octaedre(octa)
    assert order == [1, 3, 5, 2, 4]
    assert parent[4] == 2


def test_marques(octa):
    _, _, _, batch = batch_octaedre(octa)
    # seul 4 (dernier du parcours) est un split-vertex
    assert batch["marks"] == [False, False, False, False, True]


def test_split(octa):
    _, _, _, batch = batch_octaedre(octa)
    assert batch["splits"] == [
        {"cut_edges": (0, 2), "direction": False, "error": (1.0, 0.0, 0.0)},
    ]


def test_bits_connectivite(octa):
    c, order, _, _ = batch_octaedre(octa)
    # 5 marques + 1 bit de direction + ceil(log2 C(4, 2)) = ceil(log2 6) = 3 bits
    assert connectivity_bits(octa, [c], len(order)) == 5 + 1 + 3
