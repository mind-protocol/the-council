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
    villes = sorted({str(p.get("lieu_id") or "").strip()
                     for p in donnees if isinstance(p, dict)} - {""})
    zones = ["mj"] + ["mj-" + v.replace("-", "") for v in villes]
    for z in zones:
        neuve = not os.path.isdir(chambre.chemin(z))
        chambre.ouvrir(z)
        dire("  %s%s" % (z, "  (ouverte)" if neuve else ""))
    return zones
