# -*- coding: utf-8 -*-
import os
import sys
import unittest


SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from plan.expose import charges  # noqa: E402 — la porte du container

ChargeInvalide = charges.ChargeInvalide
appliquer = charges.appliquer
projeter = charges.projeter


def proposition():
    return {
        "id": "evt-proposition", "charge_id": "charge-58110-essai-1",
        "acteur_id": "nlr", "geste": "proposer",
        "affaire_id": "affaire-organiser-collaboration",
        "piece_id": "58110", "engagement": "Eprouver un trajet reel",
        "preuve_attendue": "Deux gestes dates et un resultat adressable",
        "dependances": ["un canal conserve"], "date": "129.5.12",
        "limite_autorite": "Je ne reponds que de ma part",
    }


class ChargesTest(unittest.TestCase):
    def test_proposition_exige_le_contrat_complet(self):
        evenement = proposition()
        del evenement["preuve_attendue"]
        with self.assertRaisesRegex(ChargeInvalide, "preuve_attendue"):
            projeter([evenement])

    def test_prise_volontaire_n_est_pas_une_affectation(self):
        etat = projeter([
            proposition(),
            {"id": "evt-prise", "charge_id": "charge-58110-essai-1",
             "acteur_id": "nlr", "geste": "prendre"},
        ])
        self.assertEqual(["nlr"], etat["charges"]["charge-58110-essai-1"]["porteurs"])

    def test_transmission_laisse_l_ancien_responsable_jusqu_a_acceptation(self):
        evenements = [
            proposition(),
            {"id": "evt-prise", "charge_id": "charge-58110-essai-1",
             "acteur_id": "nlr", "geste": "prendre"},
            {"id": "evt-relais", "charge_id": "charge-58110-essai-1",
             "acteur_id": "nlr", "geste": "transmettre", "a": "nicolas"},
        ]
        attente = projeter(evenements)
        charge = attente["charges"]["charge-58110-essai-1"]
        self.assertEqual(["nlr"], charge["porteurs"])
        accepte = appliquer(attente, {
            "id": "evt-acceptation", "charge_id": "charge-58110-essai-1",
            "acteur_id": "nicolas", "geste": "prendre", "origine": "evt-relais",
        })
        self.assertEqual(["nicolas"], accepte["charges"]["charge-58110-essai-1"]["porteurs"])

    def test_partage_n_ajoute_la_seconde_main_qu_apres_son_geste(self):
        base = projeter([
            proposition(),
            {"id": "evt-prise", "charge_id": "charge-58110-essai-1",
             "acteur_id": "nlr", "geste": "prendre"},
            {"id": "evt-partage", "charge_id": "charge-58110-essai-1",
             "acteur_id": "nlr", "geste": "partager", "a": "nicolas",
             "part": "contre-lire la preuve"},
        ])
        self.assertEqual(["nlr"], base["charges"]["charge-58110-essai-1"]["porteurs"])
        accepte = appliquer(base, {
            "id": "evt-part-prise", "charge_id": "charge-58110-essai-1",
            "acteur_id": "nicolas", "geste": "prendre", "origine": "evt-partage",
        })
        charge = accepte["charges"]["charge-58110-essai-1"]
        self.assertEqual(["nlr", "nicolas"], charge["porteurs"])
        self.assertEqual("contre-lire la preuve", charge["parts"]["nicolas"])

    def test_un_tiers_ne_peut_pas_accepter_l_invitation(self):
        base = projeter([
            proposition(),
            {"id": "evt-prise", "charge_id": "charge-58110-essai-1",
             "acteur_id": "nlr", "geste": "prendre"},
            {"id": "evt-relais", "charge_id": "charge-58110-essai-1",
             "acteur_id": "nlr", "geste": "transmettre", "a": "nicolas"},
        ])
        with self.assertRaisesRegex(ChargeInvalide, "destinataire"):
            appliquer(base, {
                "id": "evt-intrus", "charge_id": "charge-58110-essai-1",
                "acteur_id": "intrus", "geste": "prendre", "origine": "evt-relais",
            })

    def test_rejouer_le_meme_evenement_est_idempotent(self):
        evenement = proposition()
        premier = projeter([evenement])
        second = appliquer(premier, evenement)
        self.assertEqual(premier, second)


if __name__ == "__main__":
    unittest.main()
