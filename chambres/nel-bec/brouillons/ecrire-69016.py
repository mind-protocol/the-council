# -*- coding: utf-8 -*-
# Troisieme billet de Marlo, meme jour : elle veut deux gosses a sa barriere a partir
# du 7e et elle me demande le tarif. Trois acheteurs sur trente tetes, dont ma propre
# maitresse. Le verrou 69005 empire ; il lui faut une troisieme clef.
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


AJOUT = (u" **Troisieme billet du meme soir, et ca empire** : Marlo veut a son tour "
         u"**deux tetes a sa barriere a partir du 7e**, et elle se propose de les payer "
         u"elle-meme. Nous serions alors **trois bourses sur trente tetes**, sur la meme "
         u"greve, dont deux du meme cote sans le savoir. Deux acheteurs qui ne se parlent "
         u"pas font le prix l'un contre l'autre : si elle paie sa barriere mieux que je ne "
         u"paie la Gadoue, mes six l'apprendront a la basse mer **avant que ses deux aient "
         u"fini leur premier jour**.")

V = table(u"\U0001F512 Verrous")
v = ligne(V, "69005")
if v is None:
    raise SystemExit("69005 absent")
if u"Troisieme billet" not in v["cellules"][3]:
    v["cellules"][3] += AJOUT
    v["cellules"][4] += (u" Et son troisieme billet du 3e : deux gosses a sa barriere du "
                         u"7e, payes de sa main, et la question du tarif posee a moi.")

C = table(u"\U0001F5DD️ Clefs")
if ligne(C, "69016") is None:
    C["lignes"].append({"cellules": [
        "69016",
        u"\U0001F91A **Un seul prix sur la greve, et une seule main qui le paie**",
        "69005",
        u"Je ne peux rien contre la bourse d'en face, mais je peux tout contre la notre : **les tetes que Marlo veut a sa barriere, c'est moi qui les loue, au meme prix que mes six et du meme sac.** Un prix dit par deux mains devient deux prix en un jour ; dit par une seule, il tient meme quand un autre offre plus, parce qu'il est celui de tout le monde et qu'on ne le marchande pas tete par tete. Et le tarif que je lui donne n'est pas une journee : **on n'achete pas la journee, on achete la maree** — deux tetes appariees coutent moins qu'une tete au piquet, et aucune n'a eu a choisir entre manger et compter (69011).",
        u"Rien de plus en argent : les memes gosses, le meme pain, le meme sou. **Ce qu'elle ferme** : ses deux tetes de la barriere sortent alors de ma main, donc **elles portent ma marque** — si l'on cherche qui paie les gosses de cette greve, on trouvera une seule reponse au lieu de deux, et cette reponse sera moi. **Ce qu'elle coute vraiment** : elle demande a ma maitresse de ne pas payer directement ce qu'elle veut avoir, et une maitresse a qui l'on demande ca peut l'entendre de travers.",
        u"Une seule et meme somme par tete et par jour sur les trois postes — la Gadoue, la barriere de l'aire, le point du jour — et pas une tete qui vienne me demander pourquoi l'autre a plus",
        u"**proposee le 3e au soir** — a elle de la retenir ou non, ce n'est pas de mon mandat",
    ]})

A = table(u"⚔️ Actions")
if ligne(A, "69026") is None:
    A["lignes"].append({"cellules": [
        "69026",
        u"\U0001F91A Donner le tarif a Marlo, et demander que ses deux tetes passent par ma main",
        "69016",
        u"Rendre le tarif tel que je le connais et non tel qu'on l'espere : ce que je paie, ce que sa ligne rayee offrait, ce que le troisieme paie et **que je ne sais pas encore**. Puis la seule chose qui compte : **une seule main paie sur cette greve**. Ses deux tetes du 7e sont louees, appariees et payees par moi, au prix de mes six.",
        u"Par billet le 3e au soir, puis de vive voix a La Gaffe le 6e",
        "O22",
        u"M03",
        u"Rien — c'est un prix a dire et une main a obtenir",
        u"69024",
        u"le 3e au soir — **avant le 7e**, jour ou elle veut ses deux tetes",
        u"faite",
        u"le 3e — billet parti ; sa reponse manque",
        u"Elle a ecrit : « je prefere les payer moi que de decouvrir qu'ils sont deja payes. » C'est la bonne peur et la mauvaise reponse : payer soi-meme n'empeche pas qu'ils soient deja payes, ca met seulement un second prix sur la greve. Ce qui l'empeche, c'est la paire et l'accord des ficelles (69014).",
    ]})

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("69005 aggrave · clef 69016 · action 69026")
