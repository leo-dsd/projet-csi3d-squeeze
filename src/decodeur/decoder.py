import argparse
import os
import sys

import numpy as np

# pour importer le code commun avec l'encodeur (même arbre, même numérotation, même prédiction)
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ICI, "..", "commun"))

from mesh import Mesh
from prediction import predict
from tree import build_tree, neighbor_order


class Split:
    """Un vertex split du batch + ce qu'on récupère en l'appliquant (pour l'OBJA)."""

    def __init__(self, sommet, u1, u2, direction, erreur, degre):
        # infos lues dans le batch
        self.sommet = sommet          # le split-vertex v (sommet de Mi)
        self.u1 = u1                  # les deux cut-edges sont (v, u1) et (v, u2)
        self.u2 = u2
        self.direction = direction    # True : l'arc va de u1 à u2, False : de u2 à u1
        self.erreur = erreur          # erreur de prédiction (v_del - v_est)
        self.degre = degre            # degré de v dans Mi, sert pour le calcul du poids
        # rempli pendant l'application du split
        self.nouveau = None           # indice du sommet créé
        self.faces_deplacees = []     # (face, coin 0/1/2) des faces qui passent de v au nouveau sommet
        self.faces_creees = []        # (face, (a, b, c)) des deux faces ajoutées


def commencer_par(liste, element):
    """Fait tourner une liste cyclique pour qu'elle commence par element : [a, b, c], b -> [b, c, a]."""
    i = liste.index(element)
    return liste[i:] + liste[:i]


# 1. lecture
def lire_splits(mesh, batch):
    """Repère tous les splits du batch dans Mi AVANT de modifier quoi que ce soit (§6 étape A),
    parce que les numéros d'arête sont donnés par rapport à Mi."""
    # on refait le même parcours en profondeur que l'encodeur
    ordre, parent = build_tree(mesh)
    # une marque par sommet parcouru : True si c'est un split-vertex
    marques = batch["marks"]
    if len(marques) != len(ordre):
        raise ValueError(f"le batch a {len(marques)} marques pour {len(ordre)} sommets parcourus")
    if sum(marques) != len(batch["splits"]):
        raise ValueError("nombre de marques True différent du nombre de splits")

    splits = []
    # indice du prochain split à lire dans batch["splits"]
    k = 0
    for v, marque in zip(ordre, marques):
        if not marque:
            continue
        donnees = batch["splits"][k]
        k += 1
        # numéro d'arête -> voisin, même numérotation que l'encodeur grâce au parent
        numerotation = neighbor_order(mesh, v, parent[v])
        c1, c2 = donnees["cut_edges"]
        splits.append(Split(
            sommet=v,
            u1=numerotation[c1],
            u2=numerotation[c2],
            direction=donnees["direction"],
            erreur=np.array(donnees["error"], dtype=np.float64),
            degre=len(numerotation),
        ))
    return splits


# 2. connectivité
def arc_autour(mesh, v, depart, arrivee):
    """Voisins de v entre depart et arrivee (inclus), en tournant avec next (§3)."""
    arc = [depart]
    while arc[-1] != arrivee:
        suivant = mesh.next(v, arc[-1])
        # si on a fait le tour sans tomber sur arrivee c'est qu'il n'est pas voisin de v
        if suivant is None or suivant == depart:
            raise ValueError(f"split {v} : {arrivee} n'est pas un voisin de {v}")
        arc.append(suivant)
    return arc


def appliquer_connectivite(mesh, split, splits_suivants):
    """Applique un split sur le mesh (§6 étape B)."""
    v = split.sommet

    # on relit l'arc maintenant, sur le mesh déjà modifié par les splits d'avant
    # le bit de direction dit dans quel sens on tourne
    if split.direction:
        arc = arc_autour(mesh, v, split.u1, split.u2)
    else:
        arc = arc_autour(mesh, v, split.u2, split.u1)

    # on crée le nouveau sommet, sa vraie position est calculée plus tard (étape 3)
    nouveau = mesh.add_vertex(np.zeros(3))
    split.nouveau = nouveau

    # les faces (v, a, b) de l'arc passent au nouveau sommet, sans changer l'enroulement
    # zip(arc, arc[1:]) donne les paires de voisins consécutifs de l'arc
    for a, b in zip(arc, arc[1:]):
        f = mesh.face_with(v, a, b)
        # on garde la position de v dans la face pour écrire la ligne efv
        coin = mesh.vertices_from_f(f).index(v)
        mesh.replace_vertex_in_face(f, v, nouveau)
        split.faces_deplacees.append((f, coin))

    # on ajoute les deux nouvelles faces, de chaque côté de l'arête (v, nouveau)
    for coins in ((v, arc[0], nouveau), (v, nouveau, arc[-1])):
        f = mesh.add_face(*coins)
        split.faces_creees.append((f, coins))

    # renommage : si un split suivant a son sommet à l'intérieur de l'arc, son cut-edge vers v
    # est devenu une arête vers le nouveau sommet, il faut le mettre à jour
    interieur = arc[1:-1]
    for q in splits_suivants:
        if q.sommet in interieur:
            if q.u1 == v:
                q.u1 = nouveau
            if q.u2 == v:
                q.u2 = nouveau


# 3. géométrie
def calculer_position(mesh, split, anciens):
    """Position du nouveau sommet = moyenne de ses anciens voisins + erreur (§7)."""
    _, voisins = mesh.fan(split.nouveau)
    # le contrat impose de commencer par le split-vertex
    voisins = commencer_par(voisins, split.sommet)
    # on enlève les sommets créés pendant ce batch, l'encodeur ne les connaît pas dans Mi
    voisins_anciens = [w for w in voisins if w in anciens]
    mesh.vertices[split.nouveau] = predict(mesh.vertices, voisins_anciens) + split.erreur


# un batch et le stream
# pour chaque batch : lecture des splits, puis connectivité, puis géométrie
def appliquer_batch(mesh, batch):
    """Transforme Mi en M(i+1) (directement dans mesh) et renvoie les splits appliqués, dans l'ordre."""
    # sommets de Mi, avant d'appliquer le batch
    anciens = set(mesh.visible_vertices())
    splits = lire_splits(mesh, batch)
    # chaque split a besoin de connaître ceux qui viennent après lui (pour le renommage)
    for k, split in enumerate(splits):
        appliquer_connectivite(mesh, split, splits[k + 1:])
    # les positions à la fin, une fois que toute la connectivité du batch est en place
    for split in splits:
        calculer_position(mesh, split, anciens)
    return splits


def decoder_stream(stream, sortie_obja=None):
    """Décode le stream et renvoie le mesh final. Si on donne sortie_obja (un ObjaWriter),
    l'OBJA est écrit au fur et à mesure : M0 puis chaque batch."""
    mesh = Mesh(stream["m0"]["vertices"], stream["m0"]["faces"])
    if sortie_obja is not None:
        sortie_obja.write_m0(mesh)
    for batch in stream["batches"]:
        splits = appliquer_batch(mesh, batch)
        if sortie_obja is not None:
            sortie_obja.write_batch(mesh, batch, splits)
    return mesh


# main
def afficher_poids(niveaux):
    # tableau récap par niveau, les >n servent juste à aligner les colonnes
    print(f"{'niveau':>6} {'|V|':>7} {'|F|':>7} {'conn. bits':>11} {'géom. bits':>11} "
          f"{'cumul Ko':>9} {'bits/sommet':>12}")
    for n in niveaux:
        print(f"{n['level']:>6} {n['vertices']:>7} {n['faces']:>7} "
              f"{n['connectivity_bits']:>11} {n['geometry_bits']:>11} "
              f"{n['total_bits'] / 8 / 1024:>9.1f} {n['total_bits'] / n['vertices']:>12.1f}")


# python src/decodeur/decoder.py obja/example/bunny.obj -o bunny.obja [--quantization 12]
# le stream n'est pas enregistré dans un fichier, donc on lance l'encodeur puis on décode
def main(argv=None):
    p = argparse.ArgumentParser(description="Encode un .obj puis le décode en .obja (Squeeze / CPM)")
    p.add_argument("input", help="fichier .obj")
    p.add_argument("-o", "--output", default=None, help="fichier .obja (défaut : <nom>.obja)")
    p.add_argument("--quantization", type=int, default=None, metavar="Q",
                   help="quantifier sur Q bits par coordonnée (défaut : pas de quantification)")
    p.add_argument("--strategy", choices=["qem", "random"], default="qem")
    p.add_argument("--target-ratio", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)

    # on importe l'encodeur seulement ici, il n'y a que le main qui en a besoin
    sys.path.append(os.path.join(ICI, "..", "encodeur"))
    from encoder import encode
    from obja_writer import ObjaWriter

    # par défaut on prend le nom du .obj avec l'extension .obja
    sortie = args.output or os.path.splitext(os.path.basename(args.input))[0] + ".obja"
    # on encode puis on décode
    stream, _ = encode(args.input, target_ratio=args.target_ratio,
                       strategy=args.strategy, seed=args.seed)
    with open(sortie, "w") as fichier:
        sortie_obja = ObjaWriter(fichier, quantization=args.quantization)
        decoder_stream(stream, sortie_obja)

    q = f"{args.quantization} bits" if args.quantization else "aucune (float64)"
    print(f"{args.input} -> {sortie}  (stratégie {args.strategy}, quantification : {q})")
    afficher_poids(sortie_obja.levels)


if __name__ == "__main__":
    main()
