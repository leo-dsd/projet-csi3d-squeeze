import numpy as np

import batch as batch_encodeur
from collapse import Collapse, apply_collapse
from poids import Quantizer, connectivity_bits, geometry_bits, index_bits, m0_bits


def test_bits_d_un_indice():
    assert index_bits(4) == 2      # 0..3
    assert index_bits(6) == 3      # 0..5 : il faut 3 bits
    assert index_bits(1) == 1      # au moins 1 bit


def test_m0_sans_quantification():
    # 4 sommets x 3 coordonnées x 32 bits (float32) + 4 faces x 3 indices x 2 bits
    assert m0_bits(4, 4) == 384 + 24


def test_connectivite_identique_a_l_encodeur(octa):
    # même exemple que tests/encodeur/test_batch.py : 5 marques, un split de degré 4
    c = Collapse(4, 0, 2, 3, [4, 3, 5, 2], octa.vertices[0].copy())
    apply_collapse(octa, c)
    assert connectivity_bits(5, [octa.degree(4)]) == 5 + 1 + 3
    assert batch_encodeur.connectivity_bits(octa, [c], 5) == 5 + 1 + 3


def test_geometrie_sans_quantification():
    assert geometry_bits([]) == 0
    assert geometry_bits([(1.0, 0.0, 0.0)]) == 3 * 32     # 3 composantes en float32


def test_quantification():
    # boîte de côté 3, sur 2 bits : 4 valeurs 0, 1, 2, 3 -> pas de 1
    q = Quantizer([(0, 0, 0), (3, 0, 0)], bits=2)
    assert q.step == 1.0
    assert np.allclose(q.snap((1.4, 0.0, 2.6)), (1, 0, 3))
    # erreur (2.6, -0.4, 0) -> (3, 0, 0) : 3 s'écrit sur 2 bits, + 1 bit de signe = 3 bits
    # 6 bits de largeur en tête du batch + 3 composantes x 3 bits
    assert geometry_bits([(2.6, -0.4, 0.0)], q) == 6 + 3 * 3
