"""Vérifications simples du décodeur : cas limites, erreurs, et aller-retour encodeur -> décodeur."""

import numpy as np
import pytest

from decoder import appliquer_batch, arc_autour, decoder_stream, lire_splits
from encoder import encode
from exemples import faces_normalisees, octaedre
from mesh import Mesh


def faces_de(mesh):
    return faces_normalisees(mesh.vertices_from_f(f) for f in mesh.visible_faces())


def faces_en_positions(mesh):
    """Faces décrites par les positions (arrondies) : ne dépend pas de la numérotation."""
    out = []
    for f in mesh.visible_faces():
        p = [tuple(np.round(mesh.vertices[x], 9)) for x in mesh.vertices_from_f(f)]
        out.append(min([(p[0], p[1], p[2]), (p[1], p[2], p[0]), (p[2], p[0], p[1])]))
    return sorted(out)


def est_ferme_et_oriente(mesh):
    """Chaque arête orientée (a, b) apparaît une seule fois et son opposée (b, a) existe."""
    aretes = []
    for f in mesh.visible_faces():
        a, b, c = mesh.vertices_from_f(f)
        aretes += [(a, b), (b, c), (c, a)]
    return len(aretes) == len(set(aretes)) and all((b, a) in set(aretes) for a, b in aretes)


def octaedre_subdivise():
    """Octaèdre dont chaque face est coupée en 4, sommets projetés sur la sphère (18 sommets)."""
    octa = octaedre()
    sommets = [p.copy() for p in octa.vertices]
    milieux = {}

    def milieu(a, b):
        cle = (min(a, b), max(a, b))
        if cle not in milieux:
            p = sommets[a] + sommets[b]
            sommets.append(p / np.linalg.norm(p))
            milieux[cle] = len(sommets) - 1
        return milieux[cle]

    faces = []
    for f in octa.visible_faces():
        a, b, c = octa.vertices_from_f(f)
        ab, bc, ca = milieu(a, b), milieu(b, c), milieu(c, a)
        faces += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    mesh = Mesh(sommets, faces)
    mesh.compute_non_manifold()
    return mesh


# cas limites et erreurs

def test_batch_sans_split(flux_octa):
    mesh = Mesh(flux_octa["m0"]["vertices"], flux_octa["m0"]["faces"])
    avant = faces_de(mesh)
    splits = appliquer_batch(mesh, {"marks": [False] * 5, "splits": []})
    assert splits == []
    assert mesh.n_visible_v == 5
    assert faces_de(mesh) == avant


def test_plus_de_marques_que_de_splits(flux_octa):
    batch = flux_octa["batches"][0]
    batch["marks"][0] = True                     # 2 marques True pour 1 split
    with pytest.raises(ValueError):
        lire_splits(Mesh(flux_octa["m0"]["vertices"], flux_octa["m0"]["faces"]), batch)


def test_arc_vers_un_non_voisin(flux_octa):
    mesh = Mesh(flux_octa["m0"]["vertices"], flux_octa["m0"]["faces"])
    with pytest.raises(ValueError):
        arc_autour(mesh, 3, 2, 99)


def test_flux_non_modifie(flux_octa):
    m0_avant = flux_octa["m0"]["vertices"].copy()
    decoder_stream(flux_octa)
    assert np.array_equal(flux_octa["m0"]["vertices"], m0_avant)


# aller-retour encodeur -> décodeur

@pytest.mark.parametrize("fabrique, cible, strategie", [
    (octaedre, 4, "qem"),
    (octaedre_subdivise, 6, "qem"),
    (octaedre_subdivise, 6, "random"),     # celui-ci passe par le renommage
])
def test_aller_retour(fabrique, cible, strategie):
    original = fabrique()
    stream, _ = encode(original, target_vertices=cible, strategy=strategie)
    assert len(stream["batches"]) >= 1

    mesh = decoder_stream(stream)
    assert mesh.n_visible_v == original.n_visible_v
    assert mesh.n_visible_f == original.n_visible_f
    assert faces_en_positions(mesh) == faces_en_positions(original)


def test_maillage_valide_apres_chaque_batch():
    stream, _ = encode(octaedre_subdivise(), target_vertices=6, strategy="random")
    mesh = Mesh(stream["m0"]["vertices"], stream["m0"]["faces"])
    for batch in stream["batches"]:
        n_avant = mesh.n_visible_v
        splits = appliquer_batch(mesh, batch)
        # 1 sommet et 2 faces par split
        assert mesh.n_visible_v == n_avant + len(splits)
        assert mesh.n_visible_f == 2 * mesh.n_visible_v - 4      # Euler sur une sphère
        assert est_ferme_et_oriente(mesh)
