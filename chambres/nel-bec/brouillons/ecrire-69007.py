# -*- coding: utf-8 -*-
# Quatrieme billet de Marlo, le 3e au soir. Elle accorde tout : le tarif, la paire,
# le meme sac, la borne, les retours. Et elle ajoute deux choses que je n'avais pas
# demandees : ma ligne fait foi sans recompte, et mon nom sur la colonne.
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


# ---- 1. Trancher 69016 : elle l'a retenue de sa main ----
C = table(u"\U0001F5DD️ Clefs")
k = ligne(C, "69016")
if k is not None:
    k["cellules"][6] = (u"**RETENUE le 3e au soir, par Marlo Vasse elle-meme** : « Et je ne "
                        u"les paie pas. Loue-les par ta main, meme prix que tes six, MEME SAC. "
                        u"Une seule main paie, un seul prix. » Elle rembourse le sac a la maree "
                        u"sur presentation de ma ligne. La proposition du 69026 n'est plus une "
                        u"proposition : c'est un accord.")

# ---- 2. La preuve de 61001, durcie de sa bouche ----
L = table(u"\U0001F517 Affaires liées — les liens écrits, puis les calculés")
add = (u" **Durci de sa main le 3e au soir, et c'est plus dur que ce que le registre "
       u"dit** : six jours sans un trou **dont TROIS ou elle ne sera pas a Port-Real** ; "
       u"pas une journee manquante, **pas une journee de sa main**, et **pas un homme qui "
       u"ait attendu sa parole pour ecrire**. Le pourquoi, qu'on ne m'avait jamais dit : "
       u"**elle vend les portes, en colonnes.** Une colonne trouee ne vaut pas la moitie, "
       u"elle ne vaut RIEN — l'acheteur ignore ou est le trou et doit tout recompter. "
       u"C'est pour ca que la preuve est de SUITE et non de quantite.")
n = 0
for l in L["lignes"]:
    c = l.get("cellules") or []
    if len(c) >= 5 and c[0] == "sert" and c[3].replace(u"\U0001F3AF", "").strip() == "61001" \
            and u"Durci de sa main" not in c[4]:
        c[4] += add
        n += 1

# ---- 3. Le verrou du sac ----
V = table(u"\U0001F512 Verrous")
if ligne(V, "69007") is None:
    V["lignes"].append({"cellules": [
        "69007",
        u"\U0001F9FE **Ma ligne fait foi sans que personne la recompte**",
        "69000",
        u"L'accord du 3e au soir : je tiens le sac, je loue les six et les deux de la barriere, j'ecris la ligne, **et elle rembourse a la maree sur presentation de ma ligne, sans recompter** — « ta ligne fait foi sans que je recompte ». C'est de la confiance et c'est justement pour ca que c'est un empechement : **un sac qui passe par des mains pieds nus perd un sou**, ce n'est pas une supposition, c'est une semaine. Le jour ou le compte tombera court, il n'y aura **qu'un nom sur la ligne et ce sera le mien**, et je n'aurai rien a opposer parce que personne n'aura jamais recompte. Une main de onze ans qu'on ne verifie jamais n'est pas une main de confiance : c'est la main qu'on designera proprement le premier jour ou le compte sera faux. Et le jour ou l'on me designe, mes six s'arretent — la colonne aussi, au milieu de ses six jours, et elle repart de zero.",
        u"Le quatrieme billet de Marlo Vasse du 3e, de sa main : « je te rembourse le sac a la maree, sur presentation de ta ligne, et ta ligne fait foi sans que je recompte » ; et « je veux qu'il trouve ton nom et pas le mien » sur la provenance de la colonne.",
        u"Quand **au moins une ligne sur six aura ete recomptee par quelqu'un qui n'est pas moi**, et que le recompte sera ecrit sur la ligne",
    ]})

if ligne(C, "69018") is None:
    C["lignes"].append({"cellules": [
        "69018",
        u"\U0001F9FE **Je demande a etre recomptee**",
        "69007",
        u"Ce n'est pas de la defiance envers elle, c'est ce qui rend ma ligne **opposable**. Au sixieme jour, la ligne du sac se recompte devant elle ou devant qui elle nomme — sous, quignons, sous du sixieme, tete par tete — et **le recompte s'ecrit sur la ligne, de la main de celui qui recompte, pas de la mienne**. Une ligne recomptee une seule fois vaut six lignes crues : la premiere se defend, les autres ne se defendent pas. Et le meme principe que la paire (69014) : ce qui protege n'est pas la confiance, c'est le second regard.",
        u"Un quart d'heure au sixieme jour, et l'ennui de demander a sa maitresse un travail qu'elle a explicitement offert de ne pas faire. **Ce qu'elle ferme** : recompter, c'est ouvrir le compte a une seconde paire d'yeux — celui qui recompte apprend ce que je paie, a combien de tetes, et donc combien de tetes je tiens ; on echange un risque de nom contre un peu de secret. **Ce qu'elle coute vraiment** : le jour ou le recompte tombera juste six fois de suite, on cessera de le faire — et il faudra le redemander.",
        u"Au sixieme jour, un recompte ecrit sur ma ligne d'une main qui n'est pas la mienne",
        u"**retenue le 3e au soir** — a demander des la premiere paie, le 4e",
    ]})

A = table(u"⚔️ Actions")
if ligne(A, "69028") is None:
    A["lignes"].append({"cellules": [
        "69028",
        u"\U0001F9FE Faire recompter ma ligne du sac, et refuser qu'elle fasse foi seule",
        "69018",
        u"Lui ecrire ce soir que je n'accepte pas la ligne qui fait foi sans recompte, et pourquoi. Puis, des la premiere paie : tenir la ligne du sac tete par tete, et au sixieme jour la faire recompter par elle ou par qui elle nomme, **le recompte ecrit de sa main sur ma ligne**.",
        u"La greve basse, puis la ou elle voudra recompter",
        "O22",
        u"M03",
        u"Un quart d'heure, et de le demander",
        u"69022 · 69024",
        u"dit le 3e au soir · premier recompte **le 9e**, au sixieme jour de colonne",
        u"en cours",
        "",
        u"Elle veut mon nom sur la provenance de la colonne, pour qu'elle se vende deux fois sans mentir une seule. Je le prends — mais un nom qui repond de la marchandise doit pouvoir repondre du sac, et on ne repond de rien sur un compte que personne n'a jamais verifie. Ecrit le 3e au soir.",
    ]})

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("69016 tranchee · %d liens 61001 durcis · verrou 69007 · clef 69018 · action 69028" % n)
