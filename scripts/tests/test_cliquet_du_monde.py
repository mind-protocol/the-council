# -*- coding: utf-8 -*-
"""`monde.date` ne recule pas par la porte — elle avance, ou elle ne bouge pas.

CE QUE CE TEST GARDE, ET POURQUOI IL EXISTE. Le 31.8, le curseur du monde a
recule DEUX FOIS dans la meme heure, apres un recalage accorde et applique au
129.4.4 minute 540 — la derniere minute ECRITE de toutes les tables du joue.

  * la premiere par `scene/flux.py` : un lot rejoue, date du 3e, ecrivait
    `monde.date` a sa propre date sans regarder si elle etait anterieure ;
  * la seconde par une ECRITURE PERDUE : un processus avait lu `monde.json`
    avant le recalage, travaille, et reecrit son exemplaire entier apres.

La seconde est celle qui commande la forme du garde-fou. Un cliquet pose chez
un appelant ne protege que de ceux qui savent qu'ils ecrivent ; celui qui
ecrase, par definition, ne le sait pas. Le cliquet vit donc A LA PORTE, relit
le disque, et DIT tout haut ce qu'il refuse — un garde-fou muet ne se distingue
pas d'une panne.

Un monde derriere son propre registre ne se voit dans aucune table : il se voit
six jours plus tard, quand une scene deja ecrite se rejoue.
"""
import io
import json
import os
import sys
import unittest

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import tables  # noqa: E402 — LA PORTE


def _ecrire(chemin, date):
    with io.open(chemin, "w", encoding="utf-8") as f:
        f.write(json.dumps({"date": date, "phase": "guerre_ouverte"},
                           ensure_ascii=False))


def _date(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.loads(f.read())["date"]


class CliquetDuMonde(unittest.TestCase):
    """On eprouve la fonction sur le vrai chemin de `monde.json`, sans y toucher :
    le cliquet ne se declenche que pour ce fichier-la, et le mesurer ailleurs ne
    prouverait rien."""

    def setUp(self):
        self.p = tables.chemin("monde")
        self.sauvegarde = None
        if os.path.exists(self.p):
            with io.open(self.p, encoding="utf-8") as f:
                self.sauvegarde = f.read()
        os.environ.pop("RECUL_VOULU", None)

    def tearDown(self):
        if self.sauvegarde is not None:
            with io.open(self.p, "w", encoding="utf-8") as f:
                f.write(self.sauvegarde)
        os.environ.pop("RECUL_VOULU", None)

    def test_un_recul_est_refuse_et_la_date_du_disque_reste(self):
        _ecrire(self.p, {"annee": 129, "lune": 4, "jour": 4, "minute": 540})
        propose = {"date": {"annee": 129, "lune": 4, "jour": 3, "minute": 721},
                   "phase": "guerre_ouverte"}
        tables.ecrire("monde", propose)
        self.assertEqual(_date(self.p)["jour"], 4)
        self.assertEqual(_date(self.p)["minute"], 540)
        # et la valeur remise en main de l'appelant est celle qui a ete ecrite,
        # pour qu'un appelant qui relit son propre dictionnaire ne se croie pas
        # au 3e alors que le monde est au 4e.
        self.assertEqual(propose["date"]["jour"], 4)

    def test_une_avance_passe(self):
        _ecrire(self.p, {"annee": 129, "lune": 4, "jour": 4, "minute": 540})
        tables.ecrire("monde", {"date": {"annee": 129, "lune": 4, "jour": 4,
                                         "minute": 900}})
        self.assertEqual(_date(self.p)["minute"], 900)

    def test_le_recul_voulu_reste_possible_mais_se_declare(self):
        """Une purge arriere est un ACTE : elle passe, et elle se nomme."""
        _ecrire(self.p, {"annee": 129, "lune": 4, "jour": 9, "minute": 540})
        os.environ["RECUL_VOULU"] = "1"
        tables.ecrire("monde", {"date": {"annee": 129, "lune": 4, "jour": 4,
                                         "minute": 540}})
        self.assertEqual(_date(self.p)["jour"], 4)

    def test_la_minute_compte_autant_que_le_jour(self):
        """Le premier recul du 31.8 valait dix-neuf heures, pas un jour entier."""
        _ecrire(self.p, {"annee": 129, "lune": 4, "jour": 4, "minute": 540})
        tables.ecrire("monde", {"date": {"annee": 129, "lune": 4, "jour": 4,
                                         "minute": 300}})
        self.assertEqual(_date(self.p)["minute"], 540)


if __name__ == "__main__":
    unittest.main()
