# -*- coding: utf-8 -*-
# Ce que ma journee du 3e a trouve et que le calcul ne trouvera jamais tout seul.
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
if not deja(V, "69004"):
    V["lignes"].append({"cellules": [
        "69004",
        u"\U0001F312 **La Gadoue s'ouvre la nuit, et il n'y a personne de moi la nuit**",
        "69000",
        u"Ma colonne court **du point du jour a la fermeture** : c'est ecrit de ma main au 69000, et mes six tetes dorment le reste. Or la nuit du 2e au 3e la Gadoue a ete ouverte **a une heure ou elle ne l'avait pas ete en quatorze mois** — lanterne du corps de garde a terre et brulant encore, quatre hommes a cinq pas d'un seuil, dont un qui ne respirait plus. Personne de chez moi n'y etait, et personne n'y sera : je ne mets pas un gosse a cette porte apres la nuit tombee, et je n'y vais pas moi-meme. **Six colonnes pleines diront donc que la Gadoue est une porte de jour**, et elles le diront sans un trou, du ton d'un compte juste — c'est le seul mensonge qu'une colonne sache faire toute seule.",
        u"La lettre de Marlo Vasse du 3e — **rapportee, je ne l'ai pas vu de mes yeux** ; et mon propre 69000, ma main, le 3e, qui borne la colonne au point du jour. J'ai tente de lire le sol et la lanterne depuis ma marche le 3e a midi et je n'ai pas eu de verdict.",
        u"Quand la colonne dira quelque chose de chaque nuit — **fut-ce qu'elle a ete tranquille**",
    ]})

C = table(u"\U0001F5DD️ Clefs")
if not deja(C, "69013"):
    C["lignes"].append({"cellules": [
        "69013",
        u"\U0001F312 **On ne veille pas la nuit, on la lit au point du jour**",
        "69004",
        u"Une porte qu'on ouvre la nuit **ecrit dans la boue**, et la boue tient jusqu'au premier charroi du matin. Donc on ne poste personne la nuit : la tete du matin, celle que la maree met a la porte au point du jour, arrive **un quart d'heure avant le premier charroi** et lit trois choses qu'un gosse lit sans savoir une lettre — une orniere dans la boue de nuit sous le vantail, la lanterne hors de son crochet, la barre hors du sien. **Cinquieme ficelle, un noeud par signe, trois au plus.** Zero noeud vaut sol propre. Ce n'est pas un souvenir, donc ca ne rabote pas ; et ca ne peut pas depasser trois, donc ca ne s'emballe pas non plus.",
        u"Une brasse de plus de ligne de rebut, au meme filet creve du mole, et un quart d'heure de lever plus tot — pas un quignon de plus, pas une tete de plus, **et pas un enfant a la porte apres la nuit tombee**. **Ce qu'elle ferme** : la boue dit QU'ON est passe, jamais qui ni avec quoi — et une nuit de pluie efface tout, donc les nuits de pluie s'ecrivent **manquantes** et surtout pas calmes. **Ce qu'elle coute vraiment** : le jour ou le sol sera balaye avant l'aube, je saurai qu'on sait que je le lis. Ce jour-la aussi est une reponse, et je la prends.",
        u"Au sixieme jour, six bas de colonne qui portent chacun un mot de la nuit — **y compris les nuits qui ne disent rien**",
        u"**retenue le 3e**",
    ]})

A = table(u"⚔️ Actions")
if not deja(A, "69023"):
    A["lignes"].append({"cellules": [
        "69023",
        u"\U0001F312 Faire lire le sol au point du jour, cinquieme ficelle",
        "69013",
        u"La tete du matin arrive un quart d'heure avant le premier charroi et regarde trois choses, dans l'ordre : orniere dans la boue de nuit sous les vantaux, lanterne du corps de garde a son crochet ou non, barre a son crochet ou non. **Un noeud par signe sur la cinquieme ficelle, trois au plus, zero pour sol propre.** S'il a plu, elle ne noue rien et me le dit : j'ecris la nuit manquante.",
        u"Porte de la Gadoue, montant nord",
        "O22",
        u"M03 · M01",
        u"Une brasse de ligne de rebut, meme filet creve du mole",
        u"69020 · 69021",
        u"le 4e au point du jour",
        u"à faire",
        "",
        u"L'appariement se refait au sixieme parce que la maree tourne ; **cette ficelle-la ne tourne pas** — elle est de la porte, pas de la maree, et elle suit qui a le point du jour quel qu'il soit. Ecrite le 3e, apres la lettre de Marlo.",
    ]})

L = table(u"\U0001F517 Affaires liées — les liens écrits, puis les calculés")
pourquoi = (u"61001 veut que les portes se comptent **sans Néra**. Mes deux etats cibles "
            u"sont les deux moities de ce compte : la terre par la Gadoue, l'eau par la "
            u"greve. 61001 vit dans INSPECTER, qui n'est pas sur mon etagere — la remontee "
            u"est donc vraie et **je ne peux pas la verifier d'ici**. Ce n'est pas un "
            u"chiffre casse : c'est un chiffre chez quelqu'un d'autre.")
n = 0
for l in L["lignes"]:
    c = l.get("cellules") or []
    if len(c) >= 5 and c[0] == "sert" and c[3].replace(u"\U0001F3AF", "").strip() == "61001" \
            and not c[4].strip():
        c[4] = pourquoi
        n += 1

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ecrit : 69004 verrou / 69013 clef / 69023 action / %d liens 61001 motives" % n)
