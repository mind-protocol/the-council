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

# --- VERROU 68104 : la date du compte -------------------------------------
c += [
 r(V, "68104", "\U0001F512 N°", "**68104**"),
 r(V, "68104", "\U0001F3F7️ Le verrou",
   "\U0001F4C5 Rien, dans une feuille de prix, ne distingue un chiffre COMPTÉ d'un "
   "chiffre RECOPIÉ — et c'est ce défaut-là, non un mensonge, qui a produit "
   "les deux écarts du 3e"),
 r(V, "68104", "⛔ Bloque", "68100"),
 r(V, "68104", "\U0001F4CC Ce qui est vrai aujourd'hui",
   "Deux hommes de métier, chacun tenant bien ses colonnes, se sont trompés le "
   "même jour de la même façon. Marlo Vasse a écrit son devis le soir du "
   "25e en y portant le compte de l'avant-veille, après une vente faite le matin "
   "même par son second : dix-huit membrures et deux rouleaux au lieu de douze et "
   "un. Je l'ai payé 266 cerfs comptant le 30e sans recompter la marchandise que je "
   "levais. QUATRE-VINGT-CINQ CERFS de bois qui n'existaient plus, et pas une ligne "
   "fausse dans les deux papiers — chaque chiffre était vrai le jour où il "
   "avait été compté, et aucun des deux ne portait ce jour-là. || CE QUI EN "
   "FAIT UN VERROU POUR 68100 : une feuille dont on ne peut pas dire si une ligne a "
   "été comptée ce matin ou recopiée d'il y a trois jours ne se tend pas. Le "
   "tiers qui la porte devant un acheteur ne peut pas répondre à « c'est "
   "encore vrai ? », et il revient me le demander. Ma tête est de nouveau dans "
   "la pièce, sur un autre défaut que celui de l'étalon (68103) mais avec la "
   "même conséquence exacte. Un chiffre recopié n'est pas un chiffre "
   "compté, et une feuille qui ne les sépare pas ne mesure rien : elle date "
   "d'un jour qu'elle ne dit pas."),
 r(V, "68104", "\U0001F441️ La preuve",
   "Le devis du lot, de la main de Marlo Vasse, écrit le soir du 25e de la 3e lune "
   "et portant le compte du 23e : dix-huit membrures, deux rouleaux. Le recompte "
   "pièce par pièce du 3e de la 4e lune, fait des deux côtés séparément "
   "et concordant : douze membrures — dix saines, deux roussies au pied — et "
   "un rouleau de vingt-six brasses au cordeau. Les six pièces parties aux "
   "Trois-Marches le 25e AU MATIN ; le premier rouleau le 27e à la première "
   "marée. Écart payé : 85 cerfs, soit 4760 sous. Marlo a cloué son propre "
   "recompte au montant de son auvent le 3e au soir, en trois copies, avant d'avoir lu "
   "ma lettre."),
 r(V, "68104", "\U0001F513 Levé quand",
   "Quand chaque ligne de la feuille portera la date de son compte, et qu'une ligne dont "
   "la date de compte n'est pas celle du jour sera soit recomptée, soit "
   "accompagnée en clair de la raison de ne pas l'avoir fait."),
]

# --- CLEF 68113 -----------------------------------------------------------
c += [
 r(C, "68113", "\U0001F5DD️ N°", "**68113**"),
 r(C, "68113", "\U0001F3F7️ La clef",
   "\U0001F4C5 Toute ligne porte la DATE DU COMPTE et non la date de la feuille — "
   "*règle de Marlo Vasse, donnée le 3e de la 4e lune*"),
 r(C, "68113", "\U0001F513 Ouvre", "68104"),
 r(C, "68113", "\U0001F4A1 Le principe",
   "Une feuille porte deux dates et l'on n'en écrivait qu'une. Celle du jour où "
   "on l'écrit ne dit rien ; celle du jour où l'on a COMPTÉ dit tout. Si les "
   "deux ne sont pas le même jour, deux issues et pas une troisième : ON "
   "RECOMPTE, ou L'ON ÉCRIT POURQUOI ON NE L'A PAS FAIT. La règle est "
   "gratuite, elle ne demande ni cordeau ni témoin, elle tient en une ligne en "
   "tête de feuille — et elle rend au lecteur le seul jugement qu'il ne pouvait "
   "pas porter seul : ce chiffre a-t-il encore quelque chose derrière lui ? || Elle "
   "n'est pas de moi. Elle est de Marlo Vasse, charpentier de l'aire de bris de la vase, "
   "qui l'a apprise le 3e à ses frais et me l'a donnée le soir même en "
   "condition de sa signature. C'est écrit ici sous son nom, et c'est la preuve "
   "que le barème a cessé d'être le mien : la première règle "
   "que la feuille porte en tête n'a pas été écrite par celle qui tient "
   "la feuille."),
 r(C, "68113", "\U0001F4B0 Ce qu'elle coûte et ce qu'elle ferme",
   "Rien, et c'est ce qui la rend redoutable. Elle ferme en revanche la vente en bloc "
   "sur papier — on ne lève plus un lot sur un devis de trois jours sans "
   "repasser dessus, ce qui ralentit toute affaire pressée. C'est exactement le genre "
   "de lenteur que j'aurais refusée le 30e au soir, et elle m'aurait valu 85 cerfs."),
 r(C, "68113", "\U0001F441️ La preuve attendue",
   "Une vente refusée ou renégociée par un tiers, moi absente, au seul motif "
   "que la date de compte d'une ligne n'était pas celle du jour — et l'écart "
   "trouvé avant le paiement et non après."),
 r(C, "68113", "⚖️ Décision",
   "**retenue le 3e au soir, et posée en TÊTE de la feuille** — avant les "
   "prix, avant les questions du dos. Donnée par Marlo Vasse en première de ses "
   "trois conditions de signature ; acceptée sans marchander, et créditée "
   "à son nom sur toutes les copies."),
]

# --- ACTION 68123 ---------------------------------------------------------
c += [
 r(A, "68123", "⚔️ N°", "**68123**"),
 r(A, "68123", "\U0001F3F7️ L'action",
   "\U0001F4C5 Refondre la feuille sur les trois conditions de l'aire, et la porter "
   "à signer sous l'auvent de Marlo Vasse"),
 r(A, "68123", "\U0001F5DD️ Réalise", "68113"),
 r(A, "68123", "\U0001F4DD Ce qu'on fait",
   "TROIS CONDITIONS POSÉES PAR MARLO VASSE LE 3e AU SOIR, TOUTES ACCEPTÉES "
   "SANS MARCHANDER, ET AUCUNE NE COÛTE UN SOU. || I. CHAQUE LIGNE PORTE UNE "
   "UNITÉ QU'UN HOMME VÉRIFIE SEUL, avec ce qu'il a dans la main : le "
   "bordé à la brasse et non au rouleau, la journée d'homme en sous. Fait le 3e "
   "au soir avant sa lettre — 41 sous la brasse, 26 sous le manœuvre au bris. || "
   "II. TOUTE LIGNE PORTE LA DATE DU COMPTE ET NON LA DATE DE LA FEUILLE ; si les deux "
   "diffèrent, on recompte ou l'on écrit pourquoi on ne l'a pas fait. À "
   "porter EN TÊTE, avant les prix, sous son nom et daté du 3e. || III. SOUS LA "
   "LIGNE DU ROULEAU, LA PLACE D'UNE SECONDE LONGUEUR, mesurée par une main qui "
   "n'est ni la sienne ni la mienne. Deux mesures font un étalon, une seule fait encore "
   "une opinion. || PUIS : porter la feuille SOUS SON AUVENT, faire l'addition devant "
   "lui — 228 contre 228 — et recueillir sa main et son jour. Mes deux fautes "
   "du 3e restent datées dessus, les siennes viendront à côté, de sa main. Il a "
   "écrit qu'il ne signe pas un papier dont l'auteur ne s'est pas encore "
   "trompé dessus."),
 r(A, "68123", "\U0001F4CD Où",
   "Sous l'auvent de Marlo Vasse, aire de bris de la vase — et c'est LUI qui a "
   "nommé le lieu, ce qui ne m'était pas arrivé"),
 r(A, "68123", "\U0001FAB6 Office", "O21"),
 r(A, "68123", "\U0001F9F0 Moyens", "M05"),
 r(A, "68123", "⛓️ Dépend de", "68021"),
 r(A, "68123", "\U0001F4C5 Jour dû",
   "avant le 7e de la 4e lune — il a quatre bras sans bois à partir du 7e et "
   "fera porter un devis au chantier du bout ; la feuille doit être à deux mains "
   "avant que ce devis-là sorte"),
 r(A, "68123", "⏳ Où ça en est", "en cours"),
 r(A, "68123", "\U0001F4DD Note",
   "Il paie ses quatre-vingt-cinq cerfs de cette encre-là plutôt qu'en or, et "
   "c'est moi qui y gagne : je n'aurais jamais tiré 85 cerfs d'un homme qui n'en a "
   "pas, et je n'aurais jamais acheté sa signature à aucun prix. Il tient la dette "
   "pour une dette et refuse qu'on s'en console — noté, et je ne la lui "
   "rappellerai pas."),
]

# --- 68011 : la décision se ferme ----------------------------------------
c += [
 r(C, "68011", "⚖️ Décision",
   "**TENUE le 3e au soir — sa main est promise par écrit.** Marlo Vasse "
   "signe : « ma main et mon jour au bas de votre feuille de prix, et je paie mes "
   "quatre-vingt-cinq cerfs de cette encre-là plutôt qu'en or ». Il donne sa "
   "raison lui-même et elle vaut mieux que la mienne : *« je n'ai aucune envie "
   "que le prix de mon bois soit réputé sortir du Crochet »*. Reste le geste — "
   "la feuille portée sous son auvent, l'addition faite devant lui, sa main posée "
   "(⚔️ 68123) — et trois conditions qu'il a mises, toutes acceptées "
   "sans marchander, dont une (la date du compte) est devenue la première ligne de la "
   "feuille sous SON nom. C'est là que le barème a cessé d'être le "
   "mien : le jour où sa règle est passée avant mes prix."),
]

# --- 68021 : où ça en est --------------------------------------------
c += [
 r(A, "68021", "⏳ Où ça en est", "en cours"),
 r(A, "68021", "\U0001F4DD Note",
   "ACCORD OBTENU LE 3e AU SOIR, PAR BILLET, AVANT MÊME QUE LA FEUILLE SOIT "
   "PORTÉE. Il avait recompté de son côté le même soir et cloué son "
   "recompte à son auvent en trois copies avant de lire ma lettre — les deux "
   "comptes concordent pièce à pièce, y compris les vingt-six brasses au "
   "cordeau. || CE QUI A EMPORTÉ L'AFFAIRE, et ce n'était pas l'argument que "
   "j'avais préparé : ce n'est pas 228 contre 228, c'est de lui avoir écrit "
   "LE JOUR MÊME que j'avais porté ma feuille à la grille du chantier du "
   "bout — le chantier qu'il cherchait depuis cinq jours. Il répond : « vous "
   "m'avez dit le jour même où vous y avez mis les pieds, et ça vaut plus "
   "que l'excuse ». Ce qui achète un homme qui écrit, ce n'est pas un "
   "chiffre juste, c'est une nouvelle mauvaise apportée à temps. || Le geste "
   "reste à faire sous son auvent : voir ⚔️ 68123, qui porte ses trois "
   "conditions."),
]

chemin = os.path.join(RACINE, "etat", "rapports", "_sirel-datecompte.json")
with io.open(chemin, "w", encoding="utf-8") as f:
    json.dump({"qui": "sirel-quintaine", "quand": "129.4.3", "cahier2": c},
              f, ensure_ascii=False, indent=1)
print("ecrit :", len(c), "coordonnees ->", os.path.normpath(chemin))
