"""Configuration commune à tous les tests (lu automatiquement par pytest).

1. On ajoute les dossiers de src/ (et tests/ lui-même, pour exemples.py) au chemin de
   recherche des modules, pour pouvoir écrire « from mesh import Mesh » comme dans le code.
2. On déclare les fixtures : les petits maillages de exemples.py, recréés pour chaque test
   (un test peut donc modifier son maillage sans gêner les autres).
"""

import os
import sys

import pytest

ICI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ICI, "..", "src")
sys.path.insert(0, ICI)
for dossier in ("commun", "encodeur", "decodeur"):
    sys.path.insert(0, os.path.join(SRC, dossier))

import exemples


@pytest.fixture
def octa():
    return exemples.octaedre()


@pytest.fixture
def fan4():
    return exemples.eventail_ouvert()


@pytest.fixture
def flux_octa():
    return exemples.flux_octaedre()
