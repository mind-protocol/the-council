# -*- coding: utf-8 -*-
# Bourbe repond le 3e au soir. Deux choses de lui, et les deux sont bonnes :
#  - ma lettre portait DEUX dates pour une seule chose (au sixieme / le 9e) ;
#  - ma plus grosse perte de la semaine n'est pas entre les mains, elle est ECRITE
#    et LEGALE : un sou sur vingt au change, qui sort du sac avant le premier noeud.
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
A = table(u"⚔️ Actions")

# --- 69012 : le sou sur vingt n'est pas une perte, c'est une LIGNE ---
k = ligne(C, "69012")
if k is not None and u"quatre colonnes" not in k["cellules"][4]:
    k["cellules"][4] += (u" **Corrige le 3e au soir, sur Hann Bourbe, et c'est ma faute de "
                         u"comptable** : j'avais porte le sou sur vingt comme une perte "
                         u"negligeable — « moins qu'un quignon ». C'est faux de forme, sinon de "
                         u"montant. **La plus grosse perte de ma semaine n'est pas entre les "
                         u"mains, elle est ecrite et elle est legale**, et elle sort du sac "
                         u"AVANT que la premiere ficelle ait un noeud. Une deduction reguliere "
                         u"qu'on n'ecrit pas est indiscernable d'un vol au moment du recompte : "
                         u"au premier compte qui tombe court, **c'est une paire de pieds nus "
                         u"qu'on designera pour un sou qui n'a jamais quitte le banc du "
                         u"changeur**. Donc elle se porte en **quatre colonnes** : le sac recu, "
                         u"le sac change, l'ECART, le jour et l'heure.")

# --- 69022 : la paie se fait en ecrivant l'ecart ---
a = ligne(A, "69022")
if a is not None and u"quatre colonnes" not in a["cellules"][3]:
    a["cellules"][3] += (u" **Et l'on ecrit le change avant de payer, en quatre colonnes : sac "
                         u"recu / sac change / ecart / jour et heure.** Le sou sur vingt est une "
                         u"ligne, pas une perte : ce qui n'est pas ecrit se retrouve sur le dos "
                         u"de la derniere main qui a tenu le sac.")

# --- 69018 : la date, et pourquoi elle a bouge ---
k18 = ligne(C, "69018")
if k18 is not None and u"le 6e" not in k18["cellules"][6]:
    k18["cellules"][6] = (u"**RETENUE le 3e, accordee le meme soir — et la date corrigee par "
                          u"Hann Bourbe : LE 6e, non le 9e.** Ma lettre portait deux dates pour "
                          u"une seule chose (« au sixieme » en tete, « le 9e » au pied) : c'est "
                          u"exactement le chiffre mort que je m'etais jure de ne pas laisser "
                          u"vivre. Ses deux raisons valent mieux que ma date : le 9e sa caisse "
                          u"touche le fond, **et un homme qui recompte le jour ou il est court "
                          u"cherche a se rassurer et non a se contredire** ; et une ligne "
                          u"recomptee trois jours en retard a eu trois jours pour etre mise au "
                          u"propre, pas forcement par moi. **On ne contredit bien que du frais.**")

a28 = ligne(A, "69028")
if a28 is not None and u"le 6e" not in a28["cellules"][9]:
    a28["cellules"][9] = (u"dit le 3e au soir · **premier recompte LE 6e** (trois jours de sac, "
                          u"frais), par Hann Bourbe · le sou de la paire tombe au 9e et se "
                          u"recompte a part")
    a28["cellules"][12] += (u" — Il a corrige ma date et il a raison : on ne recompte pas une "
                            u"fois par colonne, **on recompte frais**. Il ecrira les deux "
                            u"chiffres si le sien differe du mien, et il ne corrigera pas le "
                            u"mien : c'est exactement ce que je voulais.")

json.dump(d, io.open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("69012 : l'ecart en quatre colonnes · 69022 mis a jour · 69018/69028 : recompte au 6e")
