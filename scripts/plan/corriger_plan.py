# -*- coding: utf-8 -*-
# Applique une proposition de correction du PLAN a etat/books.json.
#
# POURQUOI. Le plan de la Prise de Port-Real est un graphe : chaque piece porte
# un numero et pointe vers d'autres par des colonnes de lien. Quand un de ces
# numeros ne designe rien, le lien n'existe pas pour la machine et personne ne
# s'en apercoit a la lecture — la chaine a l'air tenue, elle est coupee. Ces
# renvois dans le vide se reparent a la CELLULE, une par une, et pas autrement.
#
# CE SCRIPT N'A AUCUN JUGEMENT. Il ne cherche pas la bonne cible, il ne devine
# rien : il prend une proposition deja arbitree, ecrite dans etat/, et
# il la pose. Toute l'intelligence est dans le fichier de proposition ; ici il
# n'y a qu'un poseur de cellules, et trois gardes.
#
# TROIS GARDES, et c'est pour cela qu'il existe plutot qu'une edition a la main :
#   1. IL RELIT etat/books.json AU MOMENT DE L'APPLICATION. Une autre session de
#      jeu ecrit dans ce fichier ; travailler sur une copie prise plus tot, c'est
#      ecraser le travail d'un autre.
#   2. IL REFUSE SI LA CELLULE NE CONTIENT PAS `avant`. L'etat a bouge sous lui :
#      on s'arrete, on ne repare pas au jugé, et RIEN n'est ecrit — le lot est
#      indivisible.
#   3. IL EST IDEMPOTENT. Une cellule qui contient deja `apres` est annoncee et
#      laissee tranquille ; un ajout deja present a l'identique aussi. Relancer
#      ne casse rien.
#
# Il ecrit par ADRESSE — livre + table + numero de ligne + nom de colonne — et
# jamais en reconstruisant le fichier depuis une structure a lui : il charge le
# JSON, touche les cellules visees, et redonne le tout. Ce qu'il n'a pas nomme
# n'a pas bouge.
#
# BLANC PAR DEFAUT, comme scripts/appliquer.py. Il dit ce qu'il ferait, ligne
# par ligne, et n'ecrit qu'avec --vraiment.
#
# Usage :
#     python scripts/plan/corriger_plan.py etat/correction-plan-<horodatage>.json
#     python scripts/plan/corriger_plan.py <fichier> --vraiment
#
# Apres application : relancer `python scripts/couverture.py`, qui refait les
# blocs calcules en tete de chaque cahier, puis `python scripts/etat_du_plan.py`.
import io
import json
import os
import re
import sys
import unicodedata

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import bibliotheque

racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVRES = os.path.join(racine, "etat", "books.json")
STAGING = os.path.join(racine, "etat")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ADRESSE = re.compile(r"^\s*(\d{3,6})(?:\b|\s)")


# ─────────────────────────────────────────────── lire les cellules comme couverture.py
def nu(t):
    """Le texte d'une cellule, sans gras ni fioritures — meme lecture que
    couverture.py, pour qu'une comparaison ici veuille dire la meme chose
    qu'un lien la-bas."""
    s = u"" if t is None else t if isinstance(t, str) else str(t)
    s = s.replace(u"**", u"")
    s = u"".join(c for c in s if c not in u"　└")
    return u" ".join(s.split())


def sans_emoji(s):
    return u" ".join(u"".join(c for c in nu(s)
                              if unicodedata.category(c) != "So"
                              and c != u"️").split())


def cellules(ligne):
    """Une ligne est tantot une liste, tantot {"cellules": [...]}. On rend la
    LISTE VIVE, pour que l'ecriture porte sur le document et non sur une copie."""
    if isinstance(ligne, list):
        return ligne
    return ligne.setdefault("cellules", [])


def numero_de(cellule):
    """Le numero d'adresse est le premier nombre de la cellule, jamais un
    numero seulement cite dans une ligne morte ou une note."""
    m = ADRESSE.match(nu(cellule))
    return m.group(1) if m else None


# ─────────────────────────────────────────────── trouver une adresse
def livre_de(livres, ident):
    for b in livres:
        if b.get("id") == ident:
            return b
    return None


def table_de(livre, titre):
    """`titre` a None designe un registre a plat : le livre lui-meme fait table."""
    if titre is None:
        # la liste des lignes doit rester CELLE DU LIVRE : un ajout se pose
        # dedans, pas dans une copie qu'on jetterait a la sortie.
        if livre.get("lignes") is None:
            livre["lignes"] = []
        return {"colonnes": livre.get("colonnes") or [],
                "lignes": livre["lignes"]}
    for t in (livre.get("tables") or []):
        if t.get("titre") == titre:
            return t
    # repli : le titre porte des emojis et des espaces qui se copient mal
    for t in (livre.get("tables") or []):
        if sans_emoji(t.get("titre") or u"").lower() == sans_emoji(titre).lower():
            return t
    return None


def index_colonne(table, nom):
    colonnes = table.get("colonnes") or []
    for i, c in enumerate(colonnes):
        if c == nom:
            return i
    for i, c in enumerate(colonnes):
        if sans_emoji(c).lower() == sans_emoji(nom).lower():
            return i
    return None


def lignes_du_numero(table, numero):
    """Toutes les lignes dont la colonne 0 porte ce numero. Plus d'une : on
    refuse — une adresse ambigue n'est pas une adresse."""
    trouvees = []
    for ligne in (table.get("lignes") or []):
        c = cellules(ligne)
        if c and numero_de(c[0]) == numero:
            trouvees.append(ligne)
    return trouvees


def numero_pris(livres, numero):
    """Ou ce numero est-il deja pose comme N° de ligne, dans tout le graphe ?
    Rend la liste des adresses (id de livre, titre de table)."""
    ou = []
    for b in livres:
        tables = b.get("tables") or [{"titre": None,
                                      "colonnes": b.get("colonnes"),
                                      "lignes": b.get("lignes")}]
        for t in tables:
            for ligne in (t.get("lignes") or []):
                c = cellules(ligne)
                if c and numero_de(c[0]) == numero:
                    ou.append((b.get("id"), t.get("titre")))
    return ou


# ─────────────────────────────────────────────── preparer le lot
def adresse(c):
    return u"%s / %s / N° %s / %s" % (c.get("livre"),
                                      c.get("table") or u"(registre a plat)",
                                      c.get("numero"), c.get("colonne"))


def preparer_correction(livres, c):
    """(action, detail) — action vaut 'poser', 'deja', ou 'refus'."""
    b = livre_de(livres, c.get("livre"))
    if b is None:
        return "refus", u"livre introuvable : %s" % c.get("livre")
    t = table_de(b, c.get("table"))
    if t is None:
        return "refus", u"table introuvable : %s" % (c.get("table"),)
    i = index_colonne(t, c.get("colonne"))
    if i is None:
        return "refus", u"colonne introuvable : %s (colonnes : %s)" % (
            c.get("colonne"), u" | ".join(t.get("colonnes") or []))
    trouvees = lignes_du_numero(t, c.get("numero"))
    if not trouvees:
        return "refus", u"aucune ligne de N° %s" % c.get("numero")
    if len(trouvees) > 1:
        return "refus", u"%d lignes portent le N° %s — adresse ambigue" % (
            len(trouvees), c.get("numero"))
    cells = cellules(trouvees[0])
    if i >= len(cells):
        return "refus", u"la ligne n'a que %d cellules, la colonne est la %de" % (
            len(cells), i + 1)
    valeur = cells[i]
    # Une cellule de plan peut porter plusieurs milliers de caractères. Pour
    # corriger une adresse au milieu, recopier toute la cellule dans la
    # proposition crée une seconde version de la prose et une occasion de la
    # tronquer. Le remplacement borné garde les mêmes garanties : fragment
    # attendu exactement une fois, état relu au dernier moment, lot atomique.
    if "avant_dans" in c or "apres_dans" in c:
        avant_dans, apres_dans = c.get("avant_dans"), c.get("apres_dans")
        if not isinstance(avant_dans, str) or not avant_dans \
                or not isinstance(apres_dans, str):
            return "refus", u"avant_dans/apres_dans doivent être deux textes non vides"
        if apres_dans in valeur:
            c["_apres_calcule"] = valeur
            return "deja", (cells, i, valeur)
        compte = valeur.count(avant_dans)
        if compte != 1:
            return "refus", u"le fragment attendu apparaît %d fois, il en faut exactement une" % compte
        apres = valeur.replace(avant_dans, apres_dans, 1)
    else:
        apres = c.get("apres")
        if nu(valeur) != nu(c.get("avant")):
            return "refus", (u"la cellule ne contient pas ce qui etait attendu.\n"
                             u"        attendu : %s\n        trouve  : %s"
                             % (json.dumps(c.get("avant"), ensure_ascii=False),
                                json.dumps(valeur, ensure_ascii=False)))
    c["_apres_calcule"] = apres
    if nu(valeur) == nu(apres):
        return "deja", (cells, i, valeur)
    return "poser", (cells, i, valeur)


def preparer_ajout(livres, a):
    b = livre_de(livres, a.get("livre"))
    if b is None:
        return "refus", u"livre introuvable : %s" % a.get("livre")
    t = table_de(b, a.get("table"))
    if t is None:
        return "refus", u"table introuvable : %s" % (a.get("table"),)
    colonnes = t.get("colonnes") or []
    ligne = a.get("ligne") or []
    if len(ligne) != len(colonnes):
        return "refus", u"la ligne a %d cellules, la table en attend %d (%s)" % (
            len(ligne), len(colonnes), u" | ".join(colonnes))
    numero = a.get("numero")
    if numero_de(ligne[0] if ligne else u"") != numero:
        return "refus", u"la premiere cellule (%s) ne porte pas le N° %s" % (
            json.dumps(ligne[0] if ligne else u"", ensure_ascii=False), numero)
    deja = numero_pris(livres, numero)
    if deja:
        # deja pose : idempotent si c'est bien NOTRE ligne, refus sinon
        existantes = lignes_du_numero(t, numero)
        if len(deja) == 1 and existantes and \
                [nu(x) for x in cellules(existantes[0])] == [nu(x) for x in ligne]:
            return "deja", existantes[0]
        return "refus", (u"le N° %s est deja pris ailleurs dans le graphe : %s"
                         % (numero, u" · ".join(
                             u"%s/%s" % (i, tt or u"(a plat)") for i, tt in deja)))
    return "poser", t


# ─────────────────────────────────────────────── mise en page
def entete(titre):
    sys.stdout.write(u"\n" + titre + u"\n" + u"─" * 96 + u"\n")


AIDE = u"""corriger_plan.py — pose une proposition de correction du plan.

    python scripts/plan/corriger_plan.py etat/correction-plan-<horodatage>.json
    python scripts/plan/corriger_plan.py <fichier> --vraiment

Blanc par defaut : il dit ce qu'il ferait et n'ecrit rien. Il relit
etat/books.json au moment de l'application, refuse si une cellule a bouge, et
ne touche pas a celle qui porte deja la valeur voulue.
"""


def main():
    args = sys.argv[1:]
    if not args or "--aide" in args or "-h" in args or "--help" in args:
        sys.stdout.write(AIDE)
        return 0
    vraiment = "--vraiment" in args
    chemin = next((a for a in args if not a.startswith("--")), None)
    if chemin is None:
        sys.stdout.write(AIDE)
        return 2
    if not os.path.isfile(chemin):
        chemin = os.path.join(STAGING, os.path.basename(chemin))
    if not os.path.isfile(chemin):
        sys.stdout.write(u"proposition introuvable : %s\n" % args[0])
        return 2

    with io.open(chemin, encoding="utf-8") as f:
        prop = json.load(f)

    # GARDE 1 — on relit la bibliothèque MAINTENANT, pas plus tôt. La session
    # gardera cette version pour refuser une écriture concurrente du même livre.
    session = bibliotheque.ouvrir(STAGING)
    livres = session.livres

    corrections = prop.get("corrections") or []
    ajouts = prop.get("ajouts") or []
    non_corrige = prop.get("non_corrige") or []

    sys.stdout.write(u"Proposition : %s\n" % os.path.basename(chemin))
    if prop.get("quoi"):
        sys.stdout.write(u"%s\n" % prop["quoi"])
    sys.stdout.write(u"\n%d correction(s) · %d ajout(s) · %d laissee(s) de cote\n"
                     % (len(corrections), len(ajouts), len(non_corrige)))

    a_poser, a_faire, refus, deja = [], [], [], []

    # les ajouts d'abord : une correction peut pointer sur une piece qu'ils creent
    entete(u"➕ LES AJOUTS — pieces creees")
    if not ajouts:
        sys.stdout.write(u"  — aucun.\n")
    for a in ajouts:
        quoi, detail = preparer_ajout(livres, a)
        tete = u"  N° %-7s %s / %s" % (a.get("numero"), a.get("livre"),
                                       a.get("table") or u"(registre a plat)")
        if quoi == "refus":
            sys.stdout.write(tete + u"\n     ⛔ REFUS : %s\n" % detail)
            refus.append(u"ajout N° %s — %s" % (a.get("numero"), detail))
            continue
        if quoi == "deja":
            sys.stdout.write(tete + u"\n     ✓ deja present a l'identique — rien a faire\n")
            deja.append(u"ajout N° %s" % a.get("numero"))
            continue
        sys.stdout.write(tete + u"\n")
        for i, c in enumerate(detail.get("colonnes") or []):
            sys.stdout.write(u"     %-34s = %s\n" % (nu(c), nu(a["ligne"][i])))
        if a.get("pourquoi"):
            sys.stdout.write(u"     motif : %s\n" % a["pourquoi"])
        a_faire.append((detail, a))

    entete(u"✏️ LES CORRECTIONS — cellules reecrites")
    if not corrections:
        sys.stdout.write(u"  — aucune.\n")
    for c in corrections:
        quoi, detail = preparer_correction(livres, c)
        tete = u"  %s" % adresse(c)
        if quoi == "refus":
            sys.stdout.write(tete + u"\n     ⛔ REFUS : %s\n" % detail)
            refus.append(u"%s — %s" % (adresse(c), detail))
            continue
        if quoi == "deja":
            sys.stdout.write(tete + u"\n     ✓ contient deja %s — rien a faire\n"
                             % json.dumps(c.get("_apres_calcule"), ensure_ascii=False))
            deja.append(adresse(c))
            continue
        cells, i, valeur = detail
        sys.stdout.write(tete + u"\n     avant : %s\n     apres : %s\n"
                         % (json.dumps(valeur, ensure_ascii=False),
                            json.dumps(c.get("_apres_calcule"), ensure_ascii=False)))
        sys.stdout.write(u"     certitude : %s\n" % (c.get("certitude") or u"—"))
        if c.get("pourquoi"):
            sys.stdout.write(u"     motif : %s\n" % c["pourquoi"])
        a_poser.append((cells, i, c))

    if non_corrige:
        entete(u"⚠️ LAISSE DE COTE — a trancher a la main, rien n'est touche")
        for n in non_corrige:
            sys.stdout.write(u"  %s / %s / N° %s / %s = %s\n"
                             % (n.get("livre"), n.get("table") or u"(a plat)",
                                n.get("numero"), n.get("colonne"),
                                json.dumps(n.get("valeur_actuelle"),
                                           ensure_ascii=False)))
            if n.get("pourquoi"):
                sys.stdout.write(u"     %s\n" % n["pourquoi"])

    for r in (prop.get("remarques") or []):
        sys.stdout.write(u"\n  ℹ %s\n" % r)

    entete(u"\U0001f9ee LE COMPTE")
    sys.stdout.write(u"  %d a poser · %d ajout(s) a faire · %d deja en place · "
                     u"%d refus\n" % (len(a_poser), len(a_faire), len(deja),
                                      len(refus)))

    # GARDE 2 — un seul refus arrete tout le lot. Rien n'est ecrit.
    if refus:
        sys.stdout.write(u"\n== REFUS (%d) — RIEN N'A ETE ECRIT ==\n" % len(refus))
        for r in refus:
            sys.stdout.write(u"  ⛔ %s\n" % r)
        sys.stdout.write(u"\nL'etat a bouge sous cette proposition, ou une adresse "
                         u"est fausse. Relis etat/books.json et refais la "
                         u"proposition — ne repare pas au juge.\n")
        return 1

    if not (a_poser or a_faire):
        sys.stdout.write(u"\nTout est deja en place : rien a faire.\n")
        return 0

    if not vraiment:
        sys.stdout.write(u"\nBlanc : rien n'a ete ecrit. Relance avec --vraiment "
                         u"pour appliquer.\n")
        return 0

    for table, a in a_faire:
        table.setdefault("lignes", []).append({"cellules": list(a["ligne"])})
    for cells, i, c in a_poser:
        cells[i] = c["_apres_calcule"]
    try:
        session.sauver()
    except bibliotheque.BibliothequeModifiee as exc:
        sys.stdout.write(u"\n⛔ %s\n" % exc)
        return 1

    sys.stdout.write(u"\nApplique dans etat/books.json : %d cellule(s) reecrite(s), "
                     u"%d ligne(s) ajoutee(s).\n" % (len(a_poser), len(a_faire)))
    sys.stdout.write(u"Refais les couvertures : python scripts/couverture.py\n")
    sys.stdout.write(u"Puis relis le plan    : python scripts/etat_du_plan.py\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
