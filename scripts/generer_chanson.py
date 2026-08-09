# -*- coding: utf-8 -*-
"""generer_chanson.py — envoyer une fiche de `musiques/` a Suno, et rapatrier l'audio.
#
# Usage :
#     python scripts/generer_chanson.py musiques/le-manteau-d-or.md
#     python scripts/generer_chanson.py --toutes          (toutes les fiches sans audio)
#     python scripts/generer_chanson.py <fiche> --sec     (montre ce qui partirait, n'appelle rien)
#
# POURQUOI CE SCRIPT EXISTE, ET CE QU'IL NE PEUT PAS FAIRE. Suno n'a pas d'API
# publique officielle : on passe forcement par une passerelle tierce, avec un
# compte et une cle a soi. Le script ne choisit pas la passerelle pour toi — il
# lit son adresse dans l'environnement, et refuse proprement si elle manque,
# plutot que de deviner un service et de le faire payer a quelqu'un.
#
# Dans .env :
#     SUNO_API_KEY=...
#     SUNO_API_URL=https://api.example.com   (racine de la passerelle)
#     SUNO_MODELE=V4_5                       (facultatif)
#
# La fiche est la source unique : le titre en tete, `## Les paroles` et
# `## Le prompt musical` en donnent les trois champs. Rien a ressaisir, et ce
# qu'on a ecrit dans musiques/ est exactement ce qui part.
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "musiques"
ATTENTE_MAX = 600          # dix minutes : au-dela, la passerelle a un probleme
PAS = 15


def env(nom, defaut=None):
    """La cle vient de l'environnement, ou du .env a la racine — jamais du code."""
    if os.environ.get(nom):
        return os.environ[nom]
    fichier = RACINE / ".env"
    if fichier.exists():
        for ligne in io.open(fichier, encoding="utf-8"):
            if ligne.strip().startswith(nom + "="):
                return ligne.split("=", 1)[1].strip().strip('"').strip("'")
    return defaut


def depecer(chemin):
    """Titre, paroles et prompt musical, tires de la fiche .md telle qu'ecrite."""
    texte = io.open(chemin, encoding="utf-8").read()
    titre = re.search(r"^#\s+(.+)$", texte, re.M)
    sections = dict(re.findall(r"^##\s+(.+?)\n(.*?)(?=^## |\Z)", texte, re.M | re.S))
    def section(*noms):
        for n in noms:
            for cle, corps in sections.items():
                if n.lower() in cle.lower():
                    # composer.py pose les blocs entre barrieres ``` : elles sont
                    # de la mise en page, pas du contenu, et Suno les chanterait.
                    return re.sub(r"^```.*?$", "", corps, flags=re.M).strip()
        return ""
    return {
        "titre": titre.group(1).strip() if titre else Path(chemin).stem,
        "paroles": section("paroles"),
        "style": section("prompt musical", "style"),
    }


def appeler(url, cle, charge):
    requete = urllib.request.Request(
        url, data=json.dumps(charge).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + cle})
    with urllib.request.urlopen(requete, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def lire(url, cle):
    requete = urllib.request.Request(url, headers={"Authorization": "Bearer " + cle})
    with urllib.request.urlopen(requete, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def pistes(reponse):
    """Les passerelles n'ont pas toutes le meme emballage : on cherche l'audio."""
    trouvees = []
    def fouiller(o):
        if isinstance(o, dict):
            for c in ("audioUrl", "audio_url", "streamAudioUrl", "source_audio_url"):
                if o.get(c):
                    trouvees.append((o.get("title") or "", o[c]))
                    return
            for v in o.values():
                fouiller(v)
        elif isinstance(o, list):
            for v in o:
                fouiller(v)
    fouiller(reponse)
    return trouvees


def engendrer(chemin, sec=False):
    fiche = depecer(chemin)
    if not fiche["paroles"] or not fiche["style"]:
        print("  IGNOREE — il manque les paroles ou le prompt : %s" % chemin)
        return
    if len(fiche["style"]) > 800:
        print("  IGNOREE — prompt musical au-dela de 800 caracteres : %s" % chemin)
        return

    charge = {"customMode": True, "instrumental": False,
              "prompt": fiche["paroles"], "style": fiche["style"],
              "title": fiche["titre"], "model": env("SUNO_MODELE", "V4_5")}
    if sec:
        print(json.dumps(charge, ensure_ascii=False, indent=2)[:1200])
        return

    cle, racine = env("SUNO_API_KEY"), env("SUNO_API_URL")
    if not cle or not racine:
        raise SystemExit(
            "Il manque SUNO_API_KEY et/ou SUNO_API_URL dans .env.\n"
            "Suno n'ayant pas d'API officielle, l'adresse de la passerelle doit etre\n"
            "declaree a la main : ce script n'en choisit pas une a ta place.")
    racine = racine.rstrip("/")

    print("  envoi : %s" % fiche["titre"])
    reponse = appeler(racine + "/api/v1/generate", cle, charge)
    tache = (reponse.get("data") or {}).get("taskId") or reponse.get("taskId")
    if not tache:
        raise SystemExit("  la passerelle n'a pas rendu de taskId : %s" % json.dumps(reponse)[:400])

    debut = time.time()
    while time.time() - debut < ATTENTE_MAX:
        time.sleep(PAS)
        etat = lire(racine + "/api/v1/generate/record-info?taskId=" + tache, cle)
        trouvees = pistes(etat)
        if trouvees:
            base = Path(chemin).stem
            for i, (nom, url) in enumerate(trouvees, 1):
                sortie = DOSSIER / ("%s-%d.mp3" % (base, i))
                with urllib.request.urlopen(url, timeout=180) as flux:
                    sortie.write_bytes(flux.read())
                print("  ecrit : %s   (%s)" % (sortie, nom or "sans titre"))
            return
        print("  ... en cours (%d s)" % int(time.time() - debut))
    print("  ABANDON — rien rendu en %d s." % ATTENTE_MAX)


def main():
    args = sys.argv[1:]
    sec = "--sec" in args
    args = [a for a in args if a != "--sec"]
    if "--toutes" in args:
        fiches = [f for f in sorted(DOSSIER.glob("*.md"))
                  if not list(DOSSIER.glob(f.stem + "-*.mp3"))]
    else:
        fiches = [Path(a) for a in args]
    if not fiches:
        raise SystemExit(__doc__)
    for f in fiches:
        print(f.name)
        engendrer(f, sec)


if __name__ == "__main__":
    main()
