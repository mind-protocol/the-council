# -*- coding: utf-8 -*-
import os
import sys
import threading

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from scene import flux_transport
from scene import tunnel


def test_empreinte_ignore_les_estampilles_mais_pas_le_contenu():
    a = {"type": "recit", "texte": "La porte s'ouvre.", "pour": "rhaenyra",
         "heure": "7h06", "date": {"jour": 12}}
    b = dict(a, heure="7h07", date={"jour": 12, "minute": 427})
    c = dict(a, texte="La porte se ferme.")
    assert flux_transport.empreinte(a) == flux_transport.empreinte(b)
    assert flux_transport.empreinte(a) != flux_transport.empreinte(c)


def test_memoire_ne_garde_que_la_fenetre(tmp_path):
    chemin = str(tmp_path / "dedup.json")
    flux_transport.ecrire(chemin, {"recent": 100, "vieux": 1})
    assert flux_transport.lire(chemin, maintenant=120, ttl=60) == {"recent": 100}


def test_le_verrou_serialise_deux_plumes(tmp_path):
    runtime = str(tmp_path / "flux")
    libere = flux_transport.prendre_verrou(runtime, timeout=1)
    resultat = []

    def seconde_plume():
        try:
            flux_transport.prendre_verrou(runtime, timeout=.05, stale=120)
        except RuntimeError:
            resultat.append("bloquee")

    fil = threading.Thread(target=seconde_plume)
    fil.start()
    fil.join()
    libere()
    assert resultat == ["bloquee"]


def test_le_debit_de_1500_caracteres_cadence_plusieurs_messages():
    items = [
        {"type": "recit", "texte": "a" * 500},
        {"type": "replique", "texte": "b" * 500},
        {"type": "geste", "texte": "c" * 500},
    ]
    assert [tunnel.cadencer(it) for it in items] == [20, 20, 20]
    assert sum(it["delai_s"] for it in items) == 60


def test_le_debit_ne_touche_pas_le_joueur_ni_un_delai_plus_long():
    joueur = {"type": "vous", "texte": "a" * 2000}
    lent = {"type": "recit", "texte": "b" * 100, "delai_s": 12}
    assert tunnel.cadencer(joueur) == 0
    assert "delai_s" not in joueur
    assert tunnel.cadencer(lent) == 12


def test_le_debit_couvre_aussi_reponses_et_suites_du_mj():
    reponse = {"type": "reponse", "texte": "a" * 250}
    suites = {"type": "suites", "texte": "b" * 250, "options": []}
    assert tunnel.cadencer(reponse) == 10
    assert tunnel.cadencer(suites) == 10
