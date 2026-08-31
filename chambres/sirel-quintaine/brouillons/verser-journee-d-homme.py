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

c += [
 r(V, "68106", "\U0001F512 N°", "**68106**"),
 r(V, "68106", "\U0001F3F7️ Le verrou",
   "\U0001F464 Toute la moitié « journée d'homme » de ma feuille "
   "repose sur UNE bouche, en UNE phrase, et cette bouche n'est pas ce qu'elle dit "
   "être"),
 r(V, "68106", "⛔ Bloque", "68100"),
 r(V, "68106", "\U0001F4CC Ce qui est vrai aujourd'hui",
   "Le bois de ma feuille porte désormais trois papiers concordants et un "
   "étalon qu'on refait au cordeau. LA JOURNÉE D'HOMME NE PORTE RIEN DE TOUT "
   "ÇA. Vingt-six sous le manœuvre au bris, corrigés de quarante-trois "
   "le 3e au matin par un homme qui s'est présenté à mon étal, m'a "
   "reprise en une phrase — trente-six journées font seize cerfs quarante et non "
   "vingt-huit — et s'en est allé. J'ai porté la correction sur la feuille le "
   "jour même, et cette ligne va partir demain à toutes les aires du quartier. "
   "|| Or Marlo Vasse m'écrit le 3e au soir : cet homme est chez lui DEPUIS PEU, "
   "SANS MÉTIER ANNONCÉ, et c'est PAR LUI QUE PASSE CE QUI SORT DE CHEZ LUI. Sa "
   "phrase : « un manœuvre qui reprend une prêteuse sur son propre calcul, "
   "à son étal, en une phrase, n'est pas un manœuvre. » || CE QUI EN FAIT "
   "UN VERROU ET NON UNE INQUIÉTUDE : ce n'est pas que le chiffre soit faux — il "
   "est probablement juste, c'est bien ce qui m'a convaincue. C'est qu'IL N'A PAS DE "
   "PROCÉDÉ DERRIÈRE LUI. Le jour où un tiers tend ma feuille et qu'un "
   "acheteur conteste vingt-six sous, le tiers n'a rien à répondre : ni un "
   "second chiffre, ni un geste à refaire, ni un homme à citer. J'ai "
   "exigé un étalon pour un rouleau de corde et j'ai accepté un nombre pour "
   "le prix d'un homme. C'est la moitié de ma feuille."),
 r(V, "68106", "\U0001F441️ La preuve",
   "Ma feuille, section I, note sous le tableau : « Trente-six journées de "
   "manœuvre font 16 cerfs 40, et non 28 — je l'ai écrit faux ce matin "
   "même du 3e, un manœuvre m'a reprise. » Une seule source, orale, non "
   "répétée, non vérifiée à la paie. Et le billet de Marlo Vasse du 3e "
   "au soir sur cet homme, avec sa demande expresse : *« je ne vous demande rien sur "
   "lui et je ne veux pas que vous lui parliez. »*"),
 r(V, "68106", "\U0001F513 Levé quand",
   "Quand la journée d'homme portera ce que le bois porte déjà : non pas un "
   "chiffre de plus, mais LA MANIÈRE DONT ELLE SE PAIE — à la marée "
   "ou au jour, le pain compté dedans ou à côté, ce qu'on retient pour "
   "l'outil — établie auprès de ceux qui la reçoivent, un jour de paie, "
   "et sans passer par cet homme-là."),
]

c += [
 r(C, "68115", "\U0001F5DD️ N°", "**68115**"),
 r(C, "68115", "\U0001F3F7️ La clef",
   "\U0001F44B Demander la MANIÈRE et non le nombre — la journée d'homme "
   "s'établit chez ceux qui la reçoivent, un jour de paie"),
 r(C, "68115", "\U0001F513 Ouvre", "68106"),
 r(C, "68115", "\U0001F4A1 Le principe",
   "Hann Bourbe m'a montré la forme sur le rouleau : je demandais une longueur, il "
   "m'a donné deux fiches et treize tours. **Une unité n'est pas fondée par "
   "un second chiffre, elle est fondée par un geste que n'importe qui peut "
   "refaire.** La journée d'homme a le sien, et il est public : c'est LA PAIE. On "
   "n'y demande à personne combien vaut un manœuvre — on regarde ce qu'on "
   "lui met dans la main, à quelle heure, et ce qu'on en retire. À la "
   "marée ou au jour ? le pain compté dedans ou à côté ? "
   "qu'est-ce qu'on retient pour l'outil, pour la lampe, pour l'eau ? Ces "
   "réponses-là ne se falsifient pas, parce qu'elles se disent devant six "
   "hommes qui viennent d'être payés. || Et elles valent mieux qu'un nombre : "
   "un acheteur qui conteste vingt-six sous se tait devant « ils sont payés "
   "à la marée, pain compté dedans, et on retient deux sous pour "
   "l'outil ». On ne discute pas une manière, on la vérifie ou on se "
   "tait."),
 r(C, "68115", "\U0001F4B0 Ce qu'elle coûte et ce qu'elle ferme",
   "Une matinée de paie, et la patience d'attendre le bon jour. || Elle ferme, ET "
   "C'EST LE POINT, la voie courte : je ne retourne pas voir l'homme qui m'a "
   "reprise. Marlo me l'a demandé, et ma propre journée me l'interdit — une "
   "approche se paie avec la peau de quelqu'un, et cet homme-là est place chez lui, "
   "pas chez moi. Je perds la source la plus commode que j'aie eue de la journée "
   "pour la seule raison qu'elle n'est pas à moi."),
 r(C, "68115", "\U0001F441️ La preuve attendue",
   "La ligne de la journée d'homme portant, comme le rouleau, un procédé "
   "et non un chiffre seul — et un tiers qui défend vingt-six sous devant un "
   "acheteur sans me citer."),
 r(C, "68115", "⚖️ Décision",
   "**retenue le 3e au soir**, dès que Marlo m'a dit ce qu'il savait de cette "
   "bouche. Le chiffre reste sur la feuille : il est vraisemblable et il m'a "
   "corrigée d'une faute réelle. C'est sa FONDATION qui manque, pas sa "
   "valeur."),
]

c += [
 r(A, "68125", "⚔️ N°", "**68125**"),
 r(A, "68125", "\U0001F3F7️ L'action",
   "\U0001F44B Relever la manière dont se paie la journée, un jour de paie, "
   "chez ceux qui la reçoivent"),
 r(A, "68125", "\U0001F5DD️ Réalise", "68115"),
 r(A, "68125", "\U0001F4DD Ce qu'on fait",
   "Attendre un jour de paie à l'aire de bris de la vase et regarder, sans "
   "demander de chiffre à personne : à la marée ou au jour ? le pain "
   "compté dedans ou donné en plus ? ce qu'on retient pour l'outil, pour la "
   "lampe, pour l'eau ? qui touche double et pourquoi ? Écrire la "
   "MANIÈRE sous la ligne des vingt-six sous, comme l'étalon du rouleau est "
   "écrit sous celle du bordé. || TROIS INTERDITS QUE JE M'ÉCRIS À "
   "MOI-MÊME. Ne pas parler à l'homme qui m'a reprise : Marlo me l'a "
   "demandé, et cet homme est placé chez lui. Ne pas demander à Marlo ce "
   "qu'il sait de plus : il m'a dit ce qu'il jugeait devoir, et réclamer la suite "
   "serait lui faire payer sa franchise. Ne pas envoyer d'enfant."),
 r(A, "68125", "\U0001F4CD Où", "L'aire de bris de la vase, un jour de paie"),
 r(A, "68125", "\U0001FAB6 Office", "O21"),
 r(A, "68125", "\U0001F9F0 Moyens", "M05"),
 r(A, "68125", "⛓️ Dépend de", "68123"),
 r(A, "68125", "\U0001F4C5 Jour dû",
   "avant le 15e de la 4e lune — les copies partent demain avec cette ligne "
   "non fondée ; chaque jour de retard est un jour où elle circule sans "
   "appui"),
 r(A, "68125", "⏳ Où ça en est", "à faire"),
 r(A, "68125", "\U0001F4DD Note",
   "CE QUE J'AI FAIT DE MAL AVEC CE NOM, ET QUE J'ÉCRIS POUR NE PAS LE REFAIRE : "
   "j'ai nommé cet homme par écrit à Hann Bourbe le 3e au soir, dans le "
   "billet des prix corrigés, avant de savoir ce qu'il était. Troisième "
   "fois du jour que je dépense la couverture d'autrui sans l'avoir comptée "
   "— Ollo Marran, le gamin de la Claie, et lui. La règle est écrite "
   "depuis ce matin et je l'ai enfreinte trois fois dans la même journée : "
   "ça veut dire qu'elle n'est pas encore un réflexe, seulement une phrase."),
]

chemin = os.path.join(RACINE, "etat", "rapports", "_sirel-journee-d-homme.json")
with io.open(chemin, "w", encoding="utf-8") as f:
    json.dump({"qui": "sirel-quintaine", "quand": "129.4.3", "cahier2": c},
              f, ensure_ascii=False, indent=1)
print("ecrit :", len(c), "coordonnees ->", os.path.normpath(chemin))
