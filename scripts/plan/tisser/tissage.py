# -*- coding: utf-8 -*-
"""TISSAGE — tisser() projette tous les mecanismes de lien dans UNE SEULE
table d'aretes, et main() imprime le rapport (--pendantes, --ecrire).
"""
import argparse
import collections
import io
import json
import os
import re
import sys

import chiffrer  # la grammaire des couts
from etat.expose import tables  # LA PORTE de etat/

from plan.tisser.lecture import (RACINE, ETAT, SORTIE, CANON, INVERSES,
                                 PIECE, MOYEN, OFFICE, HYPO, charger,
                                 grilles, registres_de, sphere_de,
                                 resoudre_code, nommer, plat_nom,
                                 A_DESIGNER, col, nu, indexer)
from plan.tisser.chambre_mj import charger_affaires_mj, aretes_affaires_mj
from plan.tisser.personnelles import (charger_affaires_personnelles,
                                      aretes_affaires_personnelles)

def tisser(books, intentions, mains, plans, evenements, personnages=None,
           joueur=None, lieux_connus=(), plis=None, liens=None,
           affaires_mj=None, affaires_personnelles=None):
    registres = registres_de(books)
    noms = nommer(personnages or [])
    personnes_connues = {p.get("id") for p in (personnages or [])
                         if isinstance(p, dict) and p.get("id")}
    """Une arete par lien reellement ecrit. `flou` = presente, non suivable."""
    A = []

    def arc(de, vers, nature, source, flou=False, texte="", **proprietes):
        # LE REPLI, A LA POSE. Canoniser apres coup obligerait chaque script
        # d'assessment a le refaire, et le premier qui l'oublierait mesurerait
        # un goulot faux.
        c = CANON.get(nature, nature)
        if c in INVERSES:
            c, de, vers = INVERSES[c], vers, de
        # CE QUI EST EN PROSE ET SE LAISSE POURTANT LIRE. Un cout qui cite une
        # mesure pointe vers un vrai noeud ; un cout chiffre porte ce qu'il
        # mange ; un « neant » est une reponse, pas un trou. 343 aretes sur
        # 1 048 sortent du flou sans qu'on ait rien converti.
        lu = None
        if flou and texte and c in ("coute_chiffre", "coute"):
            classe, tire = chiffrer.classer(texte)
            if classe == "cite_une_mesure":
                vers, flou, lu = tire["adresse"], False, {"classe": classe}
            elif classe == "declare_neant":
                vers, flou, lu = "neant", False, dict(tire, classe=classe)
            elif classe == "chiffrable":
                q = (tire.get("quantites") or [{}])[0]
                if q.get("quoi"):
                    vers, flou = "unite:" + q["quoi"], False
                    lu = dict(tire, classe=classe)
        a = {"de": de, "vers": vers, "nature": c, "source": source,
             "flou": flou, "texte": nu(texte)[:110]}
        if lu:
            a["lu"] = lu
        a.update({k: v for k, v in proprietes.items() if v is not None})
        A.append(a)

    def personnes_dans(texte):
        """Résout tous les habitants explicitement nommés dans une cellule.

        Les groupes de verrou citent plusieurs ids canoniques. Dès qu'un id
        exact est présent, il gagne sur les noms humains et leurs homonymes.
        """
        brut = str(texte or "")
        exactes = {
            "pers:" + pid for pid in personnes_connues
            if re.search(r"(?<![a-z0-9-])" + re.escape(pid)
                         + r"(?![a-z0-9-])", brut, re.I)
        }
        if exactes:
            return exactes
        pn = plat_nom(brut)
        resultat = set()
        for nom, pid in noms.items():
            if re.search(r"(?:^| )" + re.escape(nom) + r"(?: |$)", pn):
                resultat.add("pers:" + pid)
        return resultat

    # --- les cinq mecanismes des cahiers
    for l in books:
        lid = l.get("id")
        # LE PROPRIETAIRE D'UNE AFFAIRE ENTRE DANS SON GRAPHE, sans devenir
        # pour autant l'executant de chacune de ses actions. `tient` est une
        # assignation de tache et fermerait celles-ci aux collaborateurs ;
        # `porte` relie seulement la personne aux buts strategiques du cahier.
        # L'importance peut ainsi circuler depuis le proprietaire, tandis que
        # chaque action conserve sa propre main (ou sa vacance explicite).
        proprietaire = l.get("tenu_par")
        if proprietaire in personnes_connues:
            for titre, C, lignes in grilles(l):
                if "cible" not in titre.casefold():
                    continue
                for r in lignes:
                    cells = r.get("cellules") or []
                    cible = nu(cells[0]) if cells else ""
                    if PIECE.fullmatch(cible):
                        arc("pers:" + str(proprietaire), cible, "porte",
                            "books/tenu_par", texte=lid)
        for titre, C, lignes in grilles(l):
            est_act = "Action" in titre
            est_clef = "Clef" in titre
            est_ver = "Verrou" in titre
            est_lie = "liées" in titre or "liees" in titre
            est_ten = "ne tient pas" in titre
            for r in lignes:
                cells = r.get("cellules") or []
                d = dict(zip(C, cells))
                tete = nu(cells[0]) if cells else ""
                if est_act and PIECE.fullmatch(tete):
                    for n in PIECE.findall(col(d, "Réalise")):
                        arc(tete, n, "realise", "books/actions")
                    for n in PIECE.findall(col(d, "Dépend")):
                        arc(tete, n, "depend_de", "books/actions")
                    for m in MOYEN.findall(col(d, "Moyens")):
                        arc(tete, resoudre_code(m, lid, registres), "coute",
                            "books/actions")
                    bureau = col(d, "Office")
                    codes = OFFICE.findall(bureau)
                    for o in codes:
                        arc(tete, resoudre_code(o, lid, registres), "tient",
                            "books/actions")
                    if not codes and bureau.strip():
                        pn = plat_nom(bureau)
                        # Un identifiant canonique exact gagne avant la
                        # comparaison des noms. `plat_nom` retire les chiffres
                        # et confondrait sinon anchor-builder et
                        # anchor-builder1, ou greek-trader et greek-trader2.
                        trouve = ("pers:" + bureau.strip()
                                  if bureau.strip() in personnes_connues
                                  else None)
                        if trouve is None and A_DESIGNER.search(pn):
                            trouve = "a_designer"
                        elif trouve is None:
                            for nom, pid in noms.items():
                                if re.search(r"(?:^| )" + re.escape(nom)
                                             + r"(?: |$)", pn):
                                    trouve = "pers:" + pid
                                    break
                        arc(tete, trouve or "?", "tient", "books/actions",
                            flou=trouve is None, texte=bureau)
                    # Le cout est a moitie en prose : on le pose FLOU quand il
                    # ne cite aucune adresse. Compter une arete floue comme
                    # suivable serait mentir sur ce que le graphe sait faire.
                    c = col(d, "coûte")
                    if c.strip():
                        cible = None
                        mm = re.search(r"([a-z0-9-]+\.[a-z0-9-]+)", c)
                        if mm:
                            cible = mm.group(1)
                        arc(tete, cible or "?", "coute_chiffre",
                            "books/actions", flou=cible is None, texte=c)
                elif est_clef and PIECE.fullmatch(tete):
                    for n in PIECE.findall(col(d, "Ouvre")):
                        arc(tete, n, "ouvre", "books/clefs")
                    # Une amélioration part de moyens existants qualifiés. La
                    # clef peut donc citer directement les modules qu'elle
                    # rend utilisables, sans inventer une action d'emploi à
                    # seule fin de raccorder le graphe.
                    for m in MOYEN.findall(col(d, "Moyens")):
                        arc(tete, resoudre_code(m, lid, registres), "coute",
                            "books/clefs")
                elif est_ver and PIECE.fullmatch(tete):
                    for n in PIECE.findall(col(d, "Bloque")):
                        arc(tete, n, "bloque", "books/verrous")
                    # Le préalable logique porte sur le verrou : il dit ce qui
                    # doit déjà être vrai avant que cette serrure puisse être
                    # levée. Une action reste libre de sa méthode et ne sert
                    # pas de faux séquenceur au plan.
                    for n in PIECE.findall(col(d, "Dépend")):
                        arc(tete, n, "depend_de", "books/verrous")
                    porteurs = col(d, "Porteurs")
                    if porteurs.strip():
                        cibles = personnes_dans(porteurs)
                        if cibles:
                            for cible in sorted(cibles):
                                arc(tete, cible, "tient", "books/verrous",
                                    texte=porteurs)
                        else:
                            arc(tete, "?", "tient", "books/verrous",
                                flou=True, texte=porteurs)
                elif MOYEN.fullmatch(tete) or OFFICE.fullmatch(tete):
                    # UN MOYEN A UN PORTEUR, et c'est ce qui en fait un point
                    # de rupture : « un seul mestre pour tout ». Les offices
                    # nomment la meme chose « Le titulaire » et peuvent en
                    # avoir plusieurs ; les perdre faisait passer leurs
                    # actions pour des taches sans maitre.
                    porteur = col(d, "Qui le tient") or col(d, "titulaire")
                    if not porteur.strip():
                        continue
                    pn = plat_nom(porteur)
                    cibles = set()
                    if pn.strip() in ("moi", "moi meme", "la reine"):
                        cibles.add("pers:" + (joueur or "rhaenyra"))
                    if re.fullmatch(r"maison-[a-z0-9-]+", porteur.strip(), re.I):
                        cibles.add("maison:" + porteur.strip().lower())
                    for nom, pid in noms.items():
                        if re.search(r"(?:^| )" + re.escape(nom)
                                     + r"(?: |$)", pn):
                            cibles.add("pers:" + pid)
                    source = resoudre_code(tete, lid, registres)
                    if cibles:
                        for cible in sorted(cibles):
                            arc(source, cible, "tient", "books/moyens",
                                texte=porteur)
                    else:
                        arc(source, "?", "tient", "books/moyens", flou=True,
                            texte=porteur)
                elif est_lie:
                    nature = nu(col(d, "Le lien")) or "lie"
                    nous = PIECE.findall(col(d, "Notre pièce"))
                    leur = PIECE.findall(col(d, "La leur"))
                    for a in (nous or ["?"]):
                        for b in (leur or ["?"]):
                            arc(a, b, nature.replace(" ", "_"),
                                "books/affaires-liees",
                                flou=(a == "?" or b == "?"),
                                texte=col(d, "Pourquoi"))
                elif est_ten:
                    arc(lid, "?", "contredit", "books/tensions", flou=True,
                        texte=col(d, "monnaie") or nu(cells[1] if len(cells) > 1 else ""))

    # --- les tetes
    for t in intentions:
        pid = "pers:" + str(t.get("personnage_id"))
        for e in t.get("plan") or []:
            eid = "etape:" + str(e.get("id"))
            arc(pid, eid, "poursuit", "intentions/plan")
            for dd in e.get("depend_de") or []:
                arc(eid, "etape:" + str(dd), "depend_de", "intentions/plan")
            for c in e.get("cout") or []:
                if isinstance(c, dict) and c.get("mesure"):
                    arc(eid, c["mesure"], "coute_chiffre", "intentions/cout")
                else:
                    arc(eid, "?", "coute_chiffre", "intentions/cout",
                        flou=True, texte=str(c))
        for dcl in t.get("declencheurs") or []:
            arc(pid, "?", "repond", "intentions/declencheurs", flou=True,
                texte=(dcl.get("si") if isinstance(dcl, dict) else str(dcl)))

    # --- les evenements
    for e in evenements:
        eid = "ev:" + str(e.get("id"))
        for dif in e.get("diffusion") or []:
            route = {
                "canal": dif.get("canal"),
                "date": dif.get("date"),
                "fiabilite": dif.get("fiabilite"),
                "deformation": dif.get("version"),
                "etat": "arrive" if dif.get("livree") else "attendu",
            }
            for q in (dif.get("qui") or []):
                arc(eid, "pers:" + str(q), "revele", "evenements/diffusion",
                    texte=dif.get("version"), route=route,
                    visible_par=[q], connaissance=True)
            if not (dif.get("qui") or []):
                arc(eid, "lieu:" + str(dif.get("ou")), "revele",
                    "evenements/diffusion", texte=dif.get("version"),
                    route=route, connaissance=True)
        for c in e.get("conditions") or []:
            arc("?", eid, "devie", "evenements/conditions", flou=True, texte=c)
        for a in (e.get("acteurs") or []):
            arc("pers:" + str(a), eid, "acteur_de", "evenements/acteurs")

    # --- les mains
    for a in mains:
        aid = a.get("id")
        porteur = a.get("porteur") or {}
        por = porteur.get("id")
        if por:
            prefixe = {
                "lieu": "lieu:",
                "maison": "maison:",
                "personnage": "pers:",
            }.get(porteur.get("type"), "lieu:" if por in lieux_connus else "pers:")
            arc(prefixe + str(por), "main:" + str(aid), "tient", "mains/porteur")
        for mes in a.get("mesure") or []:
            adr = "{}.{}".format(aid, mes.get("id"))
            for dd in mes.get("depend_de") or []:
                arc(adr, dd, "depend_de", "mains/mesure")
        for s in a.get("seuils") or []:
            if s.get("promeut"):
                arc("main:" + str(aid), "echelle:" + s["promeut"], "promeut",
                    "mains/seuils")

    # --- les plans d'en face
    for pl in plans:
        for x in pl.get("verrous") or []:
            for b in x.get("bloque") or []:
                arc(x["id"], b, "bloque", "plans/verrous")
        for x in pl.get("clefs") or []:
            for b in x.get("ouvre") or []:
                arc(x["id"], b, "ouvre", "plans/clefs")
        for x in pl.get("actions") or []:
            for b in x.get("realise") or []:
                arc(x["id"], b, "realise", "plans/actions")
            for b in x.get("depend_de") or []:
                arc(x["id"], b, "depend_de", "plans/actions")
            if x.get("office"):
                cible = ("a_designer" if A_DESIGNER.search(plat_nom(x["office"]))
                         else "pers:" + x["office"])
                arc(x["id"], cible, "tient", "plans/actions")
        for x in pl.get("resonance") or []:
            arc(x.get("leur_piece", "?"), x.get("notre_affaire", "?"),
                "resonance", "plans/resonance", flou=True,
                texte=x.get("pourquoi"))

    # --- le miroir de connaissance : un pli est une chose qui voyage.
    # Les deux arcs gardent le depart et l'arrivee visibles dans le meme graphe,
    # sans confondre le texte transporte avec la personne qui le porte.
    def jour(d):
        if not isinstance(d, dict) or d.get("annee") is None:
            return None
        return ((d["annee"] * 12 + d.get("lune", 1) - 1) * 30
                + d.get("jour", 1) - 1)

    for p in plis or []:
        pid = "pli:" + str(p.get("id"))
        depart, arrivee = jour(p.get("parti_le")), jour(p.get("attendu_le"))
        route = {
            "canal": p.get("canal"),
            "depart": p.get("parti_le"),
            "arrivee": p.get("attendu_le"),
            "delai_jours": (arrivee - depart
                            if depart is not None and arrivee is not None else None),
            "fiabilite": None,
            "deformation": p.get("porte"),
            "etat": p.get("etat"),
            "scelle": p.get("scelle"),
        }
        arc("pers:" + str(p.get("de")), pid, "achemine", "plis/depart",
            texte=p.get("porte"), route=route, connaissance=True,
            visible_par=[p.get("de")])
        # Le temps de voyage est payé sur `achemine`. `revele` est la remise
        # au destinataire, instantanée une fois le pli arrivé ; recopier le
        # même délai sur les deux arcs le ferait payer deux fois au graphe.
        route_remise = dict(route)
        route_remise["delai_jours"] = 0
        arc(pid, "pers:" + str(p.get("pour")), "revele", "plis/arrivee",
            texte=p.get("porte"), route=route_remise, connaissance=True,
            visible_par=[p.get("pour")])

    # --- les liens natifs, tisses a la main. Ils ont exactement le meme poids
    # que les arcs extraits des cahiers ; `natif` ne sert qu'a montrer leur
    # provenance dans la regie.
    for l in liens or []:
        if not isinstance(l, dict):
            continue
        arc(l.get("de", "?"), l.get("vers", "?"), l.get("nature", "lie"),
            "liens", flou=not l.get("de") or not l.get("vers"),
            texte=l.get("pourquoi"), natif=True, auteur=l.get("qui"),
            date=l.get("quand"), justification=l.get("pourquoi"),
            visible_par=l.get("visible_par"), route=l.get("route"))

    # La chambre du MJ fait exception : ses affaires alimentent directement
    # la projection, avec leur provenance locale et sans devenir de l'état du
    # monde. Les mêmes règles de canonisation d'arêtes s'appliquent ici.
    for a in aretes_affaires_mj(affaires_mj or [], evenements):
        extras = {k: v for k, v in a.items()
                  if k not in ("de", "vers", "nature", "source", "flou", "texte")}
        arc(a["de"], a["vers"], a["nature"], a["source"],
            flou=a.get("flou", False), texte=a.get("texte", ""), **extras)
    for a in aretes_affaires_personnelles(affaires_personnelles or []):
        extras = {k: v for k, v in a.items()
                  if k not in ("de", "vers", "nature", "source", "flou", "texte")}
        arc(a["de"], a["vers"], a["nature"], a["source"],
            flou=a.get("flou", False), texte=a.get("texte", ""), **extras)
    return A


# ------------------------------------------------------------- le rapport

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pendantes", action="store_true")
    ap.add_argument("--ecrire", action="store_true")
    args = ap.parse_args()

    books = charger("books", [])
    intentions = charger("intentions", [])
    mains = charger("mains", [])
    evenements = charger("evenements", [])
    personnages = charger("personnages", [])
    plis = charger("plis", [])
    liens = charger("liens", [])
    plans_brut = charger("plans", {})
    plans = plans_brut.get("plans", []) if isinstance(plans_brut, dict) else plans_brut
    affaires_mj = charger_affaires_mj(RACINE)
    affaires_personnelles = charger_affaires_personnelles(RACINE, personnages)

    noeuds, doubles = indexer(books, intentions, mains, plans, evenements,
                              personnages, plis, affaires_mj,
                              affaires_personnelles)
    jr = charger("journal", {})
    joueur = (jr or {}).get("personnage_joueur_id") if isinstance(jr, dict) else None
    lieux_connus = {l.get("id") for l in charger("lieux", [])
                    if isinstance(l, dict) and l.get("id")}
    aretes = tisser(books, intentions, mains, plans, evenements,
                    personnages, joueur, lieux_connus, plis, liens,
                    affaires_mj, affaires_personnelles)

    genres = collections.Counter(n["genre"] for n in noeuds.values())
    print("LE TISSU")
    print("  {} noeuds : {}".format(
        len(noeuds), " · ".join("{} {}".format(v, k)
                                for k, v in genres.most_common())))
    print("  {} aretes".format(len(aretes)))
    print()

    par_nature = collections.Counter(a["nature"] for a in aretes)
    print("PAR NATURE")
    for k, v in par_nature.most_common():
        print("  {:<18} {:>5}".format(k[:18], v))
    print()

    # --- LE CHIFFRE QUI DECIDE
    suivables = [a for a in aretes if not a["flou"]]
    pend = [a for a in suivables
            if a["de"] not in noeuds or a["vers"] not in noeuds]
    resolues = len(suivables) - len(pend)
    print("L'ADRESSAGE — le chiffre qui decide de la suite")
    print("  {} aretes suivables (les autres sont en prose)".format(len(suivables)))
    print("  {} resolvent des deux cotes  ({:.0f}%)".format(
        resolues, 100.0 * resolues / max(1, len(suivables))))
    print("  {} pendantes                  ({:.0f}%)".format(
        len(pend), 100.0 * len(pend) / max(1, len(suivables))))
    print("  {} floues, presentes mais non suivables".format(
        len(aretes) - len(suivables)))
    print("  seuil de decision : au-dela de 10% de pendantes, on repare")
    print("  l'adressage avant d'aller plus loin.")
    print()

    manquants = collections.Counter()
    for a in pend:
        for bout in (a["de"], a["vers"]):
            if bout not in noeuds:
                manquants[(a["nature"], bout)] += 1
    print("CE QUI NE RESOUT PAS — les vingt premiers")
    for (nature, bout), n in manquants.most_common(20):
        print("  {:<16} -> {:<28} {}".format(nature[:16], str(bout)[:28], n))
    if doubles:
        print()
        print("ADRESSES A DEUX GENRES : {}".format(len(doubles)))
        for k, v in doubles.most_common(8):
            print("  {} ({} fois)".format(k, v))

    if args.pendantes:
        print()
        print("LES PENDANTES EN CLAIR")
        for a in pend[:60]:
            print("  [{}] {} -> {}".format(a["nature"], a["de"], a["vers"]))
            if a["texte"]:
                print("      {}".format(a["texte"]))

    if args.ecrire:
        p = tables.ecrire_lignes(os.path.join(SORTIE, "aretes.jsonl"), aretes)
        q = tables.ecrire(os.path.join(SORTIE, "noeuds.json"), noeuds, indent=1)
        print()
        print("Tissu depose : {} / {}".format(
            os.path.relpath(p, RACINE), os.path.relpath(q, RACINE)))
        print("Derive et regenerable — les fichiers restent la source.")
    return 0
