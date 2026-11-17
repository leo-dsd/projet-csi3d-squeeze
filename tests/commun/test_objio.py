import numpy as np

from objio import load_obj, write_obj


def test_ecriture_puis_lecture(octa, tmp_path):
    # tmp_path : dossier temporaire fourni par pytest
    chemin = tmp_path / "octa.obj"
    write_obj(octa, chemin)
    relu = load_obj(chemin)

    vertices, faces = relu.rebuild()
    vertices_attendus, faces_attendues = octa.rebuild()
    assert np.allclose(vertices, vertices_attendus)
    assert faces == faces_attendues
    # load_obj calcule aussi les sommets non-manifold : aucun sur l'octaèdre
    assert relu.non_manifold == [False] * 6
