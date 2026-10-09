# VirtualQueue — publication du projet de recherche

Ce dépôt contient **le code exécutable et les résultats d'une simulation FIFO synthétique** utilisés pour l'étude sur la prédiction des violations de délai avec rapports de paquets incomplets.
Il ne comprend pas de véritables mesures 5G et ne constitue pas une validation externe.

**Pour publier sur GitHub et obtenir un DOI Zenodo :** lire
[`docs/GUIDE_GITHUB_ZENODO_FR.md`](docs/GUIDE_GITHUB_ZENODO_FR.md).

La procédure est la suivante : créer un dépôt GitHub public, y déposer ces fichiers,
connecter et activer le dépôt dans Zenodo **avant** de créer la release GitHub
`v0.1.0`, puis récupérer le DOI réellement délivré par Zenodo.

Avant la publication, confirmer avec les cinq coauteurs les métadonnées de
`CITATION.cff`, l'attribution des contributions au logiciel et la licence MIT.
Le papier complet et la classe LaTeX du journal ne sont pas inclus dans ce dépôt
public, afin de séparer les sources du programme du processus éditorial anonyme.

Tests rapides : `python code/test_temporal_integrity.py` puis
`python -m unittest discover -s tests -v`.
