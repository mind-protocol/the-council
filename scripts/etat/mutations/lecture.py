# -*- coding: utf-8 -*-
"""LECTURE - le chemin des tables, leur lecture par la porte, les empreintes.

CE QUE CE MODULE POSSEDE : les tables-croyances (a un joueur, pas au monde),
le chemin d'une table (dossier du joueur compris), la lecture par la porte
noyau/tables, les listes deroulees (mains, plis), l'empreinte sha1 du fichier
qu'on va reellement ecrire. Matiere descendue de scripts/appliquer.py (lot 2).
"""
import hashlib
import io
import json
import os
import sys
from etat.expose import tables as porte  # LA PORTE de etat/
import bibliotheque  # noyau : il sait lire les livres scindes comme le monolithe

SCRIPTS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RACINE = os.path.dirname(SCRIPTS)
ETAT = os.path.join(RACINE, "etat")
STAGING = ETAT


# Les tables qui appartiennent a UN JOUEUR, pas au monde. Elles ne decrivent
# pas ce qui est : elles decrivent ce qu'un joueur CROIT. A deux, les partager
# revient a donner la table de guerre de la reine a sa maitresse de la voix —
# elles vivent donc dans etat/joueurs/<personnage_id>/.
CROYANCES = ("jetons", "vues", "objectifs")


def chemin_table(nom, joueur=None):
    """Le fichier d'une table — dans le dossier du joueur si c'en est une.

    Meme regle que scripts/ajouter.py, et meme refus bruyant : une fois la
    racine archivee, ecrire une croyance sans dire A QUI reviendrait a la
    poser dans un fichier fantome que le jeu ne relira jamais. C'est
    exactement le bug qu'on vient de corriger — on ne le laisse pas revenir.
    """
    if nom in CROYANCES:
        if joueur:
            p = os.path.join(ETAT, "joueurs", joueur, nom + ".json")
            if os.path.isfile(p):
                return p
        p = os.path.join(ETAT, nom + ".json")
        if os.path.isfile(p):
            return p
        if joueur:
            sys.exit(
                "pas de {}.json pour le joueur '{}', et plus de repli a la "
                "racine.\nVerifiez etat/joueurs/{}/ : le --joueur est-il le "
                "bon personnage_id ?".format(nom, joueur, joueur))
        sys.exit(
            "{}.json n'existe plus a la racine : cette table appartient a un "
            "joueur.\nPrecisez a qui vous ecrivez : --joueur <personnage_id>."
            .format(nom))
    return os.path.join(ETAT, nom + ".json")


def lire(nom, joueur=None):
    # LES LIVRES NE SONT PLUS UN FICHIER, ET CE CHEMIN NE LE SAVAIT PAS.
    # `scinder_bibliotheque.py` a eclate `etat/books.json` en un volume par
    # fichier sous `etat/books/` ; ici on visait encore le monolithe, donc
    # `chemin_table("books")` tombait sur un chemin mort et `porte.lire`
    # sortait par `sys.exit`. Mesure du 31.8 : toute activation qui produisait
    # une mutation mourait a l'application, apres que l'homme ait vecu sa
    # journee et que le rapport ait ete normalise — le travail etait fait et
    # jete. `bibliotheque` sait lire les deux formes ; on lui demande.
    if nom == "books":
        return bibliotheque.charger(ETAT)
    try:
        return porte.lire(chemin_table(nom, joueur))
    except porte.TableAbimee as e:
        sys.exit(str(e))


def liste_mains(table):
    """mains.json a une racine {mains: [...]} ; on rend la liste."""
    return table.get("mains", []) if isinstance(table, dict) else table


def liste_plis(table):
    """plis.json a une racine {plis: [...]} ; on rend la liste."""
    return table.get("plis", []) if isinstance(table, dict) else table


def empreinte(nom, joueur=None):
    # Le sceau doit porter sur le fichier qu'on va REELLEMENT ecrire : sceller
    # la racine tout en ecrivant dans le dossier du joueur ne garde rien.
    chemin = (chemin_table(nom, joueur) if nom in CROYANCES
              else os.path.join(ETAT, nom + ".json"))
    if not os.path.isfile(chemin):
        return None
    with io.open(chemin, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def par_id(table, cle="id"):
    return {x.get(cle): x for x in table if isinstance(x, dict)}
