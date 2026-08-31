# -*- coding: utf-8 -*-
"""La regence — ce qu'un siege vacant a le droit de faire, et ce qu'il rend.

    python scripts/regence.py                          # l'etat des sieges en regence
    python scripts/regence.py --clause rhaenyra        # la clause a poser dans sa tete
    python scripts/regence.py --poser rhaenyra --vraiment
    python scripts/regence.py --verifier <rapport.json>   # passer un rapport au crible
    python scripts/regence.py --compte-rendu rhaenyra  # ce qu'on herite en se rasseyant

POURQUOI. Un siege vacant a deja une tete (`intentions.json`, garde de
`sieges.py`) et le moteur d'activation (`boucle_activation.py`) l'elit deja
comme n'importe quel acteur : il n'est exclu que tant qu'il est OCCUPE. Ce qui
manquait n'etait donc pas un second moteur, c'etaient deux choses :

  1. UNE LIGNE QU'IL NE FRANCHIT PAS. Un homme de maison qui se trompe coute
     une journee ; un SIEGE qui se trompe engage le joueur pour le reste de la
     partie. Prêter un serment, marier quelqu'un, livrer bataille, faire tuer,
     declarer une trahison, se rendre, ceder une place forte : ces sept-la ne
     se defont pas, et le joueur les retrouverait faites en revenant. On les
     ecrit dans sa tete (il le SAIT) et on les verifie a la validation du
     rapport (il ne peut PAS, meme s'il l'oublie).
  2. UNE PASSATION. Ce qui a ete decide en son absence, par qui, quand, et ce
     qui l'engage desormais — persiste dans `etat/joueurs/<id>/regence.jsonl`,
     rendu quand il se rassoit.

La detection est LEXICALE, et ce n'est pas un aveu de faiblesse : le rapport
d'activation est de la prose francaise arbitree par le narrateur, il n'y a
rien d'autre a lire. Elle est donc reglee large et elle se trompe dans le sens
sur : un rapport refuse a tort coute un passage de correction (l'homme se
rabat et recommence), un rapport passe a tort coute la partie. On garde aussi
les evitements (« il n'a PAS prete serment ») pour ne pas refuser une phrase
qui dit precisement qu'on s'est arrete a la ligne.
"""
from __future__ import print_function

import argparse
import datetime as dt
import io
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ETAT = os.path.join(RACINE, "etat")


from temps.expose import occupation  # qui est ASSIS — mesure, pas drapeau
from etat.expose import tables  # LA PORTE de etat/ : une lecture, une ecriture, une semantique d'erreur


# --------------------------------------------------------------------------
# Lecture
# --------------------------------------------------------------------------


def lire_json(chemin, defaut):
    """Une seule porte, une seule semantique — voir `scripts/tables.py`.

    Il y avait quatre `lire_json` dans ce depot et quatre comportements devant
    un fichier corrompu : deux plantaient, deux repartaient en silence sur le
    defaut. C'est tranche une fois pour toutes — un JSON abime PLANTE, seule
    l'absence rend le defaut.
    """
    return tables.lire(chemin, defaut)


def lire_table(nom, defaut):
    return lire_json(os.path.join(ETAT, nom + ".json"), defaut)


def sieges():
    roster = lire_table("joueurs", [])
    if isinstance(roster, dict):
        roster = roster.get("joueurs") or roster.get("sieges") or []
    return [s for s in roster if isinstance(s, dict) and s.get("personnage_id")]


def sieges_vacants():
    # LA MESURE, PAS LE DRAPEAU. Le garde des lignes rouges ne doit pas
    # dependre d'un champ que personne ne rebascule : un siege abandonne
    # depuis dix heures et reste marque `occupe` echapperait a la garde au
    # moment precis ou il est joue par la machine.
    return occupation.vacants()


def sieges_occupes():
    return occupation.occupes()


def est_en_regence(pid):
    """Ce personnage est-il un siege que personne n'occupe en ce moment ?"""
    return bool(pid) and pid in sieges_vacants()


def nom_de(pid):
    for s in sieges():
        if s["personnage_id"] == pid:
            return s.get("nom") or pid
    for p in lire_table("personnages", []) or []:
        if isinstance(p, dict) and p.get("id") == pid:
            return p.get("nom") or pid
    return pid


def date_du_monde():
    return (lire_table("monde", {}) or {}).get("date") or {}


def horloge_de(pid):
    return (lire_table("horloges", {}) or {}).get(pid) or date_du_monde()


def dire_date(d):
    if not d:
        return "date inconnue"
    return "an %s, %se lune, %se jour" % (
        d.get("annee"), d.get("lune"), d.get("jour"))


# --------------------------------------------------------------------------
# Les sept lignes rouges
# --------------------------------------------------------------------------
# Chaque ligne porte ce qu'elle interdit, de quoi la reconnaitre, et surtout
# CE QU'IL FAUT FAIRE A LA PLACE. Un garde-fou qui dit seulement non renvoie
# l'acteur dans le mur une seconde fois : on lui donne son rabattement.

LIGNES_ROUGES = [
    {
        "code": "serment",
        "quoi": "prêter ou rompre un serment, un hommage, une allégeance",
        "motifs": [
            # « jurer que » n'est pas un serment : c'est une assertion. On
            # n'attrape que le serment PRETE, avec son objet ou son rite.
            r"\bpr[êe]t(?:e|es|ent|er|é|ée|és|ées)\s+"
            r"(?:un\s+|le\s+|son\s+|leur\s+|ce\s+)?serment",
            r"\bserment\s+(?:pr[êe]t[ée]|donn[ée]|re[çc]u|scell[ée])\b",
            r"\bromp(?:t|re|u|ent)\s+(?:son|le|un|leur|ce)\s+serment",
            r"\bjur(?:e|er|ent|ons|é)\s+(?:fid[ée]lit[ée]|all[ée]geance|"
            r"ob[ée]issance|foi|de\s+servir|de\s+tenir|sur\s+les\s+dieux)",
            r"\bpr[êe]te(?:r)?\s+(?:foi|hommage|all[ée]geance)",
            r"\b(?:donne|engage|offre)\s+(?:sa|son|ma|mon)\s+(?:foi|parole\s+de\s+f[ée]al)",
            r"\bparjure\b",
            r"\bfait?\s+hommage\b",
            r"\bse\s+d[ée]lie\s+de\s+(?:son|ses)\s+serment",
        ],
        "rabattement": "préparer la forme du serment, réunir les témoins, "
                       "fixer une date — et laisser la parole elle-même au "
                       "retour de qui tient le siège",
    },
    {
        "code": "mariage",
        "quoi": "conclure un mariage, des fiançailles, promettre une main",
        "motifs": [
            r"\b[ée]pous(?:e|er|ent|ée|é)\b",
            r"\bmari(?:e|er|ent|ée|é)\b(?!\w)",
            r"\bmariage\b.{0,40}?\b(?:conclu|scell[ée]|c[ée]l[ée]br[ée]|"
            r"arr[êe]t[ée]|convenu|sign[ée])",
            r"\bfian[çc]ailles\b.{0,40}?\b(?:conclues|scell[ée]es|"
            r"arr[êe]t[ée]es|annonc[ée]es)",
            r"\bpromet(?:s|tre)?\s+la\s+main\b",
            r"\bc[ée]l[èe]bre\s+(?:les\s+)?noces\b",
        ],
        "rabattement": "sonder, chiffrer la dot, écrire le projet au registre "
                       "— aucune promesse donnée, aucun contrat scellé",
    },
    {
        "code": "bataille",
        "quoi": "livrer bataille, donner l'assaut, engager le combat",
        "motifs": [
            r"\b(?:livre|livrer|donne|donner)\s+(?:la\s+)?bataille\b",
            r"\bdonne(?:r)?\s+l'assaut\b",
            r"\bmonte(?:r|nt)?\s+[àa]\s+l'assaut\b",
            r"\bengage(?:r|nt)?\s+(?:le\s+)?combat\b",
            r"\bordonne\s+(?:la\s+)?charge\b",
            r"\bl[àa]che\s+le\s+dragon\s+sur\b",
            r"\bmet\s+le\s+feu\s+[àa]\s+la\s+ville\b",
            r"\bouvre\s+le\s+si[èe]ge\b",
            r"\bsonne\s+l'attaque\b",
            r"\bpasse\s+[àa]\s+l'abordage\b",
        ],
        "rabattement": "poster, reconnaître, chiffrer les forces, tenir la "
                       "position — le premier coup n'est pas de son ressort",
    },
    {
        "code": "mort",
        "quoi": "faire tuer, exécuter, mettre à mort",
        "motifs": [
            r"\b(?:fait|fais|faire)\s+(?:pendre|[ée]gorger|d[ée]capiter|ex[ée]cuter|tuer|noyer)\b",
            r"\bmet(?:tre|s)?\s+[àa]\s+mort\b",
            # « s'exécuter » veut dire obéir : on exige l'objet ou le rite.
            r"\bex[ée]cute(?:r|nt)?\s+(?:la\s+sentence|l'arr[êe]t|le\s+"
            r"prisonnier|la\s+condamn|le\s+jugement\s+de\s+mort)",
            r"\bex[ée]cution\s+(?:capitale|de\s+la\s+sentence)\b",
            r"\bassassin(?:e|er|ent|[ée])\b",
            r"\b[ée]gorge(?:r|nt)?\b",
            r"\bd[ée]capite(?:r|nt)?\b",
            r"\bempoisonne(?:r|nt)?\b",
            r"\bordonne\s+(?:sa|leur|la)\s+mort\b",
            r"\bcondamne\s+[àa]\s+(?:la\s+)?mort\b",
        ],
        "rabattement": "arrêter, garder au cachot, instruire, écrire le chef "
                       "d'accusation — la sentence attend qui tient le siège",
    },
    {
        "code": "trahison",
        "quoi": "déclarer une trahison, changer de camp, livrer quelqu'un",
        "motifs": [
            r"\btrahi(?:t|r|ssent|e)\b",
            r"\bpasse\s+(?:aux?\s+)?(?:Verts|l'ennemi|l'autre\s+camp)\b",
            r"\bchange\s+de\s+camp\b",
            r"\bfait?\s+d[ée]fection\b",
            r"\bd[ée]clare\s+(?:la\s+)?trahison\b",
            r"\bd[ée]nonce\s+publiquement\b",
            r"\blivre\s+\w+\s+(?:aux?|[àa])\s+(?:l'ennemi|Verts|Aegon|Alicent)\b",
            r"\brenie\s+(?:sa|la)\s+(?:reine|cause|maison)\b",
        ],
        "rabattement": "recueillir, vérifier, écrire ce qu'on soupçonne et à "
                       "qui on le doit — l'accusation publique attend",
    },
    {
        "code": "reddition",
        "quoi": "se rendre, capituler, déposer les armes",
        "motifs": [
            r"\bse\s+rend(?:re|ent)?\s+(?:[àa]|sans)\b",
            r"\breddition\b",
            r"\bcapitule(?:r|nt)?\b",
            r"\bcapitulation\b",
            r"\bd[ée]pose(?:r|nt)?\s+les\s+armes\b",
            r"\bhisse\s+(?:le\s+)?(?:drapeau\s+)?blanc\b",
            r"\bdemande\s+(?:les\s+)?termes\s+de\s+(?:la\s+)?reddition\b",
        ],
        "rabattement": "tenir, compter les vivres et les bras, ouvrir un "
                       "pourparler qui n'engage rien — et le dire tel quel",
    },
    {
        "code": "place-forte",
        "quoi": "céder, livrer ou ouvrir une place forte",
        "motifs": [
            r"\b(?:c[èe]de|c[ée]der|livre|livrer|rend|rendre|remet|remettre)\s+"
            r"(?:la\s+place|le\s+ch[âa]teau|la\s+forteresse|le\s+donjon|"
            r"la\s+citadelle|les\s+clefs|la\s+porte\s+de\s+mer)\b",
            r"\bouvre\s+les\s+portes\s+(?:[àa]|aux?)\b",
            r"\babandonne\s+(?:la\s+place|le\s+ch[âa]teau|l'[îi]le)\b",
            r"\b[ée]vacue\s+(?:la\s+place|le\s+ch[âa]teau|la\s+forteresse)\b",
        ],
        "rabattement": "barrer, doubler le guet, préparer l'évacuation des "
                       "gens — les clefs ne quittent pas la maison",
    },
]

# Ce qui, juste avant la formule, dit qu'on ne l'a PAS faite. On garde ces
# passages a part au lieu de refuser : « il n'a pas prêté serment » est
# exactement ce qu'on veut lire d'un siege en regence bien joue.
#
# L'ancrage compte AUTANT que la liste. Chercher « ne » n'importe ou dans la
# fenetre rendrait evitee toute phrase qui contient une negation ailleurs —
# « il refuse de fuir et donne l'assaut » deviendrait innocent. On exige donc
# que la marque soit juste avant la formule, a deux mots pres.
MARQUES_EVITEMENT = (
    r"ne|n'|pas|plus|jamais|rien|aucun\w*|sans|nul\w*|"
    r"refus\w*|s'abstien\w*|s'arr[êe]te|s'interdit|d[ée]cline|"
    r"diff[èe]re|ajourne|reporte|attend|laisse|garde|r[ée]serve|"
    r"avant\s+de|au\s+lieu\s+de|faute\s+de|[àa]\s+d[ée]faut\s+de|"
    r"si|au\s+cas\s+o[ùu]|hypoth[èe]se|supposer|faudrait|devrait|"
    r"aurait|pourrait|risque\s+de|menace\s+de|craint\s+de|"
    r"ne\s+peut|ne\s+veut|interdit\s+de|emp[êe]che\s+de|"
    # Nommer la decision, c'est deja ne pas la prendre.
    r"d[ée]cision|choix|question|possibilit[ée]|projet|hypoth[èe]se\s+de|"
    r"opportunit[ée]|[ée]ventualit[ée]|co[ûu]t\s+d|prix\s+d"
)
EVITEMENTS = re.compile(
    r"\b(?:%s)\b[^.;!?]{0,30}$" % MARQUES_EVITEMENT, re.IGNORECASE)
# Ce qui rapporte l'acte d'un AUTRE, ou d'un autre temps : « le registre dit
# que Borros a rompu son serment » n'engage pas le siege. Fenetre serree, et
# la completive exigee — sans quoi n'importe quel verbe de parole innocenterait
# la phrase qui le suit.
CITATIONS = re.compile(
    r"\b(?:dit|dis[ae]nt|rapporte|raconte|[ée]cri[tv]\w*|note|lit|apprend|"
    r"pr[ée]tend|assure|jure|se\s+souvient|selon)\b\s*(?:qu[e']|:)?"
    r"[^.;!?]{0,30}$", re.IGNORECASE)

FENETRE_EVITEMENT = 90  # caracteres relus en amont de la formule


def _passages(rapport):
    """Les endroits du rapport ou l'acteur dit ce qu'il a FAIT.

    On ne lit ni les sources touchees ni le dossier : citer un serment dans un
    registre n'est pas en preter un. On lit son verbe, ce qu'il dit avoir fait,
    l'etat qu'il declare produit, sa suite, et ce qu'il veut ecrire dans etat/.
    """
    activation = (rapport or {}).get("activation") or {}
    passages = []
    for activite in activation.get("activites") or []:
        if not isinstance(activite, dict):
            continue
        ordre = activite.get("ordre")
        action = activite.get("action") or {}
        for clef in ("verbe", "quoi", "comment"):
            if action.get(clef):
                passages.append(("activité %s · %s" % (ordre, clef),
                                 str(action[clef])))
        for resultat in activite.get("resultats_produits") or []:
            if not isinstance(resultat, dict):
                continue
            for clef in ("quoi", "apres"):
                valeur = resultat.get(clef)
                if isinstance(valeur, str) and valeur:
                    passages.append(("activité %s · résultat %s"
                                     % (ordre, clef), valeur))
        if activite.get("blocage"):
            passages.append(("activité %s · blocage" % ordre,
                             str(activite["blocage"])))
    if activation.get("suite"):
        passages.append(("la suite qu'il annonce", str(activation["suite"])))
    return passages


def _court(texte, n=160):
    texte = " ".join(str(texte or "").split())
    return texte if len(texte) <= n else texte[:n - 1] + "…"


def franchissements(rapport):
    """Rend (franchies, evitees) : la liste des lignes touchees et comment."""
    franchies, evitees = [], []
    for ou, texte in _passages(rapport):
        for ligne in LIGNES_ROUGES:
            fiche = None
            for motif in ligne["motifs"]:
                trouve = re.search(motif, texte, re.IGNORECASE)
                if trouve is None:
                    continue
                debut = max(0, trouve.start() - FENETRE_EVITEMENT)
                fiche = {
                    "code": ligne["code"],
                    "quoi": ligne["quoi"],
                    "rabattement": ligne["rabattement"],
                    "ou": ou,
                    "extrait": _court(
                        texte[max(0, trouve.start() - 60):trouve.end() + 60]),
                    "formule": trouve.group(0),
                    "evitee": evitement_dans(texte[debut:trouve.start()]),
                }
                # Une ligne franchie quelque part dans le passage prime sur
                # une occurrence evitee : on ne se rassure pas sur la premiere.
                if not fiche["evitee"]:
                    break
            if fiche is None:
                continue
            (evitees if fiche.pop("evitee") else franchies).append(fiche)
    return franchies, evitees


def evitement_dans(amont):
    """Vrai si ce qui precede la formule la nie, la diffère ou la cite."""
    amont = " ".join(str(amont or "").split())
    return bool(EVITEMENTS.search(amont)) or bool(CITATIONS.search(amont))


def texte_du_refus(pid, franchies):
    nom = nom_de(pid)
    lignes = [
        "RÉGENCE : ce rapport franchit une ligne que %s ne peut pas franchir "
        "en l'absence de qui tient le siège." % nom,
        "",
    ]
    for f in franchies:
        lignes.append("- %s (%s) — dans %s : « %s »"
                      % (f["quoi"], f["code"], f["ou"], f["extrait"]))
        lignes.append("  À la place : %s." % f["rabattement"])
    lignes.extend([
        "",
        "Reprends l'activation sans cet acte : garde la journée, garde le "
        "travail réel, remplace le geste irréversible par son rabattement, "
        "et dis explicitement dans le rapport ce qui a été laissé en "
        "suspens et pour qui. Rien d'autre n'est à changer.",
    ])
    return "\n".join(lignes)


def verifier_rapport_activation(pid, rapport, journaliser=None):
    """Le garde mecanique. Leve RuntimeError si le siege vacant a franchi.

    Appele par `boucle_activation.py` AVANT que les mutations soient ecrites
    dans `etat/` — un refus renvoie l'acteur corriger, il ne detruit pas sa
    journee. Sans effet sur les acteurs ordinaires et sur les sieges occupes.
    """
    if not est_en_regence(pid):
        return None
    franchies, evitees = franchissements(rapport)
    if journaliser and evitees:
        journaliser("regence.evitement", acteur=pid, nombre=len(evitees),
                    lignes=",".join(sorted({f["code"] for f in evitees})))
    if not franchies:
        return {"franchies": [], "evitees": evitees}
    if journaliser:
        journaliser("regence.refus", acteur=pid, nombre=len(franchies),
                    lignes=",".join(sorted({f["code"] for f in franchies})))
    raise RuntimeError(texte_du_refus(pid, franchies))



# La clause, la passation (le registre jsonl) et le main vivent dans
# regence_passation.py (meme container) ; on les rattache ici pour que
# `regence.consigner`, `regence.clause_posee`, `regence.compte_rendu`,
# `regence.remettre` et la CLI restent au meme endroit qu'avant.
from temps.regence_passation import (  # noqa: E402,F401
    clause_croyance, clause_declencheur, clause_posee, tete_de,
    poser_clause, registre_de, lire_registre, consigner, compte_rendu,
    remettre, etat_des_regences, main)
