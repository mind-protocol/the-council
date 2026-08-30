# -*- coding: utf-8 -*-
"""MISSIONS — la coupe par personne : ce qu'un homme porte, dit en
missions (missions_de, phrase), et les sections par homme (--pour, --qui).
"""
import re
import sys

from plan.expose import (nu, sans_emoji, marque, blocs,  # noqa: F401
                         NUM, MO, NOM_GENRE, EST_MO, NERA, etiquette)
from plan.expose import genre_de as C_genre  # noqa: F401
# Les tables de la descente et le motif du « fait » vivent chez le chargeur :
# un seul lecteur du graphe, une seule verite — y compris pour ses constantes.
from plan.expose import ATTENDU as C_ATTENDU, RANG as C_RANG  # noqa: F401
from plan.expose import FINI as C_FINI, premier_mot as C_premier_mot  # noqa: F401
from plan.expose import tete_ornee as C_tete_ornee  # noqa: F401
from plan.expose import numero_de as C_numero_de  # noqa: F401

import jours_relatifs as JR

from plan.etat_du_plan.page import LARGEUR, titre, ligne, cale
from plan.etat_du_plan.echeances import (statut_de, echeance_de, echelle,
                                         amont_de)

# ─────────────────────────────────────────────── la coupe par personne
# MES AFFAIRES — ce qu'un homme voit quand il regarde SON propre cahier.
#
# Ce n'est pas une file de demandes qu'on lui assigne : c'est le bon sens de
# celui qui porte l'affaire. Un homme competent qui ouvre son cahier voit ces
# trous et travaille dessus ; personne n'a a les lui ordonner. Le manuel pose
# « pas de source, pas de pensee » — les trous de son propre cahier sont une
# source de ce genre, au meme titre qu'un registre depouille.
#
# L'ACHEMINEMENT NE S'INVENTE PAS : chaque cahier porte `tenu_par`, et c'est la
# seule clef. Pas d'appariement de noms, pas d'heuristique.
#
# RIEN NE S'ECRIT. Ni ici, ni dans `intentions.json` — le budget du schema donne
# 3 a 5 etapes a une tete du quartier, et le plus charge a quatre-vingts trous.
# On lui donne sa reserve, en tete ce qui debloque le plus, ET IL PREND CE QU'IL
# PEUT PORTER. Ce qu'il laisse reste ; un homme qui laisse vingt trous ouverts
# trois lunes durant est une information sur lui, pas un defaut du script.
#
# LE GABARIT est celui de l'echiquier, et c'est voulu : afin d'atteindre X,
# faire Y aurait effet Z. X remonte le graphe, Y est le verbe, Z mesure ce que
# l'acte debloque — « le seul verrou qui l'en separe » quand c'est vrai, « un
# verrou sur deux » quand ca ne suffit pas.
def etats_bloques(n, pieces):
    """Les etats cibles qu'un verrou bloque."""
    return [v for v in (pieces.get(n) or {}).get("vers", [])
            if (pieces.get(v) or {}).get("genre") == "etat"]


def verrous_de(e, pieces):
    return [n for n, p in pieces.items() if p["genre"] == "verrou" and e in p["vers"]]


def clefs_de(v, pieces):
    return [n for n, p in pieces.items() if p["genre"] == "clef" and v in p["vers"]]


def actions_de(k, pieces):
    return [n for n, p in pieces.items() if p["genre"] == "action" and k in p["vers"]]


def nom_de(n, pieces):
    p = pieces.get(n)
    return (NOM_GENRE.get(p["genre"], u"") + u" " + p["nom"]) if p else n


def adresse(n, pieces):
    """Le signe, LE NUMERO, et le nom. Une piece citee sans son numero oblige
    celui qui lit a la retrouver — et le manuel proscrit le renvoi nu."""
    p = pieces.get(n)
    return (marque(n, pieces) + u" " + nu(p["nom"])) if p else n


def suffisance(v, pieces):
    es = etats_bloques(v, pieces)
    n = len(verrous_de(es[0], pieces)) if es else 0
    return (u"le seul verrou qui l'en sépare" if n <= 1
            else u"un verrou sur %d" % n)


def force(m):
    # UNE RUPTURE PASSE AVANT TOUT. Les six pas disent ce qui manque au BOUT de
    # la chaîne ; une rupture dit qu'elle est cassée AU MILIEU, et le guide est
    # net là-dessus : « si la remontée est impossible, l'action n'a pas de
    # raison stratégique démontrée — elle se supprime ou se requalifie ». Une
    # action sans raison passe donc avant un office sans numéro.
    if m.get("nature") == "rupture":
        return 0
    # PUIS CE QUI EST IMPOSSIBLE PAR CONSTRUCTION. Une inversion de date et un
    # travail deja livre sous une decision qu'on n'a pas prise ne sont pas des
    # trous au bout de la chaine : ce sont des defauts qui garantissent la perte
    # — l'un du calendrier, l'autre du travail. Ils passent avant le verrou sans
    # clef, qui n'a encore rien coute a personne.
    if m.get("nature") == "ordre":
        return 0.5
    t = m.get("precision") or u""
    if t.startswith(u"le seul verrou"):
        return 1
    x = re.match(r"un verrou sur (\d+)", t)
    if x:
        return 1 + int(x.group(1))
    if t.startswith(u"la seule action"):
        return 20
    x = re.match(r"une action sur (\d+)", t)
    if x:
        return 20 + int(x.group(1))
    return 60


def missions_de(nom_affaire, pieces):
    """Les trous d'une affaire, dits dans le gabarit. Memes detecteurs que la
    route /echiquier — quand les deux divergent, `--comparer` le dit."""
    miennes = {n: p for n, p in pieces.items() if p["affaire"] == nom_affaire}
    out = {}
    en_clair = []
    fini_bancal = []

    def pose(acte, but, verbe, piece, effet, vers, precision, nature="pas"):
        if acte in out:
            return
        out[acte] = {"acte": acte, "but": but, "verbe": verbe, "piece": piece,
                     "effet": effet, "vers": vers, "precision": precision,
                     "nature": nature}

    # ── LES RUPTURES D'ABORD ────────────────────────────────────────────────
    # On ne rapproche JAMAIS au plus proche : trois actions désignent la clef
    # 21020, qui n'est dans aucun cahier. Renumérotage ? clef supprimée ? doigt
    # glissé depuis 21021 ? Écrire la réponse à leur place, ce serait écrire une
    # FAUSSE raison stratégique — pire que pas de raison, parce qu'elle ne se
    # voit plus. On détecte, on ne corrige pas.
    GENRE_MOT = {"etat": u"l'état cible", "verrou": u"le verrou",
                 "clef": u"la clef", "action": u"l'action"}
    registre_seul = []
    for n, p in sorted(miennes.items()):
        attendu = C_ATTENDU.get(p["genre"])
        for v in p["vers"]:
            q = pieces.get(v)
            if q is None:
                pose(u"retrouver/" + v, None, u"retrouver %s %s qu'elle désigne"
                     % (GENRE_MOT.get(attendu, u"la pièce"), v), nom_de(n, pieces),
                     u"lui rendrait sa remontée jusqu'à l'affaire", None,
                     u"aujourd'hui elle ne remonte à rien", nature="rupture")
            elif not q.get("cahier"):
                registre_seul.append(n)
            elif C_RANG.get(q["genre"], 9) >= C_RANG.get(p["genre"], 0) \
                    and not (p["genre"] == "etat" and q["genre"] == "etat"):
                pose(u"genre/" + n + u"/" + v, None,
                     u"remettre le bon numéro à la place de %s %s"
                     % (NOM_GENRE.get(q["genre"], u""), v), nom_de(n, pieces),
                     u"rendrait la colonne lisible", None,
                     u"cette colonne attend %s, elle porte %s"
                     % (GENRE_MOT.get(attendu, u"autre chose"),
                        GENRE_MOT.get(q["genre"], u"autre chose")), nature="rupture")
        if p["genre"] == "action" and not p["vers"]:
            pose(u"orpheline/" + n, None, u"lui donner la clef qu'elle réalise",
                 nom_de(n, pieces), u"lui donnerait une raison d'être", None,
                 u"elle ne désigne rien, elle n'a jamais rien remonté",
                 nature="rupture")

    # ── LE TRAVAIL FAIT SOUS UNE DECISION JAMAIS PRISE ──────────────────────
    # L'ACTE EST LE MEME QUE « retenir ou ecarter », et c'est pour cela qu'il se
    # pose ICI, avant la boucle des verrous : `pose` garde le premier venu, et
    # la doctrine dedouble par l'ACTE et non par le detecteur qui le trouve.
    # Ce qui change n'est pas la decision a prendre, c'est ce qu'elle coute
    # desormais — quelqu'un a deja travaille dessous. On rend la cellule de
    # decision MOT POUR MOT : quand elle dit « prise — tenue depuis le… », le
    # trou n'est pas une decision qui manque mais un mot que le registre ne
    # connait pas, et l'homme le voit sans qu'on ait a le deviner pour lui.
    faites_sous = {}
    for n, p in pieces.items():
        if p["genre"] != "action":
            continue
        if C_premier_mot(p["etat"]) not in (u"faite", u"close"):
            continue
        for k in p["vers"]:
            q = pieces.get(k)
            if q and q["genre"] == "clef" \
                    and u"retenue" not in (q.get("etat") or u"").lower():
                faites_sous.setdefault(k, []).append(n)
    for k, faites in sorted(faites_sous.items()):
        if k not in miennes:
            continue
        dit = re.sub(r"\s+", u" ", sans_emoji(nu(pieces[k].get("etat") or u""))).strip()
        out[u"retenir/" + k] = {
            "acte": u"retenir/" + k, "but": None, "nature": "ordre",
            "texte": u"🗝️ %s %s faite%s sous %s, qui n'est pas tranchée — sa "
                     u"décision dit « %s ». Le travail est livré sous une décision "
                     u"qu'on n'a pas prise : la trancher aujourd'hui ne coûte rien, "
                     u"l'écarter demain coûte le travail."
                     % (u" et ".join(adresse(f, pieces) for f in sorted(faites)),
                        u"sont" if len(faites) > 1 else u"est",
                        u"s" if len(faites) > 1 else u"",
                        adresse(k, pieces),
                        (dit[:70] + (u"…" if len(dit) > 70 else u"")) or u"(rien)")}

    # ── LES INVERSIONS DE DATE ──────────────────────────────────────────────
    # Le rapport lit les J−N d'un cote et les chaines de l'autre, et les deux
    # sections ne se croisaient jamais. Une action due J−38 qui attend une piece
    # due J−31 n'est pas en retard : elle est IMPOSSIBLE telle qu'ecrite, et rien
    # ne le disait. Plancher assume : 426 actions sur 655 portent un J−N, et il
    # en faut un aux DEUX bouts pour que la regle puisse se prononcer.
    rel = echelle()
    for n, p in sorted(miennes.items()):
        f = rel.get(n)
        if not f:
            continue
        for a in sorted(set(p["dep"]) | set(amont_de(p["etat"]))):
            g = rel.get(a)
            if not g or a not in pieces:
                continue
            ecart = g[0]["n"] - f[0]["n"]
            if ecart <= 0:
                continue
            pose(u"ordre/" + n + u"/" + a, None, None, None, None, None, None,
                 nature="ordre")
            out[u"ordre/" + n + u"/" + a]["texte"] = (
                u"📅 %s est dû %s et attend %s, dû %s — %d jour%s après lui. Dans "
                u"cet ordre la chaîne ne peut pas se tenir : redater l'un des deux, "
                u"ou couper la dépendance."
                % (adresse(n, pieces), JR.canonique(f[0]),
                   adresse(a, pieces), JR.canonique(g[0]),
                   ecart, u"s" if ecart > 1 else u""))

    for n, p in sorted(miennes.items()):
        if p["genre"] == "verrou":
            es = etats_bloques(n, pieces)
            but = nom_de(es[0], pieces) if es else None
            ks = clefs_de(n, pieces)
            if not ks:
                pose(u"clef/" + n, but, u"écrire une clef contre", nom_de(n, pieces),
                     u"donnerait de quoi le lever", None, suffisance(n, pieces))
            else:
                # une clef qui n'est pas retenue : rien ne part tant qu'on n'a
                # pas tranche. La colonne s'appelle « Décision » dans les
                # cahiers et « Retenue » aux registres : on lit les deux.
                for k in ks:
                    e = (pieces[k].get("etat") or u"").lower()
                    if u"retenue" in e:
                        continue
                    pose(u"retenir/" + k, but, u"retenir ou écarter", nom_de(k, pieces),
                         u"lèverait", nom_de(n, pieces), suffisance(n, pieces))
        elif p["genre"] == "clef":
            e = (p.get("etat") or u"").lower()
            if u"retenue" in e and not actions_de(n, pieces):
                vs = [v for v in p["vers"] if (pieces.get(v) or {}).get("genre") == "verrou"]
                es = etats_bloques(vs[0], pieces) if vs else []
                pose(u"action/" + n, nom_de(es[0], pieces) if es else None,
                     u"écrire l'action de", nom_de(n, pieces),
                     u"la mettrait en marche", None,
                     u"elle est retenue et rien ne la fait")
        elif p["genre"] == "action":
            # DEUX MANQUES, DEUX ACTES. « Personne ne la porte » se répare d'une
            # parole — c'est la reine qui désigne. « Quelqu'un la porte, mais son
            # office n'est pas écrit par son numéro » se répare d'un trait de
            # plume au registre, et ce n'est pas la même chose du tout. On les
            # confondait, et l'on demandait de désigner un homme déjà nommé.
            if C_FINI.match(C_premier_mot(p["etat"]) or u"") \
                    and (C_premier_mot(p["etat"]) != u"faite"
                         or C_tete_ornee(p["etat"])):
                fini_bancal.append(n)
            if p["office"] == u"EN CLAIR":
                en_clair.append(n)
                continue
            if p["office"] and p["office"] != u"SANS OFFICE":
                continue
            ks = [v for v in p["vers"] if (pieces.get(v) or {}).get("genre") == "clef"]
            k = ks[0] if ks else None
            vs = [v for v in (pieces.get(k) or {}).get("vers", [])
                  if (pieces.get(v) or {}).get("genre") == "verrou"] if k else []
            es = etats_bloques(vs[0], pieces) if vs else []
            soeurs = len(actions_de(k, pieces)) if k else 0
            pose(u"office/" + n, nom_de(es[0], pieces) if es else None,
                 u"désigner qui répond de", nom_de(n, pieces),
                 u"porterait" if k else u"lui donnerait une main",
                 nom_de(k, pieces) if k else None,
                 (u"elle ne remonte à aucune clef" if not k else
                  u"la seule action écrite sous elle" if soeurs <= 1 else
                  u"une action sur %d sous elle" % soeurs))
        elif p["genre"] == "etat":
            if not verrous_de(n, pieces):
                pose(u"empeche/" + n, None, u"trouver ce qui empêche", nom_de(n, pieces),
                     u"ouvrirait la première prise sur lui", None,
                     u"aucun verrou n'est écrit contre lui")
    # UN FAIT VRAI DE PRESQUE TOUT LE MONDE VA AU CHAPEAU, JAMAIS SUR LES
    # PIÈCES. « Son office n'est pas écrit par son numéro » est vrai de 448
    # actions sur 617 : posé ligne à ligne, il noierait tout le reste et l'on
    # aurait remplacé un doublon par un mur. Il se dit donc UNE FOIS par cahier,
    # avec son compte — c'est une discipline de registre à reprendre d'un coup,
    # pas quatre cent quarante-huit décisions à prendre une par une.
    # Le renvoi qui ne tient qu'au registre est vrai de 81 pièces : c'est UNE
    # question — deux plans, ou un seul ? — et non quatre-vingt-une décisions.
    if registre_seul:
        n_rs = len(set(registre_seul))
        out[u"registre/" + nom_affaire] = {
            "acte": u"registre/" + nom_affaire, "but": None, "nature": "rupture",
            "texte": u"🪢 %d pièce%s de ce cahier désigne%s ce qu'aucun cahier ne porte "
                     u"— seul un registre par type le connaît. Ici la chaîne tient ; "
                     u"à l'écran, qui ne lit que les cahiers, elle pend. À trancher "
                     u"une fois pour tout le plan : deux plans, ou un seul."
                     % (n_rs, u"s" if n_rs > 1 else u"", u"nt" if n_rs > 1 else u"")}
    # « fait » écrit de trois façons : une tenue à reprendre d'un coup.
    if fini_bancal:
        out[u"fait/" + nom_affaire] = {
            "acte": u"fait/" + nom_affaire, "but": None, "nature": "pas",
            "texte": u"🏷️ %d action%s terminée%s de ce cahier ne s'écrivent pas de la "
                     u"même façon (« fait », « ✅ faite », « faite »). Les mettre "
                     u"toutes à « faite » rendrait comptable ce qui est déjà fait."
                     % (len(fini_bancal), u"s" if len(fini_bancal) > 1 else u"",
                        u"s" if len(fini_bancal) > 1 else u"")}
    if en_clair:
        out[u"numeros/" + nom_affaire] = {
            "acte": u"numeros/" + nom_affaire, "but": None,
            "verbe": u"écrire au registre le numéro de l'office de",
            "piece": u"⚔️ %d action(s) de ce cahier" % len(en_clair),
            "effet": u"rendrait leur porteur lisible à la machine", "vers": None,
            "precision": u"quelqu'un les porte, aucun numéro ne le dit"}
    return sorted(out.values(), key=lambda m: (force(m), m["acte"]))


def phrase(m):
    # Un fait systémique — « quatre-vingt-un renvois ne tiennent qu'au
    # registre » — n'est ni un pas ni une rupture d'une pièce : il porte sa
    # phrase toute faite, et l'y forcer la rendrait illisible.
    if m.get("texte"):
        return m["texte"]
    # DEUX FORMES, PARCE QU'IL Y A DEUX NATURES. « Afin d'atteindre X » suppose
    # qu'on connaisse l'état cible servi — or c'est EXACTEMENT ce qui est perdu
    # quand la référence pend : X est introuvable par construction. Forcer une
    # rupture dans le gabarit des pas la ferait passer pour un oubli d'écriture,
    # quand c'est une action sans raison stratégique démontrée.
    if m.get("nature") == "rupture":
        t = u"Afin de rendre sa raison à " + m["piece"] + u", " + m["verbe"]
        if m.get("vers"):
            t += u" " + m["vers"]
        if m.get("effet"):
            t += u" " + m["effet"]
        if m.get("precision"):
            t += u" — " + m["precision"]
        return t + u"."
    t = u""
    if m["but"] and m["but"] != m["piece"]:
        t += u"Afin d'atteindre " + m["but"] + u", "
    t += m["verbe"] + u" " + m["piece"]
    if m["effet"]:
        t += u" " + m["effet"] + ((u" " + m["vers"]) if m["vers"] else u"")
    if m["precision"]:
        t += u" — " + m["precision"]
    return t + u"."


def section_pour(qui, pieces, affaires, plafond):
    siennes = [b for b in affaires if (b.get("tenu_par") or u"") == qui]
    titre(u"🕳️ MES AFFAIRES — " + qui + u", %d cahier(s)" % len(siennes))
    if not siennes:
        ligne(u"— aucun cahier ne porte `tenu_par: \"" + qui + u"\"`.")
        return []
    tout = []
    for b in siennes:
        nom = nu(b["titre"])
        ms = missions_de(nom, pieces)
        tout += [(m, nom) for m in ms]
        ligne(cale(nom, 52), u"%3d chose(s) à y voir" % len(ms))
    # UNE SEULE FOIS PAR HOMME pour ce qui n'est pas de son ressort : « deux
    # plans, ou un seul » est une décision de maison, pas une par cahier. Trois
    # fois la même ligne en tête de réserve, c'est le mur qu'on proscrit.
    rs = [x for x in tout if x[0]["acte"].startswith(u"registre/")]
    if len(rs) > 1:
        tout = [x for x in tout if not x[0]["acte"].startswith(u"registre/")]
        n_c = sum(int(re.search(u"[0-9]+", x[0]["texte"]).group(0)) for x in rs)
        tout.append(({"acte": u"registre/tous", "nature": "rupture",
                      "texte": u"🪢 %d pièces, réparties sur %d de vos cahiers, désignent "
                               u"ce qu'aucun cahier ne porte — seuls les registres par "
                               u"type les connaissent. À trancher une fois pour tout le "
                               u"plan : deux plans, ou un seul." % (n_c, len(rs))},
                     u"vos cahiers"))
    tout.sort(key=lambda x: (force(x[0]), x[0]["acte"]))
    sys.stdout.write(u"\n")
    ligne(u"Ce que le plan montre, ce qui débloque le plus en tête. "
          u"Prenez ce que vous pouvez porter.")
    sys.stdout.write(u"\n")
    for i, (m, nom) in enumerate(tout[:plafond], 1):
        sys.stdout.write(u"  %2d. %s\n" % (i, phrase(m)))
        sys.stdout.write(u"      (%s)\n" % nom)
    if len(tout) > plafond:
        sys.stdout.write(u"\n")
        ligne(u"… et %d autre(s) : le reste attendra, et c'est très bien."
              % (len(tout) - plafond))
    return tout


def section_emblemes(livres):
    """Deux cahiers sous le même emblème ne se distinguent plus dans la bascule
    de l'échiquier, où l'affaire n'est QUE son signe. `tick.py --verifier` le
    signale déjà ; on le redit ici parce que c'est ici qu'on regarde le plan."""
    # TOUS les cahiers, pas seulement ceux qu'on analyse : les quatre qui
    # partagent 🗂️ sont précisément ceux qui n'ont pas encore d'ouverture, donc
    # ceux qu'aucune autre section ne regarde.
    par = {}
    for b in livres:
        if not str(b.get("id") or u"").startswith("affaire-"):
            continue
        e = (b.get("embleme") or u"").strip()
        if e:
            par.setdefault(e, []).append(nu(b["titre"]))
    doubles = {e: v for e, v in par.items() if len(v) > 1}
    if not doubles:
        return
    titre(u"🎭 EMBLÈMES EN DOUBLON — deux affaires sous le même signe")
    for e, v in sorted(doubles.items(), key=lambda x: -len(x[1])):
        ligne(cale(e + u"  ×%d" % len(v), 12), u" · ".join(v)[:LARGEUR - 16])


def section_qui(pieces, affaires):
    """Qui tient quoi, et combien de trous chacun porte."""
    titre(u"🕳️ LES TROUS PAR HOMME — la clef de routage est `tenu_par`")
    par = {}
    for b in affaires:
        qui = b.get("tenu_par") or u"(sur personne)"
        ms = missions_de(nu(b["titre"]), pieces)
        d = par.setdefault(qui, {"cahiers": 0, "trous": 0})
        d["cahiers"] += 1
        d["trous"] += len(ms)
    for qui, d in sorted(par.items(), key=lambda x: -x[1]["trous"]):
        ligne(cale(qui, 24), u"%3d trou(s)" % d["trous"],
              u"   dans %d cahier(s)" % d["cahiers"])
    sys.stdout.write(u"\n")
    ligne(u"%d homme(s) · %d trou(s) en tout. Personne n'a à les leur ordonner : "
          u"ce sont leurs affaires." % (len(par), sum(d["trous"] for d in par.values())))
    return par

