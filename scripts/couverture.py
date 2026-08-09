# -*- coding: utf-8 -*-
# La couverture d'une affaire — calculee, jamais saisie.
#
# POURQUOI. Une couverture ecrite a la main ment en trois jours : on ajoute une
# action et l'on oublie de redire, en tete, qu'elle attend une piece d'ailleurs.
# Tout ce qui se DEDUIT du graphe se recalcule donc ici, et l'on ne laisse a la
# plume que ce qu'aucun calcul ne peut trouver : la conclusion, et fermee quand.
#
# LES LIENS SONT TYPES, ET LA MOITIE SE DERIVE.
#   ecrits  : decoupe / decoupee par · contredit · remplace / remplacee par · exclut
#   derives : attend / attendue par · sert / servie par · partage
# Un lien derive ne se saisit jamais : on le refait, il ne peut pas mentir.
#
# Usage :
#     python scripts/couverture.py              toutes les affaires
#     python scripts/couverture.py --affaire "L'entree sans bataille"
#     python scripts/couverture.py --verifier   dit ce qui bougerait, n'ecrit rien
import io, json, os, re, sys, unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVRES = os.path.join(RACINE, "etat", "books.json")

GENRES = [(u"états? cibles?", "etat"), (u"verrous?", "verrou"), (u"clefs?", "clef"),
          (u"actions?", "action"), (u"moyens?", "moyen"), (u"offices?", "office")]
NOM_GENRE = {"etat": u"🎯", "verrou": u"🔒", "clef": u"🗝️", "action": u"⚔️",
             "moyen": u"🔨", "office": u"🪶", "affaire": u"🏰"}

# Les liens qu'une main pose, et qu'on ne touche donc jamais.
ECRITS = {u"découpe", u"découpée par", u"contredit", u"remplace",
          u"remplacée par", u"exclut"}
# Ce qu'on trouvait avant le typage, et ce que ça devient.
VIEUX = {u"affaire mère": u"découpée par", u"affaire fille": u"découpe",
         u"mère": u"découpée par", u"fille": u"découpe"}


def nu(t):
    s = u"" if t is None else unicode(t) if sys.version_info[0] == 2 else str(t)
    s = s.replace(u"**", u"")
    s = u"".join(c for c in s if c not in u"　└")
    return u" ".join(s.split())


def sans_emoji(s):
    return u" ".join(u"".join(c for c in nu(s)
                              if unicodedata.category(c) != "So" and c != u"️").split())


def genre_de(titre):
    t = sans_emoji(titre).lower()
    for motif, g in GENRES:
        if re.search(motif, t):
            return g
    return None


NUM = re.compile(r"\b(\d{3,6})\b")
MO = re.compile(r"\b([MO]\d{2,3})\b")


def col(cols, motif):
    for i, c in enumerate(cols):
        if re.search(motif, sans_emoji(c), re.I):
            return i
    return None


# ─────────────────────────────────────────────── lire tout le graphe
def charger():
    livres = json.load(io.open(LIVRES, encoding="utf-8"))
    pieces = {}          # numero -> {genre, nom, affaire, vers[], moyens[], office, dep[], etat, ou}
    inventaire = {}      # M01 / O03 -> nom
    affaires = []        # les livres qui sont des affaires

    for b in livres:
        tables = b.get("tables") or [{"titre": b.get("titre"), "colonnes": b.get("colonnes"),
                                      "lignes": b.get("lignes")}]
        est_affaire = bool(b.get("tables")) and re.search(
            u"ouverture", sans_emoji(tables[0].get("titre") or u""), re.I)
        if est_affaire:
            affaires.append(b)
        for t in tables:
            g = genre_de(t.get("titre") or u"") or genre_de(b.get("titre") or u"")
            if not g:
                continue
            cols = t.get("colonnes") or []
            i_num, i_nom = 0, 1
            i_vers = col(cols, u"sert|bloque|ouvre|réalise|realise")
            i_moy, i_off = col(cols, u"moyens"), col(cols, u"office")
            i_dep, i_etat = col(cols, u"dépend|depend"), col(cols, u"^état$|^etat$|où ça en est|ou ca en est")
            # La colonne « Jour du » que docs/decoupage.md reclame : quand
            # elle existe, l'echeance cesse d'etre devinee dans du texte
            # libre. Absente, rien ne change — les cahiers sans colonne
            # continuent d'etre lus au motif, comme avant.
            i_jour = col(cols, u"jour dû|jour du")
            i_aff = col(cols, u"affaire")
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in (l if isinstance(l, list) else l.get("cellules") or [])]
                if len(c) < 2 or not c[i_num] or not c[i_nom]:
                    continue
                if g in ("moyen", "office"):
                    m = MO.search(c[i_num])
                    if m:
                        inventaire[m.group(1)] = c[i_nom]
                    continue
                m = NUM.search(c[i_num])
                if not m:
                    continue
                n = m.group(1)
                aff = c[i_aff] if (i_aff is not None and i_aff < len(c) and c[i_aff]) \
                    else (nu(b.get("titre")) if est_affaire else u"")
                p = pieces.setdefault(n, {"genre": g, "nom": c[i_nom], "affaire": aff,
                                          "vers": [], "moyens": [], "office": u"",
                                          "dep": [], "etat": u""})
                if aff and not p["affaire"]:
                    p["affaire"] = aff
                if i_vers is not None and i_vers < len(c):
                    p["vers"] = sorted(set(p["vers"]) | set(NUM.findall(c[i_vers])))
                if i_moy is not None and i_moy < len(c):
                    p["moyens"] = sorted(set(p["moyens"]) | set(MO.findall(c[i_moy])))
                    # cite en clair, sans numero : le lien n'existe pas pour la
                    # machine, et personne ne s'en apercevra jamais a la lecture
                    if c[i_moy] and not MO.search(c[i_moy]):
                        p["clair"] = True
                if i_off is not None and i_off < len(c):
                    o = MO.findall(c[i_off])
                    p["office"] = o[0] if o else (u"SANS OFFICE" if re.search(
                        u"sans office", c[i_off], re.I) else p["office"])
                    if c[i_off] and not o and not re.search(u"sans office", c[i_off], re.I):
                        p["clair"] = True
                        p["office"] = u"SANS OFFICE"
                if i_dep is not None and i_dep < len(c):
                    p["dep"] = sorted(set(p["dep"]) | set(NUM.findall(c[i_dep])))
                if i_etat is not None and i_etat < len(c) and c[i_etat]:
                    p["etat"] = c[i_etat]
                if i_jour is not None and i_jour < len(c) and c[i_jour]:
                    p["jour"] = c[i_jour]
    return livres, pieces, inventaire, affaires


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
        for m in p["moyens"] + ([p["office"]] if MO.match(p["office"] or u"") else []):
            engage.setdefault(m, []).append(n)
    autres = {}
    for n, p in pieces.items():
        if p["affaire"] in (nom_affaire, u""):
            continue
        for m in p["moyens"] + ([p["office"]] if MO.match(p["office"] or u"") else []):
            autres.setdefault(m, set()).add(p["affaire"])
    lignes_eng = [[m + u" " + inventaire.get(m, u"—"),
                   u" · ".join(marque(x, pieces) for x in sorted(v)),
                   u" · ".join(sorted(autres.get(m, []))) or u"—"]
                  for m, v in sorted(engage.items())]

    # 🕳️ les trous — cinq défauts, tous dérivés des relations
    ouvre_par, bloque_par, realise_par = set(), set(), set()
    for n, p in miennes.items():
        if p["genre"] == "clef":
            ouvre_par |= set(p["vers"])
        if p["genre"] == "verrou":
            bloque_par |= set(p["vers"])
        if p["genre"] == "action":
            realise_par |= set(p["vers"])
    trous = [
        (u"⚔️ action que personne ne peut porter (SANS OFFICE)",
         [n for n, p in miennes.items() if p["genre"] == "action"
          and (not p["office"] or p["office"] == u"SANS OFFICE")]),
        (u"🔒 verrou qu'aucune clef n'ouvre — il est mal nommé",
         [n for n, p in miennes.items() if p["genre"] == "verrou" and n not in ouvre_par]),
        (u"🗝️ clef retenue qu'aucune action ne réalise — une décision sans geste",
         [n for n, p in miennes.items() if p["genre"] == "clef"
          and re.search(u"retenue", p["etat"] or u"", re.I) and n not in realise_par]),
        (u"🎯 état qu'aucun verrou ne bloque — une intention sans plan",
         [n for n, p in miennes.items() if p["genre"] == "etat" and n not in bloque_par]),
        (u"🔤 moyen ou office cité en clair au lieu de son numéro — le lien n'existe pas",
         [n for n, p in miennes.items() if p.get("clair")]),
        (u"⚔️ action dont la chaîne ne remonte à aucun état cible",
         [n for n, p in miennes.items() if p["genre"] == "action" and not remonte(n, pieces)]),
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
            liens.add((u"partage", a, m + u" " + inventaire.get(m, u""), u""))

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


# ─────────────────────────────────────────────── écrire la couverture
CHAMPS = [u"LE NOM", u"L'OBJET", u"LE PÉRIMÈTRE — DANS", u"LE PÉRIMÈTRE — HORS",
          u"L'ÉTAT ACTUEL", u"LA PLAGE", u"LA CONCLUSION", u"FERMÉE QUAND"]
SIGNE = {u"LE NOM": u"🏷️", u"L'OBJET": u"🎯", u"LE PÉRIMÈTRE — DANS": u"🧱",
         u"LE PÉRIMÈTRE — HORS": u"🚫", u"L'ÉTAT ACTUEL": u"📌", u"LA PLAGE": u"🔢",
         u"LA CONCLUSION": u"💡", u"FERMÉE QUAND": u"🔚"}
CALCULE = u" — calculé, ne pas écrire à la main"


def refaire(b, pieces, inventaire):
    nom = nu(b.get("titre"))
    pend, eng, trous, liens, ech = blocs(nom, pieces, inventaire)
    tables = b["tables"]

    # 1 · l'ouverture : on garde tout ce qui est écrit, on ajoute LA CONCLUSION
    ouv = tables[0]
    largeur = len(ouv.get("colonnes") or [u"", u"", u"", u""])
    ecrit = {}
    for l in ouv.get("lignes") or []:
        c = (l if isinstance(l, list) else l.get("cellules")) or []
        if c:
            ecrit[sans_emoji(c[0]).upper()] = c
    neuves = []
    for ch in CHAMPS:
        c = ecrit.get(ch.upper())
        if c is None:
            c = [SIGNE[ch] + u" **" + ch + u"**"] + [u""] * (largeur - 1)
        neuves.append({"cellules": (c + [u""] * largeur)[:largeur]})
    if ech:
        r = [u"⏳ **LA PROCHAINE ÉCHÉANCE**", marque(ech[1], pieces) + u" — " + ech[0]] \
            + [u""] * largeur
        neuves.append({"cellules": r[:largeur]})
    ouv["lignes"] = neuves

    # 2 · les liens : les écrits restent, les dérivés se refont
    i_liens = next((i for i, t in enumerate(tables)
                    if re.search(u"affaires? li", sans_emoji(t.get("titre") or u""), re.I)), None)
    COLS_L = [u"🪢 Le lien", u"🔗 L'affaire", u"🔢 Notre pièce", u"🔢 La leur", u"📝 Pourquoi"]
    gardees = []
    if i_liens is not None:
        for l in tables[i_liens].get("lignes") or []:
            c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
            if not any(c):
                continue
            # ancienne forme : [affaire, relation, pourquoi]
            t0 = sans_emoji(tables[i_liens].get("colonnes", [u""])[0]).lower()
            if t0.startswith(u"l'affaire") or t0.startswith(u"laffaire"):
                lien = VIEUX.get(c[1].lower(), c[1].lower()) if len(c) > 1 else u""
                c = [lien, c[0], u"", u"", c[2] if len(c) > 2 else u""]
            c = (c + [u""] * 5)[:5]
            c[0] = VIEUX.get(c[0].lower(), c[0])
            if c[0].lower() in ECRITS:
                gardees.append({"cellules": c})
    derivees = [{"cellules": [l[0], l[1], l[2], l[3], u""]} for l in liens]
    table_liens = {"titre": u"🔗 Affaires liées — les liens écrits, puis les calculés",
                   "colonnes": COLS_L,
                   "lignes": (gardees + derivees) or [{"cellules": [u""] * 5}]}

    # 3 · les trois blocs calculés
    t_pend = {"titre": u"⛓️ Ce qui pend, et sur qui" + CALCULE,
              "colonnes": [u"🧭 Sens", u"🔢 Notre pièce", u"🔢 La leur", u"🔗 L'affaire"],
              "lignes": [{"cellules": l} for l in pend] or
                        [{"cellules": [u"—", u"", u"", u"rien ne traverse"]}]}
    t_eng = {"titre": u"🔨🪶 Ce qu'on engage, et qui d'autre le veut" + CALCULE,
             "colonnes": [u"🔢 La pièce", u"⚔️ Nos actions", u"🔗 Aussi engagée par"],
             "lignes": [{"cellules": l} for l in eng] or
                       [{"cellules": [u"—", u"", u"aucun moyen, aucun office"]}]}
    t_trous = {"titre": u"🕳️ Les trous" + CALCULE,
               "colonnes": [u"🕳️ Le défaut", u"🔢 Les pièces"],
               "lignes": [{"cellules": l} for l in trous] or
                         [{"cellules": [u"aucun — la chaîne tient de bout en bout", u""]}]}

    reste = [t for i, t in enumerate(tables) if i != 0 and i != i_liens
             and not re.search(u"ce qui pend|ce qu'on engage|les trous",
                               sans_emoji(t.get("titre") or u""), re.I)]
    b["tables"] = [ouv, table_liens, t_pend, t_eng, t_trous] + reste
    return len(pend), len(eng), len(trous), len(derivees)


if __name__ == "__main__":
    args = sys.argv[1:]
    verif = "--verifier" in args
    filtre = args[args.index("--affaire") + 1] if "--affaire" in args else None

    livres, pieces, inventaire, affaires = charger()
    if filtre:
        affaires = [a for a in affaires if sans_emoji(filtre).lower() in sans_emoji(a["titre"]).lower()]

    for b in affaires:
        n = refaire(b, pieces, inventaire)
        sys.stdout.write(u"%-46s pend %d · engage %d · trous %d · liens calcules %d\n"
                         % (nu(b["titre"])[:46], n[0], n[1], n[2], n[3]))
    if verif:
        sys.stdout.write(u"--verifier : rien n'a ete ecrit.\n")
    else:
        json.dump(livres, io.open(LIVRES, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        sys.stdout.write(u"%d couverture(s) refaite(s) dans etat/books.json\n" % len(affaires))
