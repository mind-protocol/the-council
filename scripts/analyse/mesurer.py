# -*- coding: utf-8 -*-
# MESURER — la part des repliques du jour qui ne portent la trace d'aucune
# pensee. Un seul chiffre, et c'est voulu.
#
# CE QUI A ETE JETE, ET POURQUOI. L'ancien mesurait six choses : l'excitation
# de chaque homme, l'etat de ses affaires, ses conclusions mures, ses etapes
# seches, ses trajets, et la part de ses pensees marquees `servie`. Cinq de ces
# six ne mesuraient rien de reel :
#
#   - l'excitation etait un compteur qui montait sans sources et retombait d'un
#     point par jour ; il disait qui avait envie de parler, jamais qui avait de
#     quoi ;
#   - l'etat `mur` d'une conclusion se calculait au lieu de se constater — une
#     conclusion est ecrite ou elle ne l'est pas ;
#   - le marquage `servie` etait tenu 11 fois sur 613. Son absence faisait
#     conclure a 98 % de travail perdu, ce qui etait faux et decourageant.
#
# CE QUI RESTE EST LA SEULE FAUTE QUE LA CHAINE EXISTAIT POUR ATTRAPER : une
# replique qui n'a AUCUNE pensee derriere elle — un homme qui commente la salle
# parce que commenter la salle ressemble a avoir une raison d'agir. C'est le
# defaut que ce jeu produit quand on le laisse faire, et le seul qui se voie.
#
# LE RECOUPEMENT EST APPROCHE, ET C'EST ASSUME. On n'a pas de lien ecrit entre
# une replique et la pensee qui l'a produite. On recoupe par le VOCABULAIRE
# RARE : les mots qu'un texte partage avec une pensee et que presque personne
# d'autre n'emploie — un chiffre, un nom, un lieu, un metier. Trois mots rares
# partages suffisent a dire « celle-la vient de la ».
#
# Usage :
#   python scripts/analyse/mesurer.py                 le jour du monde
#   python scripts/analyse/mesurer.py --jours 3       la fenetre de trois jours
#   python scripts/analyse/mesurer.py --qui gerardys  un homme seul
#   python scripts/analyse/mesurer.py --orphelines    les repliques sans amont, en clair
import argparse
import io
import json
import math
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")

# ------------------------------------------------------------- les chiffres
RECOUPEMENT = 3        # mots rares partages pour lier une replique a une pensee
RARETE = 0.08          # un mot est rare s'il est dans moins de 8% des textes
MOT_MIN = 4            # longueur minimale d'un mot retenu (les chiffres passent)
FENETRE = 1            # jours mesures par defaut, celui du monde inclus

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12

DIT = ("replique",)
FAIT = ("geste",)


def jour_absolu(date):
    if not isinstance(date, dict):
        return None
    try:
        return ((int(date["annee"]) * LUNES_PAR_AN + int(date["lune"]) - 1)
                * JOURS_PAR_LUNE + int(date["jour"]) - 1)
    except (TypeError, ValueError, KeyError):
        return None


def fmt(date):
    if not isinstance(date, dict):
        return "?"
    return "{}e j., {}e lune, an {}".format(
        date.get("jour", "?"), date.get("lune", "?"), date.get("annee", "?"))


def charger(nom, defaut):
    chemin = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as fh:
        contenu = fh.read().strip()
    if not contenu:
        return defaut
    try:
        return json.loads(contenu)
    except ValueError as err:
        sys.exit("etat/{}.json illisible : {}".format(nom, err))


def plat(t):
    t = unicodedata.normalize("NFD", t or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def mots(texte):
    """Les mots d'un texte, gras d'appui et ponctuation retires.

    On garde les chiffres quelle que soit leur longueur : « 119 », « 26 » sont
    exactement le genre de trace qui relie une replique a la source qui l'a
    donnee.
    """
    t = plat(texte).replace("**", " ")
    out = set()
    for m in re.findall(r"[a-z0-9']+", t):
        m = m.strip("'")
        if m.isdigit() or len(m) >= MOT_MIN:
            out.add(m)
    return out


def pourcent(n, sur):
    return "{}%".format(int(round(100.0 * n / sur))) if sur else "-"


def tronque(t, n):
    t = re.sub(r"\s+", " ", (t or "").replace("**", "")).strip()
    return t if len(t) <= n else t[:n - 1] + "…"


# ------------------------------------------------------------- la collecte

def lire_pensees(debut, fin):
    """Les pensees de la fenetre, a plat. Une sans date est comptee a part —
    elle ne peut pas etre placee, et la taire mentirait sur la couverture."""
    brut = charger("pensees", {})
    liste = brut.get("pensees", []) if isinstance(brut, dict) else (brut or [])
    dedans, sans_date = [], 0
    for p in liste:
        if not isinstance(p, dict):
            continue
        j = jour_absolu(p.get("date"))
        if j is None:
            sans_date += 1
        elif debut <= j <= fin:
            dedans.append(p)
    return dedans, sans_date


def lire_flux(debut, fin):
    dedans, sans_date = [], 0
    chemin = os.path.join(ETAT, "flux.jsonl")
    if not os.path.isfile(chemin):
        return dedans, sans_date
    with io.open(chemin, encoding="utf-8") as fh:
        for ligne in fh:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                item = json.loads(ligne)
            except ValueError:
                continue
            if item.get("type") not in DIT + FAIT:
                continue
            j = jour_absolu(item.get("date"))
            if j is None:
                sans_date += 1
            elif debut <= j <= fin:
                dedans.append(item)
    return dedans, sans_date


# ------------------------------------------------------------ le recoupement

def signatures(documents):
    """Le vocabulaire rare de chaque document, mesure sur le corpus lui-meme.

    Aucune liste de mots vides a tenir : « votre », « grace », « hommes »
    tombent d'eux-memes parce qu'ils sont partout. Ce qui reste est ce qui
    distingue.
    """
    sacs = [mots(d) for d in documents]
    df = {}
    for sac in sacs:
        for m in sac:
            df[m] = df.get(m, 0) + 1
    plafond = max(2, int(math.ceil(RARETE * len(sacs))))
    return [set(m for m in sac if df[m] <= plafond) for sac in sacs]


def recouper(pensees, dits):
    """Pour chaque replique, la pensee dont elle porte la trace.

    A CALCULER SUR TOUT LE CORPUS, toujours. La rarete d'un mot se mesure
    contre l'ensemble : restreindre a un homme avant de compter rendrait ses
    propres mots rares et lierait n'importe quoi a n'importe quoi. On filtre a
    l'affichage, jamais ici.
    """
    textes_p = [p.get("texte") or "" for p in pensees]
    textes_r = [i.get("texte") or "" for i in dits]
    sigs = signatures(textes_p + textes_r)
    sigs_p, sigs_r = sigs[:len(textes_p)], sigs[len(textes_p):]

    portantes, orphelines = [], []
    for item, sig_r in zip(dits, sigs_r):
        qui = item.get("locuteur_id") or item.get("acteur_id")
        meilleure, score = None, 0
        for p, sig_p in zip(pensees, sigs_p):
            # Un homme ne s'appuie que sur SES pensees : deux hommes qui parlent
            # de la meme affaire partagent le vocabulaire sans partager l'amont.
            if p.get("qui") != qui:
                continue
            n = len(sig_r & sig_p)
            if n > score:
                meilleure, score = p, n
        if meilleure is not None and score >= RECOUPEMENT:
            portantes.append((item, meilleure, score))
        else:
            orphelines.append((item, score))
    return portantes, orphelines


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jours", type=int, default=FENETRE)
    ap.add_argument("--qui")
    ap.add_argument("--orphelines", action="store_true",
                    help="dire en clair les repliques sans amont")
    args = ap.parse_args()

    monde = charger("monde", {})
    date = monde.get("date") or {"annee": 129, "lune": 1, "jour": 1}
    fin = jour_absolu(date)
    if fin is None:
        sys.exit("etat/monde.json n'a pas de date lisible.")
    debut = fin - max(0, args.jours - 1)

    pensees, p_sans_date = lire_pensees(debut, fin)
    items, i_sans_date = lire_flux(debut, fin)
    dits = [i for i in items if i.get("type") in DIT]
    faits = [i for i in items if i.get("type") in FAIT]
    portantes, orphelines = recouper(pensees, dits)

    if args.qui:
        pensees = [p for p in pensees if p.get("qui") == args.qui]
        portantes = [x for x in portantes
                     if (x[0].get("locuteur_id") or x[0].get("acteur_id"))
                     == args.qui]
        orphelines = [x for x in orphelines
                      if (x[0].get("locuteur_id") or x[0].get("acteur_id"))
                      == args.qui]

    total = len(portantes) + len(orphelines)
    print("MESURER — du {} au {}{}".format(
        fmt({"annee": date["annee"], "lune": date["lune"],
             "jour": date["jour"] - (args.jours - 1)}),
        fmt(date), "  ({})".format(args.qui) if args.qui else ""))
    print()
    print("  {} pensee(s) dans la fenetre, {} replique(s), {} geste(s).".format(
        len(pensees), total, len(faits)))
    if p_sans_date or i_sans_date:
        print("  (non placables : {} pensee(s) et {} item(s) sans date)".format(
            p_sans_date, i_sans_date))
    print()
    print("  LE CHIFFRE — repliques sans aucune pensee derriere elles :")
    print("      {} sur {}  ({})".format(
        len(orphelines), total, pourcent(len(orphelines), total)))
    print()
    print("  Une replique orpheline n'est pas fautive en soi : une politesse,")
    print("  un accuse de reception, une reponse a une question directe n'ont")
    print("  pas d'amont et n'en ont pas besoin. Ce qui se lit ici, c'est la")
    print("  PENTE — si la part monte, la salle commente au lieu de rapporter.")

    if portantes:
        print()
        print("  CE QUI A PORTE — la pensee retrouvee sous la replique :")
        for item, p, score in sorted(portantes, key=lambda x: -x[2])[:8]:
            qui = item.get("locuteur_id") or item.get("acteur_id")
            print("    [{} mots] {:<16} {}".format(
                score, (qui or "?")[:16], tronque(item.get("texte"), 52)))
            print("       <- {}".format(tronque(p.get("texte"), 62)))
            print("          source : {}".format(tronque(p.get("source"), 62)))

    if args.orphelines and orphelines:
        print()
        print("  SANS AMONT ({}) — a lire une a une, le chiffre ne dit pas"
              " lesquelles sont fautives :".format(len(orphelines)))
        for item, score in orphelines:
            qui = item.get("locuteur_id") or item.get("acteur_id")
            print("    {:<16} {}".format((qui or "?")[:16],
                                         tronque(item.get("texte"), 60)))
    elif orphelines:
        print()
        print("  (--orphelines pour les lire une a une)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
