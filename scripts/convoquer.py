# -*- coding: utf-8 -*-
# CONVOQUER — qui doit une journee de travail aujourd'hui, et le dossier a lui
# mettre entre les mains. La piece manquante en tete de la chaine de
# docs/travaux.md : celle qui dit A QUI l'on fait vivre une journee.
#
# POURQUOI CE N'EST PAS UN CROCHET DANS `tick.py`. Le tick est de
# l'arithmetique : il compte des tonneaux, decompte des horloges, et rend un
# verdict sur ce qui est deja ecrit. Faire PENSER un homme n'est pas un calcul
# — c'est une session qui le vit, source par source, et qui rapporte ce qu'elle
# a trouve. Le tick ne peut donc pas produire les pensees ; il peut dire qui en
# doit. Ce script est cette liste-la, plus le dossier qui va avec.
#
# CE QU'UNE CONVOCATION PORTE. Un homme qu'on envoie travailler sans son
# dossier refera ce qu'il a deja fait, ou inventera ce qu'il aurait pu aller
# chercher. Chaque brief porte donc : sa maniere (il travaille comme il parle),
# son affaire et son echeance, OU IL EN EST, ce qu'il sait deja — pour ne pas
# le redecouvrir —, les sources qu'il n'a pas encore touchees, et le cahier ou
# sa conclusion doit atterrir.
#
# CE SCRIPT N'ECRIT JAMAIS DANS etat/. Il lit et il redige une convocation.
#
# Usage :
#     python scripts/convoquer.py                 qui doit une journee
#     python scripts/convoquer.py --dossiers      les briefs, prets a depecher
#     python scripts/convoquer.py --qui gerardys
#     python scripts/convoquer.py --tous          meme ceux qui ne doivent rien
import argparse
import io
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
STAGING = os.path.join(ETAT, "staging", "travaux")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import travaux as mod_travaux  # noqa: E402

# ------------------------------------------------------------- les chiffres
# A l'essai, comme partout ailleurs dans cette chaine.

VIEUX = 1            # jours depuis le dernier travail au-dela desquels il doit
PROCHE = 3           # une echeance a moins de N jours convoque d'office
DERNIERES = 4        # pensees rappelees dans le dossier, les plus recentes
AFFAIRES_PAR_JOUR = 2


def charger(nom, defaut):
    chemin = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as fh:
        contenu = fh.read().strip()
    return json.loads(contenu) if contenu else defaut


def liste(brut, clef):
    if isinstance(brut, dict):
        return brut.get(clef, [])
    return brut or []


def net(t, n=None):
    t = re.sub(r"\s+", " ", (t or "").replace("**", "")).strip()
    return t if (n is None or len(t) <= n) else t[:n - 1] + "…"


def dernier_depot(qui):
    """Le jour de la derniere journee deposee pour cet homme, ou None.

    Le fichier de staging n'est pas date : on le date par ses pensees, comme
    `mesurer.py`. Sans ca, on reconvoquerait un homme qui vient de rendre.
    """
    chemin = os.path.join(STAGING, qui + ".json")
    if not os.path.isfile(chemin):
        return None
    try:
        with io.open(chemin, encoding="utf-8") as fh:
            d = json.load(fh)
    except ValueError:
        return None
    jours = []
    for t in d.get("travaux") or []:
        for p in t.get("pensees") or []:
            j = mod_travaux.jour_absolu(p.get("date"))
            if j is not None:
                jours.append(j)
    return max(jours) if jours else None


def convoquer(travaux, aujourdhui, tous):
    """Rend une liste de (qui, [travaux], motifs). Pas de jugement, des dates."""
    par_homme = {}
    for trav in travaux:
        if trav.get("etat") in ("rendu", "abandonne"):
            continue
        par_homme.setdefault(trav.get("qui"), []).append(trav)

    out = []
    for qui, siens in sorted(par_homme.items()):
        motifs = []
        depot = dernier_depot(qui)
        if depot is None:
            motifs.append("il n'a jamais rendu de journee")
        elif aujourdhui - depot >= VIEUX:
            motifs.append("{} jour(s) sans rendre de journee"
                          .format(aujourdhui - depot))

        for trav in siens:
            ech = mod_travaux.jour_absolu(trav.get("echeance"))
            if ech is None:
                continue
            if ech < aujourdhui and not trav.get("conclusion"):
                motifs.append("« {} » : echeance passee, rien de rendu"
                              .format(net(trav.get("affaire"), 40)))
            elif ech - aujourdhui <= PROCHE:
                motifs.append("« {} » : echeance dans {} jour(s)".format(
                    net(trav.get("affaire"), 40), ech - aujourdhui))

        ouvertes = [t for t in siens if not t.get("conclusion")]
        if ouvertes and not motifs:
            motifs.append("{} affaire(s) ouverte(s), sans echeance proche"
                          .format(len(ouvertes)))

        if motifs or tous:
            out.append((qui, siens, motifs))
    return out


def dossier(qui, siens, motifs, gens, date):
    """Le brief a coller dans l'agent qui vivra sa journee."""
    p = gens.get(qui) or {}
    lignes = []
    lignes.append("=" * 72)
    lignes.append("CONVOCATION — {} ({})".format(p.get("nom") or qui, qui))
    lignes.append("  {}".format(net(p.get("titre")) or "sans titre inscrit"))
    lignes.append("  le {}, a {}".format(mod_travaux.fmt(date),
                                         p.get("lieu_id") or "?"))
    if p.get("maniere"):
        lignes.append("  sa maniere : {}".format(net(p["maniere"], 200)))
    if p.get("traits"):
        lignes.append("  ses traits : {}".format(", ".join(p["traits"])))
    lignes.append("")
    lignes.append("  POURQUOI ON LE CONVOQUE")
    for m in motifs:
        lignes.append("    - {}".format(m))
    lignes.append("")

    for trav in siens:
        lignes.append("  AFFAIRE — {}".format(net(trav.get("affaire"))))
        lignes.append("    echeance : {} · etat : {} · son cahier : {}".format(
            mod_travaux.fmt(trav.get("echeance")) if trav.get("echeance")
            else "aucune (travail continu)",
            trav.get("etat") or "?", trav.get("livre") or "aucun inscrit"))
        pensees = trav.get("pensees") or []
        lignes.append("    il a deja {} pensee(s) la-dessus{}".format(
            len(pensees),
            " et sa conclusion est ecrite" if trav.get("conclusion")
            else ", et pas de conclusion"))
        for pen in pensees[-DERNIERES:]:
            lignes.append("      · {}".format(net(pen.get("texte"), 150)))
        srcs = trav.get("sources") or []
        if srcs:
            lignes.append("    ce qu'il n'a pas encore touche :")
            for s in srcs:
                lignes.append("      · {} ({}{})".format(
                    net(s.get("quoi")), s.get("genre") or "?",
                    ", {} j.".format(s["cout_jours"])
                    if s.get("cout_jours") is not None else ""))
        else:
            lignes.append("    AUCUNE SOURCE INSCRITE — il doit d'abord "
                          "trouver ou aller, sinon ce travail est un voeu.")
        lignes.append("")

    lignes.append("  CE QU'IL RAPPORTE, DANS etat/staging/travaux/{}.json"
                  .format(qui))
    lignes.append("    `journal` : ses etapes horodatees (heure, duree, lieu ou")
    lignes.append("      de/a, quoi il allait chercher, ce que ca a donne — y")
    lignes.append("      compris « rien », qui est une reponse honnete).")
    lignes.append("    `travaux` : par affaire, ses pensees DATEES et SOURCEES.")
    lignes.append("      Pas de source, pas de pensee. Jamais `dite`.")
    lignes.append("    `cahier2` : ses changements de registre en coordonnees")
    lignes.append("      exactes (livre, table, ligne, colonne, valeur).")
    lignes.append("    `conclusion` : de SA main, et seulement si elle est mure.")
    lignes.append("")
    lignes.append("  LES BORNES : {} affaires touchees au plus dans la journee ; "
                  "le nombre".format(AFFAIRES_PAR_JOUR))
    lignes.append("    de pensees, lui, n'est pas borne. Il invente largement la")
    lignes.append("    MATIERE (des gens, des prix, des rancunes) et jamais le")
    lignes.append("    VERDICT : ce que la source pouvait rendre, elle le rend,")
    lignes.append("    et pas ce qui arrangerait la scene.")
    return "\n".join(lignes)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dossiers", action="store_true")
    ap.add_argument("--qui")
    ap.add_argument("--tous", action="store_true")
    args = ap.parse_args()

    monde = charger("monde", {})
    date = monde.get("date") or {"annee": 0, "lune": 1, "jour": 1}
    aujourdhui = mod_travaux.jour_absolu(date) or 0

    travaux = liste(charger("travaux", {}), "travaux")
    gens = {p.get("id"): p for p in liste(charger("personnages", []),
                                          "personnages")
            if isinstance(p, dict)}
    if args.qui:
        travaux = [t for t in travaux if t.get("qui") == args.qui]

    convoques = convoquer(travaux, aujourdhui, args.tous)

    if args.dossiers:
        for qui, siens, motifs in convoques:
            print(dossier(qui, siens, motifs, gens, date))
            print()
        return 0

    print("A CONVOQUER LE {} ({} homme(s))".format(
        mod_travaux.fmt(date), len(convoques)))
    if not convoques:
        print("  personne — tout le monde a rendu sa journee.")
    for qui, siens, motifs in convoques:
        p = gens.get(qui) or {}
        print("  {:<18} {}".format(qui, net(p.get("titre"), 48)))
        for m in motifs:
            print("      {}".format(m))
    print()
    print("  --dossiers pour les briefs a depecher (un agent par homme).")

    # Ceux qui parlent sans rien avoir a dire : meme signalement que
    # travaux.py --verifier, mais rappele ici parce que c'est au moment de
    # convoquer qu'on peut y remedier.
    avec = set(t.get("qui") for t in travaux)
    orphelins = [t.get("personnage_id") for t in charger("intentions", [])
                 if isinstance(t, dict)
                 and (t.get("echelle") or "").strip() == "scene"
                 and t.get("personnage_id") not in avec]
    if orphelins and not args.qui:
        print()
        print("  SANS AUCUN TRAVAIL OUVERT, et pourtant en scene : {}"
              .format(", ".join(sorted(orphelins))))
        print("  Ceux-la parleront sans source. Ouvre-leur une affaire avant "
              "de les convoquer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
