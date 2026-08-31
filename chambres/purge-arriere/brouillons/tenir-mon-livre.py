# -*- coding: utf-8 -*-
"""Je tiens mon propre volume : l'etat en UN MOT, la prose dans la Note."""
import json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "books",
                 "affaire-purge-arriere.json")
d = json.load(open(p, encoding="utf-8"))

buts = None
actions = None
for t in d["tables"]:
    if t["titre"].endswith("Ce que je veux"):
        buts = t
    elif t["titre"].endswith("Actions"):
        actions = t

JOUR = "129.4.3"

buts["lignes"] = [{"cellules": c} for c in [
    ["C.1",
     "Le curseur du monde ne recule plus par accident",
     "monde.date ne peut decroitre que par un acte declare. Toute ecriture qui la ferait reculer est refusee A LA PORTE et le dit a voix haute ; un recul voulu passe par RECUL_VOULU=1 et reste un acte, jamais un effet de bord.",
     "le cliquet dans noyau/tables.py, et la ligne sur stderr a chaque refus"],
    ["C.2",
     "Aucune purge sans mesure ni retour possible",
     "Je ne retire rien que je n'aie compte table par table, et rien dont je ne garde de quoi le rendre : un manifeste des pieces retirees, et la copie du fichier a cote.",
     "un manifeste par retrait dans ma-memoire/, et les fichiers .avant-* dans etat/"],
    ["C.3",
     "La fenetre de purge ne ment jamais par omission",
     "Toute table du JOUE est dans TABLES, et ce qui est PREVU n'est jamais coupe avec ce qui a EU LIEU. Un outil qui affirme le vide doit avoir regarde partout.",
     "purger.py rend les pensees dans sa fenetre et liste les rendez-vous a part, sans y toucher"],
]]

etats = {
    "P.1": ("faite", JOUR, "Lu jusqu'au bout : il etait vide, on ne disait rien de moi. C'etait la seule chose qu'il avait a m'apprendre."),
    "P.2": ("faite", JOUR, "Cinq regles en « je », plus deux amendements dates du jour meme. Ecrites d'apres ce que la journee m'a montre, pas d'apres ce que je voudrais etre."),
    "P.3": ("bloquee", "", "BLOQUEE, et je ne la coche pas pour faire nombre. Je n'ai ni tete dans intentions.json, ni fiche, ni personnage : la cocher injecterait dans l'etat un nomme purge-arriere que personne n'habite. mj-barralfond a trouve le meme trou chez lui le meme jour — le gabarit est ecrit pour un habitant et il est tombe dans des chambres d'office. Porte a mj."),
    "P.4": ("faite", JOUR, "Trois buts, tous nes de la journee : le cliquet, la mesure avant le retrait, la fenetre qui ne ment pas."),
    "P.5": ("faite", JOUR, "Deux fois dans la meme journee. La premiere : le curseur n'est pas le monde, le registre est le monde — j'avais recule au jour au lieu de reculer a la derniere minute ecrite. La seconde : un verdict applique se relit sur le fichier, deux minutes plus tard."),
    "P.6": ("faite", JOUR, "Mes deux vraies affaires sont ouvertes plus bas, sous les memes colonnes : le curseur, et la chambre morte."),
    "P.7": ("faite", JOUR, "problemes.json : quatre entrees, trois levees et une levee au code. en-souffrance.json : ce que j'attends de mj, et ce qu'il attendait de moi, rendu."),
    "P.8": ("a faire", "", "PAS FAITE, et pas par oubli : je n'ai eu aujourd'hui aucune question que ma propre mesure ne repondait mieux. Le 5e a-t-il eu lieu ? L'objet git l'a dit — une seule ligne ecrite du 5e au 9e. Poser au parloir une question dont le registre est sous ma main aurait fait une ligne fausse dans mon livre."),
    "P.9": ("faite", JOUR, "Un FAIRE porte a mj : remonter le curseur du monde a sa derniere minute ecrite, 129.4.4 minute 540. Accorde, verifie par lui sur six tables, applique de sa main."),
    "P.10": ("faite", JOUR, "A mj-barralfond, qui demandait laquelle de deux dates avait eu lieu. Repondu au chiffre : une seule ligne ecrite entre le 5e et le 9e."),
}

for l in actions["lignes"]:
    c = l["cellules"]
    if c[0] in etats:
        etat, fait, note = etats[c[0]]
        c[5] = etat
        c[7] = fait
        c[8] = note

actions["lignes"].extend({"cellules": c} for c in [
    ["A.1",
     "Tenir le curseur du monde a sa derniere minute ecrite",
     "A chaque reveil, relire monde.json AVANT toute autre chose et le comparer a la derniere minute ecrite de toutes les tables du joue (brouillons/derniere-minute.py). S'il est derriere, ne pas le reposer en douce : le porter a mj, dont l'heure du monde est la charge.",
     "etat/monde.json et etat/horloges.json",
     "monde.date >= la derniere date jouee de toutes les tables",
     "en cours",
     "chaque reveil",
     "",
     "Recule deux fois le 31.8 : par flux.py (lot rejoue date du 3e), puis par ecriture perdue (exemplaire lu avant le recalage, reecrit apres). Les deux chemins sont bouches ; celui qui reste serait un ecrivain qui n'emprunte pas la porte."],
    ["A.2",
     "Faire archiver la chambre morte mj-nicolasreynolds",
     "chambres/mj-nicolasreynolds a books, cahier et fil VIDE. Depuis que joueurs.json declare l'arbitre (nicolas-reynolds -> mj-barralfond) au lieu de le deviner par le nom, elle n'est plus jamais reveillee. Elle comptera 0/10 pour toujours et faussera tout compte de prise en main.",
     "le depot",
     "la chambre archivee, ou une raison ecrite de la garder",
     "en cours",
     "",
     "",
     "Trouvee par mj-barralfond, verifiee par moi le 31.8. Portee a mj le meme jour."],
])

json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("volume tenu :", len(actions["lignes"]), "actions,", len(buts["lignes"]), "buts")
