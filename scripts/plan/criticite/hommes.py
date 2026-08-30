# -*- coding: utf-8 -*-
"""HOMMES — ce que chaque homme porte, les idees et leur prix, ce qu'un
homme NE VOIT PAS (la porte des hommes, leur charge), et le nom qu'on montre
pour une clef d'homme (affiche).
"""
import json
import re
import sys
import unicodedata

from plan.expose import nu, sans_emoji, NOM_GENRE
from plan.criticite.page import LARGEUR, cale, titre

def gens(livres):
    """{O##: (office, titulaire)} et {M##: (moyen, qui le tient)}.

    LE NOM SE COUPE A LA PREMIERE VIRGULE, et c'est une approximation assumee :
    « Ser Robert Quince, onze ans en charge » et « Dame Aurore Inchauspe, de La
    Noiseraie » portent leur glose dans la meme cellule. Le point-virgule separe
    deux hommes (« Tobb, de la Claie ; Nesse, du Marais du sud ») — les deux
    comptent, et chacun porte alors la charge entiere de l'office : on ne
    partage pas une charge en deux parce que deux hommes la tiennent."""
    from plan.expose import MO as _MO, registre_de as _ns
    offices, moyens = {}, {}
    for b in livres:
        # LE CASIER M/O, COMME DANS `charger()` — et l'oublier ici a coûté un
        # castellan. La Nera et le grand plan tiennent chacun leur registre sans
        # s'etre concertes : O01 vaut « Castellan de Peyredragon » d'un cote et
        # « Le chantier » de l'autre. Sans prefixe, le dernier livre lu ecrasait
        # l'autre — les vingt-cinq pas de ser Robert Quince etaient attribues a
        # Hann Bourbe, et le castellan ne figurait NULLE PART au tableau des
        # hommes. `couverture.py` a reparé exactement cette faute pour son
        # inventaire (l. 74-92) ; elle n'avait pas ete reportee ici.
        ns = _ns(b.get("id"))
        i = None
        for t in [b] + list(b.get("tables") or []):
            cols = t.get("colonnes") or []
            if not cols:
                continue
            from plan.expose import col as _col
            i_t = _col(cols, u"titulaire")
            i_q = _col(cols, u"qui le tient")
            if i_t is None and i_q is None:
                continue
            cible, i = (offices, i_t) if i_t is not None else (moyens, i_q)
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
                if len(c) <= max(1, i):
                    continue
                m = _MO.search(c[0])
                if not m:
                    continue
                qui = [x.split(u",")[0].strip() for x in c[i].split(u";") if x.strip()]
                cible[ns + m.group(1)] = (c[1], [q for q in qui if q and q != u"—"])
    return offices, moyens


TITRES = re.compile(u"^(ser|dame|lord|lady|le prince|la princesse|mestre|maitre|maître"
                    u"|septon|celui qu'on appelle) ", re.I)
MOI = re.compile(u"^(moi|moi seule|moi-même|moi meme)$", re.I)
# LA GLOSE AU TIRET CADRATIN COUPE UN HOMME EN DEUX. « SER STEFFON DARKLYN —
# DÉMIS PAR SA PROPRE BORNE » (O16) et « Ser Steffon Darklyn » (O12) faisaient
# deux porteurs, sur le premier goulot de la maison : sa charge se lisait en deux
# moities dont aucune n'etait la sienne. On coupe donc au tiret comme a la
# virgule — c'est la meme chose, une glose derriere le nom.
GLOSE = re.compile(u"\\s+[—–]\\s+.*$")
# UNE CASE VACANTE N'EST PAS UN HOMME. Les registres disent le vide en prose
# (« CASE BLANCHE », « VIDE. Ligne ouverte le 27e », « un trou ne se voit pas »),
# et cette prose se rangeait au classement des porteurs comme un titulaire.
VACANT = re.compile(u"^(vide|case blanche|néant|neant|à désigner|a designer|vacant"
                    u"|personne|personne encore|un trou|une case)\\b", re.I)
# « Elle-même », « Lui », « Eux-mêmes » : le moyen qui se tient tout seul. Ce
# n'est pas un porteur de plus, c'est l'absence de tiers.
SOI = re.compile(u"^(lui|elle|lui-même|elle-même|eux-mêmes|elles-mêmes"
                 u"|lui meme|elle meme|eux memes)$", re.I)


def cle_homme(nom):
    """DEUX REGISTRES, DEUX ORTHOGRAPHES DU MEME HOMME. Les offices ecrivent
    « Dame Aurore Inchauspe », les moyens « Aurore Inchauspe » : sans cette
    normalisation, elle porte 30 de criticite dans une colonne et 21 dans
    l'autre sans que les deux se rejoignent — et l'on conclut qu'on ne lui tire
    rien, alors qu'elle est le second goulot de la maison.

    « Moi » est la reine : les moyens sont ecrits de sa main, a la premiere
    personne. C'est une jointure devinee, et elle est dite en clair sous la
    table plutot que cachee dans un dictionnaire."""
    t = u" ".join(nu(nom).split())
    if MOI.match(t):
        return u"la reine"
    if SOI.match(t):
        return u"— lui-même —"
    if VACANT.match(t):
        return u"— personne, la case est vide —"
    t = TITRES.sub(u"", GLOSE.sub(u"", t)).strip()
    return t.lower()


# ─────────────────────────────────────────────── les idées, et leur prix
#
# CE QUE ÇA RÉPARE. `missions_de()` sait déjà proposer, par affaire, ce qu'il
# faudrait écrire pour que la chaîne tienne — « afin d'atteindre X, faire Y
# aurait effet Z ». Il les range par `force()`, un barème à la main (0, 1, 1+N,
# 20, 20+N, 60) qui mélange deux axes et ne sait rien du plan hors du cahier
# qu'il regarde. Résultat : trente-six listes d'une dizaine d'idées chacune, et
# aucun moyen de savoir laquelle des trois cent cinquante ouvre le plus.
#
# Ici on ne réécrit pas les détecteurs — une seconde définition du trou, et les
# deux divergeraient. On prend les idées telles qu'elles sortent, et l'on colle
# à chacune la CRITICITÉ DE LA PIÈCE QU'ELLE VISE. Une idée ne vaut pas par la
# gravité de son défaut : elle vaut par ce que la pièce qu'elle débloque tient.
#
# LE NUMÉRO SE LIT SUR LA CLEF DE L'ACTE, qui l'y a déjà mis (`clef/28017`,
# `office/220`, `genre/44001/23000`). C'est laid et c'est juste : cette clef est
# la seule chose que `missions_de` promet de garder stable, et la reconstruire
# en rapprochant des libellés serait inventer un appariement là où il y a une
# adresse.
CHIFFRES = re.compile(r"\d{3,6}")


def idees(pieces, crit, poids, base):
    from plan.expose import missions_de, phrase   # noqa: E402
    out = []
    for aff in sorted({p["affaire"] for p in pieces.values() if p["affaire"]}):
        for m in missions_de(aff, pieces):
            ns = CHIFFRES.findall(m.get("acte") or u"")
            # LA PREMIÈRE EST CELLE QU'ON VISE. « genre/44001/23000 » parle de la
            # colonne de 44001, pas de 23000 qu'elle désigne à tort ; et
            # « retrouver/21020 » vise une pièce qui n'existe pas — score nul,
            # ce qui est la vérité : on ne peut pas chiffrer ce qui manque.
            n = ns[0] if ns else None
            c = crit.get(n) or {}
            score = c.get("perte", 0) + c.get("attendu", 0)
            if not c and n in poids:
                # un état cible n'a pas de perte : il a son poids, et le fait
                # qu'on puisse l'atteindre ou non
                score = poids[n] if not base.get(n) else 0
            out.append({
                "acte": m.get("acte"), "affaire": aff, "nature": m.get("nature", "pas"),
                "texte": phrase(m), "piece": n,
                "genre": (pieces.get(n) or {}).get("genre") if n else None,
                "perte": c.get("perte", 0), "attendu": c.get("attendu", 0),
                "score": score,
            })
    out.sort(key=lambda x: (-x["score"], x["acte"] or u""))
    return out


# ─────────────────────────────────────────── ce qu'un homme NE VOIT PAS
#
# LE ROUTAGE DU PLAN TIENT SUR UN SEUL CHAMP, `tenu_par`, ecrit en tete du
# cahier. Un homme depeche recoit les trous DE SES CAHIERS, et rien d'autre.
# C'est propre, et c'est trop etroit : une action dont il repond par son office
# — c'est ecrit noir sur blanc dans la colonne `🪶 Office` de la ligne — ne lui
# parvient jamais si le cahier appartient a un autre. Personne ne la lui cache :
# simplement, aucun chemin ne la lui porte.
#
# CE SCRIPT NE CHANGE RIEN, IL COMPTE. Avant d'ouvrir la reserve d'un homme aux
# affaires qu'il ne tient pas — ce qui redefinit ce qu'est un cahier —, on
# regarde ce que ca representerait. Trois colonnes, et la troisieme est la
# question : ce qu'il voit, ce qui tombe sur son office ailleurs, et ce qui tire
# sur un moyen qu'il tient sans que son nom soit sur la ligne.
#
# LA JOINTURE ENTRE `tenu_par` ET LE REGISTRE DES OFFICES EST DEVINEE, et elle
# est dite : l'un ecrit des identifiants (`aurore-inchauspe`), l'autre des noms
# avec leurs titres (`Dame Aurore Inchauspe`). On normalise des deux cotes et
# l'on IMPRIME les titulaires qu'on n'a pas su rattacher, plutot que de les
# perdre en silence.
def _id(s):
    t = unicodedata.normalize("NFD", cle_homme(s))
    t = u"".join(c for c in t if unicodedata.category(c) != "Mn")
    return u"-".join(re.sub(u"[^a-z0-9]+", u" ", t.lower()).split())


def rapprocher(ids):
    """UN PRENOM SEUL EST LE MEME HOMME QU'UN PRENOM SUIVI D'UN NOM. Les cahiers
    ecrivent `tenu_par: "jacaerys"`, le registre des offices « Le prince Jacaerys
    Velaryon » : deux clefs, deux hommes, et le prince ressortait a 100 %
    d'aveugle alors qu'il tient DEUX cahiers. C'est la faute la plus couteuse de
    ce tableau, parce qu'elle fabrique exactement le symptome qu'on cherche.

    On replie donc le plus court sur le plus long quand l'un prefixe l'autre, et
    JAMAIS autrement : « nesse » et « nesse-du-marais » sont le meme homme, « rulf
    corne » et « rulf-le-jeune » ne le sont pas. Une inclusion au milieu du mot
    marierait des inconnus."""
    canon = {}
    longs = sorted(ids, key=len, reverse=True)
    for i in ids:
        canon[i] = next((L for L in longs
                         if L == i or L.startswith(i + u"-")), i)
    return canon


def porte_des_hommes(lignes, offices, moyens):
    """Par homme : la criticite des pas dont SON office repond, et celle des pas
    qui tirent sur un moyen qu'il tient. C'est la mesure de la table
    `--acteurs`, et il n'y en a qu'une : la table l'imprime, le JSON la sert,
    l'ecran fait varier ses ronds dessus.

    DEUX FACONS DE PESER SUR LE PLAN, ET IL FAUT LES DEUX. Un homme porte ce
    qu'on lui a confie (son office est ecrit sur l'action) ; il TIENT aussi des
    choses dont d'autres ont besoin (son nom est dans « qui le tient » d'un
    moyen que l'action engage). Le second est invisible aux tableaux de charge —
    et c'est par la qu'on est bloque par quelqu'un qui ne sait meme pas qu'on
    l'attend.

    LA CLEF EST CELLE DE `charge_des_hommes` — un slug replie par
    `rapprocher()` —, et non le nom nu d'autrefois. Un chiffre que l'ecran ne
    sait pas poser sur un visage ne sert a personne, et les deux tableaux du
    meme script ne peuvent pas nommer le meme homme de deux facons.

    Retourne (hommes, sans_office, office_en_clair)."""
    bruts = ({_id(q) for o, (nom, qui) in offices.items() for q in qui}
             | {_id(q) for m, (nom, qui) in moyens.items() for q in qui})
    canon = rapprocher(bruts)
    out, sans, en_clair = {}, [0.0, 0], [0.0, 0]

    def chez(q0):
        i = _id(q0)
        h = out.setdefault(canon.get(i, i),
                           {"nom": u"", "offices": set(), "moyens": set(),
                            "porte": 0.0, "pas": 0, "goulots": 0,
                            "tire": 0.0, "tire_pas": 0})
        # LE PLUS LONG N'EST PAS LE PLUS CLAIR. « Lord Corlys Velaryon —
        # PROPOSE le 27e a neuf heures » est un nom plus une nouvelle ; au
        # classement des hommes, on veut le nom.
        h["nom"] = affiche(cle_homme(q0), q0, h["nom"])
        return h

    for c, pt, n, p in lignes:
        o = p.get("office")
        if o in offices:
            for q0 in (offices[o][1] or [u"— titulaire non écrit —"]):
                h = chez(q0)
                h["porte"] += c
                h["pas"] += 1
                h["goulots"] += 1 if c > 0 else 0
                h["offices"].add(o)
        elif o == u"SANS OFFICE":
            sans[0] += c
            sans[1] += 1
        elif o:
            en_clair[0] += c
            en_clair[1] += 1
        for m in p.get("moyens") or []:
            for q0 in (moyens.get(m) or (u"", []))[1]:
                h = chez(q0)
                h["tire"] += c
                h["tire_pas"] += 1
                h["moyens"].add(m)

    for h in out.values():
        h["offices"] = sorted(h["offices"])
        h["moyens"] = sorted(h["moyens"])
        h["porte"] = round(h["porte"], 3)
        h["tire"] = round(h["tire"], 3)
    return out, sans, en_clair


def charge_des_hommes(pieces, affaires, lignes, attendu, offices, moyens):
    """Par homme : ce qu'il voit, ce qu'il porte sans le voir, ce qu'on lui tire."""
    tenu = {nu(b.get("titre")): (b.get("tenu_par") or u"") for b in affaires}
    score = {n: c + attendu.get(n, 0) for c, pt, n, p in lignes}
    # On rassemble d'abord TOUS les noms des trois sources, puis on les replie :
    # sans ce passage, la meme personne existe une fois par registre.
    bruts = ({_id(q) for o, (nom, qui) in offices.items() for q in qui}
             | {_id(q) for m, (nom, qui) in moyens.items() for q in qui}
             | {_id(v) for v in tenu.values() if v})
    canon = rapprocher(bruts)
    par_off = {}
    for o, (nom, qui) in offices.items():
        for q in qui:
            par_off.setdefault(canon[_id(q)], set()).add(o)
    par_moyen = {}
    for m, (nom, qui) in moyens.items():
        for q in qui:
            par_moyen.setdefault(canon[_id(q)], set()).add(m)

    hommes = {}
    for q in set(list(par_off) + list(par_moyen) + [canon[_id(v)] for v in tenu.values() if v]):
        hommes[q] = {"qui": q, "offices": sorted(par_off.get(q, [])),
                     "moyens": sorted(par_moyen.get(q, [])),
                     "cahiers": sorted({a for a, t in tenu.items()
                                        if t and canon[_id(t)] == q}),
                     "vu": [], "sien_ailleurs": [], "tire": []}

    for c, pt, n, p in lignes:
        s = score.get(n, 0)
        if not s:
            continue
        chez = canon.get(_id(tenu.get(p["affaire"], u"")), u"")
        porteur = None
        for q, os_ in par_off.items():
            if p.get("office") in os_:
                porteur = q
                break
        if chez and chez in hommes:
            hommes[chez]["vu"].append((s, n, p))
        if porteur and porteur in hommes and porteur != chez:
            hommes[porteur]["sien_ailleurs"].append((s, n, p))
        for m in (p.get("moyens") or []):
            for q, ms in par_moyen.items():
                if m in ms and q in hommes and q != chez and q != porteur:
                    hommes[q]["tire"].append((s, n, p))
                    break
    for h in hommes.values():
        for k in ("vu", "sien_ailleurs", "tire"):
            h[k].sort(key=lambda x: (-x[0], x[1]))
    return hommes


def section_charge(hommes, combien, qui=None):
    somme = lambda L: sum(x[0] for x in L)          # noqa: E731
    if not qui:
        titre(u"🪶 CE QU'UN HOMME VOIT, ET CE QU'IL NE VOIT PAS")
        sys.stdout.write(
            u"  « vu » = les cahiers dont il est `tenu_par` — la seule chose qui lui parvienne\n"
            u"  aujourd'hui. « sien ailleurs » = des pas dont SON office répond, dans le cahier\n"
            u"  d'un autre. « on lui tire » = des pas qui engagent un moyen qu'il tient.\n\n")
        sys.stdout.write(u"  %s%s%s%s%s\n" % (
            cale(u"vu", 7), cale(u"sien", 7), cale(u"tiré", 7),
            cale(u"aveugle", 9), u"l'homme"))
        for h in sorted(hommes.values(), key=lambda x: -(somme(x["sien_ailleurs"])
                                                         + somme(x["tire"]))):
            v, s, t = somme(h["vu"]), somme(h["sien_ailleurs"]), somme(h["tire"])
            if not (v or s or t):
                continue
            # LE CHIFFRE QUI DECIDE : la part de ce qui le concerne qu'aucun
            # chemin ne lui porte. Un homme a 100 % d'aveugle est un homme dont
            # le plan attend quelque chose sans avoir aucun moyen de le lui dire.
            aveugle = (100 * (s + t) / (v + s + t)) if (v + s + t) else 0
            sys.stdout.write(u"  %s%s%s%s%s\n" % (
                cale(u"%g" % v, 7), cale(u"%g" % s, 7), cale(u"%g" % t, 7),
                cale(u"%d %%" % aveugle, 9),
                cale(h["qui"] + u"  · " + u" ".join(h["offices"] + h["moyens"]), 56)))
        return

    h = hommes.get(_id(qui)) or next(
        (v for k, v in hommes.items() if k.startswith(_id(qui) + u"-")), None)
    if not h:
        titre(u"🪶 " + qui)
        sys.stdout.write(u"  Personne de ce nom ne tient d'office, de moyen ni de cahier.\n"
                         u"  Connus : " + u" · ".join(sorted(hommes)) + u"\n")
        return
    titre(u"🪶 " + h["qui"].upper() + u" — " + (u" ".join(h["offices"]) or u"sans office")
          + (u" · moyens " + u" ".join(h["moyens"]) if h["moyens"] else u""))
    sys.stdout.write(u"  %d cahier(s) : %s\n"
                     % (len(h["cahiers"]), u" · ".join(h["cahiers"]) or u"aucun"))
    for k, t in ((u"vu", u"📘 CE QU'IL VOIT DÉJÀ — ses cahiers, ce que la dépêche lui porte"),
                 (u"sien_ailleurs", u"🪶 SA CHARGE AILLEURS — son office répond, "
                                    u"le cahier est à un autre"),
                 (u"tire", u"🪝 CE QU'ON LUI TIRE — un moyen qu'il tient, "
                           u"et son nom n'est pas sur la ligne")):
        L = h[k]
        sys.stdout.write(u"\n  %s  (%g sur %d pas)\n" % (t, somme(L), len(L)))
        for s, n, p in L[:combien]:
            sys.stdout.write(u"    %s%s%s%s\n" % (
                cale(u"%g" % s, 6), cale(NOM_GENRE.get(p["genre"], u"") + u" " + n, 10),
                cale(p["nom"], 46), cale(p["affaire"], 32)))
        if len(L) > combien:
            sys.stdout.write(u"    … et %d autres\n" % (len(L) - combien))



def affiche(cle, brut, deja=None):
    """Le nom qu'on montre pour une clef d'homme. Les clefs sentinelles se
    disent en clair — « la reine » n'est pas un nom qu'on a lu quelque part,
    c'est une deduction, et le lecteur doit pouvoir la contester."""
    if cle == u"la reine":
        return u"La reine (« moi » aux registres)"
    if cle.startswith(u"—"):
        return cle
    n = GLOSE.sub(u"", u" ".join(nu(brut).split())).strip()
    return max(deja or u"", n, key=len)
