# www.robalp.fr

Le platform engineering expliqué par le concret : chaque principe tel qu'on le met en place en
entreprise, puis tel qu'il tourne sur le labo maison. Statique, sans framework, publié par GitHub
Pages à chaque poussée sur `main` (`.github/workflows/pages.yml`). Aucune donnée personnelle.

## Pages

| Fichier | Contenu |
|---|---|
| `index.html` | Accueil : les trois niveaux de lecture, le relevé des livraisons |
| `en-vrai.html` | C'est quoi, en vrai ? Problème, rôle d'une équipe plateforme, journée type, vocabulaire |
| `portail.html` | Le portail développeur (Port) |
| `golden-paths.html` | Les golden paths, le bac à sable, les douze critères d'acceptation |
| `agents-ia.html` | La gouvernance des agents IA (délégation encadrée), mesures et journal des erreurs |
| `observabilite.html` | Ce qui est mesuré, pour qui, et comment sans ouvrir de porte |
| `architecture.html` | Machines, chemin des données, ce qui part dans Azure et ce qui reste à la maison |
| `404.html` | Page introuvable (non indexée) |

## Référencement (moteurs et assistants IA)

- Chaque page : `title` et `description` propres, URL canonique, Open Graph (image `assets/partage.png`,
  1200 × 630), données structurées schema.org (`WebSite`, `TechArticle`, `BreadcrumbList`, et
  `DefinedTermSet` pour le vocabulaire).
- `sitemap.xml` : les sept pages. `robots.txt` : tout est ouvert, et les robots des assistants IA sont
  nommés pour que le choix soit lisible (instructions en tête du fichier pour refuser l'entraînement).
- `llms.txt` : résumé du site pour les agents. Proposition communautaire, pas une norme ; Google
  indique qu'il ne l'utilise pas pour la recherche ni pour ses réponses IA.

## Sobriété

- Fond noir, une seule police téléchargée : Anybody (licence OFL, `assets/anybody-OFL.txt`), réduite
  aux caractères du français, largeur figée, graisse variable 100 à 800 : 15 ko. Le texte courant
  utilise la police du système.
- Chaque page affiche son poids, mesuré par le navigateur, et une estimation de l'énergie
  (modèle Sustainable Web Design v4, 0,30 kWh par Go) : `assets/compteur.js`.

## Chiffres

Le relevé de l'accueil et le graphique de `agents-ia.html` sont calculés depuis
`greenrabbyte-lab/platform`, `qualite/livraisons.csv` (du 17 octobre au 5 novembre 2026, dépôts
`platform`, `linky`, `keycloak-non-regression`). À rafraîchir quand le fichier avance.

## Avant de publier

- Vérifier avec l'employeur ce qui peut être publié ; aucune mention de l'employeur sur le site.
