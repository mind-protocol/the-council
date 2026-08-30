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
# DEUX ECHELLES, ET IL A LONGTEMPS N'EN LIRE QU'UNE. Le plan ne se date pas en
# jours de lune : il se date A REBOURS du jour d'entree, qui n'est pas arrete.
# Pres de cinq cents actions portent un J-N parfaitement ecrit — et ce script
# ne lisait que l'absolu, donc il annoncait « 588 sans date ni amont sur 609 »
# quand il y en a 106. Il lit desormais les deux echelles (`jours_relatifs.py`).
# Faute de jour d'entree dans l'etat, il compte et trie les J-N ENTRE EUX, et
# dit en tete sous quelle hypothese — ou sans aucune — il travaille.
#
# CE QUI A ETE AJOUTE LE 2e DE LA 4e, ET POURQUOI CA PASSE PAR `missions_de`.
# Trois choses manquaient, et aucune n'etait une vue de plus : c'etaient des
# DETECTEURS. Un rapport plus complet ne corrige pas un plan — ce qui le corrige
# est ce qui tombe dans la reserve de l'homme qui tient le cahier. Les deux
# premieres sortent donc par `missions_de`, dans le gabarit des pas, et se
# rangent juste apres les ruptures parce qu'elles ne disent pas ce qui manque au
# bout de la chaine : elles disent ce qui est deja perdu.
#   * L'INVERSION DE DATE. On lisait les J−N d'un cote et les chaines de
#     l'autre, sans jamais les croiser. Une action due J−17 qui attend une piece
#     due J−14 n'est pas en retard, elle est impossible telle qu'ecrite.
#   * LE TRAVAIL FAIT SOUS UNE DECISION JAMAIS PRISE. Le detecteur « retenir ou
#     ecarter » existait deja ; il ne regardait pas si quelqu'un avait DEJA
#     travaille dessous. Meme acte, prix tout autre.
#   * LA GRILLE (`--grille`). Toutes les autres sections coupent par piece ;
#     aucune ne disait ce que vaut un CAHIER, qui est pourtant l'unite qu'on
#     ouvre, qu'on tient, et qu'on peut decider d'arreter.
# CONSEQUENCE ATTENDUE SUR `--comparer` : la route /echiquier ne connait pas ces
# deux detecteurs, l'ecart est donc normal jusqu'a ce qu'elle les porte aussi.
#
# Usage :
#     python scripts/etat_du_plan.py                 le rapport entier
#     python scripts/etat_du_plan.py --du            ce qui est du, seulement
#     python scripts/etat_du_plan.py --affaire "..." une affaire
#     python scripts/etat_du_plan.py --office O03    ce qui tombe sur un office
#     python scripts/etat_du_plan.py --jour-entree "30e de la 4e lune"
#                                                    resout les J-N sous hypothese
import io
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from plan.expose import (nu, sans_emoji, marque, blocs,  # noqa: E402
                         NUM, MO, NOM_GENRE, EST_MO, NERA, etiquette)
from plan.expose import genre_de as C_genre  # noqa: E402
# Les tables de la descente et le motif du « fait » vivent chez le chargeur :
# un seul lecteur du graphe, une seule vérité — y compris pour ses constantes.
from plan.expose import ATTENDU as C_ATTENDU, RANG as C_RANG  # noqa: E402
from plan.expose import FINI as C_FINI, premier_mot as C_premier_mot  # noqa: E402
from plan.expose import tete_ornee as C_tete_ornee  # noqa: E402
from plan.expose import numero_de as C_numero_de  # noqa: E402
import jours_relatifs as JR  # noqa: E402
import plan_modele as PM  # noqa: E402

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
# `voir` SANS limite de mot armait la lecture de dependance sur « sans avoir
# ete employee », et le nombre le plus proche etait pris pour un renvoi : les
# « 266 cerfs de Sirel » sont devenus une reference pendante de 64020. Un mot
# de dependance doit etre un MOT.
DEPEND = re.compile(u"apr[eè]s|d[eé]pend\\s+de|\\bvoir\\b", re.I)

# CE QUI EST CLOS — et la table l'ignorait. Elle a ete ecrite quand la colonne
# d'etat etait de la prose ; depuis la normalisation elle ne porte plus que six
# mots, et trois n'y figuraient pas. « faite » ne tombait dans aucun motif et
# ressortait « ? » : cinquante-six actions rendues s'affichaient comme si l'on
# ne savait pas ou elles en etaient.
FINI_ETAT = (u"faite", u"close", u"abandonnée")
STATUTS = [(u"^faite$", u"faite"), (u"^close$", u"close"),
           (u"^abandonn", u"abandonnée"),
           (u"tenu", u"tenu"), (u"bloqu", u"bloqué"), (u"en cours", u"en cours"),
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
        # Un jour NU ne dit pas sa lune. Le prendre pour la lune courante etait
        # juste vingt-neuf jours sur trente et faux le trentieme : au premier de
        # la quatrieme lune, « avant le 27e » devenait « dans vingt-six jours »
        # alors qu'il voulait dire « il y a quatre jours ». On retient donc
        # l'occurrence la PLUS PROCHE d'aujourd'hui, lune precedente comprise.
        j = int(m.group(1))
        a, l0 = date.get("annee", 0), date.get("lune", 0)
        ici = rang(a, l0, date.get("jour", 0))
        r, l = min(((rang(a, l0 + d, j), l0 + d) for d in (-1, 0, 1)),
                   key=lambda x: abs(x[0] - ici))
        return r, u"%de jour de la %de lune" % (j, l)
    return None


# ─────────────────────────────────────────────── l'echelle relative J−N
# Le chargeur de `couverture.py` ne retient qu'une poignee de colonnes, et les
# J−N vivent ailleurs : dans « Ce qu'on fait » (335 cellules), dans le cout
# (466), dans la note (83), dans l'office (24). On refait donc ici une passe
# de LECTURE SEULE sur les tables d'actions, avec la grammaire de
# `jours_relatifs.py` — la meme que celle qu'ecrit `dater_plan.py`, pour que
# le lecteur et l'ecrivain ne divergent jamais.
def relatives(livres):
    """{numero: (forme, colonne d'ou elle vient)} pour tout ce qui porte un J−N."""
    out = {}
    for b in livres:
        for t in (b.get("tables") or []):
            g = (C_genre((t or {}).get("titre") or u"")
                 or C_genre(b.get("titre") or u""))
            if g != "action":
                continue
            cols = (t or {}).get("colonnes") or []
            idx = {sans_emoji(nu(c)).strip().lower(): i for i, c in enumerate(cols)}
            for l in (t.get("lignes") or []):
                cel = [nu(x) for x in ((l if isinstance(l, list)
                                        else l.get("cellules")) or [])]
                if not cel:
                    continue
                m = C_numero_de(cel[0] or u"")
                if not m:
                    continue
                f, source = JR.candidat({k: cel[i] for k, i in idx.items()
                                         if i < len(cel)})
                if f:
                    out.setdefault(m.group(1), (f, source))
    return out


# L'ECHELLE, ACCESSIBLE AUX DETECTEURS SANS CHANGER LEUR SIGNATURE. `missions_de`
# est appelee a deux arguments par `criticite.py` et `depecher.py` : leur imposer
# un troisieme pour une seule regle serait payer le detecteur au prix de ses
# appelants. On memorise donc l'echelle une fois — posee par le __main__ qui a
# deja les livres en main, relue toute seule pour qui ne les a pas.
_REL = None


def echelle(livres=None):
    global _REL
    if _REL is None:
        if livres is None:
            livres = PM.charger()["livres"]
        _REL = relatives(livres)
    return _REL


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


def section_portee(modele):
    """Rend visible la frontiere de lecture qui protege les autres maisons."""
    ligne(u"Vue de %s · " % (modele.get("vue_de") or u"?"),
          u"%d volumes visibles · %d brouillons hors calcul"
          % (len(modele.get("livres") or []), len(modele.get("brouillons") or [])))


def section_synthese(modele):
    """Trois mesures qui ne doivent plus etre confondues."""
    m = PM.mesures(modele)
    s, d, p = m["structure"], m["declaration"], m["preuves"]
    titre(u"🧭 SYNTHÈSE — forme, déclaration, preuve")
    ligne(u"Structure · ", u"%d affaires actives · %d brouillons · %d collisions de numéro"
          % (s["affaires_actives"], s["brouillons"], s["collisions"]))
    ligne(u"Déclaré par les cahiers · ",
          u"%d faites · %d en cours · %d bloquées · %d à faire"
          % (d["fait"], d["en-cours"], d["bloque"], d["a-faire"]))
    ligne(u"Preuve des %d faites · " % p["actions_declarees_faites"],
          u"%d décrites au cahier · %d rattachées exactement à actes/événements résolus"
          % (p["preuve_documentee_dans_le_cahier"],
             p["preuve_rattachee_a_un_registre_canonique"]))
    ligne(u"Règle de lecture · ",
          u"un état 'fait' est une déclaration; un lien canonique est une preuve rattachée, pas une preuve inventée")


def section_brouillons(modele):
    brouillons = modele.get("brouillons") or []
    if not brouillons:
        return
    titre(u"📝 BROUILLONS — visibles, mais exclus de l'avancement")
    for b in brouillons:
        ligne(u"· " + (b.get("titre") or b.get("id") or u"sans titre"),
              u", ".join(b.get("raisons") or []))


PLAFOND = 40


def section_du(pieces, date, rel, jour_j, source_j,
               filtre_aff=None, filtre_off=None, tout=False):
    titre(u"⏳ CE QUI EST DÛ — les échéances datées, du plus urgent au plus lointain")
    ici = rang(date.get("annee", 0), date.get("lune", 0), date.get("jour", 0))

    # SOUS QUELLE ECHELLE ON TRAVAILLE, EN TETE ET SANS DETOUR. Un rapport qui
    # resout des J−N sur une date supposee et ne le dit pas est pire qu'un
    # rapport qui ne les lit pas : on le prend pour un calendrier.
    if jour_j:
        ligne(u"J = %de jour de la %de lune  (%s)"
              % (jour_j.get("jour", 0), jour_j.get("lune", 0), source_j))
        if source_j.startswith(u"hypothèse"):
            ligne(u"⚠ HYPOTHÈSE DE TRAVAIL — le jour d'entrée n'est arrêté nulle part "
                  u"dans l'état.")
            ligne(u"  Tout ce qui suit en J−N est calculé sous cette supposition et "
                  u"n'engage rien.")
    else:
        ligne(u"⚠ AUCUN JOUR D'ENTRÉE — ni dans l'état, ni en argument. Les J−N sont "
              u"comptés et")
        ligne(u"  triés entre eux, sans être convertis en jours de lune. "
              u"(--jour-entree \"30e de la 4e lune\")")
    sys.stdout.write(u"\n")

    datees, relat, attentes, muettes = [], [], 0, 0
    for n, p in pieces.items():
        if p["genre"] != "action":
            continue
        if filtre_aff and filtre_aff not in sans_emoji(p["affaire"]).lower():
            continue
        if filtre_off and p["office"] != filtre_off:
            continue
        # UNE ACTION RENDUE N'EST PLUS DUE. Elles montaient dans « ce qui est
        # dû » avec leur terme passé, et le tableau des retards s'ouvrait sur du
        # travail déjà fait — 11021, rendue par le castellan, tenait la première
        # ligne sous les cinq hypothèses de jour d'entrée.
        if nu(p["etat"]) in FINI_ETAT:
            continue
        e = echeance_de(p.get("jour") or p["etat"], date)
        if e:
            datees.append((e[0], n, p, e[1]))
            continue
        f = rel.get(n)
        if f:
            forme, source = f
            r = JR.resoudre(forme, jour_j) if jour_j else None
            if r is not None:
                datees.append((r, n, p, JR.canonique(forme)))
            else:
                relat.append((forme["n"], n, p, JR.canonique(forme), source))
            continue
        if amont_de(p["etat"]):
            attentes += 1
        else:
            muettes += 1

    if not datees:
        ligne(u"— aucune action ne porte de date absolue lisible.")
    montrees = sorted(datees) if (tout or filtre_aff or filtre_off) \
        else sorted(datees)[:PLAFOND]
    for r, n, p, lib in montrees:
        ecart = r - ici
        if ecart < 0:
            marq = u"‼ EN RETARD de %d j" % -ecart
        elif ecart == 0:
            marq = u"▶ AUJOURD'HUI     "
        else:
            marq = u"  dans %2d jours    " % ecart
        ligne(marq, u"  ", cale(marque(n, pieces), 12), cale(p["nom"], 40),
              cale(p["affaire"], 24), statut_de(p["etat"]))
    if len(montrees) < len(datees):
        ligne(u"… et %d autres, plus lointaines (--tout pour les voir)"
              % (len(datees) - len(montrees)))

    # SANS JOUR D'ENTREE, ON NE JETTE PLUS : on trie l'echelle sur elle-meme.
    # La plus en amont d'abord — c'est elle qui commande la date, et c'est la
    # seule question que le conseil ait a trancher.
    if relat:
        sys.stdout.write(u"\n")
        titre(u"🎡 CE QUI EST DÛ EN J−N — l'échelle à rebours, de la plus en amont "
              u"à la plus tardive")
        vus = sorted(relat)
        aff = vus if tout or filtre_aff or filtre_off else vus[:PLAFOND]
        for nn, n, p, lib, source in aff:
            ligne(cale(lib, 20), u"  ", cale(marque(n, pieces), 12),
                  cale(p["nom"], 38), cale(p["affaire"], 22), statut_de(p["etat"]))
        if len(aff) < len(vus):
            ligne(u"… et %d autres, plus proches de l'entrée (--tout pour les voir)"
                  % (len(vus) - len(aff)))
        # LA PLUS EN AMONT SE PREND PARMI CELLES QUI RESTENT A FAIRE. Une
        # action deja faite ne commande plus rien, et c'est elle qui remontait
        # en tete : le conseil aurait cale la date sur du travail fini.
        ouvertes = [v for v in vus if not C_FINI.match(statut_de(v[2]["etat"]))
                    and statut_de(v[2]["etat"]) not in (u"tenu",)]
        plus = (ouvertes or vus)[0]
        ligne(u"")
        ligne(u"La plus en amont encore ouverte : %s — %s (%s)."
              % (plus[3], sans_emoji(plus[2]["nom"]), sans_emoji(plus[2]["affaire"])))
        ligne(u"Tant que J n'est pas posé, aucune de ces %d-là ne peut être dite "
              u"en retard." % len(vus))

    sys.stdout.write(u"\n")
    ligne(u"%d action(s) à date absolue · %d en J−N%s · %d attendent une autre pièce · "
          u"%d sans date ni amont"
          % (len(datees), len(relat),
             u" (résolues ci-dessus)" if jour_j else u"", attentes, muettes))
    if muettes:
        ligne(u"→ ces %d-là ne se synchronisent sur rien : ni date, ni J−N, ni amont. "
              u"C'est le vrai trou." % muettes)


def section_chaines(pieces, date, filtre_aff=None, tout=False, rel=None):
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
            # UNE ACTION EN J−N EST ENGAGEE, elle aussi. Sans cette ligne, une
            # chaine dont l'aval est date a rebours passait pour dormante, et
            # « ce qui attend » ne montrait que les vingt et une actions a date
            # absolue : la section entiere ne voyait pas le plan.
            engage = (bool(echeance_de(p.get("jour") or p["etat"], date))
                      or (rel is not None and n in rel)
                      or statut_de(p["etat"]) == u"en cours")
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
    # LES DEUX REGISTRES NE SE MÉLANGENT PLUS. Les clefs portent leur casier
    # depuis le chargeur (voir `couverture.registre_de`) : le M01 de la reine et
    # celui de la Néra sont deux lignes, et chacune dit d'où elle sort.
    titre(u"🔨 CE QU'ON S'ARRACHE — moyens et offices tirés par plus d'une affaire")
    par_piece = {}
    for n, p in pieces.items():
        for m in p["moyens"] + ([p["office"]] if EST_MO.match(p["office"] or u"") else []):
            par_piece.setdefault(m, {}).setdefault(p["affaire"] or u"(sans affaire)", []).append(n)
    tires = {m: a for m, a in par_piece.items() if len(a) > 1}
    if filtre_aff:
        tires = {m: a for m, a in tires.items()
                 if any(filtre_aff in sans_emoji(x).lower() for x in a)}
    if not tires:
        ligne(u"— aucun moyen n'est tiré par deux affaires.")
    for m, a in sorted(tires.items(), key=lambda x: -len(x[1])):
        total = sum(len(v) for v in a.values())
        ligne(cale(etiquette(m, inventaire), 42),
              u"%d affaires, %d actions" % (len(a), total))
        ligne(u"   ", cale(u"", 38), u" · ".join(sorted(a)))
        # L'état ne se lit qu'au registre du grand plan : n'en coller aucun sur
        # un numéro de la Néra vaut mieux que d'y coller celui d'un homonyme —
        # c'est exactement la faute qu'on vient de retirer.
        e = etats_moyens.get(m) if not m.startswith(NERA) else None
        if e:
            ligne(u"   ", cale(u"", 38), u"état au registre : " + e)


def section_charge(pieces, offices, titulaires, filtre_aff=None):
    titre(u"🪶 LA CHARGE — ce qui tombe sur chaque office")
    par_off = {}
    for n, p in pieces.items():
        if p["genre"] != "action":
            continue
        if filtre_aff and filtre_aff not in sans_emoji(p["affaire"]).lower():
            continue
        par_off.setdefault(p["office"] or u"SANS OFFICE", []).append(p)
    orphelines = par_off.pop(u"SANS OFFICE", []) + par_off.pop(u"EN CLAIR", [])
    for o, ps in sorted(par_off.items(), key=lambda x: -len(x[1])):
        st = {}
        for p in ps:
            s = statut_de(p["etat"])
            st[s] = st.get(s, 0) + 1
        ligne(cale(etiquette(o, offices), 46), u" %3d actions   " % len(ps),
              u" · ".join(u"%s %d" % (k, v) for k, v in sorted(st.items())))
        t = titulaires.get(o)
        if t:
            ligne(u"   ", cale(u"", 43), u"titulaire : " + t)
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


# ─────────────────────────────────────────────── la grille
# UNE LIGNE PAR CAHIER — ce que le rapport ne savait pas dire.
#
# Toutes les autres sections coupent le plan par PIECE : ce qui est du, ce qui
# attend, ce qui tombe sur un office. Aucune ne dit ce que vaut un CAHIER, et
# c'est pourtant l'unite qu'on ouvre, qu'on tient, et qu'on peut decider
# d'arreter. Les six colonnes sont celles qui discriminent — mesure faite sur
# les 44 : les clefs tranchees vont de 0/15 a 10/10, les actions sans office de
# 0 a 17 sur 20. Une colonne ou tout le monde a la meme note ne s'ecrit pas.
#
# ELLE NE NOTE RIEN ET NE TOTALISE RIEN. Six colonnes cote a cote, jamais une
# moyenne : un cahier moyen partout et un cahier excellent sauf sur un point
# n'ont rien a voir, et la moyenne cache exactement ce qui tue.
def section_grille(pieces, affaires, date, rel):
    titre(u"📊 LA GRILLE — une ligne par cahier, le plus à reprendre en tête")
    ligne(cale(u"", 34), u"  🎯   🔒   🗝    ⚔    tranchées  ss office  ss date   faites"
                         u"   trous")
    lignes = []
    for b in affaires:
        nom = nu(b["titre"])
        g = {}
        tranchees = clefs = sans_off = sans_date = faites = actions = 0
        for n, p in pieces.items():
            if p["affaire"] != nom:
                continue
            g[p["genre"]] = g.get(p["genre"], 0) + 1
            if p["genre"] == "clef":
                clefs += 1
                e = (p.get("etat") or u"").lower()
                if u"retenue" in e or u"écart" in e or u"ecart" in e:
                    tranchees += 1
            elif p["genre"] == "action":
                actions += 1
                if p["office"] in (None, u"", u"SANS OFFICE", u"EN CLAIR"):
                    sans_off += 1
                if not echeance_de(p.get("jour") or p["etat"], date) and n not in rel:
                    sans_date += 1
                if C_premier_mot(p["etat"]) in (u"faite", u"close"):
                    faites += 1
        lignes.append((len(missions_de(nom, pieces)), nom, g, tranchees, clefs,
                       sans_off, sans_date, faites, actions))
    for trous, nom, g, tr, cl, so, sd, fa, ac in sorted(lignes, reverse=True):
        ligne(cale(nom, 34),
              u"%4d %4d %4d %4d   " % (g.get("etat", 0), g.get("verrou", 0),
                                       g.get("clef", 0), ac),
              cale(u"%d/%d" % (tr, cl) if cl else u"—", 11),
              cale(u"%d" % so if so else u"—", 11),
              cale(u"%d" % sd if sd else u"—", 9),
              cale(u"%d/%d" % (fa, ac) if ac else u"—", 8),
              u"%d" % trous)
    sys.stdout.write(u"\n")
    # LES DEUX FAITS QUI NE SE LISENT PAS EN BALAYANT LA COLONNE, parce qu'ils
    # sont des ZEROS : un cahier ou rien n'est tranche et un cahier ou rien n'est
    # commence se ressemblent en pleine page et ne se ressemblent pas du tout.
    muets = [x[1] for x in lignes if x[4] and not x[3]]
    froids = [x[1] for x in lignes if x[8] and not x[7]]
    if muets:
        ligne(u"‼ %d cahier(s) n'ont pas UNE clef tranchée : " % len(muets),
              u" · ".join(sorted(muets))[:LARGEUR - 44])
        ligne(u"  Ils ont pensé et n'ont rien décidé — rien ne peut partir de "
              u"là, quel que soit le nombre d'actions écrites.")
    if froids:
        ligne(u"❄ %d cahier(s) portent des actions et pas une de faite : " % len(froids),
              u" · ".join(sorted(froids))[:LARGEUR - 52])


def section_comparer(pieces, affaires):
    """DEUX LECTEURS, UN SEUL GRAPHE — et l'écart se voit. La route /echiquier
    dérive les mêmes trous pour l'écran ; si les deux comptes divergent, l'un
    des deux se trompe, et il vaut mieux le lire ici qu'en séance."""
    titre(u"⚖️ LES DEUX LECTEURS — ce script, et la route /echiquier")
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:3142/echiquier", timeout=60) as r:
            d = json.load(r)
    except Exception as e:
        ligne(u"— la route ne répond pas (%s). Lancer : node serveur/serveur.js 3142"
              % str(e)[:40])
        return
    ici = {}
    for b in affaires:
        for m in missions_de(nu(b["titre"]), pieces):
            ici[m["acte"]] = 1
    la = set((d.get("missions") or {}).keys())
    a, b2 = set(ici), la
    ligne(u"ici %d acte(s) · route %d acte(s) · communs %d"
          % (len(a), len(b2), len(a & b2)))
    if a - b2:
        ligne(u"ici seulement : " + u" · ".join(sorted(a - b2))[:LARGEUR - 20])
    if b2 - a:
        ligne(u"route seulement : " + u" · ".join(sorted(b2 - a))[:LARGEUR - 20])


AIDE = u"""etat_du_plan.py — l'état du plan, toutes affaires confondues.

    python scripts/etat_du_plan.py                 le rapport entier
    python scripts/etat_du_plan.py --du            ce qui est dû, et les chaînes
    python scripts/etat_du_plan.py --tout          toutes les chaînes, même dormantes
    python scripts/etat_du_plan.py --affaire "port-real"
    python scripts/etat_du_plan.py --office O03
    python scripts/etat_du_plan.py --grille          une ligne par cahier
    python scripts/etat_du_plan.py --qui             les trous par homme
    python scripts/etat_du_plan.py --pour gerardys   ses affaires, à lui seul
    python scripts/etat_du_plan.py --vue-de marlo-vasse
                                      le plan visible depuis un autre siège
    python scripts/etat_du_plan.py --comparer        l'écart avec la route /echiquier
    python scripts/etat_du_plan.py --jour-entree "30e de la 4e lune"
                                     résout les J−N sous hypothèse, et le dit en tête

DEUX ÉCHELLES. Le plan se date à rebours du jour d'entrée, qui n'est arrêté
nulle part (verrou 11001). Sans jour d'entrée, les J−N sont comptés et triés
entre eux dans leur propre section ; avec `--jour-entree`, ils sont convertis
en jours de lune sous une hypothèse annoncée en tête de rapport.

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
    pour = args[args.index("--pour") + 1] if "--pour" in args else None
    plafond = int(args[args.index("--combien") + 1]) if "--combien" in args else 12
    seul_du = "--du" in args

    vue_de = (args[args.index("--vue-de") + 1]
              if "--vue-de" in args else PM.personnage_par_defaut())
    modele = PM.charger(vue_de)
    livres = modele["livres"]
    pieces = modele["pieces"]
    inventaire = modele["inventaire"]
    affaires = modele["affaires"]
    date = aujourdhui()

    # L'ECHELLE RELATIVE, ET SON ANCRE. On cherche d'abord le jour d'entree
    # dans l'etat ; a defaut on prend l'hypothese donnee en argument ; a defaut
    # on ne resout rien et on le DIT. Jamais de date supposee en silence.
    rel = echelle(livres)
    jour_j, source_j = JR.cherche_dans_etat()
    if not jour_j and "--jour-entree" in args:
        jour_j = JR.lire_hypothese(args[args.index("--jour-entree") + 1], date)
        source_j = u"hypothèse donnée en argument"
        if not jour_j:
            raise SystemExit(u"--jour-entree : date illisible. Ex. \"30e de la 4e lune\".")
    elif not jour_j:
        source_j = None
    # LE NOM D'UN OFFICE VIENT DU CHARGEUR, le reste du registre du grand plan.
    # `registre()` lit un volume à plat et ne sait donc rien de `nera-moyens`,
    # qui porte ses deux tables dans `tables` : sans le repli sur l'inventaire,
    # l'office O01 de la Néra s'afficherait sans nom.
    offices = dict(inventaire)
    offices.update(registre(livres, "plan-offices", u"l'office|loffice"))
    titulaires = registre(livres, "plan-offices", u"titulaire")
    etats_moyens = registre(livres, "plan-moyens", u"^état$|^etat$")

    # LA COUPE PAR PERSONNE ferme le reste : un homme qui ouvre ça veut SES
    # affaires, pas l'état du royaume. Le conseil du matin, lui, garde sa page.
    if pour:
        section_jour(date, pieces, affaires)
        section_portee(modele)
        section_pour(pour, pieces, affaires, plafond)
        sys.stdout.write(u"\n")
        raise SystemExit(0)
    if "--grille" in args:
        section_jour(date, pieces, affaires)
        section_portee(modele)
        section_grille(pieces, affaires, date, rel)
        section_brouillons(modele)
        sys.stdout.write(u"\n")
        raise SystemExit(0)
    if "--qui" in args:
        section_jour(date, pieces, affaires)
        section_portee(modele)
        section_qui(pieces, affaires)
        section_emblemes(livres)
        section_brouillons(modele)
        if "--comparer" in args:
            section_comparer(pieces, affaires)
        sys.stdout.write(u"\n")
        raise SystemExit(0)
    if "--comparer" in args:
        section_comparer(pieces, affaires)
        sys.stdout.write(u"\n")
        raise SystemExit(0)

    section_jour(date, pieces, affaires)
    section_portee(modele)
    section_synthese(modele)
    section_du(pieces, date, rel, jour_j, source_j, filtre_aff, filtre_off,
               "--tout" in args)
    section_chaines(pieces, date, filtre_aff, "--tout" in args, rel)
    if not seul_du:
        section_arrache(pieces, inventaire, etats_moyens, filtre_aff)
        section_charge(pieces, offices, titulaires, filtre_aff)
        if not filtre_aff and not filtre_off:
            section_muettes(pieces, affaires)
        section_trous(pieces, inventaire, affaires, filtre_aff)
        section_brouillons(modele)
    sys.stdout.write(u"\n")
