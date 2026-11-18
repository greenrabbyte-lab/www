#!/usr/bin/env python3
"""Annonce les pages publiées aux moteurs qui suivent IndexNow (Bing, Yandex, Seznam, Naver, Yep).

    python3 outils/indexnow.py _site

Lit les adresses dans _site/sitemap.xml et la clé dans indexnow.txt (publique : elle est servie à
la racine du site). Google ne suit pas IndexNow : il découvre les pages par le plan du site.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
HOTE = "www.robalp.fr"


def main():
    sortie = Path(sys.argv[1] if len(sys.argv) > 1 else RACINE / "_site")
    cle = (RACINE / "indexnow.txt").read_text(encoding="utf-8").strip()
    adresses = re.findall(r"<loc>([^<]+)</loc>", (sortie / "sitemap.xml").read_text(encoding="utf-8"))
    corps = {"host": HOTE, "key": cle, "keyLocation": f"https://{HOTE}/{cle}.txt", "urlList": adresses}
    requete = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(corps).encode(),
                                     headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        print(f"IndexNow : {len(adresses)} adresses annoncées, réponse {reponse.status}")


if __name__ == "__main__":
    main()
