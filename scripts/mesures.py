# -*- coding: utf-8 -*-
# Les adresses de mesure : ce qu'un cahier cite, et ce que l'etat tient vraiment.
#
# POURQUOI. Une colonne « La mesure » qui porte `recrutement-peyredragon.solde-due`
# a l'air tenue. Rien ne garantit pourtant que l'main existe, ni la mesure :
# on lit une adresse, on croit lire un chiffre, et personne ne s'en apercoit tant
# que la case n'est pas ouverte tout haut en conseil. La faute symetrique est pire
# encore : un compte qui avance seul dans mains.json et qu'aucun office ne cite
# ne remontera jamais a personne — il derive dans son coin jusqu'au jour ou il est
# intenable, et c'est exactement ce que la boucle des mains devait empecher.
#
# Ce script ne repare rien, n'arbitre rien, et n'ecrit NULLE PART. Il resout les
# adresses citees dans etat/books.json contre etat/mains.json, nomme les
# adresses mortes, nomme les mesures orphelines, et dit quels offices n'ont aucun
# compte a leur nom. Avec --seuils, il confronte en plus les hypotheses du plan
# (docs/decoupage.md, section 5) aux valeurs du jour — sans jamais affirmer un
# rapprochement qu'il ne peut pas prouver : quand le lien est douteux, il le dit
# et laisse la main tranchee a qui tient le registre.
#
# Usage :
#     python scripts/mesures.py                                 tout
#     python scripts/mesures.py --office O02                    une ligne d'office
#     python scripts/mesures.py --main recrutement-peyredragon
#     python scripts/mesures.py --seuils                        les hypotheses du plan
#     python scripts/mesures.py --aide
import io
import json
import os
import re
import sys
import unicodedata

import bibliotheque

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
livres_json = os.path.join(racine, "etat", "books.json")
mains_json = os.path.join(racine, "etat", "mains.json")
decoupage_md = os.path.join(racine, "docs", "decoupage.md")

LIVRE_OFFICES = "plan-offices"


# ─────────────────────────────────────────────── la sortie, sous Windows
def forcer_utf8():
    """Le shell d'ici est en cp1252 : sans ca, un emoji tue le script."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        return
    except Exception:
        pass
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")
    except Exception:
        pass


def dire(texte=u""):
    try:
        sys.stdout.write(texte + u"\n")
    except UnicodeEncodeError:
        sys.stdout.write(texte.encode("ascii", "replace").decode("ascii") + u"\n")


# ─────────────────────────────────────────────── comparer des titres a emoji
def nu(t):
    """Le texte d'une cellule, sans gras ni blancs superflus."""
    s = u"" if t is None else t if isinstance(t, str) else str(t)
    s = s.replace(u"**", u"")
    return u" ".join(s.split())


def sans_emoji(s):
    """Un titre de colonne comparable : les emoji et les selecteurs sautent."""
    return u" ".join(u"".join(c for c in nu(s)
                              if unicodedata.category(c) != "So"
                              and c != u"️").split())


def sans_accents(t):
    t = unicodedata.normalize("NFD", nu(t))
    return u"".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def colonne(colonnes, motif):
    """Index de la premiere colonne dont le titre nu colle au motif."""
    for i, c in enumerate(colonnes or []):
        if re.search(motif, sans_accents(sans_emoji(c)), re.I):
            return i
    return None


def cellules_de(ligne):
    if isinstance(ligne, list):
        return [nu(x) for x in ligne]
    return [nu(x) for x in ((ligne or {}).get("cellules") or [])]


def tables_de(livre):
    """Les deux formes d'un livre : a plat, ou en tables. Comme couverture.py."""
    if livre.get("tables"):
        return livre["tables"]
    return [{"titre": livre.get("titre"),
             "colonnes": livre.get("colonnes"),
             "lignes": livre.get("lignes")}]


# ─────────────────────────────────────────────── lire l'etat
def charger_livres():
    return bibliotheque.charger(os.path.join(racine, "etat"))


def charger_mains():
    if not os.path.exists(mains_json):
        return []
    with io.open(mains_json, encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, dict):
        d = d.get("mains") or []
    return d if isinstance(d, list) else []


def index_des_mesures(mains):
    """adresse `<main>.<mesure>` -> (main, mesure). Meme cle que tick.py."""
    index = {}
    for act in mains:
        for mes in act.get("mesure") or []:
            if act.get("id") and mes.get("id"):
                index[u"%s.%s" % (act["id"], mes["id"])] = (act, mes)
    return index


# ─────────────────────────────────────────────── les adresses dans le texte
# Entre backticks : `main-id.mesure-id`, ou la forme abregee `.mesure-id`
# qui herite de l'main de l'adresse precedente sur la MEME cellule.
BACKTICK = re.compile(u"`([^`]{1,120})`")
ADRESSE = re.compile(u"^(\\.?)([a-z0-9]+(?:-[a-z0-9]+)*)(?:\\.([a-z0-9]+(?:-[a-z0-9]+)*))?$")


def adresses_dans(texte, mains_connues=None, autoriser_inconnues=True):
    """Rend les adresses de mesure écrites dans une cellule.

    Hors d'une colonne explicitement consacrée aux mesures, un identifiant
    inconnu est bien plus souvent une référence de code (``h.l1``,
    ``process.argv``) qu'une adresse de compte. Les mains connues restent
    reconnues partout ; les inconnues ne sont gardées que lorsque l'appelant
    autorise leur diagnostic.
    """
    trouvees = []
    derniere_main = None
    for brut in BACKTICK.findall(nu(texte)):
        m = ADRESSE.match(brut.strip())
        if not m:
            continue
        point, un, deux = m.group(1), m.group(2), m.group(3)
        if deux:
            if (mains_connues is not None and un not in mains_connues
                    and not autoriser_inconnues):
                derniere_main = None
                continue
            derniere_main = un
            trouvees.append((u"%s.%s" % (un, deux), brut.strip()))
        elif point:
            # forme abregee : `.solde-due`
            if derniere_main:
                trouvees.append((u"%s.%s" % (derniere_main, un), brut.strip()))
            elif autoriser_inconnues:
                trouvees.append((None, brut.strip()))
        # un mot seul sans point n'est pas une adresse : on le laisse passer
    return trouvees


# ─────────────────────────────────────────────── les offices du plan
def lire_offices(livres):
    """Les lignes du livre plan-offices, chacune avec ce que sa case mesure cite."""
    offices = []
    for livre in livres:
        if livre.get("id") != LIVRE_OFFICES:
            continue
        for table in tables_de(livre):
            cols = table.get("colonnes") or []
            i_num = colonne(cols, u"^n°|^no$|^n$") or 0
            i_nom = colonne(cols, u"office")
            i_tit = colonne(cols, u"titulaire")
            i_mes = colonne(cols, u"mesure")
            if i_mes is None:
                continue
            for ligne in table.get("lignes") or []:
                c = cellules_de(ligne)
                if len(c) <= i_mes or not any(c):
                    continue
                case = c[i_mes]
                offices.append({
                    "numero": c[i_num] if i_num is not None and i_num < len(c) else u"",
                    "nom": c[i_nom] if i_nom is not None and i_nom < len(c) else u"",
                    "titulaire": c[i_tit] if i_tit is not None and i_tit < len(c) else u"",
                    "case": case,
                    "adresses": adresses_dans(case),
                })
    return offices


def citations_ailleurs(livres, mains_connues=None):
    """Toute adresse citee dans un autre livre que le registre des offices."""
    citations = []
    for livre in livres:
        if livre.get("id") == LIVRE_OFFICES:
            continue
        for table in tables_de(livre):
            cols = table.get("colonnes") or []
            for n, ligne in enumerate(table.get("lignes") or [], 1):
                c = cellules_de(ligne)
                for i, cell in enumerate(c):
                    titre_colonne = sans_accents(sans_emoji(cols[i])) \
                        if i < len(cols) else u""
                    colonne_mesure = bool(re.search(
                        u"mesure|compte|adresse", titre_colonne, re.I))
                    for adresse, brut in adresses_dans(
                            cell, mains_connues, autoriser_inconnues=colonne_mesure):
                        citations.append({
                            "livre_id": livre.get("id") or u"?",
                            "livre": nu(livre.get("titre")),
                            "table": nu(table.get("titre")),
                            "ligne": n,
                            "repere": c[0] if c else u"",
                            "colonne": sans_emoji(cols[i]) if i < len(cols) else u"",
                            "adresse": adresse,
                            "brut": brut,
                        })
    return citations


# ─────────────────────────────────────────────── dire une mesure
def mouvement(mesure):
    """« +3 par 2 jours » — le sens du courant, quand le rythme le dit."""
    r = mesure.get("rythme") or {}
    par = r.get("par")
    if par in (None, 0):
        return u""
    jours = r.get("jours") or 1
    signe = u"+" if par > 0 else u"−"
    quand = u"par jour" if jours == 1 else (u"par %d jours" % jours)
    return u"%s%s %s" % (signe, abs(par), quand)


def valeur_dite(mesure):
    v = mesure.get("valeur")
    u_ = mesure.get("unite") or u""
    return u"%s %s" % (v, u_) if u_ else u"%s" % (v,)


def porteur_dit(act):
    p = act.get("porteur") or {}
    bout = u"%s %s" % (p.get("type") or u"?", p.get("id") or u"?")
    if act.get("lieu_id"):
        bout += u" · à %s" % act["lieu_id"]
    bout += u" · avec mandat" if act.get("mandat") else u" · sans mandat"
    return bout


def ligne_de_mesure(adresse, act, mes, marge=u"      "):
    lignes = [u"%s`%s`  →  %s%s" % (marge, adresse, valeur_dite(mes),
                                    (u"   (" + mouvement(mes) + u")")
                                    if mouvement(mes) else u"")]
    if mes.get("quoi"):
        lignes.append(u"%s   « %s »" % (marge, mes["quoi"]))
    lignes.append(u"%s   porteur : %s" % (marge, porteur_dit(act)))
    if mes.get("depend_de"):
        lignes.append(u"%s   dépend de : %s" % (marge, u" · ".join(mes["depend_de"])))
    return lignes


# ─────────────────────────────────────────────── les trois sections
TITRE_1 = u"CE QUI SE MESURE"
TITRE_2 = u"CE QUI NE RÉSOUT PAS"
TITRE_3 = u"CE QUI N'A PAS DE MESURE"

# Ce qu'une case dit quand elle AVOUE le trou — et rien d'autre. « Aucune
# version ne prend quatre jours d'avance sur la sienne » est un critere, pas
# un aveu : le mot seul ne suffit donc pas, il faut la capitale ou le mot
# « mesure » derriere.
AVEU_MAJUSCULE = re.compile(u"\\bAUCUNE?\\b")
AVEU_MOT = re.compile(u"aucune? mesure|pas de mesure|rien au compte", re.I)


def avoue_le_trou(case):
    return bool(AVEU_MAJUSCULE.search(nu(case)) or AVEU_MOT.search(sans_accents(case)))


def entete(titre):
    dire(u"")
    dire(u"═" * 74)
    dire(u"  " + titre)
    dire(u"═" * 74)


def section_ce_qui_se_mesure(offices, citations, index, filtre_office, filtre_main):
    entete(TITRE_1)
    rien = True
    for o in offices:
        if filtre_office and sans_accents(o["numero"]) != sans_accents(filtre_office):
            continue
        vivantes = [(a, b) for a, b in o["adresses"]
                    if a in index and (not filtre_main
                                       or a.split(u".")[0] == filtre_main)]
        if not vivantes:
            continue
        rien = False
        dire(u"")
        dire(u"  %s  %s" % (o["numero"] or u"—", o["nom"]))
        if o["titulaire"]:
            dire(u"      titulaire : %s" % o["titulaire"])
        for adresse, brut in vivantes:
            act, mes = index[adresse]
            for l in ligne_de_mesure(adresse, act, mes):
                dire(l)

    if filtre_office:
        if rien:
            dire(u"")
            dire(u"  Cet office ne cite aucune adresse qui résolve.")
        return

    ailleurs = [c for c in citations if c["adresse"] in index
                and (not filtre_main
                     or c["adresse"].split(u".")[0] == filtre_main)]
    if ailleurs:
        dire(u"")
        dire(u"  ── Cité ailleurs dans les cahiers ──")
        for c in ailleurs:
            dire(u"")
            dire(u"  %s — %s" % (c["livre"], c["table"]))
            dire(u"      ligne %d (%s), colonne « %s »"
                 % (c["ligne"], c["repere"][:40], c["colonne"]))
            act, mes = index[c["adresse"]]
            for l in ligne_de_mesure(c["adresse"], act, mes):
                dire(l)
        rien = False
    elif not filtre_main:
        dire(u"")
        dire(u"  Aucun autre cahier ne cite d'adresse de mesure : le registre des")
        dire(u"  offices est le seul livre à en porter. Les colonnes de coût et de")
        dire(u"  preuve des affaires citent des chiffres en clair, qui ne bougent pas.")

    if rien:
        dire(u"")
        dire(u"  Rien. Aucune adresse citée ne résout.")


def section_ce_qui_ne_resout_pas(offices, citations, index, mains,
                                 filtre_office, filtre_main):
    entete(TITRE_2)

    # a) les adresses citees qui ne pointent nulle part
    mortes = []
    for o in offices:
        if filtre_office and sans_accents(o["numero"]) != sans_accents(filtre_office):
            continue
        for adresse, brut in o["adresses"]:
            if adresse is None:
                mortes.append((u"registre des offices, %s" % (o["numero"] or u"?"),
                               brut, u"forme abrégée sans adresse complète avant elle"))
            elif adresse not in index:
                aid = adresse.split(u".")[0]
                cause = (u"la main « %s » n'existe pas dans mains.json" % aid) \
                    if not any(a.get("id") == aid for a in mains) \
                    else (u"la main existe, mais elle n'a pas de mesure « %s »"
                          % adresse.split(u".", 1)[1])
                mortes.append((u"registre des offices, %s" % (o["numero"] or u"?"),
                               brut, cause))
    if not filtre_office:
        for c in citations:
            if c["adresse"] is None:
                mortes.append((u"%s, ligne %d" % (c["livre"], c["ligne"]),
                               c["brut"], u"forme abrégée sans adresse complète avant elle"))
            elif c["adresse"] not in index:
                aid = c["adresse"].split(u".")[0]
                cause = (u"la main « %s » n'existe pas dans mains.json" % aid) \
                    if not any(a.get("id") == aid for a in mains) \
                    else (u"la main existe, mais elle n'a pas cette mesure")
                mortes.append((u"%s, ligne %d" % (c["livre"], c["ligne"]),
                               c["brut"], cause))

    dire(u"")
    dire(u"  ── Adresses citées qui ne pointent sur rien ──")
    if mortes:
        for ou, brut, cause in mortes:
            dire(u"      `%s`  cité dans %s" % (brut, ou))
            dire(u"          %s" % cause)
    else:
        dire(u"      Aucune. Toute adresse citée trouve son compte.")

    if filtre_office:
        return

    # b) les mesures que personne ne cite
    citees = set()
    for o in offices:
        citees |= {a for a, _ in o["adresses"] if a}
    citees |= {c["adresse"] for c in citations if c["adresse"]}

    dire(u"")
    dire(u"  ── Mesures tenues que personne ne cite ──")
    orphelines = []
    for act in mains:
        if filtre_main and act.get("id") != filtre_main:
            continue
        for mes in act.get("mesure") or []:
            adresse = u"%s.%s" % (act.get("id"), mes.get("id"))
            if adresse in citees:
                continue
            gardee = [s for s in (act.get("seuils") or [])
                      if s.get("mesure_id") == mes.get("id")]
            orphelines.append((adresse, act, mes, gardee))
    if orphelines:
        for adresse, act, mes, gardee in orphelines:
            dire(u"")
            for l in ligne_de_mesure(adresse, act, mes, marge=u"    "):
                dire(l)
            if gardee:
                dire(u"       ses propres seuils la surveillent (%s) — mais aucun"
                     % u", ".join(s.get("id") or u"?" for s in gardee))
                dire(u"       cahier ne dit par quelle bouche le chiffre atteindrait")
                dire(u"       le joueur.")
            else:
                dire(u"       aucun seuil, aucun cahier : ce compte n'atteint personne.")
    else:
        dire(u"      Aucune. Chaque mesure tenue est citée quelque part.")


def section_sans_mesure(offices, filtre_office):
    entete(TITRE_3)
    trous, phrases = [], []
    for o in offices:
        if filtre_office and sans_accents(o["numero"]) != sans_accents(filtre_office):
            continue
        if any(a for a, _ in o["adresses"]):
            continue
        (trous if avoue_le_trou(o["case"]) else phrases).append(o)

    dire(u"")
    dire(u"  ── Trous déclarés : la case dit elle-même qu'il n'y a rien ──")
    if trous:
        for o in trous:
            dire(u"      %s  %s" % (o["numero"] or u"—", o["nom"]))
            dire(u"          %s" % (o["titulaire"] or u"sans titulaire"))
            dire(u"          la case : %s" % o["case"])
    else:
        dire(u"      Aucun.")

    dire(u"")
    dire(u"  ── Une phrase au lieu d'une adresse : rien ne se lit sans demander ──")
    if phrases:
        for o in phrases:
            dire(u"      %s  %s" % (o["numero"] or u"—", o["nom"]))
            dire(u"          %s" % (o["titulaire"] or u"sans titulaire"))
            dire(u"          la case : %s" % o["case"])
    else:
        dire(u"      Aucune.")


# ─────────────────────────────────────────────── les hypotheses du plan
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
