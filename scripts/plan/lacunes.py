# -*- coding: utf-8 -*-
"""LACUNES — qui compte dans cette histoire sans avoir de quoi y travailler.

Les autres boucles demandent qui a la plus forte raison d'agir. Celle-ci
demande QUI EST IMPORTANT ET PAS ECRIT. C'est une boucle d'ecriture, pas de
simulation : elle tourne rarement, en amont des trois autres.

POURQUOI L'ATTEINTE, ET PAS LA PRESSION. Le score d'election vaut
`sqrt(atteinte x pression)`. La pression sort des motifs DECIDER, qui
n'existent que la ou le graphe est detaille : elle mesure ce qu'on a ECRIT, et
elle vaut zero partout ou l'on n'a rien redige. L'atteinte, elle, mesure la
place structurelle dans l'histoire, et elle ne punit pas les peu ecrits —
mesure faite : Aegon II passe devant Aldon Hask, Cregan Stark devant Steffon
Darklyn. C'est donc la seule des deux qui puisse dire « celui-la compte » sans
repeter « celui-la est deja redige ».

L'ECART ENTRE LES DEUX EST LA LACUNE. Un homme a forte atteinte et sans
affaire est un homme dont l'histoire a besoin et qui n'a rien a faire — il ne
sera jamais elu, et son absence ne se voit nulle part. Mesure du 10 aout :
Daemon porte 2 taches et 0 affaire, Larys 2 et 0, Criston 3 et 0, Otto 7 et 0,
quand le mestre Gerardys en porte 93 et 22. Cinquante-trois acteurs actifs sur
soixante-dix n'ont aucune affaire.

CE SCRIPT N'ECRIT JAMAIS DANS etat/. Il detecte, il classe, et il rend des
convocations pretes a passer a `depecher.py` — on ne redige pas l'affaire d'un
homme, on lui demande la sienne.

Usage :
    python scripts/plan/lacunes.py
    python scripts/plan/lacunes.py --combien 12
    python scripts/plan/lacunes.py --convocations
    python scripts/plan/lacunes.py --json rapport.json
"""

import argparse
import collections
import io
import json
import os
import sys

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RACINE = os.path.dirname(SCRIPTS)
ETAT = os.path.join(RACINE, "etat")
sys.path.insert(0, SCRIPTS)

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from agents.expose import boucle_activation as activation  # noqa: E402


def lire(nom, defaut):
    try:
        with io.open(os.path.join(ETAT, nom + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut


def liste(valeur, *cles):
    if isinstance(valeur, dict):
        for cle in cles:
            if isinstance(valeur.get(cle), list):
                return valeur[cle]
        return []
    return valeur if isinstance(valeur, list) else []


def actif(p):
    return (str(p.get("etat") or "actif").strip().lower() == "actif"
            and str(p.get("condition") or "libre").strip().lower()
            not in ("mort", "morte", "disparu", "disparue"))


def analyser():
    noeuds, aretes, evaluation = activation.charger_tissu()
    adj = activation.adjacence(noeuds, aretes)
    etat = activation.lire_json(activation.ETAT_BOUCLE, {})
    horloge, occupes = activation.horloge_directe(etat)

    atteinte = activation.diffuser(
        {"pers:" + horloge["source_id"]: 1.0}, adj, noeuds)
    pic = max(atteinte.values() or [1e-12])

    # --- ce que chacun tient : taches actives et affaires touchees
    taches = collections.defaultdict(list)
    affaires = collections.defaultdict(set)
    porteurs = collections.defaultdict(set)
    for a in aretes:
        if a.get("flou"):
            continue
        de, vers = a.get("de"), a.get("vers")
        if a.get("nature") == "tient":
            for p, t in ((de, vers), (vers, de)):
                if (noeuds.get(p) or {}).get("genre") == "personne":
                    porteurs[t].add(p)
        if a.get("nature") not in ("tient", "poursuit"):
            continue
        for p, t in ((de, vers), (vers, de)):
            if (noeuds.get(p) or {}).get("genre") != "personne":
                continue
            noeud = noeuds.get(t) or {}
            if not activation.tache_active(noeud):
                continue
            taches[p].append(t)
            ou = str(noeud.get("ou") or "")
            if ou.startswith("affaire-"):
                affaires[p].add(ou)

    personnages = {p["id"]: p for p in liste(lire("personnages", []),
                                             "personnages") if p.get("id")}
    pensees = liste(lire("pensees", []), "pensees")
    travaux_de = collections.Counter(p.get("qui") for p in pensees)
    intentions = {t.get("personnage_id"): t
                  for t in liste(lire("intentions", []), "intentions")}

    acteurs = []
    for nid, n in noeuds.items():
        if n.get("genre") != "personne":
            continue
        pid = nid.removeprefix("pers:")
        fiche = personnages.get(pid)
        if not fiche or not actif(fiche) or pid in occupes:
            continue
        a = atteinte.get(nid, 0.0) / pic
        nb_aff = len(affaires[nid])
        acteurs.append({
            "qui": pid,
            "nom": fiche.get("nom") or pid,
            "titre": str(fiche.get("titre") or "")[:60],
            "lieu": fiche.get("lieu_id"),
            "atteinte": round(a, 5),
            "taches_actives": len(taches[nid]),
            "affaires": nb_aff,
            "travaux_ouverts": travaux_de.get(pid, 0),
            "a_une_tete": pid in intentions,
            # Le manque decroit vite avec la premiere affaire : ce qu'on veut
            # reperer, c'est le pas de zero a un, pas la difference entre huit
            # et neuf. Une affaire de plus chez Gerardys n'interesse personne.
            "manque": round(a / (1.0 + nb_aff), 5),
        })
    acteurs.sort(key=lambda x: (-x["manque"], -x["atteinte"], x["qui"]))

    # --- les affaires dont les taches n'atterrissent sur personne
    par_affaire = collections.defaultdict(
        lambda: {"noeuds": 0, "actives": 0, "orphelines": []})
    for nid, n in noeuds.items():
        ou = str(n.get("ou") or "")
        if not ou.startswith("affaire-"):
            continue
        fiche = par_affaire[ou]
        fiche["noeuds"] += 1
        if n.get("genre") in ("action", "etape") and activation.tache_active(n):
            fiche["actives"] += 1
            if not porteurs.get(nid):
                fiche["orphelines"].append(
                    {"id": nid, "quoi": str(n.get("quoi") or "")[:70]})
    orphelines = sorted(
        ({"affaire": ou, "noeuds": f["noeuds"], "actives": f["actives"],
          "sans_porteur": len(f["orphelines"]),
          "part": round(100.0 * len(f["orphelines"]) / f["actives"], 1)
          if f["actives"] else 0.0,
          "exemples": f["orphelines"][:3]}
         for ou, f in par_affaire.items() if f["orphelines"]),
        key=lambda x: -x["sans_porteur"])

    return {
        "acteurs": acteurs,
        "affaires_orphelines": orphelines,
        "totaux": {
            "acteurs_actifs": len(acteurs),
            "sans_affaire": sum(1 for x in acteurs if not x["affaires"]),
            "sans_tache": sum(1 for x in acteurs if not x["taches_actives"]),
            "affaires": len(par_affaire),
            "taches_sans_porteur": sum(x["sans_porteur"] for x in orphelines),
        },
    }


def genre_de_source(texte):
    """Heuristique assumee : le mot qui domine dit ou l'on va chercher."""
    bas = texte.lower()
    if any(m in bas for m in ("registre", "livre", "cahier", "compte",
                              "role", "rôle", "liste")):
        return "registre"
    if any(m in bas for m in ("pli", "lettre", "corbeau", "message")):
        return "pli"
    if any(m in bas for m in ("parler", "voir", "trouver", "demander",
                              "interroger", "recevoir")):
        return "gens"
    return "chose"


# `--ouvrir` A DISPARU. Il n'existait que pour contourner un verrou :
# `depecher.py` exigeait un dossier que `convoquer.py` ne redigeait que pour
# qui portait deja un travail — un homme sans travail n'etait donc pas
# depechable DU TOUT, et il fallait lui en ouvrir un a vide avant de pouvoir
# l'appeler. Le verrou est leve : un homme est depechable des qu'il a un CREUX
# dans sa journee. Ce script redevient ce qu'il aurait du rester — un
# detecteur, qui montre qui pese sans avoir de quoi travailler, et propose la
# ligne de commande pour aller le lui demander.


def mission(entree):
    """On ne redige pas son affaire : on lui demande la sienne."""
    return (
        "Tu n'agis pas aujourd'hui : tu rends compte. Dis ce sur quoi tu "
        "travailles EN CE MOMENT — pas tes intentions generales, les affaires "
        "concretes que tu as en cours. Pour chacune : ce que tu veux obtenir, "
        "ce qui te bloque aujourd'hui, ce que ca coute en hommes, en or et en "
        "jours, qui la tient chez toi, et a quelle date tu attends quoi. Sois "
        "chiffre et date ; une affaire sans cout ni echeance ne vaut rien. "
        "Trois a cinq affaires suffisent."
    )


def rendre(rapport, combien, convocations):
    acteurs = rapport["acteurs"]
    retenus = [x for x in acteurs if x["manque"] > 0][:combien]

    if convocations:
        for x in retenus:
            print("# %s — %s · atteinte %.4f · %d taches · %d affaires"
                  % (x["qui"], x["nom"], x["atteinte"],
                     x["taches_actives"], x["affaires"]))
            print('python scripts/depecher.py --qui %s --minutes 25 \\'
                  % x["qui"])
            print('  --mission "%s"' % mission(x))
            print()
        return

    t = rapport["totaux"]
    print("ACTEURS IMPORTANTS SANS DE QUOI TRAVAILLER")
    print("%-20s %-9s %-7s %-6s %-8s %s"
          % ("qui", "atteinte", "taches", "aff.", "pensees", "titre"))
    for x in retenus:
        print("%-20s %-9.4f %-7d %-6d %-8d %s"
              % (x["qui"], x["atteinte"], x["taches_actives"], x["affaires"],
                 x["travaux_ouverts"], x["titre"][:44]))
    print()
    print("   %d acteurs actifs · %d sans aucune affaire · %d sans aucune tache"
          % (t["acteurs_actifs"], t["sans_affaire"], t["sans_tache"]))
    print()
    print("AFFAIRES DONT LES TACHES N'ATTERRISSENT SUR PERSONNE")
    print("%-38s %-9s %-13s %s" % ("affaire", "actives", "sans porteur", "part"))
    for x in rapport["affaires_orphelines"][:12]:
        print("%-38s %-9d %-13d %.0f%%"
              % (x["affaire"][:38], x["actives"], x["sans_porteur"], x["part"]))
    print()
    print("   %d taches actives sans porteur sur %d affaires"
          % (t["taches_sans_porteur"], t["affaires"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--combien", type=int, default=15)
    ap.add_argument("--convocations", action="store_true")
    ap.add_argument("--json")
    args = ap.parse_args()
    activation.AFFICHER_LOGS = False
    activation.PERSISTER_LOGS = False
    rapport = analyser()
    rendre(rapport, args.combien, args.convocations)
    if args.json:
        with io.open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        print("rapport : %s" % args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
