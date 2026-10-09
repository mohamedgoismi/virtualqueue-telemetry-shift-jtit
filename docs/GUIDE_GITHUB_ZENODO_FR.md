# Guide — publication GitHub et obtention du DOI Zenodo

Nom proposé : **virtualqueue-telemetry-shift-jtit**.

## 1. Préparation GitHub

1. Ouvrir <https://github.com/new> et se connecter à son compte.
2. Créer un dépôt **public**, avec le nom `virtualqueue-telemetry-shift-jtit`.
3. Éviter de demander à GitHub de créer un README, une LICENSE ou un
   .gitignore initiaux : ces fichiers figurent déjà dans le projet.
4. Décompresser le ZIP reçu dans un dossier Windows. Vérifier les métadonnées
   des cinq auteurs (`AUTHORS.md`, `CITATION.cff`) et leur accord pour la licence.
5. Depuis ce dossier, ouvrir PowerShell et exécuter (remplacer `VOTRE_COMPTE`) :

```powershell
git init
git branch -M main
git add .
git commit -m "Release candidate: synthetic FIFO telemetry study"
git remote add origin https://github.com/VOTRE_COMPTE/virtualqueue-telemetry-shift-jtit.git
git push -u origin main
```

Git et un moyen d'authentification GitHub doivent être configurés. On peut
également utiliser GitHub Desktop (Add local repository → Publish repository).

**Votre lien réel sera** :
`https://github.com/VOTRE_COMPTE/virtualqueue-telemetry-shift-jtit`
seulement **après** publication. Remplacez `VOTRE_COMPTE` par le vrai compte.

## 2. Configurer Zenodo AVANT la release

1. Aller sur <https://zenodo.org/> et créer/se connecter au compte Zenodo.
2. Associer le compte GitHub dans les paramètres Zenodo.
3. Ouvrir la page « GitHub » depuis le menu du profil sur Zenodo.
4. Cliquer **Sync now** si le nouveau dépôt n'apparaît pas.
5. Activer le dépôt avec le commutateur Zenodo (enabled).
6. Vérifier que `CITATION.cff`, l'ordre et les noms des auteurs ainsi que
   la licence sont corrects. Zenodo utilise ces métadonnées lors de l'archive.

Guide officiel : <https://help.zenodo.org/docs/github/enable-repository/>

## 3. Créer la première release

1. Revenir sur GitHub, ouvrir le dépôt → **Releases** → **Create a new release**.
2. Choisir **Create new tag** et écrire `v0.1.0`, ciblant `main`.
3. Titre : `VirtualQueue synthetic FIFO research artifacts v0.1.0`.
4. Coller le contenu du fichier `docs/RELEASE_NOTES_v0.1.0.md`.
5. Cliquer **Publish release**.
6. Attendre l'archivage par Zenodo ; sur Zenodo, contrôler les auteurs,
   la licence, le titre, la version et récupérer le DOI effectivement attribué.

Guide officiel : <https://help.zenodo.org/docs/github/archive-software/github-upload/>

⚠️ **Zenodo n'attribue pas un DOI automatiquement au simple dépôt de fichiers
sur GitHub**. La release doit être créée après l'activation de l'intégration.
La présence d'un `CITATION.cff` ne suffit pas à générer le DOI.

## 4. Renseigner le DOI dans l'article

Quand Zenodo fournit un DOI de version, exemple de structure uniquement :

```latex
\subsection*{Code and Data Availability}
The simulation code, generated synthetic data and result files for this study
are publicly archived on Zenodo at DOI: \url{DOI_A_REMPLACER}.
The development repository is available at \url{URL_GITHUB_A_REMPLACER}.
No 5G field or independent network measurements are included.
```

Ne pas publier cette phrase avant d'avoir remplacé les deux champs par des
identifiants réels. Un DOI de concept (toutes versions) peut également être
fourni ; utiliser de préférence le DOI de la **version citée** pour figer les
résultats précis, et le DOI concept pour pointer sur toutes les versions.

## 5. Réutilisation et journal JTIT

Une archive GitHub/Zenodo publique peut révéler l'identité des auteurs dans
une procédure en double aveugle. Vérifier la politique JTIT ; ne pas inclure
le nom des auteurs dans les liens visibles de la version anonyme si leur
apparition n'est pas autorisée.

Les formulaires officiels JTIT (Ghostwriting, License, Conflicts of Interest)
restent indépendants du DOI du code et doivent être signés.
