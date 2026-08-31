# -*- coding: utf-8 -*-
"""AVANCER — l'horloge du monde, de la main du MJ, d'autant qu'il veut.

    python scripts/avancer.py --jours 2              # a blanc : montre tout
    python scripts/avancer.py --jours 2 --vraiment   # avance pour de bon
    python scripts/avancer.py --jusqu-a 129.4.9 --vraiment

NE UN LE 31.8, en conclusion du fil « avancer jusqu'a un evenement » : pas de
moteur de saut — l'office du MJ est deja « l'arbitrage du temps et du canon »
(affaire-le-saut-jusquau-premier-contact), et depuis ce soir il a python en
session. Ce script est donc SON outil : la chaine du passage de jour que le
dev faisait a la main — tick de la fenetre, mutation `monde` (vocabulaire
ferme de etat/mutations), application, rattrapage des horloges de siege par
la porte (le geste de flux.py a chaque scene commune, qu'aucune scene ne fait
plus sans PJ).

LA GARDE DURE (X.13 de son affaire) : on n'avance JAMAIS par-dessus un canon
echu sans arbitre. Avant chaque jour, si un evenement `type: canon` a
`date_prevue` atteinte et un statut encore ouvert (prevu/programme/a-venir),
le script s'arrete net et rend la main — le MJ arbitre, puis relance. Quand
s'arreter, qui reveiller, quoi verifier ensuite : c'est son metier, pas celui
de ce script.
"""
from __future__ import print_function

import argparse
import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(RACINE, "scripts"),
          os.path.join(RACINE, "scripts", "noyau")):
    if p not in sys.path:
        sys.path.insert(0, p)

from etat.expose import tables  # noqa: E402 — LA PORTE de etat/

STATUTS_OUVERTS = {"prevu", "programme", "a-venir"}


def date_du_monde():
    return dict(tables.lire("monde.json", {}).get("date") or {})


def _minute(d):
    return (((int(d.get("annee", 0)) * 12 + int(d.get("lune", 1)) - 1) * 30
             + int(d.get("jour", 1)) - 1) * 1440 + int(d.get("minute") or 0))


def canons_echus(date):
    """Les evenements canon dus a `date` et toujours ouverts."""
    e = tables.lire("evenements.json", [])
    evs = e.get("evenements") if isinstance(e, dict) else e
    dus = []
    for v in evs or []:
        if not isinstance(v, dict) or v.get("type") != "canon":
            continue
        if str(v.get("statut")) not in STATUTS_OUVERTS:
            continue
        prevue = v.get("date_prevue")
        if isinstance(prevue, dict) and _minute(prevue) <= _minute(date):
            dus.append(v)
    return dus


def _lendemain(date):
    d = dict(date)
    d["jour"] = int(d.get("jour", 1)) + 1
    if d["jour"] > 30:
        d["jour"] = 1
        d["lune"] = int(d.get("lune", 1)) + 1
        if d["lune"] > 12:
            d["lune"] = 1
            d["annee"] = int(d.get("annee", 0)) + 1
    d["minute"] = 540  # le matin, 9h00 — l'heure des scenes
    return d


def _derniere_proposition():
    etat = os.path.join(RACINE, "etat")
    ticks = sorted(n for n in os.listdir(etat)
                   if n.startswith("tick-") and n.endswith(".json"))
    return ticks[-1] if ticks else None


def avancer_un_jour(vraiment, ici):
    """Un jour : tick de la fenetre, mutation monde, application, horloges."""
    cible = _lendemain(ici)
    if not vraiment:
        print("  (a blanc) %s -> %s.%s.%s" % (
            "%(annee)s.%(lune)s.%(jour)s" % ici,
            cible["annee"], cible["lune"], cible["jour"]))
        return True
    r = subprocess.run([sys.executable, os.path.join(RACINE, "scripts",
                                                     "tick.py"), "--jours", "1"],
                       cwd=RACINE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("  TICK EN ECHEC — rien n'est ecrit :\n%s" % (r.stderr or
                                                            r.stdout)[-800:])
        return False
    nom = _derniere_proposition()
    chemin = os.path.join(RACINE, "etat", nom)
    prop = json.load(io.open(chemin, encoding="utf-8"))
    prop["mutations_proposees"].append({
        "table": "monde", "cible": "monde", "operation": "monde",
        "champs": {"date": cible},
        "pourquoi": "le jour passe, de la main du MJ (scripts/avancer.py)"})
    io.open(chemin, "w", encoding="utf-8").write(
        json.dumps(prop, ensure_ascii=False, indent=1))
    r = subprocess.run([sys.executable, os.path.join(RACINE, "scripts",
                                                     "appliquer.py"),
                        nom, "--vraiment"],
                       cwd=RACINE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("  APPLICATION REFUSEE — %s" % (r.stdout or r.stderr)[-400:])
        return False
    # Les horloges de siege suivent le monde — le geste de flux.py (scene
    # commune), qu'aucune scene ne fait plus sans PJ.
    h = tables.lire("horloges.json", {})
    for pid in h:
        h[pid] = dict(cible)
    tables.ecrire("horloges.json", h)
    print("  %s.%s.%s — jour ecrit (proposition %s)"
          % (cible["annee"], cible["lune"], cible["jour"], nom))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--jours", type=int, help="combien de jours avancer")
    ap.add_argument("--jusqu-a", dest="jusqu_a", metavar="129.4.9",
                    help="avancer jusqu'a cette date (matin)")
    ap.add_argument("--vraiment", action="store_true",
                    help="ecrire pour de bon (sans quoi : a blanc)")
    a = ap.parse_args()
    ici = date_du_monde()
    if a.jusqu_a:
        try:
            annee, lune, jour = (int(x) for x in a.jusqu_a.split("."))
        except ValueError:
            raise SystemExit("--jusqu-a attend annee.lune.jour, ex. 129.4.9")
        jours = ((annee * 12 + lune - 1) * 30 + jour) \
            - ((int(ici["annee"]) * 12 + int(ici["lune"]) - 1) * 30
               + int(ici["jour"]))
        if jours <= 0:
            raise SystemExit("le monde est deja au %(annee)s.%(lune)s.%(jour)s"
                             % ici)
    elif a.jours:
        if a.jours < 0:
            raise SystemExit("--jours doit etre positif")
        jours = a.jours
    else:
        ap.print_help()
        return 0

    print("AVANCER — depuis %(annee)s.%(lune)s.%(jour)s, %(m)s jour(s)%(bl)s"
          % dict(ici, m=jours, bl="" if a.vraiment else " (a blanc)"))
    def crier(dus, arret):
        print("%s — canon(s) du(s) sans arbitre (X.13) :"
              % ("ARRET SUR CANON" if arret else "NOTE : TU ATTERRIS SUR"))
        for v in dus:
            p = v.get("date_prevue") or {}
            print("  %s — importance %s, du le %s.%s.%s, statut %s"
                  % (v.get("id"), v.get("importance"), p.get("annee"),
                     p.get("lune"), p.get("jour"), v.get("statut")))
        print("Arbitre-les (statut hors {prevu, programme, a-venir})%s."
              % (", puis relance" if arret else " avant tout autre geste"))

    for _ in range(jours):
        dus = canons_echus(ici)
        if dus:
            crier(dus, arret=True)
            return 1
        if not avancer_un_jour(a.vraiment, ici):
            return 1
        ici = date_du_monde() if a.vraiment else _lendemain(ici)
    print("Fini. Le monde est au %(annee)s.%(lune)s.%(jour)s, 9h00." % ici)
    dus = canons_echus(ici)
    if dus:
        crier(dus, arret=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
