import os
import sys
import warnings

import numpy as np

# util pour pouvoir importer obja
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "obja"))
import obja

class Mesh(obja.Model):
    def __init__(self, vertices=None, faces=None):
        super().__init__()
        if vertices is not None:
            array = np.asarray(vertices, dtype=np.float64).reshape(-1, 3)
            self.vertices = [p.copy() for p in array]
        if faces is not None:
            self.faces = [obja.Face(int(f[0]), int(f[1]), int(f[2])) for f in faces]
        self.build_adjacency()

    # construction
    def build_adjacency(self):
        # liste indiquant quels sommets sont encore vivants (True) ou supprimés (False)
        self.visible_v: list[bool] = [True] * len(self.vertices)
        # liste des faces vivantes contenant chaque sommet (ensemble d'indices de faces)
        self.faces_with_v: list[set[int]] = [set() for _ in self.vertices]
        # liste indiquant quels sommets sont non-manifolds (True) ou non
        self.non_manifold: list[bool] = [False] * len(self.vertices)
        for idx, face in enumerate(self.faces):
            # si une face utilise deux fois le meme sommet on la suppr
            if face.a == face.b or face.b == face.c or face.a == face.c:
                face.visible = False
                continue
            for v in (face.a, face.b, face.c):
                self.faces_with_v[v].add(idx)

    def copy(self):
        m = Mesh.__new__(Mesh)
        m.line = self.line
        m.vertices = [p.copy() for p in self.vertices]
        m.faces = [f.clone() for f in self.faces]
        m.visible_v = list(self.visible_v)
        m.faces_with_v = [set(s) for s in self.faces_with_v]
        m.non_manifold = list(self.non_manifold)
        return m

    # primitives
    def vertices_from_f(self, f):
        face = self.faces[f]
        return face.a, face.b, face.c

    def add_vertex(self, position, non_manifold=False):
        self.vertices.append(np.asarray(position, dtype=np.float64).reshape(3).copy())
        self.visible_v.append(True)
        self.faces_with_v.append(set())
        self.non_manifold.append(non_manifold)
        return len(self.vertices) - 1

    def add_face(self, a, b, c):
        idx = len(self.faces)
        self.faces.append(obja.Face(a, b, c))
        for v in (a, b, c):
            self.faces_with_v[v].add(idx)
        return idx

    def remove_face(self, f):
        face = self.faces[f]
        if not face.visible:
            return
        face.visible = False
        for v in (face.a, face.b, face.c):
            self.faces_with_v[v].discard(f)

    def remove_vertex(self, v):
        if not self.faces_with_v[v]:
            self.visible_v[v] = False

    def replace_vertex_in_face(self, f, old, new):
        face = self.faces[f]
        if face.a == old:
            face.a = new
        if face.b == old:
            face.b = new
        if face.c == old:
            face.c = new
        self.faces_with_v[old].discard(f)
        self.faces_with_v[new].add(f)

    # requêtes
    @property
    def n_visible_v(self):
        return sum(self.visible_v)

    @property
    def n_visible_f(self):
        return sum(1 for face in self.faces if face.visible)

    def visible_vertices(self):
        return [v for v, a in enumerate(self.visible_v) if a]

    def visible_faces(self):
        return [f for f, face in enumerate(self.faces) if face.visible]

    def neighbors(self, v):
        nb = set()
        # boucle sur toutes les faces vivantes contenant v
        for f in self.faces_with_v[v]:
            # on ajoute les trois sommets de la face f à l'ensemble des voisins de v
            nb.update(self.vertices_from_f(f))
        # on enlève v lui-même de la liste des voisins
        nb.discard(v)
        return nb

    def degree(self, v):
        return len(self.neighbors(v))

    def next(self, v, w):
        for f in self.faces_with_v[v]:
            a, b, c = self.vertices_from_f(f)
            if a == v and b == w:
                return c
            if b == v and c == w:
                return a
            if c == v and a == w:
                return b
        return None

    def face_with(self, v, w, x):
        for f in self.faces_with_v[v]:
            if self.vertices_from_f(f) in ((v, w, x), (w, x, v), (x, v, w)):
                return f
        return None

    def faces_of_edge(self, v1, v2):
        return [f for f in self.faces_with_v[v1] if v2 in self.vertices_from_f(f)]

    def opposite_vertices(self, v1, v2):
        out = []
        for f in self.faces_of_edge(v1, v2):
            # une face triangulaire n'a qu'un sommet qui n'est ni v1 ni v2
            for x in self.vertices_from_f(f):
                if x != v1 and x != v2:
                    out.append(x)
                    break
        return out

    def fan(self, v):
        nbrs = self.neighbors(v)
        if not nbrs:
            return False, []
        # permettra de déterminer l'ordre des sommets, sous la forme a:b, b:c, c:d, ...
        nxt, prv = {}, {}
        for f in self.faces_with_v[v]:
            # on récupère les trois sommets de la face f, et on les réordonne pour que v soit le premier
            a, b, c = self.vertices_from_f(f)
            if b == v:
                a, b, c = b, c, a
            elif c == v:
                a, b, c = c, a, b
            # ordre cyclique (v, b, c)
            # vérifie si b ou c sont déjà dans l'ordre, ce qui indiquerait un éventail non-manifold
            # ici on vérifie que si on a une arête partagée par 3 faces, on considère les vertex de cette arrête comme "OTHER"
            if b in nxt or c in prv:
                return False, sorted(nbrs, key=self.position_key)
            nxt[b] = c
            prv[c] = b
        # parcourt les voisins et garde ceux qui n'ont pas de prédécesseur (début d'éventail)
        starts = [w for w in nbrs if w not in prv]
        # tout le monde a un prédécesseur : c'est un cycle fermé, on peut partir de n'importe quel sommet
        if len(starts) == 0:
            start = min(nbrs)
        else:
            return False, sorted(nbrs, key=self.position_key)
        # liste contenant le premier voisin
        ordered = [start]
        # vertex courant
        cur = start
        # on parcourt les voisins dans l'ordre défini par nxt
        while cur in nxt:
            cur = nxt[cur]
            # si on revient au sommet de départ, on a fait le tour de l'éventail
            if cur == start:
                break
            # ordered contient la liste des voisins dans l'ordre cyclique
            ordered.append(cur)
        if len(ordered) != len(nbrs):
            return False, sorted(nbrs, key=self.position_key)
        return True, ordered

    def position_key(self, v):
        return tuple(float(x) for x in self.vertices[v])
 
    def compute_non_manifold(self):
        for v in self.visible_vertices():
            manifold, _ = self.fan(v)
            # non_manifold si pas config classique
            self.non_manifold[v] = not manifold

    # export
    def rebuild(self):
        # on ne garde que les indices des sommets vivants
        visible = self.visible_vertices()
        # on construit un dictionnaire qui mappe les anciens indices vers les nouveaux indices
        old_to_new = {v: i for i, v in enumerate(visible)}
        # on construit le tableau des positions des sommets vivants : X,Y,Z
        vertices = np.array([self.vertices[v] for v in visible], dtype=np.float64).reshape(-1, 3)
        # on prend les faces vivantes et on remplace les anciens indices par les nouveaux indices
        faces = [tuple(old_to_new[x] for x in self.vertices_from_f(f)) for f in self.visible_faces()]
        return vertices, faces
