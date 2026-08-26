# -*- coding: utf-8 -*-
# LE BILAN — six chiffres, le même jour de la semaine prochaine.
#
# POURQUOI CE FICHIER EXISTE. On a posé aujourd'hui six dispositifs, et chacun
# attend une mesure pour être réglé : le plafond de la carte muette, l'écart des
# affaires, l'adoption des bras-jours, les fourches déclarées. « On laisse
# passer du temps et on mesure » est la bonne conduite — c'est ainsi que le
# tunnel a posé son plafond, après coup et sur un chiffre. Mais une mesure qu'il
# faut refaire à la main ne se refait pas : elle a coûté une nuit la première
# fois, et personne ne recommencera.
#
# Ce script ne mesure donc rien de neuf. Il RASSEMBLE ce que les autres savent
# déjà dire, l'écrit dans `etat/bilan.jsonl` et le compare à la ligne
# précédente. Une commande, six chiffres, un écart.
#
# IL N'ÉCRIT QUE SA PROPRE TRACE. Rien dans `books.json`, rien dans le plan.
#
# Usage :
#     python scripts/bilan.py            mesure, compare, et pose la ligne
#     python scripts/bilan.py --sec      mesure et compare, n'écrit rien
import io

import rapporteurs
import json
import os
import re
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TRACE = os.path.join(RACINE, "etat", "bilan.jsonl")
# LES EMPREINTES — ce qui permet de dire « cette pièce est neuve ».
#
# Le bilan compte des totaux ; il ne sait pas QUELLES pièces ont bougé. Or c'est
# la question qu'un homme pose en ouvrant l'échiquier le matin : qu'est-ce qui a
# changé depuis hier ? Aucun total ne répond à ça, et rien dans `books.json` ne
# garde d'hier — le fichier est réécrit, le passé disparaît.
#
# On garde donc, à côté du bilan, une empreinte par pièce : un condensé de ce
# qui la définit (son nom, ce qu'elle sert, ce dont elle dépend, son état, son
# office, ses moyens). Une pièce absente hier est NEUVE ; une pièce dont
# l'empreinte a changé est RETOUCHÉE ; une pièce disparue l'est aussi. Trois
# faits, une ligne de 1400 condensés — vingt kilo-octets par jour, et le seul
# moyen d'avoir une mémoire du plan.
EMPREINTES = os.path.join(RACINE, "etat", "plan-empreintes.jsonl")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def empreinte_des_pieces(pieces):
    """{numéro: condensé}. Le condensé porte ce qui, s'il change, change la
    pièce pour un lecteur : son nom, sa remontée, ses dépendances, son état, son
    porteur, ses moyens, ses exclusions. Il ne porte PAS la prose du « ce qu'on
    fait » — une reformulation n'est pas un mouvement du plan, et la compter
    comme tel ferait clignoter la moitié de l'échiquier après une relecture."""
    import hashlib
    out = {}
    for n, p in pieces.items():
        cle = u"|".join([p.get("nom") or u"", u",".join(p.get("vers") or []),
                         u",".join(p.get("dep") or []), p.get("etat") or u"",
                         p.get("office") or u"", u",".join(p.get("moyens") or []),
                         u",".join(p.get("exclut") or [])])
        out[n] = hashlib.sha1(cle.encode("utf-8")).hexdigest()[:8]
    return out


def poser_empreintes(pieces, quand, vue_de=None):
    emp = empreinte_des_pieces(pieces)
    with io.open(EMPREINTES, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"quand": quand, "vue_de": vue_de, "pieces": emp},
                           ensure_ascii=False) + u"\n")
    return emp


def mesurer(vue_de=None):
    import criticite as C
    import plan_modele as PM
    modele = PM.charger(vue_de)
    livres, pieces, affaires = (modele["livres"], modele["pieces"],
                                modele["affaires"])
    lignes, base, poids, saisis, m0, dehors = C.calculer(pieces)
    tous, un, _d = C.amonts(pieces)
    ok = C.atteignables(pieces, tous, un)
    dec, aval, rac = C.arbre_des_decisions(pieces)
    prix = C.prix(livres)

    fins = C.objectifs_finaux(pieces)
    orphelins = sum(1 for c, pt, n, p in lignes if pt == 0)
    # L'adoption du chiffrage, sur les seules voies de premier rang : c'est là
    # qu'on l'a demandée, c'est donc là qu'il faut la lire. La compter sur les
    # neuf cents prix du plan donnerait un taux qui ne bouge jamais.
    import collections
    sous = collections.defaultdict(list)
    for n, p in pieces.items():
        if p["genre"] == "action":
            for k in p["vers"]:
                if k in pieces and pieces[k]["genre"] == "clef":
                    sous[k].append(n)
    voies = [(v, k) for v in rac for k in dec[v]]
    a_chiffrer = set()
    chiffrees = set()
    for v, k in voies:
        for a in C.plan_de(k, pieces, sous):
            (chiffrees if C.cout(prix.get(a)).get("lisible") else a_chiffrer).add(a)

    # La main sur la carte : le même compte que `carte_muette`, sur tout le flux.
    parlants = mains = 0
    try:
        import carte_muette as CM
        lieux = CM._lieux()
        motif = re.compile(u"|".join(re.escape(x) for x in
                                     sorted(lieux, key=len, reverse=True)))
        occasions = muettes = 0
        for l in io.open(os.path.join(RACINE, "etat", "flux.jsonl"), encoding="utf-8"):
            l = l.strip()
            if not l:
                continue
            try:
                it = json.loads(l)
            except ValueError:
                continue
            if it.get("type") not in ("replique", "geste", "table"):
                continue
            parlants += 1
            pose = CM._pose(it)
            if pose:
                mains += 1
            if motif.search(it.get("texte") or u"") and CM.CHIFFRE.search(it.get("texte") or u""):
                occasions += 1
                if not pose:
                    muettes += 1
    except Exception as e:
        sys.stderr.write(u"  (carte non mesurée : %s)\n" % e)
        occasions = muettes = 0

    return {
        "quand": time.time(),
        "vue_de": modele["vue_de"],
        "pieces": len(pieces),
        "etats_atteignables": sum(1 for n in poids if ok.get(n)),
        "etats": len(poids),
        "objectifs_atteignables": sum(1 for n in fins if ok.get(n)),
        "objectifs": len(fins),
        "cercles": len(C.cercles(pieces, tous, un)),
        "orphelins": orphelins,
        "fourches": len(dec),
        "fourches_declarees": sum(1 for v, ks in dec.items() if C.declaree(ks, pieces)),
        "voies_premier_rang": len(voies),
        "actions_chiffrees": len(chiffrees),
        "actions_a_chiffrer": len(a_chiffrer),
        "flux_parlants": parlants,
        "flux_mains": mains,
        "carte_occasions": occasions,
        "carte_muettes": muettes,
    }


LIGNES = [
    (u"états cibles atteignables", "etats_atteignables", "etats", True),
    (u"objectifs finaux atteignables", "objectifs_atteignables", "objectifs", True),
    (u"cercles de dépendance", "cercles", None, False),
    (u"pas orphelins", "orphelins", None, False),
    (u"fourches déclarées ⛔", "fourches_declarees", "fourches", True),
    (u"actions de fourche chiffrées", "actions_chiffrees", "actions_a_chiffrer", None),
    (u"mains sur la carte (tout le flux)", "flux_mains", "flux_parlants", True),
    (u"occasions de carte restées muettes", "carte_muettes", "carte_occasions", False),
]


def dire(m, avant):
    j = time.strftime(u"%d/%m à %Hh%M", time.localtime(m["quand"]))
    sys.stdout.write(u"\n⚖️  BILAN — %s · vue de %s · %d pièces au plan\n%s\n"
                     % (j, m.get("vue_de") or u"?", m["pieces"], u"─" * 78))
    if avant:
        sys.stdout.write(u"  écart depuis le %s\n\n"
                         % time.strftime(u"%d/%m %Hh%M", time.localtime(avant["quand"])))
    for nom, a, b, mieux_haut in LIGNES:
        v = m.get(a, 0)
        # LE DÉNOMINATEUR CHANGE DE SENS SELON LA LIGNE : « 12 sur 39 » pour une
        # part, « 34 chiffrées, 72 restantes » pour un reste. `mieux_haut = None`
        # dit le second cas, et l'on n'imprime alors aucun pourcentage — 34 sur
        # 106 n'aurait pas le même sens que 12 sur 39.
        if b and mieux_haut is None:
            corps = u"%d chiffrées, %d restantes" % (v, m.get(b, 0))
        elif b:
            d = m.get(b, 0)
            corps = u"%d / %d  (%.0f %%)" % (v, d, (100.0 * v / d) if d else 0)
        else:
            corps = u"%d" % v
        ec = u""
        if avant is not None and a in avant:
            delta = v - avant[a]
            if delta:
                bon = (delta > 0) == bool(mieux_haut) if mieux_haut is not None else delta > 0
                ec = u"   %s%+g" % (u"✔ " if bon else u"✖ ", delta)
        sys.stdout.write(u"  %-38s %s%s\n" % (nom, corps, ec))
    sys.stdout.write(
        u"\n  Ce qu'on attend de la prochaine mesure : le plafond de `carte_muette`\n"
        u"  (aujourd'hui aucun, faute de chiffre), et le premier écart d'affaire\n"
        u"  sous le même barème de notes.\n")


def main():
    args = sys.argv[1:]
    vue_de = args[args.index("--vue-de") + 1] if "--vue-de" in args else None
    m = mesurer(vue_de)
    avant = None
    if os.path.exists(TRACE):
        try:
            L = [json.loads(x) for x in io.open(TRACE, encoding="utf-8") if x.strip()]
            # Les anciennes lignes étaient globales : les comparer à une
            # étagère bornée fabriquerait un écart spectaculaire mais faux.
            meme_vue = [x for x in L if x.get("vue_de") == m["vue_de"]]
            avant = meme_vue[-1] if meme_vue else None
        except Exception:
            avant = None
    dire(m, avant)
    if "--sec" in args:
        sys.stdout.write(u"\n  (à sec : rien n'a été écrit)\n")
        return
    with io.open(TRACE, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(m, ensure_ascii=False) + u"\n")
    try:
        import plan_modele as PM
        modele = PM.charger(m["vue_de"])
        poser_empreintes(modele["pieces"], m["quand"], m["vue_de"])
    except Exception as e:
        sys.stderr.write(u"  (empreintes non posées : %s)\n" % e)


if __name__ == "__main__":
    main()
    # Le battement se pose APRES main(), donc seulement si elle est allee
    # au bout : un plantage ne bat pas, et c est le mecanisme entier.
    rapporteurs.battre("bilan", u"mesure d ecart posee")
