# -*- coding: utf-8 -*-
"""LECTURE — le bati, les pieces, les liens (etat/corps.json), les
positions et les adresses : transformer des identifiants en metres.
"""
import io
import json
import math
import os
import sys

from plan.expose import bibliotheque  # LA PORTE de plan/
from etat.expose import tables  # LA PORTE de etat/

# La console de Windows est en cp1252 et le script parle avec des flèches.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Trois etages de plus qu'a la racine : scripts/agents/affectation/.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RACINE, "scripts", "monde"))
from monde.expose import bati as _bati              # le lecteur unique du bâti

DEFAUT_MONDE = _bati.DEFAUT
GENS = os.path.join(RACINE, "monde", "portreal.gens.json")
LIENS = os.path.join(RACINE, "etat", "corps.json")
PERSOS = os.path.join(RACINE, "etat", "personnages.json")
BOOKS = os.path.join(RACINE, "etat", "books.json")
PLANS = os.path.join(RACINE, "ecrans", "modules", "plans.js")
VILLE = os.path.join(RACINE, "etat", "villes", "port-real.json")

GENRES = ("lieu", "salle", "personnage", "acteur", "livre")

# LE RAYON DE RÉANCRAGE, ET IL EST PARTAGÉ. `reancrer` l'emploie pour choisir
# le bâtiment du bon métier le plus proche des mètres écrits ; `verifier`
# l'emploie pour savoir ce qu'il a le droit de reprocher. Deux chiffres
# différents aux deux endroits, et le contrôle condamne ce que la réparation
# vient de faire — c'est très exactement ce qui est arrivé.
#
# 150 m, et il a été MESURÉ, pas choisi : douze des quatorze affectations
# retrouvent leur métier à moins de 102 m, la treizième — la table de change du
# Culpucier — à 136, et à 120 elle serait retombée sur l'échoppe posée à trois
# mètres.
RAYON_REANCRAGE = 150.0

# Deux genres NOMMENT le bâtiment lui-même : un bâtiment est un endroit, et un
# seul. Les autres sont DEDANS — un livre, un homme, un jeton de la table
# partagent sans conflit le toit qui les abrite, et c'est le cas normal.
OCCUPANTS = ("lieu", "salle")



def sortir(msg):
    print(msg)
    sys.exit(1)


_MONDES = {}


def charger_bati(monde=DEFAUT_MONDE):
    """Le bâti d'un monde, gardé en mémoire — on en ouvre parfois deux."""
    monde = monde or DEFAUT_MONDE
    if monde not in _MONDES:
        try:
            _MONDES[monde] = _bati.charger(monde)
        except _bati.MondeInconnu as e:
            sortir("  %s" % e)
    return _MONDES[monde]


_PIECES = {}


def charger_pieces(monde=DEFAUT_MONDE):
    """Les intérieurs engendrés d'un monde : une pièce creuse par salle du plan.

    C'est la prise JUSTE pour une salle. Un bâtiment du bourg n'est pas une
    salle du château — l'index n'y renvoyait que faute de mieux, et il pointait
    dans le vide dès la première régénération. Une pièce, elle, porte l'id du
    plan : elle survit à la graine parce qu'elle ne dépend pas d'elle.
    """
    monde = monde or DEFAUT_MONDE
    if monde not in _PIECES:
        f = os.path.join(RACINE, "monde", "%s.interieurs.json" % monde)
        try:
            d = json.load(io.open(f, encoding="utf-8"))
            _PIECES[monde] = {s["id"]: s for s in d.get("salles", [])}
        except (OSError, ValueError, KeyError):
            _PIECES[monde] = {}
    return _PIECES[monde]


def fiche_piece(monde, pid):
    """La même forme qu'un bâtiment, pour que tout le reste ne change pas."""
    s = charger_pieces(monde).get(pid)
    if not s:
        return None
    x, y, z = s["centre"]
    return {"monde": monde, "bat": None, "piece": pid,
            "x": x, "y": y, "z": s.get("sol_z", z),
            "usage": "pièce", "quartier": s.get("nom", pid),
            "etages": 0, "facade_m": s.get("long_m", 0.0),
            "porte": (x, y)}


def monde_de(entree):
    """Le monde d'une affectation. Absent = portreal : les neuf affectations
    écrites avant que Peyredragon soit joignable restent justes telles quelles."""
    return (entree or {}).get("monde") or DEFAUT_MONDE


def charger_liens():
    L = tables.lire(LIENS, {"liens": {}, "affectations": {}})
    L.setdefault("liens", {})
    L.setdefault("affectations", {})
    return L


def retrait(chemin, defaut=2):
    """L'indentation déjà en place — pour ne pas rendre un diff illisible."""
    try:
        with io.open(chemin, encoding="utf-8") as f:
            for ligne in f:
                n = len(ligne) - len(ligne.lstrip(" "))
                if n: return n
    except OSError:
        pass
    return defaut


def ecrire(chemin, obj):
    """Relire-écrire dans la même milliseconde : à deux MJ, on ne s'écrase pas.
    L'indentation du fichier en place est préservée (voir retrait)."""
    tables.ecrire(chemin, obj, indent=retrait(chemin))


def fiche_bati(bati, C, i, monde=DEFAUT_MONDE):
    if not isinstance(i, int) or i < 0 or i >= len(bati):
        return None
    b = bati[i]
    return {
        "monde": monde,
        "bat": i, "x": b[C["x"]], "y": b[C["y"]], "z": b[C["z"]],
        "usage": b[C["usage"]], "quartier": b[C["quartier"]],
        "etages": b[C["etages"]], "facade_m": b[C["facade_m"]],
        # Tous les mondes n'ont pas de porte dans leur bâti — le bourg de
        # Peyredragon n'en porte pas. À défaut, la porte est le corps lui-même.
        "porte": (b[C["porte_x"]], b[C["porte_y"]]) if "porte_x" in C
                 else (b[C["x"]], b[C["y"]]),
    }


def dire_bati(f):
    if f.get("piece"):
        m = "" if f.get("monde", DEFAUT_MONDE) == DEFAUT_MONDE else " [%s]" % f["monde"]
        return ("  pièce « %s »%s — %s\n"
                "  x %.1f  y %.1f  z %.1f  %.1f m de long"
                % (f["piece"], m, f["quartier"],
                   f["x"], f["y"], f["z"], f["facade_m"]))
    # Le monde ne se dit que s'il n'est pas celui d'où l'on vient : la sortie
    # de Port-Réal doit rester mot pour mot ce qu'elle était.
    m = "" if f.get("monde", DEFAUT_MONDE) == DEFAUT_MONDE else " [%s]" % f["monde"]
    return ("  bâtiment %d%s — %s, %s\n"
            "  x %.1f  y %.1f  z %.1f  %d étage(s), façade %.1f m"
            % (f["bat"], m, f["usage"], f["quartier"],
               f["x"], f["y"], f["z"], f["etages"], f["facade_m"]))


# --- où se trouve une chose, affectée ou non --------------------------------

def position(L, clef):
    """Les mètres d'une chose, ET le monde où ils sont comptés. Une affectation
    d'abord ; sinon, pour un personnage, le corps que `corps.py` lui a prêté —
    les deux tables disent la même sorte de vérité et se lisent ensemble."""
    genre, _, ident = clef.partition(":")
    a = L["affectations"].get(clef)
    if a:
        m = monde_de(a)
        if a.get("piece"):
            f = fiche_piece(m, a["piece"])
            if f or genre != "personnage":
                return (f, "pièce engendrée") if f else (None, "pièce disparue")
        else:
            bati, C = charger_bati(m)
            f = fiche_bati(bati, C, a.get("bat"), m)
            if f or genre != "personnage":
                return (f, "affectation") if f else (None, "affectation morte")
        # UN HOMME EN MARCHE N'A PAS D'ADRESSE, et le serveur lui en écrit une
        # quand même : `personnage:<id>` sans `bat`, juste ses mètres de
        # l'instant. Elle ne résout donc rien — mais dead-ender ici revenait à
        # dire qu'il n'habite nulle part parce qu'il est sorti. On retombe sur
        # son corps, qui est son domicile.
    if genre == "salle":
        # Une salle du plan a déjà ses mètres si le monde l'a creusée : on ne
        # demande pas d'affectation pour lire ce qui est engendré.
        for m in _bati.mondes():
            f = fiche_piece(m, ident)
            if f:
                return (f, "pièce engendrée")
    if genre == "personnage":
        aid = next((k for k, v in L["liens"].items() if v == ident), None)
        if aid:
            g = corps_par_id(aid)
            if g:
                # les corps engendrés sont ceux de Port-Réal, et d'elle seule
                return ({"monde": DEFAUT_MONDE,
                         "bat": g["bat"], "x": g["x"], "y": g["y"], "z": g["z"],
                         "usage": g["usage"], "quartier": g["quartier"],
                         "etages": 0, "facade_m": 0.0,
                         "porte": (g["x"], g["y"])}, "corps prêté")
        # `corps.py --loger` écrit dans `corps`, pas dans `liens` : un corps
        # CRÉÉ est une adresse aussi bonne qu'un corps emprunté, et l'oublier
        # ici faisait répondre « n'a pas d'adresse physique » à un homme qu'on
        # venait de loger. Les trois tables se lisent ensemble ou aucune.
        c = next((x for x in L.get("corps", [])
                  if x.get("personnage_id") == ident), None)
        if c:
            m = c.get("monde") or DEFAUT_MONDE
            return ({"monde": m,
                     "bat": c.get("bat"), "x": c["x"], "y": c["y"], "z": c["z"],
                     "usage": c.get("usage", ""), "quartier": c.get("quartier", ""),
                     "etages": 0, "facade_m": 0.0,
                     "porte": (c["x"], c["y"])}, "corps créé")
    return (None, None)


def adresse(clef, L=None):
    """LE résolveur, celui que tout le monde doit appeler. (x, y, z) ou None.

    Il essaie dans l'ordre : l'affectation (pièce, puis bâtiment), le corps
    prêté, la pièce engendrée du même id. Il ne lit JAMAIS le `xyz` recopié
    dans `etat/corps.json` — cette copie n'est là que pour que `--verifier`
    compare, et un cache qui répond encore quand la cible est morte est
    exactement ce qui a fabriqué la carte fantôme du 24e. Une adresse morte
    rend None ; personne n'a le droit d'en tirer un chiffre.

    On accepte `salle:archives` comme `archives` — les appelants n'avaient pas
    tous la même convention, et c'est de là que venait la moitié des trous.
    """
    L = L if L is not None else charger_liens()
    essais = [clef] if ":" in clef else ["salle:" + clef, "lieu:" + clef,
                                         "personnage:" + clef]
    for c in essais:
        f, _ = position(L, c)
        if f:
            return (f["x"], f["y"], f["z"])
    return None


def corps_par_id(aid):
    """Un corps engendré, cherché cellule par cellule (jamais tout en mémoire)."""
    if not os.path.exists(GENS): return None
    G = json.load(io.open(GENS, encoding="utf-8"))
    C = {n: k for k, n in enumerate(G["_colonnes"])}
    d = os.path.join(RACINE, *G.get("dossier", "monde/gens").split("/"))
    for clef in sorted(G["cellules"]):
        f = os.path.join(d, clef + ".json")
        if not os.path.exists(f): continue
        try:
            lot = json.load(io.open(f, encoding="utf-8"))["gens"]
        except (ValueError, UnicodeDecodeError):
            continue
        for g in lot:
            if g[C["id"]] == aid:
                return {k: g[C[k]] for k in
                        ("id", "nom", "x", "y", "z", "bat", "usage", "quartier")}
    return None


# --- les registres narratifs, pour valider une clef -------------------------

def identifiants(genre):
    """Ce qui existe, du côté de la fiction. Renvoie None si le genre n'a pas
    de registre : on n'invente pas de garde qu'on ne peut pas tenir."""
    try:
        if genre == "personnage":
            P = json.load(io.open(PERSOS, encoding="utf-8"))
            return {x["id"] for x in (P if isinstance(P, list)
                                      else P.get("personnages", []))}
        if genre == "livre":
            return {x["id"] for x in bibliotheque.charger(
                os.path.join(RACINE, "etat"))}
        if genre == "acteur":
            V = json.load(io.open(VILLE, encoding="utf-8"))
            return {x["id"] for x in V.get("acteurs", []) if x.get("id")}
        if genre == "salle":
            # plans.js est du JS : on y lit les `id: "..."` sans l'exécuter.
            import re
            src = io.open(PLANS, encoding="utf-8").read()
            return set(re.findall(r'\bid:\s*"([a-z0-9\-]+)"', src))
    except (OSError, ValueError, KeyError):
        return None
    return None                                    # `lieu` : pas de registre


def visibilite_demandee(argv):
    """`--visible`, `--visible-pour a,b`, `--invisible` — ou rien.

    Rien renvoie None : réaffecter une chose déjà montrée ne la cache pas par
    surprise. C'est le drapeau qui décide, jamais l'absence de drapeau.
    """
    if "--invisible" in argv:
        return False
    if "--visible-pour" in argv:
        i = argv.index("--visible-pour")
        qui = [s for s in argv[i + 1:i + 2][0].split(",") if s] if len(argv) > i + 1 else []
        if not qui:
            sortir("  --visible-pour attend un ou plusieurs sièges, séparés "
                   "par des virgules.")
        return qui
    if "--visible" in argv:
        return True
    return None


def voit(entree, siege):
    """Ce siège a-t-il le droit de voir cette étiquette ?

    `True` = tout le monde ; une liste = ces sièges-là seulement. C'est du
    brouillard, pas de l'affichage : ce que Marlo a reconnu de ses yeux, la
    reine ne l'a pas vu.
    """
    v = entree.get("visible")
    if v is True: return True
    if isinstance(v, list): return siege in v
    return False

