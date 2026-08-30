# FLUX — ajoute des items au flux de jeu (append-only) ET tient l'horloge du monde.
# (matiere de scripts/append_flux.py, descendue au lot 2 ; la facade racine
# l'execute via runpy — voir scene/expose.pousser_flux. Les familles sans etat
# de poussee vivent dans flux_scribe.py et flux_ecrits.py ; le reste est UN
# SCRIPT au flux top-level assume — le decouper en fonctions est un vrai
# design, differe au lot-2-features.)
# Usage : python scripts/append_flux.py '<json item>' '<json item>' ...
#    ou : python scripts/append_flux.py --fichier chemin.json   (liste d'items)
# Un item {"type": "effacer"} vide l'écran (changement de scène).
#
# L'HORLOGE. Chaque item consomme du temps de jeu. Le script estampe l'item de
# l'heure a laquelle il se produit ("heure": "6h04"), puis avance
# monde.date.minute de sa duree. Le MJ n'ecrit que "duree" (en minutes) quand
# elle sort de l'ordinaire ; sinon le defaut du type s'applique. Au passage de
# 1440 minutes, le jour s'incremente. Voir docs/schema.md.
import json, io, os, re, sys, hashlib, tempfile, unicodedata

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from etat.expose import tables  # LA PORTE de etat/

# CE FICHIER EST UN SCRIPT, PAS UN MODULE. Tout son corps s'execute au chargement
# — il ecrit le flux, avance monde.json et les horloges des sieges. Un `import
# append_flux` fait donc tourner le monde par accident, en affichant son mode
# d'emploi comme si l'on s'etait trompe d'argument. On le refuse tout haut
# plutot que de laisser une horloge bouger sans que personne l'ait voulu.
if __name__ != "__main__":
    raise ImportError(
        "append_flux.py s'execute, il ne s'importe pas : l'importer pousserait "
        "le flux et avancerait l'horloge. Lancez-le en sous-processus.")

from scene.flux_scribe import (  # les chemins et les gestes d'ecriture du fil
    bibliotheque, racine, chemin, monde_p, joueurs_p, horloges_p, corps_p,
    JOURS_PAR_LUNE, LUNES_PAR_AN, teinte_du_nom, portrait,
    empreinte_du_dessin, toucher_le_livre, extrait_du_livre,
    format_heure, avancer)
from scene.flux_ecrits import (  # les avis sur ce qui s'annonce
    avis_renvois, avis_ecrits, sans_accents_simple)

# Minutes consommees par defaut, par type d'item.
# question/reponse sont hors fiction ; pensee est gratuite par regle du jeu.
DUREES = {
    "replique": 1, "geste": 1, "vous": 1, "recit": 5, "table": 2,
    "evenement": 2, "salle": 0, "breve": 0, "marque": 0, "objectif": 0,
    "effacer": 0, "question": 0, "reponse": 0, "pensee": 0,
    # Les coulisses sont hors univers : l'horloge de la fiction n'y touche pas.
    "meta": 0, "coulisses": 0,
    # L'intervention divine : on repare le fil par-dessus la fiction. Hors
    # univers de bout en bout — l'horloge n'y touche pas.
    "intervention": 0, "reparation": 0,
    # Les suites d'un « laisser faire » : une main tendue au joueur, pas un
    # geste dans la fiction. Personne ne l'entend, l'horloge n'y touche pas.
    "suites": 0,
    # L'atelier de chanson : on compose SUR la partie, jamais dedans. Hors
    # univers comme les coulisses, et sans une minute de fiction.
    "composer": 0, "chanson": 0,
}

# --- les fronts de temps, un par joueur -----------------------------------
# A deux joueurs, une seule horloge ne peut pas tenir : une tranche poussee a
# l'une ferait sonner minuit chez l'autre, qui n'a rien vecu de cette heure-la.
# Chaque joueur porte donc son propre FRONT (etat/horloges.json, fichier
# technique hors docs/schema.md), et `monde.date` devient le MINIMUM des fronts
# — la date jusqu'a laquelle le monde est acquis pour tout le monde. C'est cette
# date-la, et pas une autre, que le tick doit voir : il travaille en jours sur ce
# qui est commun, la scene travaille en minutes sur ce qui est prive.
BARRIERE_MINUTES = 2880  # un joueur ne devance jamais l'autre de plus de deux jours


def minute_absolue(d):
    """Une date en minutes depuis l'an zero — 12 lunes de 30 jours."""
    return ((((d["annee"] * LUNES_PAR_AN + (d["lune"] - 1)) * JOURS_PAR_LUNE)
             + (d["jour"] - 1)) * 1440) + d.get("minute", 0)


def dit_ecart(minutes):
    """« 1 j 4 h 20 » — un ecart doit se lire, pas se calculer de tete."""
    j, r = divmod(int(minutes), 1440)
    h, m = divmod(r, 60)
    return " ".join(([str(j) + " j"] if j else []) + ([str(h) + " h"] if h else [])
                    + ([str(m) + " min"] if m or not (j or h) else []))


def roster():
    """Les sieges de la partie. Absent ou vide = partie seule, rien ne change.

    Un siege de REGIE (Corneille) n'en est pas un : il ne tient aucun front, il
    n'est nomme dans aucune audience, et rien ne s'ecrit pour lui. Il lit le
    flux entier depuis le serveur, `pour` ou pas — l'y nommer lui ouvrirait un
    horloge et le ferait compter comme une oreille de plus dans la salle.
    """
    l = tables.lire(joueurs_p, [])
    if not (isinstance(l, list) and l):
        return []
    return [j for j in l if isinstance(j, dict) and not j.get("regie")]


def lire_horloges(defaut):
    """Les fronts connus, completes par `defaut` pour qui n'a jamais joue.

    Un joueur sans entree est repute au front du monde : il n'a rien vecu de
    plus que le commun, ce qui est exactement vrai.
    """
    h = tables.lire(horloges_p, {})
    if not isinstance(h, dict):
        h = {}
    for j in roster():
        pid = j["personnage_id"]
        h.setdefault(pid, dict(defaut))
        # Le tick, lui, travaille en JOURS sur `monde.date` : quand il fait
        # avancer le monde commun, un front reste derriere. Il le rattrape ici,
        # sans quoi la scene rejouerait une journee que le monde a deja passee.
        if minute_absolue(h[pid]) < minute_absolue(defaut):
            h[pid] = dict(defaut)
    return h


def audience_courante():
    """A qui appartient la scene ouverte ? On le LIT dans le flux lui-meme.

    Pas de fichier d'accompagnement : le dernier `effacer` ecrit porte le `pour`
    de la scene en cours, et c'est vrai pour toujours, meme si l'on relit le
    fichier dans dix ans. Un flux qui se decrit tout seul ne peut pas desynchroniser.
    """
    if not os.path.exists(chemin):
        return None
    dernier = None
    with io.open(chemin, encoding="utf-8") as f:
        for ligne in f:
            if not ligne.strip():
                continue
            try:
                it = json.loads(ligne)
            except ValueError:
                continue
            if it.get("type") == "effacer":
                dernier = it.get("pour")
    return dernier


# --- la presence : ou se tient chacun, une seule fois ---------------------
# `presents`, `entrent`, `sortent` sont des items de FLUX, donc cloisonnes par
# `pour`. Or se tenir dans une piece est un fait du MONDE, pas une mise en scene
# privee : le mestre entre chez l'une, il quitte donc la salle de l'autre. Tant
# que le plan du chateau deduisait la piece du flux, chaque joueur en tenait sa
# propre version — et un PNJ partage se retrouvait dans deux pieces a la fois,
# une par ecran, sans qu'aucun item ne puisse l'en faire sortir des deux (un
# `sortent` porte forcement une audience, donc une seule des deux salles).
#
# `etat/presence.json` (technique, hors docs/schema.md, comme horloges.json) tient
# donc UNE entree par personnage : {salle, lieu, date}. Poser quelqu'un quelque
# part l'enleve d'office d'ailleurs, par construction du dictionnaire — c'est tout
# le correctif. Le MJ n'a rien de nouveau a ecrire : le script le derive des
# items qu'il pousse deja.
presence_p = os.path.join(racine, "etat", "presence.json")


def lire_presence():
    t = tables.lire(presence_p, {})
    p = t.get("presence") if isinstance(t, dict) else None
    return p if isinstance(p, dict) else {}


# La position ne se STOCKE pas, elle se CALCULE — `scripts/presence.py`. Ce
# fichier-ci ne tient que les EXCEPTIONS : ce qu'une scene a constate, et qui
# vaut le temps que ca vaut. Le reste du chateau suit sa journee (routines.json)
# et marche vraiment d'une salle a l'autre (chemins.json).
#
# C'est ICI qu'on resout, et c'est justifie : `monde.date` n'avance que par ce
# script. Entre deux poussees, l'horloge ne bouge pas, donc l'instantane qu'on
# ecrit reste vrai — le serveur peut le lire tel quel sans refaire le calcul en
# JS. Un seul moteur de position, en Python.
try:
    from temps.expose import presence as calcul_presence
except Exception:
    calcul_presence = None


def meme_piece(a, b):
    """Deux pieces sont la meme si leur `salle` l'est — a defaut, leur `lieu`.

    Le MJ ne pose pas toujours `salle` (le plan la devine de l'en-tete de lieu,
    cote navigateur). On ne duplique pas cette devinette ici : on compare ce
    qu'on a, du plus precis au moins precis.
    """
    if a.get("salle") and b.get("salle"):
        return a["salle"] == b["salle"]
    return (a.get("lieu") or "") == (b.get("lieu") or "")


args = sys.argv[1:]

# --- l'audience -----------------------------------------------------------
# A deux joueurs separes, presque TOUT devient prive : il suffit d'oublier
# `pour` une seule fois pour fuiter une scene entiere a l'autre camp. On ne
# s'en remet donc pas a la vigilance — l'audience est COLLANTE. Un `effacer`
# ouvre une scene qui appartient a quelqu'un, et tous les items qui suivent en
# heritent jusqu'au prochain `effacer`.
#   --pour daemon   -> ces items (et la scene, s'ils l'ouvrent) sont a Daemon
#   --pour tous     -> scene commune : les deux joueurs la voient
#   (rien)          -> on herite de la scene en cours
#   --messe-basse a[,b]  -> ces items ne sont entendus QUE de ceux-la
pour = None
explicite = False
if "--pour" in args:
    i = args.index("--pour")
    pour = args[i + 1]
    explicite = True
    args = args[:i] + args[i + 2:]
    if pour in ("tous", "commun", "-"):
        # UNE SCENE COMMUNE SE NOMME, ELLE NE SE TAIT PAS. Ecrire le commun par
        # ABSENCE de `pour` etait la faille : un item sans audience retombait
        # dans le cas « rien n'a ete declare », que le serveur servait a tout le
        # monde — y compris a un siege qui n'etait pas dans la salle, et pour
        # toujours, puisqu'une audience commune ne se referme jamais d'elle-meme.
        # On enumere donc les oreilles occupees. « Commun » devient un tableau
        # comme un autre, et plus un trou dans lequel tout tombe.
        assis = [j.get("personnage_id") for j in roster()
                 if j.get("occupe") and j.get("personnage_id")]
        pour = sorted(assis) if len(assis) > 1 else None

# LA MESSE BASSE. Optionnelle, et c'est tout l'interet : par defaut on parle a
# la piece (voir plus bas — l'audience se deduit de `presence.json`). Chuchoter
# est le cas rare, donc le cas qu'on DECLARE. Un ou plusieurs auditeurs : ce que
# deux personnes se disent a l'ecart, dans une salle qui en compte six, n'est ni
# public ni prive a une seule oreille.
messe_basse = None
if "--messe-basse" in args:
    i = args.index("--messe-basse")
    messe_basse = [x for x in args[i + 1].split(",") if x.strip()]
    args = args[:i] + args[i + 2:]
    # Chuchoter EST une declaration d'audience : sans ce drapeau ici, la garde
    # anti-heritage ci-dessous refuserait la poussee faute de `--pour`.
    explicite = True
    if not messe_basse:
        sys.stderr.write("REFUS : --messe-basse sans personne pour l'entendre.\n")
        raise SystemExit(2)

# LE MUR VOULU. `--tunnel` desarme le garde-fou du meme nom (voir tunnel.py) ;
# il ne dit rien de l'audience ni du contenu, donc il sort des arguments ici,
# avant qu'on ne cherche a lire du JSON dedans. Sans ce retrait, le seul moyen
# documente de pousser une longue piece — un registre relu tout haut, une lettre
# lue en entier — plantait sur `json.loads("--tunnel")`.
args = [a for a in args if a != "--tunnel"]

items = []
if args and args[0] == "--fichier":
    items = json.load(io.open(args[1], encoding="utf-8"))
else:
    items = [json.loads(a) for a in args]

if not explicite:
    pour = audience_courante()
    # A DEUX MJ, l'heritage silencieux est un piege. « La scene en cours » se
    # lit dans un flux UNIQUE, alors que deux scenes se jouent en meme temps :
    # si l'autre MJ a ouvert une scene privee en dernier, votre tranche part
    # chez SON joueur et disparait de l'ecran du votre — sans une erreur, sans
    # une ligne perdue, juste un fil qui ne recoit rien. On refuse donc plutot
    # que d'heriter d'une audience qui n'est pas la sienne. A un seul joueur au
    # roster (ou aucun), l'heritage reste commode et sans danger.
    if pour and len([j for j in roster()]) > 1:
        sys.stderr.write(
            "REFUS : la derniere scene ouverte appartient a « %s », et vous n'avez\n"
            "pas dit --pour. A deux joueurs, l'audience ne s'herite pas : elle se\n"
            "declare, sinon votre tranche part dans le fil de l'autre.\n"
            "  --pour %s   pour continuer CETTE scene\n"
            "  --pour <votre joueur>   pour la votre\n"
            "  --pour tous             pour une scene commune\n"
            "Rien n'a ete ecrit.\n" % (pour, pour))
        raise SystemExit(2)

monde = tables.lire(monde_p)
monde["date"].setdefault("minute", 0)

# Quelle horloge cette poussee fait-elle tourner ? Celle du joueur nomme s'il
# est au roster ; celle du monde sinon (partie seule, ou scene commune : ce que
# tout le monde voit avance tout le monde).
sieges = [j["personnage_id"] for j in roster()]


def sieges_de_regie():
    """Les sieges qui REGARDENT — Corneille. `roster()` les a deja ecartes.

    Pousser vers un siege de regie ne doit RIEN couter au monde : la regie est
    hors fiction de bout en bout, personne dans aucune salle ne l'entend, et
    une seule minute prise sur l'horloge parce qu'un recit lui a ete adresse
    serait du temps vole aux joueurs. On force donc les durees a zero et l'on
    n'ecrit ni `monde.json` ni `horloges.json` pour ces poussees-la.
    """
    l = tables.lire(joueurs_p, [])
    if not isinstance(l, list):
        return set()
    return {j.get("personnage_id") for j in l
            if isinstance(j, dict) and j.get("regie") and j.get("personnage_id")}


REGIES = sieges_de_regie()
en_regie = isinstance(pour, str) and pour in REGIES

# --- l'audience se DECLARE, jamais ne se devine ----------------------------
# On a essaye de la DEDUIRE de `presence.json` : deux sieges situes dans la meme
# piece s'entendaient d'office, et un `--pour <siege>` etait silencieusement
# elargi a ses voisins. C'etait joli sur le papier et faux a l'ecran : une
# presence perimee, une salle mal nommee, un lieu commun a deux etages, et la
# tranche d'une session tombait chez le joueur d'en face. Le symptome est
# toujours le meme — des messages qui s'affichent partout — et il ne se voit
# jamais du cote qui l'a cause.
#
# Donc : `--pour X` veut dire X, et rien d'autre. Une scene commune se dit
# `--pour tous` ; une piece partagee se dit `--messe-basse a,b`. Ce que le MJ
# n'a pas declare ne s'entend pas.
#
# CE QUI N'EST PAS DANS LA FICTION N'EST PAS DANS LA PIECE. Une question, une
# reponse, une pensee, une remarque de coulisses ne se disent a personne : elles
# n'ont pas lieu dans la salle et ne coutent pas une minute. Elles restent
# privees au siege vise meme quand la scene, elle, est commune.
HORS_FICTION = {"question", "reponse", "pensee", "meta", "coulisses",
                "composer", "chanson", "intervention", "reparation"}
pour_hors_fiction = pour if pour in sieges else None

if messe_basse:
    pour = messe_basse if len(messe_basse) > 1 else messe_basse[0]
    explicite = True

mien = pour if pour in sieges else None
horloges = lire_horloges(monde["date"]) if sieges else {}
date = dict(horloges[mien]) if mien else monde["date"]
date.setdefault("minute", 0)
depart = (date["jour"], date["minute"])


def simuler(depart_date):
    """Ou l'horloge finirait si l'on poussait — sans rien ecrire.

    La barriere doit se juger AVANT la premiere ligne ecrite : un flux est
    append-only, on ne reprend pas une tranche partie de travers.
    """
    d = dict(depart_date)
    for it in items:
        if isinstance(it.get("date"), dict):
            for k in ("annee", "lune", "jour", "minute"):
                if k in it["date"]:
                    d[k] = it["date"][k]
        avancer(d, 0 if en_regie else it.get("duree", DUREES.get(it.get("type"), 0)))
    return d


def reclamer_un_run(retarde, demandeur, ecart):
    """La barriere ne bloque plus : elle DEMANDE a l'autre d'avancer.

    Un refus sec laissait le joueur en avance devant un mur, avec pour seule
    issue d'aller reveiller l'autre session a la main — ou de basculer de siege.
    Or ce qu'il faut est simple et connu : que le retardataire joue sa journee.
    On depose donc un ordre de « laisser faire » dans SON inbox : son guetteur
    sonne, son MJ le joue, le monde rattrape, et la poussee refusee passe au
    coup d'apres sans que personne ait eu a comprendre la mecanique.

    Un seul ordre a la fois : si l'on en a deja depose un qui n'a pas ete
    traite, on ne l'empile pas — le MJ d'en face n'a pas besoin de dix.
    """
    dossier = os.path.join(racine, "etat", "inbox", retarde)
    try:
        os.makedirs(dossier, exist_ok=True)
        for f in os.listdir(dossier):
            if f.startswith("barriere-"):
                return ("  Un ordre de rattrapage attend deja dans l'inbox de %s."
                        % retarde)
        tables.ecrire(os.path.join(dossier, "barriere-%s.json" % retarde), {
            "type": "libre", "mode": "run",
            "texte": ("Rattrapage : %s a %s d'avance et ne peut plus avancer. "
                      "Joue ta journee jusqu'a rejoindre le front commun."
                      % (demandeur, dit_ecart(ecart))),
            "joueur_id": retarde, "barriere": True,
        }, indent=None)
    except OSError as e:
        return "  (impossible de prevenir %s : %s)" % (retarde, e)
    return ("  Un ordre de « laisser faire » vient d'etre depose dans l'inbox de "
            "%s : son MJ va jouer sa journee, et cette poussee passera ensuite."
            % retarde)


# --- la barriere de deux jours --------------------------------------------
# Sans elle, une joueuse apprendrait une nouvelle avant qu'elle ne soit arrivee
# a l'autre, et le brouillard s'effondrerait par le temps au lieu de
# l'information. On refuse, et l'on n'ecrit rien du tout.
if mien and len(sieges) > 1:
    autres = min(minute_absolue(horloges[s]) for s in sieges if s != mien)
    for quand, quoi in ((minute_absolue(date), "est deja"),
                        (minute_absolue(simuler(date)), "passerait")):
        if quand - autres > BARRIERE_MINUTES:
            retarde = min((s for s in sieges if s != mien),
                          key=lambda s: minute_absolue(horloges[s]))
            demande = reclamer_un_run(retarde, mien, quand - autres)
            sys.stderr.write(
                "REFUS : le front de %s %s en avance de %s sur le plus retarde des "
                "autres -- le monde n'est pas encore arrive jusqu'a eux.\n"
                "Rien n'a ete ecrit (ni flux, ni horloges).\n"
                % (mien, quoi, dit_ecart(quand - autres)))
            sys.stderr.write(demande + "\n")
            raise SystemExit(2)

# La meme barriere, pour la scene COMMUNE. Elle n'a pas de front a elle : elle
# part du minimum et TIRE les fronts derriere elle (voir plus bas). C'est par la
# que le temps peut se perdre en silence : une scene commune portant une date
# explicite fait sauter le front du retardataire jusque-la, et les minutes qu'il
# n'a pas vecues disparaissent sans une ligne. Rien ne le disait, parce que la
# barriere ne se jugeait que sur une poussee privee.
# `en_regie` en est exclu : une poussee vers la regie n'est pas une scene
# commune, c'est une lecture hors fiction. Elle ne tire aucun front — les
# durees y valent zero et rien n'est reecrit — et l'avertir de son ecart au
# front des joueurs n'aurait aucun sens.
if not mien and not en_regie and sieges:
    fin = minute_absolue(simuler(date))
    for s in sieges:
        saut = fin - minute_absolue(horloges[s])
        if saut > BARRIERE_MINUTES:
            sys.stderr.write(
                "REFUS : cette scene commune tirerait le front de %s de %s d'un "
                "coup -- des minutes qu'il n'a pas vecues.\n"
                "Rien n'a ete ecrit (ni flux, ni horloges). Jouez-lui ce temps-la, "
                "ou posez une date plus proche.\n" % (s, dit_ecart(saut)))
            raise SystemExit(2)
    # L'autre facette, qui ne justifie pas un refus : une scene commune estampee
    # dans le passe d'un joueur deja plus avance. C'est le cas ordinaire (son
    # front porte quelques minutes de scene privee), mais au-dela d'une heure
    # c'est le signe qu'on lui pousse du vecu par-dessous. On le dit, sans bloquer.
    for s in sieges:
        retard = minute_absolue(horloges[s]) - minute_absolue(date)
        if retard > 60:
            sys.stderr.write(
                "AVIS : scene commune estampee %s AVANT le front de %s -- il la "
                "verra datee de son passe.\n" % (dit_ecart(retard), s))

# La piece courante de la tranche. Un `effacer` la remet a l'inconnu ; un item
# porteur de `lieu`/`salle` la nomme ; a defaut, une scene privee se tient la ou
# se tient SON joueur — c'est ce qui permet a un `entrent` nu, au milieu de
# quarante repliques sans en-tete, de savoir dans quelle piece il fait entrer.
presence = lire_presence()
suivi = {"touchee": False}
piece = None
if mien and mien in presence:
    piece = {"salle": presence[mien].get("salle"), "lieu": presence[mien].get("lieu")}


# LE GARDE-FOU : personne ne parait dans une salle sans avoir traverse celles
# d'entre. On n'INTERDIT rien — l'item pousse fait foi, c'est la scene qui a
# raison contre le calcul — mais on le DIT, parce qu'un homme qui saute d'un
# bout du chateau a l'autre en deux minutes est presque toujours un oubli du MJ
# et jamais une intention.
_chateau = None
if calcul_presence:
    try:
        _chateau = calcul_presence.Chateau(calcul_presence._lire("chemins.json", {}))
    except Exception:
        _chateau = None


# UN HOMME, UNE FICHE DE PRESENCE. `avis_acteurs_inconnus()` disait deja sur la
# sortie d'erreur qu'un id neuf ressemblait a quelqu'un du registre — mais un
# avis n'arrete rien, et la presence, elle, s'ecrivait quand meme. Resultat :
# « jacaerys-velaryon » a vecu six jours a cote de « jacaerys », chacun avec sa
# salle, et le plan du chateau montrait le prince a DEUX endroits a la fois.
#
# On replie donc l'id sur celui du registre, et a une seule condition : que l'id
# pousse n'ait PAS de fiche a lui. Deux ids qui existent tous les deux sont deux
# hommes — « nesse » et « nesse-la-mere » sont bien deux personnes, et les
# marier serait une faute pire que le doublon. Le repli suit le prefixe et
# jamais le milieu d'un mot, comme `rapprocher()` dans criticite.py.
_registre_ids = None


def _ids_connus():
    global _registre_ids
    if _registre_ids is None:
        try:
            with io.open(os.path.join(racine, "etat", "personnages.json"),
                         encoding="utf-8") as f:
                g = json.load(f)
            g = g if isinstance(g, list) else g.get("personnages", [])
            _registre_ids = {p.get("id") for p in g if p.get("id")}
        except Exception:
            _registre_ids = set()
    return _registre_ids


def canonique(pid):
    connus = _ids_connus()
    if not pid or pid in connus:
        return pid
    for c in connus:
        if pid.startswith(c + "-") or c.startswith(pid + "-"):
            sys.stderr.write(
                "PRESENCE : « %s » n'a pas de fiche ; sa presence est ecrite "
                "sous « %s », qui en a une.\n"
                "  Si ce sont deux hommes differents, donnez une fiche au second.\n"
                % (pid, c))
            return c
    return pid


def avertir_saut(pid, piece, quand):
    if not (_chateau and calcul_presence and piece.get("salle")):
        return
    avant = presence.get(pid)
    if not (avant and avant.get("salle") and avant.get("date")):
        return
    if meme_piece(avant, piece):
        return
    marche = _chateau.duree(avant["salle"], piece["salle"])
    ecoule = calcul_presence.absolu(quand) - calcul_presence.absolu(avant["date"])
    if marche > max(ecoule, 0):
        sys.stderr.write(
            "AVIS : %s parait a %s alors qu'on l'a laisse a %s il y a %d min --"
            " il y a %d min de marche. Il n'a pas eu le temps d'y aller.\n"
            % (pid, piece["salle"], avant["salle"], max(ecoule, 0), marche))


vus = set()          # les salles ou le joueur s'est tenu pendant cette tranche


def reveler(salles, siege):
    """Les endroits traverses passent en clair sur la ville, pour ce siege-la.

    L'affectation (`scripts/affecter.py`) donne des metres a un endroit ; sa
    clef `visible` dit qui a le droit d'en voir le nom sur la carte. Les deux
    sont separes parce que le MJ affecte souvent AVANT que le joueur y aille —
    le chantier du bout avait ses metres bien avant qu'on y mette les pieds.
    Mais une fois qu'il y a mis les pieds, personne ne devrait avoir a le
    declarer a la main : y avoir ete, c'est le connaitre.

    On n'ecrit que si ca change, et on relit le fichier a l'instant : a deux MJ,
    `etat/corps.json` a deux plumes.
    """
    salles = {s for s in salles if s}
    if not (salles and siege) or not os.path.exists(corps_p):
        return
    try:
        C = json.load(io.open(corps_p, encoding="utf-8"))
    except (ValueError, OSError):
        return
    A = C.get("affectations") or {}
    change = False
    for s in salles:
        # `salle:` d'abord, `lieu:` en repli : un endroit que le plan ne connait
        # pas (une taverne, un chantier) est affecte en `lieu`, et il serait
        # absurde qu'y avoir passe la nuit ne le revele pas.
        e = A.get("salle:" + s) or A.get("lieu:" + s)
        if not e or e.get("visible") is True:
            continue
        qui = e.get("visible")
        qui = list(qui) if isinstance(qui, list) else []
        if siege in qui:
            continue
        qui.append(siege)
        e["visible"] = qui
        change = True
    if change:
        tables.ecrire(corps_p, C)


def _affectations():
    return tables.lire(corps_p, {}).get("affectations") or {}


def connue_quelque_part(salle):
    """Cette salle a-t-elle une adresse, ou au moins un plan qui la connaisse ?"""
    A = _affectations()
    if ("salle:" + salle) in A or ("lieu:" + salle) in A:
        return True
    try:
        src = io.open(os.path.join(racine, "ecrans", "modules", "plans.js"),
                      encoding="utf-8").read()
        return ('id: "%s"' % salle) in src
    except OSError:
        return True          # pas de plan lisible : on ne reproche rien


def conseiller_salle(nom_lieu, depuis, inconnue=None):
    """Dire ce qui manque, et donner de quoi le reparer en une ligne.

    On ne devine pas a la place du MJ : on lui rend les endroits DEJA affectes
    les plus proches de la ou il etait, et la commande pour en creer un neuf.
    Sans ca, l'oubli ne se voit qu'a l'ecran, trois scenes plus tard, sous la
    forme d'un joueur qui a l'air d'etre chez le roi.
    """
    A = _affectations()
    ancre = (A.get("salle:" + (depuis or "")) or A.get("lieu:" + (depuis or ""))
             or {})
    ici = ancre.get("xyz")
    # Les affectations vivent dans plusieurs mondes (Port-Real, Peyredragon) et
    # chacun a son repere : comparer leurs coordonnees donne des voisins
    # absurdes — la table peinte de Peyredragon a cent metres de la porte de
    # Fer. On ne propose donc que le monde ou l'on se tient.
    mien_monde = ancre.get("monde") or "portreal"
    lignes = []
    if ici:
        proches = []
        for clef, e in A.items():
            g = clef.split(":")[0]
            if g not in ("salle", "lieu") or not e.get("xyz"):
                continue
            if (e.get("monde") or "portreal") != mien_monde:
                continue
            d = ((e["xyz"][0] - ici[0]) ** 2 + (e["xyz"][1] - ici[1]) ** 2) ** 0.5
            proches.append((d, clef, e.get("nom") or clef.split(":")[1]))
        proches.sort()
        for d, clef, nom in proches[:5]:
            lignes.append("    %-34s %5d m   %s" % (clef, round(d), nom))
    quoi = ("la salle « %s » n'a ni adresse ni entree dans plans.js" % inconnue
            if inconnue else
            "un en-tete de lieu (« %s ») sans salle -- la piece precedente est "
            "gardee" % (nom_lieu or "?"))
    sys.stderr.write("AVIS : %s\n" % quoi)
    if lignes:
        sys.stderr.write("  Endroits deja affectes, autour de la:\n"
                         + "\n".join(lignes) + "\n")
    sys.stderr.write(
        "  Pour en creer un :\n"
        "    python scripts/affecter.py --chercher --usage taverne --pres-de x,y\n"
        "    python scripts/affecter.py --affecter lieu:<id> <batiment> "
        "--nom \"<nom>\" --visible-pour <siege> --vraiment\n")


def suivre_presence(it, quand):
    """Derive la presence des items pousses. Rien a ecrire de plus pour le MJ."""
    global piece
    if it.get("type") == "effacer":
        piece = None
        return
    if it.get("salle") or it.get("lieu"):
        # `salle: null` N'EST PAS « pas de salle », c'est un EFFACEMENT. Pousser
        # un recit d'exterieur avec `"salle": null` sortait le joueur de toute
        # piece : sa presence devenait inconnue, et le decor le renvoyait a la
        # place forte du lieu — au Donjon Rouge, alors qu'il descendait une rue.
        # On ne l'efface donc plus, on le DIT, et l'on propose ce qu'il aurait
        # fallu ecrire.
        neuve = it.get("salle")
        if neuve is None and it.get("lieu") and piece and piece.get("salle"):
            conseiller_salle(it.get("lieu"), piece.get("salle"))
            piece = {"salle": piece.get("salle"), "lieu": it.get("lieu")}
        else:
            if neuve and not connue_quelque_part(neuve):
                conseiller_salle(it.get("lieu") or neuve, (piece or {}).get("salle"),
                                 inconnue=neuve)
            piece = {"salle": neuve, "lieu": it.get("lieu")}
    if piece is None:
        return

    def poser(x):
        pid = x.get("id") if isinstance(x, dict) else x
        if not pid:
            return
        pid = canonique(pid)
        avertir_saut(pid, piece, quand)
        presence[pid] = {"salle": piece.get("salle"), "lieu": piece.get("lieu"),
                         "date": dict(quand)}
        suivi["touchee"] = True

    def retirer(pid):
        # On ne chasse quelqu'un que de la piece ou l'on est : un `sortent` en
        # retard ne doit pas l'arracher a la salle ou il vient d'entrer.
        pid = canonique(pid)
        if pid in presence and meme_piece(presence[pid], piece):
            del presence[pid]
            suivi["touchee"] = True

    if it.get("type") == "salle" and it.get("presents"):
        nommes = [canonique(p.get("id") if isinstance(p, dict) else p)
                  for p in it["presents"]]
        # Une salle DECLAREE fait autorite sur ses occupants : qui y etait sans
        # y etre nomme n'y est plus. C'est le `vider()` du navigateur, cote etat.
        for pid in list(presence):
            if pid not in nommes and meme_piece(presence[pid], piece):
                del presence[pid]
                suivi["touchee"] = True
        for p in it["presents"]:
            poser(p)
    # Parler ou faire, c'est etre la — la meme regle que la galerie applique a
    # l'ecran. Sans elle, la presence ne connaitrait que les gens explicitement
    # mis en scene, et tous ceux qui n'existent que par leurs repliques
    # resteraient hors du fichier : ni situes, ni situables.
    for cle in ("locuteur_id", "acteur_id"):
        if it.get(cle):
            poser(it[cle])
    # LE JOUEUR EST QUELQU'UN. Il n'a ni `locuteur_id` ni `acteur_id` — ses
    # items sont des `vous`, et les recits qui le suivent n'ont d'acteur du
    # tout —, si bien qu'il etait le seul de la salle a ne jamais bouger : la
    # piece changeait autour de lui et sa presence restait celle de la veille.
    # Un en-tete de lieu le deplace donc comme il deplace n'importe qui.
    #
    # Hors fiction excepte : penser, demander, parler en coulisses ne fait pas
    # entrer dans une piece. Le mode « laisser faire » (`run`) non plus — c'est
    # le pas de cote du joueur, pas un geste du personnage ; ce sont les items
    # `vous` qu'il produit ensuite qui, eux, le posent.
    if mien and it.get("type") not in HORS_FICTION and it.get("type") != "run":
        poser(mien)
        # Y ETRE, C'EST LE CONNAITRE. Un endroit ou le joueur vient de se tenir
        # cesse d'etre un point sur une carte qu'il ne verrait pas : son nom
        # parait sur la ville, pour lui seul. C'est du brouillard qui se leve
        # tout seul, au bon moment, sans que le MJ ait a y penser — et il ne se
        # leve que la ou il a marche.
        vus.add(piece.get("salle"))
    for p in (it.get("entrent") or []):
        poser(p)
    for x in (it.get("sortent") or []):
        retirer(x.get("id") if isinstance(x, dict) else x)


# QUI EST CET HOMME ? — l'avis des acteurs sans fiche.
#
# Un id neuf dans un item, c'est presque toujours l'une de deux choses : une
# figure de passage qu'on ne reverra pas (tres bien), ou QUELQU'UN QUI EXISTAIT
# DEJA, sous un autre id, et qu'on vient de dedoubler sans le savoir. Le 25e de
# la troisieme lune, « wat-duhamel » a ete pousse dans les caves alors que Wat du
# hameau au gue etait aux geoles depuis huit jours, dans les annales, avec un
# frere mort — et trois ecritures d'etat ont ete bati dessus avant qu'on s'en
# apercoive.
#
# Le script ne refuse rien : il NOMME les homonymes possibles, une fois, au
# moment ou l'on pousse. C'est tout ce qu'il fallait.
def avis_acteurs_inconnus(items):
    try:
        with io.open(os.path.join(racine, "etat", "personnages.json"),
                     encoding="utf-8") as f:
            gens = json.load(f)
    except Exception:
        return
    gens = gens if isinstance(gens, list) else gens.get("personnages", [])
    connus, par_mot = set(), {}
    for p in gens:
        pid = p.get("id")
        if not pid:
            continue
        connus.add(pid)
        for mot in re.split(r"[^a-zA-Z0-9]+", sans_accents_simple(
                (p.get("nom") or "") + " " + pid)):
            if len(mot) >= 3:
                par_mot.setdefault(mot, []).append(
                    "%s (%s)" % (p.get("nom") or pid, pid))

    vus_ici, signales = [], set()
    for it in items:
        for cle in ("locuteur_id", "acteur_id"):
            if it.get(cle):
                vus_ici.append(it[cle])
        for clef in ("presents", "entrent"):
            for p in (it.get(clef) or []):
                pid = p.get("id") if isinstance(p, dict) else p
                if pid:
                    vus_ici.append(pid)

    for pid in vus_ici:
        if not pid or pid in connus or pid in signales or pid == "vous":
            continue
        signales.add(pid)
        proches = []
        for mot in re.split(r"[^a-zA-Z0-9]+", sans_accents_simple(pid)):
            if len(mot) >= 3:
                for cand in par_mot.get(mot, []):
                    if cand not in proches:
                        proches.append(cand)
        sys.stderr.write(
            "AVIS : « %s » n'a pas de fiche dans personnages.json.\n" % pid)
        if proches:
            sys.stderr.write(
                "  Deja au monde sous un nom proche : %s\n"
                "  Verifiez que ce n'est pas le meme homme avant d'ecrire l'etat.\n"
                % ", ".join(proches[:4]))
        else:
            sys.stderr.write(
                "  Aucun homonyme connu. Figure de passage : rien a faire.\n"
                "  S'il doit durer, creez sa fiche (et lisez d'abord :"
                " python scripts/dossier.py --sur %s).\n"
                % re.split(r"[^a-zA-Z0-9]+", pid)[0])


try:
    avis_acteurs_inconnus(items)
except Exception:
    pass  # un avis ne doit jamais empecher une poussee

try:
    avis_renvois(items)
except Exception:
    pass  # idem : on nomme ce qui cloche, on ne bloque rien

try:
    avis_ecrits(items)
except Exception:
    pass  # idem : ce qui est annonce se verifie, mais rien ne bloque la poussee

try:
    from scene.expose import tunnel
    tunnel.avis(items)
except Exception:
    pass  # un avis ne doit jamais empecher une poussee

try:
    import carte_muette
    carte_muette.avis(items)
except SystemExit:
    raise          # le refus, quand il sera pose, doit passer
except Exception:
    pass  # idem : un avis ne bloque pas


with io.open(chemin, "a", encoding="utf-8") as f:
    for it in items:
        # raccourci : {"presents": ["daemon", ...]} avec ids simples → inline les SVG
        #
        # `entrent` en a AUTANT besoin que `presents` : CLAUDE.md en fait le geste
        # normal pour faire entrer quelqu'un en cours de scene, sans repousser une
        # salle entiere. Sans portrait inline, l'arrivant entre dans l'etat mais
        # pas dans la galerie — il est la sans visage, ce qui ressemble a un bug
        # de scene alors que c'est un oubli d'inlining.
        for clef in ("presents", "entrent"):
            gens = it.get(clef)
            if gens and isinstance(gens[0], dict) and "portrait_svg" not in gens[0]:
                for p in gens:
                    p["portrait_svg"] = portrait(p["id"], p.get("nom"))
        # `montre: {livre: "…"}` — quelqu'un tend un volume ouvert sur une page.
        # On y colle la citation maintenant : voir extrait_du_livre.
        if isinstance(it.get("montre"), dict) and it["montre"].get("livre"):
            extrait_du_livre(it["montre"])
            # Un volume qu'on vient de tendre remonte sur le dessus de la pile.
            toucher_le_livre(it["montre"]["livre"], date)
        # Un item peut porter sa propre date (saut de temps narre) : on la suit.
        if isinstance(it.get("date"), dict):
            for k in ("annee", "lune", "jour"):
                if k in it["date"]:
                    date[k] = it["date"][k]
            if "minute" in it["date"]:
                date["minute"] = it["date"]["minute"]
        # UN `pour` D'ITEM NE COMPREND PAS LES MOTS-CLES. « tous », « commun »,
        # « - » sont des mots de la LIGNE DE COMMANDE : ecrits dans l'item, ils
        # y restent tels quels, et le serveur cherche alors un siege qui
        # s'appelle « tous ». Il n'en trouve aucun — l'item n'est servi a
        # personne, sur aucun ecran, sans une erreur nulle part. On les traduit
        # ici, la ou ils veulent dire quelque chose : pas d'audience du tout.
        if it.get("pour") in ("tous", "commun", "-"):
            # Meme regle qu'en ligne de commande : on NOMME les oreilles. Le mot
            # « tous » ecrit dans un item ne veut rien dire pour le serveur ; le
            # supprimer purement et simplement rendait l'item public, ce qui est
            # pire — c'est la faille qu'on ferme.
            assis = sorted(j.get("personnage_id") for j in roster()
                           if j.get("occupe") and j.get("personnage_id"))
            if len(assis) > 1:
                it["pour"] = assis
            else:
                del it["pour"]
                if it.get("type") == "effacer":
                    it["commun"] = True
        # L'audience s'estampille a l'ecriture : elle est portee par chaque
        # item, jamais recalculee a la lecture. Un `pour` deja pose sur l'item
        # l'emporte — c'est l'apartee dans une scene commune.
        if "pour" not in it and pour:
            it["pour"] = pour
        # Le hors-fiction reste a celui qui l'a demande, meme si la piece est
        # commune : la deduction par la presence ne doit pas rendre publique une
        # reponse de MJ ou une pensee. Elle ne se dit a personne.
        if "pour" not in it and it.get("type") in HORS_FICTION and pour_hors_fiction:
            it["pour"] = pour_hors_fiction
        # LE MARQUEUR DU COMMUN. Un `pour` absent ne veut PAS dire « pour tout
        # le monde » : il veut dire « rien n'a ete declare », et c'est le cas de
        # tout le flux anterieur au passage a deux joueurs. Le serveur a besoin
        # d'un signe POSITIF pour reconnaitre une scene commune, sans quoi il
        # confond une salle partagee avec l'ancien monde et y fait fuiter la
        # parole de l'un chez l'autre. `--pour tous` le pose ici, sur l'effacer
        # qui ouvre la scene — le seul item que le serveur relit pour trancher.
        if explicite and pour is None and it.get("type") == "effacer":
            it["commun"] = True
        it["heure"] = format_heure(date["minute"])
        # la date portee par l'item reflete l'horloge, pour le bandeau et la reprise
        it["date"] = {"annee": date["annee"], "lune": date["lune"],
                      "jour": date["jour"], "minute": date["minute"]}
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
        suivre_presence(it, date)
        # La regie ne coute pas une minute : voir sieges_de_regie().
        avancer(date, 0 if en_regie else it.get("duree", DUREES.get(it.get("type"), 0)))

# On ecrit les exceptions ET l'instantane resolu qui en decoule. `resolu` est un
# CACHE, pas une source : il vaut pour la date qu'il porte, et il est refait a
# chaque poussee. Le serveur le lit sans avoir a refaire le calcul en JS ; s'il
# manque, ou si sa date n'est pas la bonne, on retombe sur `presence` comme
# avant — le jeu ne s'arrete pas parce qu'un cache est absent.
# La regie ne deplace personne : ce qu'on lui montre n'a pas lieu dans le
# chateau, et une `salle` poussee vers elle ne doit pas faire entrer un homme
# quelque part.
if not en_regie and (suivi["touchee"] or calcul_presence):
    paquet = {"presence": presence}
    if calcul_presence:
        try:
            paquet["resolu"] = {"date": dict(date),
                                "gens": calcul_presence.resoudre(date, presence)}
        except Exception:
            pass
    tables.ecrire(presence_p, paquet)

# Ce que le joueur vient de traverser paraît désormais sur sa ville.
reveler(vus, mien)

if en_regie:
    # Rien. Ni `monde.json`, ni `horloges.json` : une poussee vers la regie
    # n'a pas eu lieu dans le monde, et le monde ne doit pas s'en apercevoir.
    pass
elif mien:
    horloges[mien] = date
    tables.ecrire(horloges_p, horloges)
    # `monde.date` recule au plus lent : c'est la date jusqu'a laquelle le monde
    # est acquis pour TOUT LE MONDE. Elle n'avance donc que quand la derniere
    # scene a rattrape — et jamais en arriere, un front partant du monde.
    lent = min(sieges, key=lambda s: minute_absolue(horloges[s]))
    monde["date"] = dict(horloges[lent])
else:
    monde["date"] = date
    # Une scene commune (ou une partie seule) fait avancer le monde : les fronts
    # qui trainaient derriere sont rattrapes, sans quoi le minimum les ferait
    # reculer au prochain calcul.
    if sieges:
        change = False
        for s in sieges:
            if minute_absolue(horloges[s]) < minute_absolue(date):
                horloges[s] = dict(date)
                change = True
        if change or os.path.exists(horloges_p):
            tables.ecrire(horloges_p, horloges)
if not en_regie:
    tables.ecrire(monde_p, monde)

# Sans encodage force, la console Windows (cp1252) etouffe sur une fleche et
# le script sort en erreur APRES avoir tout ecrit — de quoi croire a un echec.
print("%d item(s) ajoutes au flux [%s] -- %s j%d -> %s j%d" % (
    len(items),
    ("messe basse : " + ", ".join(pour)) if isinstance(pour, list)
    else ("pour " + pour) if pour else "tous",
    format_heure(depart[1]), depart[0], format_heure(date["minute"]), date["jour"]))
