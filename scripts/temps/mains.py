# -*- coding: utf-8 -*-
"""MAINS — l'arithmetique des mesures : rythmes, bornes, decomptes, seuils.

CE QUE CE MODULE POSSEDE : tout ce qui fait bouger une mesure de mains.json
en entiers exacts (le reliquat empeche toute derive, quelle que soit la
decoupe des ticks), la lecture des couts chiffres d'une etape de plan, et le
predicat de seuil.

CE QU'IL REFUSE : la boucle qui applique tout ca sur une fenetre (fenetre.py),
et le jugement des mains mal formees (gardes/plan.py).

CONSOMMATEURS : fenetre.py (le decompte de la fenetre), gardes/plan.py
(verifier_mains, verifier_couts_chiffres via couts_chiffres et seuil_franchi).
"""


def rythme_de(mesure):
    """(par, jours) en entiers. Un rythme illisible vaut 'ne bouge pas'."""
    r = mesure.get("rythme")
    if not isinstance(r, dict):
        return (0, 1)
    par = r.get("par", 0)
    jours = r.get("jours", 1)
    if not isinstance(par, int) or not isinstance(jours, int) or jours <= 0:
        return (0, 1)
    return (par, jours)


def borner(valeur, mesure):
    bas, haut = mesure.get("plancher"), mesure.get("plafond")
    if isinstance(bas, int) and valeur < bas:
        return bas, "plancher"
    if isinstance(haut, int) and valeur > haut:
        return haut, "plafond"
    return valeur, None


def au_plancher(mesure):
    bas = mesure.get("plancher")
    return isinstance(bas, int) and mesure.get("valeur") == bas


def decompter(mesure, jours):
    """Entiers seulement : total = par*n + reliquat, puis division plancher.

    Rend (valeur_apres, reliquat_apres, borne). Exact et sans derive, quelle
    que soit la decoupe des ticks — c'est tout l'interet du reliquat.
    """
    par, pas = rythme_de(mesure)
    depart = mesure.get("valeur")
    if not isinstance(depart, int):
        depart = 0
    reliquat = mesure.get("reliquat")
    if not isinstance(reliquat, int) or not 0 <= reliquat < pas:
        reliquat = 0
    total = par * jours + reliquat
    valeur, borne = borner(depart + total // pas, mesure)
    return valeur, total % pas, borne


def porteur_absent(e, act):
    """Un porteur mort ou absent ne produit plus, mais l'affaire coute encore."""
    p = act.get("porteur") or {}
    if p.get("type") != "personnage":
        return False
    perso = e.perso_par_id.get(p.get("id"))
    return perso is None or perso.get("etat") == "mort"


def couts_chiffres(etape):
    """Les couts qui CITENT une mesure : {mesure: <adresse>, quantite: <int>}.

    Un cout en clair ('des journees de seize heures') reste au jugement du MJ ;
    seuls ceux-la se verifient tout seuls.
    """
    return [c for c in (etape.get("cout") or [])
            if isinstance(c, dict) and c.get("mesure")]


def chiffrer_cout(etape, mesures_apres):
    """Ce qui manque pour tenir l'etape, adresse par adresse. [] = ca passe."""
    manque = []
    for c in couts_chiffres(etape):
        adresse = c["mesure"]
        besoin = c.get("quantite", 0)
        if adresse not in mesures_apres:
            manque.append({"mesure": adresse, "quantite": besoin,
                           "probleme": "adresse de mesure inconnue"})
            continue
        dispo = mesures_apres[adresse]
        if isinstance(besoin, int) and dispo < besoin:
            manque.append({"mesure": adresse, "quantite": besoin,
                           "disponible": dispo, "manque": besoin - dispo})
    return manque


def seuil_franchi(mesure_valeur, seuil):
    quand, borne = seuil.get("quand"), seuil.get("valeur")
    if not isinstance(borne, int):
        return False
    if quand == "sous":
        return mesure_valeur < borne
    if quand == "sur":
        return mesure_valeur > borne
    return False
