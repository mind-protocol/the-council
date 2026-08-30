# -*- coding: utf-8 -*-
# DISPONIBILITE (evaluer) — les questions qu'on ne pouvait pas poser.
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

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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





# La force narrative, la feuille de la regie et le main vivent dans
# disponibilite_regie.py (meme container) ; on les rattache ici pour que
# `evaluer.force_narrative` et la CLI restent au meme endroit qu'avant.
from temps.disponibilite_regie import (  # noqa: E402,F401
    force_narrative, pour_la_regie, main)
