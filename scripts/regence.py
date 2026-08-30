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

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import occupation  # qui est ASSIS — mesure, pas drapeau
import tables  # LA PORTE de etat/ : une lecture, une ecriture, une semantique d'erreur


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
    for mutation in (rapport or {}).get("mutations_proposees") or []:
        if not isinstance(mutation, dict):
            continue
        valeur = mutation.get("valeur")
        if not isinstance(valeur, str):
            valeur = json.dumps(valeur, ensure_ascii=False)
        passages.append(("mutation %s/%s sur %s"
                         % (mutation.get("table"), mutation.get("operation"),
                            mutation.get("cible")), valeur))
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


# --------------------------------------------------------------------------
# La clause dans sa tete
# --------------------------------------------------------------------------
# Le garde mecanique refuse ; la clause fait qu'il n'essaie pas. Les deux sont
# necessaires et ne se remplacent pas. On l'ecrit dans les champs du schema —
# une croyance et un declencheur —, jamais dans un champ invente.

def clause_croyance(pid):
    return (u"Je ne tiens la place que jusqu'au retour de celui qui décide : "
            u"je peux tout préparer, rien conclure d'irréversible. Pas de "
            u"serment prêté ni rompu, pas de mariage, pas de bataille livrée, "
            u"pas de mort ordonnée, pas de trahison déclarée, pas de "
            u"reddition, pas de place forte cédée. Ce qui engage pour "
            u"toujours attend, et j'écris pour qui reviendra.")


def clause_declencheur():
    return {
        "si": u"une affaire ne peut avancer qu'en prêtant ou rompant un "
              u"serment, en concluant un mariage, en livrant bataille, en "
              u"faisant tuer quelqu'un, en déclarant une trahison, en se "
              u"rendant ou en cédant une place forte",
        "alors": u"je m'arrête à la ligne : je prépare tout ce qui peut "
                 u"l'être, je note au clair ce qui manque, à qui la décision "
                 u"revient et ce qu'elle coûtera de retard, et je laisse "
                 u"l'acte entier à celui dont c'est le siège",
        "une_fois": False,
    }


def clause_posee(tete):
    """La tete porte-t-elle deja la clause ? On la reconnait a sa signature."""
    tete = tete or {}
    signature = u"irréversible"
    for croyance in tete.get("croyances") or []:
        if signature in str(croyance):
            return True
    for declencheur in tete.get("declencheurs") or []:
        if isinstance(declencheur, dict) and \
                u"serment" in str(declencheur.get("si") or "") and \
                u"siège" in str(declencheur.get("alors") or ""):
            return True
    return False


def tete_de(pid):
    for tete in lire_table("intentions", []) or []:
        if isinstance(tete, dict) and tete.get("personnage_id") == pid:
            return tete
    return None


def poser_clause(pid, vraiment):
    """Ecrit la clause dans la tete du siege vacant, sans toucher au reste.

    Relecture juste avant l'ecriture, remplacement de la SEULE entree du
    personnage : une autre session qui edite une autre tete pendant ce temps
    ne perd rien.
    """
    if not est_en_regence(pid):
        sys.exit("'%s' n'est pas un siège vacant : rien à poser." % pid)
    tete = tete_de(pid)
    if tete is None:
        sys.exit("'%s' n'a pas de tête dans intentions.json — écrivez-la "
                 "d'abord (voir sieges.py)." % pid)
    if clause_posee(tete):
        print("la clause de régence est déjà dans la tête de %s." % pid)
        return
    print("à poser dans la tête de %s :" % pid)
    print("  croyance   : " + clause_croyance(pid))
    print("  déclencheur: si " + clause_declencheur()["si"])
    if not vraiment:
        print("\n(rien n'a été écrit — ajoutez --vraiment)")
        return
    chemin = os.path.join(ETAT, "intentions.json")
    with io.open(chemin, encoding="utf-8") as f:
        tetes = json.load(f)
    touche = False
    for entree in tetes:
        if not isinstance(entree, dict) or \
                entree.get("personnage_id") != pid:
            continue
        if clause_posee(entree):
            print("posée entre-temps par une autre session — rien à faire.")
            return
        entree.setdefault("croyances", []).append(clause_croyance(pid))
        entree.setdefault("declencheurs", []).append(clause_declencheur())
        # `date_maj` est un OBJET de date partout ailleurs dans le fichier
        # ({annee, lune, jour}) : y poser la phrase francaise de `dire_date`
        # rendait la tete illisible a `tick.py` ("date_maj absente ou
        # illisible") et la faisait passer pour jamais mise a jour. Corrige le
        # 10 aout, apres l'avoir vu casser la premiere tete posee avec.
        # …et sans la `minute` : une tete se date au jour, comme les 67 autres.
        d = date_du_monde() or {}
        entree["date_maj"] = {c: d[c] for c in ("annee", "lune", "jour")
                              if c in d} or entree.get("date_maj")
        touche = True
    if not touche:
        sys.exit("la tête de %s a disparu entre-temps : rien écrit." % pid)
    temporaire = chemin + ".regence.tmp"
    with io.open(temporaire, "w", encoding="utf-8") as f:
        json.dump(tetes, f, ensure_ascii=False, indent=2)
        f.write(u"\n")
    os.replace(temporaire, chemin)
    print("\nécrit dans etat/intentions.json.")


# --------------------------------------------------------------------------
# Le registre de regence — ce qu'on herite
# --------------------------------------------------------------------------

def registre_de(pid):
    return os.path.join(ETAT, "joueurs", pid, "regence.jsonl")


def _ligne(chemin, enregistrement):
    dossier = os.path.dirname(chemin)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(chemin, "a", encoding="utf-8") as f:
        f.write(json.dumps(enregistrement, ensure_ascii=False) + u"\n")


def lire_registre(pid):
    chemin = registre_de(pid)
    if not os.path.exists(chemin):
        return []
    entrees = []
    with io.open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                entrees.append(json.loads(ligne))
            except ValueError:
                continue
    return entrees


def _engagements(rapport):
    """Ce qui, dans ce rapport, lie le siege apres coup.

    Trois sources, et pas d'invention : ce qu'il a dit a quelqu'un, ce qu'il a
    ecrit dans une table qui garde (plis, relations, evenements, books), et la
    suite qu'il annonce lui-meme.
    """
    activation = (rapport or {}).get("activation") or {}
    engagements = []
    for activite in activation.get("activites") or []:
        if not isinstance(activite, dict):
            continue
        for resultat in activite.get("resultats_produits") or []:
            if not isinstance(resultat, dict):
                continue
            if resultat.get("type") not in ("communication", "objet_produit"):
                continue
            quoi = resultat.get("apres") or resultat.get("quoi")
            if quoi:
                engagements.append({
                    "genre": resultat.get("type"),
                    "quoi": _court(quoi, 240),
                    "cible": resultat.get("cible"),
                })
    for mutation in (rapport or {}).get("mutations_proposees") or []:
        if not isinstance(mutation, dict):
            continue
        if mutation.get("table") not in ("plis", "relations", "evenements",
                                          "books", "mains"):
            continue
        valeur = mutation.get("valeur")
        if not isinstance(valeur, str):
            valeur = json.dumps(valeur, ensure_ascii=False)
        engagements.append({
            "genre": "%s/%s" % (mutation.get("table"),
                                 mutation.get("operation")),
            "quoi": _court(valeur, 240),
            "cible": mutation.get("cible"),
        })
    if activation.get("suite"):
        engagements.append({"genre": "suite annoncée",
                            "quoi": _court(activation["suite"], 240),
                            "cible": None})
    return engagements


def _faits(rapport):
    activation = (rapport or {}).get("activation") or {}
    faits = []
    for activite in activation.get("activites") or []:
        if not isinstance(activite, dict):
            continue
        quoi = activite.get("quoi") or (activite.get("action") or {}).get("quoi")
        if quoi:
            faits.append({"quoi": _court(quoi, 240),
                          "resultat": _court(activite.get("resultat") or "", 240)})
    return faits


def consigner(pid, rapport, fichier=None, horloge=None):
    """Pose au registre ce que ce siege vient de decider seul.

    Appele apres le depot du rapport d'activation. N'ecrit rien pour un
    acteur ordinaire : seul un siege peut se faire heriter.
    """
    if not est_en_regence(pid):
        return None
    activation = (rapport or {}).get("activation") or {}
    franchies, evitees = franchissements(rapport)
    enregistrement = {
        "genre": "activation",
        "a": dt.datetime.now().astimezone().isoformat(),
        "date_monde": horloge or horloge_de(pid),
        "qui": pid,
        "tache": (activation.get("tache") or {}).get("quoi"),
        "issue": activation.get("issue"),
        "faits": _faits(rapport),
        "engagements": _engagements(rapport),
        "lignes_evitees": [{"code": f["code"], "extrait": f["extrait"]}
                            for f in evitees],
        "lignes_franchies": [{"code": f["code"], "extrait": f["extrait"]}
                              for f in franchies],
        "rapport": (os.path.relpath(fichier, RACINE).replace("\\", "/")
                     if fichier else None),
        "remis": False,
    }
    _ligne(registre_de(pid), enregistrement)
    return enregistrement


def compte_rendu(pid):
    """Le texte de passation : ce qu'on hérite en se rasseyant."""
    entrees = [e for e in lire_registre(pid)
               if e.get("genre") == "activation"]
    remises = {i for e in lire_registre(pid) if e.get("genre") == "passation"
               for i in (e.get("couvre") or [])}
    en_attente = [e for e in entrees if e.get("a") not in remises]
    nom = nom_de(pid)
    lignes = ["# Ce qui s'est décidé sans vous — %s" % nom, ""]
    if not en_attente:
        lignes.append("Rien : ce siège n'a rien décidé seul depuis la "
                      "dernière passation.")
        return "\n".join(lignes), []
    lignes.append("%d activation(s) en votre absence, de %s à %s."
                  % (len(en_attente),
                     dire_date(en_attente[0].get("date_monde")),
                     dire_date(en_attente[-1].get("date_monde"))))
    lignes.append("")
    lignes.append("## Ce qui a été fait")
    lignes.append("")
    for e in en_attente:
        lignes.append("- %s — %s (%s)" % (
            dire_date(e.get("date_monde")),
            e.get("tache") or "affaire sans intitulé",
            e.get("issue") or "issue inconnue"))
        for fait in e.get("faits") or []:
            detail = fait.get("resultat")
            lignes.append("    · %s%s" % (
                fait.get("quoi"), (" → " + detail) if detail else ""))
    engagements = [(e, g) for e in en_attente for g in e.get("engagements") or []]
    lignes.extend(["", "## Ce qui vous engage désormais", ""])
    if engagements:
        for e, g in engagements:
            lignes.append("- [%s] %s%s  (%s)" % (
                g.get("genre"), g.get("quoi"),
                (" — sur " + str(g["cible"])) if g.get("cible") else "",
                dire_date(e.get("date_monde"))))
    else:
        lignes.append("- rien qui vous lie.")
    evitees = [(e, f) for e in en_attente for f in e.get("lignes_evitees") or []]
    lignes.extend(["", "## Ce qu'il a laissé pour vous", ""])
    if evitees:
        for e, f in evitees:
            lignes.append("- ligne « %s » non franchie, %s : %s"
                          % (f.get("code"), dire_date(e.get("date_monde")),
                             f.get("extrait")))
    else:
        lignes.append("- rien n'a buté sur une décision qui vous revienne.")
    franchies = [(e, f) for e in en_attente for f in e.get("lignes_franchies") or []]
    if franchies:
        lignes.extend(["", "## ALERTE — lignes franchies malgré la garde", ""])
        for e, f in franchies:
            lignes.append("- « %s », %s : %s" % (
                f.get("code"), dire_date(e.get("date_monde")),
                f.get("extrait")))
    lignes.extend(["", "Sources : " + ", ".join(
        sorted({e.get("rapport") for e in en_attente if e.get("rapport")})
        or ["aucune"])])
    return "\n".join(lignes), en_attente


def remettre(pid, vraiment=True):
    """Rend la passation et la marque remise. Rend (texte, chemin_ecrit)."""
    texte, en_attente = compte_rendu(pid)
    if not en_attente or not vraiment:
        return texte, None
    horodatage = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dossier = os.path.join(ETAT, "joueurs", pid)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    chemin = os.path.join(dossier, "regence-%s.md" % horodatage)
    with io.open(chemin, "w", encoding="utf-8") as f:
        f.write(texte + u"\n")
    _ligne(registre_de(pid), {
        "genre": "passation",
        "a": dt.datetime.now().astimezone().isoformat(),
        "date_monde": horloge_de(pid),
        "qui": pid,
        "couvre": [e.get("a") for e in en_attente],
        "fichier": os.path.relpath(chemin, RACINE).replace("\\", "/"),
    })
    return texte, chemin


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def etat_des_regences():
    vacants = sorted(sieges_vacants())
    if not vacants:
        print("aucun siège vacant : personne n'est en régence.")
    for pid in vacants:
        tete = tete_de(pid)
        marques = []
        marques.append("tête écrite" if tete else "SANS TÊTE")
        marques.append("clause posée" if clause_posee(tete)
                       else "CLAUSE ABSENTE")
        attente = [e for e in lire_registre(pid)
                   if e.get("genre") == "activation"]
        remises = {i for e in lire_registre(pid)
                   if e.get("genre") == "passation"
                   for i in (e.get("couvre") or [])}
        reste = [e for e in attente if e.get("a") not in remises]
        marques.append("%d décision(s) à rendre" % len(reste))
        print("  %-22s %s" % (pid, " · ".join(marques)))
    occupes = sorted(sieges_occupes())
    if occupes:
        print("\nassis (jamais activés) : " + ", ".join(occupes))


def main():
    ap = argparse.ArgumentParser(
        description="La régence : ce qu'un siège vacant peut faire, "
                    "et ce qu'il rend en se relevant.")
    ap.add_argument("--clause", metavar="PERSONNAGE_ID",
                    help="afficher la clause de régence à poser dans sa tête")
    ap.add_argument("--poser", metavar="PERSONNAGE_ID",
                    help="écrire la clause dans sa tête (avec --vraiment)")
    ap.add_argument("--verifier", metavar="RAPPORT.JSON",
                    help="passer un rapport d'activation au crible des "
                         "lignes rouges")
    ap.add_argument("--qui", metavar="PERSONNAGE_ID",
                    help="avec --verifier : forcer l'acteur du rapport")
    ap.add_argument("--compte-rendu", metavar="PERSONNAGE_ID",
                    dest="compte_rendu",
                    help="ce qu'on hérite en se rasseyant (sans le marquer "
                         "remis)")
    ap.add_argument("--vraiment", action="store_true", help="écrire pour de bon")
    args = ap.parse_args()

    if args.clause:
        print(clause_croyance(args.clause))
        print()
        print(json.dumps(clause_declencheur(), ensure_ascii=False, indent=2))
        return
    if args.poser:
        poser_clause(args.poser, args.vraiment)
        return
    if args.verifier:
        rapport = lire_json(args.verifier, None)
        if rapport is None:
            sys.exit("rapport illisible : %s" % args.verifier)
        pid = args.qui or rapport.get("qui")
        franchies, evitees = franchissements(rapport)
        print("acteur : %s (%s)" % (
            pid, "en régence" if est_en_regence(pid) else "acteur ordinaire"))
        for f in evitees:
            print("  évitée   « %s » dans %s : %s"
                  % (f["code"], f["ou"], f["extrait"]))
        for f in franchies:
            print("  FRANCHIE « %s » dans %s : %s"
                  % (f["code"], f["ou"], f["extrait"]))
        if not franchies:
            print("  aucune ligne franchie.")
        elif est_en_regence(pid):
            print("\n" + texte_du_refus(pid, franchies))
        return
    if args.compte_rendu:
        texte, _ = compte_rendu(args.compte_rendu)
        print(texte)
        return
    etat_des_regences()


if __name__ == "__main__":
    main()
