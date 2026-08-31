# -*- coding: utf-8 -*-
import json, io, os

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
L = "nera-le-dehors"
V = "\U0001F512 Verrous"
C = "\U0001F5DD️ Clefs"
A = "⚔️ Actions"
O = "\U0001F3F0 Ouverture de l'Affaire — chantier de la vase, 2e jour de la 4e lune"


def r(table, ligne, colonne, valeur):
    return {"livre": L, "table": table, "ligne": ligne,
            "colonne": colonne, "valeur": valeur}


c = []

# --- VERROU 68103 ---------------------------------------------------------
c += [
 r(V, "68103", "\U0001F512 N°", "**68103**"),
 r(V, "68103", "\U0001F3F7️ Le verrou",
   "\U0001F4CF Ma feuille tarife le bordé AU ROULEAU, et un rouleau n'est pas une "
   "mesure — un prix dont l'unité ne se vérifie que dans ma tête me "
   "garde dans la pièce"),
 r(V, "68103", "⛔ Bloque", "68100"),
 r(V, "68103", "\U0001F4CC Ce qui est vrai aujourd'hui",
   "J'ai signé le 3e au matin une feuille où le filin se dit À LA BRASSE et "
   "le bordé À L'EMBALLAGE : dix-neuf cerfs le rouleau. Or un rouleau est ce que "
   "le chantier a roulé, ni plus ni moins ; il n'existe aucun étalon du rouleau "
   "sur la Néra, et je n'ai qu'un exemplaire au monde pour dire si le mien est grand "
   "ou petit. Conséquence exacte, et c'est elle le verrou : le jour où un tiers "
   "tend ma feuille et dit « dix-neuf le rouleau », l'acheteur répond "
   "« quel rouleau ? », et il n'y a qu'une bouche au monde capable de "
   "répondre — la mienne. UN PRIX SANS ÉTALON N'EST PAS UN PRIX ÉCRIT, "
   "C'EST UN RENDEZ-VOUS. Il reconduit sur chaque ligne la dépendance que 68100 doit "
   "supprimer. Même chose par l'autre bout dans ma colonne des démentis : j'y "
   "opposais neuf cerfs à dix-neuf sans qu'aucun des deux rouleaux ait été "
   "mesuré — je démentais un chiffre sans étalon dans la main, ce qui "
   "ne dément rien."),
 r(V, "68103", "\U0001F441️ La preuve",
   "Ma feuille de prix des Chantiers de la Néra, section II, du 3e de la 4e lune, "
   "telle que signée le matin : « Bordé, le rouleau, sec et sain — 19 "
   "cerfs », deux lignes sous « Filin trois-torons, LA BRASSE, 9 sous ». Et "
   "le rouleau du lot, mesuré au cordeau à mon banc le 3e au soir : VINGT-SIX "
   "BRASSES, sans second exemplaire pour la comparaison. Correction datée et "
   "signée portée le soir même sur toutes les copies, y compris celles qui "
   "sortent."),
 r(V, "68103", "\U0001F513 Levé quand",
   "Quand chaque ligne de la feuille portera une unité qu'un homme peut vérifier "
   "seul, au cordeau ou à la pièce, sans me demander ce que j'entendais — et "
   "quand une seconde longueur de rouleau, écrite d'une autre main, sera venue "
   "s'inscrire sous la mienne. Deux mesures font un étalon ; une seule fait encore une "
   "opinion."),
]

# --- CLEF 68111 (ouvre 68102) ---------------------------------------------
c += [
 r(C, "68111", "\U0001F5DD️ N°", "**68111**"),
 r(C, "68111", "\U0001F3F7️ La clef",
   "\U0001F9FE Ne pas répondre à un chiffre par un chiffre : lui écrire "
   "à côté ce qui le rend comparable — ou ce qui l'en empêche"),
 r(C, "68111", "\U0001F513 Ouvre", "68102"),
 r(C, "68111", "\U0001F4A1 Le principe",
   "Un prix taillé sur une caisse à remplir bat toujours un prix taillé sur "
   "du bois, parce qu'il n'a pas à être juste, seulement à tomber le jour "
   "dit. On ne le combat donc pas : on l'INSTRUIT. Trois questions écrites à "
   "côté de lui, et n'importe qui les applique sans moi. L'ÉTALON A-T-IL "
   "ÉTÉ MESURÉ ? LE VENDEUR AVAIT-IL UNE ÉCHÉANCE DANS LES TROIS "
   "JOURS ? L'ACHETEUR A-T-IL UN NOM AU RÔLE ? Deux « non » sur trois, et ce "
   "n'est pas un prix de bois, c'est le chiffre d'une caisse — il mesure la hâte "
   "du vendeur, pas la valeur de la pièce. Le renversement est là : le chiffre du "
   "port cesse d'être une objection CONTRE ma feuille et devient une ENTRÉE DE ma "
   "feuille, dans une colonne qui l'explique. Et le critère étant écrit, il "
   "se manie sans moi — ce que ne fait pas une prêteuse qui répond « "
   "oui mais je sais pourquoi »."),
 r(C, "68111", "\U0001F4B0 Ce qu'elle coûte et ce qu'elle ferme",
   "Rien en or, et très cher en tenue : le critère vaut CONTRE MOI aussi, et il "
   "faut donc porter mes propres ventes dans la colonne. J'y ai inscrit la première, "
   "du 3e au soir : 266 cerfs comptant le 30e pour 143 cerfs de bois à mes propres "
   "prix, échéance de six bras le lendemain matin, aucun nom de payeur — mon "
   "chiffre échoue à mes trois questions. Elle ferme définitivement la voie "
   "où j'aurais dit « ce chiffre-là ne compte pas » sans avoir à "
   "dire pourquoi : à partir d'aujourd'hui, tout chiffre que je récuse doit "
   "être écrit, avec sa raison, à côté du mien."),
 r(C, "68111", "\U0001F441️ La preuve attendue",
   "Un acheteur qui, ma feuille en main et moi absente, écarte lui-même un prix "
   "du port en citant la colonne — « pas d'étalon, échéance à "
   "trois jours, pas de nom » — et conclut dans la fourchette."),
 r(C, "68111", "⚖️ Décision",
   "**retenue le 3e** — les deux colonnes sont ajoutées à la feuille le soir "
   "même, et la première entrée qu'elles portent est la mienne, contre moi."),
]

# --- CLEF 68112 (ouvre 68103) ---------------------------------------------
c += [
 r(C, "68112", "\U0001F5DD️ N°", "**68112**"),
 r(C, "68112", "\U0001F3F7️ La clef",
   "\U0001F4CF Aucun prix sans son étalon — le bordé se dit à la "
   "brasse, le rouleau n'est qu'une corde autour du bois"),
 r(C, "68112", "\U0001F513 Ouvre", "68103"),
 r(C, "68112", "\U0001F4A1 Le principe",
   "Une unité se choisit sur ce qu'un homme peut vérifier SEUL, avec ce qu'il a "
   "dans la main : un cordeau, ses bras, ses yeux. La brasse se vérifie ; le rouleau "
   "ne se vérifie pas, il se croit. On ne garde donc que des unités qui se "
   "mesurent, et l'emballage redevient ce qu'il est — on l'ouvre, on mesure, on "
   "multiplie. Dix-neuf cerfs sur vingt-six brasses font 41 sous la brasse : le chiffre ne "
   "bouge pas, c'est l'unité qui change, et avec elle la personne qui doit être "
   "là pour la dire. Et l'on invite l'autre main à écrire SA longueur "
   "au-dessous : la ligne cesse d'être la mienne au moment où un second l'a "
   "mesurée."),
 r(C, "68112", "\U0001F4B0 Ce qu'elle coûte et ce qu'elle ferme",
   "Un cordeau et une heure. Elle me coûte l'avantage du flou — au rouleau, "
   "c'était moi qui disais si le rouleau était bon ; à la brasse, l'acheteur "
   "compte tout seul, et il comptera quelquefois contre moi. Elle ferme la vente en bloc au "
   "jugé, qui est justement celle que j'ai faite le 30e et qui m'a coûté 123 "
   "cerfs."),
 r(C, "68112", "\U0001F441️ La preuve attendue",
   "Une seconde longueur de rouleau, mesurée par une autre main que la mienne et "
   "écrite sous la ligne — et un bordé vendu à la brasse par une bouche "
   "qui n'est pas la mienne."),
 r(C, "68112", "⚖️ Décision",
   "**retenue et faite le 3e au soir** — mesurée, corrigée, datée sur "
   "les trois copies."),
]

# --- ACTION 68021 (réalise 68011) ------------------------------------
c += [
 r(A, "68021", "⚔️ N°", "**68021**"),
 r(A, "68021", "\U0001F3F7️ L'action",
   "✍️ Poser 228 contre 228 — porter ma feuille à l'aire avec le devis "
   "de Marlo du 25e, et demander sa main et sa date au bas"),
 r(A, "68021", "\U0001F5DD️ Réalise", "68011"),
 r(A, "68021", "\U0001F4DD Ce qu'on fait",
   "LE FAIT DU JOUR, ET C'EST LUI QUI REND CETTE ACTION FAISABLE : j'ai recompté le "
   "lot pièce par pièce, puis appliqué mon barème du 3e au stock que le "
   "devis de Marlo portait le 25e — dix-huit membrures dont deux roussies, deux "
   "rouleaux. Seize à onze font 176, deux roussies à sept font 14, deux rouleaux "
   "à dix-neuf font 38 : DEUX CENT VINGT-HUIT CERFS. C'est, AU CERF PRÈS, le "
   "total que Marlo Vasse avait écrit de sa main, à la chandelle, la nuit du 25e, "
   "sans m'avoir jamais vue chiffrer quoi que ce soit. Deux mains, deux soirées, deux "
   "papiers, le même nombre. || CE QU'ON FAIT : je porte la feuille à l'aire de "
   "bris de la vase, je la pose à plat, je pose son devis du 25e à côté, "
   "et je ne plaide pas — je fais l'addition devant lui. Puis je demande la seule "
   "chose qui manque : sa main et son jour au bas de la feuille. L'argument tient en une "
   "phrase et il n'est pas de moi, il est du papier : CE BARÈME N'EST PAS LE MIEN, "
   "PUISQUE VOUS L'AVIEZ DÉJÀ ÉCRIT AVANT DE L'AVOIR LU. Une feuille qu'un "
   "second homme signe, c'est un usage ; une feuille qu'une seule main tient, c'est un "
   "tarif. || Je porte aussi, sans qu'on me le demande, les deux chiffres qui me sont "
   "contraires : les 123 cerfs payés au-dessus du barème le 30e, et la faute du "
   "rouleau. Un homme ne signe pas un papier dont l'auteur ne s'est pas encore "
   "trompé dessus."),
 r(A, "68021", "\U0001F4CD Où",
   "L'aire de bris de la vase — chez lui, sous son auvent, et non à mon banc : la "
   "feuille doit avoir l'air d'être rentrée chez elle"),
 r(A, "68021", "\U0001FAB6 Office", "O21"),
 r(A, "68021", "\U0001F9F0 Moyens", "M05"),
 r(A, "68021", "⛓️ Dépend de", "68120"),
 r(A, "68021", "\U0001F4C5 Jour dû",
   "avant le 8e de la 4e lune — la feuille doit être à deux mains AVANT que "
   "le premier devis en sorte, sinon elle sortira signée de mon seul nom et le pli "
   "sera pris"),
 r(A, "68021", "⏳ Où ça en est", "à faire"),
 r(A, "68021", "\U0001F4DD Note",
   "Le billet du 3e au soir le lui annonce, avec le recompte entier et le 228 contre 228. "
   "Ce que cette action peut casser, écrit d'avance : il peut lire la concordance "
   "comme un vol de son devis et non comme un accord. C'est pourquoi on ne dit pas « "
   "nos prix sont les mêmes » mais « vous les aviez écrits le premier "
   "» — sa date du 25e est antérieure à la mienne du 3e, et je la lui "
   "reconnais par écrit."),
]

# --- ACTION 68122 (réalise 68112), faite -----------------------------
c += [
 r(A, "68122", "⚔️ N°", "**68122**"),
 r(A, "68122", "\U0001F3F7️ L'action",
   "\U0001F4CF Mesurer le rouleau au cordeau et refaire la feuille à la brasse"),
 r(A, "68122", "\U0001F5DD️ Réalise", "68112"),
 r(A, "68122", "\U0001F4DD Ce qu'on fait",
   "Ouvrir le rouleau du lot à mon banc, le mesurer au cordeau, écrire la "
   "longueur sur la feuille : vingt-six brasses. Diviser : 19 cerfs font 1064 sous, sur 26 "
   "brasses, 41 sous la brasse. Remplacer la ligne « le rouleau, 19 cerfs » par "
   "« à la brasse, 41 sous », et laisser dessous la ligne du rouleau avec, "
   "pour tout prix, « SE MESURE AVANT DE SE DIRE ». Dater et signer la correction "
   "sur les trois copies. Ajouter au dos, AVANT les trois questions, une question "
   "zéro : DE QUOI ÇA SE MESURE ?"),
 r(A, "68122", "\U0001F4CD Où", "L'étal de Sirel, marché du Crochet"),
 r(A, "68122", "\U0001FAB6 Office", "O21"),
 r(A, "68122", "\U0001F9F0 Moyens", "M05"),
 r(A, "68122", "⛓️ Dépend de", "68120"),
 r(A, "68122", "\U0001F4C5 Jour dû", "129.4.3"),
 r(A, "68122", "⏳ Où ça en est", "faite"),
 r(A, "68122", "\U0001F4C5 Jour fait", "129.4.3"),
 r(A, "68122", "\U0001F4DD Note",
   "Deuxième fois en un jour qu'un autre reprend un chiffre de ma feuille — Sabbe "
   "le matin sur la journée d'homme, le recompte du lot le soir sur le rouleau. Je les "
   "porte toutes les deux sur le papier plutôt que de les corriger en silence : une "
   "feuille qui montre les ratures de son auteur se croit, une feuille lisse est un "
   "boniment."),
]

# --- 68120 : faite --------------------------------------------------------
c += [
 r(A, "68120", "⏳ Où ça en est", "faite"),
 r(A, "68120", "\U0001F4C5 Jour fait", "129.4.3"),
 r(A, "68120", "\U0001F4DD Note",
   "FAITE LE 3e — une soirée, une chandelle, et deux reprises le jour même. "
   "La feuille porte en plus de ce qui était prévu : une colonne des DÉMENTIS, "
   "qui figure sur les copies qui SORTENT et où j'inscris ce que le marché a fait "
   "contre ma propre ligne ; et depuis le soir, trois critères de plus qui disent si "
   "un chiffre contredisant est comparable — étalon mesuré, échéance "
   "du vendeur, nom du payeur au rôle. Le prix de cette feuille est écrit à "
   "la clef 68110 et il est pour moi seule : je l'ai payé. || TROIS COPIES ET NON "
   "DEUX. Une à l'aire, une à mon banc, une chez un acheteur — la "
   "troisième est celle qui compte, et elle est partie le 3e au soir. Les copies qui "
   "sortent portent I, II et le dos ; elles ne portent pas le bas fermé."),
]

# --- l'état actuel de l'affaire --------------------------------------
c += [
 r(O, "ligne 5", "✍️ Ce qu'on y ecrit",
   "LE LOT EST PLACE ET IL N'EN RESTE RIEN A VENDRE — mais le lot n'était pas "
   "celui du devis, et je ne le sais que depuis le 3e au soir. RECOMPTE PIÈCE PAR "
   "PIÈCE : douze membrures et non dix-huit — dix saines de portée au-delà "
   "de quatre pas, deux roussies au pied ; UN rouleau de bordé et non deux, sec, sain, "
   "pas entamé, vingt-six brasses au cordeau. Les six membrures manquantes sont parties "
   "aux Trois-Marches le 25e au matin, quatre cerfs de moins la pièce, comptant ; le "
   "rouleau manquant le 27e à la première marée, neuf cerfs. Le devis que "
   "j'ai emporté a été écrit LE SOIR DU 25e : Marlo y a porté le "
   "chiffre de l'avant-veille sans recompter après une vente faite le matin par son "
   "second. Il ne m'a pas menti d'un nombre — il a recopié le sien. || LE "
   "CHIFFRE, À MES PROPRES PRIX SIGNÉS DU 3e : dix saines à onze font 110, "
   "deux roussies à sept font 14, un rouleau 19 — CENT QUARANTE-TROIS CERFS. J'en "
   "ai compté DEUX CENT SOIXANTE-SIX comptant sur mon banc le 30e au soir. CENT "
   "VINGT-TROIS CERFS D'ÉCART : quatre-vingt-cinq de bois déjà vendu que le "
   "devis portait encore, trente-huit posés exprès pour tomber sur la paie de six "
   "bras le 31e au matin. || ET CECI, QUI VAUT MIEUX QUE LE RESTE : le même "
   "barème appliqué au stock du 25e rend 228 cerfs, c'est-à-dire AU CERF "
   "PRÈS le total que Marlo avait écrit de sa main cette nuit-là. Deux mains, "
   "deux papiers, le même nombre. Le barème des Chantiers n'est donc pas dans ma "
   "tête : il est déjà dans deux têtes, et personne ne l'avait "
   "vérifié faute d'avoir posé les deux feuilles côte à "
   "côté. || CE QUE J'IGNORE ET QUE J'ÉCRIS COMME IGNORÉ : qui paie le "
   "chantier du bout, derrière les entrepôts à sel — deux galères "
   "sur bers, une troisième quille, quarante bras, comptant, aucun nom nulle part. "
   "Marlo le cherche depuis cinq jours pour lui vendre son bois et ne l'a pas trouvé. "
   "Je ne le cherche pas : ma troisième copie est partie à sa grille."),
]

chemin = os.path.join(RACINE, "etat", "rapports", "_sirel-recompte.json")
with io.open(chemin, "w", encoding="utf-8") as f:
    json.dump({"qui": "sirel-quintaine", "quand": "129.4.3", "cahier2": c},
              f, ensure_ascii=False, indent=1)
print("ecrit :", len(c), "coordonnees ->", os.path.normpath(chemin))
