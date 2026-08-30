# -*- coding: utf-8 -*-
"""RAPPORT — dire une mesure, et les trois sections : ce qui se mesure,
ce qui ne resout pas, ce qui n'a pas de mesure.
"""
import re

from plan.mesures.adresses import (dire, nu, sans_emoji, sans_accents,
                                   colonne, cellules_de, tables_de,
                                   adresses_dans)

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

