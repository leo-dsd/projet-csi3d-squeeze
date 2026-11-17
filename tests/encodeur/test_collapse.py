from collapse import (Collapse, apply_collapse, half_edge_validity, opposite_sides,
                      select_and_apply_batch)
from quadrics import compute_quadrics


def collapse_4_0(mesh):
    """Collapse de l'arête (4, 0) de l'octaèdre : 4 reste, 0 disparaît."""
    c = Collapse(v_keep=4, v_del=0, w1=2, w2=3, del_neighbors=[4, 3, 5, 2],
                 position=mesh.vertices[0].copy())
    apply_collapse(mesh, c)
    return c


def test_cotes_opposes(octa):
    # quadrilatères ayant (4, 0) pour côté : (4, 0, 2, 1), (4, 0, 2, 5), (4, 0, 3, 1), (4, 0, 3, 5)
    assert sorted(opposite_sides(octa, 4, 0)) == [(1, 2), (1, 3), (2, 5), (3, 5)]


def test_condition_de_lien_valide(octa):
    ok, w1, w2 = half_edge_validity(octa, 4, 0)
    assert ok
    assert {w1, w2} == {2, 3}


def test_apply_collapse(octa):
    collapse_4_0(octa)
    # 2 faces de l'arête supprimées, 1 sommet en moins
    assert octa.n_visible_v == 5
    assert octa.n_visible_f == 6
    assert not octa.visible_v[0]
    # 4 récupère le voisin 5 de 0 (et garde 1, 2, 3)
    assert octa.neighbors(4) == {1, 2, 3, 5}


def test_condition_de_lien_refusee(octa):
    """Après le collapse (4, 0), le maillage est une double pyramide : sommets 2 et 3 en
    haut et en bas, triangle 1, 4, 5 au milieu. L'arête (1, 4) a pour sommets opposés 2 et
    3, mais 1 et 4 ont aussi 5 comme voisin commun : la collapser pincerait le maillage."""
    collapse_4_0(octa)
    ok, _, _ = half_edge_validity(octa, 1, 4)
    assert not ok


def test_batch_octaedre(octa):
    Q = compute_quadrics(octa)
    collapses = select_and_apply_batch(octa, Q, max_collapses=10)
    assert len(collapses) >= 1
    # contrainte 1 : aucun sommet n'apparaît dans deux collapses
    sommets = [v for c in collapses for v in (c.v_keep, c.v_del)]
    assert len(sommets) == len(set(sommets))
    # chaque collapse retire 1 sommet et 2 faces
    assert octa.n_visible_v == 6 - len(collapses)
    assert octa.n_visible_f == 8 - 2 * len(collapses)
    # le maillage obtenu est toujours fermé et manifold
    for v in octa.visible_vertices():
        manifold, _ = octa.fan(v)
        assert manifold


def test_bord_jamais_collapse(fan4):
    # toutes les arêtes touchent un sommet du bord : aucun collapse possible
    Q = compute_quadrics(fan4)
    assert select_and_apply_batch(fan4, Q, max_collapses=10) == []
    assert fan4.n_visible_v == 5
