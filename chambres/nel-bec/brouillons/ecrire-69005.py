# -*- coding: utf-8 -*-
# Le soir du 3e, apres la lettre de Marlo. Ce qu'elle a publie sans le voir :
# un prix pour une feuille. Mes six sont payees au-dessous de ce prix-la.
import json, io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "..", "..", "etat", "books", "nera-les-portes.json")
P = os.path.normpath(P)
d = json.load(io.open(P, encoding="utf-8"))


def table(titre):
    for t in d["tables"]:
        if t["titre"] == titre:
            return t
    raise SystemExit("table absente : " + titre)


def deja(t, num):
    for l in t["lignes"]:
        c = l.get("cellules") or [""]
        if c[0].strip().replace("*", "") == num:
            return True
    return False


V = table(u"\U0001F512 Verrous")
if not deja(V, "69005"):
    V["lignes"].append({"cellules": [
        "69005",
        u"\U0001FA99 **Ma paie est au-dessous du prix qu'on vient de publier pour la meme feuille**",
        "69000",
        u"Marlo Vasse met **deux sous par jour et par tete** pour la COPIE d'une feuille qu'un gosse porte deja ailleurs — trois tetes, soixante sous la dizaine de jours. La regle est bonne : acheter la copie n'apprend rien a l'acheteur. Mais **un prix dit une fois sur la greve n'est pas dit une fois** : trente tetes se parlent a la basse mer. Mes six sont payees d'un quignon le jour et **d'un sou au sixieme** — pour le meme geste exactement : compter et rendre. Le jour ou l'une des six l'apprend, elle ne me quitte pas et ne me le dit pas : elle **vend ma colonne a l'autre bourse au prix que ma propre maitresse vient d'afficher**, et me rend sa ficelle quand meme. Une colonne vendue deux fois arrive a l'heure, sans un trou, et fausse a l'endroit precis qu'on lui a paye. Ma preuve du 69000 — six colonnes de suite sans un trou — ne sait pas voir ca.",
        u"La lettre de Marlo Vasse du 3e, de sa main : deux sous par jour et par tete, a la feuille et jamais a l'avance. Et mon propre 69011, ma main le 3e : un quignon par tete et par jour, un sou au sixieme.",
        u"Quand ce que je paie ne se gagnera plus a une seule tete — quand le sou du sixieme ira **a la paire et sur l'accord des deux ficelles**, jamais a un gosse seul",
    ]})

C = table(u"\U0001F5DD️ Clefs")
if not deja(C, "69014"):
    C["lignes"].append({"cellules": [
        "69014",
        u"\U0001F91D **Le sou se gagne a deux, sur l'accord des ficelles**",
        "69005",
        u"Le 69010 attend deja pour preuve **deux tetes sur la meme porte, a un noeud pres**. J'en fais le PRIX au lieu d'en faire seulement la preuve : au sixieme, le sou n'est pas du a celui qui a tenu son poste, il est du **aux deux quand leurs deux ficelles tombent au meme nombre a un noeud pres**. Qui rabote pour une autre bourse fait perdre son sou a celui qui mange a cote de lui, et celui-la le lui reprend de sa main, pas de la mienne. **Je n'ai pas besoin de savoir qui achete** : il suffit que l'autre soit assis a cote et attende son sou.",
        u"Pas un sou de plus : six sous au sixieme, les memes, autrement attribues. **Ce qu'elle ferme** : deux tetes qui s'entendent mentent ensemble, et alors la paire n'est plus un miroir mais un mur — donc une paire ne tient pas la meme porte deux colonnes de suite. Et un gosse dont la paire a manque sa maree perd un sou qu'il n'a pas vole : c'est injuste, je le sais, et **je le dis tout haut le premier jour** au lieu de le laisser decouvrir au sixieme.",
        u"Au sixieme : trois paires, six ficelles, pas un ecart de plus d'un noeud — et le sou paye a la paire devant les deux",
        u"**retenue le 3e au soir**, apres la lettre de Marlo",
    ]})

A = table(u"⚔️ Actions")
if not deja(A, "69024"):
    A["lignes"].append({"cellules": [
        "69024",
        u"\U0001F91D Dire le prix de la paire avant que la premiere piece change de main",
        "69014",
        u"Au point du jour du 4e, devant les six ensemble et non une a une : le quignon est du chaque jour a chacun ; **le sou du sixieme est du a la paire, et seulement si les deux ficelles tombent au meme nombre a un noeud pres**. Dit avant la premiere paie, jamais apres.",
        u"Greve basse, avant la porte et avant le banc",
        "O22",
        u"M03",
        u"Rien — des mots, et de les dire aux six a la fois",
        u"69021",
        u"le 4e au point du jour — **avant** le 69022",
        u"à faire",
        "",
        u"Un prix qu'on change apres la premiere paie est une punition ; le meme prix dit avant est une regle. Ecrit le 3e au soir, du meme coup que le 69005.",
    ]})

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ecrit : verrou 69005 / clef 69014 / action 69024")
