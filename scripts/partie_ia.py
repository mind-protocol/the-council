#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
partie_ia.py — un camp joué par un modèle SANS OUTILS : une position entre, une ligne de coup sort.

    python scripts/partie_ia.py <partie> --camp openai --role technique            # propose, n'écrit pas
    python scripts/partie_ia.py <partie> --camp openai --role technique --vraiment # écrit au greffe
    python scripts/partie_ia.py <partie> --camp openai --role technique --voir     # montre le prompt, n'appelle pas

Pourquoi ce fichier existe, et pourquoi il n'appelle pas `depecher.py`.

Le 3.9, on a fait jouer le camp vert par un homme dépêché dans sa session :
239 000 jetons et deux minutes POUR UN COUP, dix millions la partie. Le prompt
pesait 13 000 jetons ; le reste était des tours d'outils — il TRAVAILLAIT quand
on lui demandait de JOUER (docs/partie.md, « essayé, mesuré, retiré »). Le seul
levier de l'ordre de grandeur est de lui retirer les outils : ici l'appel n'en a
aucun, sa seule sortie est le coup, en JSON contraint par un schéma, et c'est ce
script qui vérifie et qui écrit. Un modèle qui ne peut rien ouvrir ne lit pas
quatre minutes : il joue.

Ce qu'il reçoit : les règles (docs/regles-partie.md), le caractère de son camp
et de sa moitié — technique ou politique, l'autre moitié étant un humain qu'il
ne doit pas jouer —, le plateau de son camp (`partie.py --plateau --entier`) et
les coups joués depuis le sien. Ce qu'il rend : un coup. S'il est refusé par le
greffe, on lui rend le refus UNE fois ; s'il est refusé encore, on s'arrête et
on le dit — le MJ joue à la ligne. Rien ici n'écrit ailleurs que dans le jsonl
de la partie, et seulement avec --vraiment.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import time

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)
from partie_greffe import Partie, RACINE, DOSSIER, COUPS_COMPTES  # noqa: E402
import partie_cartes  # noqa: E402
import partie_ascii   # noqa: E402

REGLES = os.path.join(RACINE, "docs", "regles-partie.md")

# LE CARACTÈRE D'UN CAMP N'EST PLUS DANS CE FICHIER (C5, 7.9). Il vit dans
# `caractere: {<camp>: "<texte>"}` de etat/parties/<id>.json, et rien d'autre :
# la table `CAMPS` codée ici décrivait charmed-1 (Nexus, trois marches) et
# aurait contredit charmed-2 le jour où sa config l'aurait oublié. Un camp sans
# caractère écrit ne joue pas — `jouer()` s'arrête avant tout appel.
# LE RYTHME D'UNE MOITIÉ : l'IA joue d'abord, l'humain après l'avoir lue. Ne
# vaut que pour les rôles à partenaire — un camp joué en entier n'en a pas.
_RYTHME = ("TU JOUES EN PREMIER à chaque tour, et ton partenaire humain joue après avoir lu ton mot. "
           "Ton `mot` est votre seul canal : dis-lui ce que tu as fait et ce que tu attends de lui, "
           "sans lui donner d'ordre.")

ROLES = {
    "entier": (
        "Tu joues ton camp EN ENTIER : les états, les pièces, les clefs, les verrous, les questions, "
        "les frappes et les retournements. Personne ne joue avec toi ; en face, un humain. Un coup compté "
        "par tour, plus ce qui est gratuit (demander, justifier, un maillon qui répond). Ton `mot` "
        "s'adresse à ton ADVERSAIRE : ce que ton camp lui fait savoir, dans sa voix, sans dévoiler "
        "ce que tu prépares."),
    "technique": (
        "Tu joues la MOITIÉ TECHNIQUE de ton camp : les pièces, les clefs qui lèvent un "
        "verrou ou servent un état, les demandes de ressources (calcul, modèles, "
        "infrastructure — gratuites, l'arbitre les date), les maillons qui répondent à une "
        "question. L'autre moitié, politique, est jouée par un HUMAIN : tu ne poses pas "
        "d'état nouveau, tu ne poses pas de verrou sur un état d'en face, tu n'exiges pas "
        "de chaîne — c'est son travail. Ton coup construit avec ce qu'on a, ou obtient ce "
        "qui manque. " + _RYTHME),
    "politique": (
        "Tu joues la MOITIÉ POLITIQUE de ton camp : les verrous sur les états d'en face "
        "(avec une pièce, toujours), les questions — exiger la chaîne d'une pièce adverse, "
        "gratuit, une fois par pièce —, les états nouveaux si le deck a de la place, les "
        "maillons qui répondent à une question posée sur un verrou à toi. L'autre moitié, "
        "technique, est jouée par un HUMAIN : tu ne demandes pas de calcul ni de modèle, "
        "tu ne lèves pas de verrou avec une pièce technique — c'est son travail. " + _RYTHME),
}

# LES COUPS QUE CHAQUE RÔLE N'A PAS LE DROIT DE JOUER (C4). La prose de ROLES
# le disait déjà ; le schéma, lui, promettait tout l'enum, et le modèle jouait
# ce qu'on lui offrait — un état posé par la moitié technique, légal pour le
# greffe, et le partenaire humain héritait d'un coup hors rôle. `lever` reste
# ouvert à la politique : le greffe ne sait pas ce qu'est une pièce technique.
COUPS_HORS_ROLE = {
    "entier": (),
    "technique": ("viser", "sortir", "bloquer", "justifier", "detruire", "retourner"),
    "politique": ("demander", "reconstruire"),
}

SCHEMA = {
    "type": "object",
    "properties": {
        "coup": {"type": "string", "enum": ["viser", "sortir", "demander", "bloquer", "lever", "agir",
                                            "justifier", "detruire", "retourner", "retirer",
                                            "reconstruire", "rearmer", "passer"]},
        "id": {"type": "string"},
        "texte": {"type": "string"},
        "sur": {"type": "string"}, "sert": {"type": "string"}, "cible": {"type": "string"},
        "realise": {"type": "string"}, "qui": {"type": "string"},
        "ouvre": {"type": "array", "items": {"type": "string"}, "maxItems": 1},
        "engage": {"type": "array", "items": {"type": "string"}},
        "avec": {"type": "array", "items": {"type": "string"}},
        "nombre": {"type": "integer"},
        "genre": {"type": "string"}, "gel_tours": {"type": "integer"}, "arrive_tour": {"type": "integer"},
        "signe": {"type": "string",
                  "description": "UN emoji qui dit ce qu'est la chose (🗳️ une élection, 🚢 un port, 🔬 un résultat…)."},
        "pourquoi": {"type": "string",
                     "description": "Une phrase, pour le MJ : ce que ce coup change. N'entre pas au greffe."},
        "mot": {"type": "string",
                "description": "Ce que tu dis à l'humain de la partie, publié dans son fil. Si tu joues une moitié : "
                               "à ton partenaire, qui joue après toi — ce que tu as fait, ce que tu attends de lui. "
                               "Si tu joues seul : à ton adversaire — ce que ton camp lui fait savoir, dans sa voix, "
                               "sans dévoiler ce que tu prépares. Deux à quatre phrases, à la première personne."},
    },
    "required": ["coup", "texte", "pourquoi", "mot"],
    "additionalProperties": False,
}


# Les champs que chaque coup a le droit de porter au greffe (docs/regles-partie.md, annexe A).
_BASE = ("coup", "texte", "signe")
CHAMPS = {
    "*": _BASE,
    "viser": _BASE + ("id", "sert", "arrive_tour"),
    "sortir": _BASE + ("id",),
    "demander": _BASE + ("id", "nombre", "genre"),
    "bloquer": _BASE + ("id", "sur", "engage"),
    "lever": _BASE + ("id", "ouvre", "sert", "engage"),
    "agir": _BASE + ("id", "realise", "qui", "avec"),
    "justifier": _BASE + ("sur",),
    "detruire": _BASE + ("id", "cible", "engage", "arrive_tour"),
    "retourner": _BASE + ("id", "cible", "engage", "arrive_tour"),
    "retirer": _BASE + ("id", "gel_tours"),
    "reconstruire": _BASE + ("id", "revient_tour"),
    "rearmer": _BASE + ("id", "engage"),
    "passer": _BASE,
}


# ---------------------------------------------------------------- le prompt
def schema(p, role="entier"):
    """Le schéma du coup, sans les coups que cette partie a sortis du jeu ni
    ceux que ce rôle n'a pas le droit de jouer (COUPS_HORS_ROLE)."""
    interdits = set(partie_cartes.config(p).get("coups_interdits") or [])
    interdits |= set(COUPS_HORS_ROLE.get(role) or ())
    sc = json.loads(json.dumps(SCHEMA))
    sc["properties"]["coup"]["enum"] = [c for c in sc["properties"]["coup"]["enum"] if c not in interdits]
    return sc


def caractere_de(p, camp):
    """Le caractère écrit pour ce camp dans etat/parties/<id>.json, ou None."""
    if p is None:
        return None
    c = (partie_cartes.config(p).get("caractere") or {}).get(camp)
    return c.strip() if isinstance(c, str) and c.strip() else None


def systeme(camp, role, p=None):
    with io.open(REGLES, encoding="utf-8") as f:
        regles = f.read()
    interdits = list(partie_cartes.config(p).get("coups_interdits") or []) if p is not None else []
    hors = ("\n- CETTE PARTIE SE JOUE SANS : %s. Ces coups n'existent pas ici, ne les joue jamais."
            % ", ".join(interdits)) if interdits else ""
    # LA PORTÉE ET LA FIN, quand la partie les écrit (`portee`, `fin` de sa
    # configuration) : ce que chaque pièce peut atteindre, et quand on compte.
    cfg = partie_cartes.config(p) if p is not None else {}
    if cfg.get("portee"):
        hors += "\n- LA PORTÉE DES PIÈCES, tenue par l'arbitre (il refuse ce qui la dépasse) :"
        for cp, table in cfg["portee"].items():
            hors += "\n  · %s : " % cp + " ; ".join("%s → %s" % (k, v) for k, v in table.items())
    if cfg.get("fin"):
        hors += "\n- FIN DE PARTIE : tour %s — %s" % (cfg["fin"].get("tour"), cfg["fin"].get("regle"))
    return "\n\n".join([
        "Tu joues UN COUP dans une partie de position (le « conseil de guerre », règles ci-dessous). "
        "Tu n'as aucun outil et tu n'en as pas besoin : tout ce qu'il faut savoir est dans le message. "
        "Tu réponds par UN SEUL coup, au format JSON demandé, rien d'autre.",
        # LE CARACTÈRE VIT DANS LA PARTIE (`caractere` de sa configuration, 6.9),
        # et seulement là : `caractere_de()` a déjà refusé de jouer sans lui.
        caractere_de(p, camp) or "Tu es le camp « %s »." % camp,
        ROLES[role],
        "Comment jouer juste :\n"
        "- Un coup vise des ids EXACTS : ceux des pièces sont dans le grand livre du message, ceux des états, "
        "verrous, clefs et questions sont écrits sur le plateau (« o-democratie », « q39 »). N'en invente aucun.\n"
        "- Un coup neuf (viser, bloquer, lever, agir, detruire, retourner) reçoit un id court et neuf, "
        "préfixé de l'initiale de ton camp : « o-… » ou « a-… ».\n"
        "- « pas de ressource, pas de coup » : bloquer, lever, détruire engagent au moins une pièce À TOI, "
        "libre, nommée par son id. Une pièce en route s'engage ; une pièce gelée, posée ailleurs ou d'en face, non.\n"
        "- Un état doit être CONSTATABLE ; jamais une action. Un blocage se pose sur un état, un maillon, "
        "une clef ou une frappe D'EN FACE, jamais sur soi.\n"
        "- Ce qui manque au grand livre se DEMANDE (gratuit) : c'est souvent le meilleur coup technique.\n"
        "- UNE PIÈCE PAR COUP. Une clef à une pièce lève autant qu'une clef à deux ; la seconde est perdue pour "
        "ton partenaire tant que le coup tient. Tu n'en engages une deuxième que si l'arbitre ne pourrait pas "
        "croire le coup avec une seule — et tu le dis dans `pourquoi`. Pour renforcer plus tard, il y a `rearmer`.\n"
        "- Le texte d'un coup est une phrase, verbe d'abord, dans la voix de ton camp. Pas de commentaire dedans.\n"
        "- Tout coup qui pose une carte (viser, bloquer, lever, agir, detruire, retourner) porte un `signe` : "
        "UN emoji qui dit ce qu'est la chose, jamais le type (pas 🎯 ni 🔒).\n"
        "- Un maillon (agir) réalise une CLEF, un BLOCAGE ou une FRAPPE — jamais un état. Une question posée sur "
        "un état ne se lève pas par un maillon : c'est l'arbitre qui tranche en constatant ; on y répond en posant "
        "une clef qui sert l'état, avec des pièces.\n"
        "- Ne joue pas ce que l'autre moitié de ton camp doit jouer. Si rien de ton domaine n'avance la position, « passer »." + hors,
        "=== LES RÈGLES ===\n" + regles,
    ])


def depuis_mon_dernier(p, camp):
    """Les lignes du greffe depuis le dernier coup de ce camp : c'est ce qu'il n'a pas vu."""
    n0 = 0
    for l in p.lignes:
        if l.get("camp") == camp:
            n0 = int(l.get("n") or 0)
    return [json.dumps(l, ensure_ascii=False) for l in p.lignes if int(l.get("n") or 0) > n0]


def message(p, camp, role):
    vue = partie_cartes.vue(p, camp, 0)
    plateau = "\n".join(partie_ascii.plateau(vue, gras=False, entier=True))
    depuis = depuis_mon_dernier(p, camp)
    joues = len([1 for x in p.lignes if x.get("camp") == camp and int(x.get("tour") or 0) == p.tour
                 and x.get("coup") in COUPS_COMPTES and not x.get("repond")])
    # LES IDS DES PIÈCES, que le plateau texte ne montre pas : sans eux le modèle
    # ne peut nommer aucune pièce dans `engage`, et chaque coup serait refusé.
    pieces = []
    for rid, r in sorted(p.ressources.items(), key=lambda kv: (kv[1]["camp"], kv[0])):
        c = partie_cartes.carte_piece(p, rid)
        pieces.append("  %s · %s · %s · %s" % (rid, r["camp"], c["titre"], c["pied"]["droite"] or "libre"))
    parts = ["Tour %d. Tu es le camp « %s », moitié %s. Coups comptés déjà joués par ton camp ce tour : %d "
             "(un par moitié est toléré)." % (p.tour, camp, role, joues),
             "=== LES PIÈCES DU GRAND LIVRE (id · camp · ce que c'est · état) ===\n" + "\n".join(pieces)]
    # CE QUE LES PIÈCES CONTIENNENT (7.9). Une pièce dont le `lieu` est un
    # fichier du dépôt est servie avec son texte, pas seulement son titre :
    # dans `le-jeu-lui-meme`, les deux IA ont cité des fichiers qu'elles
    # n'avaient jamais vus, et six clefs sont tombées sur des faits faux. La
    # seule source qu'elles avaient était la description de la pièce et les
    # verrous adverses. `lieu` peut viser une section : `docs/x.md#3` sert la
    # section markdown numérotée 3 (« ## 3. … ») et rien d'autre.
    contenus = extraits(p)
    if contenus:
        parts.append("=== CE QUE LES PIÈCES CONTIENNENT (extraits des fichiers, tels quels) ===\n" + "\n\n".join(contenus))
    parts.append("=== LE PLATEAU, VU DE TON CAMP ===\n" + plateau)
    if depuis:
        parts.append("=== CE QUI S'EST JOUÉ DEPUIS TON DERNIER COUP (lignes du greffe, brutes) ===\n"
                     + "\n".join(depuis[-40:]))
    parts.append("À toi. Un seul coup, en JSON.")
    return "\n\n".join(parts)


PLAFOND_EXTRAIT = 24000  # caractères par pièce ; au-delà, la tête et le compte de lignes. 6000 tronquait le carnet et le lecteur a cité un paragraphe qui contredisait celui qu il n avait pas (presentation n°40)


def extraits(p):
    """Le texte des pièces dont le `lieu` est un fichier du dépôt (ou une section `#N` d'un markdown)."""
    out = []
    for rid, r in sorted(p.ressources.items(), key=lambda kv: (kv[1]["camp"], kv[0])):
        if r.get("detruite"):
            continue
        lieu = (r.get("lieu") or "").strip()
        if not lieu or "*" in lieu:
            continue
        chemin, _, section = lieu.partition("#")
        chemin = chemin.replace("\\", "/").strip("/")
        if ".." in chemin:
            continue
        abs_ = os.path.join(RACINE, chemin)
        if not os.path.isfile(abs_):
            continue
        try:
            texte = io.open(abs_, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if section:
            texte = section_markdown(texte, section)
            if texte is None:
                continue
        n_lignes = texte.count("\n") + 1
        if len(texte) > PLAFOND_EXTRAIT:
            texte = texte[:PLAFOND_EXTRAIT] + "\n[… coupé : %d lignes en tout, %d caractères]" % (n_lignes, len(texte))
        out.append("--- %s · %s (%s) ---\n%s" % (rid, r["camp"], lieu, texte.rstrip()))
    return out


def section_markdown(texte, numero):
    """La section `## N. …` d'un markdown, jusqu'au prochain `## `. None si absente."""
    lignes = texte.splitlines()
    debut = None
    for i, l in enumerate(lignes):
        if l.startswith("## ") and l[3:].lstrip().startswith(numero + "."):
            debut = i
        elif debut is not None and l.startswith("## "):
            return "\n".join(lignes[debut:i])
    return "\n".join(lignes[debut:]) if debut is not None else None


# ---------------------------------------------------------------- l'appel
def appeler(systeme_txt, message_txt, modele=None, effort=None, timeout=240, schema_coup=None):
    """`claude -p` sans aucun outil, sortie contrainte par le schéma. Rend (coup, mesure)."""
    # LE PROMPT SYSTÈME PASSE PAR UN FICHIER, jamais en argument : les règles
    # font 28 000 caractères, et la ligne de commande de Windows s'arrête à
    # 32 767. Deux coups sont tombés sur « The filename or extension is too
    # long » le jour où le schéma a grandi de cent caractères.
    vide = os.path.join(tempfile.gettempdir(), "partie-ia-vide")
    os.makedirs(vide, exist_ok=True)
    fichier_systeme = os.path.join(vide, "systeme-%d.md" % os.getpid())
    with io.open(fichier_systeme, "w", encoding="utf-8") as f:
        f.write(systeme_txt)
    commande = ["claude", "-p", "--tools", "", "--no-session-persistence",
                "--output-format", "json", "--json-schema", json.dumps(schema_coup or SCHEMA),
                "--system-prompt-file", fichier_systeme]
    if modele:
        commande += ["--model", modele]
    if effort:
        commande += ["--effort", effort]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    kw = {"creationflags": 0x08000000} if os.name == "nt" else {}   # pas de fenêtre
    # HORS DU DÉPÔT, et c'est la moitié du prix. Lancé dans la racine, `claude -p`
    # charge le CLAUDE.md du projet par-dessus le prompt : mesuré 56 000 jetons
    # entrés pour un prompt de 13 000. Un dossier vide n'a pas de manuel.
    t0 = time.time()
    r = subprocess.run(commande, input=message_txt.encode("utf-8"), capture_output=True,
                       timeout=timeout, cwd=vide, env=env, **kw)
    duree = time.time() - t0
    sortie = r.stdout.decode("utf-8", "replace")
    # L'ERREUR EST DANS LE JSON, PAS SUR STDERR. « OAuth session expired » est
    # arrivé en code 1 avec un stderr vide et tout le message dans `result` :
    # on lit le JSON d'abord, quel que soit le code de retour, et l'on rend sa
    # phrase — sinon on cherche une panne réseau là où il faut taper `claude login`.
    try:
        res = json.loads(sortie)
    except ValueError:
        res = None
    if res and res.get("is_error"):
        raise RuntimeError("claude a répondu par une erreur : %s" % (res.get("result") or "?"))
    if r.returncode != 0:
        raise RuntimeError("claude a quitté avec le code %d : %s"
                           % (r.returncode, (r.stderr.decode("utf-8", "replace") or sortie)[-600:]))
    if res is None:
        raise RuntimeError("réponse illisible : " + sortie[:400])
    coup = res.get("structured_output")
    if coup is None:
        brut = res.get("result") or ""
        try:
            coup = json.loads(brut)
        except ValueError:
            deb, fin = brut.find("{"), brut.rfind("}")
            coup = json.loads(brut[deb:fin + 1]) if deb >= 0 and fin > deb else None
    u = res.get("usage") or {}
    mesure = {"secondes": round(duree, 1), "cout_usd": res.get("total_cost_usd"),
              "entree": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                        + (u.get("cache_creation_input_tokens") or 0),
              "sortie": u.get("output_tokens"), "tours": res.get("num_turns"), "modele": res.get("model")}
    return coup, mesure


# ---------------------------------------------------------------- jouer
def jouer(p, camp, role, modele=None, effort=None, vraiment=False, voir=False):
    # PAS DE CARACTÈRE, PAS D'APPEL (C5) : on le dit en clair et l'on rend 2,
    # avant d'avoir construit le prompt ou dépensé un jeton.
    if not caractere_de(p, camp):
        nom = os.path.splitext(os.path.basename(p.chemin))[0]
        print("aucun caractère écrit pour le camp %s dans etat/parties/%s.json : "
              "écris-le (`caractere: {%s: …}`) avant de faire jouer une IA." % (camp, nom, camp))
        return 2
    sys_txt, msg = systeme(camp, role, p), message(p, camp, role)
    if voir:
        print(sys_txt[:1200] + "\n[…]\n\n" + msg)
        return 0
    essais, refus, ligne, mesures = 0, [], None, []
    while essais < 2:
        essais += 1
        coup, mesure = appeler(sys_txt, msg, modele, effort, schema_coup=schema(p, role))
        mesures.append(mesure)
        if not coup:
            refus = ["aucun coup dans la réponse"]
            break
        pourquoi = coup.pop("pourquoi", "")
        mot = coup.pop("mot", "")
        # NE GARDER QUE LES CHAMPS DU COUP. Le modèle remplit volontiers tout le
        # schéma — une clef est arrivée avec cible, realise, tenu_par, arrive_tour
        # et gel_tours —, et le greffe, qui ignore ce qu'il ne lit pas, aurait
        # écrit ce bruit au livre pour toujours. Un jsonl ne se réécrit pas.
        ligne = dict((k, v) for k, v in coup.items() if k in CHAMPS.get(coup.get("coup"), CHAMPS["*"]))
        ligne["camp"] = camp
        for k in ("ouvre", "engage", "avec"):
            if k in ligne and not ligne[k]:
                del ligne[k]
        refus = p.verifier(ligne)
        print("%s %s/%s → %s" % ("OK" if not refus else "REFUS", camp, role, json.dumps(ligne, ensure_ascii=False)))
        if pourquoi:
            print("   pourquoi : " + pourquoi)
        if not refus:
            break
        print("   refusé : " + " ; ".join(refus))
        msg += ("\n\nTon coup précédent a été REFUSÉ par le greffe : %s\nRejoue autre chose, ou corrige-le."
                % " ; ".join(refus))
    for m in mesures:
        print("   mesure : %ss · %s jetons entrés · %s sortis · %s tours · %s USD · %s" % (
            m["secondes"], m["entree"], m["sortie"], m["tours"], m["cout_usd"], m["modele"]))
    if refus:
        print("Le coup n'est pas écrit : le MJ joue à la ligne.")
        return 2
    if vraiment:
        r = p.ecrire(ligne)
        if r:
            print("REFUSÉ à l'écriture : " + " ; ".join(r))
            return 2
        print("écrit n°%d (tour %d)" % (p.lignes[-1]["n"], p.tour))
        if p.avertissements:
            print("!  " + "\n!  ".join(sorted(set(p.avertissements))))
        publier(p, camp, role, ligne, mot)
    else:
        if mot:
            print("   mot au partenaire : " + mot)
        print("(proposé seulement — --vraiment pour l'écrire)")
    return 0


# ---------------------------------------------------------------- publier
def sieges_de(p, camp):
    """Les sièges qui jouent ce camp, dits par `_courante.json` (`sieges`) pour CETTE partie."""
    s = (partie_cartes.config(p).get("sieges") or {}).get(camp) or []
    return list(s) if isinstance(s, list) else [s]


def publier(p, camp, role, ligne, mot):
    """L'IA parle à son partenaire DANS SON FIL, et c'est leur seul canal (6.9).

    Elle joue en premier ; l'humain joue après l'avoir lue. L'item est en
    coulisses — hors univers, zéro minute, rien dans l'état — parce que ce
    n'est pas un personnage du monde qui parle, c'est la moitié d'un camp. On
    dit le coup en clair, avec son signe, puis le mot. Sans siège déclaré pour
    ce camp, on ne publie nulle part et on le dit : un fil qu'on croit servi et
    qui ne l'est pas est pire qu'un silence."""
    sieges = sieges_de(p, camp)
    if not sieges and role == "entier":
        # UN CAMP JOUÉ SEUL PARLE À SON ADVERSAIRE : le mot de la Source va dans
        # le fil des sièges de la partie, tous camps confondus — c'est sa voix.
        sieges = [x for c in (partie_cartes.config(p).get("sieges") or {}).values()
                  for x in (c if isinstance(c, list) else [c])]
    if not sieges:
        print("   (aucun siège déclaré pour cette partie : rien publié au fil)")
        return
    signe = ligne.get("signe") or ""
    dit = partie_journal_clair(p, ligne)
    texte = "%s %s" % (signe, dit) if signe else dit
    if mot:
        texte += "\n\n" + mot
    item = {"type": "coulisses", "qui": "%s · %s (IA)" % (camp, role), "texte": texte}
    for siege in sieges:
        r = subprocess.run([sys.executable, os.path.join(RACINE, "scripts", "append_flux.py"),
                            "--pour", siege, json.dumps(item, ensure_ascii=False)],
                           cwd=RACINE, capture_output=True, timeout=60,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if r.returncode == 0:
            print("   publié au fil de %s" % siege)
        else:
            print("   ÉCHEC de la publication au fil de %s : %s" % (
                siege, (r.stderr or r.stdout).decode("utf-8", "replace")[-300:]))


def partie_journal_clair(p, ligne):
    """Le coup en clair, par le même module que l'écran (`partie_journal`)."""
    try:
        import partie_journal
        return partie_journal._phrase(p, ligne)
    except Exception:
        return "%s : %s" % (ligne.get("coup"), ligne.get("texte", ""))


def main():
    ap = argparse.ArgumentParser(description="un camp joué par un modèle sans outils")
    ap.add_argument("partie")
    ap.add_argument("--camp", required=True)
    ap.add_argument("--role", choices=("entier", "technique", "politique"), default="entier")
    ap.add_argument("--modele")
    ap.add_argument("--effort")
    ap.add_argument("--vraiment", action="store_true", help="écrire le coup au greffe")
    ap.add_argument("--voir", action="store_true", help="montrer le prompt, ne pas appeler")
    a = ap.parse_args()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8") if hasattr(sys.stdout, "buffer") else sys.stdout
    chemin = a.partie if a.partie.endswith(".jsonl") else os.path.join(DOSSIER, a.partie + ".jsonl")
    p = Partie(chemin)
    if a.camp not in p.camps():
        print("le camp « %s » n'a pas encore visé dans cette partie (camps : %s)" % (a.camp, ", ".join(p.camps())))
        sys.exit(2)
    sys.exit(jouer(p, a.camp, a.role, a.modele, a.effort, a.vraiment, a.voir))


if __name__ == "__main__":
    main()
