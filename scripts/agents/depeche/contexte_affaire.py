# -*- coding: utf-8 -*-
"""Le morceau du plan general qu'un appel contextualise doit reellement voir."""

from agents.depeche.brief import id_item_affaire


def _resoudre_mj(numero):
    """Les numéros 8xxxx vivent dans la chambre MJ, pas dans les cahiers de maison."""
    if not (80000 <= int(numero) <= 89999):
        return None
    from plan.expose import tisser
    affaires = tisser.charger_affaires_mj(tisser.RACINE)
    noeuds = {n["id"]: n for n in tisser.noeuds_affaires_mj(affaires)}
    if numero not in noeuds:
        return None
    choisi = noeuds[numero]
    livre_id = choisi.get("livre_id")
    livre = next((a for a in affaires if a.get("id") == livre_id), {})
    aretes = tisser.aretes_affaires_mj(affaires, [])
    chaine, vus, file = [], {numero}, [numero]
    while file:
        courant = file.pop(0)
        for a in aretes:
            parent = str(a.get("vers") or "")
            if (str(a.get("de")) != courant or parent in vus
                    or parent not in noeuds
                    or noeuds[parent].get("livre_id") != livre_id):
                continue
            vus.add(parent)
            chaine.append(parent)
            file.append(parent)
    lignes = [
        "Affaire MJ : **%s**." % (livre.get("titre") or livre_id),
        "Adresse canonique MJ : `%s`." % numero,
        "Source : `%s`." % livre_id,
        "",
        "ITEM DEMANDE — `%s` · %s · %s" % (
            numero, choisi.get("genre"), choisi.get("quoi")),
    ]
    for ident in chaine:
        n = noeuds[ident]
        lignes.append("- `%s` · %s · %s" %
                      (ident, n.get("genre"), n.get("quoi")))
    lignes.extend([
        "",
        "Ce contexte contribue à la préparation du MJ. Réponds à la question "
        "reçue avec les éléments utiles à la scène et à son issue.",
    ])
    return {"id": numero, "affaire": livre.get("titre") or livre_id,
            "texte": "\n".join(lignes), "chaine": [numero] + chaine,
            "volumes": [livre_id], "autorite": "mj"}


def _charge(chargeur=None):
    if chargeur is None:
        from plan.expose import couverture
        chargeur = couverture.charger
    resultat = chargeur()
    # couverture.charger() rend (livres, pieces, inventaire, affaires). Un
    # chargeur de test peut rendre directement le dictionnaire des pieces.
    return resultat[1] if isinstance(resultat, tuple) else resultat


def _ligne(numero, piece, choisie=False):
    marque = "ITEM DEMANDE — " if choisie else ""
    ligne = "- %s`%s` · %s · %s" % (
        marque, numero, piece.get("genre") or "piece",
        piece.get("nom") or "pièce à nommer")
    details = []
    if piece.get("etat"):
        details.append("etat : %s" % piece["etat"])
    if piece.get("jour"):
        details.append("jour du : %s" % piece["jour"])
    if details:
        ligne += "\n  " + " ; ".join(details)
    return ligne


def resoudre(contexte_id, chargeur=None):
    """Resout l'item et sa chaine ascendante, sans aspirer toute l'affaire."""
    numero = id_item_affaire(contexte_id)
    pieces = _charge(chargeur)
    if numero not in pieces:
        focus_mj = _resoudre_mj(numero) if chargeur is None else None
        if focus_mj:
            return focus_mj
        raise ValueError("l'item d'affaire `%s` n'existe pas dans le plan general"
                         % numero)

    choisie = pieces[numero]
    affaire = choisie.get("affaire") or "affaire à nommer"
    volumes = list(dict.fromkeys(
        s.get("volume_id") for s in (choisie.get("cahier_sources") or [])
        if s.get("volume_id")))
    if len(volumes) > 1:
        raise ValueError(
            "collision sur l'item `%s` : il appartient a plusieurs cahiers (%s)"
            % (numero, ", ".join(volumes)))
    chaine, vus, a_lire = [], {numero}, [numero]
    while a_lire:
        courant = a_lire.pop(0)
        for parent in pieces.get(courant, {}).get("vers") or []:
            # La premiere sortie hors du cahier est une dependance du grand
            # plan, pas le brief local de cette affaire.
            if parent in vus or parent not in pieces:
                continue
            if pieces[parent].get("affaire") != affaire:
                continue
            vus.add(parent)
            chaine.append(parent)
            a_lire.append(parent)

    sources = []
    for source in choisie.get("cahier_sources") or []:
        volume = source.get("volume_id")
        table = source.get("table")
        etiquette = "`%s`" % volume if volume else "cahier à identifier"
        if table:
            etiquette += " · table %s" % table
        if etiquette not in sources:
            sources.append(etiquette)

    lignes = [
        "Affaire : **%s**." % affaire,
        "Adresse canonique : `%s`. Cette adresse seule identifie la piece."
        % numero,
    ]
    if sources:
        lignes.append("Source : " + " ; ".join(sources) + ".")
    lignes.extend(["", "Chaîne utile, de l'item vers ce qu'il doit ouvrir :",
                   _ligne(numero, choisie, choisie=True)])
    lignes.extend(_ligne(n, pieces[n]) for n in chaine)
    lignes.extend([
        "",
        "Travaille depuis cet item et cette chaîne. Lorsqu'une dépendance "
        "précise ouvre une autre affaire, suis cette dépendance et poursuis.",
    ])
    return {"id": numero, "affaire": affaire, "texte": "\n".join(lignes),
            "chaine": [numero] + chaine, "volumes": volumes}


def focaliser(dossier, contexte_id, chargeur=None):
    """Remplace les inventaires quotidiens larges par le seul contexte vise."""
    focus = resoudre(contexte_id, chargeur=chargeur)
    resultat = dict(dossier or {})
    resultat["contexte_affaire"] = focus
    resultat["affaires_du_jour"] = focus["texte"]
    resultat["travaux_ouverts"] = []
    return resultat
