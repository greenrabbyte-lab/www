#!/usr/bin/env python3
"""Vérifie, sur le site en ligne, tout ce dont un moteur ou un assistant IA a besoin pour l'indexer.

    python3 outils/verifier_indexation.py                      # le site publié
    python3 outils/verifier_indexation.py --base http://127.0.0.1:8000   # un _site servi localement

Contrôles : robots.txt ouvert et qui annonce le plan du site ; chaque adresse du plan répond 200,
se déclare canonique, indexable, dans sa langue, avec ses trois traductions ; llms.txt et la clé
IndexNow sont servis ; l'apex et http renvoient vers https://www. Ce script ne dit pas si un moteur
a effectivement indexé le site : cela se lit dans Search Console et Bing Webmaster Tools.
"""
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SITE = "https://www.robalp.fr"
LANGUES = {"fr": "", "en": "/en", "de": "/de"}


class SansRedirection(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def lire(adresse, suivre=True):
    ouvreur = urllib.request.build_opener() if suivre else urllib.request.build_opener(SansRedirection)
    requete = urllib.request.Request(adresse, headers={"User-Agent": "robalp-verification-indexation"})
    try:
        with ouvreur.open(requete, timeout=20) as reponse:
            return reponse.status, reponse.read().decode("utf-8", "replace"), reponse.headers
    except urllib.error.HTTPError as erreur:
        return erreur.code, "", erreur.headers


def main():
    base = sys.argv[sys.argv.index("--base") + 1].rstrip("/") if "--base" in sys.argv else SITE
    en_ligne = base == SITE
    erreurs, avertissements = [], []

    code, robots, _ = lire(f"{base}/robots.txt")
    if code != 200:
        erreurs.append(f"robots.txt : {code}")
    if f"Sitemap: {SITE}/sitemap.xml" not in robots:
        erreurs.append("robots.txt n'annonce pas le plan du site")
    bloc = re.search(r"User-agent: \*\n((?:.+\n)*)", robots)
    if not bloc or re.search(r"^Disallow: /\s*$", bloc.group(1), re.M):
        erreurs.append("robots.txt ferme le site à tous les robots")

    code, plan, _ = lire(f"{base}/sitemap.xml")
    adresses = re.findall(r"<loc>([^<]+)</loc>", plan)
    if code != 200 or not adresses:
        erreurs.append(f"sitemap.xml : {code}, {len(adresses)} adresse(s)")
    for adresse in adresses:
        code, page, _ = lire(adresse.replace(SITE, base, 1))
        if code != 200:
            erreurs.append(f"{adresse} : {code}")
            continue
        canonique = re.search(r'<link rel="canonical" href="([^"]+)"', page)
        if not canonique or canonique.group(1) != adresse:
            erreurs.append(f"{adresse} : adresse canonique {canonique.group(1) if canonique else 'absente'}")
        robots_page = re.search(r'<meta name="robots" content="([^"]+)"', page)
        if not robots_page or "noindex" in robots_page.group(1) or "index" not in robots_page.group(1):
            erreurs.append(f"{adresse} : balise robots {robots_page.group(1) if robots_page else 'absente'}")
        langue = next(l for l, prefixe in sorted(LANGUES.items(), key=lambda p: -len(p[1])) if adresse.startswith(SITE + prefixe + "/") or adresse == SITE + prefixe)
        if f'<html lang="{langue}' not in page:
            erreurs.append(f"{adresse} : attribut lang différent de {langue}")
        traductions = set(re.findall(r'<link rel="alternate" hreflang="([^"]+)"', page))
        if traductions != {"fr", "en", "de", "x-default"}:
            erreurs.append(f"{adresse} : hreflang {sorted(traductions)}")
        if "<h1" not in page or not re.search(r'<meta name="description" content="[^"]{50,}"', page):
            erreurs.append(f"{adresse} : titre h1 ou description absents")
        if 'type="application/ld+json"' not in page:
            erreurs.append(f"{adresse} : données structurées absentes")

    cle = (RACINE / "indexnow.txt").read_text(encoding="utf-8").strip()
    code, contenu, _ = lire(f"{base}/{cle}.txt")
    if code != 200 or contenu.strip() != cle:
        erreurs.append(f"clé IndexNow : {code}")
    code, llms, _ = lire(f"{base}/llms.txt")
    if code != 200 or len(re.findall(r"\]\(https://www\.robalp\.fr/", llms)) != len(adresses):
        erreurs.append(f"llms.txt : {code}, liens différents du plan du site")

    if en_ligne:
        for depart in ("https://robalp.fr/", "http://robalp.fr/"):
            code, _, entetes = lire(depart, suivre=False)
            if code not in (301, 308) or "www.robalp.fr" not in (entetes.get("Location") or ""):
                erreurs.append(f"{depart} ne renvoie pas vers www ({code})")
        code, _, entetes = lire("http://www.robalp.fr/", suivre=False)
        if code not in (301, 308):
            # À passer en erreur dès que « Enforce HTTPS » est coché dans les réglages GitHub Pages.
            avertissements.append(f"http://www.robalp.fr/ répond {code} sans renvoyer vers https (réglage GitHub Pages « Enforce HTTPS »)")

    print(f"{len(adresses)} adresses vérifiées, {len(erreurs)} erreur(s), {len(avertissements)} avertissement(s)")
    for a in avertissements:
        print(f"::warning::{a}")
    for e in erreurs:
        print(f"::error::{e}")
    sys.exit(1 if erreurs else 0)


if __name__ == "__main__":
    main()
