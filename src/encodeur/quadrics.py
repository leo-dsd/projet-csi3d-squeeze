import numpy as np


def compute_quadrics(mesh):
    n = len(mesh.vertices)
    # chaque sommet a sa matrice 4x4, initialisée à zéro
    Q = np.zeros((n, 4, 4), dtype=np.float64)
    # on récupère les sommets des faces visibles
    faces = np.array([mesh.vertices_from_f(f) for f in mesh.visible_faces()], dtype=np.int64).reshape(-1, 3)
    if len(faces) == 0:
        return Q
    V = np.asarray(mesh.vertices, dtype=np.float64).reshape(-1, 3)   # liste obja -> tableau (n, 3)
    # coordonnées des premiers sommets de toutes les faces
    p0 = V[faces[:, 0]]
    # coordonnées des deuxièmes sommets de toutes les faces
    p1 = V[faces[:, 1]]
    # coordonnées des troisièmes sommets de toutes les faces
    p2 = V[faces[:, 2]]
    # vecteur normal à chaque face
    normals = np.cross(p1 - p0, p2 - p0)
    # norme de chaque vecteur normal
    norms = np.linalg.norm(normals, axis=1)
    ok = norms > 0
    # on normalise les vecteurs normaux pour obtenir des normales unitaires
    normals[ok] /= norms[ok, None]
    normals[~ok] = 0.0
    # calcul du coefficient d des plans ax + by + cz + d = 0
    # produit scalaire entre la normale et un point de la face
    d = -np.sum(normals * p0, axis=1)
    # on ajoute la colonne d aux normales pour obtenir les équations des plans
    planes = np.column_stack([normals, d])               # (M, 4)
    # produit tensoriel des équations des plans pour obtenir les quadriques
    K = planes[:, :, None] * planes[:, None, :]          # (M, 4, 4)
    """équivalent plus optimisé de :
        for i in range(len(faces)):
        Q[faces[i]] += K[i]
    """
    # on somme les quadriques de toutes les faces associées à chaque sommet
    for k in range(3):
        np.add.at(Q, faces[:, k], K)
    return Q


def collapse_cost(Q, mesh, v_keep, v_del):
    p = np.append(mesh.vertices[v_keep], 1.0)
    return float(p @ (Q[v_keep] + Q[v_del]) @ p)
