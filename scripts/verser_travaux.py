# -*- coding: utf-8 -*-
# VERSER LES TRAVAUX — porter dans `etat/travaux.json` ce qu'un homme a appris
# pendant sa journee. Le maillon qui manquait entre l'agent qui pense et l'etat
# qui compte.
#
# POURQUOI. `appliquer_travaux.py` verse le CAHIER (books.json) ; rien ne
# versait les PENSEES. Le 28e, neuf journees ont ete deposees dans
# `etat/staging/travaux/` et leurs pensees sont arrivees dans `travaux.json` a
# la main, une par une. Et `appliquer.py` ne connait meme pas la table
# `travaux` : les mutations que `tick.py` produit dessus (l'excitation, la
# conclusion mure) ne peuvent s'ecrire par aucun chemin. La chaine de
# docs/travaux.md etait donc coupee en deux endroits, et la moitie amont ne
# tournait que si quelqu'un la portait a bras.
#
# CE QU'IL VERSE, ET CE QU'IL REFUSE DE TOUCHER :
#   - les pensees, dedoublonnees sur (date, texte) — relancer ne double rien ;
#   - la conclusion, quand l'homme l'a ecrite. On ne l'invente jamais et on ne
#     l'ecrase pas en silence : un remplacement est annonce ;
#   - `dernier_travail`, `etat`, et `excitation` recalculee par `travaux.py`.
#   - JAMAIS `servie`. Une pensee est servie quand on y a PUISE pour ecrire
#     une replique, pas quand elle est versee. C'est le geste de celui qui
#     tient la plume de la scene ; le confondre avec celui-ci reviendrait a
#     declarer depensee toute une journee dont personne ne s'est servi.
#
# UN TRAVAIL NEUF SE CREE ICI, mais seulement s'il porte de quoi vivre : un
# homme, une affaire, un livre ou aller. Un `travail_id` inconnu et nu est
# refuse et nomme — c'est le meme parti qu'`appliquer_travaux.py`, et pour la
# meme raison : mieux vaut une entree en attente qu'une entree de travers.
#
# Usage :
#     python scripts/verser_travaux.py                ce qui serait verse
#     python scripts/verser_travaux.py --vraiment     ecrit etat/travaux.json
#     python scripts/verser_travaux.py --qui gerardys
import argparse
import hashlib
import io
import json
import os
import re
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
STAGING = os.path.join(ETAT, "staging", "travaux")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import travaux as mod_travaux  # noqa: E402  (le calcul de l'excitation)


def plat(t):
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def empreinte(pensee):
    """De quoi reconnaitre une pensee deja versee, sans dependre du copier.

    La date seule ne suffit pas — un homme en pose treize le meme jour ; le
    texte entier est trop fragile — une virgule corrigee en referait une neuve.
    """
    d = pensee.get("date") or {}
    return (d.get("annee"), d.get("lune"), d.get("jour"),
            plat(pensee.get("texte"))[:90])


def charger(chemin, defaut):
    if not os.path.isfile(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as fh:
        contenu = fh.read().strip()
    return json.loads(contenu) if contenu else defaut


def sceau(chemin):
    """L'empreinte du fichier qu'on va reellement ecrire.

    Meme filet qu'`appliquer.py`, et pour la meme raison : la session qui joue
    ecrit dans `travaux.json` pendant qu'on reflechit — elle y a ajoute une
    affaire pendant la redaction de ce script. Un `Write` sur le tableau entier
    sans ce controle avale silencieusement ce qu'elle vient de poser.
    """
    if not os.path.isfile(chemin):
        return None
    with io.open(chemin, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def jour_du_depot(depot):
    """Le jour d'un depot, deduit de ses pensees — il ne porte pas de date."""
    jours = []
    for t in depot.get("travaux") or []:
        for p in t.get("pensees") or []:
            j = mod_travaux.jour_absolu(p.get("date"))
            if j is not None:
                jours.append((j, p["date"]))
    return max(jours)[1] if jours else None


def journaliser(depots, faire):
    """Le JOURNAL DES JOURNEES — append-only, une ligne par etape.

    POURQUOI. Un depot de `etat/staging/travaux/<qui>.json` s'ECRASE au depot
    suivant : la journee du 28e disparaitra le 29e, avec ses vingt-cinq etapes,
    ses heures, et ce qui n'a rien donne. Tout ce qu'on saurait encore, ce sont
    les pensees qui en sont sorties — c'est-a-dire le resultat sans le travail.
    On perdrait exactement ce qui permet de dire pourquoi une journee a rendu.

    Meme idiome que `flux.jsonl` : une ligne JSON, on ajoute, on ne reecrit
    jamais. Et le depot brut part dans `etat/archive/journees/` pour que rien
    ne soit irrecuperable — le jsonl est un index rapide, pas la seule copie.

    Idempotent sur (jour, qui) : relancer un versement ne double pas le
    journal.
    """
    chemin = os.path.join(ETAT, "journees.jsonl")
    deja, seances = set(), {}
    if os.path.isfile(chemin):
        with io.open(chemin, encoding="utf-8") as fh:
            for ligne in fh:
                ligne = ligne.strip()
                if not ligne:
                    continue
                try:
                    o = json.loads(ligne)
                except ValueError:
                    continue
                d = o.get("jour") or {}
                if o.get("type") == "etape":
                    deja.add((d.get("annee"), d.get("lune"), d.get("jour"),
                              o.get("qui"), o.get("heure")))
                elif o.get("type") == "journee":
                    seances[(d.get("annee"), d.get("lune"), d.get("jour"),
                             o.get("qui"))] = max(
                        seances.get((d.get("annee"), d.get("lune"),
                                     d.get("jour"), o.get("qui")), 0),
                        int(o.get("seance") or 1))

    lignes, ignores = [], 0
    for qui, depot in depots:
        jour = jour_du_depot(depot)
        if jour is None:
            ignores += 1
            continue
        cle = (jour.get("annee"), jour.get("lune"), jour.get("jour"), qui)
        journal = [e for e in (depot.get("journal") or [])
                   if cle + (e.get("heure"),) not in deja]
        if not journal:
            ignores += 1
            continue
        for e in journal:
            lignes.append({
                "type": "etape", "jour": jour, "qui": qui,
                "heure": e.get("heure"), "duree": e.get("duree"),
                "lieu": e.get("lieu"), "de": e.get("de"), "a": e.get("a"),
                "quoi": e.get("quoi"), "resultat": e.get("resultat"),
                "genre": ("trajet" if mod_travaux.etape_est_trajet(e)
                          else "travail"),
                "sec": mod_travaux.etape_seche(e),
            })
        pensees = sum(len(t.get("pensees") or [])
                      for t in depot.get("travaux") or [])
        lignes.append({
            "type": "journee", "jour": jour, "qui": qui,
            "seance": seances.get(cle, 0) + 1,
            "etapes": len(journal),
            "minutes": sum(int(e.get("duree") or 0) for e in journal),
            "trajets": sum(1 for e in journal
                           if mod_travaux.etape_est_trajet(e)),
            "secs": sum(1 for e in journal if mod_travaux.etape_seche(e)),
            "pensees": pensees,
            "affaires": [t.get("travail_id") or t.get("id")
                         for t in depot.get("travaux") or []],
            "conclusions": sum(1 for t in depot.get("travaux") or []
                               if t.get("conclusion")),
            "cahier_proposes": len(depot.get("cahier2") or []),
        })

    if faire and lignes:
        with io.open(chemin, "a", encoding="utf-8") as fh:
            for o in lignes:
                fh.write(json.dumps(o, ensure_ascii=False) + "\n")
        arch = os.path.join(ETAT, "archive", "journees")
        if not os.path.isdir(arch):
            os.makedirs(arch)
        for qui, depot in depots:
            jour = jour_du_depot(depot)
            if jour is None:
                continue
            nom = "{}-{}-{}-{}.json".format(jour.get("annee"), jour.get("lune"),
                                            jour.get("jour"), qui)
            cible = os.path.join(arch, nom)
            if not os.path.isfile(cible):
                with io.open(cible, "w", encoding="utf-8") as fh:
                    json.dump(depot, fh, ensure_ascii=False, indent=1)
    return lignes, ignores


def lire_depots(qui_filtre):
    depots = []
    if not os.path.isdir(STAGING):
        return depots
    for nom in sorted(os.listdir(STAGING)):
        if not nom.endswith(".json"):
            continue
        qui = nom[:-5]
        if qui_filtre and qui != qui_filtre:
            continue
        try:
            d = charger(os.path.join(STAGING, nom), {})
        except ValueError as err:
            print("  {} illisible : {}".format(nom, err))
            continue
        depots.append((d.get("qui") or qui, d))
    return depots


def verser(depots, table):
    """Rend (faits, refus). Ne modifie `table` que pour de vrai."""
    index = {t.get("id"): t for t in table if isinstance(t, dict)}
    faits, refus = [], []

    for qui, depot in depots:
        for prop in depot.get("travaux") or []:
            tid = prop.get("travail_id") or prop.get("id")
            if not tid:
                refus.append((qui, "?", "aucun travail_id"))
                continue

            trav = index.get(tid)
            if trav is None:
                # Un travail neuf : on l'accepte s'il porte de quoi vivre.
                if not prop.get("affaire"):
                    refus.append((qui, tid,
                                  "travail inconnu et sans `affaire` — a "
                                  "ouvrir a la main dans etat/travaux.json"))
                    continue
                trav = {"id": tid, "qui": qui, "affaire": prop["affaire"],
                        "echeance": prop.get("echeance"), "etat": "en cours",
                        "excitation": 0, "dernier_travail": None,
                        "livre": prop.get("livre"),
                        "sources": prop.get("sources") or [],
                        "pensees": [], "conclusion": None}
                table.append(trav)
                index[tid] = trav
                faits.append((qui, tid, "travail OUVERT : {}"
                              .format(prop["affaire"][:60])))

            if trav.get("qui") != qui:
                refus.append((qui, tid, "ce travail est a {}"
                              .format(trav.get("qui"))))
                continue

            deja = set(empreinte(p) for p in trav.get("pensees") or [])
            neuves, sans_source = 0, 0
            for p in prop.get("pensees") or []:
                if not (p.get("source") or "").strip():
                    sans_source += 1
                    continue
                if not isinstance(p.get("date"), dict):
                    sans_source += 1
                    continue
                if empreinte(p) in deja:
                    continue
                # `servie` n'est jamais pose ici : voir l'en-tete.
                trav.setdefault("pensees", []).append({
                    "date": p["date"], "source": p["source"],
                    "texte": p.get("texte") or "", "servie": False})
                deja.add(empreinte(p))
                neuves += 1
            if neuves:
                faits.append((qui, tid, "{} pensee(s) versee(s)".format(neuves)))
            if sans_source:
                refus.append((qui, tid, "{} pensee(s) sans source ou sans date "
                                        "— pas de source, pas de pensee"
                              .format(sans_source)))

            if prop.get("dernier_travail"):
                trav["dernier_travail"] = prop["dernier_travail"]

            c = prop.get("conclusion")
            if c and plat(c) != plat(trav.get("conclusion")):
                if trav.get("conclusion"):
                    faits.append((qui, tid, "conclusion REMPLACEE (l'ancienne "
                                            "faisait {} signes)"
                                  .format(len(trav["conclusion"]))))
                else:
                    faits.append((qui, tid, "conclusion ecrite ({} signes)"
                                  .format(len(c))))
                trav["conclusion"] = c
                if trav.get("etat") == "en cours":
                    trav["etat"] = "mur"
    return faits, refus


def recalculer(table, aujourdhui):
    """L'excitation, par l'arithmetique de travaux.py — pas a la louche.

    Passe ici parce qu'`appliquer.py` n'a pas de table `travaux` dans ses
    OPERATIONS : les mutations du tick n'ont aujourd'hui aucun chemin
    d'ecriture. Les ajouter la-bas est la suite propre ; en attendant, on ne
    laisse pas un compteur mentir apres un versement.
    """
    lignes, _ = mod_travaux.calculer_travaux(table, aujourdhui, 0)
    bouge = []
    par_id = {l["id"]: l for l in lignes}
    for trav in table:
        l = par_id.get(trav.get("id"))
        if not l:
            continue
        if int(trav.get("excitation") or 0) != l["excitation"]:
            bouge.append((trav["qui"], trav["id"],
                          "excitation {} -> {}".format(
                              trav.get("excitation"), l["excitation"])))
            trav["excitation"] = l["excitation"]
    return bouge


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vraiment", action="store_true")
    ap.add_argument("--journal-seul", dest="journal_seul", action="store_true",
                    help="ecrire le journal et l'archive, sans toucher "
                         "etat/travaux.json")
    ap.add_argument("--qui")
    args = ap.parse_args()

    depots = lire_depots(args.qui)
    if not depots:
        print("Aucune journee deposee dans etat/staging/travaux/.")
        return 0

    chemin = os.path.join(ETAT, "travaux.json")
    avant = sceau(chemin)
    racine = charger(chemin, {"travaux": []})
    table = racine.get("travaux") if isinstance(racine, dict) else racine

    faits, refus = verser(depots, table)
    monde = charger(os.path.join(ETAT, "monde.json"), {})
    aujourdhui = mod_travaux.jour_absolu(monde.get("date")) or 0
    bouge = recalculer(table, aujourdhui)

    print("VERSE : {} changement(s) sur {} journee(s)".format(
        len(faits), len(depots)))
    for qui, tid, quoi in faits:
        print("  {:<16} {:<32} {}".format(qui, tid[:32], quoi))
    if bouge:
        print()
        print("RECALCULE : {}".format(len(bouge)))
        for qui, tid, quoi in bouge:
            print("  {:<16} {:<32} {}".format(qui, tid[:32], quoi))
    if refus:
        print()
        print("REFUSE, a poser a la main : {}".format(len(refus)))
        for qui, tid, motif in refus:
            print("  {:<16} {:<32} {}".format(qui, str(tid)[:32], motif))

    # Le journal a son propre interrupteur : archiver une journee et muter
    # l'etat sont deux gestes, et l'un ne doit pas se payer de l'autre. On veut
    # pouvoir garder la trace d'un depot sans encore trancher ce qu'on en verse.
    lignes_log, deja_log = journaliser(depots, args.vraiment or args.journal_seul)
    if lignes_log or deja_log:
        print()
        print("JOURNAL : {} ligne(s) vers etat/journees.jsonl{}".format(
            len(lignes_log),
            " · {} journee(s) deja journalisee(s)".format(deja_log)
            if deja_log else ""))

    if args.journal_seul:
        print("\nJournal ecrit. etat/travaux.json n'a pas ete touche.")
        return 0

    if args.vraiment:
        if sceau(chemin) != avant:
            print("\nREFUSE : etat/travaux.json a bouge pendant le calcul — "
                  "une autre session ecrit. Relance, rien n'a ete touche.")
            return 1
        if isinstance(racine, dict):
            racine["travaux"] = table
        else:
            racine = table
        with io.open(chemin, "w", encoding="utf-8") as fh:
            json.dump(racine, fh, ensure_ascii=False, indent=1)
        print("\netat/travaux.json ecrit.")
    else:
        print("\nRien n'a ete ecrit. --vraiment pour verser.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
