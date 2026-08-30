# -*- coding: utf-8 -*-
"""AFFECTER — donner une adresse physique à une chose de la fiction.

    python scripts/affecter.py                          l'état des affectations
    python scripts/affecter.py --bati 1554              la fiche d'un bâtiment
    python scripts/affecter.py --chercher --usage taverne --pres-de 1772,2789
    python scripts/affecter.py --chercher --usage chateau-archives --monde peyredragon
    python scripts/affecter.py --affecter lieu:la-gaffe 1554 --vraiment
    python scripts/affecter.py --affecter salle:archives piece:archives --monde peyredragon --vraiment

UNE SALLE SE VISE PAR SA PIÈCE, pas par un bâtiment. Les intérieurs engendrés
(`monde/<monde>.interieurs.json`) portent une pièce creuse par salle du plan,
sous l'id du plan : cette prise-là survit à une régénération, un index de
bâtiment non. Le 24e, huit salles de Peyredragon pointaient vers des bâtiments
disparus — et comme l'affectation recopie les mètres, `--entre` et `--rayon`
répondaient encore, sur une carte fantôme. Une salle que le monde a creusée n'a
d'ailleurs plus besoin d'affectation du tout : `--ou salle:cachots` répond seul.
On n'en écrit une que pour ce que le plan ne creuse pas (une taverne, un
chantier) ou pour porter un `nom`, une `note`, un `visible`.
    python scripts/affecter.py --ou lieu:la-gaffe
    python scripts/affecter.py --entre lieu:la-gaffe personnage:marlo-vasse
    python scripts/affecter.py --defaire lieu:la-gaffe --vraiment
    python scripts/affecter.py --verifier

POURQUOI. `scripts/corps.py` fait déjà ce geste, mais pour un seul couple :
personnage <-> corps engendré. Or c'est la MÊME opération pour tout le reste —
une taverne nommée en scène, une salle du plan, un acteur de la table de guerre,
un livre posé quelque part. Tant qu'une chose n'est pas affectée, elle n'a pas
de mètres : on ne peut pas dire combien de pas la séparent d'une autre, donc
on l'estime, donc on se trompe. Affecter, ce n'est pas décorer — c'est
transformer des distances en FAITS, et donc rendre calculables les délais et
les `cout` d'étape qui s'estimaient au doigt mouillé.

Ce que ça a donné la première fois qu'on l'a fait pour des gens : le corps de
garde de la Gadoue est à douze mètres du coffre de Marlo. Personne ne l'avait
écrit ; c'est la géométrie qui l'a dit.

LE CONTRAT, le même que pour les corps :
  - le monde engendré (`monde/`) est régénérable et bête — on n'y écrit JAMAIS ;
  - ce qui est décidé en jeu vit dans `etat/corps.json`, sous la clef
    `affectations`, et survit à tous les passages de `scripts/monde/peupler.py` ;
  - rien ne s'écrit sans `--vraiment` ;
  - `--verifier` (appelé aussi par `scripts/tick.py --verifier`) signale les
    affectations dont la cible a disparu après une régénération.

LA FORME. Une affectation est une entrée « quoi narratif -> quoi physique » :

    "lieu:la-gaffe": {"bat": 1554, "note": "...", "date": "129.3.24"}

La clef porte son GENRE, parce qu'un même identifiant peut exister des deux
côtés (`salle:cabane-du-peigne` n'est pas `lieu:cabane-du-peigne`) :

    lieu        un endroit nommé par la fiction (La Gaffe, le chantier du bout)
    salle       une salle de `ecrans/modules/plans.js`
    personnage  une fiche de `personnages.json` — mais préfère `corps.py --lier`,
                qui emprunte un corps VIVANT au lieu d'un bâtiment vide
    acteur      un acteur de `etat/villes/<lieu>.json`
    livre       un livre de `etat/books.json`

La cible est un INDEX de bâtiment dans `monde/<monde>.bati.json` — le même
entier que la colonne `bat` des corps. C'est la seule prise stable : les
bâtiments sont réengendrés à l'identique tant que la graine ne change pas, et
si elle change, `--verifier` le dit au lieu de laisser mentir la carte.

LE MONDE est une donnée de l'affectation, à côté de `bat` :

    "salle:table-peinte": {"monde": "peyredragon", "bat": 812, ...}

Son ABSENCE vaut « portreal » — les affectations écrites avant que Peyredragon
soit joignable restent valides sans être retouchées. L'index reste un ENTIER :
on ne préfixe pas, parce que `bat` est aussi la colonne des corps engendrés et
qu'un entier se compare, se trie et se vérifie. L'unicité d'un bâtiment porte
donc sur la PAIRE (monde, bat) : le bâtiment 1554 de Port-Réal et le 1554 de
Peyredragon n'ont rien à voir l'un avec l'autre.
"""
import io, json, math, os, sys, tempfile

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import bibliotheque

# La console de Windows est en cp1252 et le script parle avec des flèches.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts", "monde"))
import bati as _bati                                # le lecteur unique du bâti

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
    if not os.path.exists(LIENS):
        return {"liens": {}, "affectations": {}}
    L = json.load(io.open(LIENS, encoding="utf-8"))
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
    """Relire-écrire dans la même milliseconde : à deux MJ, on ne s'écrase pas."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(chemin), suffix=".tmp")
    with io.open(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=retrait(chemin)))
    os.replace(tmp, chemin)


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


def verifier(L, bati=None, C=None):
    """Ce qui ne tient plus. Appelé aussi par `tick.py --verifier`.

    Le bâti n'est plus passé en argument : chaque affectation dit SON monde, et
    l'on va chercher le bon. (Les deux paramètres restent acceptés pour les
    appelants d'avant, et sont ignorés.)
    """
    maux = []
    for clef, a in sorted(L["affectations"].items()):
        genre, _, ident = clef.partition(":")
        if genre not in GENRES:
            maux.append("[%s] genre inconnu — attendus : %s"
                        % (clef, ", ".join(GENRES)))
            continue
        m = monde_de(a)
        if m not in _bati.mondes():
            maux.append("[%s] monde inconnu : %s — engendré nulle part "
                        "(mondes présents : %s)"
                        % (clef, m, ", ".join(_bati.mondes()) or "aucun"))
            continue
        connus = identifiants(genre)
        if a.get("piece"):
            if not fiche_piece(m, a["piece"]):
                maux.append("[%s] pièce « %s » absente des intérieurs de « %s » "
                            "— le monde ne l'a pas creusée"
                            % (clef, a["piece"], m))
            if connus is not None and ident not in connus:
                maux.append("[%s] plus aucun %s de cet id" % (clef, genre))
            continue
        try:
            bati, C = _bati.charger(m)
        except _bati.MondeInconnu as e:
            maux.append("[%s] %s" % (clef, e))
            continue
        i = a.get("bat")
        # Le serveur écrit la position d'un marcheur en `personnage:<id>`, sans
        # `bat` : ce n'est pas une affectation qui aurait perdu sa cible, c'est
        # un homme entre deux portes. Le signaler à chaque pas ferait crier le
        # vérificateur pour tout le monde qui bouge.
        if genre == "personnage" and i is None:
            continue
        if not isinstance(i, int) or i < 0 or i >= len(bati):
            maux.append("[%s] bâtiment %r hors du monde engendré « %s » — il a "
                        "ete regenere, ou l'index est faux" % (clef, i, m))
            continue
        connus = identifiants(genre)
        if connus is not None and ident not in connus:
            maux.append("[%s] plus aucun %s de cet id : l'affectation pointe "
                        "vers un bâtiment bien réel, pour une chose disparue"
                        % (clef, genre))
        attendu = a.get("usage")
        if attendu and bati[i][C["usage"]] != attendu:
            maux.append("[%s] le bâtiment %d est devenu un %s, il était un %s"
                        % (clef, i, bati[i][C["usage"]], attendu))
        # LES MÈTRES ÉCRITS SONT L'INTENTION, LE RANG N'EST QU'UN CACHE — et
        # c'est ce qui décide de ce qu'on a le droit de reprocher ici.
        #
        # Ce contrôle comparait `xyz` à la position du bâtiment avec un seuil de
        # deux mètres. Or `reancrer` ne réécrit JAMAIS `xyz` — délibérément :
        # sans quoi chaque régénération re-ancrerait sur le voisin d'à côté,
        # puis sur le voisin du voisin, et l'adresse dériverait au hasard de
        # cent cinquante mètres par passage sans que personne le voie. Le prix
        # de ce choix est qu'une affectation replacée garde un écart résiduel —
        # et le contrôle le dénonçait comme une panne. Quatorze alertes qui ne
        # s'éteignaient plus, dans un relevé que `tick.py --verifier` lit à
        # chaque début de session : la seule chose qu'un tel avertissement
        # enseigne est de ne plus lire les avertissements.
        #
        # On ne se plaint donc que lorsque la résolution est MAUVAISE : plus
        # rien du bon métier à portée. Le résidu d'un réancrage réussi se lit
        # où il doit se lire — dans `--reancrer`, qui l'imprime en clair.
        xyz = a.get("xyz")
        if xyz:
            d = math.hypot(bati[i][C["x"]] - xyz[0], bati[i][C["y"]] - xyz[1])
            if d > RAYON_REANCRAGE:
                maux.append("[%s] le bâtiment %d est à %.0f m des mètres "
                            "écrits, et plus rien du bon métier n'est à portée "
                            "— l'adresse est perdue, il faut la reposer à la "
                            "main" % (clef, i, d))
    return maux


def reancrer(L, monde, vraiment):
    """Remettre chaque affectation sur le bâtiment qui est À SA POSITION.

    LE RANG N'EST PAS UNE ADRESSE DURABLE, et c'est écrit depuis toujours :
    « le rang n'est stable que tant que bati.json n'est pas réengendré ». Le
    28e, le monde a été refait — quarante-huit mille bâtiments devenus
    quarante-cinq mille — et les quatorze affectations ont glissé avec. La
    porte de Fer désignait une échoppe à trois kilomètres.

    LES MÈTRES, EUX, TIENNENT. `--affecter` écrit `xyz` en même temps que le
    rang, précisément pour ce jour-là : la position est la vraie adresse, le
    rang n'en est qu'un raccourci. On relit donc la position et l'on redonne
    le rang.

    ET L'ON NE RÉÉCRIT PAS `xyz`. C'est le point qui a manqué de se perdre : il
    serait tentant de recaler les mètres sur le bâtiment qu'on vient de choisir,
    ce qui ferait taire `--verifier` d'un coup. Ce serait échanger un faux
    avertissement contre une dérive muette — chaque régénération ancrerait sur
    le voisin, puis sur le voisin du voisin, et au bout de quatre passages la
    Gaffe serait à trois rues de la porte sans qu'une seule ligne l'ait dit.
    L'intention ne bouge pas ; c'est le contrôle qui a appris à ne se plaindre
    que du vrai (voir `verifier`).

    ON CHERCHE D'ABORD LE BON MÉTIER. Une affectation dit ce qu'elle attend
    (`usage`) : le corps de garde de la porte de Fer est un corps de garde.
    Prendre le plus proche TOUT COURT, c'est risquer de nommer « porte de
    Fer » la maison d'à côté parce qu'elle est à deux mètres de moins. On
    prend donc le plus proche DU MÉTIER ATTENDU dans un rayon raisonnable, et
    l'on ne retombe sur le plus proche tout court qu'à défaut — en le disant.
    """
    bati, C = charger_bati(monde)
    ix, iy, iu = C["x"], C["y"], C["usage"]
    # Un lieu nommé « Le change » que le jeu rapporterait comme une échoppe
    # serait faux DANS LA FICTION, là où cent trente-six mètres ne sont qu'un
    # semis qui a glissé. Mieux vaut le bon métier un peu déplacé que le mauvais
    # métier pile sur le point. (Le chiffre est en tête de fichier : `verifier`
    # s'en sert aussi, et il faut qu'ils disent la même chose.)
    RAYON = RAYON_REANCRAGE
    A = L["affectations"]
    lignes, change = [], 0
    for clef in sorted(A):
        v = A[clef]
        if not isinstance(v, dict) or v.get("bat") is None:
            continue
        if monde_de(v) != monde:
            continue
        xyz = v.get("xyz")
        if not xyz:
            lignes.append(("  %-34s pas de mètres écrits : on ne peut pas la "
                           "replacer" % clef, None))
            continue
        attendu = v.get("usage")
        best_u = best_t = None
        for i, r in enumerate(bati):
            d = math.hypot(r[ix] - xyz[0], r[iy] - xyz[1])
            if best_t is None or d < best_t[0]:
                best_t = (d, i)
            if attendu and r[iu] == attendu and (best_u is None or d < best_u[0]):
                best_u = (d, i)
        choix, par = (best_u, "métier") if (best_u and best_u[0] <= RAYON) else (best_t, "position")
        if not choix:
            continue
        d, i = choix
        avant = v["bat"]
        note = ""
        if par == "position" and attendu:
            note = "  ** aucun %s à moins de %d m : pris au plus proche (%s) **" % (
                attendu, RAYON, bati[i][iu])
        if i == avant:
            lignes.append(("  %-34s bat %-6d inchangé (%.0f m)" % (clef, i, d), None))
            continue
        change += 1
        lignes.append(("  %-34s bat %-6d -> %-6d  %.0f m, par %s%s"
                       % (clef, avant, i, d, par, note), (clef, i)))
    for txt, _ in lignes:
        print(txt)
    print()
    if not change:
        print("  rien à replacer : tout est déjà en place.")
        return
    if not vraiment:
        print("  %d affectations à replacer. Rien n'est écrit." % change)
        print("  → python scripts/affecter.py --reancrer --vraiment")
        return
    for _, maj in lignes:
        if maj:
            A[maj[0]]["bat"] = maj[1]
    ecrire(LIENS, L)
    print("  %d affectations replacées dans %s." % (change, LIENS))


def main():
    a = sys.argv[1:]
    def opt(nom, n=1):
        if nom not in a: return None
        i = a.index(nom)
        return a[i + 1:i + 1 + n]
    vraiment = "--vraiment" in a
    # Le monde sur lequel on travaille — pour --affecter, --chercher, --bati.
    # Les affectations déjà écrites disent le leur ; ce drapeau ne les touche pas.
    monde = ((a[a.index("--monde") + 1] if "--monde" in a
              and len(a) > a.index("--monde") + 1 else None) or DEFAUT_MONDE)
    if "--monde" in a and monde not in _bati.mondes():
        sortir("  monde inconnu : %s (présents : %s)"
               % (monde, ", ".join(_bati.mondes()) or "aucun"))

    bati, C = charger_bati(monde)
    L = charger_liens()

    # --- l'état -------------------------------------------------------------
    if not a:
        A = L["affectations"]
        print("  %d bâtiments engendrés, %d affectations, %d corps prêtés"
              % (len(bati), len(A), len(L["liens"])))
        for clef, v in sorted(A.items()):
            m = monde_de(v)
            if v.get("piece"):
                f = fiche_piece(m, v["piece"])
                vu = v.get("visible")
                marque = ("  [vu de tous]" if vu is True else
                          "  [vu de %s]" % ", ".join(vu) if isinstance(vu, list) else "")
                print("   %-34s -> pièce %-14s (%s) %s%s"
                      % (clef, v["piece"], m,
                         f["quartier"] if f else "** non creusée **", marque))
                continue
            bt, Ct = charger_bati(m)
            f = fiche_bati(bt, Ct, v.get("bat", -1), m)
            vu = v.get("visible")
            marque = ("  [vu de tous]" if vu is True else
                      "  [vu de %s]" % ", ".join(vu) if isinstance(vu, list) else "")
            ou = "" if m == DEFAUT_MONDE else " (%s)" % m
            print("   %-34s -> bâtiment %-6s%s %s%s"
                  % (clef, v.get("bat"), ou,
                     "%s, %s" % (f["usage"], f["quartier"]) if f
                     else "** hors du monde engendré **", marque))
        print()
        print("  python scripts/affecter.py --chercher --usage taverne "
              "--pres-de 1772,2789")
        return

    # --- replacer -----------------------------------------------------------
    # Avant tout le reste : c'est une réparation, elle ne se mêle à rien.
    if "--reancrer" in a:
        return reancrer(L, monde, vraiment)

    # --- consulter ----------------------------------------------------------
    if opt("--bati"):
        f = fiche_bati(bati, C, int(opt("--bati")[0]), monde)
        if not f: sortir("  aucun bâtiment de cet index.")
        print(dire_bati(f))
        pris = [k for k, v in L["affectations"].items()
                if v.get("bat") == f["bat"] and monde_de(v) == monde]
        if pris: print("  -> déjà affecté à %s" % ", ".join(pris))
        return

    if opt("--ou"):
        clef = opt("--ou")[0]
        f, comment = position(L, clef)
        if not f:
            print("  %s n'a pas d'adresse physique%s."
                  % (clef, " (affectation morte)" if comment else ""))
            return
        print(dire_bati(f))
        print("  (%s)" % comment)
        note = (L["affectations"].get(clef) or {}).get("note")
        if note: print("  %s" % note)
        return

    if opt("--entre", 2):
        c1, c2 = opt("--entre", 2)
        f1, _ = position(L, c1)
        f2, _ = position(L, c2)
        for c, f in ((c1, f1), (c2, f2)):
            if not f: sortir("  %s n'a pas d'adresse physique." % c)
        # Deux mondes engendrés ont chacun leur origine : leurs mètres ne se
        # soustraient pas. Une distance inventée entre Port-Réal et Peyredragon
        # aurait l'air d'un chiffre, et un chiffre, on le croit.
        if f1["monde"] != f2["monde"]:
            sortir("  %s est dans « %s », %s dans « %s » — deux mondes engendrés "
                   "n'ont pas la même origine, cette distance n'existe pas.\n"
                   "  (pour une route entre places, c'est la table peinte et "
                   "`jours_de_pr`, pas la géométrie.)"
                   % (c1, f1["monde"], c2, f2["monde"]))
        d = math.hypot(f1["x"] - f2["x"], f1["y"] - f2["y"])
        # 0,75 m par pas d'homme qui marche vite, 5 km/h pour le temps
        print("  %s -> %s" % (c1, c2))
        print("  %.0f m — soit %d pas, environ %d minutes de marche"
              % (d, round(d / 0.75), max(1, round(d / 83.0))))
        return

    if "--chercher" in a:
        usage = (opt("--usage") or [None])[0]
        quartier = (opt("--quartier") or [None])[0]
        combien = int((opt("--n") or ["8"])[0])
        pres = (opt("--pres-de") or [None])[0]
        px = py = None
        if pres:
            try:
                px, py = [float(v) for v in pres.replace(" ", "").split(",")]
            except ValueError:
                sortir("  --pres-de attend « x,y » (mètres).")
        pris = {v.get("bat") for v in L["affectations"].values()
                if monde_de(v) == monde}
        trouves = []
        for i, b in enumerate(bati):
            if usage and b[C["usage"]] != usage: continue
            if quartier and quartier.lower() not in b[C["quartier"]].lower():
                continue
            d = (math.hypot(b[C["x"]] - px, b[C["y"]] - py)
                 if px is not None else 0.0)
            trouves.append((d, i, b))
        if not trouves:
            print("  aucun bâtiment. (usages : %s)"
                  % ", ".join(sorted({b[C["usage"]] for b in bati})[:14]))
            return
        trouves.sort(key=lambda t: t[0])
        for d, i, b in trouves[:combien]:
            print(dire_bati(fiche_bati(bati, C, i, monde)))
            if px is not None: print("  à %.0f m du point donné" % d)
            if i in pris: print("  ** déjà affecté **")
            print()
        return

    # --- affecter -----------------------------------------------------------
    if opt("--affecter", 2):
        clef, cible = opt("--affecter", 2)
        genre, _, ident = clef.partition(":")
        if genre not in GENRES:
            sortir("  genre inconnu : %s (attendus : %s)"
                   % (genre or "(vide)", ", ".join(GENRES)))
        if not ident:
            sortir("  il manque l'identifiant : %s:<id>" % genre)
        connus = identifiants(genre)
        if connus is not None and ident not in connus:
            sortir("  aucun %s de cet id : %s — écris-le d'abord dans sa table."
                   % (genre, ident))
        # Une salle se vise par sa PIÈCE quand le monde l'a creusée : c'est la
        # seule cible qui survive à une régénération, puisqu'elle porte l'id du
        # plan et non un index de graine.
        pid = cible[6:] if cible.startswith("piece:") else cible
        if fiche_piece(monde, pid):
            fp = fiche_piece(monde, pid)
            print(dire_bati(fp))
            print("  -> %s prendrait cette pièce." % clef)
            if not vraiment:
                print("  (rien écrit — ajoute --vraiment)")
                return
            entree = dict(L["affectations"].get(clef) or {})
            entree.pop("bat", None)
            entree.pop("usage", None)
            entree["piece"] = pid
            entree["xyz"] = [round(fp["x"], 1), round(fp["y"], 1),
                             round(fp["z"], 1)]
            if monde == DEFAUT_MONDE:
                entree.pop("monde", None)
            else:
                entree["monde"] = monde
            nom = (opt("--nom") or [None])[0]
            if nom: entree["nom"] = nom
            note = (opt("--note") or [None])[0]
            if note: entree["note"] = note
            v = visibilite_demandee(a)
            if v is not None: entree["visible"] = v
            L["affectations"][clef] = entree
            ecrire(LIENS, L)
            print("  écrit dans etat/corps.json")
            return
        try:
            i = int(cible)
        except ValueError:
            sortir("  la cible est un index de bâtiment (un entier), ou une "
                   "pièce des intérieurs (`piece:<id>`). "
                   "Trouve-la avec --chercher.")
        f = fiche_bati(bati, C, i, monde)
        if not f: sortir("  aucun bâtiment d'index %d dans « %s »." % (i, monde))
        # Deux endroits de la fiction peuvent légitimement tomber sur le même
        # bâtiment — une porte et son corps de garde sont le même mètre carré,
        # et le plan les distingue parce que la SCÈNE les distingue. On ne
        # refuse donc pas : on le dit, et `--verifier` s'en souviendra. Refuser
        # obligerait à mentir sur la géographie pour contenter le script.
        if genre in OCCUPANTS:
            # L'unicité porte sur la PAIRE (monde, bat) : le 1554 de Port-Réal
            # et le 1554 de Peyredragon ne sont pas le même mètre carré.
            deja = [k for k, v in L["affectations"].items()
                    if v.get("bat") == i and monde_de(v) == monde and k != clef
                    and k.partition(":")[0] in OCCUPANTS]
            if deja:
                print("  ATTENTION : ce bâtiment est déjà celui de %s. Les deux "
                      "auront exactement les mêmes mètres." % ", ".join(deja))
        dedans = [k for k, v in L["affectations"].items()
                  if v.get("bat") == i and monde_de(v) == monde and k != clef
                  and k.partition(":")[0] in OCCUPANTS]
        if dedans and genre not in OCCUPANTS:
            print("  (à l'intérieur de %s)" % ", ".join(dedans))
        print(dire_bati(f))
        print("  -> %s prendrait ce bâtiment." % clef)
        if not vraiment:
            print("  (rien écrit — ajoute --vraiment)")
            return
        # On recopie les mètres DANS l'affectation. Le décor peut alors poser
        # l'étiquette sans ouvrir les cinq mégaoctets du bâti à chaque requête,
        # et `--verifier` compare la copie à la source : si la ville a été
        # réengendrée autrement, la dérive se voit au lieu de se taire.
        # Réaffecter n'efface pas ce qu'on avait écrit : le nom et la note sont
        # du travail de MJ, la cible est de la tuyauterie.
        entree = dict(L["affectations"].get(clef) or {})
        entree.update({"bat": i, "usage": f["usage"],
                       "xyz": [round(f["x"], 1), round(f["y"], 1),
                               round(f["z"], 1)]})
        # On n'écrit le monde que s'il n'est pas celui par défaut : l'absence
        # VAUT portreal, et un champ ajouté partout ferait un diff de neuf
        # lignes qui ne dit rien.
        if monde == DEFAUT_MONDE:
            entree.pop("monde", None)
        else:
            entree["monde"] = monde
        nom = (opt("--nom") or [None])[0]
        if nom: entree["nom"] = nom
        note = (opt("--note") or [None])[0]
        if note: entree["note"] = note
        v = visibilite_demandee(a)
        if v is not None: entree["visible"] = v
        L["affectations"][clef] = entree
        ecrire(LIENS, L)
        print("  écrit dans etat/corps.json")
        return

    # Montrer et cacher se font APRÈS coup, et c'est le cas normal : un endroit
    # est affecté le jour où l'on en a besoin pour calculer, et montré le jour
    # où le joueur le reconnaît de ses yeux. Les deux dates n'ont aucune raison
    # d'être la même.
    if opt("--montrer") or opt("--cacher"):
        montre = bool(opt("--montrer"))
        clef = (opt("--montrer") or opt("--cacher"))[0]
        if clef not in L["affectations"]:
            sortir("  %s n'est affecté à rien — affecte-le d'abord." % clef)
        pour = (opt("--pour") or [None])[0]
        v = ([s for s in pour.split(",") if s] if (montre and pour) else montre)
        if not vraiment:
            print("  %s deviendrait %s (ajoute --vraiment)"
                  % (clef, "visible pour " + ", ".join(v) if isinstance(v, list)
                     else ("visible de tous" if v else "invisible")))
            return
        L["affectations"][clef]["visible"] = v
        ecrire(LIENS, L)
        print("  %s : %s" % (clef, "visible pour " + ", ".join(v)
                             if isinstance(v, list)
                             else ("visible de tous" if v else "invisible")))
        return

    if opt("--defaire"):
        clef = opt("--defaire")[0]
        if clef not in L["affectations"]:
            sortir("  %s n'est affecté à rien." % clef)
        if not vraiment:
            print("  %s -> bâtiment %s serait défait (ajoute --vraiment)"
                  % (clef, L["affectations"][clef].get("bat")))
            return
        L["affectations"].pop(clef)
        ecrire(LIENS, L)
        print("  %s n'a plus d'adresse physique." % clef)
        return

    if "--verifier" in a:
        maux = verifier(L)
        if not maux:
            print("  %d affectations, rien à signaler." % len(L["affectations"]))
            return
        for m in maux: print("  " + m)
        sys.exit(1)

    print(__doc__)


if __name__ == "__main__":
    main()
