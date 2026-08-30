# -*- coding: utf-8 -*-
"""SEUILS — les hypotheses du plan (docs/decoupage.md, section 5)
confrontees aux valeurs du jour, et l'entree CLI main().
"""
import io
import os
import re
import sys

from plan.mesures.adresses import (dire, nu, sans_emoji, sans_accents,
                                   decoupage_md, charger_livres,
                                   charger_mains, index_des_mesures,
                                   lire_offices, citations_ailleurs,
                                   forcer_utf8)
from plan.mesures.rapport import (valeur_dite, porteur_dit, entete,
                                  section_ce_qui_se_mesure,
                                  section_ce_qui_ne_resout_pas,
                                  section_sans_mesure)

MOTS_VIDES = set(u"""
avant apres dans sans pour sous plus moins chaque tout tous toute toutes avec
leur leurs cette celui celle ceux entre mais donc quand elle elles nous vous
aucun aucune etre sont fait faire rien bien meme ainsi alors encore jamais
toujours notre votre dont quoi lequel laquelle cela ceci vers chez selon
deux trois quatre cinq sept huit neuf dix cent mille premier premiere second
seconde une des les que qui est ont par sur son ses ses au aux
""".split())


def radical(mot):
    return mot[:5] if len(mot) >= 5 else mot


def mots_clefs(texte, exclure=()):
    hors = {radical(sans_accents(x)) for x in exclure}
    sortis = set()
    for m in re.split(u"[^a-z0-9]+", sans_accents(texte)):
        if len(m) < 4 or m in MOTS_VIDES or m.isdigit():
            continue
        r = radical(m)
        if r in hors:
            continue
        sortis.add(r)
    return sortis


def lire_hypotheses():
    """Le tableau H1..H11 de docs/decoupage.md, section « Les hypothèses du plan »."""
    if not os.path.exists(decoupage_md):
        return []
    with io.open(decoupage_md, encoding="utf-8") as f:
        texte = f.read()
    debut = None
    for m in re.finditer(u"^## +5\\..*$", texte, re.M):
        debut = m.end()
        break
    if debut is None:
        m = re.search(u"^#+ .*hypoth.ses du plan.*$", texte, re.M | re.I)
        debut = m.end() if m else None
    if debut is None:
        return []
    suite = re.search(u"^## ", texte[debut:], re.M)
    bloc = texte[debut:debut + suite.start()] if suite else texte[debut:]

    hypotheses = []
    for ligne in bloc.split(u"\n"):
        l = ligne.strip()
        if not l.startswith(u"|"):
            continue
        cases = [nu(x) for x in l.strip(u"|").split(u"|")]
        if len(cases) < 4:
            continue
        if re.match(u"^:?-{2,}", cases[0]) or sans_accents(cases[0]) in (u"#", u""):
            continue
        if not re.match(u"^h\\d+$", sans_accents(cases[0])):
            continue
        hypotheses.append({
            "num": cases[0],
            "hypothese": cases[1],
            "indicateur": cases[2] if len(cases) > 2 else u"",
            "seuil": cases[3] if len(cases) > 3 else u"",
            "decision": cases[4] if len(cases) > 4 else u"",
            "observateur": cases[5] if len(cases) > 5 else u"",
        })
    return hypotheses


NOMBRE = re.compile(u"(\\d+(?:[.,]\\d+)?)\\s*([a-zà-öø-ÿ']+)?", re.I)
SENS_SOUS = re.compile(u"moins de|sous|en dessous|inferieur|au plus|pas plus")
SENS_SUR = re.compile(u"plus de|au dela|au-dela|superieur|depass|doublement|au moins|excede")


def lire_seuil(texte):
    """Rend (nombre, unite, sens) tels qu'ils sont ÉCRITS. None si pas de chiffre."""
    m = NOMBRE.search(nu(texte))
    if not m:
        return None, None, None
    try:
        nombre = float(m.group(1).replace(u",", u"."))
    except ValueError:
        return None, None, None
    unite = sans_accents(m.group(2) or u"") or None
    plat = sans_accents(texte)
    sens = u"sous" if SENS_SOUS.search(plat) else (u"sur" if SENS_SUR.search(plat) else None)
    return nombre, unite, sens


def rapprocher(hypothese, index):
    """Tous les comptes qui pourraient être celui-là, du plus proche au moins.

    On ne rend jamais UN candidat quand plusieurs se valent : c'est ainsi
    qu'on annonce un franchissement qui n'a pas eu lieu. On rend la liste,
    et l'on dit pourquoi chacun est là.
    """
    nombre, unite, sens = lire_seuil(hypothese["seuil"])
    if nombre is None:
        nombre, unite, sens = lire_seuil(hypothese["indicateur"])
    if nombre is None:
        return None

    sac = mots_clefs(u"%s %s %s" % (hypothese["hypothese"], hypothese["indicateur"],
                                    hypothese["seuil"]),
                     exclure=[unite] if unite else [])
    candidats = []
    for adresse, (act, mes) in sorted(index.items()):
        u_mes = sans_accents(mes.get("unite") or u"")
        accord_unite = bool(unite) and bool(u_mes) and (
            u_mes == unite or u_mes.startswith(unite) or unite.startswith(u_mes))
        mots_mesure = mots_clefs(u"%s %s" % (mes.get("quoi") or u"", mes.get("id") or u""),
                                 exclure=[unite] if unite else [])
        mots_main = mots_clefs(u"%s %s" % (act.get("quoi") or u"", act.get("id") or u""),
                                   exclure=[unite] if unite else [])
        touche_mesure = sac & mots_mesure
        touche_main = (sac & mots_main) - touche_mesure
        note = (3.0 if accord_unite else 0.0) + len(touche_mesure) + 0.5 * len(touche_main)
        if note <= 0:
            continue
        candidats.append({
            "adresse": adresse, "main": act, "mesure": mes, "note": note,
            "accord_unite": accord_unite, "unite_seuil": unite,
            "mots_mesure": sorted(touche_mesure),
            "mots_main": sorted(touche_main),
        })
    candidats.sort(key=lambda c: (-c["note"], c["adresse"]))

    # SOLIDE seulement si un seul candidat porte la meilleure note, que
    # l'unité s'accorde, ET que deux mots au moins tombent dans le texte de
    # la mesure elle-même. Le nom d'un lieu partagé ne suffit pas.
    solide = False
    if candidats:
        tetes = [c for c in candidats if c["note"] == candidats[0]["note"]]
        solide = (len(tetes) == 1 and candidats[0]["accord_unite"]
                  and len(candidats[0]["mots_mesure"]) >= 2)
    return {"nombre": nombre, "unite": unite, "sens": sens,
            "candidats": candidats, "solide": solide}


def pourquoi_candidat(c):
    """En clair, ce qui a fait remonter ce compte — et ce qui manque."""
    bouts = []
    if c["accord_unite"]:
        bouts.append(u"même unité")
    elif c["unite_seuil"]:
        bouts.append(u"unité %s ≠ %s"
                     % (c["mesure"].get("unite") or u"?", c["unite_seuil"]))
    if c["mots_mesure"]:
        bouts.append(u"mot(s) « %s »" % u", ".join(c["mots_mesure"]))
    if c["mots_main"]:
        bouts.append(u"la main seule (« %s »)" % u", ".join(c["mots_main"]))
    return u" · ".join(bouts) or u"rien de net"


def verdict_arithmetique(valeur, sens, nombre):
    if valeur is None or sens is None:
        return u"sens du seuil non écrit — rien à conclure"
    if sens == u"sous":
        return u"franchi" if valeur < nombre else u"pas franchi"
    return u"franchi" if valeur > nombre else u"pas franchi"


def section_seuils(index):
    entete(u"LES HYPOTHÈSES DU PLAN, CONFRONTÉES AUX COMPTES DU JOUR")
    hypotheses = lire_hypotheses()
    if not hypotheses:
        dire(u"")
        dire(u"  docs/decoupage.md ne rend aucun tableau d'hypothèses lisible.")
        return
    dire(u"")
    dire(u"  Source : docs/decoupage.md, « Les hypothèses du plan ». %d hypothèses lues."
         % len(hypotheses))
    dire(u"  Aucun rapprochement n'est fait en silence : ce qui suit est proposé,")
    dire(u"  jamais acté. Un « rapprochement incertain » veut dire NE RIEN CONCLURE.")

    for h in hypotheses:
        dire(u"")
        dire(u"  %-4s %s" % (h["num"], h["hypothese"]))
        dire(u"       indicateur : %s" % (h["indicateur"] or u"—"))
        dire(u"       seuil écrit : %s" % (h["seuil"] or u"—"))
        r = rapprocher(h, index)
        if r is None:
            dire(u"       ⟶ pas de chiffre dans le seuil : rien à confronter ici.")
            dire(u"         À surveiller à l'œil, par %s." % (h["observateur"] or u"?"))
            continue
        borne = u"%g%s" % (r["nombre"], (u" " + r["unite"]) if r["unite"] else u"")
        dire(u"       lu comme : %s %s" % (r["sens"] or u"seuil (sens non écrit)", borne))
        if not r["candidats"]:
            dire(u"       ⟶ AUCUNE mesure tenue ne s'en rapproche. Cette hypothèse")
            dire(u"         n'est surveillée par aucun compte de mains.json.")
            continue

        if r["solide"]:
            c = r["candidats"][0]
            mes = c["mesure"]
            v = verdict_arithmetique(mes.get("valeur"), r["sens"], r["nombre"])
            dire(u"       ⟶ `%s` = %s · SEUIL %s"
                 % (c["adresse"], valeur_dite(mes), v.upper()))
            dire(u"         « %s »" % (mes.get("quoi") or u""))
            continue

        tetes = r["candidats"][:4]
        dire(u"       ⚠ RAPPROCHEMENT INCERTAIN — %d compte(s) s'en approchent,"
             % len(r["candidats"]))
        dire(u"         aucun ne se prouve. Les voici, et pourquoi :")
        for c in tetes:
            mes = c["mesure"]
            v = verdict_arithmetique(mes.get("valeur"), r["sens"], r["nombre"]) \
                if c["accord_unite"] else u"pas comparable"
            dire(u"           `%s` = %s" % (c["adresse"], valeur_dite(mes)))
            dire(u"               %s → dirait « %s »" % (pourquoi_candidat(c), v))
        dire(u"         Rien n'est conclu. À trancher à la main, par %s."
             % (h["observateur"] or u"?"))


# ─────────────────────────────────────────────── la main
AIDE = u"""
mesures.py — les adresses de mesure, résolues, et ce qui a franchi un seuil.

LECTURE SEULE. Ce script n'écrit dans etat/ ni nulle part ailleurs : il lit
etat/books.json, etat/mains.json et docs/decoupage.md, et imprime.

  python scripts/mesures.py
      Les trois sections : ce qui se mesure, ce qui ne résout pas, ce qui n'a
      pas de mesure.

  python scripts/mesures.py --office O02
      Une seule ligne du registre des offices (le numéro, tel qu'il y est écrit).

  python scripts/mesures.py --main recrutement-peyredragon
      Ce que tient une main, et qui la cite.

  python scripts/mesures.py --seuils
      En plus : les hypothèses du plan (docs/decoupage.md, section 5),
      confrontées aux valeurs du jour. Un rapprochement douteux est dit
      douteux — on n'annonce jamais un franchissement qu'on ne peut pas prouver.

  python scripts/mesures.py --aide     ce texte

CE QU'UNE ADRESSE EST. `main-id.mesure-id`, entre backticks, dans une
cellule de livre. La forme abrégée `.autre-mesure` hérite de la main de
l'adresse complète qui la précède dans la même cellule.

Si l'affichage casse sous ce shell, PYTHONIOENCODING=utf-8 aide — mais le
script force déjà sa sortie en utf-8 tout seul.
"""


def main(argv):
    forcer_utf8()
    if "--aide" in argv or "-h" in argv or "--help" in argv:
        dire(AIDE.strip())
        return 0

    filtre_office = filtre_main = None
    veut_seuils = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--office" and i + 1 < len(argv):
            filtre_office = argv[i + 1]; i += 2
        elif a == "--main" and i + 1 < len(argv):
            filtre_main = argv[i + 1]; i += 2
        elif a == "--seuils":
            veut_seuils = True; i += 1
        else:
            if a.startswith(u"-"):
                dire(u"Option inconnue : %s  (--aide pour la liste)" % a)
                return 2
            i += 1

    livres = charger_livres()
    mains = charger_mains()
    index = index_des_mesures(mains)
    offices = lire_offices(livres)
    mains_connues = {a.get("id") for a in mains if a.get("id")}
    citations = citations_ailleurs(livres, mains_connues)

    dire(u"LES MESURES — %d compte(s), %d mesure(s) tenue(s), %d office(s) au plan"
         % (len(mains), len(index), len(offices)))
    if filtre_office:
        dire(u"filtre : office %s" % filtre_office)
    if filtre_main:
        dire(u"filtre : main %s%s" % (filtre_main,
             u"" if any(a.get("id") == filtre_main for a in mains)
             else u"  ⚠ INCONNUE dans mains.json"))

    section_ce_qui_se_mesure(offices, citations, index, filtre_office, filtre_main)
    section_ce_qui_ne_resout_pas(offices, citations, index, mains,
                                 filtre_office, filtre_main)
    if not filtre_main:
        section_sans_mesure(offices, filtre_office)
    if veut_seuils:
        section_seuils(index)
    dire(u"")
    return 0
