# -*- coding: utf-8 -*-
"""SECTIONS — la mise en page et les sections du rapport : le jour, le du,
les chaines, ce qu'on s'arrache, la charge, les muettes, les trous, la
grille et la comparaison avec la route /echiquier.
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

import json

import plan_modele as PM

from plan.etat_du_plan.page import LARGEUR, titre, ligne, cale
from plan.etat_du_plan.echeances import (JR, aujourdhui, statut_de, echeance_de,
                                         echelle, amont_de, rang,
                                         DEPEND, FINI_ETAT, STATUTS)
from plan.etat_du_plan.missions import missions_de

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

