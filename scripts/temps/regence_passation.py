# -*- coding: utf-8 -*-
# REGENCE_PASSATION — la clause dans la tete, le registre de passation, la CLI.
#
# La seconde moitie de l'ancien scripts/regence.py (lot 2) : la clause (une
# croyance et un declencheur, jamais un champ invente), le registre
# etat/joueurs/<id>/regence.jsonl (consigner, compte rendu, remise), l'etat
# des regences et le main de la commande. La lecture, les sept lignes rouges
# et le crible lexical vivent dans regence.py, qui reexporte d'ici.
from __future__ import print_function

import argparse
import datetime as dt
import io
import json
import os
import sys

from temps.regence import (
    ETAT, RACINE, date_du_monde, dire_date, est_en_regence, franchissements, horloge_de, lire_json, lire_table, nom_de, sieges, sieges_occupes, sieges_vacants, texte_du_refus)
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



