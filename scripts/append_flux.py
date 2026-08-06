# Ajoute des items au flux de jeu (append-only) ET tient l'horloge du monde.
# Usage : python scripts/append_flux.py '<json item>' '<json item>' ...
#    ou : python scripts/append_flux.py --fichier chemin.json   (liste d'items)
# Un item {"type": "effacer"} vide l'écran (changement de scène).
#
# L'HORLOGE. Chaque item consomme du temps de jeu. Le script estampe l'item de
# l'heure a laquelle il se produit ("heure": "6h04"), puis avance
# monde.date.minute de sa duree. Le MJ n'ecrit que "duree" (en minutes) quand
# elle sort de l'ordinaire ; sinon le defaut du type s'applique. Au passage de
# 1440 minutes, le jour s'incremente. Voir docs/schema.md.
import json, io, os, sys

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
chemin = os.path.join(racine, "etat", "flux.jsonl")
monde_p = os.path.join(racine, "etat", "monde.json")

# Minutes consommees par defaut, par type d'item.
# question/reponse sont hors fiction ; pensee est gratuite par regle du jeu.
DUREES = {
    "replique": 1, "geste": 1, "vous": 1, "recit": 5, "table": 2,
    "evenement": 2, "salle": 0, "breve": 0, "marque": 0, "objectif": 0,
    "effacer": 0, "question": 0, "reponse": 0, "pensee": 0,
    # Les coulisses sont hors univers : l'horloge de la fiction n'y touche pas.
    "meta": 0, "coulisses": 0,
}

JOURS_PAR_LUNE = 30
LUNES_PAR_AN = 12


def portrait(pid):
    return io.open(os.path.join(racine, "ecrans", "portraits", pid + ".svg"), encoding="utf-8").read()


def format_heure(minute):
    return "%dh%02d" % (minute // 60, minute % 60)


def avancer(date, minutes):
    """Avance la date de N minutes, en cascadant jour/lune/annee."""
    total = date.get("minute", 0) + minutes
    while total >= 1440:
        total -= 1440
        date["jour"] += 1
        if date["jour"] > JOURS_PAR_LUNE:
            date["jour"] = 1
            date["lune"] += 1
            if date["lune"] > LUNES_PAR_AN:
                date["lune"] = 1
                date["annee"] += 1
    date["minute"] = total
    return date


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
pour = None
explicite = False
if "--pour" in args:
    i = args.index("--pour")
    pour = args[i + 1]
    explicite = True
    args = args[:i] + args[i + 2:]
    if pour in ("tous", "commun", "-"):
        pour = None

items = []
if args and args[0] == "--fichier":
    items = json.load(io.open(args[1], encoding="utf-8"))
else:
    items = [json.loads(a) for a in args]

if not explicite:
    pour = audience_courante()

monde = json.load(io.open(monde_p, encoding="utf-8"))
date = monde["date"]
date.setdefault("minute", 0)
depart = (date["jour"], date["minute"])

with io.open(chemin, "a", encoding="utf-8") as f:
    for it in items:
        # raccourci : {"presents": ["daemon", ...]} avec ids simples → inline les SVG
        if it.get("type") == "salle" and it.get("presents") and isinstance(it["presents"][0], dict) and "portrait_svg" not in it["presents"][0]:
            for p in it["presents"]:
                p["portrait_svg"] = portrait(p["id"])
        # Un item peut porter sa propre date (saut de temps narre) : on la suit.
        if isinstance(it.get("date"), dict):
            for k in ("annee", "lune", "jour"):
                if k in it["date"]:
                    date[k] = it["date"][k]
            if "minute" in it["date"]:
                date["minute"] = it["date"]["minute"]
        # L'audience s'estampille a l'ecriture : elle est portee par chaque
        # item, jamais recalculee a la lecture. Un `pour` deja pose sur l'item
        # l'emporte — c'est l'apartee dans une scene commune.
        if "pour" not in it and pour:
            it["pour"] = pour
        it["heure"] = format_heure(date["minute"])
        # la date portee par l'item reflete l'horloge, pour le bandeau et la reprise
        it["date"] = {"annee": date["annee"], "lune": date["lune"],
                      "jour": date["jour"], "minute": date["minute"]}
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
        avancer(date, it.get("duree", DUREES.get(it.get("type"), 0)))

monde["date"] = date
io.open(monde_p, "w", encoding="utf-8").write(json.dumps(monde, ensure_ascii=False, indent=2) + "\n")

# Sans encodage force, la console Windows (cp1252) etouffe sur une fleche et
# le script sort en erreur APRES avoir tout ecrit — de quoi croire a un echec.
print("%d item(s) ajoutes au flux [%s] -- %s j%d -> %s j%d" % (
    len(items), ("pour " + pour) if pour else "tous",
    format_heure(depart[1]), depart[0], format_heure(date["minute"]), date["jour"]))
