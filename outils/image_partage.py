#!/usr/bin/env python3
"""Dessine les images de partage (Open Graph, 1200 × 630) de chaque langue : assets/partage-<langue>.png.

    pip install pillow fonttools brotli
    python3 outils/image_partage.py

Les textes viennent de contenu/<langue>/commun.yml (section image_partage). À relancer seulement
quand ces textes changent : les images sont versionnées, la publication ne les redessine pas.
"""
import io
from pathlib import Path

import yaml
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
LANGUES = ["fr", "en", "de"]
FOND, TEXTE, DOUX, FILET, TENSION = "#000000", "#EDEBE4", "#A3A097", "#2A2924", "#FFE14D"


def police(graisse, taille):
    variable = TTFont(RACINE / "assets" / "geist.woff2")
    statique = instancer.instantiateVariableFont(variable, {"wght": graisse})
    statique.flavor = None
    tampon = io.BytesIO()
    statique.save(tampon)
    tampon.seek(0)
    return ImageFont.truetype(tampon, taille)


def dessiner(langue):
    textes = yaml.safe_load((RACINE / "contenu" / langue / "commun.yml").read_text(encoding="utf-8"))["image_partage"]
    image = Image.new("RGB", (1200, 630), FOND)
    d = ImageDraw.Draw(image)
    taille = 84
    while True:  # le titre doit tenir dans 1056 px de large
        gros = police(600, taille)
        if max(d.textlength(l, font=gros) for l in textes["titre"]) <= 1056 or taille <= 56:
            break
        taille -= 2
    y = 92
    for i, ligne in enumerate(textes["titre"]):
        couleur = TENSION if i == len(textes["titre"]) - 1 else TEXTE
        d.text((72, y), ligne.replace(" €", " €"), font=gros, fill=couleur)
        y += int(taille * 1.24)
    moyen = police(400, 34)
    y = 440
    for ligne in textes["sous_titre"]:
        d.text((72, y), ligne, font=moyen, fill=DOUX)
        y += 46
    d.line((72, 556, 1128, 556), fill=FILET, width=2)
    d.polygon([(85, 566), (73, 582), (81, 582), (78, 596), (91, 578), (83, 578)], fill=TENSION)
    d.text((100, 566), "robalp.fr", font=police(600, 30), fill=TEXTE)
    sortie = RACINE / "assets" / f"partage-{langue}.png"
    image.save(sortie, optimize=True)
    print(f"{sortie.relative_to(RACINE)} ({taille} px)")


if __name__ == "__main__":
    for langue in LANGUES:
        dessiner(langue)
