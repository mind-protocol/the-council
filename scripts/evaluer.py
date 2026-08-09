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
TISSU = os.path.join(ETAT, "staging", "tissu")

# ------------------------------------------------------------- les chiffres
SATURATION = 20      # au-dela, un noeud est dit sature
RARE = 3             # un moyen tenu par un seul homme est un point de rupture


def charger(nom, defaut):
    p = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(p):
        return defaut
    with io.open(p, encoding="utf-8") as fh:
        t = fh.read().strip()
    if not t:
        return defaut
    d = json.loads(t)
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
    ent = entrantes(A)
    lignes = []
    for nid, arcs in ent.items():
        noeud = N.get(nid)
        if not noeud or noeud["genre"] not in ("moyen", "office", "unite",
                                               "personne", "mesure"):
            continue
        conso = [a for a in arcs if a["nature"] in ("coute", "coute_chiffre")]
        if len(conso) < RARE:
            continue
        lignes.append((len(conso), len(arcs), nid, noeud))
    lignes.sort(reverse=True)
    dire("LES GOULOTS — ce qui est demande plus que le reste")
    for n, tot, nid, noeud in lignes[:14]:
        marque = "  SATURE" if n >= SATURATION else ""
        dire("  {:>4} demandes  {:<34} {}{}".format(
            n, nid[:34], (noeud["quoi"] or "")[:34], marque))
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
    et le joueur ne saura jamais pourquoi."""
    brut = charger("plans", {})
    plans = brut.get("plans", []) if isinstance(brut, dict) else brut
    sans, avec = [], []
    for p in plans:
        for v in p.get("verrous") or []:
            (avec if v.get("portee_pour_nous") else sans).append((p["id"], v))
    dire("LES MURS INVISIBLES — verrous d'en face sans route de fuite")
    dire("  {} verrous, {} portent une portee, {} n'en portent pas".format(
        len(avec) + len(sans), len(avec), len(sans)))
    for pid, v in sans[:10]:
        dire("    {:<12} {} — {}".format(pid, v["id"], (v["quoi"] or "")[:48]))
    if avec:
        dire("")
        dire("  PAR PORTEE :")
        c = collections.Counter(v["portee_pour_nous"].split(" —")[0]
                                for _, v in avec)
        for k, n in c.most_common():
            dire("    {:<28} {}".format(k[:28], n))
    return sans


# ----------------------------------------------------------- 6. les sourds

def sourds(dire):
    it = charger("intentions", [])
    par = collections.defaultdict(lambda: [0, 0])
    muets = []
    for t in it:
        e = (t.get("echelle") or "?").strip()
        par[e][0] += 1
        if t.get("declencheurs"):
            par[e][1] += 1
        else:
            muets.append((e, t.get("personnage_id")))
    dire("LES SOURDS — qui ne reagira jamais a ce que le joueur fait")
    for e in ("scene", "orbite", "royaume"):
        n, d = par.get(e, [0, 0])
        if n:
            dire("  {:<9} {}/{} ont un declencheur   ({} sourds)".format(
                e, d, n, n - d))
    dire("")
    for e, pid in sorted(muets)[:14]:
        dire("    [{:<7}] {}".format(e, pid))
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
POIDS_ECHELLE = {"scene": 6, "orbite": 3, "royaume": 1}
POIDS_ACTION = 1          # par action tenue, plafonne
PLAFOND_ACTIONS = 12
POIDS_CRITIQUE = 5        # par action sur le chemin critique — le plus lourd
POIDS_MOYEN_SATURE = 6    # tenir un goulot met un homme au centre
POIDS_DECLENCHEUR = 2     # un homme arme pour reagir au joueur
PLAFOND_CROYANCES = 5

# Combien de questions on lui pose dans les creux de sa boucle.
PALIERS = ((40, 5), (20, 3), (10, 1), (0, 0))


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

    lignes = []
    for pid, t in tetes.items():
        acts = tenu.get(pid, [])
        crit = sum(1 for a in acts if a in sur_critique)
        gou = [m for m in porte.get(pid, []) if m in satures]
        f = (POIDS_ECHELLE.get((t.get("echelle") or "").strip(), 0)
             + POIDS_ACTION * min(len(acts), PLAFOND_ACTIONS)
             + POIDS_CRITIQUE * crit
             + (POIDS_MOYEN_SATURE if gou else 0)
             + POIDS_DECLENCHEUR * len(t.get("declencheurs") or [])
             + min(len(t.get("croyances") or []), PLAFOND_CROYANCES))
        budget = next(q for seuil, q in PALIERS if f >= seuil)
        lignes.append({"qui": pid, "force": f, "questions": budget,
                       "echelle": t.get("echelle"), "actions": len(acts),
                       "critiques": crit, "goulots": gou,
                       "declencheurs": len(t.get("declencheurs") or [])})
    lignes.sort(key=lambda x: -x["force"])

    dire("LA FORCE NARRATIVE — ce que chacun pese, et ce qu'on lui paie")
    dire("  Le budget d'inference ne se decide pas : il se mesure. Un homme")
    dire("  qu'aucune arete ne met en position ne merite aucune question.")
    dire("")
    dire("  {:>4} {:>3}  {:<20} {:<8} {:>4} {:>5} {:>5}  {}".format(
        "for", "q", "qui", "echelle", "act", "crit", "decl", "goulot"))
    for l in lignes[:18]:
        dire("  {:>4} {:>3}  {:<20} {:<8} {:>4} {:>5} {:>5}  {}".format(
            l["force"], l["questions"], l["qui"][:20], l["echelle"] or "?",
            l["actions"], l["critiques"], l["declencheurs"],
            ", ".join(g.split(":")[-1] for g in l["goulots"])))
    dire("  ...")
    for l in lignes[-4:]:
        dire("  {:>4} {:>3}  {:<20} {:<8} {:>4} {:>5} {:>5}".format(
            l["force"], l["questions"], l["qui"][:20], l["echelle"] or "?",
            l["actions"], l["critiques"], l["declencheurs"]))
    total = sum(l["questions"] for l in lignes)
    servis = sum(1 for l in lignes if l["questions"])
    dire("")
    dire("  {} questions au total, sur {} tetes servies (sur {}).".format(
        total, servis, len(lignes)))
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
        import presence as mod_presence
        ou = mod_presence.resoudre()
        gens = charger("personnages", [])
        noms = {g.get("id"): (g.get("nom") or g.get("id"))
                for g in gens if isinstance(g, dict)}
        arretes, chemin = collections.defaultdict(list), []
        for pid, o in ou.items():
            if o.get("etat") == "arrete":
                cle = o.get("salle") or ("(hors plan) %s" % (o.get("lieu") or "?"))
                arretes[cle].append(noms.get(pid, pid))
            else:
                chemin.append({"qui": noms.get(pid, pid), "de": o.get("de"),
                               "vers": o.get("vers")})
        out["presence"] = {
            "salles": [{"salle": k, "gens": sorted(v)}
                       for k, v in sorted(arretes.items())],
            "en_chemin": sorted(chemin, key=lambda x: x["qui"]),
        }
    except Exception as e:
        out["presence"] = {"erreur": str(e)[:120]}

    # --- QUI A QUELQUE CHOSE A DIRE CE MATIN, et qui doit une journee.
    try:
        import travaux as mod_travaux
        import convoquer as mod_convoquer
        monde = charger("monde", {})
        date = monde.get("date") or {"annee": 0, "lune": 1, "jour": 1}
        auj = mod_travaux.jour_absolu(date) or 0
        trav = mod_travaux.lire_travaux()
        lignes, _mut = mod_travaux.calculer_travaux(trav, auj, 0)
        out["travaux"] = [{"qui": l["qui"], "affaire": l["affaire"],
                           "excitation": l["excitation"], "verdict": l["verdict"],
                           "pensees": l["pensees"], "due": l["due"],
                           "en_retard": l["en_retard"]} for l in lignes]
        conv = mod_convoquer.convoquer(trav, auj, False)
        out["convocations"] = [{"qui": q, "motifs": m,
                                "affaires": [t.get("affaire") for t in siens]}
                               for q, siens, m in conv]
    except Exception as e:
        out["travaux"] = []
        out["convocations"] = [{"qui": "erreur", "motifs": [str(e)[:120]],
                                "affaires": []}]

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
            "sourds": [{"echelle": e, "qui": q} for e, q in so],
            "force": force_narrative(A, N, muet),
        }
        out.update(pour_la_regie(A, N, muet))
        p = os.path.join(TISSU, "evaluation.json")
        with io.open(p, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
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
