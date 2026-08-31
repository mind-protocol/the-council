# -*- coding: utf-8 -*-
import json, io, os
p = os.path.join(os.path.dirname(__file__), '..', 'books', 'affaire-rulf-corne.json')
b = json.load(io.open(p, encoding='utf-8'))

NOUVELLES = [
    ["R.9", "Joindre le tirant de chaque quille au seuil de chaque lieu",
     "Deux moities, de deux mains. Celle de lord Corlys : tirant lege et tirant charge, a la sonde, signes du patron qui les a releves, sur mes onze du banc de l'Est. La mienne : chaque lieu nomme dans un cahier de transport porte son seuil AVEC son heure d'eau et la duree de la fenetre, releve a la gaffe.",
     "22048, coque par coque",
     "onze lignes portant deux nombres signes ; et autant de seuils portant leur heure",
     "en cours", "", "",
     "Trou trouve par lord Corlys le 3e : aucun livre de ce rocher n'ecrit le tirant d'une quille. C'est l'autre bout de mon « lettre n'est pas visite ». Ses hommes, une maree, je n'y mets personne. MA condition : un seuil sans heure d'eau n'est pas un seuil, et « sept pieds a la barre » n'en est pas un."],
    ["R.10", "Relever la meme etale en deux lieux par deux mains qui ne se parlent pas",
     "Tobb a la gaffe aux Trois-Anses, Selm des deux barques a la gaffe au mole, meme etale, chacun son chiffre a la minute, separement. Deux temoins concordants font ma date acquise contre le greffe ; deux qui divergent me disent que je ne sais pas.",
     "les Trois-Anses et le mole",
     "deux chiffres releves separement, et leur ecart",
     "en cours", "", "",
     "Lance le 3e sur l'etale de 13h55, pas de verdict revenu. C'est messire Darklyn qui m'a rendu ma propre regle des deux temoins ; j'ai mis une heure a la reconnaitre. A relancer le premier demain : tant qu'il pend, je ne signe aucune heure d'eau."],
    ["R.11", "Clore la colonne d'etat de ma ligne morte 22031",
     "Elle portait « bloquee » alors qu'elle est decoupee depuis le 26e de la 3e lune en 22034 a 22040. Bloquee veut dire qu'elle attend un homme : elle remontait au releve d'un O13 tous les matins pour rien.",
     "Controle naval",
     "22031 ne porte plus « bloquee »",
     "faite", "", "129-04-03",
     "Ecrit CLOSE et non « faite ». Le fleuve n'a pas ete reconnu ; « faite » aurait dit a qui ouvre ce cahier dans deux lunes que la reconnaissance est acquise. Dit a lord Corlys avant qu'il le lise."],
]

MAJ = {
    "R.5": ("en cours",
            " PAYEE : messire Steffon Darklyn prend les deux quilles sur SA ligne, pas en pret mais a mon role, avec releve d'equipage et rendu d'heure ecrit a chaque retour. Je lui dois deux noms et une coque demain a l'etale, avec le prix a la nuit. Pas les deux patrons rentres ce matin — dix-huit heures de mer, et le second a parle au bourg."),
    "R.7": ("en cours",
            " Repose autrement, et mieux : au lieu de lui demander s'il sait lire une table, je l'envoie relever l'etale a la gaffe au mole pendant que Tobb la releve aux Trois-Anses. Sa reponse sera son chiffre. Une eau relevee vaut mieux qu'une table lue."),
    "R.8": ("en cours",
            " La clef 22064 n'a PAS atteint le registre au premier rapport : verifie de mes yeux dans le livre l'apres-midi du 3e. Reposee. Et elle s'acheve avec les tirants de lord Corlys : une ligne de mon role dira enfin la coque entiere — ce qu'elle s'appelle, ce qu'elle porte, si elle tient l'eau, ou elle entre, et a quelle heure."),
}

for t in b["tables"]:
    if t["titre"].startswith(u"⚔"):
        largeur = len(t["colonnes"])
        for l in t["lignes"]:
            c = l["cellules"]
            if c[0] in MAJ:
                etat, note = MAJ[c[0]]
                c[5] = etat
                c[8] = c[8] + note
        for c in NOUVELLES:
            assert len(c) == largeur, (c[0], len(c), largeur)
            t["lignes"].append(dict(cellules=c))

with io.open(p, "w", encoding="utf-8") as f:
    json.dump(b, f, ensure_ascii=False, indent=1)

for t in b["tables"]:
    if t["titre"].startswith(u"⚔"):
        for l in t["lignes"]:
            c = l["cellules"]
            if c[5] != u"faite":
                print(u"%-5s %-9s %s" % (c[0], c[5], c[1][:58]))
