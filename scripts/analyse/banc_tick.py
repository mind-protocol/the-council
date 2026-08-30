# -*- coding: utf-8 -*-
"""
BANC DU TICK — l'etalon du hors-scene, pour qu'un deplacement de blocs se voie.

    python scripts/analyse/banc_tick.py            compare a l'etalon
    python scripts/analyse/banc_tick.py --poser    (re)pose l'etalon
    python scripts/analyse/banc_tick.py --montrer  imprime la proposition calculee

POURQUOI CE FICHIER EXISTE. `tick.py` fait trois mille deux cents lignes et
calcule TOUT le hors-scene : les horloges de plan qui tombent, les echeances,
les nouvelles a livrer, les declencheurs a peser, les tetes en retard, les
mutations arithmetiques. Il n'avait aucune epreuve — quatre tests pour cent
trente-quatre fichiers Python dans ce depot, et pas un sur la piece la plus
lourde. Un jour ou l'on deplacera un bloc de `tick.py`, rien ne dira que la
soustraction a change de sens : on s'en apercevra six semaines plus tard, en
relisant des annales qui n'ont plus de sens.

IL N'A PAS DE JUGEMENT, COMME `banc-moteur.js`. Il ne dit pas si la proposition
est BONNE — il dit si elle est LA MEME. Un banc qui aurait un avis sur la
qualite d'une fenetre devrait etre reecrit chaque fois qu'on ameliore le
moteur ; celui-ci se repose d'un `--poser`, et l'on ecrit dans le message de
commit ce qui a bouge et pourquoi.

L'ATTENDU EST ZERO, JAMAIS « A PEU PRES ». A etat identique et fenetre tenue, le
calcul est de l'arithmetique : il est deterministe. Un ecart non nul n'est pas
une tolerance a elargir, c'est la reproductibilite qui est cassee. On ne
trouvera donc ici aucun seuil.

IL EST HERMETIQUE, ET C'EST LA CONDITION. Il ne lit pas le `etat/` de la partie
— qui bouge a chaque tour, et dont la meme commande ne rendrait pas deux fois la
meme chose. Il monte une RACINE de papier dans un dossier temporaire : une copie
de `scripts/`, plus le `etat/` fige de `scripts/tests/etalon-tick/`. `tick.py`
tire sa racine de `__file__` ; poser le script ailleurs suffit donc a lui donner
un autre monde, sans une ligne a changer dans `tick.py`. Rien de ce que fait ce
banc ne peut toucher la partie en cours.

CE QU'IL COMPARE. La proposition entiere, clef par clef — les evenements a
resoudre, les nouvelles, les etapes qui tombent, qui avancent, qui attendent,
les declencheurs, les tetes, et surtout les `mutations_proposees`, qui sont la
seule arithmetique que `tick.py` ose ecrire lui-meme. Un seul champ est
neutralise : `genere_le`, l'heure du calcul. Tout le reste est tenu.
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

# La console Windows repond en cp1252 : sans cela, un accent dans un nom
# d'etape fait planter le banc AVANT qu'il ait rendu son verdict — et un banc
# qui meurt d'un caractere ne garde aucune porte.
for _flux in (sys.stdout, sys.stderr):
    try:
        _flux.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import tables  # LA PORTE de etat/

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETALON_DIR = os.path.join(RACINE, "scripts", "tests", "etalon-tick")
FIXTURE = os.path.join(ETALON_DIR, "etat")
ETALON = os.path.join(ETALON_DIR, "proposition.json")

# LA CONDITION — courte, et calculee en quelques secondes.
#
# Cinq jours et deux acteurs, ce n'est pas une fenetre interessante : c'est une
# fenetre SUFFISANTE. Il faut qu'une horloge tombe, qu'une autre avance, qu'une
# troisieme attende sa dependance, qu'une quatrieme n'ait pas d'horloge du tout,
# qu'une echeance soit en retard, qu'une nouvelle reste suspendue et qu'une
# mutation arithmetique soit redigee. Au-dela, chaque jour de plus est du temps
# qu'on ne passera pas a lancer le banc — et un banc qu'on n'a pas le temps de
# lancer ne sert a rien du tout.
JUSQU_A = "129.3.25"

VOLATILES = ("genere_le",)


def _dire(ok, texte):
    print("  %-5s %s" % ("ok" if ok else "NON", texte))


def calculer(garder=False):
    """Monter la racine de papier, y lancer le tick, rendre sa proposition."""
    temporaire = tempfile.mkdtemp(prefix="banc-tick-")
    try:
        shutil.copytree(os.path.join(RACINE, "scripts"),
                        os.path.join(temporaire, "scripts"))
        shutil.copytree(FIXTURE, os.path.join(temporaire, "etat"))

        # Le tissu est DERIVE de l'etat : on le refait ici plutot que de le
        # figer, pour que l'etalon ne porte que ce qui a ete ecrit a la main.
        tisse = subprocess.run(
            [sys.executable, os.path.join(temporaire, "scripts", "tisser.py"),
             "--ecrire"], capture_output=True, text=True)
        if tisse.returncode != 0:
            raise SystemExit("banc-tick : tisser.py a echoue\n" + tisse.stderr[-2000:])

        tick = subprocess.run(
            [sys.executable, os.path.join(temporaire, "scripts", "tick.py"),
             "--jusqu-a", JUSQU_A], capture_output=True, text=True)

        etat = os.path.join(temporaire, "etat")
        propositions = sorted(f for f in os.listdir(etat)
                              if f.startswith("tick-") and f.endswith(".json"))
        if not propositions:
            raise SystemExit(
                "banc-tick : aucune proposition ecrite.\n"
                + (tick.stdout or "")[-1500:] + (tick.stderr or "")[-1500:])
        proposition = tables.lire(os.path.join(etat, propositions[-1]))
        for clef in VOLATILES:
            proposition.pop(clef, None)
        return proposition, (tick.stdout or "")
    finally:
        if not garder:
            shutil.rmtree(temporaire, ignore_errors=True)


def canonique(valeur):
    return json.dumps(valeur, ensure_ascii=False, indent=2, sort_keys=True)


def _premiere_difference(a, b):
    """La premiere ligne qui differe, en clair.

    Un compte ne suffit pas : deux listes d'un element qui ont change de
    CONTENU s'affichaient « 1 -> 1 », ce qui ne dit rien a celui qui vient de
    casser quelque chose. On lui montre la ligne.
    """
    la, lb = canonique(a).splitlines(), canonique(b).splitlines()
    for i in range(max(len(la), len(lb))):
        x = la[i].strip() if i < len(la) else "<rien>"
        y = lb[i].strip() if i < len(lb) else "<rien>"
        if x != y:
            return x, y
    return None, None


def comparer(calculee, attendue):
    """Les clefs qui different, et en quoi. Zero tolerance."""
    ecarts = []
    for clef in sorted(set(calculee) | set(attendue)):
        a, b = attendue.get(clef, "<absente>"), calculee.get(clef, "<absente>")
        if canonique(a) == canonique(b):
            continue
        n_a = len(a) if isinstance(a, (list, dict)) else a
        n_b = len(b) if isinstance(b, (list, dict)) else b
        ecarts.append((clef, n_a, n_b) + _premiere_difference(a, b))
    return ecarts


def poser():
    proposition, _ = calculer()
    if not os.path.isdir(ETALON_DIR):
        os.makedirs(ETALON_DIR)
    with io.open(ETALON, "w", encoding="utf-8", newline="\n") as f:
        f.write(canonique(proposition) + "\n")
    print("Etalon pose : %s" % os.path.relpath(ETALON, RACINE))
    print("  %d clef(s), %d octets" % (len(proposition), os.path.getsize(ETALON)))
    return 0


def comparer_a_l_etalon(montrer=False):
    print("BANC DU TICK — fenetre %s -> %s, %s"
          % ("129.3.20", JUSQU_A, os.path.relpath(FIXTURE, RACINE)))
    print("")
    proposition, sortie = calculer()
    if montrer:
        print(sortie)

    if not os.path.exists(ETALON):
        print("  Aucun etalon. Pose-le :  python scripts/analyse/banc_tick.py --poser")
        return 1
    with io.open(ETALON, encoding="utf-8") as f:
        attendue = json.load(f)

    # Ce que la fenetre doit contenir pour que le banc mesure quelque chose. Si
    # l'un de ces comptes tombe a zero, l'etalon ne prouve plus rien meme
    # lorsqu'il est tenu — un etalon vide se compare parfaitement a lui-meme.
    couverture = [
        ("des echeances a resoudre", "evenements_a_resoudre"),
        ("des etapes qui tombent", "etapes_qui_tombent"),
        ("des etapes qui avancent", "etapes_qui_avancent"),
        ("des etapes en attente", "etapes_en_attente"),
        ("des declencheurs a peser", "declencheurs_a_evaluer"),
        ("des tetes a rafraichir", "tetes_a_rafraichir"),
        ("des mutations arithmetiques", "mutations_proposees"),
    ]
    creux = [nom for nom, clef in couverture if not proposition.get(clef)]
    for nom, clef in couverture:
        _dire(bool(proposition.get(clef)),
              "%-30s %d" % (nom, len(proposition.get(clef) or [])))
    print("")

    ecarts = comparer(proposition, attendue)
    if ecarts:
        print("--- contre l'etalon ---")
        for clef, attendu, calcule, ligne_a, ligne_b in ecarts:
            print("  NON   %-28s etalon %s -> calcule %s" % (clef, attendu, calcule))
            if ligne_a is not None:
                print("          etalon  : %s" % ligne_a[:96])
                print("          calcule : %s" % ligne_b[:96])
        print("")
        print("%d clef(s) ont bouge. Si c'est voulu, repose l'etalon" % len(ecarts))
        print("(--poser) et dis dans le message de commit ce qui a change et")
        print("pourquoi. Sinon, le deplacement de bloc a change le calcul.")
        return 1

    _dire(True, "la proposition est celle de l'etalon (%d clefs, a l'identique)"
          % len(attendue))
    if creux:
        print("")
        print("  Reserve : %s — la fenetre ne les exerce plus."
              % ", ".join(creux))
        return 1
    print("")
    print("  Toutes les epreuves sont tenues.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--poser", action="store_true",
                    help="(re)pose l'etalon depuis le calcul courant")
    ap.add_argument("--montrer", action="store_true",
                    help="imprime aussi la proposition en francais")
    args = ap.parse_args()
    if args.poser:
        return poser()
    return comparer_a_l_etalon(args.montrer)


if __name__ == "__main__":
    sys.exit(main())
