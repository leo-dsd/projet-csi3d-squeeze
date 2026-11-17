from encoder import encode


def test_flux_octaedre(octa):
    stream, stats = encode(octa, target_vertices=4)
    m0 = stream["m0"]
    batches = stream["batches"]

    assert len(batches) >= 1
    assert len(m0["vertices"]) <= 6
    # l'original n'est pas modifié (encode travaille sur une copie)
    assert octa.n_visible_v == 6

    # en remontant les batchs, on retrouve les 6 sommets de départ
    total_splits = sum(len(b["splits"]) for b in batches)
    assert len(m0["vertices"]) + total_splits == 6

    nb_sommets = len(m0["vertices"])
    for b in batches:
        # une marque par sommet du niveau courant, un split par marque True
        assert len(b["marks"]) == nb_sommets
        assert sum(b["marks"]) == len(b["splits"])
        nb_sommets += len(b["splits"])

    assert stats["m0"]["vertices"] == len(m0["vertices"])
    assert len(stats["batches"]) == len(batches)
