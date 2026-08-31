# -*- coding: utf-8 -*-
"""PAS-DE-TIR — ce qu'on materialise dans le repertoire neutre d'un reveil :
l'etagere (ses volumes en fichiers) et la memoire (croyances, pensees).

Sorti de mission.py le 31.8.2026 (plafond des 500 lignes) : mission.py garde
le texte de mission et l'appel d'agent ; ici vit ce qu'on pose sur le
disque du pas-de-tir avant le depart.
"""
import io
import os

from etat.expose import tables

from agents.depeche.brief import RACINE, livre


def poser_letagere(neutre, qui):
    """Materialise ses volumes en fichiers, un par volume, dans son dossier.

    C'EST LE SELECTEUR, ET IL EST PHYSIQUE. On aurait pu lui donner le
    lecteur en Bash et lui dire de s'en servir ; mais un outil qu'on autorise
    par motif de commande se contourne, et une consigne ne verrouille rien.
    La ou il travaille, il n'EXISTE que ce qu'il peut ouvrir. Le carnet de la
    reine n'est pas refuse : il n'est pas la.

    Effet de bord heureux : Grep sur ./livres/ lui donne la recherche
    plein-texte de son etagere, ce qui est exactement le geste d'un homme qui
    cherche dans ses registres — et qui evite les 547 000 jetons de
    etat/books.json, ou il s'est noye pendant huit minutes.
    """
    dossier = os.path.join(neutre, "livres")
    os.makedirs(dossier)
    n = 0
    index = []
    for b in livre.etagere(qui):
        with io.open(os.path.join(dossier, "%s.txt" % b.get("id")), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(livre.rendre(b, large=True))
        index.append("%-34s %s%s" % (
            b.get("id"), b.get("titre") or "",
            ("   (porte par %s)" % b["acteur_id"]) if b.get("acteur_id")
            else ("   (pose : %s)" % b["salle_id"]) if b.get("salle_id")
            else ""))
        n += 1
    # SES PROPRES VOLUMES, QUI N'Y ETAIENT PAS. `livre.etagere` lit
    # `etat/books` — la bibliotheque commune — et rien d'autre. Un homme
    # recevait donc 82 volumes de la maison et PAS LE SIEN : sa prise en main,
    # posee dans `chambres/<lui>/books/`, n'existait pas la ou il travaille.
    # On les copie tels quels, en JSON : c'est sa main qui les ecrira, et un
    # rendu ne se reecrit pas.
    sien = os.path.join(RACINE, "chambres", qui, "books")
    for nom in sorted(os.listdir(sien)) if os.path.isdir(sien) else []:
        if not nom.endswith(".json"):
            continue
        ident = nom[:-5]
        try:
            texte = io.open(os.path.join(sien, nom), encoding="utf-8").read()
        except IOError:
            continue
        with io.open(os.path.join(dossier, "%s.json" % ident), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(texte)
        # ET LE MEME, RENDU LISIBLE. Mesure du 31.8 : DEUX hommes sur deux —
        # aldon-hask puis tobb — se sont ecrit un lecteur JSON dans leurs
        # brouillons. La cause etait ici : ils recevaient 82 volumes de la
        # maison en TEXTE et leur propre cahier en JSON BRUT, seul illisible
        # de toute l'etagere. « Un rendu ne se reecrit pas » est vrai pour
        # l'ECRITURE et faux pour la lecture : on sert les deux formes, et
        # l'index dit laquelle sert a quoi.
        try:
            import json as _json
            rendu = livre.rendre(_json.loads(texte), large=True)
            with io.open(os.path.join(dossier, "%s.txt" % ident), "w",
                         encoding="utf-8", newline="\n") as f:
                f.write(rendu)
        except Exception:
            pass
        index.append("%-34s %s" % (
            ident,
            u"— A TOI. Lis le .txt, ecris dans ta chambre (le .json)."))
        n += 1

    # L'INDEX EST UN FICHIER, PLUS UN PARAGRAPHE DU REVEIL. Il pesait 7,2 Ko
    # dans le message pour dire des noms de fichiers ; il est ici, a cote de
    # ce qu'il indexe, et c'est la ou un homme le cherche.
    with io.open(os.path.join(dossier, "_index.txt"), "w", encoding="utf-8",
                 newline="\n") as f:
        f.write("LES VOLUMES A TA PORTEE — %d" % n + chr(10))
        f.write("Chacun s'ouvre sous ./livres/<identifiant>.txt ;"
                " Grep cherche dans leur texte." + chr(10) * 2)
        f.write((chr(10)).join(sorted(index)) + chr(10))
    return n


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
    # `contexte` est un confort, pas une dependance : les deux chemins d'appel
    # (depeche et boucle d'activation) ne l'ont pas tous les deux sous la main,
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
