import math

import numpy as np

FLOAT_BITS = 32
# largeur des erreurs d'un batch, sur 6 bits donc de 0 à 63
WIDTH_BITS = 6


class Quantizer:
    """Grille régulière, pas = (plus grand côté de la boîte englobante de M0) / (2^q - 1)."""

    def __init__(self, vertices, bits):
        points = np.asarray(vertices, dtype=np.float64).reshape(-1, 3)
        self.bits = bits
        self.origin = points.min(axis=0)
        extent = float((points.max(axis=0) - self.origin).max())
        # si tous les points sont confondus on met un pas de 1 pour éviter de diviser par 0
        if extent > 0:
            self.step = extent / (2 ** bits - 1)
        else:
            self.step = 1.0

    def snap(self, position):
        """Point de la grille le plus proche (c'est cette position qu'on écrit dans l'OBJA)."""
        k = np.round((np.asarray(position) - self.origin) / self.step)
        return self.origin + k * self.step

    def error_to_int(self, error):
        # erreur exprimée en nombre de pas de la grille
        return np.round(np.asarray(error) / self.step).astype(np.int64)


def index_bits(n):
    """Nombre de bits pour écrire un indice parmi n (au moins 1)."""
    return math.ceil(math.log2(max(n, 2)))


def m0_bits(n_vertices, n_faces, quantizer=None):
    """3 coordonnées par sommet + 3 indices par face (codage naïf)."""
    coord_bits = quantizer.bits if quantizer else FLOAT_BITS
    return 3 * coord_bits * n_vertices + 3 * index_bits(n_vertices) * n_faces


def connectivity_bits(n_marks, degrees):
    """Même formule que dans l'encodeur (src/encodeur/batch.py, connectivity_bits)."""
    bits = n_marks
    for d in degrees:
        # 1 bit de direction + le choix de 2 cut-edges parmi d
        bits += 1 + math.ceil(math.log2(d * (d - 1) // 2))
    return bits


def geometry_bits(errors, quantizer=None):
    """3 composantes d'erreur par split : 64 bits chacune sans quantification, sinon juste
    assez de bits pour la plus grande erreur du batch (largeur envoyée sur WIDTH_BITS bits)."""
    if not errors:
        return 0
    if quantizer is None:
        return 3 * FLOAT_BITS * len(errors)
    # on cherche la plus grande erreur (en valeur absolue) du batch pour fixer la largeur
    largest = max(int(np.abs(quantizer.error_to_int(e)).max()) for e in errors)
    # + 1 bit de signe
    width = largest.bit_length() + 1
    return WIDTH_BITS + 3 * width * len(errors)
