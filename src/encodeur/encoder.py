import argparse
import os
import pathlib
import random
import sys
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))

from batch import connectivity_bits, write_batch
from collapse import select_and_apply_batch
from mesh import Mesh
from objio import load_obj, write_obj
from quadrics import compute_quadrics
from tree import build_tree


def encode(source, target_vertices=None, target_ratio=0.05, strategy="qem", seed=0,
           max_batches=None, min_vertices=4):
    
    if isinstance(source, (str, pathlib.Path)):
        mesh = load_obj(source)
    else:
        mesh = source.copy()
    rng = random.Random(seed)
    Q = compute_quadrics(mesh) if strategy == "qem" else None

    n_start = mesh.n_visible_v
    if target_vertices is None:
        target_vertices = max(int(round(n_start * target_ratio)), min_vertices)

    batches: list[dict] = []
    batch_stats: list[dict] = []
    while mesh.n_visible_v > target_vertices:
        if max_batches is not None and len(batches) >= max_batches:
            break
        n_before = mesh.n_visible_v
        collapses = select_and_apply_batch(
            mesh, Q, max_collapses=n_before - target_vertices, strategy=strategy, rng=rng
        )
        if not collapses:
            break
        order, parent = build_tree(mesh)
        batch = write_batch(mesh, collapses, order, parent)
        n_after = mesh.n_visible_v
        batches.append(batch)
        batch_stats.append({
            "vertices_coarse": n_after,
            "vertices_fine": n_before,
            "faces_fine": mesh.n_visible_f + 2 * len(collapses),
            "splits": len(collapses),
            "tau_v": len(collapses) / n_after,
            "connectivity_bits": connectivity_bits(mesh, collapses, len(batch["marks"])),
        })

    batches.reverse()
    batch_stats.reverse()
    vertices, faces = mesh.rebuild()
    stream = {"m0": {"vertices": vertices, "faces": faces}, "batches": batches}
    stats = {
        "m0": {"vertices": len(vertices), "faces": len(faces)},
        "batches": batch_stats,
        "input_vertices": n_start,
    }
    return stream, stats


def main(argv=None):
    p = argparse.ArgumentParser(description="Encodeur progressif Squeeze / CPM")
    p.add_argument("input", help="fichier .obj")
    p.add_argument("--target-vertices", type=int, default=None)
    p.add_argument("--target-ratio", type=float, default=0.05)
    p.add_argument("--strategy", choices=["qem", "random"], default="qem")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-batches", type=int, default=None)
    p.add_argument("--export-m0", type=pathlib.Path, default=None, help="écrit M0 en .obj")
    args = p.parse_args(argv)

    t0 = time.perf_counter()
    stream, stats = encode(
        args.input, target_vertices=args.target_vertices, target_ratio=args.target_ratio,
        strategy=args.strategy, seed=args.seed, max_batches=args.max_batches,
    )
    dt = time.perf_counter() - t0

    n_faces_full = max((b["faces_fine"] for b in stats["batches"]), default=stats["m0"]["faces"])
    print(f"{args.input} : {stats['input_vertices']} sommets -> M0 {stats['m0']['vertices']} "
          f"sommets, {len(stream['batches'])} batchs, {dt:.1f} s")
    print(f"{'batch':>6} {'|Vi|':>7} {'|Vi+1|':>7} {'splits':>7} {'tau_v':>6} {'C bits':>8} {'C/tri':>6}")
    total = 0
    for i, b in enumerate(stats["batches"]):
        total += b["connectivity_bits"]
        print(f"{i:>6} {b['vertices_coarse']:>7} {b['vertices_fine']:>7} {b['splits']:>7} "
              f"{b['tau_v']:>6.2f} {b['connectivity_bits']:>8} "
              f"{b['connectivity_bits'] / b['faces_fine']:>6.2f}")
    print(f"connectivité totale des batchs : {total} bits = {total / n_faces_full:.2f} bits/triangle "
          f"de Mn ({n_faces_full} faces)")

    if args.export_m0 is not None:
        write_obj(Mesh(stream["m0"]["vertices"], stream["m0"]["faces"]), args.export_m0)
        print(f"M0 écrit dans {args.export_m0}")


if __name__ == "__main__":
    main()
