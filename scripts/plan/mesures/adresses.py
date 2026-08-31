# -*- coding: utf-8 -*-
"""ADRESSES — la sortie utf-8, les comparaisons de titres, la lecture de
l'etat, la resolution des adresses `main.mesure` et les offices du plan.
"""
import io
import os
import re
import sys
import unicodedata

import bibliotheque
import documents_maison

# Trois etages de plus qu'a la racine : scripts/plan/mesures/.
racine = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
decoupage_md = os.path.join(racine, "docs", "decoupage.md")

LIVRE_OFFICES = "plan-offices"


# ─────────────────────────────────────────────── la sortie, sous Windows
def forcer_utf8():
    """Le shell d'ici est en cp1252 : sans ca, un emoji tue le script."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        return
    except Exception:
        pass
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")
    except Exception:
        pass


def dire(texte=u""):
    try:
        sys.stdout.write(texte + u"\n")
    except UnicodeEncodeError:
        sys.stdout.write(texte.encode("ascii", "replace").decode("ascii") + u"\n")


# ─────────────────────────────────────────────── comparer des titres a emoji
def nu(t):
    """Le texte d'une cellule, sans gras ni blancs superflus."""
    s = u"" if t is None else t if isinstance(t, str) else str(t)
    s = s.replace(u"**", u"")
    return u" ".join(s.split())


def sans_emoji(s):
    """Un titre de colonne comparable : les emoji et les selecteurs sautent."""
    return u" ".join(u"".join(c for c in nu(s)
                              if unicodedata.category(c) != "So"
                              and c != u"️").split())


def sans_accents(t):
    t = unicodedata.normalize("NFD", nu(t))
    return u"".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def colonne(colonnes, motif):
    """Index de la premiere colonne dont le titre nu colle au motif."""
    for i, c in enumerate(colonnes or []):
        if re.search(motif, sans_accents(sans_emoji(c)), re.I):
            return i
    return None


def cellules_de(ligne):
    if isinstance(ligne, list):
        return [nu(x) for x in ligne]
    return [nu(x) for x in ((ligne or {}).get("cellules") or [])]


def tables_de(livre):
    """Les deux formes d'un livre : a plat, ou en tables. Comme couverture.py."""
    if livre.get("tables"):
        return livre["tables"]
    return [{"titre": livre.get("titre"),
             "colonnes": livre.get("colonnes"),
             "lignes": livre.get("lignes")}]


# ─────────────────────────────────────────────── lire l'etat
def charger_livres():
    return bibliotheque.charger(os.path.join(racine, "etat"))


def charger_mains():
    return documents_maison.charger_mains(os.path.join(racine, "etat"))


def index_des_mesures(mains):
    """adresse `<main>.<mesure>` -> (main, mesure). Meme cle que tick.py."""
    index = {}
    for act in mains:
        for mes in act.get("mesure") or []:
            if act.get("id") and mes.get("id"):
                index[u"%s.%s" % (act["id"], mes["id"])] = (act, mes)
    return index


# ─────────────────────────────────────────────── les adresses dans le texte
# Entre backticks : `main-id.mesure-id`, ou la forme abregee `.mesure-id`
# qui herite de l'main de l'adresse precedente sur la MEME cellule.
BACKTICK = re.compile(u"`([^`]{1,120})`")
ADRESSE = re.compile(u"^(\\.?)([a-z0-9]+(?:-[a-z0-9]+)*)(?:\\.([a-z0-9]+(?:-[a-z0-9]+)*))?$")


def adresses_dans(texte, mains_connues=None, autoriser_inconnues=True):
    """Rend les adresses de mesure écrites dans une cellule.

    Hors d'une colonne explicitement consacrée aux mesures, un identifiant
    inconnu est bien plus souvent une référence de code (``h.l1``,
    ``process.argv``) qu'une adresse de compte. Les mains connues restent
    reconnues partout ; les inconnues ne sont gardées que lorsque l'appelant
    autorise leur diagnostic.
    """
    trouvees = []
    derniere_main = None
    for brut in BACKTICK.findall(nu(texte)):
        m = ADRESSE.match(brut.strip())
        if not m:
            continue
        point, un, deux = m.group(1), m.group(2), m.group(3)
        if deux:
            if (mains_connues is not None and un not in mains_connues
                    and not autoriser_inconnues):
                derniere_main = None
                continue
            derniere_main = un
            trouvees.append((u"%s.%s" % (un, deux), brut.strip()))
        elif point:
            # forme abregee : `.solde-due`
            if derniere_main:
                trouvees.append((u"%s.%s" % (derniere_main, un), brut.strip()))
            elif autoriser_inconnues:
                trouvees.append((None, brut.strip()))
        # un mot seul sans point n'est pas une adresse : on le laisse passer
    return trouvees


# ─────────────────────────────────────────────── les offices du plan
def lire_offices(livres):
    """Les lignes du livre plan-offices, chacune avec ce que sa case mesure cite."""
    offices = []
    for livre in livres:
        if livre.get("id") != LIVRE_OFFICES:
            continue
        for table in tables_de(livre):
            cols = table.get("colonnes") or []
            i_num = colonne(cols, u"^n°|^no$|^n$") or 0
            i_nom = colonne(cols, u"office")
            i_tit = colonne(cols, u"titulaire")
            i_mes = colonne(cols, u"mesure")
            if i_mes is None:
                continue
            for ligne in table.get("lignes") or []:
                c = cellules_de(ligne)
                if len(c) <= i_mes or not any(c):
                    continue
                case = c[i_mes]
                offices.append({
                    "numero": c[i_num] if i_num is not None and i_num < len(c) else u"",
                    "nom": c[i_nom] if i_nom is not None and i_nom < len(c) else u"",
                    "titulaire": c[i_tit] if i_tit is not None and i_tit < len(c) else u"",
                    "case": case,
                    "adresses": adresses_dans(case),
                })
    return offices


def citations_ailleurs(livres, mains_connues=None):
    """Toute adresse citee dans un autre livre que le registre des offices."""
    citations = []
    for livre in livres:
        if livre.get("id") == LIVRE_OFFICES:
            continue
        for table in tables_de(livre):
            cols = table.get("colonnes") or []
            for n, ligne in enumerate(table.get("lignes") or [], 1):
                c = cellules_de(ligne)
                for i, cell in enumerate(c):
                    titre_colonne = sans_accents(sans_emoji(cols[i])) \
                        if i < len(cols) else u""
                    colonne_mesure = bool(re.search(
                        u"mesure|compte|adresse", titre_colonne, re.I))
                    for adresse, brut in adresses_dans(
                            cell, mains_connues, autoriser_inconnues=colonne_mesure):
                        citations.append({
                            "livre_id": livre.get("id") or u"?",
                            "livre": nu(livre.get("titre")),
                            "table": nu(table.get("titre")),
                            "ligne": n,
                            "repere": c[0] if c else u"",
                            "colonne": sans_emoji(cols[i]) if i < len(cols) else u"",
                            "adresse": adresse,
                            "brut": brut,
                        })
    return citations

