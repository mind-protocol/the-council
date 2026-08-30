# -*- coding: utf-8 -*-
# EVALUER — les questions qu'on ne pouvait pas poser.
#
# POURQUOI. Le tissu projete par `tisser.py` porte ~3 900 aretes sur ~1 700
# noeuds, dont 99% resolvent des deux cotes. Tant qu'elles vivaient sous treize
# noms dans cinq fichiers, aucune de ces questions n'avait de reponse :
#
#     ou sont les goulots ?  quelle pression n'a pas de contre-arete ?
#     qu'est-ce qui commande vraiment la date d'entree ?
#     qu'est-ce qui pend dans le vide ?  qui n'a pas de titulaire ?
#     quel mur est invisible au joueur ?  qui est sourd a ce qu'il fait ?
#
# CE SCRIPT NE DECIDE RIEN ET N'ECRIT PAS. Meme contrat que `tick.py` : il
# compte, il ordonne, il rend. L'arbitrage reste au MJ.
#
# LE TEST DE SORTIE, et il est ecrit avant le code : il doit retrouver SEUL
# l'equilibrage de M12 qu'on a fait a la main — 143 consommateurs, aucun
# producteur, neuf actions sans titulaire dessus, et un sous-clerc embauche le
# 27e que rien ne relie au moyen qu'il soulage. S'il ne le retrouve pas, c'est
# la nomenclature qui est fausse, pas les donnees.
#
# Usage :
#     python scripts/evaluer.py                tout, en resume
#     python scripts/evaluer.py --goulots      les noeuds satures
#     python scripts/evaluer.py --desequilibres  ce qui n'a pas de contre-arete
#     python scripts/evaluer.py --critique     ce qui commande les dates
#     python scripts/evaluer.py --orphelins    ce qui ne tombe sur personne
#     python scripts/evaluer.py --murs         les verrous sans route de fuite
#     python scripts/evaluer.py --sourds       les tetes sans declencheur
#     python scripts/evaluer.py --portees      ce que le camp d'en face engendre
import argparse
import io
import json
import os
import re
import sys
import collections
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
TISSU = os.path.join(ETAT, "tissu")

from etat.expose import tables  # noqa: E402 — LA PORTE de etat/

# ------------------------------------------------------------- les chiffres
SATURATION = 20      # au-dela, un noeud est dit sature
RARE = 3             # un moyen tenu par un seul homme est un point de rupture


def charger(nom, defaut):
    d = tables.lire(nom, defaut)
    return d.get(nom, d) if isinstance(d, dict) else d


def plat(t):
    t = unicodedata.normalize("NFD", str(t or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", t)


def lire_tissu():
    pa = os.path.join(TISSU, "aretes.jsonl")
    pn = os.path.join(TISSU, "noeuds.json")
    if not os.path.isfile(pa):
        sys.exit("Aucun tissu. Lance d'abord : python scripts/tisser.py --ecrire")
    A = [json.loads(l) for l in io.open(pa, encoding="utf-8") if l.strip()]
    N = json.load(io.open(pn, encoding="utf-8"))
    return A, N


def entrantes(A):
    d = collections.defaultdict(list)
    for a in A:
        d[a["vers"]].append(a)
    return d


def sortantes(A):
    d = collections.defaultdict(list)
    for a in A:
        d[a["de"]].append(a)
    return d


# --------------------------------------------------------------- 1. goulots

def goulots(A, N, dire):
    """UNE UNITE N'EST PAS UN GOULOT, et c'est la faute qu'on vient de retirer.

    `tisser.py` sort du flou un cout chiffre en prose (« douze hommes ») en le
    pointant vers `unite:homme` : la dimension de ce qu'il mange, jamais le
    stock ou il puise. Comptee ici, elle affichait 139 demandes et se lisait
    comme un goulot au meme rang que M12 — alors qu'une unite n'a ni capacite,
    ni producteur, ni titulaire : rien ne peut la saturer et rien ne peut la
    soulager. Le chiffre etait vrai et ne mesurait rien, ce qui est pire qu'un
    chiffre faux : il masquait les vrais goulots en tete de liste.

    Les dimensions se rendent quand meme, plus bas et sous leur nom : « 139
    couts se comptent en hommes » est un fait utile — il dit qu'aucun moyen de
    la table ne porte les bras, et donc qu'il en manque un.
    """
    ent = entrantes(A)
    lignes, dimensions = [], []
    for nid, arcs in ent.items():
        noeud = N.get(nid)
        if not noeud:
            continue
        conso = [a for a in arcs if a["nature"] in ("coute", "coute_chiffre")]
        if len(conso) < RARE:
            continue
        if noeud["genre"] == "unite":
            dimensions.append((len(conso), nid, noeud))
            continue
        if noeud["genre"] not in ("moyen", "office", "personne", "mesure"):
            continue
        lignes.append((len(conso), len(arcs), nid, noeud))
    lignes.sort(reverse=True)
    dimensions.sort(reverse=True)
    dire("LES GOULOTS — ce qui est demande plus que le reste")
    for n, tot, nid, noeud in lignes[:14]:
        marque = "  SATURE" if n >= SATURATION else ""
        dire("  {:>4} demandes  {:<34} {}{}".format(
            n, nid[:34], (noeud["quoi"] or "")[:34], marque))
    if dimensions:
        dire("")
        dire("  EN QUOI CA SE COMPTE — des dimensions, pas des stocks.")
        dire("  Un chiffre eleve ici ne dit pas qu'on manque : il dit qu'aucun")
        dire("  moyen de la table ne porte cette unite-la.")
        for n, nid, noeud in dimensions[:8]:
            dire("    {:>4} couts se comptent en {}".format(
                n, (noeud["quoi"] or nid)[:30]))
    return lignes


# -------------------------------------------------------- 2. desequilibres

def desequilibres(A, N, dire):
    """Un noeud qui n'a QUE des consommateurs. Personne ne le nourrit, personne
    ne l'allege : la pression ne peut que monter."""
    ent, sor = entrantes(A), sortantes(A)
    trouves = []
    for nid, arcs in ent.items():
        noeud = N.get(nid)
        if not noeud or noeud["genre"] not in ("moyen", "office"):
            continue
        conso = [a for a in arcs if a["nature"] in ("coute", "coute_chiffre")]
        autres = [a for a in arcs if a["nature"] not in ("coute", "coute_chiffre")]
        if len(conso) >= RARE and not autres:
            trouves.append((len(conso), nid, noeud, sor.get(nid, [])))
    trouves.sort(reverse=True)

    dire("LES PRESSIONS SANS CONTRE-ARETE")
    dire("  Un noeud dont TOUTES les aretes entrantes sont de la consommation :")
    dire("  rien ne le nourrit, rien ne l'allege, et la pression ne peut que monter.")
    dire("")
    for n, nid, noeud, sortant in trouves[:10]:
        dire("  {} — {}".format(nid, (noeud["quoi"] or "")[:52]))
        dire("      {} consommateurs · 0 producteur · {} arete(s) sortante(s)"
             .format(n, len(sortant)))
    return trouves


def candidats_equilibrage(A, N, cible, dire):
    """Ce qui SOULAGERAIT un noeud sature et n'y est relie par aucune arete.

    Reperage par le TEXTE, et c'est dit : le graphe ne peut pas trouver ce que
    personne n'a relie. C'est exactement ainsi qu'un sous-clerc embauche le 27e
    reste invisible au moyen qu'il decharge.
    """
    noeud = N.get(cible)
    if not noeud:
        return []
    mots = [m for m in plat(noeud["quoi"]).split() if len(m) > 4]
    deja = set(a["de"] for a in A if a["vers"] == cible)
    out = []
    for nid, n in N.items():
        if nid in deja or nid == cible or n["genre"] != "action":
            continue
        t = plat(n["quoi"])
        if sum(1 for m in mots if m in t) >= 2 or "clerc" in t or "plume" in t:
            out.append((nid, n))
    if out:
        dire("")
        dire("  CANDIDATS D'EQUILIBRAGE, reperes au texte et NON RELIES :")
        for nid, n in out[:6]:
            dire("    {:<10} {}".format(nid, (n["quoi"] or "")[:64]))
        dire("    -> ces aretes n'existent pas. C'est le tissage qui manque,")
        dire("       pas la ressource.")
    return out


# ---------------------------------------------------------- 3. le critique

def critique(A, N, dire):
    """La plus longue chaine de `depend_de`. Ce qui la retarde retarde tout."""
    sor = collections.defaultdict(list)
    for a in A:
        if a["nature"] == "depend_de" and a["vers"] in N:
            sor[a["de"]].append(a["vers"])
    memo = {}

    def prof(n, vus):
        if n in memo:
            return memo[n]
        if n in vus:
            return (0, [n])
        best = (0, [n])
        for s in sor.get(n, []):
            d, ch = prof(s, vus | {n})
            if d + 1 > best[0]:
                best = (d + 1, [n] + ch)
        memo[n] = best
        return best

    chaines = sorted((prof(n, set()) for n in sor), reverse=True)
    dire("LE CHEMIN CRITIQUE — la plus longue chaine de dependances")
    for d, ch in chaines[:3]:
        dire("  {} maillons :".format(d + 1))
        for n in ch:
            q = (N.get(n, {}).get("quoi") or "")[:58]
            dire("     {:<8} {}".format(n, q))
        dire("")
    return chaines


# --------------------------------------------------------- 4. les orphelins

def orphelins(A, N, dire):
    """Trois sortes de vacance, et il ne faut pas les confondre.

    Compter « les actions sans arete `tient` » donnait 501 quand la colonne
    Office nommait les gens en clair, puis 0 une fois les noms resolus. Ni
    l'un ni l'autre n'etait la question : ce qu'on veut savoir, c'est sur qui
    l'action tombe REELLEMENT.
    """
    par_action = collections.defaultdict(list)
    for a in A:
        if a["nature"] == "tient":
            par_action[a["de"]].append(a)
    vacantes, floues, muettes = [], [], []
    for nid, n in N.items():
        if n["genre"] != "action":
            continue
        arcs = par_action.get(nid, [])
        if not arcs:
            muettes.append((nid, n, ""))
        elif any(a["vers"] == "a_designer" for a in arcs):
            vacantes.append((nid, n, "à désigner"))
        elif all(a["flou"] for a in arcs):
            floues.append((nid, n, arcs[0].get("texte", "")))
    dire("CE QUI NE TOMBE SUR PERSONNE")
    dire("  {:>4} actions dont l'office est A DESIGNER — la case est ouverte"
         .format(len(vacantes)))
    dire("  {:>4} actions dont le titulaire est nomme mais ne resout pas"
         .format(len(floues)))
    dire("  {:>4} actions sans aucune mention d'office".format(len(muettes)))
    dire("")
    for nid, n, quoi in sorted(vacantes)[:10]:
        dire("    {:<8} {:<30} {}".format(nid, str(n["ou"])[:30],
                                          (n["quoi"] or "")[:34]))
    if floues:
        dire("")
        dire("  NOMMES MAIS NON RESOLUS — orthographe, ou personne inconnue :")
        for nid, n, quoi in sorted(floues)[:6]:
            dire("    {:<8} {}".format(nid, str(quoi)[:60]))
    return vacantes


# ------------------------------------------------------------- 5. les murs

def murs(dire):
    """Un verrou d'en face sans route de fuite est un mur invisible : il bloque
    et le joueur ne saura jamais pourquoi. `portee_pour_nous` dit ce qu'on
    pourrait en faire APRES l'avoir appris ; ce n'est pas une route."""
    brut = charger("plans", {})
    plans = brut.get("plans", []) if isinstance(brut, dict) else brut
    liens = charger("liens", [])

    def route_effective(route):
        if isinstance(route, dict):
            return bool(route.get("canal") or route.get("par") or route.get("etapes"))
        t = str(route or "").strip().lower()
        return bool(t) and not t.startswith(("aucune", "aucun", "néant", "neant"))

    sans, avec = [], []
    for p in plans:
        for v in p.get("verrous") or []:
            routes = [l for l in liens if isinstance(l, dict)
                      and v.get("id") in (l.get("de"), l.get("vers"))
                      and route_effective(l.get("route"))]
            ligne = {"plan": p.get("id"), "id": v.get("id"),
                     "quoi": v.get("quoi"),
                     "portee": v.get("portee_pour_nous"),
                     "routes": routes}
            (avec if routes else sans).append(ligne)
    dire("LES MURS INVISIBLES — verrous d'en face sans route de fuite")
    dire("  {} verrous, {} ont une route effective, {} n'en ont aucune".format(
        len(avec) + len(sans), len(avec), len(sans)))
    for v in sans[:10]:
        dire("    {:<12} {} — {}".format(
            v["plan"], v["id"], (v["quoi"] or "")[:48]))
    return sans


# ----------------------------------------------------------- 6. les sourds

def sourds(dire):
    """Qui n'a aucun declencheur — donc qui ne repondra jamais au joueur.

    Groupe par QUARTIER et non plus par echelle : un sourd que le joueur peut
    atteindre en dix minutes est une faute a reparer aujourd'hui, un sourd a
    l'autre bout du royaume est une economie. L'echelle melangeait les deux.
    """
    it = charger("intentions", [])
    dedans = set()
    try:
        from temps.expose import presence as mod_presence
        dedans = set((mod_presence.quartier().get("dedans") or {}))
    except Exception:
        pass
    par = collections.defaultdict(lambda: [0, 0])
    muets = []
    for t in it:
        pid = t.get("personnage_id")
        e = "quartier" if pid in dedans else "au loin"
        par[e][0] += 1
        if t.get("declencheurs"):
            par[e][1] += 1
        else:
            muets.append((e, pid))
    dire("LES SOURDS — qui ne reagira jamais a ce que le joueur fait")
    for e in ("quartier", "au loin"):
        n, d = par.get(e, [0, 0])
        if n:
            dire("  {:<9} {}/{} ont un declencheur   ({} sourds)".format(
                e, d, n, n - d))
    dire("")
    for e, pid in sorted(muets)[:14]:
        dire("    [{:<8}] {}".format(e, pid))
    return muets


# ---------------------------------------------------------- 7. les portees

def portees(dire):
    brut = charger("plans", {})
    plans = brut.get("plans", []) if isinstance(brut, dict) else brut
    dire("CE QUE LE CAMP D'EN FACE ENGENDRE CHEZ NOUS")
    for p in plans:
        eng = p.get("ce_que_ca_engendre_chez_nous") or []
        dire("  {} — {} sortie(s)".format(p["id"], len(eng)))
        for x in eng:
            dire("    [{:<10}] {}".format(x["type"][:10], x["sujet"][:62]))
            dire("       {}".format(x["pourquoi"][:70]))
    return plans



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
    # homme hors quartier n'a pas de journee ; un homme dont la journee est
    # pavee de bandes fermees n'a pas de creux. Ni l'un ni l'autre ne pense, si
    # fort soit-il — et c'est ca, le cout d'un mandat : on l'occupe.
    creux_de, motif = {}, {}
    try:
        from temps.expose import presence as mod_presence
        q = mod_presence.quartier()
        rout, chem, _ = mod_presence.charger()
        chat = mod_presence.Chateau(chem)
        pj, fiches = mod_presence.joueurs(), (rout.get("gens") or {})
        motif.update(q.get("dehors") or {})
        for pid in q.get("dedans") or {}:
            c = mod_presence.creux(pid, rout, chat)
            if c:
                creux_de[pid] = c
            # Un muet se dit POURQUOI il est muet, sinon on repare la mauvaise
            # chose : un siege occupe est normal, une journee fermee est un
            # choix, une fiche manquante est une faute.
            elif pid in pj:
                motif[pid] = "siege occupe"
            elif pid not in fiches:
                motif[pid] = "sans routine"
            else:
                motif[pid] = "journee fermee"
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

    # Le budget se calcule sur les SEULS eligibles — ceux qui ont un creux.
    eligibles = [l for l in lignes if l["creux"]]
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


if __name__ == "__main__":
    sys.exit(main())
