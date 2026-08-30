# -*- coding: utf-8 -*-
"""CLI — l'entree de scripts/affecter.py, gelee (la facade l'appelle par
la porte agents/expose.py).
"""
import json
import math
import os
import sys

from agents.affectation.lecture import _bati
from agents.affectation.lecture import (RACINE, DEFAUT_MONDE, GENS, LIENS,
                                        PERSOS, BOOKS, PLANS, VILLE, GENRES,
                                        RAYON_REANCRAGE, OCCUPANTS, sortir,
                                        charger_bati, charger_pieces,
                                        fiche_piece, monde_de, charger_liens,
                                        retrait, ecrire, fiche_bati,
                                        dire_bati, position, adresse,
                                        corps_par_id, identifiants,
                                        visibilite_demandee, voit)
from agents.affectation.controle import verifier, reancrer

def main():
    a = sys.argv[1:]
    def opt(nom, n=1):
        if nom not in a: return None
        i = a.index(nom)
        return a[i + 1:i + 1 + n]
    vraiment = "--vraiment" in a
    # Le monde sur lequel on travaille — pour --affecter, --chercher, --bati.
    # Les affectations déjà écrites disent le leur ; ce drapeau ne les touche pas.
    monde = ((a[a.index("--monde") + 1] if "--monde" in a
              and len(a) > a.index("--monde") + 1 else None) or DEFAUT_MONDE)
    if "--monde" in a and monde not in _bati.mondes():
        sortir("  monde inconnu : %s (présents : %s)"
               % (monde, ", ".join(_bati.mondes()) or "aucun"))

    bati, C = charger_bati(monde)
    L = charger_liens()

    # --- l'état -------------------------------------------------------------
    if not a:
        A = L["affectations"]
        print("  %d bâtiments engendrés, %d affectations, %d corps prêtés"
              % (len(bati), len(A), len(L["liens"])))
        for clef, v in sorted(A.items()):
            m = monde_de(v)
            if v.get("piece"):
                f = fiche_piece(m, v["piece"])
                vu = v.get("visible")
                marque = ("  [vu de tous]" if vu is True else
                          "  [vu de %s]" % ", ".join(vu) if isinstance(vu, list) else "")
                print("   %-34s -> pièce %-14s (%s) %s%s"
                      % (clef, v["piece"], m,
                         f["quartier"] if f else "** non creusée **", marque))
                continue
            bt, Ct = charger_bati(m)
            f = fiche_bati(bt, Ct, v.get("bat", -1), m)
            vu = v.get("visible")
            marque = ("  [vu de tous]" if vu is True else
                      "  [vu de %s]" % ", ".join(vu) if isinstance(vu, list) else "")
            ou = "" if m == DEFAUT_MONDE else " (%s)" % m
            print("   %-34s -> bâtiment %-6s%s %s%s"
                  % (clef, v.get("bat"), ou,
                     "%s, %s" % (f["usage"], f["quartier"]) if f
                     else "** hors du monde engendré **", marque))
        print()
        print("  python scripts/affecter.py --chercher --usage taverne "
              "--pres-de 1772,2789")
        return

    # --- replacer -----------------------------------------------------------
    # Avant tout le reste : c'est une réparation, elle ne se mêle à rien.
    if "--reancrer" in a:
        return reancrer(L, monde, vraiment)

    # --- consulter ----------------------------------------------------------
    if opt("--bati"):
        f = fiche_bati(bati, C, int(opt("--bati")[0]), monde)
        if not f: sortir("  aucun bâtiment de cet index.")
        print(dire_bati(f))
        pris = [k for k, v in L["affectations"].items()
                if v.get("bat") == f["bat"] and monde_de(v) == monde]
        if pris: print("  -> déjà affecté à %s" % ", ".join(pris))
        return

    if opt("--ou"):
        clef = opt("--ou")[0]
        f, comment = position(L, clef)
        if not f:
            print("  %s n'a pas d'adresse physique%s."
                  % (clef, " (affectation morte)" if comment else ""))
            return
        print(dire_bati(f))
        print("  (%s)" % comment)
        note = (L["affectations"].get(clef) or {}).get("note")
        if note: print("  %s" % note)
        return

    if opt("--entre", 2):
        c1, c2 = opt("--entre", 2)
        f1, _ = position(L, c1)
        f2, _ = position(L, c2)
        for c, f in ((c1, f1), (c2, f2)):
            if not f: sortir("  %s n'a pas d'adresse physique." % c)
        # Deux mondes engendrés ont chacun leur origine : leurs mètres ne se
        # soustraient pas. Une distance inventée entre Port-Réal et Peyredragon
        # aurait l'air d'un chiffre, et un chiffre, on le croit.
        if f1["monde"] != f2["monde"]:
            sortir("  %s est dans « %s », %s dans « %s » — deux mondes engendrés "
                   "n'ont pas la même origine, cette distance n'existe pas.\n"
                   "  (pour une route entre places, c'est la table peinte et "
                   "`jours_de_pr`, pas la géométrie.)"
                   % (c1, f1["monde"], c2, f2["monde"]))
        d = math.hypot(f1["x"] - f2["x"], f1["y"] - f2["y"])
        # 0,75 m par pas d'homme qui marche vite, 5 km/h pour le temps
        print("  %s -> %s" % (c1, c2))
        print("  %.0f m — soit %d pas, environ %d minutes de marche"
              % (d, round(d / 0.75), max(1, round(d / 83.0))))
        return

    if "--chercher" in a:
        usage = (opt("--usage") or [None])[0]
        quartier = (opt("--quartier") or [None])[0]
        combien = int((opt("--n") or ["8"])[0])
        pres = (opt("--pres-de") or [None])[0]
        px = py = None
        if pres:
            try:
                px, py = [float(v) for v in pres.replace(" ", "").split(",")]
            except ValueError:
                sortir("  --pres-de attend « x,y » (mètres).")
        pris = {v.get("bat") for v in L["affectations"].values()
                if monde_de(v) == monde}
        trouves = []
        for i, b in enumerate(bati):
            if usage and b[C["usage"]] != usage: continue
            if quartier and quartier.lower() not in b[C["quartier"]].lower():
                continue
            d = (math.hypot(b[C["x"]] - px, b[C["y"]] - py)
                 if px is not None else 0.0)
            trouves.append((d, i, b))
        if not trouves:
            print("  aucun bâtiment. (usages : %s)"
                  % ", ".join(sorted({b[C["usage"]] for b in bati})[:14]))
            return
        trouves.sort(key=lambda t: t[0])
        for d, i, b in trouves[:combien]:
            print(dire_bati(fiche_bati(bati, C, i, monde)))
            if px is not None: print("  à %.0f m du point donné" % d)
            if i in pris: print("  ** déjà affecté **")
            print()
        return

    # --- affecter -----------------------------------------------------------
    if opt("--affecter", 2):
        clef, cible = opt("--affecter", 2)
        genre, _, ident = clef.partition(":")
        if genre not in GENRES:
            sortir("  genre inconnu : %s (attendus : %s)"
                   % (genre or "(vide)", ", ".join(GENRES)))
        if not ident:
            sortir("  il manque l'identifiant : %s:<id>" % genre)
        connus = identifiants(genre)
        if connus is not None and ident not in connus:
            sortir("  aucun %s de cet id : %s — écris-le d'abord dans sa table."
                   % (genre, ident))
        # Une salle se vise par sa PIÈCE quand le monde l'a creusée : c'est la
        # seule cible qui survive à une régénération, puisqu'elle porte l'id du
        # plan et non un index de graine.
        pid = cible[6:] if cible.startswith("piece:") else cible
        if fiche_piece(monde, pid):
            fp = fiche_piece(monde, pid)
            print(dire_bati(fp))
            print("  -> %s prendrait cette pièce." % clef)
            if not vraiment:
                print("  (rien écrit — ajoute --vraiment)")
                return
            entree = dict(L["affectations"].get(clef) or {})
            entree.pop("bat", None)
            entree.pop("usage", None)
            entree["piece"] = pid
            entree["xyz"] = [round(fp["x"], 1), round(fp["y"], 1),
                             round(fp["z"], 1)]
            if monde == DEFAUT_MONDE:
                entree.pop("monde", None)
            else:
                entree["monde"] = monde
            nom = (opt("--nom") or [None])[0]
            if nom: entree["nom"] = nom
            note = (opt("--note") or [None])[0]
            if note: entree["note"] = note
            v = visibilite_demandee(a)
            if v is not None: entree["visible"] = v
            L["affectations"][clef] = entree
            ecrire(LIENS, L)
            print("  écrit dans etat/corps.json")
            return
        try:
            i = int(cible)
        except ValueError:
            sortir("  la cible est un index de bâtiment (un entier), ou une "
                   "pièce des intérieurs (`piece:<id>`). "
                   "Trouve-la avec --chercher.")
        f = fiche_bati(bati, C, i, monde)
        if not f: sortir("  aucun bâtiment d'index %d dans « %s »." % (i, monde))
        # Deux endroits de la fiction peuvent légitimement tomber sur le même
        # bâtiment — une porte et son corps de garde sont le même mètre carré,
        # et le plan les distingue parce que la SCÈNE les distingue. On ne
        # refuse donc pas : on le dit, et `--verifier` s'en souviendra. Refuser
        # obligerait à mentir sur la géographie pour contenter le script.
        if genre in OCCUPANTS:
            # L'unicité porte sur la PAIRE (monde, bat) : le 1554 de Port-Réal
            # et le 1554 de Peyredragon ne sont pas le même mètre carré.
            deja = [k for k, v in L["affectations"].items()
                    if v.get("bat") == i and monde_de(v) == monde and k != clef
                    and k.partition(":")[0] in OCCUPANTS]
            if deja:
                print("  ATTENTION : ce bâtiment est déjà celui de %s. Les deux "
                      "auront exactement les mêmes mètres." % ", ".join(deja))
        dedans = [k for k, v in L["affectations"].items()
                  if v.get("bat") == i and monde_de(v) == monde and k != clef
                  and k.partition(":")[0] in OCCUPANTS]
        if dedans and genre not in OCCUPANTS:
            print("  (à l'intérieur de %s)" % ", ".join(dedans))
        print(dire_bati(f))
        print("  -> %s prendrait ce bâtiment." % clef)
        if not vraiment:
            print("  (rien écrit — ajoute --vraiment)")
            return
        # On recopie les mètres DANS l'affectation. Le décor peut alors poser
        # l'étiquette sans ouvrir les cinq mégaoctets du bâti à chaque requête,
        # et `--verifier` compare la copie à la source : si la ville a été
        # réengendrée autrement, la dérive se voit au lieu de se taire.
        # Réaffecter n'efface pas ce qu'on avait écrit : le nom et la note sont
        # du travail de MJ, la cible est de la tuyauterie.
        entree = dict(L["affectations"].get(clef) or {})
        entree.update({"bat": i, "usage": f["usage"],
                       "xyz": [round(f["x"], 1), round(f["y"], 1),
                               round(f["z"], 1)]})
        # On n'écrit le monde que s'il n'est pas celui par défaut : l'absence
        # VAUT portreal, et un champ ajouté partout ferait un diff de neuf
        # lignes qui ne dit rien.
        if monde == DEFAUT_MONDE:
            entree.pop("monde", None)
        else:
            entree["monde"] = monde
        nom = (opt("--nom") or [None])[0]
        if nom: entree["nom"] = nom
        note = (opt("--note") or [None])[0]
        if note: entree["note"] = note
        v = visibilite_demandee(a)
        if v is not None: entree["visible"] = v
        L["affectations"][clef] = entree
        ecrire(LIENS, L)
        print("  écrit dans etat/corps.json")
        return

    # Montrer et cacher se font APRÈS coup, et c'est le cas normal : un endroit
    # est affecté le jour où l'on en a besoin pour calculer, et montré le jour
    # où le joueur le reconnaît de ses yeux. Les deux dates n'ont aucune raison
    # d'être la même.
    if opt("--montrer") or opt("--cacher"):
        montre = bool(opt("--montrer"))
        clef = (opt("--montrer") or opt("--cacher"))[0]
        if clef not in L["affectations"]:
            sortir("  %s n'est affecté à rien — affecte-le d'abord." % clef)
        pour = (opt("--pour") or [None])[0]
        v = ([s for s in pour.split(",") if s] if (montre and pour) else montre)
        if not vraiment:
            print("  %s deviendrait %s (ajoute --vraiment)"
                  % (clef, "visible pour " + ", ".join(v) if isinstance(v, list)
                     else ("visible de tous" if v else "invisible")))
            return
        L["affectations"][clef]["visible"] = v
        ecrire(LIENS, L)
        print("  %s : %s" % (clef, "visible pour " + ", ".join(v)
                             if isinstance(v, list)
                             else ("visible de tous" if v else "invisible")))
        return

    if opt("--defaire"):
        clef = opt("--defaire")[0]
        if clef not in L["affectations"]:
            sortir("  %s n'est affecté à rien." % clef)
        if not vraiment:
            print("  %s -> bâtiment %s serait défait (ajoute --vraiment)"
                  % (clef, L["affectations"][clef].get("bat")))
            return
        L["affectations"].pop(clef)
        ecrire(LIENS, L)
        print("  %s n'a plus d'adresse physique." % clef)
        return

    if "--verifier" in a:
        maux = verifier(L)
        if not maux:
            print("  %d affectations, rien à signaler." % len(L["affectations"]))
            return
        for m in maux: print("  " + m)
        sys.exit(1)

    print(__doc__)

