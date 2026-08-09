# -*- coding: utf-8 -*-
# L'etat du plan, toutes affaires confondues — une page, au conseil du matin.
#
# POURQUOI. `couverture.py` derive deja tout ce qu'il faut : ce qui pend, ce
# qu'on engage, les trous. Mais il l'ecrit AFFAIRE PAR AFFAIRE, en tete de
# chaque cahier. Personne ne peut donc repondre a « qu'est-ce qui est du cette
# semaine » ni a « qui d'autre tire sur les voiles du Gosier » sans ouvrir
# trente-deux cahiers l'un apres l'autre — et le mestre qui relit le registre au
# conseil n'ouvre pas trente-deux cahiers.
#
# Deuxieme manque, plus grave : le plan est un graphe CLOS. Il ne sait pas quel
# jour on est. Une action « avant le 30e » est ecrite pareil le 20e et le 2e de
# la lune suivante. Ce script croise donc les registres avec `monde.date`, et
# c'est la seule chose qu'il apporte que les cahiers n'ont pas.
#
# IL NE DERIVE RIEN DE NEUF ET N'ECRIT NULLE PART. Il importe le chargeur de
# `couverture.py` — un seul lecteur du graphe, une seule verite — agrege, et
# imprime. Si un chiffre d'ici contredit un cahier, c'est le cahier qui est
# vieux : relancer `python scripts/couverture.py`.
#
# CE QU'IL DEVINE, ET QU'IL FAUT SAVOIR. L'echeance d'une action n'a pas de
# colonne : elle est noyee dans le texte libre de « Ou ca en est », qui porte a
# la fois un statut, une date et une dependance. Ce script les separe au motif,
# et DIT toujours combien de cellules il n'a pas su lire — il ne devine jamais
# en silence. Le vrai remede est une colonne `Jour du`, que le decoupage reclame
# deja (docs/decoupage.md, section 7) et que personne n'a creee.
#
# Usage :
#     python scripts/etat_du_plan.py                 le rapport entier
#     python scripts/etat_du_plan.py --du            ce qui est du, seulement
#     python scripts/etat_du_plan.py --affaire "..." une affaire
#     python scripts/etat_du_plan.py --office O03    ce qui tombe sur un office
import io
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from couverture import (charger, nu, sans_emoji, marque, blocs,  # noqa: E402
                        NUM, MO, NOM_GENRE)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LARGEUR = 96


# ─────────────────────────────────────────────── le jour, et les echeances
def aujourdhui():
    m = json.load(io.open(os.path.join(RACINE, "etat", "monde.json"), encoding="utf-8"))
    return m.get("date") or {}


def rang(annee, lune, jour):
    """Un numero de jour, pour comparer. Une lune vaut trente jours, douze l'an :
    approximation assumee — seul l'ecart entre deux dates nous interesse, et
    toutes les echeances du plan tiennent dans deux lunes."""
    return ((annee * 12) + lune) * 30 + jour


# « avant le 4e de la 4e », « le 4e jour de la 4e lune » : jour ET lune. Le mot
# entre les deux nombres est libre — « 4e jour de la 4e » s'ecrit aussi souvent
# que « 4e de la 4e », et l'oublier faisait lire le second nombre comme la lune
# courante : une echeance a venir devenait vingt-deux jours de retard.
DATE_LUNE = re.compile(r"(?:avant\s+)?le\s+(\d{1,2})e(?:\s+\w+)?\s+de\s+la\s+(\d{1,2})e", re.I)
# « avant le 30e », « avant le 28e au soir » : jour seul, dans la lune courante.
DATE_JOUR = re.compile(r"(?:avant|le)\s+le?\s*(\d{1,2})e", re.I)
DEPEND = re.compile(u"apr[eè]s|d[eé]pend\\s+de|voir", re.I)

STATUTS = [(u"tenu", u"tenu"), (u"bloqu", u"bloqué"), (u"en cours", u"en cours"),
           (u"retenue", u"retenue"), (u"à étudier|a etudier", u"à étudier"),
           (u"à faire|a faire", u"à faire")]


def statut_de(texte):
    t = sans_emoji(texte or u"").lower()
    for motif, nom in STATUTS:
        if re.search(motif, t):
            return nom
    return u"—" if not t else u"?"


def echeance_de(texte, date):
    """(rang, libelle) si la cellule porte une date lisible, sinon None."""
    t = nu(texte or u"")
    m = DATE_LUNE.search(t)
    if m:
        j, l = int(m.group(1)), int(m.group(2))
        return rang(date.get("annee", 0), l, j), u"%de jour de la %de lune" % (j, l)
    m = DATE_JOUR.search(t)
    if m:
        j = int(m.group(1))
        l = date.get("lune", 0)
        return rang(date.get("annee", 0), l, j), u"%de jour de la %de lune" % (j, l)
    return None


def amont_de(texte):
    """Les pieces qu'une cellule dit attendre. On ne lit les numeros que si un
    mot de dependance est present : sinon « 220 » serait un jour, un compte
    d'hommes, ou n'importe quoi."""
    if not DEPEND.search(nu(texte or u"")):
        return []
    return sorted(set(NUM.findall(nu(texte))))


# ─────────────────────────────────────────────── les registres annexes
def colonne(livre, motif):
    for i, c in enumerate(livre.get("colonnes") or []):
        if re.search(motif, sans_emoji(c), re.I):
            return i
    return None


def registre(livres, ident, motif_cle):
    """{numero: valeur} pour une colonne d'un registre a plat (moyens, offices)."""
    b = next((x for x in livres if x.get("id") == ident), None)
    if not b:
        return {}
    i = colonne(b, motif_cle)
    if i is None:
        return {}
    out = {}
    for l in b.get("lignes") or []:
        c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
        if len(c) > max(1, i):
            m = MO.search(c[0])
            if m:
                out[m.group(1)] = c[i]
    return out


# ─────────────────────────────────────────────── mise en page
def titre(t):
    sys.stdout.write(u"\n" + t + u"\n" + u"─" * LARGEUR + u"\n")


def ligne(*cols):
    sys.stdout.write(u"  " + u"".join(cols) + u"\n")


def cale(t, n):
    t = nu(t)
    return (t[:n - 1] + u"…") if len(t) > n else t.ljust(n)


# ─────────────────────────────────────────────── les sections
def section_jour(date, pieces, affaires):
    j = u"%de jour de la %de lune, an %d" % (date.get("jour", 0), date.get("lune", 0),
                                             date.get("annee", 0))
    mn = date.get("minute", 0)
    titre(u"📅 LE JOUR — " + j + u", %02dh%02d" % (mn // 60, mn % 60))
    g = {}
    for p in pieces.values():
        g[p["genre"]] = g.get(p["genre"], 0) + 1
    ligne(u"%d affaires · " % len(affaires),
          u" · ".join(u"%s %d" % (NOM_GENRE.get(k, k), v) for k, v in sorted(g.items())))


def section_du(pieces, date, filtre_aff=None, filtre_off=None):
    titre(u"⏳ CE QUI EST DÛ — les échéances datées, du plus urgent au plus lointain")
    ici = rang(date.get("annee", 0), date.get("lune", 0), date.get("jour", 0))

    datees, relatives, muettes = [], 0, 0
    for n, p in pieces.items():
        if p["genre"] != "action":
            continue
        if filtre_aff and filtre_aff not in sans_emoji(p["affaire"]).lower():
            continue
        if filtre_off and p["office"] != filtre_off:
            continue
        e = echeance_de(p.get("jour") or p["etat"], date)
        if e:
            datees.append((e[0], n, p, e[1]))
        elif amont_de(p["etat"]):
            relatives += 1
        else:
            muettes += 1

    if not datees:
        ligne(u"— aucune action ne porte de date lisible.")
    for r, n, p, lib in sorted(datees):
        ecart = r - ici
        if ecart < 0:
            marq = u"‼ EN RETARD de %d j" % -ecart
        elif ecart == 0:
            marq = u"▶ AUJOURD'HUI     "
        else:
            marq = u"  dans %2d jours    " % ecart
        ligne(marq, u"  ", cale(marque(n, pieces), 12), cale(p["nom"], 40),
              cale(p["affaire"], 24), statut_de(p["etat"]))

    sys.stdout.write(u"\n")
    ligne(u"%d action(s) datées · %d attendent une autre pièce (voir ci-dessous) · "
          u"%d sans date ni amont" % (len(datees), relatives, muettes))
    if muettes:
        ligne(u"→ ces %d-là ne se synchronisent sur rien. C'est le trou que la colonne "
              u"« Jour dû » comblerait." % muettes)


def section_chaines(pieces, date, filtre_aff=None, tout=False):
    """Les dependances viennent de DEUX endroits, et il faut les deux : la
    colonne « Depend de » des cahiers, qui est propre, et les « apres NNN »
    enfouis dans la cellule d'etat, qui ne sont dans aucun graphe."""
    titre(u"⛓️ CE QUI ATTEND — la colonne « Dépend de », plus les « après NNN » du texte libre")
    lignes = []
    for n, p in sorted(pieces.items()):
        if filtre_aff and filtre_aff not in sans_emoji(p["affaire"]).lower():
            continue
        libre = amont_de(p["etat"])
        for a in sorted(set(p["dep"]) | set(libre)):
            q = pieces.get(a)
            etat_amont = statut_de(q["etat"]) if q else u"⚠ INTROUVABLE"
            # Ce qui merite d'etre montre : l'amont qui n'existe pas, et l'aval
            # engage (date, ou deja commence) dont l'amont ne tient pas encore.
            engage = bool(echeance_de(p.get("jour") or p["etat"], date)) or statut_de(p["etat"]) == u"en cours"
            grave = (q is None) or (engage and etat_amont != u"tenu")
            lignes.append((grave, etat_amont, n, p, a, q, a in libre))
    montrees = [l for l in lignes if l[0] or tout]
    if not montrees:
        ligne(u"— rien d'engagé n'attend une pièce qui ne tient pas.")
    for grave, etat_amont, n, p, a, q, du_texte in sorted(
            montrees, key=lambda x: (q is not None, x[2])):
        pret = u"⚠" if q is None else u"✗"
        ligne(pret, u" ", cale(marque(n, pieces), 12), cale(p["nom"], 32),
              u"attend ", cale(marque(a, pieces), 12),
              cale(q["nom"] if q else u"(aucune pièce de ce numéro)", 22),
              u"[" + etat_amont + u"]", u" ⟵texte" if du_texte and q else u"")
    sys.stdout.write(u"\n")
    orphelines = sorted({l[2] for l in lignes if l[5] is None})
    ligne(u"%d dépendance(s) au total · %d montrée(s) ici · %d renvoi(s) vers un numéro "
          u"inexistant" % (len(lignes), len(montrees), len(orphelines)))
    if orphelines:
        ligne(u"‼ pièces qui renvoient dans le vide : " + u" · ".join(orphelines))
    if not tout and len(lignes) > len(montrees):
        ligne(u"(--tout pour voir les %d chaînes dont l'aval n'est pas encore engagé)"
              % (len(lignes) - len(montrees)))


def section_arrache(pieces, inventaire, etats_moyens, filtre_aff=None):
    titre(u"🔨 CE QU'ON S'ARRACHE — moyens et offices tirés par plus d'une affaire")
    par_piece = {}
    for n, p in pieces.items():
        for m in p["moyens"] + ([p["office"]] if MO.match(p["office"] or u"") else []):
            par_piece.setdefault(m, {}).setdefault(p["affaire"] or u"(sans affaire)", []).append(n)
    tires = {m: a for m, a in par_piece.items() if len(a) > 1}
    if filtre_aff:
        tires = {m: a for m, a in tires.items()
                 if any(filtre_aff in sans_emoji(x).lower() for x in a)}
    if not tires:
        ligne(u"— aucun moyen n'est tiré par deux affaires.")
    for m, a in sorted(tires.items(), key=lambda x: -len(x[1])):
        total = sum(len(v) for v in a.values())
        ligne(cale(m + u" " + inventaire.get(m, u"—"), 38),
              u"%d affaires, %d actions" % (len(a), total))
        ligne(u"   ", cale(u"", 34), u" · ".join(sorted(a)))
        e = etats_moyens.get(m)
        if e:
            ligne(u"   ", cale(u"", 34), u"état au registre : " + e)


def section_charge(pieces, offices, titulaires, filtre_aff=None):
    titre(u"🪶 LA CHARGE — ce qui tombe sur chaque office")
    par_off = {}
    for n, p in pieces.items():
        if p["genre"] != "action":
            continue
        if filtre_aff and filtre_aff not in sans_emoji(p["affaire"]).lower():
            continue
        par_off.setdefault(p["office"] or u"SANS OFFICE", []).append(p)
    orphelines = par_off.pop(u"SANS OFFICE", [])
    for o, ps in sorted(par_off.items(), key=lambda x: -len(x[1])):
        st = {}
        for p in ps:
            s = statut_de(p["etat"])
            st[s] = st.get(s, 0) + 1
        ligne(cale(o + u" " + offices.get(o, u""), 42), u" %3d actions   " % len(ps),
              u" · ".join(u"%s %d" % (k, v) for k, v in sorted(st.items())))
        t = titulaires.get(o)
        if t:
            ligne(u"   ", cale(u"", 39), u"titulaire : " + t)
    if orphelines:
        total = sum(len(v) for v in par_off.values()) + len(orphelines)
        sys.stdout.write(u"\n")
        ligne(u"‼ %d actions sur %d ne nomment AUCUN office par son numéro — soit %d%% du plan."
              % (len(orphelines), total, (100 * len(orphelines)) // max(1, total)))
        ligne(u"  Elles nomment un homme en toutes lettres, ou personne. Pour la machine, "
              u"nul ne les porte.")


def section_muettes(pieces, affaires):
    titre(u"🏰 LES AFFAIRES MUETTES — un cahier ouvert, pas une action écrite")
    par_aff = {}
    for p in pieces.values():
        if p["genre"] == "action":
            par_aff[p["affaire"]] = par_aff.get(p["affaire"], 0) + 1
    muettes = [nu(b["titre"]) for b in affaires if not par_aff.get(nu(b["titre"]))]
    for m in sorted(muettes):
        ligne(u"— ", m)
    sys.stdout.write(u"\n")
    ligne(u"%d affaire(s) sur %d ne portent aucune action : elles n'avanceront pas d'un jour."
          % (len(muettes), len(affaires)))
    hors = sorted({p["affaire"] for p in pieces.values()
                   if p["affaire"] and p["affaire"] not in
                   {nu(b["titre"]) for b in affaires}})
    if hors:
        ligne(u"Et %d nom(s) d'affaire cités par des pièces sans cahier ouvert : %s"
              % (len(hors), u" · ".join(hors)))


def section_trous(pieces, inventaire, affaires, filtre_aff=None):
    retenues = [b for b in affaires
                if not filtre_aff or filtre_aff in sans_emoji(nu(b["titre"])).lower()]
    titre(u"🕳️ LES TROUS — les six défauts de couverture, sur %d affaire(s)" % len(retenues))
    total = {}
    for b in retenues:
        nom = nu(b["titre"])
        _, _, trous, _, _ = blocs(nom, pieces, inventaire)
        for defaut, numeros in trous:
            total.setdefault(defaut, []).append((nom, numeros))
    if not total:
        ligne(u"— la chaîne tient de bout en bout, partout.")
    for defaut, cas in sorted(total.items(), key=lambda x: -len(x[1])):
        n = sum(len(c[1].split(u" · ")) for c in cas)
        ligne(defaut)
        ligne(u"   ", u"%d pièce(s) dans %d affaire(s) : " % (n, len(cas)),
              u" · ".join(sorted(c[0] for c in cas))[:LARGEUR - 20])


AIDE = u"""etat_du_plan.py — l'état du plan, toutes affaires confondues.

    python scripts/etat_du_plan.py                 le rapport entier
    python scripts/etat_du_plan.py --du            ce qui est dû, et les chaînes
    python scripts/etat_du_plan.py --tout          toutes les chaînes, même dormantes
    python scripts/etat_du_plan.py --affaire "port-real"
    python scripts/etat_du_plan.py --office O03

Lecture seule : rien n'est écrit. Les dérivations viennent du chargeur de
couverture.py ; si un cahier dit autre chose, relancer couverture.py.
"""


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--aide" in args or "-h" in args or "--help" in args:
        sys.stdout.write(AIDE)
        raise SystemExit(0)

    filtre_aff = None
    if "--affaire" in args:
        filtre_aff = sans_emoji(args[args.index("--affaire") + 1]).lower()
    filtre_off = args[args.index("--office") + 1] if "--office" in args else None
    seul_du = "--du" in args

    livres, pieces, inventaire, affaires = charger()
    date = aujourdhui()
    offices = registre(livres, "plan-offices", u"l'office|loffice")
    titulaires = registre(livres, "plan-offices", u"titulaire")
    etats_moyens = registre(livres, "plan-moyens", u"^état$|^etat$")

    section_jour(date, pieces, affaires)
    section_du(pieces, date, filtre_aff, filtre_off)
    section_chaines(pieces, date, filtre_aff, "--tout" in args)
    if not seul_du:
        section_arrache(pieces, inventaire, etats_moyens, filtre_aff)
        section_charge(pieces, offices, titulaires, filtre_aff)
        if not filtre_aff and not filtre_off:
            section_muettes(pieces, affaires)
        section_trous(pieces, inventaire, affaires, filtre_aff)
    sys.stdout.write(u"\n")
