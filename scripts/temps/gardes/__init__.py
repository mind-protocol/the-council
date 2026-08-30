# -*- coding: utf-8 -*-
"""GARDES — l'audit de coherence de etat/ : `python scripts/tick.py --verifier`.

CE QUE CE PAQUET POSSEDE : le Rapport (trois gravites, une gravite mal
orthographiee PLANTE au lieu de se perdre), les dix-neuf verificateurs
repartis par famille de tables, et `verifier()` qui les assemble dans l'ordre.

    plan.py      : intentions, mains, couts chiffres, etats du plan,
                   rapporteurs
    ecrits.py    : pensees, books, boites
    croyances.py : croyances sans porteur, sources possibles
    social.py    : evenements, personnages, plis, rumeurs
    sieges.py    : occupation, sieges, audiences, affectations, registres,
                   activations

TENSION ACTEE : conceptuellement du banc (lit tout, n'ecrit rien) — reexamen
vers bancs/ apres le lot 2. On ne le deplace pas avant.

CE QU'IL REFUSE : la moindre ecriture, et la moindre reparation — un audit
signale, il ne repare jamais.

CONSOMMATEURS : la facade scripts/tick.py (--verifier), /admin/sante via
--verifier --json, scripts/tests/essai_occupation.py (verifier_occupation).
"""
import json

from temps.gardes.plan import (  # noqa: F401
    verifier_intentions, verifier_mains, verifier_couts_chiffres,
    verifier_etats_du_plan, verifier_rapporteurs)
from temps.gardes.ecrits import (  # noqa: F401
    CLES_BOOK, CLES_BOITE, TYPES_BOOK, verifier_pensees, qui_a_du_temps,
    verifier_books, verifier_boites)
from temps.gardes.croyances import (  # noqa: F401
    sources_possibles, verifier_croyances_sans_porteur)
from temps.gardes.social import (  # noqa: F401
    verifier_evenements, verifier_personnages, verifier_plis,
    verifier_rumeurs)
from temps.gardes.sieges import (  # noqa: F401
    verifier_occupation, siege_par_id, verifier_sieges,
    verifier_audiences, verifier_affectations,
    verifier_registres_derives, verifier_activations)

GRAVITES = ("grave", "avertissement", "note")


class Rapport(object):
    def __init__(self):
        self.anomalies = []

    def dire(self, gravite, sujet, texte):
        # `imprimer` ne parcourt que GRAVITES : une gravite mal orthographiee
        # disparaissait sans un mot, et l'audit se croyait propre. On refuse
        # bruyamment plutot que de perdre l'anomalie.
        if gravite not in GRAVITES:
            raise ValueError(
                "gravite inconnue {!r} pour [{}] — attendu {}".format(
                    gravite, sujet, ", ".join(GRAVITES)))
        self.anomalies.append({"gravite": gravite, "sujet": sujet,
                               "texte": texte})

    def imprimer_json(self):
        # Meme audit, servi a l'ecran au lieu du terminal : `--verifier --json`
        # alimente /admin/sante. Le texte reste la source, on ne le reformate
        # pas — un panneau qui dit autre chose que le terminal ne vaut rien.
        durs = [a for a in self.anomalies if a["gravite"] != "note"]
        print(json.dumps({
            "anomalies": self.anomalies,
            "durs": len(durs),
            "notes": len(self.anomalies) - len(durs),
            "par_gravite": {g: len([a for a in self.anomalies
                                    if a["gravite"] == g]) for g in GRAVITES},
        }, ensure_ascii=False))

    def imprimer(self):
        durs = [a for a in self.anomalies if a["gravite"] != "note"]
        print("Audit de etat/ — {} anomalie(s){}".format(
            len(durs),
            " + {} note(s) informative(s)".format(
                len(self.anomalies) - len(durs))
            if len(durs) != len(self.anomalies) else ""))
        if not self.anomalies:
            print("  rien a signaler.")
            return
        for gravite in GRAVITES:
            lot = [a for a in self.anomalies if a["gravite"] == gravite]
            if not lot:
                continue
            print("\n== {} ({}) ==".format(gravite.upper(), len(lot)))
            for a in lot:
                print("  [{}] {}".format(a["sujet"], a["texte"]))


def verifier(e, en_json=False):
    r = Rapport()
    if not e.joueur:
        r.dire("avertissement", "journal",
               "personnage_joueur_id absent — impossible de proteger sa tete")
    verifier_sieges(e, r)
    verifier_intentions(e, r)
    verifier_evenements(e, r)
    verifier_personnages(e, r)
    verifier_mains(e, r)
    verifier_pensees(e, r)
    verifier_books(e, r)
    verifier_registres_derives(e, r)
    verifier_rapporteurs(e, r)
    verifier_etats_du_plan(e, r)
    verifier_boites(e, r)
    verifier_plis(e, r)
    verifier_couts_chiffres(e, r)
    verifier_rumeurs(e, r)
    verifier_croyances_sans_porteur(e, r)
    verifier_affectations(e, r)
    verifier_activations(e, r)
    verifier_audiences(e, r)
    r.imprimer_json() if en_json else r.imprimer()
    # Les 'note' sont informatives : elles ne font pas echouer l'audit. La
    # croyance sans porteur crie fort sur l'etat d'avant la refonte, et ce
    # n'est pas une raison de bloquer le jeu.
    return 1 if [a for a in r.anomalies if a["gravite"] != "note"] else 0
