# -*- coding: utf-8 -*-
"""Audite la convergence de ``rendre_au_joueur`` sous coupures.

Le banc remplace uniquement les quatre autorités de sortie par des doublures
en mémoire. Il n'écrit ni dans ``etat/`` ni dans une chambre. Son verdict
décrit le code courant : une non-conformité attendue reste une exécution
réussie du banc.
"""
from __future__ import annotations

import json
import os
import sys
from unittest import mock


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(RACINE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from agents import parloir  # noqa: E402


ETAPES = ("canal", "web", "spool_mj", "lecture")


class Sorties:
    def __init__(self, coupure_apres=None):
        self.coupure_apres = coupure_apres
        self.coupe = False
        self.acquis = {etape: 0 for etape in ETAPES}

    def _acquerir(self, etape):
        self.acquis[etape] += 1
        if self.coupure_apres == etape and not self.coupe:
            self.coupe = True
            raise RuntimeError("coupure après %s" % etape)

    def deposer_canal(self, *args, **kwargs):
        if self.acquis["canal"]:
            return "canal-fixture", False
        self._acquerir("canal")
        return "canal-fixture", True

    def pousser_web(self, *args, **kwargs):
        self._acquerir("web")

    def deposer_spool(self, *args, **kwargs):
        self._acquerir("spool_mj")
        return {"id": "retour-fixture"}

    def marquer_lu(self, *args, **kwargs):
        self._acquerir("lecture")


def eprouver(coupure_apres):
    sorties = Sorties(coupure_apres)
    enveloppe = {
        "de": "living-stone-architect",
        "joueur": "nicolas-lester-reynolds",
        "texte": "fixture-audit",
        "contexte_id": "94020",
        "ref": "vmti7dah5pnl8",
    }
    erreurs = []
    with mock.patch("agents.expose.billet.deposer", sorties.deposer_canal), \
            mock.patch("agents.parloir._pousser_au_flux_web", sorties.pousser_web), \
            mock.patch("agents.expose.mj.deposer_retour_parloir", sorties.deposer_spool), \
            mock.patch("agents.chambre.marquer_lu", sorties.marquer_lu):
        for tentative in (1, 2):
            try:
                parloir.rendre_au_joueur(**enveloppe)
            except RuntimeError as exc:
                erreurs.append({"tentative": tentative, "erreur": str(exc)})
    conforme = all(sorties.acquis[etape] == 1 for etape in ETAPES)
    return {
        "coupure_apres": coupure_apres or "aucune",
        "tentatives": 2,
        "effets_acquis": sorties.acquis,
        "erreurs": erreurs,
        "attendu_apres_reprise": {etape: 1 for etape in ETAPES},
        "verdict": "CONFORME" if conforme else "NON_CONVERGENT",
    }


def main():
    cas = [eprouver(None)] + [eprouver(etape) for etape in ETAPES]
    rapport = {
        "schema": "audit-reprise-retour-joueur/1",
        "cible": "scripts/agents/parloir.py:rendre_au_joueur",
        "enveloppe": {
            "contexte_id": "94020",
            "ref": "vmti7dah5pnl8",
        },
        "invariant": (
            "Après toute coupure et reprise du même billet, chaque sortie "
            "est acquise exactement une fois."
        ),
        "cas": cas,
        "verdict_global": (
            "CONFORME" if all(c["verdict"] == "CONFORME" for c in cas)
            else "NON_CONFORME"
        ),
    }
    print(json.dumps(rapport, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
