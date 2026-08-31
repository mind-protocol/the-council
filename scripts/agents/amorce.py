# -*- coding: utf-8 -*-
"""AMORCE — les arbitres de zone naissent AVANT qu'on les appelle.

`appeler_zone` ouvre la chambre d'un MJ paresseusement, au premier call —
mais un mecanisme paresseux sans amorce est invisible : tant que personne ne
parle a `mj-portreal`, il n'existe nulle part, et le front (« Les arbitres »)
ne liste que les chambres sur disque. Ici on ouvre la chambre de `mj` et
d'un `mj-<ville>` par ville habitee (les `lieu_id` distincts de
personnages.json, normalises sans tirets — la regle de zone.py).

Idempotent : une chambre existante n'est jamais retouchee (chambre.ouvrir).
Une ville qui nait plus tard retombe sur le paresseux, qui marche toujours.
"""
from agents import chambre


def ouvrir_les_zones(dire=lambda t: None):
    """Ouvre mj + un mj-<ville> par ville habitee. Rend la liste des ids."""
    from etat.expose import tables
    import os
    donnees = tables.lire(os.path.join(chambre.RACINE, "etat",
                                       "personnages.json"), [])
    if isinstance(donnees, dict):
        donnees = donnees.get("personnages") or []
    if any(isinstance(p, dict) and p.get("id") == "dev" for p in donnees):
        dire("  ATTENTION : un personnage du monde s'appelle 'dev' — ce nom"
             " est RESERVE au developpeur (docs/habitant.md).")
    villes = {str(p.get("lieu_id") or "").strip()
              for p in donnees if isinstance(p, dict)}
    # LES LIEUX D'ECHEANCES AUSSI (trou signale par le MJ le 31.8 :
    # ralliement-trident echoit a vivesaigues et personne n'y arbitrait —
    # une echeance peut pointer une zone qu'aucun personnage n'habite).
    evenements = tables.lire(os.path.join(chambre.RACINE, "etat",
                                          "evenements.json"), [])
    if isinstance(evenements, dict):
        evenements = (evenements.get("evenements")
                      or next((v for v in evenements.values()
                               if isinstance(v, list)), []))
    for e in evenements or []:
        if isinstance(e, dict):
            villes.add(str(e.get("ou") or "").strip())
            # ... et les lieux de DIFFUSION : une nouvelle a produire quelque
            # part exige un arbitre la-bas (le cas vivesaigues : l'evenement
            # n'y est pas, sa diffusion si).
            for diff in (e.get("diffusion") or []):
                if isinstance(diff, dict):
                    villes.add(str(diff.get("ou") or "").strip())
    villes = sorted(villes - {""})
    # `dev` : le developpeur est un habitant adressable (nom reserve) —
    # une chambre, des billets, des actions assignees ; jamais depeche.
    zones = ["mj", "dev"] + ["mj-" + v.replace("-", "") for v in villes]
    for z in zones:
        neuve = not os.path.isdir(chambre.chemin(z))
        chambre.ouvrir(z)
        dire("  %s%s" % (z, "  (ouverte)" if neuve else ""))
    return zones
