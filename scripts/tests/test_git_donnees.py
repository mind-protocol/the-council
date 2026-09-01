# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys

import pytest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOYAU = os.path.join(SCRIPTS, "noyau")
if NOYAU not in sys.path:
    sys.path.insert(0, NOYAU)

import git_donnees


def test_le_snapshot_ne_prend_que_donnees_sans_verrous_ni_caches():
    assert git_donnees.inclus("etat/monde.json")
    assert git_donnees.inclus("chambres/mj/claude.md")
    assert not git_donnees.inclus("scripts/agents/mj.py")
    assert not git_donnees.inclus("etat/activations/.boucle.lock")
    assert not git_donnees.inclus("etat/histoire/empreintes.json")


def test_validation_json_et_jsonl(tmp_path):
    objet = tmp_path / "objet.json"
    lignes = tmp_path / "lignes.jsonl"
    objet.write_text(json.dumps({"ok": True}), encoding="utf-8")
    lignes.write_text('{"a": 1}\n{"b": 2}\n', encoding="utf-8")
    git_donnees.valider(str(objet))
    git_donnees.valider(str(lignes))


def test_jsonl_invalide_n_est_pas_pousse(tmp_path):
    lignes = tmp_path / "casse.jsonl"
    lignes.write_text('{"ok": 1}\npas du json\n', encoding="utf-8")
    with pytest.raises(ValueError, match=":2:"):
        git_donnees.valider(str(lignes))


def test_json_windows_avec_bom_est_accepte(tmp_path):
    objet = tmp_path / "settings.json"
    objet.write_text('{"ok": true}', encoding="utf-8-sig")
    git_donnees.valider(str(objet))


def test_empreinte_detecte_un_fichier_qui_bouge(tmp_path):
    chemin = tmp_path / "monde.json"
    chemin.write_text("un", encoding="utf-8")
    avant = git_donnees.empreinte(str(chemin))
    chemin.write_text("deux", encoding="utf-8")
    assert git_donnees.empreinte(str(chemin)) != avant


def test_git_add_ne_prepare_que_les_donnees_autorisees(tmp_path):
    racine = str(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=racine, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"],
                   cwd=racine, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=racine,
                   check=True)
    for dossier in ("etat/activations", "etat/histoire", "chambres/mj",
                    "scripts"):
        os.makedirs(os.path.join(racine, dossier), exist_ok=True)
    fichiers = {
        "etat/monde.json": "{}",
        "etat/activations/.boucle.lock": "1",
        "etat/histoire/empreintes.json": "{}",
        "chambres/mj/claude.md": "ancien",
        "scripts/code.py": "ancien",
    }
    for relatif, texte in fichiers.items():
        with open(os.path.join(racine, relatif), "w", encoding="utf-8") as f:
            f.write(texte)
    subprocess.run(["git", "add", "."], cwd=racine, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=racine, check=True)
    for relatif in fichiers:
        with open(os.path.join(racine, relatif), "a", encoding="utf-8") as f:
            f.write("\nnouveau")

    git_donnees.ajouter(racine)
    stages = git_donnees.lancer(
        racine, "diff", "--cached", "--name-only").stdout.splitlines()
    assert stages == ["chambres/mj/claude.md", "etat/monde.json"]
