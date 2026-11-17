import math

from mesh import Mesh       # importer mesh ajoute aussi le dossier obja/ au chemin
import obja
from poids import Quantizer, connectivity_bits, geometry_bits, m0_bits


class ObjaWriter:
    def __init__(self, out, quantization=None):
        """out : fichier texte ouvert en écriture, quantization : nombre de bits par coordonnée
        (None si pas de quantification)."""
        self.out = out
        # obja.Output s'occupe de la correspondance indices du Mesh -> indices dans l'OBJA
        self.output = obja.Output(out)
        self.quantization = quantization
        self.quantizer = None
        self.total_bits = 0
        # une entrée par niveau (M0, M1, ...) pour afficher les stats à la fin
        self.levels = []

    def position(self, p):
        # si on quantifie, on écrit le point de la grille le plus proche
        if self.quantizer:
            return self.quantizer.snap(p)
        return p

    def write_size(self, mesh, connectivity, geometry):
        self.total_bits += connectivity + geometry
        # le viewer attend une taille en octets
        print(f"s {math.ceil(self.total_bits / 8)}", file=self.out)
        self.levels.append({
            "level": len(self.levels),
            "vertices": mesh.n_visible_v,
            "faces": mesh.n_visible_f,
            "connectivity_bits": connectivity,
            "geometry_bits": geometry,
            "total_bits": self.total_bits,
        })

    def write_m0(self, mesh):
        # la grille de quantification est calée sur la boîte englobante de M0
        if self.quantization:
            self.quantizer = Quantizer(mesh.vertices, self.quantization)
        for v in mesh.visible_vertices():
            self.output.add_vertex(v, self.position(mesh.vertices[v]))
        for f in mesh.visible_faces():
            self.output.add_face(f, mesh.faces[f])
        bits = m0_bits(mesh.n_visible_v, mesh.n_visible_f, self.quantizer)
        # pour M0 on compte tout dans la géométrie
        self.write_size(mesh, 0, bits)

    # pas besoin de ligne ev : avec des half-edge collapses le sommet splitté ne bouge pas
    def write_batch(self, mesh, batch, splits):
        for s in splits:
            self.output.add_vertex(s.nouveau, self.position(mesh.vertices[s.nouveau]))
            # les indices OBJA commencent à 1
            new_index = self.output.vertex_mapping[s.nouveau] + 1
            for f, corner in s.faces_deplacees:
                face_index = self.output.face_mapping[f] + 1
                print(f"efv {face_index} {corner + 1} {new_index}", file=self.out)
            # on écrit les faces comme elles étaient à leur création : si un split suivant du
            # même batch les a modifiées depuis, c'est lui qui écrira sa propre ligne efv
            for f, (a, b, c) in s.faces_creees:
                self.output.add_face(f, obja.Face(a, b, c))
        connectivity = connectivity_bits(len(batch["marks"]), [s.degre for s in splits])
        geometry = geometry_bits([s.erreur for s in splits], self.quantizer)
        self.write_size(mesh, connectivity, geometry)
