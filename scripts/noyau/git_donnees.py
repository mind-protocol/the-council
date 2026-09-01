# -*- coding: utf-8 -*-
"""Snapshot Git cohérent de l'état vivant et des chambres."""
import hashlib
import json
import os
import subprocess


RACINES = ("etat", "chambres")


def inclus(chemin):
    p = chemin.replace("\\", "/")
    if not any(p == r or p.startswith(r + "/") for r in RACINES):
        return False
    if p.endswith(".lock") or "/.lock" in p or p.endswith(".tmp"):
        return False
    if p.startswith("etat/histoire/empreintes") and p.endswith(".json"):
        return False
    return True


def valider(chemin):
    """Valide les formats structurés ; les autres documents restent opaques."""
    if not os.path.exists(chemin):
        return
    if chemin.lower().endswith(".json"):
        try:
            with open(chemin, encoding="utf-8-sig") as f:
                json.load(f)
        except ValueError as exc:
            raise ValueError("%s: %s" % (chemin, exc))
    elif chemin.lower().endswith(".jsonl"):
        with open(chemin, encoding="utf-8-sig") as f:
            for numero, ligne in enumerate(f, 1):
                if ligne.strip():
                    try:
                        json.loads(ligne)
                    except ValueError as exc:
                        raise ValueError("%s:%d: %s" % (chemin, numero, exc))


def empreinte(chemin):
    if not os.path.exists(chemin):
        return "ABSENT"
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


def lancer(racine, *args, check=True):
    return subprocess.run(
        ["git"] + list(args), cwd=racine, check=check,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8")


def fichiers(racine):
    rep = lancer(racine, "ls-files", "-z", "--cached", "--others",
                 "--exclude-standard", "--", *RACINES)
    return sorted(p for p in rep.stdout.split("\0") if p and inclus(p))


def photographie(racine, chemins):
    return {p: empreinte(os.path.join(racine, p)) for p in chemins}


def changements(racine):
    rep = lancer(racine, "status", "--porcelain", "-z",
                 "--untracked-files=all", "--", *RACINES)
    resultat = []
    for entree in rep.stdout.split("\0"):
        if len(entree) >= 4:
            chemin = entree[3:]
            if " -> " in chemin:
                chemin = chemin.split(" -> ", 1)[1]
            if inclus(chemin):
                resultat.append(chemin)
    return sorted(set(resultat))


def index_propre(racine):
    return lancer(racine, "diff", "--cached", "--quiet",
                  check=False).returncode == 0


def ajouter(racine):
    lancer(racine, "add", "-A", "--", "etat", "chambres",
           ":(exclude,glob)etat/**/*.lock",
           ":(exclude,glob)etat/**/*.tmp",
           ":(exclude,glob)etat/histoire/empreintes*.json")


def destager(racine):
    lancer(racine, "restore", "--staged", "--", "etat", "chambres",
           check=False)
