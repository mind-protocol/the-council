# -*- coding: utf-8 -*-
# Second billet de Marlo, une heure apres le premier : elle raye la ligne des copies.
# J'avais bati 69005 sur ce prix-la. Elle m'a dit de corriger un chiffre faux plutot
# que de le laisser passer. Je corrige le mien.
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


def ligne(t, num):
    for l in t["lignes"]:
        c = l.get("cellules") or [""]
        if c[0].strip().replace("*", "") == num:
            return l
    return None


V = table(u"\U0001F512 Verrous")
v = ligne(V, "69005")
if v is None:
    raise SystemExit("69005 absent")
v["cellules"] = [
    "69005",
    u"\U0001FA99 **Mes six tetes sont louables ailleurs, et j'ignore a quel prix et en quelle monnaie**",
    "69000",
    u"Corrige le 3e au soir. **Ce que j'avais ecrit d'abord etait bati sur un prix qui n'existe plus** : Marlo avait mis deux sous par jour et par tete pour la copie d'une feuille, elle a raye la ligne une heure apres, et je ne laisse pas passer un chiffre mort dans mon registre. Ce qui reste vrai, et qui est pire : **on paie deja des gosses de MA greve, depuis trois jours, pour compter a l'aire de bris** — donc une autre bourse loue des tetes ici, a un tarif que je ne connais pas. Les miennes tiennent la Gadoue pour un quignon le jour et un sou au sixieme. Si l'autre paie plus, elles ne me quitteront pas et ne me le diront pas : elles rendront leur ficelle **et la meme au second acheteur**, ou rabotees a sa mesure. Une colonne vendue deux fois arrive a l'heure, sans un trou, et fausse a l'endroit precis qu'on a paye — ma preuve du 69000, six colonnes sans un trou, ne sait pas voir ca.",
    u"Marlo Vasse, ses deux billets du 3e : trois jours qu'on paie des gosses a l'aire de bris (le premier), et la ligne des copies rayee de sa main (le second). Mon 69011, ma main le 3e, pour ce que je paie, moi.",
    u"Quand je saurai **le prix et la monnaie** de l'autre bourse — par tete, par jour, depuis quel jour — et quand ce que je paie ne se gagnera plus a une seule tete",
]

C = table(u"\U0001F5DD️ Clefs")
if ligne(C, "69015") is None:
    C["lignes"].append({"cellules": [
        "69015",
        u"\U0001FA99 **On ne demande pas le prix, on ouvre un guichet**",
        "69005",
        u"Un prix demande a un gosse remonte le soir meme a celui qui le paie : on lui apprend qu'on sait, et il change de greve. **Mais un gosse paye en piece neuve ne peut pas la depenser** — pieds nus a la Gadoue, on la lui prend et on lui demande d'ou elle vient (69003). Je passe deja au banc de dame Sirel Quintaine avant chaque paie et j'en ressors avec de l'use (69012). **Donc je porte un peu plus de petite monnaie que ma paie n'en demande, et je change au pair, sans mon sou sur vingt, pour n'importe quelle tete de la greve.** Le metal me vient **dans la main** au lieu de m'etre raconte : je vois la frappe, je n'ai interroge personne. Et ce qu'un gosse apporte a changer dit le montant tout seul, et le jour ou il l'apporte dit depuis quand.",
        u"Ce que le banc me prend en plus sur le change des autres, et rien d'autre — je ne paie pas la piece, je l'echange. **Ce qu'elle ferme** : elle ne donne que ceux qui viennent, et l'on ne saura jamais par la ceux qui sont payes en use ; le silence du guichet ne prouve donc rien, et surtout pas qu'on paie en vieil argent. **Ce qu'elle coute vraiment** : au bout de quelques jours, la greve saura que la petite change chez elle — c'est une marque de plus sur moi, et je la prends encore, comme au 69012, parce qu'elle est sur moi et non sur un enfant.",
        u"Une frappe tenue de ma main, non rapportee — et le montant et le jour qui viennent avec elle, sans qu'une question ait ete posee a personne",
        u"**retenue le 3e au soir**, apres le second billet de Marlo",
    ]})

A = table(u"⚔️ Actions")
if ligne(A, "69025") is None:
    A["lignes"].append({"cellules": [
        "69025",
        u"\U0001FA99 Porter de la monnaie en trop au banc, et changer au pair pour qui vient",
        "69015",
        u"Au banc, le 4e au matin, en meme temps que le 69022 : prendre **plus de petite monnaie usee que la paie n'en demande**. Puis, sur la greve, changer au pair — sans rien prendre — la piece de toute tete qui en apporte une qu'elle ne peut pas depenser. **On ne demande ni qui paie, ni pourquoi, ni combien il y en aura.** On note pour soi : la frappe, le montant, le jour.",
        u"Le banc de dame Sirel Quintaine, puis la greve basse",
        "O22",
        u"M03",
        u"Le surplus de petite monnaie, sur les deux cerfs de la semaine — et pas un sou pris a un enfant",
        u"69022",
        u"a partir du 4e au matin, et tant qu'il vient quelqu'un",
        u"à faire",
        "",
        u"C'est la reponse a la seule question du second billet de Marlo — a quel prix et **en quelle monnaie** on loue les gosses de cette greve. Elle veut la frappe : la frappe ne se rapporte pas, elle se tient. Ecrit le 3e au soir.",
    ]})

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("corrige : verrou 69005 · ajoute : clef 69015, action 69025")
