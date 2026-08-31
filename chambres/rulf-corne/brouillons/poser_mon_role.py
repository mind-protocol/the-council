# -*- coding: utf-8 -*-
# 3e de la 4e lune, an 129 — je pose mes buts et mes actions dans mon propre volume.
import json, io, os

p = os.path.join(os.path.dirname(__file__), '..', 'books', 'affaire-rulf-corne.json')
b = json.load(io.open(p, encoding='utf-8'))

BUTS = [
    ["C.1",
     "Mon livre reste a moi, et rien n'en sort qui n'ait ete regarde",
     "Rien ne sort de mon livre qu'en copie de ma main, marquee VU ou DIT ligne par ligne, sous cire, contre nom au talon que je garde et qu'il signe au recevoir — et aucune ligne de mon livre ne porte comme VU ce que je n'ai pas regarde de mes yeux. Le livre lui-meme ne sort jamais.",
     "la clef 22062 decidee et appliquee, un talon signe par chaque receveur ; et mon role de coques tenu en DEUX colonnes, VUES et DITES, qu'on n'additionne jamais"],
    ["C.2",
     "Aucun compte de blocus ne repose sur une quille que personne n'a regardee",
     "Les onze quilles du banc de l'Est portent chacune sa date de visite sous la ligne de flottaison, ou la mention « non visitee » en toutes lettres ; et le cahier des deniers ne cautionne que des visitees.",
     "le role du banc de l'Est, quille par quille, avec sa date de visite ou son trou nomme ; et 28025 arrete sur ce role et non sur le lettrage"],
    ["C.3",
     "Rien n'entre ni ne sort de cette rade que je ne le sache le premier",
     "Deux quilles legeres sont tenues sous ma main pour la seule course d'avis, de sorte qu'aucun point de la baie ne soit a plus de douze heures de ce quai ; et tout acces que la maree ne ferme pas — a commencer par l'anse du levant des Trois-Anses — est porte au role avec son fond, son heure d'eau et un nom qui y demeure.",
     "22055 leve, avec rendu d'heure ecrit a chaque retour ; et 22054 leve, l'anse au role des acces et sa ligne qui monte au cahier chaque soir"],
]

FAIT = {
    "P.1": ("faite", "129-04-03",
            "claude.md lu jusqu'au bout. Je peux dire ce qu'on disait de moi, et j'ai ecrit dessous ce que j'en tiens et ce que j'en nuance."),
    "P.2": ("faite", "129-04-03",
            "Section « Ce que je dis de moi » dans claude.md, a la premiere personne : comment je parle, ce que je fais quand on me presse, ce que je ne fais jamais, et sur quoi je ne suis PAS conciliant."),
    "P.5": ("faite", "129-04-05",
            "Deux titres de jour dans claude.md : « l'heure de l'eau s'ecrit avant l'heure des hommes » et « lettre n'est pas visite ». Chacun porte le fait qui me l'a appris."),
    "P.7": ("faite", "129-04-05",
            "problemes.json : le parloir ferme au matin, quatre appels refuses. en-souffrance.json : deux fils que j'attends, trois que l'on attend de moi."),
    "P.9": ("faite", "129-04-03",
            "--tenter au matin du 3e : mes deux patrons de Sombreval entendus SEPAREMENT. Verdict rendu, acte propose a la porte."),
    "P.10": ("faite", "129-04-03",
             "--dire a aldon-hask, canal ouvert de ma chambre a la sienne : la caution de 28025 sur dix quilles dont deux visitees, et la mauvaise question de mon action 26052."),
}

MIENNES = [
    ["R.1", "Visiter sous flottaison les onze quilles du banc de l'Est",
     "Faire ouvrir chaque coque sous la ligne de flottaison a l'etale de basse mer, calfat present, et porter au role VISITEE avec sa date, ou NON VISITEE en toutes lettres. Le lettrage ne remplace pas la visite.",
     "banc de l'Est, a l'etale",
     "une date de visite ou un trou nomme en face de chacune des onze",
     "en cours", "", "",
     "DEUX faites, et une des deux hors d'etat. Neuf restent. Six au plus avant la nuit du 5e : l'etale ne donne pas davantage."],
    ["R.2", "Rendre le role du banc de l'Est avec ses trous nommes",
     "Le role part a l'heure dite meme incomplet, mais chaque manque y est ecrit comme manque. Un role qui ne nomme pas ses trous est un mensonge lent.",
     "ma table",
     "le role remis, portant en clair le nombre de quilles non visitees",
     "a faire", "129-04-05", "",
     "Le sondage du point de greve (26052) rentre APRES cette heure : ce trou-la partira nomme et non comble."],
    ["R.3", "Ecrire le verrou de la caution sur les quilles non regardees",
     "22056 dans Controle naval : nous cautionnons dix quilles et nous en avons regarde deux. Ce n'est pas un calcul, cela se voit en se baissant.",
     "Controle naval",
     "une ligne 22056 sous « Verrous »",
     "faite", "", "129-04-03",
     "Il porte aussi contre la levee de 22014, qui suppose que les dix affretees du banc de l'Est portent."],
    ["R.4", "Entendre separement les deux patrons rentres de Sombreval",
     "Chacun a un bout du quai, sans que l'un sache ce que l'autre a dit, et ne rien ajouter de l'un a l'autre. Separer VU et DIT ligne par ligne.",
     "le quai",
     "la preuve de 22055 refaite, en deux colonnes",
     "faite", "129-04-03", "129-04-03",
     "Concordants sur le port : quai de Sombreval ferme, fret au mouillage du dehors, flotte Darklyn entiere sur ses amarres. Divergents sur la banniere, deux heures d'ecart d'horloge. Rien sur lord Gunthor, et je l'ecris comme absence."],
    ["R.5", "Tenir deux quilles legeres sous ma main pour la seule course d'avis",
     "Deux barques legeres retirees du lettrage et affectees a l'avis seul, avec releve d'equipage et rendu d'heure ecrit a chaque retour. Leve 22055.",
     "le quai",
     "deux quilles nommees au role, et deux rendus d'heure ecrits",
     "a faire", "", "",
     "Sans elles la course d'avis se paie en visites de coque : deja deux marees de lettrage perdues en deux jours."],
    ["R.6", "Porter l'anse du levant des Trois-Anses au role des acces",
     "Son fond — quatre pieds a l'etale, sable dur, sans banc en travers —, son heure d'eau, qui est AUCUNE, elle prend une quille a toute heure, et ce qu'elle peut prendre. Puis lui attacher un nom qui y demeure deja et dont la ligne monte au cahier chaque soir.",
     "role des acces",
     "l'anse ecrite au role, et une premiere ligne du soir au cahier",
     "a faire", "", "",
     "Sonde a la gaffe de ma main le 2e, Tobb temoin. C'est le seul acces de cette maison que la maree ne garde pas."],
    ["R.7", "Demander a Selm des deux barques s'il sait lire une table de maree",
     "C'est le prix ecrit de la clef 22060 et je ne l'ai pas verifie. Un chef de poste qui se trompe d'une heure a ouvert la porte lui-meme.",
     "le quai",
     "sa reponse, notee avec sa date",
     "a faire", "", "",
     "Je l'ai ecrit de ma main dans le prix de 22060 : je ne compte pas cette clef pour acquise avant de le lui avoir demande."],
]

for t in b["tables"]:
    if t["titre"].startswith(u"\U0001F3AF"):          # Ce que je veux
        t["lignes"] = [dict(cellules=c) for c in BUTS]
    if t["titre"].startswith(u"⚔"):              # Actions
        largeur = len(t["colonnes"])
        for l in t["lignes"]:
            c = l["cellules"]
            if c[0] in FAIT:
                etat, jour, note = FAIT[c[0]]
                c[5] = etat
                c[7] = jour
                c[8] = (c[8] + u" " if c[8] else u"") + note
        for c in MIENNES:
            assert len(c) == largeur, (c[0], len(c), largeur)
            t["lignes"].append(dict(cellules=c))

with io.open(p, "w", encoding="utf-8") as f:
    json.dump(b, f, ensure_ascii=False, indent=1)

print("buts:", len(b["tables"][0]["lignes"]), "| actions:", len(b["tables"][1]["lignes"]))
