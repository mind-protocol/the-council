# -*- coding: utf-8 -*-
"""BLOCS — les blocs calcules d'une couverture : ce qui pend, ce qu'on
engage, les trous, les liens derives, la prochaine echeance.
"""
import re
import unicodedata

from plan.couverture.lecture import (nu, sans_emoji, NOM_GENRE, EST_MO,
                                     etiquette)

# ─────────────────────────────────────────────── ce que chaque renvoi attend
# La chaîne du guide descend : état → verrou → clef → action. Une colonne de
# renvoi attend donc un genre PRÉCIS, et rien d'autre — « ⛔ Bloque » veut un
# état cible, « 🔓 Ouvre » un verrou, « 🗝️ Réalise » une clef. Un état, lui,
# sert un autre état.
ATTENDU = {"etat": "etat", "verrou": "etat", "clef": "verrou", "action": "clef"}
# Le rang de chaque genre dans la descente. Il départage deux fautes qu'on
# confondait, et qui n'ont rien à voir :
#   RACCOURCI       le renvoi monte, mais saute un rang — une action qui
#                   désigne directement un état cible. La chaîne tient, elle est
#                   seulement plus courte que le guide ne la veut. 83 fois sur
#                   ce plan : c'est une manière d'écrire, pas un accident.
#   ERREUR DE GENRE le renvoi ne monte pas : il pointe de côté ou vers le bas —
#                   un verrou dont la colonne « Bloque » porte une action. Là,
#                   quelqu'un s'est trompé de case, et ça ne se lit pas.
RANG = {"etat": 0, "verrou": 1, "clef": 2, "action": 3}

# L'état d'une action, réduit à son premier mot — le reste de la cellule porte
# souvent autre chose (« à faire · j−35 »), et ce n'est pas le sujet ici.
FINI = re.compile(u"^(fait|faite|faits|faites)\\b", re.I)


def tete_ornee(texte):
    """Un signe plante DEVANT le mot (« ✅ faite ») est une troisieme
    orthographe ; le meme signe ailleurs dans la phrase n'est rien du tout. On
    ne regarde donc que la tete, jusqu'a la premiere lettre."""
    for c in nu(texte or u""):
        if c.isalpha():
            return False
        if unicodedata.category(c) == "So":
            return True
    return False


def premier_mot(texte):
    """Le premier mot, sans sa ponctuation. « **FAITE.** ET SI CA CASSE » finit
    une phrase par un point : ce point n'est pas une orthographe de plus, et
    exiger qu'on l'efface pour que le compte tombe juste, ce serait faire plier
    la prose devant le detecteur."""
    t = sans_emoji(texte or u"").strip().lower()
    if not t:
        return u""
    return re.split(u"[ 	·,;(]", t)[0].strip(u".*:-_")


# ─────────────────────────────────────────────── les blocs calculés
def marque(n, pieces):
    p = pieces.get(n)
    return (NOM_GENRE.get(p["genre"], u"") + u" " + n) if p else n


def blocs(nom_affaire, pieces, inventaire):
    miennes = {n: p for n, p in pieces.items() if p["affaire"] == nom_affaire}

    # ⛓️ ce qui pend — les `dépend de` qui traversent, dans les deux sens
    pend = []
    for n, p in sorted(miennes.items()):
        for d in p["dep"]:
            q = pieces.get(d)
            if q and q["affaire"] and q["affaire"] != nom_affaire:
                pend.append([u"⬅ nous attendons", marque(n, pieces), marque(d, pieces), q["affaire"]])
    for n, p in sorted(pieces.items()):
        if p["affaire"] == nom_affaire or not p["affaire"]:
            continue
        for d in p["dep"]:
            if d in miennes:
                pend.append([u"➡ on nous attend", marque(d, pieces), marque(n, pieces), p["affaire"]])

    # 🔨🪶 ce qu'on engage — et qui d'autre le veut
    engage = {}
    for n, p in sorted(miennes.items()):
        for m in p["moyens"] + ([p["office"]] if EST_MO.match(p["office"] or u"") else []):
            engage.setdefault(m, []).append(n)
    autres = {}
    for n, p in pieces.items():
        if p["affaire"] in (nom_affaire, u""):
            continue
        for m in p["moyens"] + ([p["office"]] if EST_MO.match(p["office"] or u"") else []):
            autres.setdefault(m, set()).add(p["affaire"])
    lignes_eng = [[etiquette(m, inventaire),
                   u" · ".join(marque(x, pieces) for x in sorted(v)),
                   u" · ".join(sorted(autres.get(m, []))) or u"—"]
                  for m, v in sorted(engage.items())]

    # 🕳️ les trous — cinq défauts, tous dérivés des relations
    # LE PÉRIMÈTRE EST CELUI DU GRAPHE, PAS CELUI DU CAHIER. On ne cherchait ce
    # qui couvre une pièce que dans SA propre affaire : un état bloqué par un
    # verrou d'une autre affaire était donc déclaré « intention sans plan »,
    # alors que le lien est écrit noir sur blanc. Les affaires se découpent et
    # se servent l'une l'autre — c'est même ce que la table des liens dérivés
    # passe son temps à établir deux blocs plus haut.
    ouvre_par, bloque_par, realise_par = set(), set(), set()
    for n, p in pieces.items():
        if p["genre"] == "clef":
            ouvre_par |= set(p["vers"])
        if p["genre"] == "verrou":
            bloque_par |= set(p["vers"])
        if p["genre"] == "action":
            realise_par |= set(p["vers"])
    trous = [
        (u"⚔️ action que personne ne peut porter — aucun office, aucun nom",
         [n for n, p in miennes.items() if p["genre"] == "action"
          and (not p["office"] or p["office"] == u"SANS OFFICE")]),
        (u"🔒 verrou qu'aucune clef n'ouvre — il est mal nommé",
         [n for n, p in miennes.items() if p["genre"] == "verrou" and n not in ouvre_par]),
        (u"🗝️ clef retenue qu'aucune action ne réalise — une décision sans geste",
         [n for n, p in miennes.items() if p["genre"] == "clef"
          and re.search(u"retenue", p["etat"] or u"", re.I) and n not in realise_par]),
        (u"🎯 état qu'aucun verrou ne bloque — une intention sans plan",
         [n for n, p in miennes.items() if p["genre"] == "etat" and n not in bloque_par]),
        (u"🔤 office ou moyen nommé en clair — écrire son numéro, sans quoi le lien "
         u"n'existe pas pour la machine",
         [n for n, p in miennes.items() if p.get("clair")]),
        (u"⚔️ action dont la chaîne ne remonte à aucun état cible",
         [n for n, p in miennes.items() if p["genre"] == "action" and not remonte(n, pieces)]),
        # ── LA CHAÎNE ROMPUE AU MILIEU ──────────────────────────────────────
        # Les six défauts du dessus disent ce qui manque au BOUT de la chaîne :
        # pas de clef, pas d'action, pas d'office. Ces deux-ci disent autre
        # chose, et c'est plus grave : la chaîne est rompue EN SON MILIEU. Une
        # pièce désigne un numéro qui n'existe nulle part, ou n'en désigne
        # aucun — et le test disqualifiant du guide tombe, mot pour mot : « si
        # la remontée est impossible, l'action n'a pas de raison stratégique
        # démontrée : elle se supprime ou se requalifie ».
        #
        # ON NE RAPPROCHE JAMAIS AU PLUS PROCHE. Trois actions qui désignent la
        # clef 21020, laquelle n'existe pas : renumérotage ? clef supprimée ?
        # doigt glissé depuis 21021 ? Écrire la réponse à leur place, ce serait
        # écrire une FAUSSE raison stratégique, et une fausse raison est pire
        # que pas de raison — elle ne se voit plus. Même règle que le verseur de
        # cahiers : refuser plutôt que deviner.
        (u"⛓️‍💥 référence pendante — le numéro désigné n'existe nulle part dans le plan",
         [n for n, p in miennes.items()
          if any(v not in pieces for v in p["vers"])]),
        # LA RÉFÉRENCE QUI NE TIENT QU'AU REGISTRE. Elle résout — mais seulement
        # parce qu'on lit les deux plans à la fois. L'écran, lui, ne lit que les
        # cahiers : pour lui, ces renvois-là pendent dans le vide, et l'action
        # n'a plus de raison stratégique démontrée. Ce n'est donc pas une faute
        # de saisie, c'est la trace exacte de la question qui reste à trancher :
        # deux plans, ou un seul.
        (u"🪢 référence qui ne tient qu'au registre — la pièce désignée n'est dans "
         u"aucun cahier",
         [n for n, p in miennes.items()
          if any(v in pieces and not pieces[v].get("cahier") for v in p["vers"])]),
        (u"⚔️ action orpheline — elle ne désigne aucune clef, elle n'a jamais rien remonté",
         [n for n, p in miennes.items() if p["genre"] == "action" and not p["vers"]]),
        # Un numéro qui existe, mais du mauvais genre : « ⛔ Bloque » qui porte
        # une action au lieu d'un état cible. La colonne dit ce qu'elle attend ;
        # ce qu'on y a mis dit ce qu'on a cru y mettre.
        (u"🔀 erreur de genre — la colonne attend un rang et porte l'autre : "
         u"le renvoi ne remonte pas",
         [n for n, p in miennes.items()
          if any(v in pieces and RANG.get(pieces[v]["genre"], 9) >= RANG.get(p["genre"], 0)
                 and not (p["genre"] == "etat" and pieces[v]["genre"] == "etat")
                 for v in p["vers"])]),
        (u"↗️ raccourci — le renvoi saute un rang de la chaîne du guide",
         [n for n, p in miennes.items()
          if any(v in pieces and pieces[v]["genre"] != ATTENDU.get(p["genre"])
                 and RANG.get(pieces[v]["genre"], 9) < RANG.get(p["genre"], 0)
                 for v in p["vers"])]),
        # Trente-six actions terminées sous trois orthographes : aucun compte ne
        # peut dire si le plan avance. Ce n'est pas une faute de chaîne, c'est
        # une faute de tenue — et elle se répare d'un mot.
        (u"🏷️ « fait » écrit de plusieurs façons — rien ne peut se compter tant que ça dure",
         [n for n, p in miennes.items()
          if p["genre"] == "action" and FINI.match(premier_mot(p["etat"]) or u"")
          and (premier_mot(p["etat"]) != u"faite" or tete_ornee(p["etat"]))]),
    ]
    lignes_trous = [[t, u" · ".join(marque(x, pieces) for x in sorted(l))]
                    for t, l in trous if l]

    # 🔗 les liens dérivés entre affaires
    liens = set()
    for l in pend:
        liens.add((u"attend" if l[0].startswith(u"⬅") else u"attendue par", l[3],
                   l[1], l[2]))
    for n, p in miennes.items():
        if p["genre"] != "etat":
            continue
        for v in p["vers"]:
            q = pieces.get(v)
            if q and q["affaire"] and q["affaire"] != nom_affaire:
                liens.add((u"sert", q["affaire"], marque(n, pieces), marque(v, pieces)))
    for n, p in pieces.items():
        if p["genre"] != "etat" or p["affaire"] in (nom_affaire, u""):
            continue
        for v in p["vers"]:
            if v in miennes:
                liens.add((u"servie par", p["affaire"], marque(v, pieces), marque(n, pieces)))
    for m, v in engage.items():
        for a in sorted(autres.get(m, [])):
            liens.add((u"partage", a, etiquette(m, inventaire), u""))

    # ⏳ la prochaine échéance : ce qui porte une date, au plus tôt
    ech = sorted((p["etat"], n) for n, p in miennes.items()
                 if p["genre"] == "action" and re.search(r"\d+e\b|avant|le \d", p["etat"] or u""))
    return pend, lignes_eng, lignes_trous, sorted(liens), (ech[0] if ech else None)


def remonte(n, pieces, vu=None):
    """Une action remonte-t-elle jusqu'à un état cible ? action → clef → verrou → état."""
    vu = vu or set()
    if n in vu:
        return False
    vu.add(n)
    p = pieces.get(n)
    if not p:
        return False
    if p["genre"] == "etat":
        return True
    return any(remonte(v, pieces, vu) for v in p["vers"])
