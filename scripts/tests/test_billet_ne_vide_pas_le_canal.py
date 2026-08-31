# -*- coding: utf-8 -*-
"""LE CANAL D'UNE PAIRE NE DOIT JAMAIS SE VIDER TOUT SEUL.

Trouve par mj-aurore le 129.4.4 : billet.deposer() faisait un
lire-modifier-REECRIRE sans atomicite, et sa lecture repartait d'un dict vide
sur un JSON invalide (`except ValueError: d = {}`). Un canal saisi au milieu
d'une ecriture concurrente etait donc relu comme vide, puis REECRIT avec une
seule entree — toute la correspondance disparaissait sans exception et sans
trace, le seul temoin etant un curseur .lu reste en avance sur un canal soudain
court. Elle en avait le precurseur dans son journal du 129.4.3.

Ces trois essais sont la recette de la correction. Le premier est celui qui
compte : sur le canal abime, la correspondance doit etre INTACTE apres l'echec.
"""
import io
import json
import os
import sys

import pytest

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# `agents.expose` D'ABORD, et ce n'est pas un ornement : importer `agents.billet`
# en tout premier casse sur un cycle (billet -> depeche.brief -> expose ->
# depeche.main, encore a moitie initialise). La porte est la seule entree qui
# ordonne le paquet — travers d'avant ce test, laisse tel quel ici.
from agents import expose as _porte  # noqa: E402,F401
from agents import billet, chambre  # noqa: E402


@pytest.fixture
def paire(tmp_path, monkeypatch):
    """Deux chambres jetables et le canal canonique de la paire."""
    monkeypatch.setattr(chambre, "CHAMBRES", str(tmp_path))
    monkeypatch.setattr(billet, "date_du_monde", lambda: (129, 4, 4))
    for qui in ("alicent", "mj-aurore"):
        os.makedirs(os.path.join(str(tmp_path), qui), exist_ok=True)
    return chambre.canal("alicent", "mj-aurore")


def _ecrire(fichier, texte):
    with io.open(fichier, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)


def _entrees(fichier):
    with io.open(fichier, encoding="utf-8") as f:
        return json.load(f)["entrees"]


def test_un_canal_abime_ne_se_fait_pas_ecraser(paire):
    """LE CAS. Le fichier est saisi en plein vol : JSON tronque. L'ancienne
    version repartait a vide et posait un canal d'UNE entree ; on exige
    desormais que rien ne soit ecrit et que les octets restent tels quels."""
    tronque = u'{\n "canal": ["alicent", "mj-aurore"],\n "entrees": [{"de": "ali'
    _ecrire(paire, tronque)

    with pytest.raises(Exception):
        billet.deposer("mj-aurore", "alicent", u"un billet de plus")

    with io.open(paire, encoding="utf-8") as f:
        assert f.read() == tronque, (
            u"le canal abime a ete REECRIT : c'est exactement la perte "
            u"silencieuse qu'on ferme ici")


def test_un_canal_qui_nest_pas_un_objet_ne_se_fait_pas_ecraser(paire):
    """Lisible, mais ce n'est pas un canal (une liste nue). On ne devine pas,
    et surtout on n'ecrase pas : l'ancienne version le remplacait par {}."""
    _ecrire(paire, u'["ceci n\'est pas un canal"]')
    with pytest.raises(billet.CanalAbime):
        billet.deposer("alicent", "mj-aurore", u"salut")
    with io.open(paire, encoding="utf-8") as f:
        assert json.load(f) == [u"ceci n'est pas un canal"]


def test_le_depot_ordinaire_empile_toujours(paire):
    """La garde ne doit rien coder de plus : un canal absent se cree, un canal
    sain s'allonge, et l'ancien contenu reste dessous."""
    billet.deposer("alicent", "mj-aurore", u"le premier")
    billet.deposer("mj-aurore", "alicent", u"le second")
    e = _entrees(paire)
    assert [x["texte"] for x in e] == [u"le premier", u"le second"]
    assert [x["de"] for x in e] == ["alicent", "mj-aurore"]
    assert e[0]["date"] == {"annee": 129, "lune": 4, "jour": 4}


def test_le_depot_conserve_contexte_et_ref(paire):
    billet.deposer("alicent", "mj-aurore", u"le mot lié",
                   contexte_id="23030", ref="r-parole")
    entree = _entrees(paire)[0]
    assert entree["contexte_id"] == "23030"
    assert entree["ref"] == "r-parole"


def test_verser_histoire_conserve_ce_qui_etait_la(paire):
    """Le SECOND ecrivain du meme fichier. Il tronquait pareil : sa correction
    est de la meme main, sinon la fenetre restait ouverte d'un cote."""
    billet.deposer("alicent", "mj-aurore", u"le billet du jour")
    chambre.verser_histoire("alicent", "mj-aurore", [
        {"de": "alicent", "date": {"annee": 129, "lune": 3, "jour": 1},
         "texte": u"une vieille memoire"}])
    assert [x["texte"] for x in _entrees(paire)] == [
        u"une vieille memoire", u"le billet du jour"]
