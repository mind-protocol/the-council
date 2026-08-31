# -*- coding: utf-8 -*-
# Elle a pris le recompte, et elle a nomme la main : Hann Bourbe, trente ans de vase,
# et une regle a lui — jamais un chiffre sans dire l'heure ou il l'a releve.
# Cette regle-la est meilleure que la mienne. Je la prends pour ma colonne aussi.
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


C = table(u"\U0001F5DD️ Clefs")
k = ligne(C, "69018")
if k is not None and u"Hann Bourbe" not in k["cellules"][3]:
    k["cellules"][3] += (u" **La main est nommee le 3e au soir : HANN BOURBE**, trente ans de "
                         u"vase, et non Marlo elle-meme — ce qui vaut mieux, une maitresse qui "
                         u"recompte son propre sac ne prouve rien a un tiers. Il a **une regle a "
                         u"lui, juree devant six hommes : jamais un chiffre sans dire l'heure ou "
                         u"il l'a releve.** Cette regle est plus dure que la mienne et je la "
                         u"prends : **desormais chaque nombre que j'ecris — ligne du sac ET "
                         u"colonne de la porte — porte l'heure ou je l'ai pris sur la ficelle**, "
                         u"pas seulement le jour. Ca ne coute rien, ca se fait au denouement du "
                         u"soir, et ca rend mes chiffres lisibles par un homme qui n'est pas moi.")
    k["cellules"][6] = (u"**RETENUE le 3e au soir, et accordee de sa main le meme soir** — "
                        u"recompte au sixieme jour, tete par tete, par Hann Bourbe, ecrit sur ma "
                        u"ligne de sa main. Premier recompte le 9e.")

A = table(u"⚔️ Actions")
a = ligne(A, "69028")
if a is not None and u"Hann Bourbe" not in a["cellules"][12]:
    a["cellules"][9] = u"dit le 3e au soir · **premier recompte le 9e, par Hann Bourbe**"
    a["cellules"][12] += (u" — ACCORDE le 3e au soir : elle retire sa phrase, le recompte se "
                          u"fera, et la main est Hann Bourbe. Je lui ai ecrit le soir meme "
                          u"plutot que de le laisser l'apprendre d'elle : un homme qui doit "
                          u"recompter mon compte le 9e a le droit de savoir le 3e comment il "
                          u"est bati. Et j'adopte sa regle : l'heure du releve sur chaque "
                          u"chiffre.")

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("69018 : main nommee, regle de l'heure adoptee · 69028 mis a jour")
