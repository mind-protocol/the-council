# -*- coding: utf-8 -*-
# NORMALISER LE VOCABULAIRE DES LIENS.
#
# POURQUOI. Le tissu porte 34 natures d'arete pour une quinzaine d'intentions
# reelles. Treize n'apparaissent qu'une a trois fois : `dépend_de` a cote de
# `depend_de` (527), `attendu_par` a cote de `attendue_par` (53), `verrouille`
# et `verrouillé_par` une fois chacun. Ce n'est pas du vocabulaire, c'est de la
# derive de main : chaque cahier a ete rempli un jour different et personne
# n'avait la liste sous les yeux.
#
# Le cout n'est pas esthetique. Une requete « qu'est-ce qui depend de ceci »
# rate deux aretes sur 529 aujourd'hui — et le jour ou l'on comptera les
# pressions sans contre-arete, deux manquantes suffiront a rater un goulot.
#
# DEUX SORTIES, ET ELLES NE SE CONFONDENT PAS :
#   1. ce que le LECTEUR doit replier — sans toucher aux fichiers, tout de
#      suite, et c'est reversible ;
#   2. ce que la DONNEE devrait corriger — avec le livre et la ligne, pour la
#      main qui voudra le faire un jour. On ne le fait pas ici : books.json
#      est ecrit par la session qui joue.
#
# ET LA QUESTION QUI COMPTE PLUS QUE LE VOCABULAIRE : `sert` et `servie par`
# sont la MEME arete vue des deux bouts. Si les deux cahiers l'ecrivent chacun
# de son cote, le graphe la compte deux fois — et tout degre entrant est faux.
# Ce script le mesure.
#
# Ne modifie rien. Lit le tissu depose par `tisser.py`.
import io
import json
import os
import sys
import collections


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TISSU = os.path.join(RACINE, "etat", "tissu", "aretes.jsonl")

# --------------------------------------------------------- le vocabulaire
# Seize natures, six familles. Tout le reste s'y replie ou se signale.

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from plan.expose import tisser  # noqa: E402
CANON, INVERSES = tisser.CANON, tisser.INVERSES


def lire():
    if not os.path.isfile(TISSU):
        sys.exit("Aucun tissu. Lance d'abord : python scripts/tisser.py --ecrire")
    return [json.loads(l) for l in io.open(TISSU, encoding="utf-8") if l.strip()]


def canoniser(a):
    """Rend (nature, de, vers) apres repli et retournement eventuel."""
    c = CANON.get(a["nature"])
    if c is None:
        return None, a["de"], a["vers"]
    if c in INVERSES:
        return INVERSES[c], a["vers"], a["de"]
    return c, a["de"], a["vers"]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    A = lire()
    brut = collections.Counter(a["nature"] for a in A)

    inconnues = collections.Counter()
    apres = collections.Counter()
    canon_aretes = []
    for a in A:
        c, de, vers = canoniser(a)
        if c is None:
            inconnues[a["nature"]] += 1
            continue
        apres[c] += 1
        canon_aretes.append((c, de, vers, a))

    print("NORMALISER LE VOCABULAIRE DES LIENS")
    print("  {} natures observees  ->  {} apres repli".format(
        len(brut), len(apres)))
    print("  {} aretes, {} de nature inconnue".format(
        len(A), sum(inconnues.values())))
    print()

    print("1. CE QUE LE LECTEUR REPLIE — tout de suite, sans toucher aux fichiers")
    replis = collections.defaultdict(list)
    for observee, vers_c in CANON.items():
        cible = INVERSES.get(vers_c, vers_c)
        if observee != cible and brut.get(observee):
            replis[cible].append((observee, brut[observee],
                                  vers_c in INVERSES))
    for cible in sorted(replis, key=lambda k: -apres.get(k, 0)):
        total = apres.get(cible, 0)
        dedans = ", ".join("{} ({}{})".format(o, n, ", retournee" if inv else "")
                           for o, n, inv in sorted(replis[cible],
                                                   key=lambda x: -x[1]))
        print("  {:<14} {:>5}   <- {}".format(cible, total, dedans))
    if inconnues:
        print()
        print("  HORS VOCABULAIRE, a trancher a la main :")
        for k, v in inconnues.most_common():
            print("    {:<20} {}".format(k, v))
    print()

    # --- LA QUESTION QUI COMPTE : l'arete ecrite deux fois
    print("2. LES ARETES COMPTEES DEUX FOIS")
    vus = collections.defaultdict(list)
    for c, de, vers, a in canon_aretes:
        vus[(c, de, vers)].append(a)
    doubles = {k: v for k, v in vus.items() if len(v) > 1}
    n_doubles = sum(len(v) - 1 for v in doubles.values())
    print("  {} aretes en double apres repli ({:.1f}% du tissu)".format(
        n_doubles, 100.0 * n_doubles / max(1, len(canon_aretes))))
    print("  — dont celles que DEUX cahiers ecrivent chacun de son bout :")
    croises = 0
    for k, v in doubles.items():
        sources = set(x["source"] for x in v)
        if len(sources) > 1:
            croises += 1
    print("    {} paires ecrites depuis deux endroits differents".format(croises))
    print()
    for k, v in sorted(doubles.items(), key=lambda kv: -len(kv[1]))[:10]:
        print("    {:<12} {} -> {}   x{}  [{}]".format(
            k[0], str(k[1])[:22], str(k[2])[:22], len(v),
            " · ".join(sorted(set(x["source"] for x in v)))))
    print()
    print("  CONSEQUENCE : tant que ce n'est pas replie, tout degre entrant")
    print("  est surestime d'autant — donc tout goulot mesure est faux.")
    print()

    print("3. CE QUE LA DONNEE DEVRAIT CORRIGER — pour la main qui le fera")
    print("  Les natures rares viennent de la colonne « Le lien » des tables")
    print("  « Affaires liees », remplie a la main, cahier par cahier.")
    for k, v in sorted(brut.items(), key=lambda kv: kv[1]):
        if v <= 3 and CANON.get(k) and CANON[k].rstrip("$") != k:
            print("    {:<18} {} fois  ->  ecrire {}".format(
                k, v, CANON[k].rstrip("$")))
    print()
    print("  On ne les reecrit PAS ici : books.json appartient a la session")
    print("  qui joue. Le repli du lecteur suffit a rendre le graphe juste.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
