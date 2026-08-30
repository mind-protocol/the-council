# -*- coding: utf-8 -*-
"""ECRIRE — refaire les couvertures et les registres dans les cahiers,
verser sous controle optimiste, et l'entree CLI de scripts/couverture.py.
"""
import os
import re
import sys

import bibliotheque
import rapporteurs

from plan.couverture.lecture import (nu, sans_emoji, RACINE, LIVRES, VIEUX,
                                     ECRITS, charger)
from plan.couverture.blocs import blocs, marque
from plan.couverture.registres import CALCULE, deriver

# ─────────────────────────────────────────────── écrire la couverture
CHAMPS = [u"LE NOM", u"L'OBJET", u"LE PÉRIMÈTRE — DANS", u"LE PÉRIMÈTRE — HORS",
          u"L'ÉTAT ACTUEL", u"LA PLAGE", u"LA CONCLUSION", u"FERMÉE QUAND"]
SIGNE = {u"LE NOM": u"🏷️", u"L'OBJET": u"🎯", u"LE PÉRIMÈTRE — DANS": u"🧱",
         u"LE PÉRIMÈTRE — HORS": u"🚫", u"L'ÉTAT ACTUEL": u"📌", u"LA PLAGE": u"🔢",
         u"LA CONCLUSION": u"💡", u"FERMÉE QUAND": u"🔚"}


def refaire(b, pieces, inventaire):
    nom = nu(b.get("titre"))
    pend, eng, trous, liens, ech = blocs(nom, pieces, inventaire)
    tables = b["tables"]

    # 1 · l'ouverture : on garde tout ce qui est écrit, on ajoute LA CONCLUSION
    ouv = tables[0]
    largeur = len(ouv.get("colonnes") or [u"", u"", u"", u""])
    ecrit = {}
    for l in ouv.get("lignes") or []:
        c = (l if isinstance(l, list) else l.get("cellules")) or []
        if c:
            ecrit[sans_emoji(c[0]).upper()] = c
    neuves = []
    for ch in CHAMPS:
        c = ecrit.get(ch.upper())
        if c is None:
            c = [SIGNE[ch] + u" **" + ch + u"**"] + [u""] * (largeur - 1)
        neuves.append({"cellules": (c + [u""] * largeur)[:largeur]})
    if ech:
        r = [u"⏳ **LA PROCHAINE ÉCHÉANCE**", marque(ech[1], pieces) + u" — " + ech[0]] \
            + [u""] * largeur
        neuves.append({"cellules": r[:largeur]})
    ouv["lignes"] = neuves

    # 2 · les liens : les écrits restent, les dérivés se refont
    i_liens = next((i for i, t in enumerate(tables)
                    if re.search(u"affaires? li", sans_emoji(t.get("titre") or u""), re.I)), None)
    COLS_L = [u"🪢 Le lien", u"🔗 L'affaire", u"🔢 Notre pièce", u"🔢 La leur", u"📝 Pourquoi"]
    gardees = []
    if i_liens is not None:
        for l in tables[i_liens].get("lignes") or []:
            c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
            if not any(c):
                continue
            # ancienne forme : [affaire, relation, pourquoi]
            t0 = sans_emoji(tables[i_liens].get("colonnes", [u""])[0]).lower()
            if t0.startswith(u"l'affaire") or t0.startswith(u"laffaire"):
                lien = VIEUX.get(c[1].lower(), c[1].lower()) if len(c) > 1 else u""
                c = [lien, c[0], u"", u"", c[2] if len(c) > 2 else u""]
            c = (c + [u""] * 5)[:5]
            c[0] = VIEUX.get(c[0].lower(), c[0])
            if c[0].lower() in ECRITS:
                gardees.append({"cellules": c})
    derivees = [{"cellules": [l[0], l[1], l[2], l[3], u""]} for l in liens]
    table_liens = {"titre": u"🔗 Affaires liées — les liens écrits, puis les calculés",
                   "colonnes": COLS_L,
                   "lignes": (gardees + derivees) or [{"cellules": [u""] * 5}]}

    # 3 · les trois blocs calculés
    t_pend = {"titre": u"⛓️ Ce qui pend, et sur qui" + CALCULE,
              "colonnes": [u"🧭 Sens", u"🔢 Notre pièce", u"🔢 La leur", u"🔗 L'affaire"],
              "lignes": [{"cellules": l} for l in pend] or
                        [{"cellules": [u"—", u"", u"", u"rien ne traverse"]}]}
    t_eng = {"titre": u"🔨🪶 Ce qu'on engage, et qui d'autre le veut" + CALCULE,
             "colonnes": [u"🔢 La pièce", u"⚔️ Nos actions", u"🔗 Aussi engagée par"],
             "lignes": [{"cellules": l} for l in eng] or
                       [{"cellules": [u"—", u"", u"aucun moyen, aucun office"]}]}
    t_trous = {"titre": u"🕳️ Les trous" + CALCULE,
               "colonnes": [u"🕳️ Le défaut", u"🔢 Les pièces"],
               "lignes": [{"cellules": l} for l in trous] or
                         [{"cellules": [u"aucun — la chaîne tient de bout en bout", u""]}]}

    reste = [t for i, t in enumerate(tables) if i != 0 and i != i_liens
             and not re.search(u"ce qui pend|ce qu'on engage|les trous",
                               sans_emoji(t.get("titre") or u""), re.I)]
    b["tables"] = [ouv, table_liens, t_pend, t_eng, t_trous] + reste
    return len(pend), len(eng), len(trous), len(derivees)


def verser(session):
    """Verse uniquement les volumes touchés, avec contrôle optimiste.

    Tant que le monolithe est actif, on conserve sa sauvegarde historique et
    toute écriture concurrente fait refuser le lot. Après la scission, la
    session compare seulement les cahiers qu'elle a réellement changés : deux
    titulaires peuvent enfin écrire deux livres distincts en parallèle.
    """
    import shutil, time
    scindee = bibliotheque.est_scindee(os.path.join(RACINE, "etat"))
    sauve = None
    if not scindee:
        sauve = LIVRES + u".avant-couverture-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(LIVRES, sauve)
    try:
        session.sauver()
    except bibliotheque.BibliothequeModifiee as exc:
        if sauve and os.path.exists(sauve):
            os.remove(sauve)
        sys.stdout.write(u"\n‼ %s\n" % exc)
        return False
    if sauve:
        sys.stdout.write(u"  sauvegarde : %s\n" % os.path.basename(sauve))
    return True


def refaire_registres(livres):
    """Pose les quatre index dérivés dans `livres`. Rend le compte rendu."""
    sorties = deriver(livres)
    for b in livres:
        s = sorties.get(str(b.get("id") or u""))
        if s:
            b["lignes"], b["titre"] = s["lignes"], s["titre"]
            b["colonnes"] = s["colonnes"]
    return sorties

def main(args=None):
    """L'entree CLI de scripts/couverture.py — la CLI est gelee (facade)."""
    if args is None:
        args = sys.argv[1:]
    verif = "--verifier" in args
    filtre = args[args.index("--affaire") + 1] if "--affaire" in args else None

    if "--registres" in args:
        session = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
        livres = session.livres
        pieces_avant = charger(livres)[1]
        sorties = refaire_registres(livres)
        for bid, s in sorted(sorties.items()):
            sys.stdout.write(u"%-20s %4d ligne(s) → %4d · conservees %d\n"
                             % (bid, s["avant"], len(s["lignes"]), len(s["gardees"])))
            for n, motif, a, b_ in s["gardees"]:
                sys.stdout.write(u"     ~ %-6s %-14s %s%s\n" % (n, motif, a[:44],
                                 (u"   ← cahier : " + b_[:40]) if b_ else u""))
            if s["sans_logis"]:
                sys.stdout.write(u"     ! colonne(s) sans logis au cahier : %s\n"
                                 % u" · ".join(s["sans_logis"]))
        # LA GARDE QUI COMPTE : le compte de references pendantes ne monte pas.
        av = set(pieces_avant)
        pend_av = sorted(v for n in av for v in pieces_avant[n]["vers"] if v not in av)
        sys.stdout.write(u"\n  pieces avant %d · pendantes avant %d %s\n"
                         % (len(av), len(pend_av), pend_av))
        if verif:
            sys.stdout.write(u"--verifier : rien n'a ete ecrit.\n")
            sys.exit(0)
        if not verser(session):
            sys.exit(1)
        ap = charger(bibliotheque.charger(os.path.join(RACINE, "etat")))[1]
        pend_ap = sorted(v for n in ap for v in ap[n]["vers"] if v not in ap)
        sys.stdout.write(u"  pieces apres %d · pendantes apres %d %s\n"
                         % (len(ap), len(pend_ap), pend_ap))
        if len(pend_ap) > len(pend_av):
            sys.stdout.write(u"‼ LES PENDANTES ONT MONTE — relire la sauvegarde.\n")
            sys.exit(1)
        rapporteurs.battre("couverture-registres", u"4 registres derives")
        sys.stdout.write(u"4 registre(s) derive(s) dans etat/books.json\n")
        sys.exit(0)

    session = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
    livres, pieces, inventaire, affaires = charger(session.livres)
    if filtre:
        affaires = [a for a in affaires if sans_emoji(filtre).lower() in sans_emoji(a["titre"]).lower()]

    for b in affaires:
        n = refaire(b, pieces, inventaire)
        sys.stdout.write(u"%-46s pend %d · engage %d · trous %d · liens calcules %d\n"
                         % (nu(b["titre"])[:46], n[0], n[1], n[2], n[3]))
    if verif:
        sys.stdout.write(u"--verifier : rien n'a ete ecrit.\n")
    elif verser(session):
        rapporteurs.battre("couverture", u"%d couvertures" % len(affaires))
        sys.stdout.write(u"%d couverture(s) refaite(s) dans etat/books.json\n" % len(affaires))
