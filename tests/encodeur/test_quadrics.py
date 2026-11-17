import numpy as np

from mesh import Mesh
from quadrics import collapse_cost, compute_quadrics


def deux_plans():
    """Deux triangles qui se partagent l'arête (0, 1) :
    - (0, 1, 2) dans le plan z = 0
    - (0, 3, 1) dans le plan y = 0
    """
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    return Mesh(vertices, [(0, 1, 2), (0, 3, 1)])


def test_quadrique_d_un_plan():
    mesh = deux_plans()
    Q = compute_quadrics(mesh)
    # le sommet 2 ne touche que le plan z = 0, d'équation (0, 0, 1, 0) :
    # sa quadrique vaut (0, 0, 1, 0)ᵀ (0, 0, 1, 0), un seul coefficient non nul
    attendu = np.zeros((4, 4))
    attendu[2, 2] = 1.0
    assert np.allclose(Q[2], attendu)


def test_cout_collapse():
    mesh = deux_plans()
    Q = compute_quadrics(mesh)
    # on garde 2 = (0, 1, 0) et on supprime 3 (plan y = 0) : distance 1 au plan y = 0
    assert np.isclose(collapse_cost(Q, mesh, 2, 3), 1.0)
    # on garde 0 = (0, 0, 0), qui est sur les deux plans : coût nul
    assert np.isclose(collapse_cost(Q, mesh, 0, 3), 0.0)
