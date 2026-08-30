# -*- coding: utf-8 -*-
"""LA RUMEUR — ce qui saute de proche en proche, et les bouches qui arrivent.

CE QUE CE MODULE POSSEDE : la propagation des incidents de la table de guerre
(docs/carte.md) — certitudes qui se degradent a chaque saut, lenteur de la
bouche a oreille, plafond de voisins —, la detection des arrivees (la bouche :
qui arrive ou, et ce qu'il apporte que personne sur place ne sait), les
temoins, et les cycles du graphe de dependances d'etapes.

LE FUTUR « BRUIT DE FOND » ATTERRIT ICI (grain 3 : deux co-presents se sont
parle -> entree de diffusion canal rumeur/temoin, zero appel LLM). C'est la
feature qui a tire ce decoupage — docs/organisation.md §5.

CE QU'IL REFUSE : toute prose. Le script propose le saut, sa date, la
certitude degradee ; la `version` — ce qui se dit vraiment la-bas, de
travers — est ecrite a la main par le MJ. Une machine n'a rien a faire la ou
le brouillard se fabrique.

CONSOMMATEURS : fenetre.py (propager_rumeurs, detecter_bouches), gardes/
(temoins_des_incidents, relais_de, rang_certitude, cycles, SILENCE_RUMEUR).
"""

from temps.calendrier import jour_absolu, date_de
from temps.lecture import jours_de_route
from temps.bouche import croyances_de, se_recoupent, echelle_de

# Echelle de certitude, du plus sur au plus trouble. Un saut degrade d'un cran.
CERTITUDES = ("sure", "rapportee", "rumeur")
# Plus lente que le cavalier : plein tarif x3/2, jamais moins de deux jours.
LENTEUR_RUMEUR = (3, 2)
SAUT_RUMEUR_MINIMUM = 2
PORTEE_SAUT_RUMEUR = 3
VOISINS_PAR_RUMEUR = 3
SILENCE_RUMEUR = {"vif": 5, "couve": 15}


def temoins_des_incidents(e):
    """Les gens nommes en `depuis` d'un relais : les temoins (sans tete, voulu)."""
    raise NotImplementedError("implem : passe 2")


def rang_certitude(valeur):
    """sure=2, rapportee=1, rumeur=0. Inconnu -> rapportee, au milieu."""
    raise NotImplementedError("implem : passe 2")


def degrader(valeur):
    """Ce que devient une certitude apres un saut de bouche a oreille."""
    raise NotImplementedError("implem : passe 2")


def relais_de(incident):
    """Le foyer et tout ce qui a ete gagne, au meme format {ou, date, ...}."""
    raise NotImplementedError("implem : passe 2")


def saut_rumeur(e, depuis, vers):
    """Jours d'un saut de rumeur. Plus lent que le cavalier, par principe."""
    raise NotImplementedError("implem : passe 2")


def propager_rumeurs(e, fin, cible):
    """(sauts, immobiles) : ce qu'une rumeur gagne dans la fenetre."""
    raise NotImplementedError("implem : passe 2")


def sans_accents(texte):
    """Le texte a plat, sans accents ni tirets, pour comparer des noms."""
    raise NotImplementedError("implem : passe 2")


def lieu_cite(e, texte):
    """Le lieu nomme dans un texte d'etape, s'il y en a un de reconnaissable."""
    raise NotImplementedError("implem : passe 2")


def detecter_bouches(e, a_resoudre, tombent):
    """Qui arrive ou, et ce qu'il apporte que personne sur place ne sait."""
    raise NotImplementedError("implem : passe 2")


def cycles(depend):
    """Cycles du graphe etape -> depend_de. Renvoie des chemins fermes."""
    raise NotImplementedError("implem : passe 2")
