#!/usr/bin/env python3
"""Génère www.robalp.fr en français, anglais et allemand à partir des fichiers de langue.

    python3 outils/generer.py            # écrit le site dans _site/
    python3 outils/generer.py --sortie d # ailleurs

Les textes vivent dans contenu/<langue>/<page>.yml, les chiffres dans contenu/donnees.yml.
Ce script ne contient que la structure des pages. Avant d'écrire quoi que ce soit, il vérifie que
chaque langue a exactement les mêmes clés, les mêmes {repères} et les mêmes balises HTML que le
français, et que les chiffres sont cohérents. À la moindre différence, il s'arrête et dit où.
"""
import argparse
import html
import json
import re
import shutil
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
CONTENU = RACINE / "contenu"
SITE = "https://www.robalp.fr/"
NOM = "Robalp"
LANGUES = ["fr", "en", "de"]
SOURCE = "fr"
PAGES = ["index", "en-vrai", "portail", "golden-paths", "agents-ia", "observabilite", "architecture"]
ORDRE = PAGES[1:]  # ordre de lecture pour « précédent / suivant »
NAV = PAGES[1:]
OG_LOCALE = {"fr": "fr_FR", "en": "en_US", "de": "de_DE"}
BCP47 = {"fr": "fr-FR", "en": "en-US", "de": "de-DE"}
ESTIMATION = "https://sustainablewebdesign.org/estimating-digital-emissions/"
REPERE = re.compile(r"\{(\w+)\}")
BALISE = re.compile(r"</?([a-zA-Z0-9]+)")


# --- Chargement et vérifications --------------------------------------------------------------

def charger():
    donnees = yaml.safe_load((CONTENU / "donnees.yml").read_text(encoding="utf-8"))
    textes = {}
    for langue in LANGUES:
        textes[langue] = {}
        for nom in ["commun"] + PAGES:
            chemin = CONTENU / langue / f"{nom}.yml"
            if not chemin.exists():
                sys.exit(f"Fichier manquant : {chemin.relative_to(RACINE)}")
            textes[langue][nom] = yaml.safe_load(chemin.read_text(encoding="utf-8"))
    return donnees, textes


def comparer(source, cible, ou, erreurs):
    """Même structure que le français : mêmes clés, mêmes longueurs, mêmes repères et balises."""
    if isinstance(source, dict):
        if not isinstance(cible, dict):
            erreurs.append(f"{ou} : une section était attendue")
            return
        for cle in source:
            if cle not in cible:
                erreurs.append(f"{ou}.{cle} : clé manquante")
            else:
                comparer(source[cle], cible[cle], f"{ou}.{cle}", erreurs)
        for cle in cible:
            if cle not in source:
                erreurs.append(f"{ou}.{cle} : clé inconnue en français")
    elif isinstance(source, list):
        if not isinstance(cible, list) or len(cible) != len(source):
            erreurs.append(f"{ou} : il faut {len(source)} éléments, comme en français")
            return
        for i, (s, c) in enumerate(zip(source, cible)):
            comparer(s, c, f"{ou}[{i + 1}]", erreurs)
    elif isinstance(source, str):
        if not isinstance(cible, str) or not cible.strip():
            erreurs.append(f"{ou} : texte vide")
            return
        if sorted(REPERE.findall(source)) != sorted(REPERE.findall(cible)):
            erreurs.append(f"{ou} : repères différents du français {sorted(set(REPERE.findall(source)))}")
        if Counter(BALISE.findall(source)) != Counter(BALISE.findall(cible)):
            erreurs.append(f"{ou} : balises HTML différentes du français")


def verifier(donnees, textes):
    erreurs = []
    if sum(donnees["pr_par_jour"].values()) != donnees["pr"]:
        erreurs.append("donnees.yml : la somme de pr_par_jour ne donne pas pr")
    if donnees["delegation"] not in donnees["pr_par_jour"]:
        erreurs.append("donnees.yml : la date de délégation n'est pas dans pr_par_jour")
    for langue in LANGUES:
        if textes[langue]["commun"].get("langue") != langue:
            erreurs.append(f"{langue}/commun.yml : la clé langue doit valoir {langue}")
        if langue == SOURCE:
            continue
        for nom in ["commun"] + PAGES:
            comparer(textes[SOURCE][nom], textes[langue][nom], f"{langue}/{nom}.yml", erreurs)
    for langue in LANGUES:
        if not (RACINE / "assets" / f"partage-{langue}.png").exists():
            erreurs.append(f"assets/partage-{langue}.png manquant (outils/image_partage.py)")
    return erreurs


class Equilibre(HTMLParser):
    VIDES = {"meta", "link", "br", "img", "input", "hr", "path", "rect", "line", "circle", "source"}

    def __init__(self):
        super().__init__()
        self.pile, self.erreurs = [], []

    def handle_starttag(self, balise, attributs):
        if balise not in self.VIDES:
            self.pile.append(balise)

    def handle_endtag(self, balise):
        if balise in self.VIDES:
            return
        if self.pile and self.pile[-1] == balise:
            self.pile.pop()
        else:
            self.erreurs.append(balise)


# --- Mise en forme selon la langue ------------------------------------------------------------

UNITES = r"€|ko|kB|Mo|MB|Go|GB|Mio|MiB|kWh|Wh|h\b|Uhr|minutes|Minuten|secondes|seconds|Sekunden|milliards|Milliarden|billion|jours|days|Tage"


def typo(texte, langue):
    texte = re.sub(rf"(\d) ({UNITES})", "\\1\u00a0\\2", texte)
    if langue == "fr":  # espaces insécables de la typographie française
        texte = re.sub(r" ([:;?!»])", "\u00a0\\1", texte)
        texte = texte.replace("« ", "«\u00a0")
    return texte


def nombre(x, langue, decimales=0):
    s = f"{x:.{decimales}f}"
    return s if langue == "en" else s.replace(".", ",")


def valeurs(donnees, langue):
    return {
        "jours": str(len(donnees["pr_par_jour"])),
        "pr": str(donnees["pr"]),
        "releases": str(donnees["releases"]),
        "erreurs": str(donnees["erreurs"]),
        "erreurs_prod": str(donnees["erreurs_production"]),
        "taux": nombre(100 * donnees["erreurs"] / donnees["pr"], langue, 1),
        "taux_prod": nombre(100 * donnees["erreurs_production"] / donnees["pr"], langue, 1),
        "pr_delegation": str(donnees["pr_par_jour"][donnees["delegation"]]),
    }


def url(langue, page):
    base = SITE if langue == SOURCE else f"{SITE}{langue}/"
    return base if page == "index" else f"{base}{page}.html"


def vers(depuis, langue, page):
    """Lien relatif d'une page en langue `depuis` vers `page` en langue `langue`."""
    racine = "" if depuis == SOURCE else "../"
    dossier = "" if langue == SOURCE else f"{langue}/"
    return f"{racine}{dossier}{page}.html"


ICONES = {
    "eclair": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2 4 14h7l-2 8 9-12h-7z" fill="currentColor"/></svg>',
    "portail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M3 9h18M9 9v11"/></svg>',
    "golden-paths": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 19c5 0 4-7 7-7s2-7 7-7"/><circle cx="5" cy="19" r="1.8"/><circle cx="19" cy="5" r="1.8"/></svg>',
    "agents-ia": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/></svg>',
    "observabilite": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19h16"/><path d="M5 15l4-5 4 3 6-7"/></svg>',
}
COCHE = '<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="10" fill="#FFE14D"/><path d="M5.8 10.3l2.7 2.7 5.7-5.8" stroke="#000" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'


class Page:
    """Accès aux textes d'une page, déjà remplis (chiffres) et mis en forme (typographie)."""

    def __init__(self, langue, brut, vals):
        self.langue, self.brut, self.vals = langue, brut, vals

    def __call__(self, *chemin, **extra):
        valeur = self.brut
        for cle in chemin:
            valeur = valeur[cle]
        return self.texte(valeur, **extra)

    def texte(self, valeur, **extra):
        table = dict(self.vals, **extra)
        return typo(REPERE.sub(lambda m: table[m.group(1)], valeur), self.langue)

    def liste(self, *chemin):
        valeur = self.brut
        for cle in chemin:
            valeur = valeur[cle]
        return valeur


def points(t, *chemin):
    return "\n".join(f"    <li>{t.texte(p)}</li>" for p in t.liste(*chemin, "points"))


def carte(t, cle, labo=False):
    classe = "carte labo" if labo else "carte"
    return f'<div class="{classe}"><h2>{t(cle, "titre")}</h2><ul>\n{points(t, cle)}\n  </ul></div>'


def duo(t, gauche="entreprise", droite="labo", labo_a_gauche=False):
    return f"""<section class="duo">
  {carte(t, gauche, labo=labo_a_gauche)}
  {carte(t, droite, labo=not labo_a_gauche)}
</section>"""


def etapes(t, *chemin):
    lignes = "\n".join(f"    <li><strong>{t.texte(e['titre'])}</strong><span>{t.texte(e['texte'])}</span></li>"
                       for e in t.liste(*chemin, "etapes"))
    return f'<ol class="etapes">\n{lignes}\n  </ol>'


def repli(titre, contenu):
    return f'<details class="repli"><summary>{titre}</summary><div>{contenu}</div></details>'


def repli_points(t, cle):
    return repli(t(cle, "titre"), f"<ul>\n{points(t, cle)}\n  </ul>")


def repli_texte(t, cle):
    return repli(t(cle, "titre"), f"<p>{t(cle, 'texte')}</p>")


def tableau(t, colonnes, lignes, numeros=False):
    tete = "".join(f'<th scope="col">{t.texte(c)}</th>' for c in colonnes)
    corps = []
    for i, ligne in enumerate(lignes, start=1):
        cellules = "".join(f"<td>{t.texte(v)}</td>" for v in ligne.values())
        numero = f'<td class="n">{i}</td>' if numeros else ""
        corps.append(f"      <tr>{numero}{cellules}</tr>")
    return f'<div class="tableau"><table>\n    <thead><tr>{tete}</tr></thead>\n    <tbody>\n' + "\n".join(corps) + "\n    </tbody>\n  </table></div>"


def achats(c):
    lignes = "\n".join(f"      <li><span>{c.texte(l['article'])}</span><span>{c.texte(l['prix'])}</span></li>" for l in c.liste("achats", "lignes"))
    return f'<ul class="lignes">\n{lignes}\n    </ul>'


def graphique(t, donnees):
    jours = donnees["pr_par_jour"]
    x0, largeur, base, haut, maxi = 40, 670, 196, 156, max(jours.values())
    pas = largeur / len(jours)
    morceaux = []
    for i, (jour, n) in enumerate(jours.items()):
        h = n / maxi * haut
        classe = "apres" if jour >= donnees["delegation"] else "avant"
        x = x0 + i * pas + 3
        if n:
            morceaux.append(f'<rect class="{classe}" x="{x:.1f}" y="{base - h:.1f}" width="{pas - 6:.1f}" height="{max(h, 1.5):.1f}"/>')
        if n >= 5:
            morceaux.append(f'<text class="valeur" x="{x + (pas - 6) / 2:.1f}" y="{base - h - 6:.1f}" text-anchor="middle">{n}</text>')
    xr = x0 + list(jours).index(donnees["delegation"]) * pas
    return f"""<figure class="graphe">
  <div class="defile">
    <svg viewBox="0 0 720 230" role="img" aria-labelledby="graphe-titre">
      <title id="graphe-titre">{t("graphe", "titre_accessible")}</title>
      <line class="repere" x1="{xr:.1f}" y1="22" x2="{xr:.1f}" y2="{base}"/>
      <text x="{xr - 6:.1f}" y="26" text-anchor="end">{t("graphe", "repere")}</text>
      {''.join(morceaux)}
      <line class="axe" x1="{x0}" y1="{base}" x2="{x0 + largeur}" y2="{base}"/>
      <text x="{x0 - 6}" y="{base + 4}" text-anchor="end">0</text>
      <text x="{x0}" y="{base + 22}">{t("graphe", "debut")}</text>
      <text x="{xr + pas / 2:.1f}" y="{base + 22}" text-anchor="middle">{t("graphe", "delegation")}</text>
      <text x="{x0 + largeur}" y="{base + 22}" text-anchor="end">{t("graphe", "fin")}</text>
    </svg>
  </div>
  <figcaption>{t("graphe", "legende")}</figcaption>
</figure>"""


# --- Pages ------------------------------------------------------------------------------------

def page_index(t, c, donnees):
    etapes_demo = "\n".join(f'      <li style="--i:{i}"><span class="etat">{COCHE}</span>{t.texte(e)}</li>'
                            for i, e in enumerate(t.liste("demo", "etapes")))
    pastilles = "".join(f'<span class="pastille">{t.texte(p)}</span>' for p in t.liste("demo", "pastilles"))
    tuiles = "\n".join(
        f'    <a class="tuile" href="{p}.html">{ICONES[p]}<h3>{t("methodes", p, "titre")}</h3><p>{t("methodes", p, "texte")}</p></a>'
        for p in ["portail", "golden-paths", "agents-ia", "observabilite"])
    return f"""
<section class="accroche">
  <div>
    <h1>{t("accroche", "titre")}</h1>
    <p class="chapeau">{t("accroche", "chapeau")}</p>
    <div class="boutons"><a class="bouton premier" href="en-vrai.html">{t("accroche", "bouton_principal")}</a><a class="bouton" href="architecture.html">{t("accroche", "bouton_secondaire")}</a></div>
  </div>
  <figure class="demo" aria-label="{html.escape(t("demo", "aria"))}">
    <div class="demo-carte">
      <div class="demo-tete"><strong>{t("demo", "titre")}</strong><span>{t("demo", "source")}</span></div>
      <ol>
{etapes_demo}
      </ol>
      <div class="demo-pied"><span class="pastille pret">{t("demo", "pret")}</span>{pastilles}</div>
    </div>
    <figcaption>{t("demo", "legende")}</figcaption>
  </figure>
</section>

<section class="bloc">
  <h2>{t("chiffres", "titre")}</h2>
  <dl class="chiffres">
    <div><dt>{t.vals["pr"]}</dt><dd>{t("chiffres", "pr")}</dd></div>
    <div><dt>{t.vals["releases"]}</dt><dd>{t("chiffres", "releases")}</dd></div>
    <div><dt>{t.vals["taux"]}</dt><dd>{t("chiffres", "taux")}</dd></div>
  </dl>
  <p class="doux">{t("chiffres", "periode")} <a href="agents-ia.html#mesure">{t("chiffres", "lien")}</a></p>
</section>

<section class="bloc">
  <h2>{t("methodes", "titre")}</h2>
  <div class="tuiles">
{tuiles}
  </div>
</section>

<section class="budget">
  <div class="bloc">
    <p class="somme">{t("budget", "somme")}</p>
    <p class="doux">{t("budget", "precision")}</p>
  </div>
  <div class="bloc">
    <h2>{c("achats", "titre")}</h2>
    {achats(c)}
    <p><a href="architecture.html">{t("budget", "lien")}</a></p>
  </div>
</section>

<section class="appel">
  <p>{t("appel", "texte")}</p>
  <a class="bouton premier" href="en-vrai.html">{t("appel", "bouton")}</a>
</section>
"""


def page_en_vrai(t, c, donnees):
    termes = "\n".join(f"    <div><dt>{t.texte(x['terme'])}</dt><dd>{t.texte(x['definition'])}</dd></div>"
                       for x in t.liste("vocabulaire", "termes"))
    return f"""
<section class="bloc">
  <h2>{t("probleme", "titre")}</h2>
  <p>{t("probleme", "texte")}</p>
</section>

<section class="bloc">
  <h2>{t("reponse", "titre")}</h2>
  <ul>
{points(t, "reponse")}
  </ul>
</section>

<section class="bloc">
  <h2>{t("journee", "titre")}</h2>
  {etapes(t, "journee")}
</section>

<div class="replis">
  {repli_points(t, "ce_que_ce_n_est_pas")}
  {repli_texte(t, "pourquoi_maintenant")}
  {repli(t("vocabulaire", "titre"), f'<dl class="lexique">{chr(10)}{termes}{chr(10)}  </dl>')}
</div>
"""


def page_portail(t, c, donnees):
    return f"""
{duo(t)}

<section class="bloc">
  <h2>{t("trajet", "titre")}</h2>
  {etapes(t, "trajet")}
</section>

<div class="replis">
  {repli_points(t, "a_retenir")}
  {repli_texte(t, "premier_echec")}
</div>
"""


def page_golden_paths(t, c, donnees):
    criteres = tableau(t, t.liste("criteres", "colonnes"), t.liste("criteres", "liste"), numeros=True)
    return f"""
{duo(t)}

<section class="bloc">
  <h2>{t("criteres", "titre")}</h2>
  <p class="doux">{t("criteres", "texte")}</p>
</section>

<div class="replis">
  {repli(t("criteres", "repli"), criteres)}
  {repli_points(t, "bac_a_sable")}
  {repli_points(t, "a_retenir")}
</div>
"""


def page_agents_ia(t, c, donnees):
    paliers = "\n".join(
        f'    <div class="palier{" non" if cle == "jamais" else ""}"><h3>{t("paliers", cle, "titre")}</h3><p>{t("paliers", cle, "texte")}</p></div>'
        for cle in ["seul", "avec_un_humain", "jamais"])
    assistant = f"<p>{t('assistant', 'texte')}</p>\n  <ul>\n{points(t, 'assistant')}\n  </ul>"
    return f"""
{duo(t)}

<section class="bloc">
  <h2>{t("paliers", "titre")}</h2>
  <div class="paliers">
{paliers}
  </div>
</section>

<section class="bloc" id="mesure">
  <h2>{t("mesure", "titre")}</h2>
  <p class="doux">{t("mesure", "texte")}</p>
  {graphique(t, donnees)}
  <dl class="chiffres">
    <div><dt>{t.vals["pr"]}</dt><dd>{t("mesure", "pr")}</dd></div>
    <div><dt>{t.vals["taux"]}</dt><dd>{t("mesure", "taux")}</dd></div>
    <div><dt>{t.vals["taux_prod"]}</dt><dd>{t("mesure", "taux_prod")}</dd></div>
  </dl>
</section>

<div class="replis">
  {repli(t("assistant", "titre"), assistant)}
  {repli_texte(t, "journal")}
</div>
"""


def page_observabilite(t, c, donnees):
    return f"""
{duo(t)}

<div class="replis">
  {repli(t("mesures", "titre"), tableau(t, t.liste("mesures", "colonnes"), t.liste("mesures", "lignes")))}
  {repli_points(t, "sans_porte")}
  {repli_texte(t, "sobriete")}
</div>
"""


def page_architecture(t, c, donnees):
    def zone(cle, classe):
        elements = "\n".join(f"        <li>{t.texte(e['nom'])}<span>{t.texte(e['detail'])}</span></li>"
                             for e in t.liste("schema", cle, "elements"))
        return f"""<div class="{classe}">
      <h3>{t("schema", cle, "titre")}</h3>
      <ul>
{elements}
      </ul>
    </div>"""

    return f"""
<section class="bloc">
  <div class="schema">
    {zone("maison", "zone maison")}
    <div class="liaison">
      <svg viewBox="0 0 120 16" aria-hidden="true"><path d="M2 8H112" stroke="currentColor" stroke-width="2" fill="none"/><path d="M104 2l10 6-10 6" stroke="currentColor" stroke-width="2" fill="none"/></svg>
      <span>{t("schema", "liaison")}</span>
    </div>
    {zone("azure", "zone")}
  </div>
</section>

<section class="bloc">
  <h2>{c("achats", "titre")}</h2>
  {achats(c)}
</section>

{duo(t, "part", "reste", labo_a_gauche=True)}

<div class="replis">
  {repli(t("materiel", "titre"), tableau(t, t.liste("materiel", "colonnes"), t.liste("materiel", "lignes")))}
  {repli(t("chemin", "titre"), etapes(t, "chemin"))}
  {repli_points(t, "principes")}
  {repli_texte(t, "gpu")}
</div>
"""


RENDUS = {"index": page_index, "en-vrai": page_en_vrai, "portail": page_portail, "golden-paths": page_golden_paths,
          "agents-ia": page_agents_ia, "observabilite": page_observabilite, "architecture": page_architecture}


# --- Gabarit commun ---------------------------------------------------------------------------

def donnees_structurees(langue, page, t, c):
    site = {"@type": "WebSite", "@id": SITE + "#site", "url": SITE, "name": NOM,
            "inLanguage": [BCP47[l] for l in LANGUES], "description": c("site", "description")}
    adresse = url(langue, page)
    sujet = {"@type": "Thing", "name": "Platform engineering"}
    if page == "index":
        graphe = [site, {"@type": "WebPage", "@id": adresse + "#page", "url": adresse, "name": t("meta", "titre"),
                         "description": t("meta", "description"), "inLanguage": BCP47[langue],
                         "isPartOf": {"@id": SITE + "#site"}, "about": sujet}]
    else:
        graphe = [site,
                  {"@type": "TechArticle", "@id": adresse + "#article", "url": adresse, "headline": t("entete", "titre"),
                   "description": t("meta", "description"), "inLanguage": BCP47[langue], "mainEntityOfPage": adresse,
                   "isPartOf": {"@id": SITE + "#site"}, "about": sujet},
                  {"@type": "BreadcrumbList", "itemListElement": [
                      {"@type": "ListItem", "position": 1, "name": c("navigation", "accueil"), "item": url(langue, "index")},
                      {"@type": "ListItem", "position": 2, "name": t("entete", "fil"), "item": adresse}]}]
        if page == "en-vrai":
            graphe.append({"@type": "DefinedTermSet", "name": t("vocabulaire", "nom_du_lexique"), "inLanguage": BCP47[langue],
                           "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t.texte(x["terme"]), "description": t.texte(x["definition"])}
                                              for x in t.liste("vocabulaire", "termes")]})
    contenu = json.dumps({"@context": "https://schema.org", "@graph": graphe}, ensure_ascii=False, indent=1)
    return contenu.replace("</", "<\\/")


def suite(langue, page, textes, vals, c):
    if page not in ORDRE:
        return ""
    i = ORDRE.index(page)
    morceaux = []
    if i > 0:
        p = ORDRE[i - 1]
        titre = Page(langue, textes[langue][p], vals)("entete", "titre")
        morceaux.append(f'<a href="{p}.html"><span>{c("navigation", "precedent")}</span><strong>{titre}</strong></a>')
    if i < len(ORDRE) - 1:
        s = ORDRE[i + 1]
        titre = Page(langue, textes[langue][s], vals)("entete", "titre")
        morceaux.append(f'<a class="apres-page" href="{s}.html"><span>{c("navigation", "suivant")}</span><strong>{titre}</strong></a>')
    return f'<nav class="suite" aria-label="{html.escape(c("navigation", "voisines_aria"))}">{"".join(morceaux)}</nav>'


def gabarit(langue, page, textes, donnees):
    vals = valeurs(donnees, langue)
    t = Page(langue, textes[langue][page], vals)
    c = Page(langue, textes[langue]["commun"], vals)
    actifs = "" if langue == SOURCE else "../"
    titre, desc = t("meta", "titre"), t("meta", "description")
    courant = ' aria-current="page"'
    liens = "".join(f'<a href="{p}.html"{courant if p == page else ""}>{c("navigation", "pages", p)}</a>' for p in NAV)
    actif = ' aria-current="true"'
    langues = "".join(
        f'<a href="{vers(langue, l, page)}" hreflang="{l}" lang="{l}"{actif if l == langue else ""}>'
        f'{textes[l]["commun"]["code_court"]}</a>' for l in LANGUES)
    alternatives = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{url(l, page)}">' for l in LANGUES)
    alternatives += f'\n<link rel="alternate" hreflang="x-default" href="{url(SOURCE, page)}">'
    autres_locales = "\n".join(f'<meta property="og:locale:alternate" content="{OG_LOCALE[l]}">' for l in LANGUES if l != langue)
    if page == "index":
        tete_page = ""
    else:
        tete_page = f"""<div class="entree">
  <nav class="fil" aria-label="{html.escape(c("navigation", "fil_aria"))}"><a href="index.html">{c("navigation", "accueil")}</a> / <span aria-current="page">{t("entete", "fil")}</span></nav>
  <h1>{t("entete", "titre")}</h1>
  <p class="chapeau">{t("entete", "chapeau")}</p>
</div>"""
    compteur = c("pied", "compteur",
                 poids=f'<strong id="poids">{c("pied", "poids_par_defaut")}</strong>',
                 energie=f'<strong id="energie">{c("pied", "energie_par_defaut")}</strong>',
                 estimation=f'<a href="{ESTIMATION}">{c("pied", "estimation")}</a>')
    return f"""<!doctype html>
<html lang="{langue}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titre, quote=False)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url(langue, page)}">
{alternatives}
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta name="theme-color" content="#000000">
<meta property="og:type" content="{"website" if page == "index" else "article"}">
<meta property="og:site_name" content="{NOM}">
<meta property="og:locale" content="{OG_LOCALE[langue]}">
{autres_locales}
<meta property="og:title" content="{html.escape(titre)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url(langue, page)}">
<meta property="og:image" content="{SITE}assets/partage-{langue}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{html.escape(c("image_partage", "alt"))}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{actifs}assets/icone.svg" type="image/svg+xml">
<link rel="preload" href="{actifs}assets/geist.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{actifs}assets/site.css">
<script type="application/ld+json">
{donnees_structurees(langue, page, t, c)}
</script>
<script src="{actifs}assets/compteur.js" defer></script>
</head>
<body>
<a class="evitement" href="#contenu">{c("navigation", "aller_au_contenu")}</a>
<header class="tete"><div class="cadre">
  <a class="marque" href="index.html" aria-label="{html.escape(c("navigation", "accueil_aria"))}">{ICONES["eclair"]}robalp</a>
  <nav class="liens" aria-label="{html.escape(c("navigation", "pages_aria"))}">{liens}</nav>
  <div class="outils-tete">
    <nav class="langues" aria-label="{html.escape(c("navigation", "langues_aria"))}">{langues}</nav>
    <details class="menu"><summary>{c("navigation", "menu")}</summary><nav aria-label="{html.escape(c("navigation", "menu_aria"))}">{liens}</nav></details>
  </div>
</div></header>

<main id="contenu" class="cadre">
{tete_page}
{RENDUS[page](t, c, donnees).strip()}
{suite(langue, page, textes, vals, c)}
</main>

<footer class="pied"><div class="cadre">
  <p class="compteur">{compteur}</p>
  <div class="pied-liens"><a href="mailto:romain@robalp.fr">romain@robalp.fr</a><a href="https://github.com/greenrabbyte-lab/www">{c("pied", "code_du_site")}</a><span>{c("pied", "sans_donnees")}</span></div>
</div></footer>
</body>
</html>
"""


def page_introuvable(textes, donnees):
    """GitHub Pages ne sert qu'une page 404, à la racine : elle parle les trois langues."""
    lignes = []
    for langue in LANGUES:
        c = Page(langue, textes[langue]["commun"], valeurs(donnees, langue))
        accueil = "/" if langue == SOURCE else f"/{langue}/"
        lignes.append(f'  <p lang="{langue}">{c("introuvable", "texte")} <a href="{accueil}">{c("introuvable", "retour")}</a></p>')
    c = Page(SOURCE, textes[SOURCE]["commun"], valeurs(donnees, SOURCE))
    return f"""<!doctype html>
<html lang="{SOURCE}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c("introuvable", "titre")} | {NOM}</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/assets/icone.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<header class="tete"><div class="cadre"><a class="marque" href="/">{ICONES["eclair"]}robalp</a></div></header>
<main id="contenu" class="cadre">
<div class="entree">
  <h1>{c("introuvable", "titre")}</h1>
{chr(10).join(lignes)}
</div>
</main>
</body>
</html>
"""


def plan_du_site():
    entrees = []
    for page in PAGES:
        alternatives = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url(l, page)}"/>' for l in LANGUES)
        alternatives += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url(SOURCE, page)}"/>'
        for langue in LANGUES:
            entrees.append(f"  <url>\n    <loc>{url(langue, page)}</loc>{alternatives}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(entrees) + "\n</urlset>\n")


ROBOTS_IA = [
    ("OpenAI : entraînement", "GPTBot"), ("OpenAI : index de recherche de ChatGPT", "OAI-SearchBot"),
    ("OpenAI : lecture à la demande d'un utilisateur", "ChatGPT-User"),
    ("Anthropic : entraînement", "ClaudeBot"), ("Anthropic : index de recherche de Claude", "Claude-SearchBot"),
    ("Anthropic : lecture à la demande d'un utilisateur", "Claude-User"),
    ("Perplexity : index", "PerplexityBot"), ("Perplexity : lecture à la demande", "Perplexity-User"),
    ("Google : Gemini (entraînement et ancrage)", "Google-Extended"), ("Apple : modèles d'Apple", "Applebot-Extended"),
    ("Common Crawl, corpus utilisé par de nombreux modèles", "CCBot"),
]


def robots():
    blocs = "\n\n".join(f"# {c}\nUser-agent: {r}\nAllow: /" for c, r in ROBOTS_IA)
    return f"""# www.robalp.fr : site public, sans donnée personnelle. Tout le monde peut l'indexer,
# moteurs de recherche et assistants IA compris.
# Pour rester cité par les assistants sans servir à l'entraînement : passer GPTBot, ClaudeBot,
# Google-Extended, Applebot-Extended et CCBot en « Disallow: / ».

User-agent: *
Allow: /

{blocs}

Sitemap: {SITE}sitemap.xml
"""


def llms(textes, donnees):
    sections = []
    titres = {"fr": "Pages en français", "en": "Pages in English", "de": "Seiten auf Deutsch"}
    for langue in LANGUES:
        vals = valeurs(donnees, langue)
        lignes = []
        for page in PAGES:
            t = Page(langue, textes[langue][page], vals)
            nom = t("meta", "titre").split(" | ")[0]
            lignes.append(f"- [{nom}]({url(langue, page)}): {t('meta', 'description')}")
        sections.append(f"## {titres[langue]}\n\n" + "\n".join(lignes))
    c = Page(SOURCE, textes[SOURCE]["commun"], valeurs(donnees, SOURCE))
    return f"""# Robalp

> {c("site", "description")} Site en français, en anglais et en allemand, sans donnée personnelle.

Le labo sert de démonstration : portail développeur (Port), golden path vers Azure (Terraform, GitHub Actions), agents IA encadrés (délégation à Claude avec journal et paliers), observabilité (Grafana), architecture hybride maison et cloud.

""" + "\n\n".join(sections) + """

## Code

- [Code du site](https://github.com/greenrabbyte-lab/www): pages générées depuis des fichiers de langue, publiées par GitHub Pages
- [Banc de non-régression Keycloak](https://github.com/greenrabbyte-lab/keycloak-non-regression): outil public du labo
"""


# --- Point d'entrée ---------------------------------------------------------------------------

def main():
    parametres = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parametres.add_argument("--sortie", default=str(RACINE / "_site"))
    sortie = Path(parametres.parse_args().sortie)

    donnees, textes = charger()
    erreurs = verifier(donnees, textes)
    if erreurs:
        print("Fichiers de langue incohérents :", *erreurs, sep="\n  ", file=sys.stderr)
        sys.exit(1)

    if sortie.exists():
        shutil.rmtree(sortie)
    shutil.copytree(RACINE / "assets", sortie / "assets")
    shutil.copy(RACINE / "CNAME", sortie / "CNAME")
    pages_html = {}
    for langue in LANGUES:
        dossier = sortie if langue == SOURCE else sortie / langue
        dossier.mkdir(parents=True, exist_ok=True)
        for page in PAGES:
            pages_html[dossier / f"{page}.html"] = gabarit(langue, page, textes, donnees)
    pages_html[sortie / "404.html"] = page_introuvable(textes, donnees)

    for chemin, contenu in pages_html.items():
        controle = Equilibre()
        controle.feed(contenu)
        if controle.erreurs or controle.pile:
            sys.exit(f"HTML mal formé dans {chemin.relative_to(sortie)} : {controle.erreurs or controle.pile}")
        chemin.write_text(contenu, encoding="utf-8")
    (sortie / "sitemap.xml").write_text(plan_du_site(), encoding="utf-8")
    (sortie / "robots.txt").write_text(robots(), encoding="utf-8")
    (sortie / "llms.txt").write_text(llms(textes, donnees), encoding="utf-8")
    print(f"{len(pages_html)} pages écrites dans {sortie}")


if __name__ == "__main__":
    main()
