# -*- coding: utf-8 -*-
import json, io, os

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
L = "nera-le-dehors"
V = "\U0001F512 Verrous"
C = "\U0001F5DD️ Clefs"
A = "⚔️ Actions"


def r(table, ligne, colonne, valeur):
    return {"livre": L, "table": table, "ligne": ligne,
            "colonne": colonne, "valeur": valeur}


c = []

# --- VERROU 68004 : mes deux commerces au meme comptoir --------------------
c += [
 r(V, "68004", "\U0001F512 N°", "**68004**"),
 r(V, "68004", "\U0001F3F7️ Le verrou",
   "\U0001FA9F Ma feuille et mon tiroir ne peuvent pas être lus ensemble — "
   "j'ai cloué en place publique une règle qui exclut ma meilleure "
   "clientèle, à trois pas du banc où je la sers"),
 r(V, "68004", "⛔ Bloque", "68000"),
 r(V, "68004", "\U0001F4CC Ce qui est vrai aujourd'hui",
   "Le dos de ma feuille est désormais lisible de tout le marché du Crochet, et "
   "il porte la deuxième question : QUI L'ÉCRIT — NOM DU PAYEUR ET REGISTRE. "
   "Or mon vrai fonds de commerce est exactement l'inverse : je vends de la monnaie "
   "d'usage sans nom en face, trois cents cerfs usés dans mon tiroir à toute "
   "heure, et c'est ce qui me vaut la visite de tous ceux qui ont de l'or qu'ils ne "
   "peuvent pas nommer. LES DEUX PAPIERS SONT VRAIS ET ILS SE CONTREDISENT À TROIS "
   "PAS L'UN DE L'AUTRE. || CE QUI EN FAIT UN VERROU POUR 68000, ET CE N'EST PAS UNE "
   "gêne de conscience : un homme qui A une case de dépense et un registre "
   "où l'écrire ne veut pas être vu au comptoir de celle qui sert ceux qui "
   "n'en ont pas. Les deux clientèles ne se croisent pas sans que l'une parte, et "
   "c'est toujours celle qui écrit qui part — elle a plus à perdre. Trois "
   "demandes de travaux avec leur case ne viendront donc jamais à un banc "
   "réputé pour l'autre commerce, quel que soit le barème affiché "
   "au-dessus."),
 r(V, "68004", "\U0001F441️ La preuve",
   "Ma feuille de prix des Chantiers de la Néra, dos, question 2, clouée à "
   "mon banc le 3e de la 4e lune en pleine vue du marché. Et, dans le même "
   "banc : l'or dépareillé de trois règnes pesé le 1er, sans usure de "
   "circulation, aucune quittance réclamée ; les neuf dégagements en six jours "
   "des livres de gage des quatre marches, dont six payés en dragons entiers non "
   "rognés que Pate n'a ni pesés ni inscrits. Le change de la rue haute pèse, "
   "mord, rend 202 sur 210 — ET NOTE. On vient chez moi pour ne pas être "
   "noté."),
 r(V, "68004", "\U0001F513 Levé quand",
   "Quand les deux commerces auront chacun leur heure, leur lieu et leur livre, et "
   "qu'aucun client de l'un n'aura à croiser un client de l'autre pour être "
   "servi."),
]

# --- CLEF 68013 -----------------------------------------------------------
c += [
 r(C, "68013", "\U0001F5DD️ N°", "**68013**"),
 r(C, "68013", "\U0001F3F7️ La clef",
   "\U0001F551 Deux commerces, deux heures, deux lieux — séparer par le "
   "calendrier ce qu'on ne peut pas séparer par le silence"),
 r(C, "68013", "\U0001F513 Ouvre", "68004"),
 r(C, "68013", "\U0001F4A1 Le principe",
   "On ne cache pas un commerce dont on vit, et on ne renonce pas au meilleur des deux : "
   "on les empêche d'être vus ensemble. LE BOIS SE TRAITE À L'AIRE, de jour, "
   "sous l'auvent de Marlo Vasse, à la feuille, devant témoins, et le devis se "
   "porte au registre de celui qui paie. LE CHANGE SE TRAITE À MON BANC, "
   "après la dernière cloche, comptant, sans écrit, chose contre chose. "
   "Aucun homme du premier commerce n'a de raison d'être là quand se fait le "
   "second, et réciproquement. || La forme m'a été donnée sans que je la "
   "demande, par Ollo Marran, ce même soir : il viendra un jour d'affluence "
   "APRÈS LA DERNIÈRE CLOCHE acheter du fil poissé et de la corde à "
   "ligne, comptant, rien d'inscrit. Un commis qui rapporte de la corde n'a pas besoin "
   "d'une raison écrite d'être venu — il a la corde. C'était "
   "déjà l'usage sans que personne l'ait nommé ; je le nomme et j'en fais la "
   "règle de la maison."),
 r(C, "68013", "\U0001F4B0 Ce qu'elle coûte et ce qu'elle ferme",
   "Elle coûte mes soirées et la commodité d'un seul comptoir. Et elle ferme "
   "ceci, qui était ma position la plus confortable et que j'écris pour "
   "n'avoir pas à me la reprocher plus tard : je ne pourrai plus faire d'un client "
   "du change un client du bois dans la même conversation, ni me servir de ce que "
   "j'apprends au tiroir pour placer une pièce à l'aire. Les deux livres ne se "
   "parlent plus. C'est cher, et c'est le prix de pouvoir tenir les deux."),
 r(C, "68013", "\U0001F441️ La preuve attendue",
   "Un homme qui a une case de dépense et un registre où l'écrire conclut un "
   "devis des Chantiers à l'aire, de jour — et l'on ne peut lui citer aucun "
   "motif de n'être pas venu."),
 r(C, "68013", "⚖️ Décision",
   "**retenue le 3e au soir**, contre un défaut que je n'avais pas vu en clouant "
   "ma propre feuille : elle exclut, en place publique, la clientèle dont je vis, "
   "à trois pas du tiroir où je la sers."),
]

# --- ACTION 68023 ---------------------------------------------------------
c += [
 r(A, "68023", "⚔️ N°", "**68023**"),
 r(A, "68023", "\U0001F3F7️ L'action",
   "\U0001FAA7 Me poser à moi-même ma deuxième question — écrire sur "
   "mon livre qui d'autre paie mon commis, et ouvrir les deux comptoirs"),
 r(A, "68023", "\U0001F5DD️ Réalise", "68013"),
 r(A, "68023", "\U0001F4DD Ce qu'on fait",
   "DEUX GESTES, ET LE PREMIER EST UNE RÉPARATION DE MA PROPRE FAUTE. || I. LE "
   "COMMIS. J'ai embauché le gamin de la Claie à mon comptoir, neuf sous et le "
   "pain, mon tarif affiché, devant tout le monde — et sans lui poser LA "
   "DEUXIÈME QUESTION DE MON PROPRE DOS : qui l'écrit, nom du payeur, "
   "registre. Or l'on paie des gosses de ce quartier depuis trois jours pour compter ce "
   "qui entre à l'aire de bris, et trente d'entre eux peignent la grève entre la "
   "Gadoue et le Boyau pour une femme qui partage. En prendre un à gages sans "
   "demander ne le sort pas de ce réseau : ça lui donne un observateur "
   "payé À MA LAMPE, à côté de mes plis. Je lui demande donc, à mon "
   "comptoir, en lui disant d'abord pourquoi et que c'est ma faute et non la sienne : QUI "
   "D'AUTRE TE PAIE, COMBIEN, POUR QUOI FAIRE. J'écris la réponse sur mon livre "
   "de gage avec le jour, comme une avance, et je surpaie la différence à mon "
   "tarif affiché — pour que ce qu'il me dit soit ACHETÉ et non "
   "arraché. Un double emploi écrit n'est plus un espion : c'est un "
   "observateur déclaré, et un observateur déclaré ne vaut plus rien "
   "à celui qui le paie. || II. LES DEUX COMPTOIRS. Le bois de jour, à l'aire, "
   "à la feuille, devant témoins. Le change à mon banc après la "
   "dernière cloche, comptant, chose contre chose, rien d'inscrit. Deux heures, deux "
   "lieux, deux livres qui ne se parlent pas."),
 r(A, "68023", "\U0001F4CD Où",
   "L'étal de Sirel pour la question et le livre de gage ; l'aire de bris de la vase "
   "pour le bois, désormais"),
 r(A, "68023", "\U0001FAB6 Office", "O21"),
 r(A, "68023", "\U0001F9F0 Moyens", "M05"),
 r(A, "68023", "⛓️ Dépend de", "68022"),
 r(A, "68023", "\U0001F4C5 Jour dû", "129.4.3 pour la question ; la règle des deux comptoirs court à partir du 4e"),
 r(A, "68023", "⏳ Où ça en est", "en cours"),
 r(A, "68023", "\U0001F4DD Note",
   "CE QUI EST BON DANS L'EMBAUCHE ET QUE JE GARDE : je l'ai payé à MON "
   "PROPRE TARIF ÉCRIT, neuf sous et le pain, devant tout le monde. C'est la "
   "première fois que ma feuille s'applique à moi. Une embauche faite au prix "
   "affiché n'est pas une faveur, c'est un fait de registre, et celle-là ne se "
   "relit pas de travers. || CE QUI RESTE MAUVAIS ET QUE JE N'EFFACE PAS : le gamin est "
   "allé à la grille et se tient maintenant à mon banc tous les jours, au vu de "
   "quiconque l'a vu là-bas. Je ne l'ai pas retiré de la piste, je l'ai mis au "
   "bout de la piste avec une lampe. La question écrite ne défait pas ça — "
   "elle rend seulement inutile de le suivre."),
]

chemin = os.path.join(RACINE, "etat", "rapports", "_sirel-deux-comptoirs.json")
with io.open(chemin, "w", encoding="utf-8") as f:
    json.dump({"qui": "sirel-quintaine", "quand": "129.4.3", "cahier2": c},
              f, ensure_ascii=False, indent=1)
print("ecrit :", len(c), "coordonnees ->", os.path.normpath(chemin))
