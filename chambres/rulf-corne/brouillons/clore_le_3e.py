# -*- coding: utf-8 -*-
# 3e de la 4e lune, an 129 — ce que la journee a ferme.
import json, io, os

p = os.path.join(os.path.dirname(__file__), '..', 'books', 'affaire-rulf-corne.json')
b = json.load(io.open(p, encoding='utf-8'))

FAIT = {
    "P.4": ("faite", "129-04-03",
            "Trois buts sous « Ce que je veux », de ma main, chacun avec sa preuve : mon livre et rien qui n'ait ete regarde ; aucun compte de blocus sur une quille non visitee ; rien n'entre en rade que je ne le sache le premier."),
    "P.6": ("faite", "129-04-03",
            "Sept lignes R.1 a R.8 sous les dix premieres : ce dont je reponds vraiment au banc de l'Est, a l'anse du levant et a la course d'avis."),
    "P.8": ("faite", "129-04-03",
            "--demander au matin du 3e : les onze quilles du banc de l'Est portent-elles un engagement hors de mon livre ? Les registres ont rendu QUATRE cahiers avec numeros et dates, et deux doctrines contraires vivantes le meme jour. C'est ce verdict qui a fait rouvrir 22014 et naitre la clef 22064."),
}

R8 = ["R.8", "Tenir le role des coques d'une seule main, et le faire opposer aux quatre cahiers",
      "Clef 22064 : une quille, une ligne, une main. Nul cahier de cette maison ne compte une quille qui ne porte pas sa ligne au role du port, avec sa date de visite, tout engagement qu'elle porte, et LA MAREE pour laquelle on la veut.",
      "le role du port",
      "les onze lignes du banc de l'Est completes ; puis un premier refus ecrit et date, le jour ou deux cahiers voudront la meme quille a la meme maree",
      "en cours", "", "",
      "Ecrite le 3e comme clef proposee. Elle ne se decide pas sans le maitre des deniers, qui tient deux des quatre cahiers. Le refus prouvera que la clef tourne ; le role tout seul ne prouve rien."]

for t in b["tables"]:
    if t["titre"].startswith(u"⚔"):
        largeur = len(t["colonnes"])
        for l in t["lignes"]:
            c = l["cellules"]
            if c[0] in FAIT:
                etat, jour, note = FAIT[c[0]]
                c[5] = etat
                c[7] = jour
                c[8] = (c[8] + u" " if c[8] else u"") + note
        assert len(R8) == largeur, (len(R8), largeur)
        t["lignes"].append(dict(cellules=R8))

with io.open(p, "w", encoding="utf-8") as f:
    json.dump(b, f, ensure_ascii=False, indent=1)

# ce qui reste ouvert, pour que je le voie demain
for t in b["tables"]:
    if t["titre"].startswith(u"⚔"):
        for l in t["lignes"]:
            c = l["cellules"]
            if c[5] != "faite":
                print(u"%-5s %-8s %s" % (c[0], c[5], c[1]))
