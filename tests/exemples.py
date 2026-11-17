"""Petits exemples faisables à la main, partagés par les tests."""

import os

import numpy as np

from mesh import Mesh

# dossier des modèles fournis (bunny.obj, suzanne.obj)
EXEMPLES_OBJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "obja", "example")


def octaedre():
    """Octaèdre, faces orientées vers l'extérieur.

        4 = haut (0, 0, 1), 5 = bas (0, 0, -1)
        équateur : 0 = (1, 0, 0), 2 = (0, 1, 0), 1 = (-1, 0, 0), 3 = (0, -1, 0)

    Chaque sommet a 4 voisins : tous les autres sauf son opposé (0-1, 2-3, 4-5).
    """
    vertices = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    faces = [(4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0),
             (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3)]
    mesh = Mesh(vertices, faces)
    mesh.compute_non_manifold()
    return mesh


def eventail_ouvert():
    """Carré plat découpé en 4 triangles autour du centre 4 (pyramide sans base, aplatie).

        1
      2 4 0
        3

    Les sommets 0 à 3 sont sur le bord ; seul le centre 4 a un éventail fermé.
    """
    vertices = [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 0)]
    faces = [(4, 0, 1), (4, 1, 2), (4, 2, 3), (4, 3, 0)]
    mesh = Mesh(vertices, faces)
    mesh.compute_non_manifold()
    return mesh


def flux_octaedre():
    """Flux écrit à la main : M0 = octaèdre auquel il manque le sommet (1, 0, 0), et un batch
    qui le remet. C'est le batch calculé dans tests/encodeur/test_batch.py, renuméroté :

        sommets de M0 : 0 = (-1, 0, 0), 1 = (0, 1, 0), 2 = (0, -1, 0), 3 = haut, 4 = bas
        parcours de M0 : [0, 2, 4, 1, 3] ; seul 3 (le haut) est splitté
        numérotation des arêtes de 3 (parent 1) : [1, 0, 2, 4]
        cut-edges (0, 2) -> u1 = 1, u2 = 2 ; direction False : arc de 2 à 1 = [2, 4, 1],
        le bas (4) part vers le nouveau sommet 5
        position de 5 = moyenne de 3, 2, 4, 1 (= origine) + erreur (1, 0, 0)
    """
    m0 = {
        "vertices": np.array([(-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)], dtype=float),
        "faces": [(3, 1, 0), (3, 0, 2), (4, 1, 3), (4, 0, 1), (4, 2, 0), (4, 3, 2)],
    }
    batch = {
        "marks": [False, False, False, False, True],
        "splits": [{"cut_edges": (0, 2), "direction": False, "error": (1.0, 0.0, 0.0)}],
    }
    return {"m0": m0, "batches": [batch]}


# faces de l'octaèdre décodé depuis flux_octaedre (le sommet (1, 0, 0) porte le numéro 5)
FACES_OCTAEDRE_DECODE = [(3, 5, 1), (3, 1, 0), (3, 0, 2), (3, 2, 5),
                         (4, 1, 5), (4, 0, 1), (4, 2, 0), (4, 5, 2)]


def faces_normalisees(faces):
    """Chaque face est tournée pour commencer par son plus petit indice, puis on trie la liste.
    Deux listes de faces décrivent le même maillage (enroulement compris) si et seulement si
    elles donnent le même résultat."""
    out = []
    for a, b, c in faces:
        if b < a and b < c:
            a, b, c = b, c, a
        elif c < a and c < b:
            a, b, c = c, a, b
        out.append((a, b, c))
    return sorted(out)
