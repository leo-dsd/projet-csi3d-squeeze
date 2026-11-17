"""Écriture de l'OBJA pour le flux écrit à la main (exemples.flux_octaedre).

Faces de M0, numérotées à partir de 1 dans l'OBJA :
    1: (3,1,0)  2: (3,0,2)  3: (4,1,3)  4: (4,0,1)  5: (4,2,0)  6: (4,3,2)
Le split du haut (3) déplace vers le nouveau sommet (6e sommet de l'OBJA) :
    - la face (3, 2, 4), c'est-à-dire la face 6 (4,3,2), où 3 est le 2e sommet  -> efv 6 2 6
    - la face (3, 4, 1), c'est-à-dire la face 3 (4,1,3), où 3 est le 3e sommet  -> efv 3 3 6
puis crée (3, 2, 5) et (3, 5, 1), soit en indices OBJA « f 4 3 6 » et « f 4 6 2 ».
"""

import io

import obja
from decoder import decoder_stream
from exemples import FACES_OCTAEDRE_DECODE, faces_normalisees
from mesh import Mesh
from obja_writer import ObjaWriter


def ecrire(flux):
    texte = io.StringIO()            # « fichier » en mémoire
    writer = ObjaWriter(texte)
    decoder_stream(flux, writer)
    return texte.getvalue().splitlines(), writer


def test_m0_seul():
    texte = io.StringIO()
    writer = ObjaWriter(texte)
    writer.write_m0(Mesh([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)]))
    # 3 sommets x 3 x 32 bits + 1 face x 3 indices x 2 bits = 294 bits -> 37 octets
    assert texte.getvalue().splitlines() == [
        "v 0.0 0.0 0.0", "v 1.0 0.0 0.0", "v 0.0 1.0 0.0", "f 1 2 3", "s 37",
    ]


def test_lignes_du_batch(flux_octa):
    lignes, _ = ecrire(flux_octa)
    # tout ce qui suit M0 (5 v, 6 f, 1 s)
    batch = lignes[12:]
    assert batch[0] == "v 1.0 0.0 0.0"
    assert batch[1:5] == ["efv 6 2 6", "efv 3 3 6", "f 4 3 6", "f 4 6 2"]
    assert batch[5].startswith("s ")


def test_relecture_par_obja(flux_octa, tmp_path):
    lignes, writer = ecrire(flux_octa)
    chemin = tmp_path / "octa.obja"
    chemin.write_text("\n".join(lignes) + "\n")
    # le parseur fourni par les enseignants doit relire l'octaèdre complet
    model = obja.parse_file(str(chemin))
    assert len(model.vertices) == 6
    faces = [(f.a, f.b, f.c) for f in model.faces]
    assert faces_normalisees(faces) == faces_normalisees(FACES_OCTAEDRE_DECODE)
    # une ligne de statistiques par niveau : M0 puis M1
    assert len(writer.levels) == 2
