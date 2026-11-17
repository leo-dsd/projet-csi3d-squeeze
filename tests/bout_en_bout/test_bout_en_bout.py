"""Chaîne complète : fichier .obj -> encodeur -> flux -> décodeur -> fichier .obja.

On relit le .obja avec le parseur fourni (obja.parse_file) et on vérifie qu'on retrouve
exactement le maillage de départ. Les indices des sommets changent (M0 est renuméroté, les
sommets sont ajoutés dans l'ordre des splits) : on compare donc les faces par les positions
de leurs sommets, et pas par leurs indices.
"""

import os

import numpy as np
import pytest

import obja
from decoder import decoder_stream
from encoder import encode
from exemples import EXEMPLES_OBJ
from objio import load_obj, write_obj
from obja_writer import ObjaWriter


def faces_en_positions(vertices, faces):
    """Chaque face devient le triplet des positions de ses sommets (arrondies au milliardième,
    le décodage pouvant différer de quelques ulp), tourné pour commencer par la plus petite
    position. Le résultat ne dépend plus de la numérotation des sommets."""
    out = []
    for a, b, c in faces:
        p = [tuple(np.round(vertices[x], 9)) for x in (a, b, c)]
        rotations = [(p[0], p[1], p[2]), (p[1], p[2], p[0]), (p[2], p[0], p[1])]
        out.append(min(rotations))
    return sorted(out)


def obj_vers_obja(chemin_obj, chemin_obja, **options):
    """Encode le .obj, décode le flux en écrivant le .obja ; renvoie le flux."""
    stream, _ = encode(chemin_obj, **options)
    with open(chemin_obja, "w") as fichier:
        decoder_stream(stream, ObjaWriter(fichier))
    return stream


def verifier_aller_retour(chemin_obj, chemin_obja, **options):
    stream = obj_vers_obja(chemin_obj, chemin_obja, **options)

    depart = load_obj(chemin_obj)
    faces_depart = [depart.vertices_from_f(f) for f in depart.visible_faces()]
    arrivee = obja.parse_file(str(chemin_obja))
    faces_arrivee = [(f.a, f.b, f.c) for f in arrivee.faces if f.visible]

    assert len(arrivee.vertices) == depart.n_visible_v
    assert faces_en_positions(arrivee.vertices, faces_arrivee) == \
        faces_en_positions(depart.vertices, faces_depart)

    # une ligne « s » par niveau (M0 puis chaque batch), avec un poids croissant
    with open(chemin_obja) as fichier:
        tailles = [int(l.split()[1]) for l in fichier if l.startswith("s ")]
    assert len(tailles) == 1 + len(stream["batches"])
    assert tailles == sorted(tailles)
    return stream


def test_octaedre(octa, tmp_path):
    chemin_obj = tmp_path / "octa.obj"
    write_obj(octa, chemin_obj)
    stream = verifier_aller_retour(chemin_obj, tmp_path / "octa.obja", target_vertices=4)
    assert len(stream["batches"]) >= 1


@pytest.mark.parametrize("strategie", ["qem", "random"])
def test_bunny(tmp_path, strategie):
    stream = verifier_aller_retour(os.path.join(EXEMPLES_OBJ, "bunny.obj"),
                                   tmp_path / "bunny.obja", strategy=strategie)
    assert len(stream["batches"]) > 1


def test_suzanne(tmp_path):
    # suzanne a des bords et une arête non-manifold : ces sommets restent dans M0
    verifier_aller_retour(os.path.join(EXEMPLES_OBJ, "suzanne.obj"), tmp_path / "suzanne.obja")
