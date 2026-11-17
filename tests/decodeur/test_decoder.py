"""Décodage du flux écrit à la main dans exemples.flux_octaedre (voir son docstring)."""

import numpy as np
import pytest

from decoder import (appliquer_batch, arc_autour, commencer_par, decoder_stream,
                     lire_splits)
from exemples import FACES_OCTAEDRE_DECODE, faces_normalisees
from mesh import Mesh


def m0_de(flux):
    return Mesh(flux["m0"]["vertices"], flux["m0"]["faces"])


def test_commencer_par():
    assert commencer_par([7, 8, 9], 8) == [8, 9, 7]


def test_lecture_des_splits(flux_octa):
    splits = lire_splits(m0_de(flux_octa), flux_octa["batches"][0])
    assert len(splits) == 1
    s = splits[0]
    assert (s.sommet, s.u1, s.u2, s.direction, s.degre) == (3, 1, 2, False, 4)
    assert np.allclose(s.erreur, (1, 0, 0))


def test_mauvais_nombre_de_marques(flux_octa):
    batch = flux_octa["batches"][0]
    batch["marks"] = batch["marks"][:-1]          # une marque en moins
    with pytest.raises(ValueError):
        lire_splits(m0_de(flux_octa), batch)


def test_arc(flux_octa):
    # autour du haut (3), de 2 à 1 en suivant next : 2 -> 4 (bas) -> 1
    assert arc_autour(m0_de(flux_octa), 3, 2, 1) == [2, 4, 1]


def test_un_batch(flux_octa):
    mesh = m0_de(flux_octa)
    splits = appliquer_batch(mesh, flux_octa["batches"][0])
    assert splits[0].nouveau == 5
    # connectivité : on retrouve les 8 faces de l'octaèdre, avec le bon enroulement
    faces = [mesh.vertices_from_f(f) for f in mesh.visible_faces()]
    assert faces_normalisees(faces) == faces_normalisees(FACES_OCTAEDRE_DECODE)
    # géométrie : le nouveau sommet est à (1, 0, 0)
    assert np.allclose(mesh.vertices[5], (1, 0, 0))


def test_decoder_stream(flux_octa):
    mesh = decoder_stream(flux_octa)
    assert mesh.n_visible_v == 6
    assert mesh.n_visible_f == 8
