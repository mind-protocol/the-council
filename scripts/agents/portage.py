# -*- coding: utf-8 -*-
"""PORTAGE — les registres portes au reveil du MJ (D.34).

Le MJ repond depuis l'etat seulement ; quand le message du joueur nomme des
nombres et des noms propres, le LANCEUR (zone.main, hors sandbox) va voir ce
que les registres en arretent et joint la matiere au mot du reveil — le MJ
ouvre son audience avec les lignes sous la main au lieu de partir les
chercher.

La recherche est celle de matiere.dossier_registres (D.36 : rend
(lignes, voisines, ailleurs), filtre CONJONCTIF sur les sujets). Jamais
bloquant : un inbox vide, un JSON casse ou une extraction vide n'ajoutent
rien — la matiere est un confort, jamais une condition.
"""
import io
import json
import os
import re

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

LIGNES_MAX = 6      # au-dela on redevient un mur
CELLULE_MAX = 200   # signes par ligne rendue

# Des majuscules qui ne nomment personne : les demarrages de phrase usuels.
_VIDES = {"le", "la", "les", "un", "une", "des", "je", "tu", "il", "elle",
          "on", "nous", "vous", "ils", "elles", "ce", "cette", "ces", "mon",
          "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "et", "ou",
          "mais", "donc", "que", "qui", "quoi", "dans", "pour", "avec",
          "sans", "sur", "sous", "vers", "chez", "si", "quand", "comme"}


def sujets_du_texte(texte):
    """Les nombres et les noms propres d'un message, normalises
    (matiere.sans_accents) — ce qu'on peut chercher dans un registre."""
    from agents import matiere
    sujets = []
    for nombre in re.findall(r"\d+", texte or u""):
        if nombre not in sujets:
            sujets.append(nombre)
    for mot in re.findall(u"\\b[A-ZÀ-Ý][\\wà-ÿ\\-]{2,}\\b", texte or u""):
        s = matiere.sans_accents(mot)
        if s not in _VIDES and s not in sujets:
            sujets.append(s)
    return sujets[:8]


def matiere_du_message(personnage):
    """La section « CE QUE LES REGISTRES ARRETENT » pour les messages du
    personnage en inbox (les fichiers action-*.json presents sont les non
    traites : le MJ les supprime en les depouillant) — ou u"" si rien ne
    s'y prete."""
    try:
        from agents import matiere
        dossier = os.path.join(RACINE, "etat", "inbox", personnage)
        if not os.path.isdir(dossier):
            return u""
        textes = []
        for nom in sorted(os.listdir(dossier), reverse=True):
            if not (nom.startswith("action-") and nom.endswith(".json")):
                continue
            try:
                with io.open(os.path.join(dossier, nom),
                             encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, dict) and d.get("texte"):
                    textes.append(str(d["texte"]))
            except Exception:
                continue
        if not textes:
            return u""
        sujets = sujets_du_texte(u" ".join(textes))
        if not sujets:
            return u""
        # Tous les sujets d'abord (le filtre est conjonctif) ; si rien ne
        # porte tout, chaque sujet seul, jusqu'au plafond. Un nombre seul ne
        # se cherche jamais : la recherche est en sous-chaine, et « 9 » se
        # trouve dans chaque numero de piece (mesure au banc du 31.8).
        lignes, _, _ = matiere.dossier_registres(sujets)
        if not lignes and len(sujets) > 1:
            for s in sujets:
                if s.isdigit():
                    continue
                seules, _, _ = matiere.dossier_registres([s])
                lignes.extend(x for x in seules if x not in lignes)
                if len(lignes) >= LIGNES_MAX:
                    break
        if not lignes:
            return u""
        rendues = []
        for volume, table, cellules in lignes[:LIGNES_MAX]:
            texte = u" | ".join(str(c) for c in cellules)
            if len(texte) > CELLULE_MAX:
                texte = texte[:CELLULE_MAX] + u"…"
            rendues.append(u"  · [%s / %s] %s" % (volume, table or u"—",
                                                  texte))
        return (u"\nCE QUE LES REGISTRES ARRETENT sur son message :\n"
                + u"\n".join(rendues) + u"\n")
    except Exception:
        return u""
