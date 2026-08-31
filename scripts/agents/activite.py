# -*- coding: utf-8 -*-
"""ACTIVITE — l'instrument de debug des sessions de dev : qui a fait quoi.

CE N'EST PAS UN LIVRABLE DU JEU. Aucun joueur ne le voit, rien n'entre dans
`etat/`, rien ne se decide ici. C'est une LOUPE sur ce que la boucle, les
depeches et les canaux ont reellement produit — donc le parti pris est le
maximum d'information, derriere des drapeaux, sans souci d'elegance.

    python scripts/activite.py                    tout, sur 24 h reelles
    python scripts/activite.py --heures 3         la fenetre reelle
    python scripts/activite.py --monde 12         la fenetre en HEURES DE JEU
    python scripts/activite.py --tout             sans fenetre
    python scripts/activite.py --qui otto         un seul homme
    python scripts/activite.py --appels --refus   telle ou telle section
    python scripts/activite.py --json             pour la regie ou un tableur

CE QUE LA DONNEE NE PERMET PAS, ET QUI EST DIT DANS LA SORTIE PLUTOT QUE
LAISSE A DECOUVRIR :

  - LES BILLETS N'ONT PAS DE DATE DE MONDE. Mesure du 31.8 : 370 des 385
    entrees de canal n'ont aucun champ `date`. `--monde` ne peut donc pas les
    fenetrer ; il fenetre les activations, qui portent toutes leur
    `present_secondes`, et la section des appels le dit alors en clair.

  - LES REVEILS NE SONT PAS INSTRUMENTES. Un `reveiller.py` ne laisse qu'un
    log de depeche quand il en laisse un — 7 fichiers pour bien plus de
    reveils. On compte donc ce qu'on sait compter (les ACTIVATIONS, tracees
    184 sur 184) et l'on annonce le trou au lieu de rendre un chiffre faux.
"""
import argparse
import collections
import glob
import io
import json
import os
import sys
import time

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RACINE = os.path.dirname(_d)      # `_d` est deja <depot>/scripts : UN dirname
ETAT = os.path.join(RACINE, "etat")
CHAMBRES = os.path.join(RACINE, "chambres")


def _lire(chemin, defaut):
    try:
        return json.load(io.open(chemin, encoding="utf-8"))
    except Exception:
        return defaut


def est_zone(qui):
    """La convention du parloir : « mj », « mj-aurore »… sont des regies."""
    q = qui or ""
    return q == "mj" or q.startswith("mj-")


def _duree(secondes):
    s = int(secondes or 0)
    if s < 60:
        return "%d s" % s
    if s < 3600:
        return "%d min" % (s // 60)
    return "%d h %02d" % (s // 3600, (s % 3600) // 60)


def _quoi(t):
    """Une tache est tantot une chaine, tantot {id, quoi}. On rend du texte."""
    if isinstance(t, dict):
        return t.get("quoi") or t.get("id") or ""
    return t or ""


def _depuis(mur):
    if not mur:
        return "?"
    return _duree(time.time() - mur)


# --------------------------------------------------------------- les sources

def activations():
    """Un rapport par session. Porte les DEUX horloges : `cree_le` (le mur) et
    `present_secondes` (le monde). C'est la seule source qui les ait toutes
    les deux, et c'est pour cela que `--monde` marche ici et nulle part."""
    out = []
    for f in sorted(glob.glob(os.path.join(ETAT, "activations", "2026*.json"))):
        d = _lire(f, None)
        if not d:
            continue
        a = d.get("_activation") or {}
        ac = d.get("activation") or {}
        try:
            mur = time.mktime(time.strptime((a.get("cree_le") or "")[:19],
                                            "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            mur = None
        gestes = ac.get("activites") or []
        out.append({
            "qui": d.get("qui"), "fichier": os.path.basename(f),
            "mur": mur, "monde_s": a.get("present_secondes"),
            "duree_reelle_s": round((a.get("duree_ms") or 0) / 1000.0),
            "cout_usd": float(a.get("cout_usd") or 0),
            "modele": a.get("modele"), "front": a.get("front"),
            "budget": a.get("budget"), "issue": ac.get("issue"),
            # LA TACHE VIT A DEUX ENDROITS ET `_activation.tache` est souvent
            # nul : c'est `activation.tache` qui la porte, et sous forme de
            # dict {id, quoi} la moitie du temps. On lit les deux, on aplatit.
            "tache": _quoi(ac.get("tache") or a.get("tache") or d.get("tache")),
            "depense": ac.get("energie_depensee"),
            "monde_vecu_s": sum((g.get("temps") or {}).get("duree_s") or 0
                                for g in gestes),
            "gestes": gestes,
            "mutations": len(d.get("mutations") or ac.get("mutations") or []),
        })
    return out


def canaux():
    """Les billets. UN CANAL EST ECRIT DANS LES DEUX CHAMBRES : on dedoublonne
    par la paire, sinon tout compte double — c'est la faute evidente ici."""
    vus, out = set(), []
    for f in glob.glob(os.path.join(CHAMBRES, "*", "relations", "*",
                                    "discussion.json")):
        d = _lire(f, None)
        if not d:
            continue
        paire = tuple(sorted(d.get("canal") or []))
        if len(paire) != 2 or paire in vus:
            continue
        vus.add(paire)
        try:
            mtime = os.path.getmtime(f)
        except OSError:
            mtime = None
        a, b = paire
        entrees = d.get("entrees") or []
        for i, e in enumerate(entrees):
            de = e.get("de")
            out.append({"de": de, "vers": b if de == a else a, "paire": paire,
                        "rang": i, "taille": len(e.get("texte") or ""),
                        "texte": e.get("texte") or "",
                        "date_monde": e.get("date"), "mtime": mtime,
                        "dernier": i == len(entrees) - 1})
    return out, vus


def historique():
    b = _lire(os.path.join(ETAT, "activations", "boucle.json"), {}) or {}
    return b.get("historique") or [], b


def reveils_traces():
    """CE QU'ON SAIT DES REVEILS, ET C'EST PEU. Un log par depeche quand il y
    en a un ; jamais de trace pour un reveil de MJ sur POST joueur."""
    out = []
    for f in glob.glob(os.path.join(CHAMBRES, "*", "fil", "depeche-*.log")):
        try:
            out.append({"qui": f.split(os.sep)[-3],
                        "mtime": os.path.getmtime(f),
                        "octets": os.path.getsize(f),
                        "fichier": os.path.basename(f)})
        except OSError:
            continue
    return sorted(out, key=lambda x: x["mtime"])


# --------------------------------------------------------------- la fenetre

def dans_la_fenetre(a, args, present):
    """Rend (garde, motif). Le motif est la moitie du travail : une fenetre
    qui ecarte des lignes sans dire pourquoi fait croire au vide."""
    if args.tout:
        return True, None
    if args.monde is not None:
        if a.get("monde_s") is None:
            return False, "sans heure de monde"
        return (present - a["monde_s"]) <= args.monde * 3600.0, None
    if a.get("mur") is None:
        return False, "sans heure reelle"
    return (time.time() - a["mur"]) <= args.heures * 3600.0, None


# --------------------------------------------------------------- les mesures

def par_homme(acts, hist):
    par = collections.OrderedDict()
    for a in acts:
        r = par.setdefault(a["qui"], {
            "qui": a["qui"], "activations": 0, "actes": 0, "monde_s": 0,
            "reel_s": 0, "cout": 0.0, "mutations": 0, "depense": 0.0,
            "budget": 0, "issues": collections.Counter(), "modeles": set(),
            "importance": None, "derniere": None, "tache": None})
        r["activations"] += 1
        r["actes"] += len(a["gestes"])
        r["monde_s"] += a["monde_vecu_s"]
        r["reel_s"] += a["duree_reelle_s"]
        r["cout"] += a["cout_usd"]
        r["mutations"] += a["mutations"]
        r["issues"][a["issue"] or "?"] += 1
        r["depense"] += float(a["depense"] or 0)
        r["budget"] += int(a["budget"] or 0)
        if a["modele"]:
            r["modeles"].add(a["modele"])
        if r["derniere"] is None or (a["mur"] or 0) > r["derniere"]:
            r["derniere"] = a["mur"]
            r["tache"] = a["tache"]
    for h in hist:
        q = h.get("qui")
        if q in par and h.get("importance") is not None:
            par[q]["importance"] = h["importance"]
    return par


def matrice(billets):
    """Le SENS des appels. C'est la mesure qui contredit la doctrine : au
    31.8, homme->MJ 225 contre MJ->homme 115, et homme->homme 18 sur 385.
    « Qu'ils se parlent entre eux » n'a pas lieu, et seul ce compte le dit."""
    m = collections.Counter()
    for b in billets:
        m[("MJ" if est_zone(b["de"]) else "homme",
           "MJ" if est_zone(b["vers"]) else "homme")] += 1
    return m


def verbes_et_resultats(acts):
    v = collections.Counter()
    r = collections.Counter()
    genres = collections.Counter()
    for a in acts:
        for g in a["gestes"]:
            ac = g.get("action") or {}
            v[(ac.get("verbe") or "?").lower()] += 1
            for res in g.get("resultats_produits") or []:
                r[res.get("type") or "?"] += 1
            for c in ac.get("cibles") or []:
                genres[str(c).split(":")[0]] += 1
    return v, r, genres


def ecartes():
    """CE QUE LA BOUCLE N'ELIT PAS, avec le motif. Sans cette section on ne
    voit que les elus, et un systeme qui n'active que six hommes sur cent
    vingt a l'air sain tant qu'on ne compte pas les autres."""
    try:
        from temps.expose import presence as P
        q = P.quartier()
        return collections.Counter((q.get("dehors") or {}).values()), q
    except Exception as e:
        return collections.Counter(), {"erreur": str(e)[:120]}


# ---------------------------------------------------------------- le rendu

def _titre(t):
    print("")
    print(t)
    print("-" * max(24, len(t)))


def rendre(args):
    hist, boucle = historique()
    acts_tous = activations()
    # LE PRESENT DU MONDE NE PEUT PAS VENIR DE LA SEULE HORLOGE. `boucle.json`
    # rend `present_secondes: 0.0` des que l'ancre a ete reposee — et une
    # fenetre calee sur zero laisse TOUT passer en se disant filtrante :
    # `--monde 2` rendait 184 activations sur 184. On prend donc le plus tard
    # des deux : l'horloge, ou le dernier instant reellement vecu par un
    # rapport. Un instrument qui ment sur son filtre est pire qu'absent.
    present = max(
        float((boucle.get("horloge") or {}).get("present_secondes") or 0.0),
        max([float(a["monde_s"] or 0) + float(a["monde_vecu_s"] or 0)
             for a in acts_tous] or [0.0]))
    billets_tous, paires = canaux()
    logs = reveils_traces()

    hors_fenetre = collections.Counter()
    acts = []
    for a in acts_tous:
        garde, motif = dans_la_fenetre(a, args, present)
        if garde:
            acts.append(a)
        elif motif:
            hors_fenetre[motif] += 1
    if args.qui:
        acts = [a for a in acts if a["qui"] == args.qui]

    # LES BILLETS NE SE FENETRENT QU'AU MUR, et grossierement : c'est le mtime
    # du CANAL entier, pas du billet. On le dit plutot que de faire croire a
    # une precision qu'on n'a pas.
    if args.tout or args.monde is not None:
        billets = billets_tous
        note = ("sans fenetre — les billets n'ont pas de date de monde"
                if args.monde is not None else "sans fenetre")
    else:
        limite = time.time() - args.heures * 3600.0
        billets = [b for b in billets_tous
                   if b["mtime"] and b["mtime"] >= limite]
        note = ("fenetre grossiere : par date du FICHIER de canal, "
                "pas par billet")
    if args.qui:
        billets = [b for b in billets
                   if b["de"] == args.qui or b["vers"] == args.qui]

    par = par_homme(acts, hist)
    toutes = not any([args.hommes, args.appels, args.actes, args.refus,
                      args.reveils, args.bilan])

    if args.json:
        m = matrice(billets)
        v, r, genres = verbes_et_resultats(acts)
        motifs, _q = ecartes()
        print(json.dumps({
            "fenetre": {"heures": args.heures, "monde": args.monde,
                        "tout": bool(args.tout), "present_secondes": present,
                        "activations_retenues": len(acts),
                        "activations_totales": len(acts_tous),
                        "billets_retenus": len(billets),
                        "billets_totaux": len(billets_tous),
                        "note_billets": note},
            "hommes": [dict(x, modeles=sorted(x["modeles"]),
                            issues=dict(x["issues"])) for x in par.values()],
            "matrice": {"%s->%s" % k: n for k, n in m.items()},
            "verbes": dict(v), "resultats": dict(r), "cibles": dict(genres),
            "ecartes_par_la_boucle": dict(motifs),
            "ecartes_par_la_fenetre": dict(hors_fenetre),
            "reveils_traces": len(logs), "canaux_ouverts": len(paires),
        }, ensure_ascii=False, indent=1))
        return 0

    quand = ("tout l'historique" if args.tout
             else ("%g h de JEU" % args.monde if args.monde is not None
                   else "%g h reelles" % args.heures))
    print("ACTIVITE — %s%s" % (quand, (" · %s" % args.qui) if args.qui else ""))
    print("%d activations retenues sur %d · %d billets sur %d · %d canaux"
          % (len(acts), len(acts_tous), len(billets), len(billets_tous),
             len(paires)))
    if hors_fenetre:
        print("  (ecartes faute d'heure : %s)"
              % ", ".join("%d %s" % (n, k) for k, n in hors_fenetre.items()))

    if toutes or args.hommes:
        _titre("QUI A FAIT QUOI")
        print("  %-20s %4s %5s %8s %8s %7s %5s  %s"
              % ("qui", "act", "pas", "monde", "reel", "$", "mut", "issue"))
        for x in sorted(par.values(), key=lambda y: -y["cout"]):
            print("  %-20s %4d %5d %8s %8s %7.2f %5d  %s"
                  % (x["qui"], x["activations"], x["actes"],
                     _duree(x["monde_s"]), _duree(x["reel_s"]), x["cout"],
                     x["mutations"],
                     " ".join("%s=%d" % (k, n)
                              for k, n in x["issues"].most_common())))
        if par:
            recent = max(par.values(), key=lambda y: y["derniere"] or 0)
            print("")
            print("  la plus recente : %s, il y a %s — %s"
                  % (recent["qui"], _depuis(recent["derniere"]),
                     str(recent["tache"] or "")[:60]))

    if toutes or args.appels:
        _titre("QUI APPELLE QUI  (%s)" % note)
        for (a, b), n in matrice(billets).most_common():
            print("  %-6s -> %-6s  %4d" % (a, b, n))
        sd = sum(1 for b in billets if not b.get("date_monde"))
        print("  %d des %d billets n'ont AUCUNE date de monde : une fenetre en"
              " heures de jeu ne peut pas les trier." % (sd, len(billets)))
        emis = collections.Counter(b["de"] for b in billets)
        recus = collections.Counter(b["vers"] for b in billets)
        print("")
        print("  %-22s %5s %5s" % ("par personne", "emis", "recus"))
        for q in sorted(set(emis) | set(recus),
                        key=lambda x: -(emis[x] + recus[x]))[:args.top]:
            print("  %-22s %5d %5d" % (q, emis[q], recus[q]))
        servis = {b["paire"] for b in billets_tous}
        muets = [p for p in paires if p not in servis]
        if muets:
            print("")
            print("  %d canal(aux) ouverts et jamais servis : %s"
                  % (len(muets), ", ".join("~".join(p) for p in muets[:6])))

    if toutes or args.actes:
        v, r, genres = verbes_et_resultats(acts)
        _titre("CE QU'ILS FONT — %d pas" % sum(v.values()))
        print("  verbes    : %s"
              % ", ".join("%s %d" % (k, n) for k, n in v.most_common(12)))
        print("  resultats : %s"
              % ", ".join("%s %d" % (k, n) for k, n in r.most_common(10)))
        print("  cibles    : %s"
              % ", ".join("%s %d" % (k, n) for k, n in genres.most_common(8)))

    if toutes or args.refus:
        motifs, q = ecartes()
        _titre("CE QUE LA BOUCLE N'ELIT PAS")
        if q.get("erreur"):
            print("  (quartier indisponible : %s)" % q["erreur"])
        else:
            print("  dans le quartier : %d · dehors : %d"
                  % (len(q.get("dedans") or {}), sum(motifs.values())))
            for k, n in motifs.most_common():
                print("    %-12s %4d" % (k, n))
            print("  RAPPEL (31.8) : « dehors » ne veut plus dire injoignable —")
            print("  ils gardent leur journee et se depechent ; seul leur budget")
            print("  de questions tombe a zero. « ilot » en revanche est une")
            print("  topologie trouee, et ceux-la sont vraiment perdus.")

    if toutes or args.reveils:
        _titre("LES REVEILS — ce qu'on en sait, et c'est peu")
        print("  %d log(s) de depeche sur disque." % len(logs))
        for x in logs[-args.top:]:
            print("    %-18s %-32s %5d o  il y a %s"
                  % (x["qui"], x["fichier"], x["octets"], _depuis(x["mtime"])))
        print("")
        print("  UN REVEIL N'EST PAS INSTRUMENTE : ni le POST d'un joueur qui")
        print("  reveille son MJ, ni le reveil en cast d'un billet ne laissent")
        print("  de ligne. Ce compte est un PLANCHER, pas une mesure ; ce qui")
        print("  est reellement trace, ce sont les activations ci-dessus.")

    if toutes or args.bilan:
        _titre("LE BILAN")
        cout = sum(a["cout_usd"] for a in acts)
        pas = sum(len(a["gestes"]) for a in acts)
        print("  %.2f $ pour %d activations et %d pas" % (cout, len(acts), pas))
        if acts:
            print("  %.2f $ par activation · %.3f $ par pas"
                  % (cout / len(acts), cout / max(1, pas)))
        try:
            total = len([d for d in os.listdir(CHAMBRES)
                         if os.path.isdir(os.path.join(CHAMBRES, d))])
        except OSError:
            total = 0
        vus = set(a["qui"] for a in acts_tous)
        print("  %d chambres · %d deja activees · %d jamais"
              % (total, len(vus), max(0, total - len(vus))))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="ACTIVITE — la loupe de debug : qui a fait quoi.")
    f = ap.add_argument_group("la fenetre")
    f.add_argument("--heures", type=float, default=24.0,
                   help="fenetre en heures REELLES (defaut : 24)")
    f.add_argument("--monde", type=float, default=None, metavar="H",
                   help="fenetre en heures de JEU (activations seules)")
    f.add_argument("--tout", action="store_true", help="sans fenetre")
    f.add_argument("--qui", default=None, help="un seul homme")
    s = ap.add_argument_group("les sections (aucune = toutes)")
    s.add_argument("--hommes", action="store_true")
    s.add_argument("--appels", action="store_true")
    s.add_argument("--actes", action="store_true")
    s.add_argument("--refus", action="store_true")
    s.add_argument("--reveils", action="store_true")
    s.add_argument("--bilan", action="store_true")
    ap.add_argument("--top", type=int, default=15, help="lignes par palmares")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.monde is not None and a.tout:
        ap.error("--monde et --tout se contredisent")
    return rendre(a)


if __name__ == "__main__":
    raise SystemExit(main())
