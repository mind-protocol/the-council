# -*- coding: utf-8 -*-
"""
TABLES — la seule porte de `etat/`.

    from tables import lire, ecrire, chemin
    monde = lire("monde")                     # etat/monde.json
    agenda = lire("joueurs/aurore/agenda", {})
    ecrire("monde", monde)                    # ecriture directe dans la table

POURQUOI CE MODULE EXISTE.
`tick.py` proclame en tete : « Un seul ecrivain. » L'intention est la bonne, la
realite ne l'etait pas : trente-huit fichiers Python ecrivent dans `etat/*.json`,
`lire_json(chemin, defaut)` etait defini QUATRE fois, et les quatre ne se
comportaient pas pareil devant un fichier corrompu. Deux plantaient, deux
repartaient silencieusement d'un etat vide. Sur un depot dont `etat/` est la
seule memoire du jeu, c'est la faute la plus couteuse possible — et elle est
invisible tant qu'elle ne se produit pas. Une regle ecrite dans un en-tete n'est
pas une regle : c'est un souhait. Une porte unique est une regle, parce qu'on
peut la VERIFIER :

    python scripts/noyau/tables.py --verifier

CE QUE LA PORTE TRANCHE, ET POURQUOI DANS CE SENS.

1. **Un JSON corrompu PLANTE.** Toujours, sans exception, sans defaut. Un
   `books.json` tronque par une ecriture interrompue qui repartirait sur `{}`
   fabrique une partie amnesique dont personne ne saura dire quand elle a perdu
   la memoire — on s'en apercevrait trois lunes plus tard, en lisant des annales
   qui n'ont plus de sens. Mieux vaut un arret net, tout de suite, a l'endroit
   exact.
2. **Un fichier ABSENT rend le defaut, s'il en existe un.** C'est le seul cas
   legitime : un fichier qui n'existe pas encore n'est pas un fichier abime.
   Sans defaut fourni, l'absence plante aussi — on ne devine pas la forme
   attendue d'une table qu'on n'a jamais vue.
3. **Un fichier illisible (droits, disque, verrou) PLANTE.** Meme raison qu'au
   1 : ce n'est pas une absence, c'est une panne, et une panne avalee est une
   panne qui se rejoue.
4. **Toute ecriture est DIRECTE** — la porte ouvre le fichier cible et le
   reecrit. Il n'y a ni fichier temporaire ni `os.replace`. Une interruption
   peut donc laisser un JSON tronque ; le cas 1 le fera planter au prochain
   lecteur au lieu de servir silencieusement un etat vide.

POURQUOI PAS `scripts/etat.py`, LE NOM QUE L'AUDIT DEMANDAIT.
Parce qu'il est piege. `etat/` est un DOSSIER a la racine du depot, et Python 3
en fait un paquet-espace-de-noms des que la racine passe devant `scripts/` dans
`sys.path` — ce qui arrive sous pytest, sous `python -m`, et depuis un shell
ouvert a la racine. `import etat` rendrait alors le dossier de donnees au lieu
du module, sans erreur et sans avertissement :

    >>> import etat; etat.__path__
    _NamespacePath(['.../le-conseil2/etat'])

Livrer, sous le nom `etat`, une porte destinee a fermer une classe de fautes
silencieuses, et qui peut elle-meme etre remplacee en silence, aurait ete la
meme faute d'un cran plus haut. `tables` est le mot que le manuel emploie deja
partout (« les tables que la feuille designe », « Table inconnue »).

CE QU'IL NE FAIT PAS. Il ne connait pas les tables par leur nom, ne valide aucun
schema, n'a aucun avis sur le contenu : `docs/schema.md` reste la seule autorite
sur la forme. Il ne remplace pas `scripts/ajouter.py` — poser UNE entree dans une
table d'empilement sans relire tout le tableau reste le bon geste a deux
sessions, et `ajouter.py` passe desormais par cette porte-ci pour ecrire.
"""
import io
import json
import os
import re
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")

_RIEN = object()          # « aucun defaut fourni », distinct de None


class TableAbimee(Exception):
    """Un fichier de `etat/` existe mais ne se lit pas. On ne devine jamais."""


def chemin(nom):
    """Le chemin d'une table.

    `nom` est un nom court (`"monde"`), un chemin sous `etat/`
    (`"joueurs/aurore/agenda"`), ou un chemin absolu qu'on rend tel quel — pour
    que les appelants qui tiennent deja leur chemin puissent passer la porte
    sans le recomposer.
    """
    if os.path.isabs(nom):
        return nom
    n = str(nom).replace("\\", "/")
    if not n.endswith(".json"):
        n += ".json"
    return os.path.join(ETAT, *n.split("/"))


def lire(nom, defaut=_RIEN):
    """Lire une table. Corrompue : ca plante. Absente : le defaut, s'il existe."""
    p = chemin(nom)
    try:
        with io.open(p, encoding="utf-8") as f:
            texte = f.read()
    except FileNotFoundError:
        if defaut is _RIEN:
            raise TableAbimee(
                "%s n'existe pas, et aucun defaut n'a ete fourni.\n"
                "Si l'absence est normale ici, passez-le : lire(%r, {})." % (p, nom))
        return defaut
    except OSError as e:
        # Droits, disque, verrou : une panne, pas une absence. On ne l'avale pas.
        raise TableAbimee("%s est illisible : %s" % (p, e))
    try:
        return json.loads(texte)
    except ValueError as e:
        raise TableAbimee(
            "%s n'est pas du JSON valide : %s\n"
            "AUCUN defaut ne sera servi a la place. Une table abimee qui repart a "
            "vide fabrique une partie amnesique dont personne ne saura dire quand "
            "elle a perdu la memoire.\n"
            "Reparez le fichier (git checkout, ou la copie du jour) avant de "
            "rejouer." % (p, e))


def existe(nom):
    return os.path.exists(chemin(nom))


def _cliquet_du_monde(p, valeur):
    """`monde.date` ne recule pas par la porte. Elle avance, ou elle ne bouge pas.

    LE 31.8, DEUX FOIS DANS LA MEME HEURE. Le curseur du monde avait ete recale
    au 129.4.4 minute 540 — la derniere minute ECRITE de toutes les tables, la
    reine disant « Nous attendons midi ». Deux minutes plus tard il portait
    129.4.3 minute 740 : un lot rejoue, date du 3e, l'avait tire en arriere par
    `scene/flux.py`. J'ai pose la un cliquet, et quatre minutes apres le fichier
    portait 129.4.3 minute 721 — la valeur d'AVANT le recalage, revenue seule.
    Ce second recul n'est pas passe par flux : c'est une ECRITURE PERDUE. Un
    processus avait lu `monde.json` avant le recalage, a travaille, et a reecrit
    son exemplaire entier apres — sans jamais relire le disque.

    D'ou le cliquet ICI et non chez un appelant : la porte est le seul point que
    tous les deposants traversent, et une ecriture perdue est par definition le
    fait de celui qui ne sait pas qu'il ecrase. Chaque ecriture de `monde.json`
    relit donc la date du disque et garde la plus tardive des deux.

    LE MONDE PEUT ENCORE RECULER — mais alors on le dit : `RECUL_VOULU=1` dans
    l'environnement. Un recul est un acte, jamais un effet de bord. C'est la
    difference entre avancer et recaler, et elle ne se voit dans aucune table :
    elle se voit six jours plus tard, quand une scene deja ecrite se rejoue.
    """
    try:
        if os.path.basename(p) != "monde.json" or os.path.dirname(os.path.abspath(p)) != ETAT:
            return
        if not isinstance(valeur, dict) or not isinstance(valeur.get("date"), dict):
            return
        if os.environ.get("RECUL_VOULU"):
            return
        if not os.path.exists(p):
            return
        with io.open(p, encoding="utf-8") as f:
            ancienne = json.loads(f.read()).get("date")
        if not isinstance(ancienne, dict) or ancienne.get("jour") is None:
            return

        def minutes(d):
            return ((((d.get("annee", 0) * 12 + (d.get("lune", 1) - 1)) * 30)
                     + (d.get("jour", 1) - 1)) * 1440) + d.get("minute", 0)

        if minutes(valeur["date"]) < minutes(ancienne):
            sys.stderr.write(
                u"(porte : monde.date ne recule pas — %s propose, %s garde. "
                u"RECUL_VOULU=1 si le recul est voulu.)\n"
                % (valeur["date"], ancienne))
            valeur["date"] = ancienne
    except Exception as e:
        # La porte ne plante jamais pour un garde-fou : l'ecriture reste bonne.
        sys.stderr.write(u"(porte : cliquet du monde en echec — %s)\n" % str(e)[:160])


def ecrire(nom, valeur, indent=2):
    """Ecrire directement une table. Rend le chemin ecrit.

    `indent` : la mise en page N'EST PAS un detail ici. Les gros registres
    (`books`, les rapports) s'ecrivent en indent=1 — chaque espace compte sur
    2 Mo —, les cartes de ville en compact (`indent=None` → separateurs
    serres), le reste en 2. La porte impose la semantique d'erreur, pas la mise
    en page : forcer indent=2 partout aurait reecrit
    des tables entieres au premier passage de chaque migrant.
    """
    p = chemin(nom)
    _cliquet_du_monde(p, valeur)
    p = _ecrire_direct(p, lambda f: _dump(valeur, f, indent))
    return p


def ecrire_lignes(nom, lignes):
    """Ecrire directement un fichier JSONL ENTIER (une valeur JSON par ligne).

    Pour les projections qui reecrivent tout leur fichier d'un bloc
    (`tisser.py` et `noyau/chiffrer.py` deposent `etat/tissu/*.jsonl` ainsi).
    L'APPEND au fil (`append_flux.py`) n'est PAS ce geste : il reste chez sa
    seule plume. `nom` garde son extension telle quelle.
    """
    def _rendre(f):
        for l in lignes:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    p = nom if os.path.isabs(nom) else os.path.join(ETAT, *str(nom).replace("\\", "/").split("/"))
    return _ecrire_direct(p, _rendre)


def _dump(valeur, f, indent):
    if indent is None:
        json.dump(valeur, f, ensure_ascii=False, separators=(",", ":"))
    else:
        json.dump(valeur, f, ensure_ascii=False, indent=indent)
    f.write("\n")


def _ecrire_direct(p, rendre):
    """Reecrit le fichier cible sans temporaire, remplacement ni verrou."""
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    for tentative in range(3):
        try:
            with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                rendre(f)
            break
        except OSError:
            if tentative == 2:
                raise
            time.sleep(0.05 * (tentative + 1))
    return p


# Alias de lecture historique, conserve pour les importeurs existants.
def lire_json(chemin_ou_nom, defaut=_RIEN):
    return lire(chemin_ou_nom, defaut)


# ---------------------------------------------------------------------------
# LA REGLE, RENDUE VERIFIABLE
#
# C'est ce qui manquait : la regle etait ecrite dans un en-tete, elle n'etait
# pas testable. Elle l'est. La commande liste les fichiers qui ecrivent dans
# `etat/` sans passer par cette porte, et sort en 1 s'il en reste.
#
# ELLE NE TOMBE PAS A ZERO AUJOURD'HUI, et c'est voulu : trente-huit ecrivains
# se migrent un par commit, pas en un geste aveugle. Ce que la commande donne
# des maintenant, c'est le COMPTE — donc la trajectoire, et le moyen de refuser
# le trente-neuvieme.
# ---------------------------------------------------------------------------
_ECRITURE = re.compile(r"json\.dump\s*\(|open\s*\([^)]*[\x22\x27]w")
_PORTE = re.compile(r"(from|import)\s+tables\b|\btables\.(lire|ecrire)\b")
_ETAT = re.compile(r"[\x22\x27]etat[\x22\x27]|etat/|etat" + "\\\\")
# Les exemptes, chacun avec sa raison — un fichier n'entre ici que s'il ne
# touche PAS a etat/ (le detecteur est verbeux : le mot « etat » dans un
# commentaire ou une clef de donnees suffit a le faire sonner), jamais pour
# passer outre la porte.
_HORS = (
    "scripts/noyau/tables.py",           # la porte elle-meme
    "scripts/peinture/composer.py",      # n'ecrit que musiques/*.md ; « etat » en commentaire (matiere descendue au lot 2)
    "scripts/carte_geo.py",              # lit les mods CK3, ecrit ecrans/modules/geo.js
    "scripts/analyse/graphe_archi.py",   # lit docs/containers.json, ecrit docs/graphe-archi.md
    "scripts/monde/peyredragon_chateau.py",  # ecrit monde/peyredragon.bati.json ; « etat » = clef de donnees
    "scripts/monde/peyredragon_voirie.py",   # ecrit monde/peyredragon.graph.json ; « etat » = clef de donnees
)


def _fichiers_py():
    import subprocess
    sortie = subprocess.check_output(
        ["git", "ls-files", "*.py"], cwd=RACINE).decode("utf-8", "replace")
    return [f.strip().replace("\\", "/") for f in sortie.splitlines() if f.strip()]


def verifier(bavard=True):
    """Qui ecrit dans `etat/` sans passer par la porte ?"""
    fautifs = []
    for f in _fichiers_py():
        if f in _HORS:
            continue
        p = os.path.join(RACINE, f)
        if not os.path.exists(p):
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        if not _ECRITURE.search(t) or not _ETAT.search(t):
            continue
        if _PORTE.search(t):
            continue
        fautifs.append(f)
    if bavard:
        if not fautifs:
            print("La porte tient : aucun fichier n'ecrit dans etat/ sans passer par tables.")
        else:
            print("%d fichier(s) ecrivent dans etat/ sans passer par la porte :"
                  % len(fautifs))
            for f in fautifs:
                print("   " + f)
            print("")
            print("Migration : lire  -> tables.lire(nom, defaut)")
            print("            ecrire -> tables.ecrire(nom, valeur)")
            print("Un fichier par commit. Ce compte ne doit que descendre.")
    return fautifs


if __name__ == "__main__":
    if "--verifier" in sys.argv:
        sys.exit(1 if verifier() else 0)
    print(__doc__.strip())
