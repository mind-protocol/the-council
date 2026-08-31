# -*- coding: utf-8 -*-
import json, io, os

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
L = "nera-le-dehors"
A = "⚔️ Actions"
V = "\U0001F512 Verrous"


def r(table, ligne, colonne, valeur):
    return {"livre": L, "table": table, "ligne": ligne,
            "colonne": colonne, "valeur": valeur}


c = []

c += [
 r(A, "68023", "\U0001F4DD Note",
   "CE QUE JE GARDE DE BON : je l'ai payé à MON PROPRE TARIF ÉCRIT, neuf "
   "sous et le pain, devant tout le marché — première fois que ma feuille "
   "s'applique à moi. Et c'est le clou qui a acheté sa réponse autant que ma "
   "franchise : un enfant qui vérifie de ses yeux, à trois pas, qu'on ne le "
   "vole pas sur ses neuf sous, croit le reste. || SA RÉPONSE, DU 3e AU SOIR : deux "
   "sous le matin depuis trois jours pour se tenir en haut de la venelle et compter ce "
   "qui entre à l'aire — charrois, hommes, ce qu'ils portent. PAYÉ EN "
   "PIÈCES NEUVES, par un homme qu'il sait décrire et pas nommer, qui vient à "
   "la même heure et NE DESCEND JAMAIS LUI-MÊME JUSQU'À L'AIRE. Ils sont "
   "trente sur cette grève. || MA FAUTE, ET ELLE ÉTAIT PIRE QUE CELLE QUE JE "
   "RÉPARAIS : j'avais écrit son double emploi sur mon livre, CHEZ MOI, EN "
   "PRIVÉ. Un observateur déclaré ne vaut plus rien à celui qui le paie "
   "SEULEMENT SI CELUI-LÀ APPREND QU'IL EST DÉCLARÉ. Tant que j'étais "
   "seule à le savoir, je n'avais pas désarmé un guetteur — j'avais fait un "
   "DOUBLE d'un enfant de douze ans sans en avertir la partie adverse, et c'est lui qui "
   "portait le risque de mon renseignement. Corrigé le soir même : les deux "
   "emplois sont CLOUÉS sur une planche à part, à côté de la feuille, "
   "lisibles de la venelle, sans nommer personne, avec écrit que je ne lui ai pas "
   "demandé d'arrêter et que je ne lui demande pas ce qu'il compte. J'y perds le "
   "gamin comme source, volontairement : je n'ai jamais voulu une source, je voulais "
   "qu'il cesse d'être un fil."),
]

# --- VERROU 68005 : les pieces neuves remontent a un changeur --------------
c += [
 r(V, "68005", "\U0001F512 N°", "**68005**"),
 r(V, "68005", "\U0001F3F7️ Le verrou",
   "\U0001FA99 La piste des PIÈCES NEUVES aboutit mécaniquement à un "
   "comptoir de change du Crochet — et trois métiers la remontent "
   "déjà, dont un manteau d'or"),
 r(V, "68005", "⛔ Bloque", "68000"),
 r(V, "68005", "\U0001F4CC Ce qui est vrai aujourd'hui",
   "Le chantier du bout paie en monnaie neuve : les guetteurs de la venelle sont "
   "payés deux sous le matin EN PIÈCES NEUVES, trente enfants sur cette "
   "grève, par un homme qui ne descend jamais lui-même à l'aire. Or une "
   "pièce neuve ne se cache pas — ELLE SE CHANGE, et il n'y a qu'un endroit "
   "dans ce quartier pour la changer sans laisser un nom : un banc de prêt sur gage. "
   "Le mien, avec trois cents cerfs usés dans le tiroir à toute heure. || ET LA "
   "PISTE EST DÉJÀ REMONTÉE PAR D'AUTRES : trois personnes en huit jours "
   "sont venues à un comptoir de ce quartier demander qui paie en pièces neuves "
   "— un commis, un portefaix, ET UN MANTEAU D'OR. Trois métiers, pas trois "
   "curieux. || CE QUI EN FAIT UN VERROU POUR 68000 : l'état cible veut qu'une "
   "demande de travaux arrive avec sa case de dépense ouverte, c'est-à-dire "
   "qu'on travaille au grand jour, par registre. Mais le quartier entier a une "
   "enquête en cours qui converge vers mon comptoir, et un banc que le Guet "
   "regarde ne reçoit plus de demandes écrites — il reçoit des "
   "convocations. Tant que la piste des pièces neuves n'a pas trouvé son terme "
   "ailleurs qu'ici, chaque jour de travail au clair m'expose davantage, parce que le clair "
   "est exactement ce qu'on regarde."),
 r(V, "68005", "\U0001F441️ La preuve",
   "Le gamin de la Claie, à mon comptoir le 3e de la 4e lune : deux sous le matin "
   "depuis trois jours, en pièces neuves, pour compter ce qui entre à l'aire de "
   "bris ; trente enfants sur la grève entre la Gadoue et le Boyau. Trois demandes "
   "en huit jours à un comptoir du quartier sur qui paie en pièces neuves — "
   "un commis, un portefaix, un manteau d'or. Et le change de la rue haute qui pèse, "
   "mord, rend 202 sur 210, ET NOTE : on ne va pas chez Pate avec de la monnaie qu'on ne "
   "peut pas nommer."),
 r(V, "68005", "\U0001F513 Levé quand",
   "Quand je saurai ce que la piste des pièces neuves a déjà trouvé, et par "
   "quelle bouche — ou quand ma propre caisse ne pourra plus être la "
   "réponse à la question qu'ils posent. L'un des deux, pas les deux."),
]

chemin = os.path.join(RACINE, "etat", "rapports", "_sirel-pieces-neuves.json")
with io.open(chemin, "w", encoding="utf-8") as f:
    json.dump({"qui": "sirel-quintaine", "quand": "129.4.3", "cahier2": c},
              f, ensure_ascii=False, indent=1)
print("ecrit :", len(c), "coordonnees ->", os.path.normpath(chemin))
