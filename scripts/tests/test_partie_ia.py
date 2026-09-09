# -*- coding: utf-8 -*-
"""Le camp joué par une IA (partie_ia.py) et le banc de touche (partie_coach.py),
audit du 7.9, items C4, C5, C6 : l'enum du schéma suit le rôle, la phrase du
rythme n'est dite qu'aux moitiés, un camp sans caractère ne joue pas, et le
coach ne va qu'aux sièges déclarés. Aucun appel à `claude` ici : on ne
regarde que les prompts, les schémas et les commandes."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
for p in (SCRIPTS, NOYAU):
    if p not in sys.path:
        sys.path.insert(0, p)

import partie_greffe  # noqa: E402
from partie_greffe import Partie  # noqa: E402
import partie_ia  # noqa: E402
import partie_coach  # noqa: E402


class _PartieJetable(unittest.TestCase):
    """Une partie dans un dossier temporaire, dont la config est lue là et non
    dans etat/parties : on détourne `partie_greffe.DOSSIER` le temps du test."""

    def setUp(self):
        self.dossier = tempfile.mkdtemp(prefix="partie-ia-")
        self._dossier_avant = partie_greffe.DOSSIER
        partie_greffe.DOSSIER = self.dossier
        self.chemin = os.path.join(self.dossier, "essai.jsonl")
        p = Partie(self.chemin)
        for camp in ("noir", "vert"):
            r = p.ecrire({"camp": camp, "coup": "viser", "id": camp + "-racine",
                          "texte": "Tenir la couronne (%s)" % camp})
            self.assertFalse(r, r)

    def tearDown(self):
        partie_greffe.DOSSIER = self._dossier_avant
        shutil.rmtree(self.dossier, ignore_errors=True)

    def config(self, **cfg):
        cfg.setdefault("partie", "essai")
        with io.open(os.path.join(self.dossier, "essai.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)
        return Partie(self.chemin)


class SchemaParRoleTest(_PartieJetable):
    def test_entier_recoit_tout_l_enum(self):
        p = self.config()
        self.assertEqual(partie_ia.schema(p, "entier")["properties"]["coup"]["enum"],
                         partie_ia.SCHEMA["properties"]["coup"]["enum"])

    def test_technique_ne_recoit_pas_les_coups_politiques(self):
        p = self.config()
        enum = partie_ia.schema(p, "technique")["properties"]["coup"]["enum"]
        for c in ("viser", "sortir", "bloquer", "justifier", "detruire", "retourner"):
            self.assertNotIn(c, enum)
        for c in ("demander", "lever", "agir", "passer", "reconstruire"):
            self.assertIn(c, enum)

    def test_politique_garde_lever_mais_pas_demander(self):
        p = self.config()
        enum = partie_ia.schema(p, "politique")["properties"]["coup"]["enum"]
        self.assertNotIn("demander", enum)
        self.assertNotIn("reconstruire", enum)
        # LEVER RESTE : le greffe ne sait pas ce qu'est une pièce technique.
        for c in ("lever", "viser", "bloquer", "justifier"):
            self.assertIn(c, enum)

    def test_les_coups_interdits_de_la_partie_s_ajoutent_au_role(self):
        p = self.config(coups_interdits=["retourner", "rearmer"])
        enum = partie_ia.schema(p, "politique")["properties"]["coup"]["enum"]
        for c in ("retourner", "rearmer", "demander"):
            self.assertNotIn(c, enum)
        self.assertIn("bloquer", enum)


class SystemeTest(_PartieJetable):
    RYTHME = "TU JOUES EN PREMIER"

    def test_la_phrase_du_rythme_est_absente_pour_entier(self):
        p = self.config(caractere={"noir": "Tu es le Noir."})
        txt = partie_ia.systeme("noir", "entier", p)
        self.assertNotIn(self.RYTHME, txt)
        self.assertIn("ADVERSAIRE", txt)

    def test_la_phrase_du_rythme_est_dite_aux_moitiés(self):
        p = self.config(caractere={"noir": "Tu es le Noir."})
        for role in ("technique", "politique"):
            txt = partie_ia.systeme("noir", role, p)
            self.assertEqual(txt.count(self.RYTHME), 1, role)

    def test_le_caractere_vient_de_la_config(self):
        p = self.config(caractere={"noir": "Tu es le Noir, et rien d'autre."})
        self.assertIn("Tu es le Noir, et rien d'autre.", partie_ia.systeme("noir", "entier", p))
        self.assertFalse(hasattr(partie_ia, "CAMPS"))


class RefusSansCaractereTest(_PartieJetable):
    def test_jouer_refuse_sans_caractere_et_n_appelle_pas(self):
        p = self.config(caractere={"vert": "Tu es le Vert."})
        appels = []
        avant = partie_ia.appeler
        partie_ia.appeler = lambda *a, **k: appels.append(a) or ({}, {})
        try:
            sortie = io.StringIO()
            with redirect_stdout(sortie):
                code = partie_ia.jouer(p, "noir", "entier", voir=False)
        finally:
            partie_ia.appeler = avant
        self.assertEqual(code, 2)
        self.assertEqual(appels, [])
        self.assertIn("aucun caractère écrit pour le camp noir", sortie.getvalue())
        self.assertIn("etat/parties/essai.json", sortie.getvalue())

    def test_voir_passe_avec_un_caractere(self):
        p = self.config(caractere={"noir": "Tu es le Noir."})
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            code = partie_ia.jouer(p, "noir", "technique", voir=True)
        self.assertEqual(code, 0)
        self.assertIn("Tu es le Noir.", sortie.getvalue())


class CoachTest(_PartieJetable):
    def setUp(self):
        super().setUp()
        self.items = os.path.join(self.dossier, "_commentaire.json")
        with io.open(self.items, "w", encoding="utf-8") as f:
            json.dump([{"type": "coulisses", "qui": "Le banc de touche", "texte": "Bien joué."}], f)

    def test_les_sieges_sont_l_union_des_camps_sans_doublon(self):
        p = self.config(sieges={"noir": ["rhaenyra", "aurore"], "vert": "aurore"})
        self.assertEqual(partie_coach.sieges_de_la_partie(p), ["rhaenyra", "aurore"])

    def test_voir_imprime_une_commande_par_siege_sans_rien_lancer(self):
        p = self.config(sieges={"noir": ["rhaenyra"], "vert": ["aurore"]})
        cmds = partie_coach.commandes_coach(p, self.items)
        self.assertEqual([c[-1] for c in cmds], ["rhaenyra", "aurore"])
        for c in cmds:
            self.assertTrue(c[1].endswith("append_flux.py"), c)
            self.assertEqual(c[2:4], ["--fichier", self.items])
            self.assertEqual(c[4], "--pour")
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            code = partie_coach.coach(p, self.items, voir=True)
        self.assertEqual(code, 0)
        self.assertIn("--pour rhaenyra", sortie.getvalue())
        self.assertIn("--pour aurore", sortie.getvalue())
        self.assertNotIn("poussé", sortie.getvalue())

    def test_sans_siege_declare_on_refuse_et_rien_ne_part(self):
        p = self.config()
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            code = partie_coach.coach(p, self.items, voir=False)
        self.assertEqual(code, 2)
        self.assertIn("aucun siège déclaré", sortie.getvalue())
        self.assertNotIn("tous", sortie.getvalue())

    def test_fichier_introuvable(self):
        p = self.config(sieges={"noir": ["rhaenyra"]})
        sortie = io.StringIO()
        with redirect_stdout(sortie):
            code = partie_coach.coach(p, os.path.join(self.dossier, "absent.json"), voir=True)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
