# -*- coding: utf-8 -*-
"""UNE SEULE FORME POUR LE TEXTE D'UNE PAROLE : `contenu`.

CE N'ETAIT PAS HORS SCHEMA, ET C'EST PIRE. `docs/schema.md` l.118 declare les
trois formes legitimes — « `contenu` (la forme de reference), ou `quoi`, ou
`texte` ; un lecteur les lit dans cet ordre ». Le format tolerait donc la
dispersion, et personne n'etait en faute : 383 paroles en `contenu`, 152 en
`quoi`, 130 en `texte`, sur 665.

LE DEGAT EST CHEZ LES LECTEURS QUI NE LISENT QU'UNE FORME. Mesure du 31.8 :
`scripts/temps/gardes/croyances.py` l.65 fait `parole.get("contenu") or ""` —
les 282 paroles des deux autres formes lui sont INVISIBLES. Une garde qui
ignore 42 % de la memoire verbale ne garde rien, et rien ne le disait : elle
lit une chaine vide et poursuit. Le schema autorisait trois portes ; les
consommateurs n'en ont ouvert qu'une.

CE QUE FAIT CETTE MIGRATION, ET CE QU'ELLE NE FAIT PAS. Elle deplace le texte
vers `contenu` et retire les deux autres clefs — rien d'autre. Elle est SANS
PERTE, verifie avant d'ecrire : aucune parole ne portait deux formes a la
fois, aucune n'etait vide. Elle ne touche pas `docs/schema.md`, qui reste
l'autorite et continue d'autoriser les trois : un lecteur ecrit pour lire les
trois marche toujours, et c'est voulu — on normalise la DONNEE, on ne
restreint pas le format.

    python scripts/migrations/normaliser_paroles.py            # ce qui serait fait
    python scripts/migrations/normaliser_paroles.py --vraiment # l'ecriture
"""
import io
import json
import os
import shutil
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from etat.expose import tables  # LA PORTE de etat/ : on n'ecrit pas a cote

# `_d` est deja `<depot>/scripts` : UN SEUL dirname. Le piege documente
# dans scripts/CLAUDE.md — un de trop fait chercher etat/ un etage au-dessus
# du depot, et `tables.lire` rend alors le defaut sans rien dire.
RACINE = os.path.dirname(_d)
PAROLES = os.path.join(RACINE, "etat", "paroles.json")
FORMES = ("contenu", "quoi", "texte")


def examiner(paroles):
    """Rend (a_deplacer, conflits, vides) sans rien changer."""
    a_deplacer, conflits, vides = [], [], []
    for p in paroles:
        portees = [k for k in FORMES if p.get(k) not in (None, "")]
        if len(portees) > 1:
            conflits.append(p)
        elif not portees:
            vides.append(p)
        elif portees[0] != "contenu":
            a_deplacer.append((p, portees[0]))
    return a_deplacer, conflits, vides


def main():
    vraiment = "--vraiment" in sys.argv
    paroles = tables.lire(PAROLES, [])
    if isinstance(paroles, dict):
        paroles = paroles.get("paroles") or []
    a_deplacer, conflits, vides = examiner(paroles)

    print("paroles            : %d" % len(paroles))
    print("deja en `contenu`  : %d"
          % sum(1 for p in paroles if p.get("contenu")))
    print("a deplacer         : %d  (%s)"
          % (len(a_deplacer),
             ", ".join("%s=%d" % (f, sum(1 for _, x in a_deplacer if x == f))
                       for f in ("quoi", "texte"))))
    print("conflits (2 formes): %d" % len(conflits))
    print("sans aucun texte   : %d" % len(vides))

    # DEUX FORMES SUR LA MEME PAROLE : ON NE DEVINE PAS. Le schema dit l'ordre
    # de lecture, pas lequel fait foi quand les deux sont ecrits. On s'arrete.
    if conflits:
        print("\nARRET : %d parole(s) portent deux formes. On ne choisit pas a"
              " leur place — les voici :" % len(conflits))
        for p in conflits[:5]:
            print("  %s : %s" % (p.get("id"),
                                 {k: str(p.get(k))[:60] for k in FORMES
                                  if p.get(k)}))
        return 1

    if not a_deplacer:
        print("\nRien a faire : tout est deja sous `contenu`.")
        return 0
    if not vraiment:
        print("\nA sec. Trois exemples de ce qui serait deplace :")
        for p, forme in a_deplacer[:3]:
            print("  %s  %s -> contenu : %s"
                  % (p.get("id"), forme, str(p.get(forme))[:70]))
        print("\nRelancer avec --vraiment pour ecrire.")
        return 0

    sauvegarde = PAROLES + ".avant-normalisation"
    shutil.copy2(PAROLES, sauvegarde)
    for p, forme in a_deplacer:
        p["contenu"] = p.pop(forme)
    tables.ecrire(PAROLES, paroles)
    reste = [k for p in paroles for k in ("quoi", "texte") if p.get(k)]
    print("\n%d paroles deplacees. Sauvegarde : %s"
          % (len(a_deplacer), os.path.basename(sauvegarde)))
    print("il reste %d clef(s) `quoi`/`texte` : %s"
          % (len(reste), "aucune" if not reste else reste[:5]))
    print("toutes portent `contenu` : %s"
          % all(p.get("contenu") for p in paroles))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
