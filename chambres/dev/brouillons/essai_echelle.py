# -*- coding: utf-8 -*-
"""Le test qui falsifierait le billet de mj-reposdesfreux : existe-t-il UNE
valeur d'echelle qui passe valider_tete_neuve sans lever ? On les essaie
toutes, celles des deux tables et l'absence."""
import sys
import os
import json

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RACINE, "scripts"))

from etat.mutations.val_plan import valider_tete_neuve
from etat.mutations.vocabulaire import (ECHELLES, BUDGETS, CHAMPS_TETE_REQUIS,
                                        CHAMPS_TETE)

print("ECHELLES (vocabulaire) =", ECHELLES)
print("BUDGETS  (temps)       =", tuple(BUDGETS))
print("CHAMPS_TETE_REQUIS     =", CHAMPS_TETE_REQUIS)
print("CHAMPS_TETE            =", CHAMPS_TETE)

brut = json.load(open(os.path.join(RACINE, "etat", "intentions.json"),
                      encoding="utf-8"))
tetes = brut.get("intentions", brut) if isinstance(brut, dict) else brut
vals = list(tetes.values()) if isinstance(tetes, dict) else list(tetes)
print("nb tetes dans intentions.json =", len(vals))
print("  dont portant un champ echelle =",
      sum(1 for t in vals if isinstance(t, dict) and t.get("echelle")))


def essai(ech):
    v = {"personnage_id": "zzz-test", "intention": "x",
         "croyances": ["a"],
         "plan": [{"id": "zzz.1", "quoi": "y", "etat": "en-cours",
                   "jours_restants": 1}],
         "date_maj": {"annee": 129, "lune": 4, "jour": 4}}
    if ech is not None:
        v["echelle"] = ech
    try:
        r = valider_tete_neuve(v, None, {}, {"zzz-test": {}}, None, set())
        return "REFUS : %s" % r if r else "*** ACCEPTE ***"
    except Exception as e:
        return "!! LEVE %s: %s" % (type(e).__name__, e)


print()
for ech in ("scene", "orbite", "royaume", "quartier", "au loin", None):
    print("  echelle=%-10r -> %s" % (ech, essai(ech)))
