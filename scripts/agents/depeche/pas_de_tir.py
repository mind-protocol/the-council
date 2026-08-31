# -*- coding: utf-8 -*-
"""PAS-DE-TIR — la memoire materialisee pour un reveil.

Sorti de mission.py le 31.8.2026 (plafond des 500 lignes) : mission.py garde
le texte de mission et l'appel d'agent ; ici vit ce qu'on pose sur le
disque du pas-de-tir avant le depart.
"""
import io
import os

from etat.expose import tables

from agents.depeche.brief import RACINE


def poser_la_memoire(neutre, qui, contexte=None):
    """Materialise au pas-de-tir ce que le message ne porte plus.

    LE PENDANT OBLIGE DE LA COMPRESSION. Sortir les croyances et les pensees
    du message ne vaut que si elles EXISTENT quelque part qu'il puisse ouvrir :
    un pointeur vers rien est pire qu'un percept trop long. Deux fichiers,
    ecrits ici parce que ce sont des lectures de `etat/` mises en forme pour
    lui — sa chambre, elle, est a lui, et nous n'y ecrivons pas sa memoire.

    Rend {croyances, pensees} : le nombre de lignes posees de chaque cote.
    """
    dossier = os.path.join(neutre, "ma-memoire")
    os.makedirs(dossier, exist_ok=True)
    # `contexte` est un confort, pas une dependance : tous les appels explicites
    # ne l'ont pas sous la main,
    # et un fichier qui manque parce qu'un argument manquait serait exactement
    # le pointeur mort qu'on cherche a eviter. A defaut, on relit la tete.
    intention = (contexte or {}).get("intention")
    if not intention:
        tetes = tables.lire(os.path.join(RACINE, "etat", "intentions.json"), [])
        if isinstance(tetes, dict):
            tetes = tetes.get("intentions") or []
        intention = next((t for t in tetes
                          if isinstance(t, dict)
                          and t.get("personnage_id") == qui), {})

    croyances = [str(x) for x in (intention.get("croyances") or []) if x]
    if croyances:
        with io.open(os.path.join(dossier, "ce-que-je-tiens-pour-vrai.txt"),
                     "w", encoding="utf-8", newline=chr(10)) as f:
            f.write("CE QUE JE TIENS POUR VRAI" + chr(10))
            f.write("La derniere en tete. Rien ici n'est prouve : c'est ce que"
                    " je crois," + chr(10) + "et j'ai le droit de me tromper."
                    + chr(10) * 2)
            for x in croyances:
                f.write("- " + x + chr(10) * 2)

    pensees = [p for p in _pensees_de(qui)]
    if pensees:
        with io.open(os.path.join(dossier, "ce-que-jai-appris.txt"), "w",
                     encoding="utf-8", newline=chr(10)) as f:
            f.write("CE QUE J'AI APPRIS" + chr(10))
            f.write("Mes pensees datees, la plus recente en tete." + chr(10) * 2)
            for x in pensees:
                d = x.get("date") or {}
                f.write("[%s.%s.%s] %s" % (d.get("annee"), d.get("lune"),
                                           d.get("jour"),
                                           str(x.get("texte") or "")))
                if x.get("source"):
                    f.write(chr(10) + "   (source : %s)" % x["source"])
                f.write(chr(10) * 2)
    return {"croyances": len(croyances), "pensees": len(pensees)}


def _pensees_de(qui):
    """Ses pensees, la plus recente en tete. Lecture par la porte."""
    d = tables.lire(os.path.join(RACINE, "etat", "pensees.json"), [])
    if isinstance(d, dict):
        d = d.get("pensees") or []
    siennes = [p for p in d if isinstance(p, dict) and p.get("qui") == qui]

    def rang(p):
        j = p.get("date") or {}
        return (j.get("annee", 0), j.get("lune", 0), j.get("jour", 0))
    return sorted(siennes, key=rang, reverse=True)
