# -*- coding: utf-8 -*-
"""GARDE DES CROYANCES — « aucune croyance sans porteur », et ses sources.

CE QUE CE MODULE POSSEDE : la garde de fond de la refonte — un fait n'entre
dans une tete que parce que quelqu'un ou quelque chose l'y a porte — et le
rassemblement des sources possibles d'un savoir (diffusion livree, plis en
main, actes vus, paroles entendues, incidents arrives sur place, bouches des
tetes voisines).

CE QU'IL REFUSE : comprendre le sens — recoupement de mots rares, heuristique
assumee, gravite 'note', jamais bloquante.

CONSOMMATEURS : gardes/__init__.py (verifier()).
"""
from temps.lecture import ETATS_PLI_EN_MAIN
from temps.bouche import croyances_de, se_recoupent


def sources_possibles(e, pid):
    """Tout ce qui a PU apprendre quelque chose a ce personnage.

    HEURISTIQUE, et il faut la lire comme telle (docs/plis.md, « la bouche ») :
    on ne sait pas relire le francais, on rassemble les textes auxquels il a eu
    acces et on cherchera un recoupement de mots rares. Sont retenus :
      - les entrees de diffusion LIVREES qui le nomment, ou livrees a son lieu ;
      - les plis qu'il a en main, ou qui lui sont adresses et arrives ;
      - les actes qu'il a commis, dont il est dit `connu_de`, ou qui se sont
        produits sous ses yeux (meme lieu) ;
      - les paroles dont il est locuteur, destinataire ou temoin ;
      - les croyances des autres tetes presentes au meme endroit (la bouche).
    """
    lid = e.lieu((e.perso_par_id.get(pid) or {}).get("lieu_id"))
    textes = []

    for ev in e.evenements:
        for ent in ev.get("diffusion") or []:
            if not isinstance(ent, dict) or ent.get("livree") is not True:
                continue
            if pid in (ent.get("qui") or []) or (
                    ent.get("ou") and lid and e.lieu(ent["ou"]) == lid):
                textes.append(ent.get("version") or "")

    for pli in e.plis:
        if not isinstance(pli, dict) or pli.get("etat") not in ETATS_PLI_EN_MAIN:
            continue
        if pli.get("main") == pid or pli.get("pour") == pid:
            textes.append(pli.get("porte") or "")

    for acte in e.actes:
        if not isinstance(acte, dict):
            continue
        connu = acte.get("connu_de") or []
        vu = (acte.get("acteur_id") == pid or pid in connu or "tous" in connu
              or (lid and acte.get("lieu_id")
                  and e.lieu(acte["lieu_id"]) == lid))
        if vu:
            textes.append("{} {}".format(acte.get("quoi") or "",
                                         acte.get("description") or ""))

    for parole in e.paroles:
        if not isinstance(parole, dict):
            continue
        if pid in (parole.get("locuteur_id"), parole.get("destinataire_id")) \
                or pid in (parole.get("temoins") or []):
            textes.append(parole.get("contenu") or "")

    # LE TEMOIN et la rumeur : ce qu'un incident a apporte ICI. Un relais qui a
    # pris a son lieu lui est parvenu, et un relais dont il est lui-meme le
    # `depuis` est une chose qu'il a vue et racontee. Un temoin n'a pas de tete
    # (c'est voulu) : sans cette branche, ce qu'il apporte ne justifierait
    # jamais rien, et l'heuristique crierait au faux positif sur des faits
    # parfaitement portes.
    for inc in e.incidents:
        propre = inc.get("contenu") or ""
        if lid and e.lieu(inc.get("ou")) == lid:
            textes.append(propre)
        for ent in inc.get("propage") or []:
            if isinstance(ent, str):
                if lid and e.lieu(ent) == lid:
                    textes.append(propre)
                continue
            if not isinstance(ent, dict):
                continue
            arrive = lid and e.lieu(ent.get("ou")) == lid
            porte = ent.get("depuis") == pid
            if arrive or porte:
                textes.append(ent.get("contenu") or propre)

    if lid:
        for autre in e.intentions:
            aid = autre.get("personnage_id")
            if aid == pid:
                continue
            if e.lieu((e.perso_par_id.get(aid) or {}).get("lieu_id")) == lid:
                textes.extend(croyances_de(autre))

    return [t for t in textes if t]


def verifier_croyances_sans_porteur(e, r):
    """« Aucune croyance sans porteur » — en gravite 'note', jamais bloquante.

    C'est la garde de fond de la refonte : un fait n'entre dans une tete que
    parce que quelqu'un ou quelque chose l'y a porte. La verification exacte
    demanderait de comprendre le sens ; on se contente d'un recoupement de mots
    rares, et sur l'etat d'avant la refonte elle criera beaucoup — c'est attendu.
    Elle ne compte pas dans le code de sortie et sort sous 'NOTE'.
    """
    for tete in e.intentions:
        pid = tete.get("personnage_id")
        croyances = croyances_de(tete)
        if not pid or not croyances:
            continue
        textes = sources_possibles(e, pid)
        orphelines = [c for c in croyances
                      if not any(se_recoupent(c, t) for t in textes)]
        if not orphelines:
            continue
        r.dire("note", pid,
               "{}/{} croyance(s) sans porteur repere (heuristique de mots "
               "rares — ni pli, ni bouche sur place, ni acte, ni parole, ni "
               "diffusion livree ne les explique) : {}".format(
                   len(orphelines), len(croyances),
                   " | ".join(c[:70] for c in orphelines)))
