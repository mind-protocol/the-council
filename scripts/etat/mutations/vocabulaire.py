# -*- coding: utf-8 -*-
"""VOCABULAIRE - les constantes du vocabulaire ferme des mutations.

CE QUE CE MODULE POSSEDE : les enums et champs autorises par table (transcrits
de docs/schema.md), les budgets par echelle (repris de temps/ quand la porte
repond), les petites aides sans etat (books, relations, jetons), la lecture
des dates {annee, lune, jour} et la sentinelle CONTINUE des validateurs.
Matiere descendue de scripts/appliquer.py (lot 2) - le POURQUOI du vocabulaire
ferme est dans la docstring du paquet (etat/mutations/__init__.py).
"""
import json
import re
import unicodedata
from etat.expose import tables as porte  # LA PORTE de etat/


try:
    # Une seule table de budgets pour les deux scripts : celle de tick.py,
    # qui transcrit docs/schema.md. `echelle_de` MESURE l'echelle (quartier /
    # au loin) : c'est la seule clef legitime de BUDGETS depuis que le champ
    # `echelle` a ete supprime du schema.
    from temps.expose import BUDGETS, echelle_de
except ImportError:     # doublon de secours, a retoucher AVEC celui de bouche.py
    # LE SECOURS DOIT PORTER LES MEMES CLEFS QUE LA VRAIE TABLE. Le 129.4.4, il
    # portait encore scene/orbite/royaume : tant que temps/ s'importait, la
    # contradiction restait invisible ; le jour ou l'import aurait manque, le
    # meme lot serait passe ou tombe selon l'humeur du sys.path.
    BUDGETS = {
        "quartier": {"acteurs": None, "croyances": 6, "etapes": 5,
                     "declencheurs": 3},
        "au loin":  {"acteurs": None, "croyances": 3, "etapes": 2,
                     "declencheurs": 1},
    }

    def echelle_de(tete):    # sans topologie, on simule trop plutot que trop peu
        return "quartier"

ETATS_ETAPE = ("en-cours", "fait", "bloque", "abandonne")
ETATS_ETAPE_VIVANTS = ("en-cours", "bloque")
# L'ECHELLE D'UNE TETE NE SE DECLARE PLUS (docs/schema.md l.146 : « supprime »)
# — elle se MESURE, et la clef des budgets est `echelle_de`. Ce tuple-ci ne
# survit que pour le champ `promeut` d'un seuil de main, ou docs/schema.md l.215
# le dit « valeur libre et desormais indicative ».
ECHELLES = ("scene", "orbite", "royaume")
STATUTS_EVENEMENT = ("a-venir", "resolu", "devie", "annule")
ETATS_PERSO = ("actif", "dormant", "mort")

CHAMPS_ETAPE = ("etat", "jours_restants", "quoi", "cout", "si_bloque",
                "depend_de", "accompli")
CHAMPS_TETE = ("intention", "attitude_joueur", "date_maj")
CHAMPS_TETE_REQUIS = ("personnage_id", "croyances", "intention",
                      "plan", "date_maj")
CHAMPS_EVENEMENT = ("statut", "effets", "date_prevue", "importance")
CHAMPS_PERSO = ("lieu_id", "condition", "etat")
CHAMPS_MONDE = ("date", "tension", "phase")
# les mains : seul tick.py pose valeur/reliquat, seul le MJ pose le reste
CHAMPS_MESURE = ("valeur", "reliquat")
CHAMPS_SEUIL = ("franchi_le",)
CHAMPS_MAIN = ("mandat", "porteur", "dernier_rapport", "date_maj", "salle")
# le courrier (docs/plis.md)
CANAUX_PLI = ("corbeau", "cavalier", "barque")
ETATS_PLI = ("en-route", "remis", "ouvert", "retenu", "perdu", "intercepte")
ETATS_PLI_EN_MAIN = ("remis", "ouvert", "retenu")
CHAMPS_PLI = ("etat", "main", "attendu_le", "canal", "scelle", "porte")
CHAMPS_PLI_REQUIS = ("id", "canal", "porte", "de", "pour", "vers",
                     "parti_le", "attendu_le", "etat")
# la rumeur : un incident de la table de guerre (docs/carte.md)
CERTITUDES = ("sure", "rapportee", "rumeur")
FEUX = ("vif", "couve", "eteint")
CHAMPS_INCIDENT = ("feu", "certitude", "statut", "ames", "contenu", "detail")
CHAMPS_PROPAGE_REQUIS = ("ou", "date", "certitude", "contenu")

OPERATIONS = {
    "intentions": ("etape", "etape_ajouter", "tete", "tete_ajouter",
                   "croyance_ajouter", "croyance_retirer", "ignore_ajouter",
                   "ignore_retirer", "declencheur_ajouter",
                   "declencheur_retirer"),
    "evenements": ("diffusion_livree", "diffusion_ajouter", "evenement"),
    "personnages": ("personnage", "personnage_ajouter"),
    "monde": ("monde",),
    "mains": ("mesure", "seuil", "main", "main_ajouter"),
    "plis": ("pli", "pli_ajouter"),
    "lieux": ("roukerie",),
    "jetons": ("incident_propage", "incident"),
    "relations": ("relation", "relation_ajouter"),
    # LES AFFAIRES. Sans ce domaine, un acteur pouvait EXECUTER une affaire
    # mais jamais en ouvrir une : les 33 affaires du tissu etaient toutes de
    # la main du MJ, et un homme important sans affaire le restait a jamais.
    # Une affaire proposee est relue avant
    # d'etre appliquee — c'est la garde, pas l'interdiction.
    "books": ("affaire_ajouter", "affaire_action_ajouter", "affaire_action"),
}

# La colonne d'etat d'une table d'actions, reconnue par son intitule : ces
# cahiers n'ont pas de schema, seulement des en-tetes ecrits a la main.
TITRE_TABLE_ACTIONS = "actions"
COLONNES_AFFAIRE_NEUVE = {
    "🎯 États cibles": ["🎯 N°", "🏷️ L'état", "✅ Ce qui doit être vrai",
                         "📍 Où", "👁️ La preuve", "⬆️ Sert"],
    "🔒 Verrous": ["🔒 N°", "🏷️ Le verrou", "⛔ Bloque",
                   "📌 Ce qui est vrai aujourd'hui", "👁️ La preuve",
                   "🔓 Levé quand"],
    "🗝️ Clefs": ["🗝️ N°", "🏷️ La clef", "🔓 Ouvre", "💡 Le principe",
                  "💰 Le prix", "🚪 Ce que cela ferme",
                  "👁️ La preuve attendue", "⚖️ Décision"],
    "⚔️ Actions": ["⚔️ N°", "🏷️ L'action", "🗝️ Réalise", "📝 Ce qu'on fait",
                    "📍 Où", "🪶 Office", "🧰 Moyens", "💰 Ce qu'elle coûte",
                    "⛓️ Dépend de", "👁️ La preuve", "⏳ État"],
}


def prochaine_ligne_action(actions, numero):
    """La ligne dont la premiere cellule porte ce numero, gras compris."""
    cible = str(numero or "").strip().strip("*")
    if not cible:
        return None
    for ligne in actions.get("lignes") or []:
        cellules = ligne.get("cellules") or []
        if cellules and str(cellules[0]).strip().strip("*") == cible:
            return ligne
    return None


def liste_books(tables):
    brut = tables.get("books")
    if isinstance(brut, dict):
        return brut.get("books") or brut.get("livres") or []
    return brut if isinstance(brut, list) else []


def table_actions(livre):
    """La table des actions d'une affaire, reconnue a son intitule."""
    for t in livre.get("tables") or []:
        if TITRE_TABLE_ACTIONS in plat_titre(t.get("titre")):
            return t
    return None


def plat_titre(t):
    return unicodedata.normalize("NFD", str(t or "")).encode(
        "ascii", "ignore").decode("ascii").lower()

# Ouvrir une maison cree des gens, leur donne des liens, leur arme des
# reactions et leur pose des compteurs. Les quatre operations ci-dessous
# existent pour ca : sans elles, chaque ouverture finissait par un bloc « a
# la main » — c'est-a-dire par la perte exacte des gardes que ce script
# existe pour donner.
CHAMPS_PERSO_REQUIS = ("id", "nom", "etat")
CHAMPS_MAIN_REQUIS = ("id", "quoi", "porteur", "lieu_id")
CHAMPS_RELATION = ("opinion", "liens", "connue_du_joueur")
TYPES_PORTEUR = ("personnage", "maison", "lieu")


def charge_relation(m, op, champs):
    """L'objet relation, qu'il soit range dans `valeur` ou dans `champs`.

    `valeur` est la forme documentee pour un ajout et `champs` celle d'un
    patch — mais les sessions d'activation ecrivent l'ajout dans `champs`,
    parce que c'est le geste naturel et que rien a l'ecriture ne les reprend.
    Mesure du 129.4.2 : sur 47 mutations rejetees en vingt-cinq rapports,
    CINQ l'etaient pour cette seule raison, `source_id` et `cible_id` bien
    presents dans l'autre poche. Une arete du monde perdue pour une clef.

    On accepte les deux et l'on ne desserre rien d'autre : tous les controles
    de fond (personnages connus, sens de la relation, champs autorises, borne
    de l'opinion) restent en aval, sur l'objet qu'on vient de trouver.
    """
    if op == "relation_ajouter":
        v = m.get("valeur")
        if isinstance(v, dict):
            return v
        return champs
    return champs if champs else m.get("valeur")


def rang_certitude(valeur):
    """sure=2, rapportee=1, rumeur=0. Inconnu -> rapportee."""
    try:
        return len(CERTITUDES) - 1 - CERTITUDES.index(valeur)
    except ValueError:
        return 1


def liste_jetons(table):
    """jetons.json a une racine {jetons, traits, zones} ; on rend les pieces."""
    return table.get("jetons", []) if isinstance(table, dict) else table


def liste_simple(table, clef):
    """Une table {<clef>: [...]} ou une liste nue — on rend la liste."""
    if table is None:
        return []
    return table.get(clef, []) if isinstance(table, dict) else table




# Sentinelle des validateurs : la mutation est deja traitee (faute ou
# plan), passe a la suivante - l'equivalent du continue d'origine.
CONTINUE = object()


def declencheur_vise(d, valeur):
    """Ce declencheur est-il celui que `valeur` designe (son 'si' exact) ?

    UNE ENTREE MALFORMEE DOIT RESTER ATTEIGNABLE. Les deux voies filtraient
    `isinstance(d, dict)` : une CHAINE tombee dans la liste — le champ
    `valeur` d'un declencheur_retirer qui s'y est retrouve — devenait donc
    increvable, `declencheur_retirer` ne pouvant plus la matcher et `tete`
    n'acceptant pas le champ (CHAMPS_TETE). Mesure de mj-accalmie le 129.4.3 :
    mestre-hallis.declencheurs[0] est une chaine, et AUCUNE operation du
    vocabulaire ne pouvait l'oter d'une table partagee.

    On ne devine pas pour autant : une chaine ne se designe que par
    elle-meme, a l'octet. C'est la porte de sortie d'un dechet, pas une
    tolerance de saisie.
    """
    if isinstance(d, dict):
        return d.get("si") == valeur
    return d == valeur


def date_lisible(date):
    """Vrai si c'est bien un {annee, lune, jour} d'entiers."""
    if not isinstance(date, dict):
        return False
    return all(isinstance(date.get(c), int) for c in ("annee", "lune", "jour"))


def normaliser_date(date):
    """Rend un {annee, lune, jour} d'entiers, ou None si ca ne se lit pas.

    Les sessions d'activation ecrivent parfois `date_maj` en chaine —
    « 129-4-3 », « 129.4.3 » — la ou le format est un objet. Rien ne les
    reprenait : le patch de tete controlait le NOM des champs, jamais la forme
    de celui-la. Mesure du 129.4.3 : six tetes fraichement reecrites (gerardys,
    otto, robert-quince, corlys, rulf-corne, le-sanglier) sont ressorties
    « date_maj absente ou illisible » au verificateur — donc perpetuellement en
    retard, puisqu'on ne sait plus calculer leur age.

    On normalise au lieu de refuser : le sens de « 129-4-3 » n'est pas
    ambigu, et rejeter la mutation ferait perdre TOUTE la reecriture de la
    tete pour une histoire de separateur.
    """
    if date_lisible(date):
        return date
    if isinstance(date, str):
        morceaux = re.split(r"[-./ ]+", date.strip())
        if len(morceaux) == 3:
            try:
                a, l, j = (int(x) for x in morceaux)
            except ValueError:
                return None
            return {"annee": a, "lune": l, "jour": j}
    return None
