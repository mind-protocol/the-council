# -*- coding: utf-8 -*-
"""
TABLES — la seule porte de `etat/`.

    from tables import lire, ecrire, chemin
    monde = lire("monde")                     # etat/monde.json
    agenda = lire("joueurs/aurore/agenda", {})
    ecrire("monde", monde)                    # atomique, jamais a moitie ecrit

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
4. **Toute ecriture est ATOMIQUE** — fichier temporaire dans le meme dossier,
   puis `os.replace`. Il n'existe qu'une implementation ici, la ou il y en avait
   deux. C'est ce qui empeche le fichier a moitie ecrit qui produit le cas 1.

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
import tempfile

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


def ecrire(nom, valeur, indent=2):
    """Ecrire une table, atomiquement. Rend le chemin ecrit.

    `indent` : la mise en page N'EST PAS un detail ici. Les gros registres
    (`books`, les rapports) s'ecrivent en indent=1 — chaque espace compte sur
    2 Mo —, les cartes de ville en compact (`indent=None` → separateurs
    serres), le reste en 2. La porte impose la semantique d'erreur et
    l'atomicite, pas la mise en page : forcer indent=2 partout aurait reecrit
    des tables entieres au premier passage de chaque migrant.
    """
    return _poser(chemin(nom), lambda f: _dump(valeur, f, indent))


def ecrire_lignes(nom, lignes):
    """Ecrire un fichier JSONL ENTIER (une valeur JSON par ligne), atomiquement.

    Pour les projections qui reecrivent tout leur fichier d'un bloc
    (`tisser.py` et `noyau/chiffrer.py` deposent `etat/tissu/*.jsonl` ainsi).
    L'APPEND au fil (`append_flux.py`) n'est PAS ce geste : il reste chez sa
    seule plume. `nom` garde son extension telle quelle.
    """
    def _rendre(f):
        for l in lignes:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    p = nom if os.path.isabs(nom) else os.path.join(ETAT, *str(nom).replace("\\", "/").split("/"))
    return _poser(p, _rendre)


def _dump(valeur, f, indent):
    if indent is None:
        json.dump(valeur, f, ensure_ascii=False, separators=(",", ":"))
    else:
        json.dump(valeur, f, ensure_ascii=False, indent=indent)
    f.write("\n")


def _poser(p, rendre):
    """L'ecriture atomique elle-meme : temporaire dans le meme dossier, replace."""
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    fd, provisoire = tempfile.mkstemp(dir=d or None, suffix=".tmp")
    try:
        with io.open(fd, "w", encoding="utf-8", newline="\n") as f:
            rendre(f)
        os.replace(provisoire, p)
    except BaseException:
        try:
            if os.path.exists(provisoire):
                os.remove(provisoire)
        except OSError:
            pass
        raise
    return p


# Les deux noms sous lesquels le depot connaissait deja ces gestes. Ils sont ici
# pour qu'une migration tienne en une ligne d'import au lieu d'un renommage — et
# pour qu'il n'existe plus qu'UNE implementation derriere les deux.
def lire_json(chemin_ou_nom, defaut=_RIEN):
    return lire(chemin_ou_nom, defaut)


def ecrire_atomique(chemin_ou_nom, valeur):
    return ecrire(chemin_ou_nom, valeur)


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
_HORS = ("scripts/noyau/tables.py",)


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
