import numpy as np

from mesh import Mesh


def test_voisins_et_degre(octa):
    assert octa.neighbors(4) == {0, 1, 2, 3}
    assert octa.degree(4) == 4
    assert octa.neighbors(0) == {2, 3, 4, 5}   # tout sauf 0 et son opposé 1


def test_next(octa):
    # la face (4, 0, 2) donne : après (4, 0) vient 2, après (0, 2) vient 4
    assert octa.next(4, 0) == 2
    assert octa.next(0, 2) == 4
    # 4 et 5 ne sont pas reliés : aucune face (4, 5, x)
    assert octa.next(4, 5) is None


def test_sommets_opposes(octa):
    # l'arête (0, 2) est dans les faces (4, 0, 2) et (5, 2, 0)
    assert sorted(octa.opposite_vertices(0, 2)) == [4, 5]


def test_eventail_ferme(octa):
    # autour du sommet du haut : 0 -> 2 -> 1 -> 3, en partant du plus petit indice
    assert octa.fan(4) == (True, [0, 2, 1, 3])


def test_bord_est_non_manifold(fan4):
    # les 4 sommets du bord ont un éventail ouvert, le centre a un éventail fermé
    assert fan4.non_manifold == [True, True, True, True, False]
    assert fan4.fan(4) == (True, [0, 1, 2, 3])


def test_face_degeneree_ignoree():
    mesh = Mesh([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 1)])
    assert mesh.n_visible_f == 0


def test_rebuild_renumerote():
    # le sommet 0 n'appartient à aucune face : on le supprime puis on exporte
    mesh = Mesh([(9, 9, 9), (0, 0, 0), (1, 0, 0), (0, 1, 0)], [(1, 2, 3)])
    mesh.remove_vertex(0)
    vertices, faces = mesh.rebuild()
    assert np.allclose(vertices, [(0, 0, 0), (1, 0, 0), (0, 1, 0)])
    assert faces == [(0, 1, 2)]   # les indices sont décalés de 1
