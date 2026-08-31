# -*- coding: utf-8 -*-
# DISPONIBILITE_REGIE — la force narrative et ce que la regie affiche.
#
# La seconde moitie de l'ancien scripts/evaluer.py (lot 2) : le score de
# force narrative par homme (poids, quantiles, jours de creux) et la feuille
# JSON que la regie relit (`evaluer.py --json`), plus le main de la commande.
# Les questions 1-7 (goulots, desequilibres, critique, orphelins, murs,
# sourds, portees) vivent dans disponibilite.py, qui reexporte d'ici.
import argparse
import collections
import io
import json
import os
import sys

from temps.disponibilite import (
    RACINE, TISSU, SATURATION, charger, lire_tissu, goulots, desequilibres,
    candidats_equilibrage, critique, orphelins, murs, sourds, portees)
from etat.expose import tables  # LA PORTE de etat/ : --json depose la feuille par elle

# ------------------------------------------------------ 8. la force narrative

# LE BUDGET D'INFERENCE NE SE DECIDE PAS, IL SE MESURE.
# Un acteur ne merite qu'on lui fasse penser quelque chose que dans la mesure
# ou le graphe le met en position de peser. Tout est ici, en un bloc, pour
# qu'on les bouge sans lire le code — et ils sont a l'essai.
# L'ECHELLE EST SUPPRIMEE, et c'est une mesure qui l'a tuee : en retirant
# POIDS_ECHELLE, le classement des dix premiers ne bougeait quasiment pas.
# L'echelle ne mesurait rien que les aretes ne disent mieux — elle recopiait a
# la main ce que le tissu calcule, et se contredisait avec lui six fois sur
# quinze. Ce qui la remplace n'est pas un autre poids : c'est le QUARTIER
# (qui le joueur peut atteindre) et le CREUX (le temps qu'il lui reste).
POIDS_ACTION = 1          # par action tenue, plafonne
PLAFOND_ACTIONS = 12
POIDS_CRITIQUE = 5        # par action sur le chemin critique — le plus lourd
POIDS_MOYEN_SATURE = 6    # tenir un goulot met un homme au centre
POIDS_DECLENCHEUR = 2     # un homme arme pour reagir au joueur
PLAFOND_CROYANCES = 5

# Combien de questions on lui pose dans les creux de sa boucle.
#
# EN RANGS, PAS EN SEUILS. Les paliers en valeur absolue — (40,5) (20,3)
# (10,1) — etaient calibres sur une population de cinquante-trois tetes de
# mediane 7 : une salle de douze acteurs tombait a zero question pour tout le
# monde. Le budget devient donc proportionnel a la SALLE, et non a la taille du
# monde : il est stable si le casting double ou fond de moitie.
QUANTILES = ((0.10, 5), (0.30, 3), (0.60, 1), (1.00, 0))

# Sous ce nombre d'eligibles, les quantiles degenerent — un huis clos a quatre
# donnerait 5 questions a l'un et 0 aux trois autres. On retombe alors sur une
# regle plate : les trois plus forts ont 3 questions, les autres 1.
PLANCHER_QUANTILES = 6


def force_narrative(A, N, dire, joueur=None):
    """Ce que chacun pese dans le graphe, et le budget qui en decoule."""
    it = charger("intentions", [])
    tetes = {t["personnage_id"]: t for t in it if isinstance(t, dict)}

    tenu = collections.defaultdict(list)
    porte = collections.defaultdict(list)
    for a in A:
        if a["nature"] != "tient":
            continue
        if str(a["vers"]).startswith("pers:"):
            (porte if N.get(a["de"], {}).get("genre") == "moyen"
             else tenu)[a["vers"][5:]].append(a["de"])

    ent = collections.defaultdict(list)
    for a in A:
        ent[a["vers"]].append(a)
    satures = {n for n, arcs in ent.items()
               if N.get(n, {}).get("genre") == "moyen"
               and sum(1 for x in arcs if x["nature"].startswith("coute"))
               >= SATURATION}

    sor = collections.defaultdict(list)
    for a in A:
        if a["nature"] == "depend_de" and a["vers"] in N:
            sor[a["de"]].append(a["vers"])
    memo, sur_critique = {}, set()

    def prof(n, vus):
        if n in memo:
            return memo[n]
        if n in vus:
            return (0, [n])
        b = (0, [n])
        for s2 in sor.get(n, []):
            d, c = prof(s2, vus | {n})
            if d + 1 > b[0]:
                b = (d + 1, [n] + c)
        memo[n] = b
        return b
    for d, c in sorted((prof(n, set()) for n in sor), reverse=True)[:5]:
        sur_critique.update(c)

    # LE QUARTIER ET LES CREUX. C'est ici que la force cesse de decider seule :
    # elle REPARTIT un budget de temps existant, elle n'en fabrique pas. Un
    # homme dont la journee est pavee de bandes fermees n'a pas de creux, si
    # fort soit-il — et c'est ca, le cout d'un mandat : on l'occupe.
    #
    # MAIS LE QUARTIER NE SUPPRIME PLUS LA JOURNEE (31.8). On ne calculait les
    # creux QUE pour `dedans`, et un homme au loin ressortait « aucun creux ».
    # Deux consequences, dont la seconde etait un vrai degat :
    #   - `mission.py` refuse de depecher qui n'a « AUCUN CREUX » : 44 hommes
    #     sur 78, dont TOUTE la cour verte de Port-Real, etaient injoignables.
    #     Le MJ les appelait, ils ne partaient pas.
    #   - c'etait faux dans les termes du code : `creux()` calcule tres bien
    #     pour eux — 42 des 44 ont leur fiche de routine, et Aegon II rend
    #     2 creux, 260 minutes, dans la cour du Donjon Rouge.
    # Etre loin ne retire pas sa journee a un homme : ca retire au JOUEUR le
    # moyen de l'atteindre par lui-meme. On calcule donc pour tout le monde, et
    # le quartier ne borne plus que le BUDGET DE QUESTIONS spontanees, qui est
    # le seul endroit ou il devait mordre.
    creux_de, motif, au_loin = {}, {}, set()
    try:
        from temps.expose import presence as mod_presence
        q = mod_presence.quartier()
        rout, chem, _ = mod_presence.charger()
        chat = mod_presence.Chateau(chem)
        pj, fiches = mod_presence.joueurs(), (rout.get("gens") or {})
        dehors = q.get("dehors") or {}
        au_loin = set(dehors)
        for pid in list(q.get("dedans") or {}) + list(dehors):
            c = mod_presence.creux(pid, rout, chat)
            if c:
                creux_de[pid] = c
                # Le motif du dehors reste dit — il explique pourquoi il ne
                # posera pas de question de lui-meme —, mais il ne vaut plus
                # empechement : il a ses heures, et on peut le depecher.
                if pid in dehors:
                    motif[pid] = dehors[pid]
            # Un muet se dit POURQUOI il est muet, sinon on repare la mauvaise
            # chose : un siege occupe est normal, une journee fermee est un
            # choix, une fiche manquante est une faute.
            elif pid in pj:
                motif[pid] = "siege occupe"
            elif pid not in fiches:
                motif[pid] = "sans routine"
            else:
                motif[pid] = dehors.get(pid) or "journee fermee"
    except Exception as e:
        dire("  (quartier indisponible : {})".format(str(e)[:80]))

    lignes = []
    for pid, t in tetes.items():
        acts = tenu.get(pid, [])
        crit = sum(1 for a in acts if a in sur_critique)
        gou = [m for m in porte.get(pid, []) if m in satures]
        f = (POIDS_ACTION * min(len(acts), PLAFOND_ACTIONS)
             + POIDS_CRITIQUE * crit
             + (POIDS_MOYEN_SATURE if gou else 0)
             + POIDS_DECLENCHEUR * len(t.get("declencheurs") or [])
             + min(len(t.get("croyances") or []), PLAFOND_CROYANCES))
        cx = creux_de.get(pid) or []
        lignes.append({"qui": pid, "force": f, "questions": 0,
                       "actions": len(acts), "critiques": crit, "goulots": gou,
                       "declencheurs": len(t.get("declencheurs") or []),
                       "creux": cx,
                       "creux_total": sum(x["minutes"] for x in cx),
                       "hors_quartier": motif.get(pid),
                       "questions_posees": []})
    lignes.sort(key=lambda x: -x["force"])

    # Le budget se calcule sur les SEULS eligibles — ceux qui ont un creux ET
    # que le joueur peut atteindre. C'est ICI, et nulle part ailleurs, que le
    # quartier doit mordre : une question spontanee que personne n'entendra ne
    # vaut pas une orbite. Un homme au loin garde sa journee et se depeche ;
    # il ne pense simplement pas de lui-meme pour le joueur.
    eligibles = [l for l in lignes if l["creux"] and l["qui"] not in au_loin]
    n = len(eligibles)
    for rang, l in enumerate(eligibles):
        if n < PLANCHER_QUANTILES:
            l["questions"] = 3 if rang < 3 else 1
        else:
            part = (rang + 1) / float(n)
            l["questions"] = next(q for seuil, q in QUANTILES if part <= seuil)
        # UNE QUESTION CONSOMME UN CREUX, avec sa salle : une question posee a
        # la roukerie n'a pas les memes sources qu'une posee au bourg. On lui
        # donne ses plus longues plages, rendues dans l'ordre de la journee.
        pris = sorted(l["creux"], key=lambda c: -c["minutes"])[:l["questions"]]
        l["questions_posees"] = sorted(pris, key=lambda c: c["de"])

    dire("LA FORCE NARRATIVE — ce que chacun pese, et le temps qu'il lui reste")
    dire("  La force ne cree pas de creux : un homme fort et occupe ne pense")
    dire("  pas. Elle repartit un budget de temps que la journee a deja dit.")
    dire("")
    dire("  {:>4} {:>3} {:>6}  {:<22} {:>4} {:>5} {:>5}  {}".format(
        "for", "q", "creux", "qui", "act", "crit", "decl", "goulot"))
    for l in lignes[:18]:
        dire("  {:>4} {:>3} {:>6}  {:<22} {:>4} {:>5} {:>5}  {}".format(
            l["force"], l["questions"],
            l["creux_total"] or ("—" + (l["hors_quartier"] or "")[:5]),
            l["qui"][:22], l["actions"], l["critiques"], l["declencheurs"],
            ", ".join(g.split(":")[-1] for g in l["goulots"])))
    total = sum(l["questions"] for l in lignes)
    servis = sum(1 for l in lignes if l["questions"])
    muets = [l for l in lignes if not l["creux"]]
    dire("")
    dire("  {} questions au total, sur {} tetes servies (sur {} eligibles,"
         " {} tetes).".format(total, servis, n, len(lignes)))
    if muets:
        forts = [l for l in sorted(muets, key=lambda x: -x["force"])[:5]]
        dire("  Sans creux, donc muets ce jour : {} — dont {}.".format(
            len(muets), ", ".join("%s (%s)" % (l["qui"][:16],
                                               l["hors_quartier"] or "tete sans corps")
                                  for l in forts)))
    return lignes



# ------------------------------------------------- 9. ce que la regie affiche

def pour_la_regie(A, N, muet):
    """Tout ce que /admin montre, calcule ICI et nulle part ailleurs.

    `serveur.js` ne recalcule rien : il relit ce depot. C'est la meme regle que
    partout — une definition, un seul endroit. Le jour ou l'excitation ou la
    force se recalculeraient en JS, elles divergeraient le meme jour.
    """
    out = {}

    # --- OU EST CHACUN, a la minute. La position ne se stocke pas, elle se
    # calcule : on appelle le moteur, on ne relit pas un instantane.
    try:
        from temps.expose import presence as mod_presence
        ou = mod_presence.resoudre()
        gens = charger("personnages", [])
        noms = {g.get("id"): (g.get("nom") or g.get("id"))
                for g in gens if isinstance(g, dict)}
        journal = charger("journal", {})
        joueur = journal.get("personnage_joueur_id") if isinstance(journal, dict) else None
        _routines, chemins, _exceptions = mod_presence.charger()
        chateau = mod_presence.Chateau(chemins)
        salle_joueur = (ou.get(joueur) or {}).get("salle") if joueur else None
        arretes, chemin = collections.defaultdict(list), []
        acteurs = []
        for pid, o in ou.items():
            distance = None
            salle = o.get("salle")
            # Zéro n'est une vraie distance que si les deux salles sont la
            # même. Chateau.chemin rend aussi zéro pour un trajet inconnu :
            # on exige donc que les deux extrémités soient dans la topologie.
            if (o.get("etat") == "arrete" and salle_joueur and salle
                    and chateau.connait(salle_joueur) and chateau.connait(salle)):
                distance = chateau.duree(salle_joueur, salle)
            acteurs.append({"id": pid, "qui": noms.get(pid, pid),
                             "salle": salle, "lieu": o.get("lieu"),
                             "etat": o.get("etat"), "source": o.get("source"),
                             "distance_joueur_minutes": distance})
            if o.get("etat") == "arrete":
                cle = o.get("salle") or ("(hors plan) %s" % (o.get("lieu") or "?"))
                arretes[cle].append(noms.get(pid, pid))
            else:
                chemin.append({"qui": noms.get(pid, pid), "de": o.get("de"),
                               "vers": o.get("vers")})
        out["presence"] = {
            "joueur_id": joueur,
            "joueur_salle": salle_joueur,
            "acteurs": sorted(acteurs, key=lambda x: x["qui"]),
            "salles": [{"salle": k, "gens": sorted(v)}
                       for k, v in sorted(arretes.items())],
            "en_chemin": sorted(chemin, key=lambda x: x["qui"]),
        }
    except Exception as e:
        out["presence"] = {"erreur": str(e)[:120]}

    # --- LE QUARTIER ET LES CREUX, a la place des convocations. `travaux.json`
    # et son excitation ont disparu : ce n'etait pas un compteur qui disait qui
    # a quelque chose a dire, c'etait sa journee. Un homme qui a du temps dans
    # une salle ou il y a des sources pense ; les autres travaillent.
    try:
        from temps.expose import presence as mod_presence
        q = mod_presence.quartier()
        rout, chem, _ = mod_presence.charger()
        chat = mod_presence.Chateau(chem)
        noms_p = {g.get("id"): (g.get("nom") or g.get("id"))
                  for g in charger("personnages", []) if isinstance(g, dict)}
        lignes = []
        for pid, d in (q.get("dedans") or {}).items():
            cx = mod_presence.creux(pid, rout, chat)
            if not cx:
                continue
            lignes.append({"qui": pid, "nom": noms_p.get(pid, pid),
                           "salle": d.get("salle"),
                           "minutes_du_joueur": d.get("minutes"),
                           "par": d.get("par"),
                           "creux_total": sum(x["minutes"] for x in cx),
                           "creux": cx})
        lignes.sort(key=lambda x: -x["creux_total"])
        out["quartier"] = {
            "ancres": [{"qui": a["qui"], "salle": a["salle"],
                        "minute": (a.get("quand") or {}).get("minute")}
                       for a in q.get("ancres") or []],
            "rayon_minutes": mod_presence.RAYON_MINUTES,
            "dedans": len(q.get("dedans") or {}),
            # La liste, et pas seulement le compte : c'est elle qui remplace le
            # champ `echelle` cote serveur, pour grouper les tetes a l'ecran.
            "gens": sorted(q.get("dedans") or {}),
            "dehors": [{"qui": k, "nom": noms_p.get(k, k), "motif": v}
                       for k, v in sorted((q.get("dehors") or {}).items())],
        }
        out["creux"] = lignes
    except Exception as e:
        out["quartier"] = {"erreur": str(e)[:160]}
        out["creux"] = []

    # --- LE CAMP D'EN FACE : ce que ses verrous engendrent chez nous.
    brut = charger("plans", {})
    plans = brut.get("plans", []) if isinstance(brut, dict) else brut
    out["en_face"] = [{
        "id": p.get("id"), "titre": p.get("titre"),
        "verrous": [{"id": v["id"], "quoi": v["quoi"],
                     "portee": (v.get("portee_pour_nous") or "").split(" —")[0],
                     "vrai": (v.get("vrai_aujourdhui") or "")[:160]}
                    for v in p.get("verrous") or []],
        "engendre": p.get("ce_que_ca_engendre_chez_nous") or [],
        "tensions": [{"id": t["id"], "monnaie": t["monnaie"],
                      "ecart": t["ecart"][:180]}
                     for t in p.get("tensions") or []],
    } for p in plans]
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    for m in ("goulots", "desequilibres", "critique", "orphelins", "murs",
              "sourds", "portees", "force"):
        ap.add_argument("--" + m, action="store_true")
    ap.add_argument("--json", action="store_true",
                    help="depose l'evaluation pour la regie, sans rien narrer")
    args = ap.parse_args()
    choisis = [m for m in ("goulots", "desequilibres", "critique", "orphelins",
                           "murs", "sourds", "portees", "force")
               if getattr(args, m)]
    tout = not choisis

    A, N = lire_tissu()

    if args.json:
        # LA REGIE NE CALCULE RIEN. Elle relit ce fichier, et elle en dit
        # l'age : un tissu de la veille affiche comme l'etat du jour serait
        # exactement le mensonge que `regie()` refuse deja par son absence
        # de cache.
        muet = lambda t="": None
        g = goulots(A, N, muet)
        d = desequilibres(A, N, muet)
        v = orphelins(A, N, muet)
        ch = critique(A, N, muet)
        mu = murs(muet)
        so = sourds(muet)
        out = {
            "noeuds": len(N), "aretes": len(A),
            "goulots": [{"noeud": nid, "quoi": nd["quoi"], "demandes": n,
                         "sature": n >= SATURATION}
                        for n, _t, nid, nd in g[:12]],
            "desequilibres": [{"noeud": nid, "quoi": nd["quoi"],
                               "consommateurs": n,
                               "candidats": [{"id": i, "quoi": x["quoi"]}
                                             for i, x in
                                             candidats_equilibrage(A, N, nid, muet)[:4]]}
                              for n, nid, nd, _s in d[:8]],
            "vacantes": len(v),
            "critique": [{"maillons": dd + 1,
                          "chaine": [{"id": x, "quoi": N.get(x, {}).get("quoi")}
                                     for x in cc]}
                         for dd, cc in ch[:1]],
            "murs_sans_route": len(mu),
            "murs": mu,
            "sourds": [{"echelle": e, "qui": q} for e, q in so],
            "force": force_narrative(A, N, muet),
        }
        out.update(pour_la_regie(A, N, muet))
        p = tables.ecrire(os.path.join(TISSU, "evaluation.json"), out, indent=1)
        print("evaluation deposee : {}".format(os.path.relpath(p, RACINE)))
        return 0

    sep = lambda: print("\n" + "═" * 72 + "\n")

    def dire(t=""):
        print(t)

    print("ÉVALUER — {} noeuds, {} aretes".format(len(N), len(A)))
    sep()

    if tout or "goulots" in choisis:
        g = goulots(A, N, dire)
        sep()
    if tout or "desequilibres" in choisis:
        d = desequilibres(A, N, dire)
        if d:
            candidats_equilibrage(A, N, d[0][1], dire)
        sep()
    if tout or "orphelins" in choisis:
        orphelins(A, N, dire)
        sep()
    if tout or "critique" in choisis:
        critique(A, N, dire)
        sep()
    if tout or "murs" in choisis:
        murs(dire)
        sep()
    if tout or "sourds" in choisis:
        sourds(dire)
        sep()
    if tout or "portees" in choisis:
        portees(dire)
        sep()
    if tout or "force" in choisis:
        force_narrative(A, N, dire)
    return 0


