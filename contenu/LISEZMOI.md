# Textes du site, par langue

Tous les textes visibles de www.robalp.fr sont ici, un fichier par page et par langue. Le code
(`outils/generer.py`) ne contient aucune phrase : on peut faire relire un dossier de langue sans
toucher au reste.

```
contenu/
  donnees.yml        chiffres de livraison, communs aux trois langues
  fr/                langue source
  en/                anglais, publié sous /en/
  de/                allemand, publié sous /de/
    commun.yml       navigation, pied de page, achats, image de partage, page introuvable
    index.yml        accueil
    en-vrai.yml      « C'est quoi, en vrai ? »
    portail.yml      le portail développeur
    golden-paths.yml les golden paths
    agents-ia.yml    les agents IA encadrés
    observabilite.yml l'observabilité
    architecture.yml l'architecture
```

## Règles pour relire ou traduire

- Ne modifier que le texte entre guillemets, jamais les clés à gauche des deux-points.
- Garder les `{repères}` entre accolades tels quels : le générateur les remplace par les chiffres
  de `donnees.yml`, formatés selon la langue (9,8 en français et en allemand, 9.8 en anglais).
- Garder les balises HTML (`<strong>`, `<code>`) ; leurs attributs s'écrivent entre apostrophes.
- Garder le même nombre d'éléments dans les listes : le générateur compare chaque langue au
  français et refuse de publier à la moindre différence de clé, de liste, de repère ou de balise.
- Typographie : le générateur pose lui-même les espaces insécables du français (avant `: ; ? !`,
  dans les guillemets) et entre un nombre et son unité, dans toutes les langues.
- Conventions : guillemets « » en français, “ ” en anglais, „ “ en allemand.

## Vérifier et voir le résultat

```
python3 -m pip install -r outils/requirements.txt
python3 outils/generer.py          # écrit le site dans _site/
python3 -m http.server -d _site    # puis http://localhost:8000
```

Les images de partage (`assets/partage-<langue>.png`) se redessinent avec
`outils/image_partage.py` quand la section `image_partage` de `commun.yml` change.
