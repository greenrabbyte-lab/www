# www.robalp.fr

Le platform engineering expliqué par le concret : chaque principe tel qu'on le met en place en
entreprise, puis tel qu'il tourne sur le labo maison. En français (racine), en anglais (`/en/`) et
en allemand (`/de/`). Aucune donnée personnelle.

## Organisation

| Dossier | Contenu |
|---|---|
| `contenu/` | tous les textes, un fichier YAML par page et par langue, et les chiffres (`donnees.yml`) ; voir `contenu/LISEZMOI.md` |
| `outils/generer.py` | la structure des pages ; génère `_site/` après avoir vérifié la cohérence des langues |
| `outils/image_partage.py` | dessine les images de partage de chaque langue |
| `assets/` | feuille de style, police, compteur, icône, images de partage |
| `.github/workflows/pages.yml` | génère à chaque pull request ; génère et publie sur GitHub Pages à chaque poussée sur `main` |

Les pages HTML ne sont plus versionnées : elles sont produites à la publication.

## Pages

`index`, `en-vrai` (C'est quoi, en vrai ?), `portail`, `golden-paths`, `agents-ia`,
`observabilite`, `architecture`, plus une page `404` trilingue.

## Référencement (moteurs et assistants IA)

- Chaque page : `title` et `description` propres à la langue, `lang`, URL canonique de la langue,
  balises `hreflang` vers les trois versions et `x-default` vers le français, `og:locale` et ses
  variantes, image de partage dans la langue, données structurées schema.org.
- `sitemap.xml` : les 21 adresses, chacune avec ses variantes de langue.
- `robots.txt` : tout est ouvert, robots des assistants IA nommés. `llms.txt` : résumé par langue.

## Sobriété

- Fond noir, une seule police pour tout le site : Geist (licence OFL, `assets/geist-OFL.txt`),
  réduite aux caractères du français, de l'anglais et de l'allemand, graisses 300 à 700 : 17 ko.
- Pas de framework, pas de JavaScript de mise en page : menu mobile, sélecteur de langue et
  détails repliables sont en HTML natif. Seul `assets/compteur.js` affiche le poids de la page et
  une estimation de l'énergie (modèle Sustainable Web Design v4, 0,30 kWh par Go).

## Chiffres

`contenu/donnees.yml` reprend `greenrabbyte-lab/platform`, `qualite/livraisons.csv` (du 17 octobre
au 5 novembre 2026, dépôts `platform`, `linky`, `keycloak-non-regression`). Le générateur vérifie
que la série par jour donne bien le total. À rafraîchir quand le fichier avance.

## Référencement

Le site est statique, sans JavaScript nécessaire à la lecture : moteurs et assistants IA lisent le
même HTML. Le générateur écrit `robots.txt` (tout autorisé, robots IA nommés), `sitemap.xml` (trois
langues, `hreflang`), `llms.txt` et les données structurées de chaque page. À chaque publication,
`outils/indexnow.py` annonce les adresses aux moteurs qui suivent IndexNow (Bing, Yandex, Seznam,
Naver, Yep) ; la clé de `indexnow.txt` est publique par construction. Google ne suit pas IndexNow :
déclarer le site et son plan dans Search Console (propriétaire du domaine).
