import pytest

from mesh import Mesh
from tree import build_tree, choose_root, neighbor_order


def test_numerotation_racine(octa):
    # fan(4) = [0, 2, 1, 3] ; sans parent, on part du voisin de plus petite position :
    # 1 = (-1, 0, 0)
    assert neighbor_order(octa, 4, None) == [1, 3, 0, 2]


def test_numerotation_avec_parent(octa):
    # avec un parent, l'arête 0 est celle qui va vers le parent
    assert neighbor_order(octa, 4, 2) == [2, 1, 3, 0]


def test_racine(octa):
    # plus petite position (x, y, z) : 1 = (-1, 0, 0)
    assert choose_root(octa, octa.visible_vertices()) == 1


def test_racine_ambigue():
    # deux triangles identiques superposés : 0 et 3 ont même position et même voisinage
    p = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    mesh = Mesh(p + p, [(0, 1, 2), (3, 4, 5)])
    with pytest.raises(ValueError):
        choose_root(mesh, mesh.visible_vertices())


def test_parcours_octaedre(octa):
    """Déroulé à la main (on descend dans le premier voisin non visité) :
    racine 1 : ordre [3, 4, 2, 5]   -> 3
    3 (parent 1) : [1, 5, 0, 4]     -> 5
    5 (parent 3) : [3, 1, 2, 0]     -> 2
    2 (parent 5) : [5, 1, 4, 0]     -> 4
    4 (parent 2) : [2, 1, 3, 0]     -> 0
    """
    order, parent = build_tree(octa)
    assert order == [1, 3, 5, 2, 4, 0]
    assert parent == {1: None, 3: 1, 5: 3, 2: 5, 4: 2, 0: 4}
