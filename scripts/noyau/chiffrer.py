# -*- coding: utf-8 -*-
# CHIFFRER — mesurer ce qui, dans les couts et les effets, se laisse suivre.
#
# POURQUOI. Sur 3 974 aretes du tissu, 1 048 sont FLOUES : presentes, non
# suivables. Elles se concentrent sur quatre natures, et toutes les quatre a
# 100% :
#     coute_chiffre  773   ce qu'une action coute
#     devie          103   les conditions de deviation du canon
#     repond          57   les declencheurs si/alors
#     contredit       53   les tensions
#
# C'est le plafond du modele : aucune requete ne franchira ces aretes tant
# qu'elles restent en prose. Mais « en prose » ne veut pas dire « informe » —
# beaucoup portent deja un chiffre, une unite et une duree, et n'attendent
# qu'une grammaire pour se laisser lire.
#
# CE SCRIPT CLASSE, IL NE CONVERTIT PAS. Il rend, pour chaque arete floue, ce
# qu'on peut en tirer mecaniquement et ce qui demande un jugement. Le partage
# est le meme que partout : ce qui est arithmetique se calcule, le reste monte.
# Convertir sans avoir classe serait ecrire 773 chiffres au jugement.
#
# Ne modifie rien. Depose sa proposition dans etat/tissu/.
import io
import json
import os
import re
import sys
import collections

from etat.expose import tables  # LA PORTE de etat/ : le depot atomique de la proposition

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")
TISSU = os.path.join(ETAT, "tissu")

# --------------------------------------------------------- la grammaire
# Tiree des couts reellement ecrits, pas inventee. Exemples du corpus :
#   « **1 homme 3 jours** · hommes · une fois »
#   « **1 quille 2 jours** + 8 hommes 2 jours · coques »
#   « **le quai entier 3 jours** — onze patrons deroutes, **≈30 dragons** »
#   « **neant** · — · une fois »            « **a chiffrer** »
#   « **Cede — le cout est desormais chez dame Alys Grive (6000).** »

NOMBRES = {"un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
           "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "douze": 12,
           "quinze": 15, "vingt": 20, "trente": 30, "quarante": 40}

UNITES = ("homme", "hommes", "quille", "quilles", "coque", "coques", "cheval",
          "chevaux", "corbeau", "corbeaux", "compagnie", "compagnies",
          "emissaire", "emissaires", "clerc", "clercs", "barque", "barques")

MONNAIE = ("dragon", "dragons", "cerf", "cerfs", "sol", "sols")

NEANT = re.compile(r"\b(n[ée]ant|rien|z[ée]ro|gratuit)\b", re.I)
ACHIFFRER = re.compile(r"\b(à|a) chiffrer\b", re.I)
CEDE = re.compile(r"\bc[ée]d[ée]\b", re.I)
ADRESSE = re.compile(r"\b([a-z][a-z0-9-]{3,}\.[a-z][a-z0-9-]{2,})\b")
DUREE = re.compile(r"(\d+)\s*(jour|jours|matin[ée]e|matinees|demi-jour|"
                   r"soir[ée]e|heures?|lune|lunes)", re.I)


def nombre(t):
    t = t.strip().lower()
    if t.isdigit():
        return int(t)
    return NOMBRES.get(t)


def plat(t):
    import unicodedata
    t = unicodedata.normalize("NFD", str(t or ""))
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def lire_quantites(texte):
    """<nombre> <unite> [<nombre> jours] — ce qu'une action mange."""
    t = plat(texte)
    out = []
    motif = r"(\d+|" + "|".join(NOMBRES) + r")\s+(" + "|".join(UNITES) + r")"
    for m in re.finditer(motif, t):
        n = nombre(m.group(1))
        if n is None:
            continue
        q = {"combien": n, "quoi": m.group(2)}
        suite = t[m.end():m.end() + 24]
        d = DUREE.search(suite)
        if d:
            q["pendant"] = int(d.group(1))
            q["unite_temps"] = d.group(2)
        out.append(q)
    for m in re.finditer(r"(\d+)\s*(" + "|".join(MONNAIE) + r")", t):
        out.append({"combien": int(m.group(1)), "quoi": m.group(2)})
    return out


def classer(texte):
    """Rend (classe, ce qu'on en tire). Cinq classes, pas une de plus."""
    t = str(texte or "")
    if not t.strip():
        return "vide", {}
    a = ADRESSE.search(plat(t))
    if a:
        return "cite_une_mesure", {"adresse": a.group(1)}
    if CEDE.search(t):
        return "cede", {}
    if ACHIFFRER.search(t):
        return "declare_a_chiffrer", {}
    q = lire_quantites(t)
    if q:
        return "chiffrable", {"quantites": q}
    if NEANT.search(t):
        return "declare_neant", {"quantites": []}
    return "prose", {}


def lire_tissu():
    p = os.path.join(TISSU, "aretes.jsonl")
    if not os.path.isfile(p):
        sys.exit("Aucun tissu. Lance d'abord : python scripts/tisser.py --ecrire")
    return [json.loads(l) for l in io.open(p, encoding="utf-8") if l.strip()]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    A = [a for a in lire_tissu() if a.get("flou")]

    par_nature = collections.defaultdict(collections.Counter)
    tires = []
    for a in A:
        cl, quoi = classer(a.get("texte"))
        par_nature[a["nature"]][cl] += 1
        if cl in ("chiffrable", "cite_une_mesure", "declare_neant"):
            tires.append(dict(a, classe=cl, tire=quoi))

    print("CHIFFRER — ce qui, dans le flou, se laisse deja lire")
    print("  {} aretes floues examinees".format(len(A)))
    print()
    ordre = ["chiffrable", "cite_une_mesure", "declare_neant",
             "declare_a_chiffrer", "cede", "prose", "vide"]
    entete = "  {:<16}".format("nature") + "".join(
        "{:>12}".format(c[:12]) for c in ordre)
    print(entete)
    print("  " + "-" * (len(entete) - 2))
    tot = collections.Counter()
    for nat in sorted(par_nature, key=lambda k: -sum(par_nature[k].values())):
        c = par_nature[nat]
        tot.update(c)
        print("  {:<16}".format(nat[:16]) + "".join(
            "{:>12}".format(c.get(k, 0) or "") for k in ordre))
    print("  " + "-" * (len(entete) - 2))
    print("  {:<16}".format("TOTAL") + "".join(
        "{:>12}".format(tot.get(k, 0) or "") for k in ordre))
    print()

    recuperable = tot["chiffrable"] + tot["cite_une_mesure"] + tot["declare_neant"]
    print("  RECUPERABLE MECANIQUEMENT : {} sur {}  ({:.0f}%)".format(
        recuperable, len(A), 100.0 * recuperable / max(1, len(A))))
    print("  A JUGER : {} — dont {} se declarent eux-memes « a chiffrer »".format(
        tot["prose"] + tot["declare_a_chiffrer"] + tot["cede"],
        tot["declare_a_chiffrer"]))
    print()
    print("  Un cout qui se declare « a chiffrer » n'est pas un echec de")
    print("  lecture : c'est un homme qui a dit qu'il ne savait pas encore.")
    print("  On ne le convertit pas — on le compte.")
    print()

    print("ECHANTILLON DE CE QU'ON TIRE")
    for a in tires[:12]:
        q = a["tire"].get("quantites") or a["tire"].get("adresse")
        print("  [{}] {} -> {}".format(a["classe"][:14], str(a["de"])[:16],
                                       json.dumps(q, ensure_ascii=False)[:70]))
        print("      {}".format((a.get("texte") or "")[:92]))
    print()

    print("CE QUI RESTE EN PROSE PURE — les dix premiers")
    n = 0
    for a in A:
        cl, _ = classer(a.get("texte"))
        if cl != "prose":
            continue
        n += 1
        if n > 10:
            break
        print("  [{}] {}".format(a["nature"][:12], (a.get("texte") or "")[:96]))

    p = tables.ecrire_lignes(os.path.join(TISSU, "couts-lus.jsonl"), tires)
    print()
    print("Proposition deposee : {} ({} aretes lues).".format(
        os.path.relpath(p, RACINE), len(tires)))
    print("Rien n'a ete ecrit dans etat/ : c'est une lecture, pas une conversion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
