# Manifeste d'usage de l'IA - Projet CSI3D, Squeeze / CPM

Ce manifeste déclare tous les usages d'outils d'intelligence artificielle générative dans ce
projet. Il a lui-même été rédigé par Claude Code (Anthropic, modèle Opus 5.5) à partir
du contenu du dépôt et des réponses du groupe, puis relu et validé par le groupe.

## Cadre

Deux textes s'appliquent :

- la charte d'usage de l'IA de Toulouse INP du 7 avril 2026 (`documents/Charte-usagesIA.pdf`) ;
- le paragraphe *Use of AI* du sujet (`documents/sujet.pdf`) : l'IA est permise pour comprendre
  les articles et pour aider à programmer des fonctions, mais pas pour générer le code à partir
  d'un article ou d'une explication de l'algorithme, et l'infrastructure doit être créée par le
  groupe.

## Usages de l'IA

| Production | Outil | Ce que l'IA a fait | Ce que le groupe a fait |
|---|---|---|---|
| Compréhension des articles Squeeze et CPM | Claude (Anthropic), ChatGPT (OpenAI), Gemini (Google) | Explications des deux articles | Confrontation des explications au texte et aux figures des articles, discussion en groupe |
| `documents/rapport_mi_projet.pdf` | Claude | Mise en forme | Tout le contenu. Usage déjà déclaré dans la section 4 du rapport |
| Code de `src/` | GitHub Copilot | Autocomplétion pendant la saisie | Architecture, format du flux et écriture de toutes les fonctions. Chaque suggestion a été lue avant d'être acceptée |
| Débogage de `src/` | Claude, ChatGPT, Gemini | Aide à l'analyse de bugs | Choix et écriture des corrections |
| `tests/` : 54 tests, `conftest.py`, `exemples.py` | Claude Code | Génération intégrale, choix des cas de test compris | Relecture et exécution, directives "tests faisables à la main, unitaires et de bout en bout" |
| `documents/Comprendre_les_tests.pdf` | Claude | Génération | Relecture |
| `README.md` et ce manifeste | Claude Code | Génération | Relecture et validation |
| Diapositives de l'oral final | Claude | Génération de graphiques, signalés comme tels sur les diapositives | Le reste du support |

Le dossier `obja/` est le code fourni par les enseignants.

## Respect de la consigne du sujet

Le code de `src/` n'a pas été généré par une IA à partir des articles. Le découpage en
`commun/`, `encodeur/` et `decodeur/`, le flux `M0 + batches` qui sert de contrat entre les
deux équipes, et les fonctions elles-mêmes ont été conçus et écrits par le groupe. Dans
`src/`, l'IA est intervenue de deux façons seulement : l'autocomplétion de GitHub Copilot et
l'aide au débogage.

Les tests relèvent d'un autre régime : ils ont été entièrement générés par IA. La charte range
la génération de tests unitaires parmi les bons usages en développement logiciel ; nous le
déclarons ici sans réserve.

## Données transmises aux outils d'IA

- Les deux articles de Pajarola et Rossignac, qui sont des publications publiques.
- Le code du dépôt, lu par Claude Code pour générer les tests et le README, et soumis à un
  assistant pour le débogage.
- Aucun secret n'a été transmis : le dépôt ne contient ni clé d'API ni jeton d'authentification.

Les comptes utilisés ont varié selon les membres du groupe. Nous ne pouvons donc pas affirmer
que tous les échanges ont eu lieu sur des outils sécurisés ou institutionnels.

## Les cinq piliers de la charte, dans ce projet

- **Responsabilité.** Le groupe répond de tout le contenu du dépôt, y compris des fichiers
  générés par IA.
- **Esprit critique.** Les explications des articles ont été vérifiées dans les articles
  eux-mêmes et discutées au sein du groupe. Les suggestions de Copilot ont été systématiquement critiquées avant l'intégration. Les tests générés ont été compris à l'aide du pdf d'explication et exécutés.
- **Données et sécurité.** Voir la section précédente, qui dit ce qui a été transmis et sur
  quels types de comptes.
- **Transparence.** L'usage de l'IA est mentionné dans le rapport de mi-projet, sur les
  diapositives concernées de l'oral final, dans le README et dans ce manifeste.
- **Éthique et sobriété.** L'IA a servi là où elle faisait gagner du temps sans remplacer le
  travail demandé.

## Limites

- Les valeurs attendues des tests n'ont pas été recalculées à la main de façon systématique
  par le groupe. Les calculs écrits dans les tests et dans `Comprendre_les_tests.pdf`
  viennent de l'IA ; le groupe les a relus.
- Nous n'avons relevé aucune erreur marquante de l'IA pendant le projet.

## Engagement

Conformément à la charte, le groupe s'est engagé à :

- respecter les préconisations de l'établissement ;
- ne pas contourner les exigences pédagogiques excluant l'IA ;
- mentionner explicitement l'usage d'une IA ;
- ne mobiliser l'IA qu'en tant qu'outil de soutien, en gardant la maîtrise de ce qu'il produit ;
- être acteur d'un usage sobre, respectueux de l'éthique académique et de l'environnement.

Le groupe Squeeze / CPM
