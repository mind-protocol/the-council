# -*- coding: utf-8 -*-
# Le 3e au soir. L'arbitre m'a recopie 61001 en entier. Trois choses en sortent :
#  - la preuve est une preuve de SUITE, et mes deux moities doivent tenir LES MEMES six jours ;
#  - le "trou" du plan n'est pas de moi : le detecteur cherche au mauvais endroit ;
#  - la porte a deja, depuis le 1er, un homme qui a une raison ECRITE d'y etre tous les jours.
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


# ---- 1. La preuve des deux etats cibles : LES MEMES six jours, pas six chacun ----
E = table(u"\U0001F3AF États cibles")
sup = (u" — et **ce sont LES MEMES six jours que le 69100**, non six jours chacun : "
       u"61001 se prouve par la SUITE, une seule journee sautee d'un cote fait repartir "
       u"le compte de zero **des deux cotes**.")
sup2 = (u" — et **ce sont LES MEMES six jours que le 69000**, non six jours chacun : "
        u"61001 se prouve par la SUITE, une seule journee sautee d'un cote fait repartir "
        u"le compte de zero **des deux cotes**.")
e0 = ligne(E, "69000")
if e0 and u"LES MEMES six jours" not in e0["cellules"][4]:
    e0["cellules"][4] += sup
e1 = ligne(E, "69100")
if e1 and u"LES MEMES six jours" not in e1["cellules"][4]:
    e1["cellules"][4] += sup2

# ---- 2. Les liens vers 61001 : la remontee n'est pas cassee, le detecteur cherche mal ----
L = table(u"\U0001F517 Affaires liées — les liens écrits, puis les calculés")
neuf = (u"**61001, recopie entier le 3e au soir : « LES PORTES SE COMPTENT SANS MOI » — "
        u"ce qui entre et sort par la Gadoue et par le port est releve chaque jour SANS "
        u"QUE J'Y AILLE ; preuve : six jours de colonnes sans un trou ; sert 60005.** "
        u"Le mot qui commande tout l'etat est SANS QUE J'Y AILLE : on ne me demande pas de "
        u"compter, on me demande que ca se compte quand je n'y suis pas. Mes deux etats "
        u"cibles sont les deux moities du meme compte — la terre par la Gadoue, l'eau par "
        u"la greve — et elles doivent tenir LES MEMES six jours. "
        u"**Le trou signale par le plan n'en est pas un** : les etats cibles des Chantiers "
        u"sont ranges dans une table commune avec une colonne Volume, la table des trous "
        u"d'INSPECTER cherche au mauvais endroit et crie au vide sur 61000, 61001 et 61002. "
        u"La ligne existe, complete. **La remontee est bonne — qu'on ne la rechasse pas.**")
n = 0
for l in L["lignes"]:
    c = l.get("cellules") or []
    if len(c) >= 5 and c[0] == "sert" and c[3].replace(u"\U0001F3AF", "").strip() == "61001":
        c[4] = neuf
        n += 1

# ---- 3. Le verrou du jour : la porte a deja son homme, et il est en regle ----
V = table(u"\U0001F512 Verrous")
if ligne(V, "69006") is None:
    V["lignes"].append({"cellules": [
        "69006",
        u"\U0001F528 **Un homme a deja, sur ma porte, une raison ecrite d'y etre tous les jours — et ce n'est pas moi**",
        "69000",
        u"Depuis le 1er, la ferrure du gond de la Gadoue est un ouvrage paye : **sept cerfs comptes par le Guet sur une ligne ecrite**. Qui travaille sur cette ligne a le droit d'etre a la porte **tous les jours et a toute heure, la regle a la main**, sans que personne le remarque ni le lui demande. C'est exactement ce que le 61001 reclame — une presence quotidienne qui ne se voit pas — et un autre l'a obtenue avant moi, non pas en se cachant mais **en la faisant facturer**. Or mes six tetes arrivent a cette meme porte le 4e, avec quatre ficelles au poignet et rien a y faire. Devant un homme dont le metier est d'etre la, un gosse qui reste sans raison est la seule chose anormale du tableau. Le 69003 dit que le jour ou l'une des six est demandee, la colonne s'arrete sans que je l'apprenne : voila **qui** la demandera, et il sera dans son droit.",
        u"La ligne du Guet du 1er, sept cerfs, ferrure du gond — rendue a Marlo Vasse par moi et payee au juste ; et l'arbitre de zone le 3e au soir, qui la nomme comme une presence quotidienne obtenue par facture. Et de mes yeux, le 3e a midi : le vantail droit ne se ferme pas, il est cale au coin — l'ouvrage n'est pas fini.",
        u"Quand chacune de mes six aura, a cette porte, **une raison d'y etre qui ne soit pas de compter**",
    ]})

C = table(u"\U0001F5DD️ Clefs")
if ligne(C, "69017") is None:
    C["lignes"].append({"cellules": [
        "69017",
        u"\U0001F9FA **On ne se cache pas d'un homme en regle : on se donne une regle aussi**",
        "69006",
        u"Un gosse assis compte ; **un gosse qui porte quelque chose attend quelqu'un.** Chaque tete arrive a la porte avec une charge et un motif visible, et jamais le meme deux jours de suite : un panier vide qu'on vient rendre, de l'eau, du sable pour l'ouvrage, la soupe du poste a l'heure ou le poste mange (midi et quart a midi et demi, et c'est justement la demi-heure ou l'on ne demande rien). **La ficelle se noue au fond du panier, pas au poignet** — le 69010 disait deja que quatre ficelles au poignet sont une marque ; la charge les couvre. Ce n'est pas se cacher : c'est etre la pour autre chose, comme lui.",
        u"Rien, ou le pret d'un panier. **Ce qu'elle ferme** : une charge occupe une main et ralentit le noeud — le 69010 avait mesure neuf charrois pour neuf noeuds les mains libres, ca se remesurera avec le panier ; si le compte decroche, c'est la charge qu'on allege, pas la ficelle. **Ce qu'elle coute vraiment** : un motif qui se repete devient a son tour un motif — donc on change de charge chaque jour, et la tete qui vient pour la soupe n'est jamais celle qui est venue la veille.",
        u"Six jours de suite ou aucune des six n'est interrogee a la porte, **et le compte toujours a un noeud pres entre les deux tetes d'une paire**",
        u"**retenue le 3e au soir**, sur le mot de l'arbitre",
    ]})

A = table(u"⚔️ Actions")
if ligne(A, "69027") is None:
    A["lignes"].append({"cellules": [
        "69027",
        u"\U0001F9FA Donner une charge et un motif a chaque tete, et compter l'homme de la ferrure",
        "69017",
        u"Avant le premier poste : a chaque tete, une charge du jour et un motif a dire si on l'arrete, differents d'un jour a l'autre et jamais deux fois de suite les memes. Ficelle au fond du panier. Et pendant les six jours, **compter l'homme de l'ouvrage comme on compte un charroi** : combien de fois il vient, a quelle heure, s'il repart avec quelque chose — c'est celui qui revient qu'on compte, pas ceux qui regardent.",
        u"Porte de la Gadoue, montant nord",
        "O22",
        u"M03 · M01",
        u"Un panier prete, de la ligne de rebut, rien d'autre",
        u"69020 · 69021",
        u"le 4e, avant le premier poste",
        u"à faire",
        "",
        u"Il a obtenu par facture ce que je cherche a obtenir par ruse. Je ne peux pas me faire facturer ; je peux avoir une raison d'etre la. Ecrit le 3e au soir, sur la ligne 61001 recopiee par l'arbitre.",
    ]})

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("preuves 69000/69100 liees · %d liens 61001 recrits · verrou 69006 · clef 69017 · action 69027" % n)
