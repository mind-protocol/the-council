# -*- coding: utf-8 -*-
"""Donner un CORPS aux gens du château de Peyredragon — pas seulement au bourg.

    python scripts/monde/peyredragon_chateau.py             ce qu'il ferait
    python scripts/monde/peyredragon_chateau.py --vraiment  et il l'écrit

Le bourg est peuplé depuis `peyredragon_usages.py` : ses 67 feux ont un métier,
et `peupler.py peyredragon` y pose 593 corps. Le CHÂTEAU, lui, est resté vide —
non par oubli, mais parce que ses volumes ne viennent pas du bâti. Ils sortent
des salles du plan (`materialisation/lieux.py`, qui lit `ecrans/modules/plans.js`),
et une salle n'a pas d'`usage` : elle a un nom et une porte.

Ce script est le chaînon manquant. Il prend les salles du plan, leur donne
l'usage qui leur correspond, et les ajoute au bâti de Peyredragon comme des
volumes ordinaires — quartier « Le château ». À partir de là, `peupler.py` ne
voit plus de différence entre une boucanerie du bourg et la roukerie : les deux
sont des lieux avec un métier, et il y pose des gens.

DEUX PARTIS PRIS, et ils comptent.

1. LES EFFECTIFS SONT DÉCIDÉS, PAS DÉDUITS. Ailleurs, le nombre de bras sort du
   plancher : une grande parcelle porte plus de monde. Une garnison ne marche
   pas comme ça — on n'a pas cent hommes parce que la caserne est grande, on a
   une caserne parce qu'on a décidé cent hommes. Les postes du château portent
   donc des comptes fixes (min = max), et ils ne bougeront pas si quelqu'un
   recalibre la fonction de taille.

2. UN SEUL CORPS PAR POSTE NOMMÉ. Le mestre, la septa, la nourrice, le castellan
   et le capitaine de la garde existent déjà dans `etat/personnages.json` —
   Gerardys, la septa Marlow, Tya, ser Robert Quince, ser Steffon Darklyn. On
   n'en fabrique donc pas un second : on crée UN corps pour chacun de ces
   postes, et `scripts/corps.py` y attache la fiche. Le lien remplace le nom
   anonyme ; il n'y a jamais deux mestres à Peyredragon.

Ce qu'on ne peuple pas : la chambre de la Table Peinte (on y travaille, on n'y
loge pas), la cour, le jardin, les lices, la grève, le grand escalier, le quai
et le bourg — le bourg a déjà les siens.
"""
import io
import json
import math
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")
sys.path.insert(0, os.path.join(RACINE, "scripts", "materialisation"))

import lieux as Li            # noqa: E402

# Le repère : la matérialisation compte depuis le milieu de l'île, le monde 3D
# depuis le coin sud-ouest. Le décalage est celui de `peyredragon.py`, et il
# n'est écrit qu'à ces deux endroits.
DECALAGE = (3000.0, 2500.0)

QUARTIER = "Le château"

# ---------------------------------------------------------------------------
# QUI TIENT QUELLE SALLE
# ---------------------------------------------------------------------------
# Par salle : l'usage qu'on lui donne, sa catégorie (pour la couleur du rendu),
# le nombre d'étages qu'on lui compte, et les postes avec leur effectif ferme.
#
# Les étages ne sont pas décoratifs : c'est `facade × profondeur × etages` qui
# fait le plancher, et le plancher sert au reste de la chaîne. Une grande salle
# est un volume d'un seul tenant — un étage —, une tour de logis en a trois.
#
# Les effectifs tiennent une garnison de Peyredragon en 129 AC : environ cent
# vingt piques et arbalètes réparties entre la caserne, les deux portes et le
# chemin de ronde, et une maison d'à peu près autant de bouches. C'est un siège
# de reine, pas une place forte de frontière.
CHATEAU = {
 # --- la garnison ----------------------------------------------------------
 "baraques":           ("chateau-baraques", "civique", 2, [
     ("capitaine-garde", "Capitaine de la garde", "h", "maitre", 1),
     ("sergent-garnison", "Sergent de la garnison", "h", "compagnon", 8),
     ("homme-armes", "Homme d'armes", "h", "valet", 96)]),
 "porte-dragon":       ("chateau-porte", "civique", 2, [
     ("sergent-garnison", "Sergent de la garnison", "h", "compagnon", 1),
     ("homme-armes", "Homme d'armes", "h", "valet", 6)]),
 "porte-de-mer":       ("chateau-porte", "civique", 2, [
     ("homme-armes", "Homme d'armes", "h", "valet", 4)]),
 "chemin-ronde":       ("chateau-guet", "civique", 1, [
     ("veilleur", "Veilleur", "h", "valet", 8)]),
 "tambour-de-pierre":  ("chateau-tour", "civique", 3, [
     ("veilleur", "Veilleur", "h", "valet", 4)]),
 "tour-dragon-mer":    ("chateau-tour", "civique", 3, [
     ("veilleur", "Veilleur", "h", "valet", 2)]),
 "guivre-des-vents":   ("chateau-tour", "civique", 3, [
     ("veilleur", "Veilleur", "h", "valet", 2)]),
 # --- la maison ------------------------------------------------------------
 # Le castellan tient le château quand la reine n'y est pas : il est de la
 # maison, pas de la garnison, et c'est pour ça qu'il loge aux communs.
 "communs":            ("chateau-communs", "service", 2, [
     ("castellan", "Castellan", "h", "maitre", 1),
     ("intendant-chateau", "Intendant du château", None, "compagnon", 1),
     ("servante", "Servante", "f", "valet", 10),
     ("valet-chateau", "Valet du château", "h", "valet", 6),
     ("blanchisseuse", "Blanchisseuse", "f", "valet", 4)]),
 "cuisines":           ("chateau-cuisines", "service", 1, [
     ("maitre-queux", "Maître queux", None, "maitre", 1),
     ("cuisinier", "Cuisinier", None, "compagnon", 3),
     ("marmiton", "Marmiton", None, "valet", 6),
     ("tournebroche", "Tournebroche", None, "valet", 2)]),
 "grande-salle":       ("chateau-grande-salle", "civique", 1, [
     ("senechal", "Sénéchal", "h", "maitre", 1),
     ("echanson", "Échanson", None, "valet", 2)]),
 "antichambre":        ("chateau-antichambre", "civique", 1, [
     ("huissier", "Huissier", "h", "compagnon", 1)]),
 "appartements-reine": ("chateau-appartements", "service", 1, [
     ("femme-chambre", "Femme de chambre", "f", "valet", 4)]),
 "chambre-enfants":    ("chateau-enfants", "service", 1, [
     ("nourrice", "Nourrice", "f", "compagnon", 1),
     ("berceuse", "Berceuse", "f", "valet", 2)]),
 "chambres-hotes":     ("chateau-hotes", "service", 2, [
     ("valet-chateau", "Valet du château", "h", "valet", 3)]),
 # --- les offices ----------------------------------------------------------
 "roukerie":           ("chateau-roukerie", "service", 3, [
     ("mestre", "Mestre", "h", "maitre", 1),
     ("corbier", "Corbier", None, "valet", 2)]),
 "septuaire":          ("chateau-septuaire", "culte", 1, [
     ("septa", "Septa", "f", "maitre", 1),
     ("novice", "Novice", None, "valet", 1)]),
 "forge":              ("chateau-forge", "artisanat", 1, [
     ("forgeron-armes", "Forgeron d'armes", "h", "maitre", 1),
     ("apprenti-forge", "Apprenti forgeron", "h", "valet", 2)]),
 "officine":           ("chateau-officine", "service", 1, [
     ("apothicaire", "Apothicaire", None, "maitre", 1),
     ("aide-officine", "Aide d'officine", None, "valet", 1)]),
 "archives":           ("chateau-archives", "service", 1, [
     ("clerc-archives", "Clerc de l'archive", None, "compagnon", 1)]),
 # --- les dessous ----------------------------------------------------------
 "cellier":            ("chateau-cellier", "commerce", 1, [
     ("bouteiller", "Bouteiller", "h", "maitre", 1),
     ("valet-cellier", "Valet de cellier", None, "valet", 2)]),
 "salle-froide":       ("chateau-froide", "commerce", 1, [
     ("garde-manger", "Garde-manger", None, "compagnon", 1)]),
 "etuves":             ("chateau-etuves", "service", 1, [
     ("chauffeur-etuves", "Chauffeur d'étuves", None, "valet", 2)]),
 "cachots":            ("chateau-cachots", "civique", 1, [
     ("geolier", "Geôlier", "h", "maitre", 1),
     ("porte-clefs", "Porte-clefs", "h", "valet", 2)]),
 # --- les dragons ----------------------------------------------------------
 # Peyredragon n'est pas une forteresse comme une autre : ce qui dort dans les
 # fosses demande des hommes, et ces hommes-là ne font que ça.
 "fosses":             ("chateau-fosses", "nuisance", 1, [
     ("premier-gardien", "Premier gardien des dragons", "h", "maitre", 1),
     ("gardien-dragons", "Gardien des dragons", "h", "compagnon", 8),
     ("valet-fosse", "Valet des fosses", None, "valet", 4)]),
}

# Les postes qu'un personnage NOMMÉ occupe déjà dans `etat/personnages.json`.
# On leur garde exactement une place — c'est là que `scripts/corps.py` viendra
# accrocher la fiche. Vérifié à la main contre l'état au 129.3.23.
NOMMES = {
    "mestre": "gerardys",
    "septa": "septa-marlow",
    "nourrice": "nourrice-tya",
    "castellan": "robert-quince",
    "capitaine-garde": "steffon-darklyn",
}


# Quelques salles du plan mesurent UNE unité de ce qu'elles nomment, pas
# l'ensemble : « les baraques » y sont une baraque de six mètres sur quatre, et
# non le rang de baraques adossé au mur. Tant qu'on n'y logeait personne, ça ne
# se voyait pas ; cent cinq hommes dans cinquante-huit mètres carrés se voient
# tout de suite. On déclare donc l'emprise réelle ici, en clair, plutôt que de
# corriger le plan — qui est une carte mentale et a le droit de simplifier.
EMPRISE = {
    "baraques": (42.0, 9.0),      # le rang complet, le long de la courtine
    "chemin-ronde": (150.0, 2.5),  # on n'y loge pas : on y marche
}


def toit(cat):
    """Ce qui coiffe le volume — même vocabulaire que peyredragon_usages.py."""
    return "plat" if cat in ("civique", "commerce") else "long"


def batir():
    """Les volumes du château, au format du bâti de Peyredragon."""
    par_id = {s["id"]: s for s in Li.lieux()}
    lignes, manquantes, effectif = [], [], 0
    for cle, (usage, cat, etages, postes) in CHATEAU.items():
        s = par_id.get(cle)
        if s is None:
            manquantes.append(cle)
            continue
        # Le plan donne le point et la demi-emprise ; la table des mesures donne
        # la hauteur. On ne redessine rien, on traduit.
        l, larg, haut = Li.mesures(cle)
        if cle in EMPRISE:
            l, larg = EMPRISE[cle]
        x = s["ou"][0] + DECALAGE[0]
        y = s["ou"][1] + DECALAGE[1]
        z = s["ou"][2]
        n = sum(p[4] for p in postes)
        effectif += n
        lignes.append([round(x, 1), round(y, 1), round(z, 1), 0.0,
                       round(l, 1), round(larg, 1), etages, round(haut, 1),
                       QUARTIER, usage, 0, cat, toit(cat), cle, n])
    return lignes, manquantes, effectif


COLONNES = ["x", "y", "z", "cap", "facade_m", "profondeur_m", "etages",
            "hauteur_m", "quartier", "usage", "cave", "cat", "toit"]


def main():
    vraiment = "--vraiment" in sys.argv
    lignes, manquantes, effectif = batir()

    print("Le château de Peyredragon — %d salles, %d corps prévus"
          % (len(lignes), effectif))
    print()
    print("  %-22s %-24s %-10s %7s %6s" % ("salle", "usage", "catégorie",
                                           "plancher", "corps"))
    for r in sorted(lignes, key=lambda r: -r[14]):
        pl = r[4] * r[5] * r[6]
        print("  %-22s %-24s %-10s %6.0f m² %5d" % (r[13], r[9], r[11], pl, r[14]))

    par_rang = {}
    for _u, _c, _e, postes in CHATEAU.values():
        for role, nom, _s, rang, n in postes:
            par_rang.setdefault(rang, 0)
            par_rang[rang] += n
    print()
    print("  par rang :", ", ".join("%s %d" % (k, v) for k, v in sorted(par_rang.items())))
    print("  postes tenus par un personnage nommé : %s"
          % ", ".join("%s → %s" % (r, i) for r, i in sorted(NOMMES.items())))
    if manquantes:
        print()
        print("  ! salles absentes du plan (rien posé) : %s" % ", ".join(manquantes))

    if not vraiment:
        print()
        print("  — essai à blanc. Relance avec --vraiment pour écrire dans")
        print("    monde/peyredragon.bati.json, puis :")
        print("      python scripts/monde/peupler.py peyredragon")
        return

    chemin = os.path.join(MONDE, "peyredragon.bati.json")
    B = json.load(io.open(chemin, encoding="utf-8"))
    if B["_colonnes"] != COLONNES:
        sys.exit("les colonnes du bâti ont changé : %s" % B["_colonnes"])
    # On retire d'abord ce qu'un passage précédent aurait posé : le script se
    # relance autant qu'on veut, et le bourg n'est jamais touché.
    C = {n: k for k, n in enumerate(B["_colonnes"])}
    avant = len(B["bati"])
    B["bati"] = [b for b in B["bati"] if b[C["quartier"]] != QUARTIER]
    B["bati"].extend([r[:13] for r in lignes])
    io.open(chemin, "w", encoding="utf-8").write(
        json.dumps(B, ensure_ascii=False, separators=(",", ":")))
    print()
    print("  %d volumes du bourg conservés, %d du château posés (%d avant)"
          % (len(B["bati"]) - len(lignes), len(lignes), avant))
    print("  -> monde/peyredragon.bati.json")


if __name__ == "__main__":
    main()
