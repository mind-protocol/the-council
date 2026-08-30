# -*- coding: utf-8 -*-
"""CLI — l'entree de scripts/criticite.py, gelee (la facade l'appelle par
la porte plan/expose.py).
"""
import argparse
import io
import json
import os
import re
import sys

import rapporteurs
import plan_modele as PM

from plan.expose import nu, sans_emoji, NOM_GENRE, FINI, premier_mot

from plan.criticite.page import (LARGEUR, titre, cale, statut, prix, faite)
from plan.criticite.graphe import (RACINE, POIDS, CONJONCTIF, DISJONCTIF,
                                   amonts, atteignables, cercles, pourquoi)
from plan.criticite.hommes import (gens, cle_homme, idees, porte_des_hommes,
                                   charge_des_hommes, section_charge, affiche)
from plan.criticite.affaires import totaux_par_affaire, veille
from plan.criticite.decisions import (decisions_ouvertes, arbre_des_decisions,
                                      section_decisions, plan_de, declaree,
                                      cout, cout_du_plan, dire_cout,
                                      descendance)
from plan.criticite.note import (NOTE_NEUTRE, objectifs_finaux, amplitude,
                                 poids_des_etats, masse, portee)
from plan.criticite.calcul import (raison_du_zero, calculer, charge_de,
                                   GENRES_MESURES)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--combien", type=int, default=25)
    ap.add_argument("--affaire")
    ap.add_argument("--restant", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--sans-dep", action="store_true")
    ap.add_argument("--dep", choices=("interne", "toutes", "aucune"), default="interne")
    ap.add_argument("--etats", action="store_true")
    ap.add_argument("--actions-ou", action="store_true")
    ap.add_argument("--pourquoi", metavar=u"N°")
    # POUR L'ÉCRAN, ET SANS RIEN ÉCRIRE SUR LE DISQUE. Une colonne de criticité
    # posée dans `books.json` serait effacée au prochain `couverture.py`, qui
    # regénère les registres à quatre colonnes exprès — et elle mentirait dès la
    # première action cochée. Le serveur appelle donc ce mode et sert le résultat
    # à côté du volume ; les livres restent ce qu'ils sont, l'écran les augmente.
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--acteurs", action="store_true")
    ap.add_argument("--charge", nargs="?", const="", metavar=u"QUI")
    ap.add_argument("--decisions", nargs="?", const="", metavar=u"N°")
    ap.add_argument("--vue-de", default=PM.personnage_par_defaut(),
                    help="siège dont on mesure l'étagère visible")
    a = ap.parse_args()

    modele = PM.charger(a.vue_de)
    livres, pieces, inventaire, affaires = (modele["livres"], modele["pieces"],
                                            modele["inventaire"], modele["affaires"])
    prix_de = prix(livres)
    # La date du monde, notée à côté de chaque instantané : elle ne sert pas à
    # comparer (deux mesures d'un même jour de jeu peuvent être séparées d'une
    # semaine de travail) mais à relire la trace en années de règne.
    date = json.load(io.open(os.path.join(RACINE, "etat", "monde.json"),
                             encoding="utf-8")).get("date") or {}
    mode_dep = u"aucune" if a.sans_dep else a.dep
    lignes, base, poids, saisis, m0, dehors = calculer(
        pieces, mode_dep=mode_dep, optimiste=not a.strict,
        actions_ou=a.actions_ou)
    # CE QUI ATTEND AILLEURS — le signal, une fois requalifie. Un saut, pas une
    # cascade : le poids de ce qui, dans un AUTRE cahier, nomme cette piece dans
    # son « depend de ». On somme leur criticite propre, pas leur nombre : dix
    # pieces sans consequence pesent moins qu'une seule qui tient un etat.
    crit = {n: c for c, pt, n, p in lignes}
    attendu = {n: sum(crit.get(m, 0) for m in ms) for n, ms in dehors.items()}

    if a.json:
        # La portee BRUTE — les etats qu'un pas sert, atteignables ou non. Elle
        # separe « ne sert rien » de « sert ce que le plan ne sait pas
        # atteindre » ; `calculer` la jette apres usage, on la refait ici. Le
        # cache est celui de `portee` : le second passage ne coute rien.
        cache_portee = {}
        grappes = cercles(pieces, *amonts(pieces, mode_dep, a.actions_ou)[:2])
        noue = {m: i for i, g in enumerate(grappes) for m in g}
        offices, moyens = gens(livres)
        # LA PAGE NE DOIT PAS RELIRE `books.json` POUR AFFICHER UN NOM. Le
        # fichier fait 2,4 Mo ; le faire descendre au navigateur pour y
        # rechercher trois cents intitulés serait payer mille fois le prix du
        # calcul lui-meme. On sert donc la ligne entiere, prete a poser.
        # QUI TIENT QUOI, PAR MOYEN. `pas[n].moyens` ne donne que des numeros ;
        # sans cette table, la page ne peut pas dire a qui l'on tire, et sa
        # colonne « on tire » reste a zero sans que rien n'echoue. On sert le
        # nom tel qu'il est ECRIT au registre des moyens : la jointure avec les
        # titulaires d'offices (« Dame Aurore » d'un cote, « Aurore » de
        # l'autre) se refait cote page, qui seule sait sur quoi elle regroupe.
        tenu = {m: list(qui) for m, (_nom, qui) in moyens.items() if qui}
        # LA CHARGE DES HOMMES SE SERT D'ICI, ET NON REFAITE DANS LE NAVIGATEUR.
        # La page a de quoi la recalculer — elle a `pas`, `offices` et `tenu` —
        # et c'est precisement ce qu'il ne faut pas : deux definitions de « ce
        # qu'un homme ne voit pas », dont l'une derive au premier repli de nom
        # qu'on ajoute ici. `charge_des_hommes()` est deja la seule main qui
        # replie « jacaerys » sur « jacaerys-velaryon » ; on sert son resultat.
        #
        # ON SERT DES SOMMES PAR AFFAIRE, PAS UN TOTAL. Le calcul voit les
        # quarante-deux cahiers du depot, cahiers d'un autre siege compris ; un
        # total tout cuit serait donc infiltrable et l'ecran n'aurait aucun
        # moyen de le borner. Rendues par cahier, les sommes se restreignent a
        # l'etagere que ce siege peut ouvrir — c'est la meme borne que le volume
        # « Les pas », appliquee une fois de plus et non reinventee.
        def _par_affaire(L):
            out = {}
            for s, n, p in L:
                c = out.setdefault(p["affaire"] or u"", {"s": 0.0, "pas": 0})
                c["s"] += s
                c["pas"] += 1
            return out
        charge = {q: {"offices": h["offices"], "moyens": h["moyens"],
                      "cahiers": h["cahiers"],
                      "vu": _par_affaire(h["vu"]),
                      "sien_ailleurs": _par_affaire(h["sien_ailleurs"]),
                      "tire": _par_affaire(h["tire"])}
                  for q, h in charge_des_hommes(pieces, affaires, lignes,
                                                attendu, offices, moyens).items()}
        # La table `--acteurs`, servie telle quelle : l'écran fait varier la
        # taille des ronds du plan sur `porte`, et il ne recalcule rien — la
        # jointure office↔homme est devinée, elle se fait ici ou nulle part.
        acteurs, sans_office, office_en_clair = porte_des_hommes(lignes, offices,
                                                                 moyens)
        sys.stdout.write(json.dumps({
            "vue_de": modele["vue_de"],
            "portee": PM.mesures(modele),
            "charge": charge,
            "acteurs": acteurs,
            "hors_acteurs": {"sans_office": {"s": round(sans_office[0], 3),
                                             "pas": sans_office[1]},
                             "office_en_clair": {"s": round(office_en_clair[0], 3),
                                                 "pas": office_en_clair[1]}},
            "tenu": tenu,
            "masse": m0, "saisis": saisis, "mode_dep": mode_dep,
            "date": json.load(io.open(os.path.join(RACINE, "etat", "monde.json"),
                                      encoding="utf-8")).get("date") or {},
            "etats": {n: {"poids": w, "atteignable": bool(base.get(n)),
                          "nom": pieces[n]["nom"], "affaire": pieces[n]["affaire"]}
                      for n, w in poids.items()},
            "cercles": [{"taille": len(g),
                         "pieces": [{"n": m, "genre": pieces[m]["genre"],
                                     "nom": pieces[m]["nom"],
                                     "affaire": pieces[m]["affaire"]} for m in g]}
                        for g in grappes],
            "offices": {o: {"nom": v[0], "qui": v[1]} for o, v in offices.items()},
            "tenu": {m: v[1] for m, v in moyens.items()},
            # Les sommes par cahier, avec l'écart contre la veille. Elles ne
            # sont pas dérivables à l'écran : le passé n'existe plus dans
            # `books.json` une fois qu'il a été réécrit.
            "affaires": veille(totaux_par_affaire(lignes, attendu, pieces, affaires),
                               date),
            "idees": idees(pieces,
                           {n: {"perte": c, "attendu": attendu.get(n, 0)}
                            for c, pt, n, p in lignes},
                           poids, base),
            "pas": {n: {"perte": c, "portee": pt,
                        "attendu": attendu.get(n, 0),
                        # POURQUOI CE CHIFFRE EST CE QU'IL EST. Sans elle, un
                        # zéro d'amont bloqué se lit comme un zéro d'accompli,
                        # et l'écran range sous « rien à faire » ce qui est en
                        # réalité « le plan ne sait pas y arriver ».
                        "raison": raison_du_zero(p, c, pt,
                                                 portee(n, pieces, poids,
                                                        cache_portee),
                                                 attendu.get(n, 0)),
                        "cercle": noue.get(n),
                        "genre": p["genre"], "nom": p["nom"],
                        "affaire": p["affaire"], "etat": p["etat"],
                        "faite": faite(p),
                        "office": p.get("office") or u"",
                        "moyens": p.get("moyens") or [],
                        "prix": prix_de.get(n) or u""}
                    for c, pt, n, p in lignes},
        }, ensure_ascii=False))
        return

    titre(u"⚖️ LA CRITICITÉ — ce que le plan perd si ce pas-là rate")
    sys.stdout.write(
        u"  vue de %s · %d pièces · %d états cibles, dont %d atteignables (masse %g)\n"
        u"  poids saisis à la main : %d — les autres valent 1 (etat/poids-etats.json)\n"
        u"  ET/OU lu sur le genre · « dépend de » %s · verrou sans clef : %s\n"
        % (modele["vue_de"], len(pieces), len(poids),
           sum(1 for e in poids if base.get(e)), m0, saisis,
           {u"interne": u"bloque dans le cahier, compté dehors",
            u"toutes": u"bloque partout", u"aucune": u"ignoré"}[mode_dep],
           u"bloque (strict)" if a.strict else u"se lève quand même"))

    tous, un, _ = amonts(pieces, mode_dep=mode_dep, actions_ou=a.actions_ou)
    if a.pourquoi:
        titre(u"❓ POURQUOI %s N'EST PAS ATTEIGNABLE" % a.pourquoi)
        pourquoi(a.pourquoi, pieces, tous, un, base)
        return

    grappes = cercles(pieces, tous, un)
    if grappes:
        titre(u"🔁 LES CERCLES — %d chaîne%s qui se mord%s la queue, donc ne partira%s jamais"
              % (len(grappes), u"s" if len(grappes) > 1 else u"",
                 u"ent" if len(grappes) > 1 else u"", u"ient" if len(grappes) > 1 else u""))
        for g in grappes[:12]:
            # UNE GRAPPE DE QUATRE-VINGT-NEUF PIECES N'EST PAS UN CERCLE QU'ON
            # LIT : imprimee en chaine, elle occupe six lignes et ne se repare
            # pas. On dit alors sa taille et les cahiers qu'elle traverse, et
            # l'on renvoie a `--pourquoi`. Les petites, elles, se lisent et se
            # coupent d'un trait de plume — ce sont celles qui valent l'impression.
            if len(g) > 8:
                affs = sorted({pieces[m]["affaire"] for m in g if pieces[m]["affaire"]})
                sys.stdout.write(u"  🕸️ %d pièces enchevêtrées, %d cahiers — %s…\n"
                                 % (len(g), len(affs), u" · ".join(affs[:3])))
                sys.stdout.write(u"      commence à %s · `--pourquoi %s` pour dérouler\n"
                                 % (g[0], g[0]))
                continue
            sys.stdout.write(u"  %s\n" % u" → ".join(
                NOM_GENRE.get(pieces[m]["genre"], u"") + u" " + m for m in g))
            sys.stdout.write(u"      %s\n" % cale(pieces[g[0]]["nom"], 88))
        sys.stdout.write(
            u"\n  Aucun des six détecteurs de `couverture.py` ne les voit : chaque ligne,\n"
            u"  prise seule, est bien formée. Tant qu'un cercle tient, tout ce qui pend\n"
            u"  derrière est à zéro — 🕳️ ci-dessous.\n")

    if a.decisions is not None:
        section_decisions(pieces, lignes, attendu, prix_de, a.combien,
                          a.decisions or None)
        return

    if a.charge is not None:
        offices, moyens = gens(livres)
        section_charge(charge_des_hommes(pieces, affaires, lignes, attendu,
                                         offices, moyens),
                       a.combien, a.charge or None)
        return

    if a.acteurs:
        offices, moyens = gens(livres)
        hommes, sans, en_clair = porte_des_hommes(lignes, offices, moyens)
        titre(u"👤 CE QUE CHAQUE HOMME PORTE — criticité de ses pas, et de ce qu'il tient")
        sys.stdout.write(u"  %s%s%s%s%s\n" % (
            cale(u"porte", 8), cale(u"pas", 6), cale(u"goulots", 9),
            cale(u"on tire", 9), u"l'homme, et ses offices"))
        rang = sorted(hommes.items(), key=lambda x: -x[1]["porte"])
        for q, h in [x for x in rang if x[1]["pas"]][:a.combien]:
            sys.stdout.write(u"  %s%s%s%s%s\n" % (
                cale(u"%g" % h["porte"], 8), cale(u"%d" % h["pas"], 6),
                cale(u"%d" % h["goulots"], 9), cale(u"%g" % h["tire"], 9),
                cale(h["nom"] + u"  · " + u" ".join(h["offices"]), 58)))
        titre(u"🪝 CE QU'ON LEUR TIRE — ils tiennent un moyen dont le plan a besoin")
        for q, h in sorted(hommes.items(),
                           key=lambda x: -x[1]["tire"])[:min(10, a.combien)]:
            if h["pas"] or not h["tire_pas"]:
                continue
            sys.stdout.write(u"  %s%s%s\n" % (cale(u"%g" % h["tire"], 8),
                                              cale(u"%d pas" % h["tire_pas"], 9),
                                              h["nom"]))
        sys.stdout.write(
            u"\n  🕳️ sans office écrit : %g de criticité sur %d pas"
            u"  ·  office nommé mais sans numéro : %g sur %d\n"
            u"      Ce premier chiffre est le seul qui n'ait personne pour le porter.\n"
            u"      Jointure devinée entre les deux registres : titres retirés, « moi » = la reine.\n"
            % (sans[0], sans[1], en_clair[0], en_clair[1]))
        return

    if a.etats:
        titre(u"🎯 LES ÉTATS CIBLES — poids, et atteignables ou non")
        for n, w in sorted(poids.items(), key=lambda x: (-x[1], x[0])):
            p = pieces[n]
            if a.affaire and a.affaire.lower() not in sans_emoji(p["affaire"]).lower():
                continue
            sys.stdout.write(u"  %s %-6s %s  %s  %s\n" % (
                u"✅" if base.get(n) else u"🚫", n, cale(u"%g" % w, 4),
                cale(p["nom"], 52), cale(p["affaire"], 30)))
        return

    ret = [l for l in lignes if l[0] > 0]
    red = [l for l in lignes if l[0] == 0 and l[1] > 0]
    mort = [l for l in lignes if l[1] == 0]
    if a.affaire:
        f = lambda L: [l for l in L if a.affaire.lower() in sans_emoji(l[3]["affaire"]).lower()]  # noqa: E731
        ret, red, mort = f(ret), f(red), f(mort)
    if a.restant:
        f = lambda L: [l for l in L if not faite(l[3])]  # noqa: E731
        ret, red, mort = f(ret), f(red), f(mort)

    titre(u"🔺 LES GOULOTS — %d pas dont la perte coûte quelque chose" % len(ret))
    # PERTE PLUS GRANDE QUE PORTEE N'EST PAS UNE INCOHERENCE, c'est le seul
    # endroit ou les `depend de` se voient : la portee ne suit que la remontee
    # de l'affaire, la perte compte aussi ce qui attend la piece AILLEURS.
    sys.stdout.write(
        u"  « attendu » = le poids qui, dans un AUTRE cahier, se casse la figure sans ce pas.\n"
        u"  Un saut, jamais une cascade : c'est un signal de coordination, pas un prérequis.\n")
    sys.stdout.write(u"  %s%s%s%s%s%s\n" % (cale(u"perte", 7), cale(u"portée", 7),
                                            cale(u"attendu", 8), cale(u"n°", 10),
                                            cale(u"le pas", 42), u"état"))
    for c, pt, n, p in sorted(ret, key=lambda x: (-(x[0] + attendu.get(x[2], 0)), x[2]))[:a.combien]:
        sys.stdout.write(u"  %s%s%s%s%s%s\n" % (
            cale(u"%g" % c, 7), cale(u"%g" % pt, 7),
            cale(u"%g" % attendu[n] if attendu.get(n) else u"—", 8),
            cale(NOM_GENRE.get(p["genre"], u"") + u" " + n, 10),
            cale(p["nom"], 42), statut(p)))

    titre(u"➖ LES SUBSTITUABLES — %d pas de grande portée qu'on peut perdre sans rien perdre"
          % len(red))
    for c, pt, n, p in sorted(red, key=lambda x: (-x[1], x[2]))[:min(8, a.combien)]:
        sys.stdout.write(u"  %s%s%s%s\n" % (
            cale(u"%g" % pt, 7), cale(NOM_GENRE.get(p["genre"], u"") + u" " + n, 10),
            cale(p["nom"], 48), statut(p)))

    titre(u"🕳️ LES ORPHELINS — %d pas qui ne servent aucun état atteignable" % len(mort))
    sys.stdout.write(u"  " + u" · ".join(
        NOM_GENRE.get(p["genre"], u"") + u" " + n for _, _, n, p in mort[:40]) + u"\n")

    # Le prix, en prose, pour les premiers seulement — c'est le seul endroit
    # ou il a une chance d'etre lu.
    titre(u"💰 CE QUE COÛTENT LES CINQ PREMIERS — la colonne des clefs, telle quelle")
    for c, pt, n, p in sorted(ret, key=lambda x: (-(x[0] + attendu.get(x[2], 0)), x[2]))[:5]:
        sys.stdout.write(u"  %s %s\n     %s\n" % (
            cale(n, 6), cale(p["nom"], 60), prix_de.get(n) or u"— rien d'écrit —"))

    titre(u"🏰 PAR AFFAIRE — la masse de criticité que chaque cahier porte")
    par = veille(totaux_par_affaire(lignes, attendu, pieces, affaires), date)
    sys.stdout.write(u"  %s%s%s%s\n" % (cale(u"score", 8), cale(u"depuis", 8),
                                        cale(u"pas", 6), u"le cahier"))
    for aff, o in sorted(par.items(), key=lambda x: -x[1]["score"])[:15]:
        e = o.get("ecart")
        sys.stdout.write(u"  %s%s%s%s\n" % (
            cale(u"%g" % o["score"], 8),
            cale(u"—" if e is None else (u"%+g" % e), 8),
            cale(u"%d" % o["pas"], 6), cale(aff, 58)))
    sys.stdout.write(
        u"\n  ⚠️  Un score dérivé de ce qui est ÉCRIT mesure la rédaction autant que\n"
        u"      l'importance : le nombre de pas est là pour que le gonflement se voie.\n")



def entree():
    main()
    # Le battement se pose APRES main(), donc seulement si elle est allee
    # au bout : un plantage ne bat pas, et c est le mecanisme entier.
    rapporteurs.battre("criticite", u"classement refait")
