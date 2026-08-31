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

# --- 68101 : LEVE ---------------------------------------------------------
c += [
 r(V, "68101", "\U0001F3F7️ Le verrou",
   "\U0001F4C4 **LEVÉ LE 3e AU SOIR.** Il n'existait aucune fourchette "
   "écrite : le prix des Chantiers était dans ma tête"),
 r(V, "68101", "\U0001F513 Levé quand",
   "**LEVÉ, ET MIEUX QUE PAR UNE FEUILLE — PAR TROIS PAPIERS QUI TOMBENT SUR LE "
   "MÊME NOMBRE.** (1) Mon barème, écrit et signé le 3e de la 4e lune. "
   "(2) Le devis de Marlo Vasse, écrit de sa main la nuit du 25e de la 3e lune, sans "
   "m'avoir vue chiffrer : mon barème appliqué à son stock rend DEUX CENT "
   "VINGT-HUIT CERFS, au cerf près son propre total. (3) ET L'ACTE DU 23e DE LA 3e "
   "LUNE, de la main de Hann Bourbe, passé sous l'auvent à la nuit devant Marlo "
   "Vasse ET NEL BEC, pour ces mêmes dix-huit membrures et ces deux rouleaux : "
   "« UN PEU PLUS D'UN DRAGON D'OR AU PRIX DES QUAIS », mot pour mot. Deux cent "
   "vingt-huit cerfs à deux cent dix le dragon font un dragon et dix-huit cerfs. "
   "|| TROIS MAINS, TROIS PAPIERS, DIX JOURS D'ÉCART, LE MÊME NOMBRE — et "
   "l'un des trois dit EN TOUTES LETTRES d'où le nombre vient. Ma feuille n'est donc "
   "pas un tarif de prêteuse et ce n'est plus une prétention : "
   "**C'EST LE PRIX DES QUAIS TRANSCRIT.** On pouvait me dire que j'affichais haut ; on "
   "ne le pourra plus, et la preuve sort du carnet de l'homme qui m'a vendu le lot."),
]

# --- VERROU 68105 ---------------------------------------------------------
c += [
 r(V, "68105", "\U0001F512 N°", "**68105**"),
 r(V, "68105", "\U0001F3F7️ Le verrou",
   "⚖️ Je suis à la fois l'auteur du barème ET la créancière "
   "d'un de ses signataires — aucune bouche tierce ne peut porter une feuille "
   "dont l'auteur a de l'argent à recouvrer chez le vendeur"),
 r(V, "68105", "⛔ Bloque", "68100"),
 r(V, "68105", "\U0001F4CC Ce qui est vrai aujourd'hui",
   "Marlo Vasse me doit onze dragons d'or contre la coque en gage, et depuis le "
   "recompte du 3e il me doit en outre CENT VINGT-TROIS CERFS sur le lot — "
   "quatre-vingt-cinq de bois déjà vendu que son devis portait encore, "
   "trente-huit que j'ai posés exprès sur sa paie. Trente-huit cerfs font 2 128 "
   "sous ; à 142 sous la journée de six bras, ce sont QUINZE JOURNÉES "
   "PLEINES D'HOMMES que j'ai payées, et c'est ainsi que ça se lira. || Et c'est "
   "moi qui ai écrit le barème qu'il vient de signer. || CE QUI EN FAIT UN "
   "VERROU POUR 68100 : le jour où un tiers présente ma feuille et qu'un "
   "acheteur apprend que l'auteur du barème est créancière de l'aire, "
   "le devis ne se défend plus — il se lit comme un recouvrement. Le tiers n'a "
   "aucune réponse, parce que la réponse n'est pas dans les chiffres : elle "
   "est dans ma bourse. Une feuille dont l'auteur a de l'argent à prendre chez un "
   "signataire n'est pas un relevé, quels que soient le nombre de mains au bas et "
   "l'exactitude des lignes."),
 r(V, "68105", "\U0001F441️ La preuve",
   "Le gage : onze dragons d'or avec l'intérêt contre la coque du chantier. Le "
   "recompte du 3e : 143 cerfs de bois à mes prix contre 266 comptés comptant le "
   "30e au soir, 123 d'écart. Et sa lettre du 3e au soir, où il tient les "
   "quatre-vingt-cinq pour une dette après même avoir signé : « un menteur "
   "SAIT ce qu'il écrit, moi je ne le savais pas, et ma signature valait pareil au "
   "bas de la feuille ». La créance est reconnue des deux côtés, "
   "écrite, et elle est dans la même main que le barème."),
 r(V, "68105", "\U0001F513 Levé quand",
   "Quand la créance et le barème ne seront plus dans la même main "
   "— soldée en toutes lettres sur la feuille elle-même, ou cédée "
   "à un tiers, mais pas gardée en silence. Un créancier discret est pire "
   "qu'un créancier déclaré : on le découvre au mauvais moment."),
]

# --- CLEF 68114 -----------------------------------------------------------
c += [
 r(C, "68114", "\U0001F5DD️ N°", "**68114**"),
 r(C, "68114", "\U0001F3F7️ La clef",
   "\U0001F9FE Solder les cent vingt-trois cerfs SUR LA FEUILLE ELLE-MÊME, en "
   "toutes lettres et à la date — le prix d'un relevé qu'un tiers "
   "puisse porter"),
 r(C, "68114", "\U0001F513 Ouvre", "68105"),
 r(C, "68114", "\U0001F4A1 Le principe",
   "Une créance ne se recouvre pas comme une querelle, et les deux ne "
   "s'éteignent pas de la même façon. Mon grief n'est pas contre "
   "l'honnêteté de cette maison — le devis n'a pas menti, il a recopié — "
   "il est contre sa méthode ; et cette maison a passé la nuit à "
   "installer exactement ce qui l'aurait empêchée : un livre d'entrées à la "
   "barrière, une colonne pour ce qui dort, l'étalon du rouleau, et la "
   "règle qu'on ne redit pas un chiffre sans dire l'heure où on l'a "
   "relevé. On me doit cent vingt-trois cerfs d'une faute QUI NE PEUT PLUS SE "
   "REFAIRE. || Alors je les écris, et je les éteins au même endroit : "
   "SUR LA FEUILLE, sous les trois signatures, avec le jour. *Sirel Quintaine "
   "déclare éteinte, au 3e jour de la 4e lune, toute créance sur "
   "l'aire de bris de la vase née du lot de la Néra — cent vingt-trois cerfs, "
   "dont quatre-vingt-cinq de compte et trente-huit de son propre fait.* || Ce n'est pas "
   "de la générosité et il ne faut pas que ça en ait l'air : c'est **le prix "
   "d'achat de la neutralité de ma propre feuille**. Une page dont l'auteur a "
   "publiquement renoncé à ce qu'on lui doit se laisse porter par n'importe "
   "quelle bouche ; une page dont l'auteur est créancier ne se laisse porter par "
   "personne."),
 r(C, "68114", "\U0001F4B0 Ce qu'elle coûte et ce qu'elle ferme",
   "CENT VINGT-TROIS CERFS, comptés, à moi, perdus — plus d'un demi-dragon, "
   "et quinze journées de six bras. C'est de loin ce que ma prise en main du dehors "
   "m'aura coûté de plus cher, et c'est en or, pas en encre. || Elle ferme le "
   "précédent qui m'arrangeait : à partir de là, un mauvais compte chez un "
   "vendeur avec qui je travaille ne se paie plus. Je l'écris pour l'avoir vu, et je le "
   "borne : cela vaut pour CE lot, à CETTE date, sur une faute de méthode "
   "réparée dans les vingt-quatre heures. Pas pour la suivante, et les onze "
   "dragons du gage ne sont pas touchés — le gage n'est pas né du lot."),
 r(C, "68114", "\U0001F441️ La preuve attendue",
   "Un devis des Chantiers conclu par un tiers, moi absente, sans que l'acheteur ait "
   "posé la question de ce que l'aire me doit — parce que la feuille y "
   "répond avant lui."),
 r(C, "68114", "⚖️ Décision",
   "**retenue le 3e au soir.** Marlo avait déjà offert de payer les "
   "quatre-vingt-cinq en encre ; j'ai déjà écrit que je ne les lui "
   "rappellerais plus. Je vais au bout du geste plutôt que de m'arrêter au milieu, "
   "parce qu'une créance à moitié éteinte se lit comme une "
   "créance entière."),
]

# --- ACTION 68124 ---------------------------------------------------------
c += [
 r(A, "68124", "⚔️ N°", "**68124**"),
 r(A, "68124", "\U0001F3F7️ L'action",
   "\U0001F9FE Porter l'acte du 23e en tête des concordances, et éteindre "
   "les 123 cerfs sous les signatures"),
 r(A, "68124", "\U0001F5DD️ Réalise", "68114"),
 r(A, "68124", "\U0001F4DD Ce qu'on fait",
   "DEUX LIGNES SUR LA FEUILLE, ET ELLES VONT ENSEMBLE. || I. LA CONCORDANCE À "
   "TROIS. Écrire, avant les prix : mon barème du 3e ; le devis de Marlo du "
   "25e, 228 cerfs au cerf près ; ET L'ACTE DU 23e DE LA 3e LUNE, de la main de Hann "
   "Bourbe devant Marlo Vasse et Nel Bec, « un peu plus d'un dragon d'or AU PRIX DES "
   "QUAIS » pour le même lot — 228 cerfs font un dragon et dix-huit cerfs. Trois "
   "mains, trois papiers, dix jours, le même nombre, et l'un des trois dit d'où "
   "il vient. Nel Bec est le seul témoin qui ne soit ni de l'aire ni de mon "
   "banc : c'est lui qu'il faut pouvoir citer. || II. L'EXTINCTION. Sous les "
   "signatures, en toutes lettres et à la date : Sirel Quintaine déclare "
   "éteinte toute créance née du lot de la Néra sur l'aire de bris de la "
   "vase — cent vingt-trois cerfs, dont quatre-vingt-cinq de compte et trente-huit de "
   "son propre fait. Le gage des onze dragons n'est pas touché et la ligne le dit, "
   "sans quoi on lira que j'ai tout remis."),
 r(A, "68124", "\U0001F4CD Où",
   "L'étal de Sirel pour l'écrire ; sous l'auvent de Marlo Vasse pour la "
   "signer, en même temps que ⚔️ 68123"),
 r(A, "68124", "\U0001FAB6 Office", "O21"),
 r(A, "68124", "\U0001F9F0 Moyens", "M05"),
 r(A, "68124", "⛓️ Dépend de", "68123"),
 r(A, "68124", "\U0001F4C5 Jour dû", "avant le 7e de la 4e lune, avec la signature"),
 r(A, "68124", "⏳ Où ça en est", "à faire"),
 r(A, "68124", "\U0001F4DD Note",
   "CE QUE LA CONCORDANCE À TROIS RETOURNE, ET JE NE L'AVAIS PAS VU : si mon "
   "barème EST le prix des quais, alors le rouleau parti neuf cerfs le 27e n'a pas "
   "été bradé sous la marge d'une prêteuse — il a été bradé SOUS "
   "LE PRIX DU QUAI, sur leur propre marché. Dix-neuf sous la brasse contre quarante "
   "et un : moitié moins cinq. Le démenti que Hann m'a demandé "
   "d'écrire plus dur est encore plus dur qu'il ne le croyait."),
]

chemin = os.path.join(RACINE, "etat", "rapports", "_sirel-prix-des-quais.json")
with io.open(chemin, "w", encoding="utf-8") as f:
    json.dump({"qui": "sirel-quintaine", "quand": "129.4.3", "cahier2": c},
              f, ensure_ascii=False, indent=1)
print("ecrit :", len(c), "coordonnees ->", os.path.normpath(chemin))
