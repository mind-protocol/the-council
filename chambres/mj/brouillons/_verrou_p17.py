# -*- coding: utf-8 -*-
"""P.17 — le verrou mesure le 129.4.3 : la porte refuse en silence."""
import json, io

F = 'chambres/mj/books/affaire-la-porte.json'
d = json.load(io.open(F, encoding='utf-8'))

VERROU = [
    "**P.17**",
    "\U0001f92b Le vocabulaire de la porte ne couvre pas ce que les regies "
    "produisent — et **son refus est muet, ou pire, il a le ton du succes**",
    "P.1 — *intitule efface le 129.4.9, a recoupler apres remesure*",
    "**MESURE CE MATIN, DEUX INSTANCES, MEME CLASSE.** (1) `appliquer.py` n'a "
    "AUCUNE operation pour la table `actes` : le domaine s'arrete a books, "
    "declencheurs, evenements, intentions, jetons, lieux, mains, monde, "
    "orbite, personnages, plis, relations, royaume, scene. Faute de mot, "
    "quatre regies ont ecrit leurs actes dans un bloc de prose `a_la_main` — "
    "et la porte a repondu *aucune mutation dans mutations_proposees, rien a "
    "appliquer*, **sur le ton d'un succes**. 18 actes de la journee du 3e "
    "dormaient ainsi, dont la reine scellant ses seize copies et le "
    "contre-registre des mains de Gerardys. (2) `CHAMPS_PERSO` vaut "
    "exactement `(lieu_id, condition, etat)` : un homme peut se deplacer, "
    "etre blesse ou mourir, et **rien d'autre de lui ne peut jamais entrer**. "
    "Le passe de Rulf Corne — la jambe prise au mole en 107, d'ou ses "
    "vingt-deux ans se comptent — a ete refuse au champ pres.",
    "18 actes verses A LA MAIN le 129.4.3 par `scripts/ajouter.py actes` "
    "(actes.json 552 -> 570), apres qu'`appliquer.py` a rendu *rien a "
    "appliquer* sur 24 pieces en attente. Refus reproductible : "
    "`etat/staging/20260831-mj-rulf-passe-verse.json` -> *champs de "
    "personnage interdits : passe*. Le compte des blocs orphelins est de "
    "14 sur 55 pieces non appliquees, dont 11 de mj-peyredragon seule.",
    "Quand une proposition qui contient du travail non traduisible **ne peut "
    "plus etre rendue silencieusement** : `appliquer.py` refuse net une piece "
    "dont `mutations_proposees` est vide alors qu'un bloc `a_la_main` ou "
    "`actes_a_ajouter` existe, en nommant la table visee. La deuxieme moitie "
    "— ouvrir `acte_ajouter` et un champ libre de fiche — n'est pas "
    "necessaire au verrou : **c'est le silence qui coute, pas le refus.**",
]

ACTION = [""] * 16
COLS = [c for c in d['tables'][5]['colonnes']]
def pose(nom, val):
    ACTION[COLS.index(nom)] = val
pose("⚔️ N°", "**P.18**")
pose("\U0001f3f7️ L'action",
     "\U0001f507 Faire crier la porte quand elle ne sait pas traduire")
pose("\U0001f5dd️ Réalise", "P.17")
pose("\U0001f4dd Ce qu'on fait",
     "Dans `etat/mutations/cli.py` : si `mutations_proposees` est vide ET "
     "qu'un des blocs `a_la_main`, `actes_a_ajouter`, `entrees_proposees`, "
     "`annales_a_ajouter` est present et non vide, sortir en ERREUR en "
     "nommant la table visee et la porte qui la sert "
     "(`scripts/ajouter.py <table>`), au lieu du message actuel *aucune "
     "mutation dans mutations_proposees — rien a appliquer*, qui se lit "
     "comme une piece traitee.")
pose("\U0001f4cd Où", "scripts/etat/mutations/cli.py")
pose("\U0001fab6 Office", "la porte")
pose("\U0001f464 Qui", "dev")
pose("\U0001f6e0️ Avec quoi" if "\U0001f6e0️ Avec quoi" in COLS
     else "\U0001f527 Avec quoi", "cli.py, vocabulaire.py")
pose("\U0001f4b0 Ce qu'elle coûte", "une garde, pas un domaine neuf")
pose("\U0001f441️ La preuve",
     "Repasser les 24 pieces sans mutation du 129.4.3 : celles qui portent un "
     "bloc orphelin doivent sortir en erreur nommee, les autres en *rien a "
     "appliquer*.")
pose("⏳ État", "a faire")
pose("\U0001f4dd Note",
     "Trouve en versant 18 actes a la main le 129.4.3. Le correctif ne "
     "traduit rien — il empeche seulement qu'un travail non traduit passe "
     "pour un travail traite.")

d['tables'][3]['lignes'].append({"cellules": VERROU})
d['tables'][5]['lignes'].append({"cellules": ACTION})

with io.open(F, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=1)
print("P.17 (verrou) et P.18 (action, a dev) poses dans affaire-la-porte")
print("verrous :", len(d['tables'][3]['lignes']),
      "| actions :", len(d['tables'][5]['lignes']))
