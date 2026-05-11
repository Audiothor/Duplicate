# Duplicate Finder & Manager

Un outil graphique en Python pour identifier, visualiser et gérer les fichiers photos et vidéos en double de manière sécurisée.

## Fonctionnalités

- **Scan Récursif** : Analyse tous les sous-répertoires du dossier sélectionné.
- **Détection par Empreinte Numérique (Checksum)** : 
    - Optimisation en deux étapes : les fichiers sont d'abord comparés par taille, puis par hachage MD5. Cela garantit une précision de 100% tout en restant extrêmement rapide.
- **Aperçu Intégré** : Visualisation instantanée des photos lors de la sélection dans la liste pour confirmer la duplication sans ouvrir d'application externe.
- **Système de Corbeille Sécurisé (Trash)** : 
    - Les fichiers ne sont pas supprimés définitivement mais déplacés dans un dossier `Trash` créé à la racine du dossier scanné.
    - **Nettoyage intelligent** : Si le déplacement d'un fichier rend son répertoire d'origine vide, ce répertoire est également déplacé dans la corbeille pour garder votre arborescence propre.
    - Gestion des collisions : En cas de noms identiques dans la corbeille, un suffixe numérique est automatiquement ajouté.

## Installation

### Prérequis

- **Python 3.8+**
- Un environnement Windows, macOS ou Linux (testé principalement sur Windows).

### Étapes

1. Clonez ou téléchargez ce répertoire.
2. Ouvrez un terminal dans le dossier du projet.
3. Installez la dépendance graphique (PyQt6) :

```bash
pip install -r requirements.txt
```

## Utilisation

Pour lancer l'application, exécutez la commande suivante :

```bash
python main.py
```

1. Cliquez sur **Browse** pour choisir le dossier à analyser.
2. Sélectionnez les types de fichiers à rechercher (**Photos** et/ou **Videos**).
3. Cliquez sur **Scan**.
4. Parcourez les groupes de doublons. Cliquez sur un fichier pour voir son aperçu à droite.
5. Cochez les cases dans la colonne **Trash?** pour les fichiers que vous souhaitez supprimer.
6. Cliquez sur **Move Selected to Trash** en bas à droite pour valider l'opération.

## Types de fichiers supportés

- **Photos** : .jpg, .jpeg, .png, .gif, .bmp, .webp, .tiff
- **Vidéo** : .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm
