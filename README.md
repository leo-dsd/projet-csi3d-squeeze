# Projet CSI3D — Squeeze / CPM

Transmission progressive de maillages par compression Squeeze / CPM (Pajarola & Rossignac).
L'encodeur transforme un `.obj` en un flux `M0 + batches`, le décodeur transforme ce flux en
fichier `.obja` lisible par le viewer.

## Organisation du dépôt

```
src/
  commun/     code partagé : doit donner exactement le même résultat des deux côtés
  encodeur/   code de l'encodeur uniquement
  decodeur/   code du décodeur uniquement
tests/        commun/, encodeur/, decodeur/, bout_en_bout/ (obj -> flux -> obja)
obja/         code fourni par les enseignants (parseur OBJ, écriture OBJA, viewer)
documents/    sujet, articles, charte IA, rapport de mi-projet,
              Comprendre_les_tests.pdf (explication de chaque test)
MANIFESTE_IA.md   déclaration de l'usage de l'IA dans le projet
```

| Fichier | Rôle |
|---|---|
| `src/commun/mesh.py` | classe `Mesh` (hérite de `obja.Model`) : adjacence, ordre cyclique, sommets non-manifold |
| `src/commun/tree.py` | arbre couvrant et numérotation des arêtes |
| `src/commun/prediction.py` | prédiction de la position d'un nouveau sommet |
| `src/commun/objio.py` | lecture d'un .obj, export d'un maillage en .obj |
| `src/encodeur/quadrics.py` | coût QEM d'un collapse |
| `src/encodeur/collapse.py` | choix d'un batch de collapses sous les contraintes CPM, et exécution |
| `src/encodeur/batch.py` | écriture d'un batch : marques, cut-edges, direction, erreur de prédiction |
| `src/encodeur/encoder.py` | boucle d'encodage `encode()` et programme principal |
| `src/decodeur/decoder.py` | décodage du flux `decoder_stream()` et programme principal (obj -> obja) |
| `src/decodeur/obja_writer.py` | écriture du fichier OBJA pendant le décodage |
| `src/decodeur/poids.py` | poids du modèle en bits, quantification |

Règle de partage : va dans `src/commun/` tout ce que l'encodeur et le décodeur doivent calculer
à l'identique (sinon le décodage échoue). Le reste va dans le dossier de l'équipe concernée.

## Installation

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt   # numpy, pytest
```

(Si `python3 -m venv` échoue faute d'`ensurepip` : `python3 -m venv --without-pip .venv`,
puis installer pip avec `get-pip.py` dans le venv.)

## Encodeur

```bash
.venv/bin/python src/encodeur/encoder.py obja/example/bunny.obj                 # stats par niveau
.venv/bin/python src/encodeur/encoder.py obja/example/bunny.obj --strategy random
.venv/bin/python src/encodeur/encoder.py obja/example/bunny.obj --export-m0 bunny_m0.obj
```

## Décodeur (chaîne complète obj -> obja)

```bash
.venv/bin/python src/decodeur/decoder.py obja/example/bunny.obj -o obja/example/bunny_squeeze.obja
.venv/bin/python src/decodeur/decoder.py obja/example/bunny.obj --quantization 12
.venv/bin/python src/decodeur/decoder.py obja/example/bunny.obj --strategy random --seed 1
```

Le programme encode le `.obj`, décode le flux en écrivant le `.obja` (lignes `v`, `efv`, `f`,
et une ligne `s` de poids cumulé par niveau), puis affiche le poids de chaque niveau. Options :
`--quantization Q` (positions écrites et poids calculés sur Q bits par coordonnée),
`--strategy qem|random`, `--target-ratio` (taille de M0, 0,05 par défaut), `--seed`. Pour voir
le résultat : `cd obja && ./server.py`, puis `localhost:8000/?example/bunny_squeeze.obja`.

## Tests

```bash
.venv/bin/python -m pytest                      # tous les tests (quelques secondes)
.venv/bin/python -m pytest tests/encodeur       # un seul dossier
.venv/bin/python -m pytest -v                   # avec le nom de chaque test
```

Les tests unitaires portent sur de tout petits maillages dont le résultat se calcule à la main
(le calcul est écrit dans le test ou dans son docstring) :

| Dossier | Contenu |
|---|---|
| `tests/commun/` | `Mesh` (voisins, `next`, `fan`, bords), arbre et numérotation, prédiction, lecture/écriture .obj |
| `tests/encodeur/` | quadriques, contraintes des collapses, un batch complet calculé à la main, `encode()` |
| `tests/decodeur/` | décodage de ce même batch, lignes OBJA écrites (`v`, `efv`, `f`, `s`), calcul des poids |
| `tests/bout_en_bout/` | `.obj` -> encodeur -> flux -> décodeur -> `.obja`, relu par `obja.py` : on doit retrouver exactement le maillage de départ (octaèdre, bunny en qem et random, suzanne) |

Fichiers d'aide :

- `tests/conftest.py`, lu automatiquement par pytest : ajoute `src/commun/`, `src/encodeur/`,
  `src/decodeur/` et `tests/` au chemin de recherche des modules, et déclare les fixtures
  (`octa`, `fan4`, `flux_octa`, recréés pour chaque test) ;
- `tests/exemples.py` : les petits maillages (octaèdre, éventail ouvert), le flux d'un batch
  écrit à la main pour l'octaèdre, et `faces_normalisees` pour comparer deux listes de faces.

Deux fichiers de test ne doivent pas porter le même nom, même dans des dossiers différents
(pytest les importe par leur nom).
