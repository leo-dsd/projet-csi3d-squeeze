from mesh import Mesh

def load_obj(path):
    mesh = Mesh()
    mesh.parse_file(str(path))
    mesh.build_adjacency()
    mesh.compute_non_manifold()
    return mesh

def write_obj(mesh, path):
    vertices, faces = mesh.rebuild()
    with open(path, "w") as out:
        for v in vertices:
            out.write(f"v {v[0]} {v[1]} {v[2]}\n")
        for a, b, c in faces:
            out.write(f"f {a + 1} {b + 1} {c + 1}\n")
