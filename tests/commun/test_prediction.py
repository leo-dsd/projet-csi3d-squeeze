import numpy as np

from prediction import predict

POSITIONS = [np.array(p, dtype=float) for p in [(0, 0, 0), (2, 0, 0), (0, 4, 0), (9, 9, 9)]]


def test_moyenne_des_voisins():
    # (0+2+0)/3, (0+0+4)/3, 0
    assert np.allclose(predict(POSITIONS, [0, 1, 2]), (2 / 3, 4 / 3, 0))


def test_seuls_les_voisins_donnes_comptent():
    # le sommet 3 n'est pas dans la liste : il n'intervient pas
    assert np.allclose(predict(POSITIONS, [1, 2]), (1, 2, 0))
