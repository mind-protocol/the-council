# -*- coding: utf-8 -*-
import json, io, os

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
L = "nera-le-dehors"
A = "⚔️ Actions"


def r(table, ligne, colonne, valeur):
    return {"livre": L, "table": table, "ligne": ligne,
            "colonne": colonne, "valeur": valeur}


c = [
 r(A, "68121", "⚔️ N°", "**68121**"),
 r(A, "68121", "\U0001F3F7️ L'action",
   "\U0001F9FE Faire tenir la colonne des démentis par une main qui n'est pas la "
   "mienne — et que la première entrée qu'elle y porte soit contre moi"),
 r(A, "68121", "\U0001F5DD️ Réalise", "68111"),
 r(A, "68121", "\U0001F4DD Ce qu'on fait",
   "LA COLONNE EXISTE DEPUIS LE 3e AU SOIR : sur toutes les copies, y compris celles qui "
   "sortent, chaque chiffre du marché qui contredit ma ligne est écrit avec trois "
   "réponses à côté — l'étalon a-t-il été mesuré ? le vendeur "
   "avait-il une échéance dans les trois jours ? l'acheteur a-t-il un nom au "
   "rôle ? Elle porte deux entrées, et les deux sont de moi : le rouleau à neuf "
   "cerfs du 27e, et MA PROPRE VENTE — 266 cerfs comptant le 30e pour 143 de bois, "
   "trois « non » sur trois. || CE QUI RESTE À FAIRE, ET C'EST TOUT LE "
   "TRAVAIL : une colonne que son auteur remplit seul n'est pas un critère, c'est une "
   "plaidoirie. Je la remets donc à HANN BOURBE, charpentier du chantier de la vase, "
   "qui n'a plus dit un chiffre le premier depuis 106 et qui est par là même "
   "l'homme du monde le mieux fait pour s'en servir : il ne cite un prix que s'il peut "
   "montrer d'où il vient. Je lui demande UNE chose, écrite, avec le jour — "
   "qu'à la prochaine vente de bois de coque qui passera au port sous ma ligne, il "
   "porte lui-même l'entrée dans la colonne, et qu'il la porte MÊME SI ELLE "
   "ME DONNE TORT. Et je lui ai déjà donné le gage de bonne foi : c'est moi "
   "qui ai inscrit, de ma main, que son rouleau du 27e n'était pas comparable au mien "
   "faute d'avoir été mesuré — donc que son neuf ne prouve rien contre le "
   "bordé de la Néra."),
 r(A, "68121", "\U0001F4CD Où",
   "L'étal de Sirel pour la feuille clouée ; le chantier de la vase pour la "
   "copie de Hann Bourbe"),
 r(A, "68121", "\U0001FAB6 Office", "O21"),
 r(A, "68121", "\U0001F9F0 Moyens", "M05"),
 r(A, "68121", "⛓️ Dépend de", "68122"),
 r(A, "68121", "\U0001F4C5 Jour dû",
   "la colonne est écrite le 3e ; la première entrée d'une autre main, avant "
   "le 15e de la 4e lune — au-delà, c'est que le critère ne se manie "
   "pas sans moi et qu'il faut le simplifier"),
 r(A, "68121", "⏳ Où ça en est", "en cours"),
 r(A, "68121", "\U0001F4DD Note",
   "L'ÉPREUVE EST ÉTROITE ET JE L'ÉCRIS D'AVANCE POUR NE PAS POUVOIR LA "
   "DÉPLACER : la clef 68111 n'est tenue que le jour où un chiffre du port "
   "sera écarté par quelqu'un d'autre que moi, en citant la colonne, moi absente. "
   "Si Hann porte l'entrée mais qu'il me la demande avant de l'écrire, c'est "
   "raté — c'est encore ma tête dans la pièce, sous un autre nom. || Billet "
   "porté le 3e au soir, avec les prix corrigés et la raison."),
]

chemin = os.path.join(RACINE, "etat", "rapports", "_sirel-colonne.json")
with io.open(chemin, "w", encoding="utf-8") as f:
    json.dump({"qui": "sirel-quintaine", "quand": "129.4.3", "cahier2": c},
              f, ensure_ascii=False, indent=1)
print("ecrit :", len(c), "coordonnees ->", os.path.normpath(chemin))
