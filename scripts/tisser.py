# -*- coding: utf-8 -*-
# TISSER — projeter les treize mecanismes de lien dans UNE SEULE table d'aretes.
#
# POURQUOI. Le narratif de cette partie n'est pas dans les objets, il est dans
# ce qui les relie : ~2 290 aretes ecrites a la main contre ~1 000 objets. Mais
# elles vivent sous TREIZE noms, dans CINQ fichiers, et aucune requete ne les
# traverse. On ne peut donc pas poser les questions qui comptent : ou sont les
# goulots, quelle pression n'a pas de contre-arete, qu'est-ce qui pend dans le
# vide, qu'est-ce qui repond a ce que le joueur vient de faire.
#
# CE SCRIPT NE MIGRE RIEN ET N'ECRIT PAS DANS etat/. Il PROJETTE : il relit les
# formats existants, tels qu'ils sont, et rend une vue. Les fichiers restent la
# source ; le tissu est derive et se refait a chaque appel. C'est le seul moyen
# de savoir si le modele tient AVANT d'avoir converti quoi que ce soit.
#
# LE CHIFFRE QUI DECIDE DE TOUT LE RESTE est le taux de resolution : une arete
# dont une extremite ne se resout pas est une arete qu'aucun calcul ne suivra.
# Au-dela de 10% de pendantes, on repare l'adressage avant d'aller plus loin.
#
# Usage :
#     python scripts/tisser.py                 le rapport
#     python scripts/tisser.py --pendantes     ce qui ne resout pas, en clair
#     python scripts/tisser.py --ecrire        depose le tissu en staging
import argparse
import io
import json
import os
import re
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chiffrer  # noqa: E402  (la grammaire des couts)

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
SORTIE = os.path.join(ETAT, "staging", "tissu")

# LE VOCABULAIRE DES LIENS — seize natures, six familles. Il vit ICI parce que
# c'est le projecteur qui le pose : un script d'assessment qui lirait le tissu
# brut compterait 34 natures et raterait deux aretes sur 529 en cherchant
# `depend_de`. La lecon a deja ete payee sur `sterile()` — une definition
# ecrite deux fois diverge le jour meme.
CANON = {
    "realise": "realise", "réalise": "realise",
    "ouvre": "ouvre", "verrouille": "ouvre",
    "bloque": "bloque", "verrouillé_par": "bloque", "menacé_par": "bloque",
    "depend_de": "depend_de", "dépend_de": "depend_de",
    "sert": "sert", "servie_par": "sert$", "fournit": "sert",
    "garantit": "sert", "finance": "sert",
    "attend": "attend", "attendue_par": "attend$", "attendu_par": "attend$",
    "découpe": "decoupe", "découpée_par": "decoupe$", "partage": "decoupe",
    "lie": "lie",
    "coute": "coute", "coûte_à": "coute", "coute_chiffre": "coute_chiffre",
    "tient": "tient", "promeut": "promeut",
    "revele": "revele", "prévient": "revele", "surveille": "revele",
    "repond": "repond", "devie": "devie",
    "contredit": "contredit", "resonance": "resonance",
    "poursuit": "poursuit", "acteur_de": "acteur_de",
}

# `X$` : la meme arete, ecrite a l'envers. On la retourne — un graphe oriente
# qui garde les deux sens ment sur la moitie de ses fleches.
INVERSES = {"sert$": "sert", "attend$": "attend", "decoupe$": "decoupe"}

PIECE = re.compile(r"\b\d{3,6}\b")
MOYEN = re.compile(r"\bM\d{2,3}\b")
OFFICE = re.compile(r"\bO\d{2,3}\b")
HYPO = re.compile(r"\bH\d{1,2}\b")


def charger(nom, defaut):
    p = os.path.join(ETAT, nom + ".json")
    if not os.path.isfile(p):
        return defaut
    with io.open(p, encoding="utf-8") as fh:
        t = fh.read().strip()
    if not t:
        return defaut
    try:
        d = json.loads(t)
    except ValueError:
        return defaut
    return d.get(nom, d) if isinstance(d, dict) else d


def grilles(livre):
    """Toutes les tables d'un volume, la sienne comprise."""
    out = []
    if livre.get("colonnes"):
        out.append((livre.get("titre") or "", livre["colonnes"],
                    livre.get("lignes") or []))
    for t in livre.get("tables") or []:
        if t.get("colonnes"):
            out.append((t.get("titre") or "", t["colonnes"],
                        t.get("lignes") or []))
    return out


# Les livres qui DEFINISSENT des moyens et des offices. Un M12 cite dans
# n'importe quel cahier designe celui de la sphere ou ce cahier vit — la
# reine et Aurore ont chacune leur M01, et ce ne sont pas les memes.
def registres_de(books):
    reg = {}
    for l in books:
        lid = l.get("id") or ""
        for titre, C, lignes in grilles(l):
            for r in lignes:
                tete = nu((r.get("cellules") or [""])[0])
                if MOYEN.fullmatch(tete) or OFFICE.fullmatch(tete):
                    reg.setdefault(lid, set()).add(tete)
    return reg


def sphere_de(lid):
    """A quelle sphere appartient un cahier. Les cahiers d'Aurore portent le
    prefixe `nera-` ou `affaire-` de son coffre ; le reste est a la reine."""
    return "nera" if str(lid).startswith("nera-") else "reine"


def resoudre_code(code, lid, registres):
    """Le livre de moyens/offices de la meme sphere, sinon le citant."""
    for rid, codes in registres.items():
        if code in codes and sphere_de(rid) == sphere_de(lid):
            return rid + ":" + code
    for rid, codes in registres.items():
        if code in codes:
            return rid + ":" + code
    return lid + ":" + code


def nommer(personnages):
    """nom en clair -> id. La colonne « Office » d'une action ecrit « Rulf
    Corne », pas « O07 » : sans cette table, 501 actions passaient pour sans
    titulaire alors que 54 seulement le sont. Un chiffre faux est pire qu'un
    chiffre absent — la lecon de `sterile()`, encore."""
    t = {}
    for p in personnages or []:
        if not isinstance(p, dict) or not p.get("id"):
            continue
        for forme in (p.get("nom") or "", p["id"].replace("-", " ")):
            k = plat_nom(forme)
            if len(k) > 4:
                t[k] = p["id"]
    return t


def plat_nom(t):
    import unicodedata as _u
    t = _u.normalize("NFD", str(t or ""))
    t = "".join(c for c in t if _u.category(c) != "Mn").lower()
    return re.sub(r"[^a-z ]+", " ", t).strip()


A_DESIGNER = re.compile(r"a *designer|a *nommer|case *vide", re.I)


def col(d, motif):
    """La cellule dont l'en-tete contient `motif` — les en-tetes portent des
    emoji et des accents, on ne peut pas les egaler."""
    for k, v in d.items():
        if motif in k:
            return str(v or "")
    return ""


def nu(t):
    return re.sub(r"\*", "", str(t or "")).strip()


# ------------------------------------------------------------ les noeuds

def indexer(books, intentions, mains, plans, evenements, personnages):
    """Ce qui EXISTE, et sous quelle adresse. Une arete pointe ici ou pend."""
    noeuds = {}          # id -> {genre, ou, quoi}
    doubles = collections.Counter()

    def pose(ident, genre, ou, quoi):
        if not ident:
            return
        if ident in noeuds and noeuds[ident]["genre"] != genre:
            doubles[ident] += 1
        noeuds.setdefault(ident, {"genre": genre, "ou": ou,
                                  "quoi": nu(quoi)[:70]})

    for l in books:
        lid = l.get("id")
        for titre, C, lignes in grilles(l):
            for r in lignes:
                d = dict(zip(C, r.get("cellules") or []))
                tete = nu((r.get("cellules") or [""])[0])
                if not tete:
                    continue
                m = PIECE.fullmatch(tete)
                if m:
                    genre = ("action" if "Action" in titre else
                             "clef" if "Clef" in titre else
                             "verrou" if "Verrou" in titre else
                             "etat_cible" if "cible" in titre else "piece")
                    pose(tete, genre, lid, col(d, "🏷️") or col(d, "L'action"))
                elif MOYEN.fullmatch(tete):
                    # Les moyens sont un espace de noms PAR LIVRE : M01 vaut
                    # les voiles du Gosier chez la reine et la porte de la
                    # Gadoue chez Aurore. On qualifie, sinon on melange deux
                    # mondes sous une meme adresse.
                    pose(lid + ":" + tete, "moyen", lid, col(d, "🏷️"))
                elif OFFICE.fullmatch(tete):
                    pose(lid + ":" + tete, "office", lid, col(d, "🏷️"))

    for t in intentions:
        pid = t.get("personnage_id")
        pose("pers:" + str(pid), "personne", "intentions", t.get("intention"))
        for e in t.get("plan") or []:
            if e.get("id"):
                pose("etape:" + e["id"], "etape", pid, e.get("quoi"))

    for a in mains:
        aid = a.get("id")
        pose("main:" + str(aid), "compte", "mains", a.get("quoi"))
        for mes in a.get("mesure") or []:
            pose("{}.{}".format(aid, mes.get("id")), "mesure", aid,
                 mes.get("quoi"))

    for e in evenements:
        pose("ev:" + str(e.get("id")), "evenement", "evenements",
             e.get("description"))

    for p in personnages:
        if p.get("id"):
            pose("pers:" + p["id"], "personne", "personnages", p.get("nom"))

    for lx in charger("lieux", []):
        if isinstance(lx, dict) and lx.get("id"):
            pose("lieu:" + lx["id"], "lieu", "lieux", lx.get("nom"))

    for e in ("scene", "orbite", "royaume"):
        pose("echelle:" + e, "echelle", "schema", e)
    pose("neant", "rien", "schema", "ce qui ne coute rien")
    pose("a_designer", "vacant", "schema", "aucun titulaire — case ouverte")
    for u in chiffrer.UNITES + chiffrer.MONNAIE:
        pose("unite:" + u, "unite", "schema", u)

    for pl in plans:
        for fam, genre in (("etats_cibles", "etat_cible"), ("verrous", "verrou"),
                           ("clefs", "clef"), ("actions", "action")):
            for x in pl.get(fam) or []:
                pose(x.get("id"), genre, "plan:" + pl["id"], x.get("quoi"))

    return noeuds, doubles


# ------------------------------------------------------------- les aretes

def tisser(books, intentions, mains, plans, evenements, personnages=None,
           joueur=None, lieux_connus=()):
    registres = registres_de(books)
    noms = nommer(personnages or [])
    """Une arete par lien reellement ecrit. `flou` = presente, non suivable."""
    A = []

    def arc(de, vers, nature, source, flou=False, texte=""):
        # LE REPLI, A LA POSE. Canoniser apres coup obligerait chaque script
        # d'assessment a le refaire, et le premier qui l'oublierait mesurerait
        # un goulot faux.
        c = CANON.get(nature, nature)
        if c in INVERSES:
            c, de, vers = INVERSES[c], vers, de
        # CE QUI EST EN PROSE ET SE LAISSE POURTANT LIRE. Un cout qui cite une
        # mesure pointe vers un vrai noeud ; un cout chiffre porte ce qu'il
        # mange ; un « neant » est une reponse, pas un trou. 343 aretes sur
        # 1 048 sortent du flou sans qu'on ait rien converti.
        lu = None
        if flou and texte and c in ("coute_chiffre", "coute"):
            classe, tire = chiffrer.classer(texte)
            if classe == "cite_une_mesure":
                vers, flou, lu = tire["adresse"], False, {"classe": classe}
            elif classe == "declare_neant":
                vers, flou, lu = "neant", False, dict(tire, classe=classe)
            elif classe == "chiffrable":
                q = (tire.get("quantites") or [{}])[0]
                if q.get("quoi"):
                    vers, flou = "unite:" + q["quoi"], False
                    lu = dict(tire, classe=classe)
        a = {"de": de, "vers": vers, "nature": c, "source": source,
             "flou": flou, "texte": nu(texte)[:110]}
        if lu:
            a["lu"] = lu
        A.append(a)

    # --- les cinq mecanismes des cahiers
    for l in books:
        lid = l.get("id")
        for titre, C, lignes in grilles(l):
            est_act = "Action" in titre
            est_clef = "Clef" in titre
            est_ver = "Verrou" in titre
            est_lie = "liées" in titre or "liees" in titre
            est_ten = "ne tient pas" in titre
            for r in lignes:
                cells = r.get("cellules") or []
                d = dict(zip(C, cells))
                tete = nu(cells[0]) if cells else ""
                if est_act and PIECE.fullmatch(tete):
                    for n in PIECE.findall(col(d, "Réalise")):
                        arc(tete, n, "realise", "books/actions")
                    for n in PIECE.findall(col(d, "Dépend")):
                        arc(tete, n, "depend_de", "books/actions")
                    for m in MOYEN.findall(col(d, "Moyens")):
                        arc(tete, resoudre_code(m, lid, registres), "coute",
                            "books/actions")
                    bureau = col(d, "Office")
                    codes = OFFICE.findall(bureau)
                    for o in codes:
                        arc(tete, resoudre_code(o, lid, registres), "tient",
                            "books/actions")
                    if not codes and bureau.strip():
                        pn = plat_nom(bureau)
                        trouve = None
                        if A_DESIGNER.search(pn):
                            trouve = "a_designer"
                        else:
                            for nom, pid in noms.items():
                                if nom in pn:
                                    trouve = "pers:" + pid
                                    break
                        arc(tete, trouve or "?", "tient", "books/actions",
                            flou=trouve is None, texte=bureau)
                    # Le cout est a moitie en prose : on le pose FLOU quand il
                    # ne cite aucune adresse. Compter une arete floue comme
                    # suivable serait mentir sur ce que le graphe sait faire.
                    c = col(d, "coûte")
                    if c.strip():
                        cible = None
                        mm = re.search(r"([a-z0-9-]+\.[a-z0-9-]+)", c)
                        if mm:
                            cible = mm.group(1)
                        arc(tete, cible or "?", "coute_chiffre",
                            "books/actions", flou=cible is None, texte=c)
                elif est_clef and PIECE.fullmatch(tete):
                    for n in PIECE.findall(col(d, "Ouvre")):
                        arc(tete, n, "ouvre", "books/clefs")
                elif est_ver and PIECE.fullmatch(tete):
                    for n in PIECE.findall(col(d, "Bloque")):
                        arc(tete, n, "bloque", "books/verrous")
                elif (MOYEN.fullmatch(tete) or OFFICE.fullmatch(tete))                         and col(d, "Qui le tient").strip():
                    # UN MOYEN A UN PORTEUR, et c'est ce qui en fait un point
                    # de rupture : « un seul mestre pour tout ».
                    pn = plat_nom(col(d, "Qui le tient"))
                    cible = None
                    if pn.strip() in ("moi", "moi meme", "la reine"):
                        cible = "pers:" + (joueur or "rhaenyra")
                    for nom, pid in noms.items():
                        if nom in pn:
                            cible = "pers:" + pid
                            break
                    arc(lid + ":" + tete, cible or "?", "tient",
                        "books/moyens", flou=cible is None,
                        texte=col(d, "Qui le tient"))
                elif est_lie:
                    nature = nu(col(d, "Le lien")) or "lie"
                    nous = PIECE.findall(col(d, "Notre pièce"))
                    leur = PIECE.findall(col(d, "La leur"))
                    for a in (nous or ["?"]):
                        for b in (leur or ["?"]):
                            arc(a, b, nature.replace(" ", "_"),
                                "books/affaires-liees",
                                flou=(a == "?" or b == "?"),
                                texte=col(d, "Pourquoi"))
                elif est_ten:
                    arc(lid, "?", "contredit", "books/tensions", flou=True,
                        texte=col(d, "monnaie") or nu(cells[1] if len(cells) > 1 else ""))

    # --- les tetes
    for t in intentions:
        pid = "pers:" + str(t.get("personnage_id"))
        for e in t.get("plan") or []:
            eid = "etape:" + str(e.get("id"))
            arc(pid, eid, "poursuit", "intentions/plan")
            for dd in e.get("depend_de") or []:
                arc(eid, "etape:" + str(dd), "depend_de", "intentions/plan")
            for c in e.get("cout") or []:
                if isinstance(c, dict) and c.get("mesure"):
                    arc(eid, c["mesure"], "coute_chiffre", "intentions/cout")
                else:
                    arc(eid, "?", "coute_chiffre", "intentions/cout",
                        flou=True, texte=str(c))
        for dcl in t.get("declencheurs") or []:
            arc(pid, "?", "repond", "intentions/declencheurs", flou=True,
                texte=(dcl.get("si") if isinstance(dcl, dict) else str(dcl)))

    # --- les evenements
    for e in evenements:
        eid = "ev:" + str(e.get("id"))
        for dif in e.get("diffusion") or []:
            for q in (dif.get("qui") or []):
                arc(eid, "pers:" + str(q), "revele", "evenements/diffusion",
                    texte=dif.get("version"))
            if not (dif.get("qui") or []):
                arc(eid, "lieu:" + str(dif.get("ou")), "revele",
                    "evenements/diffusion", texte=dif.get("version"))
        for c in e.get("conditions") or []:
            arc("?", eid, "devie", "evenements/conditions", flou=True, texte=c)
        for a in (e.get("acteurs") or []):
            arc("pers:" + str(a), eid, "acteur_de", "evenements/acteurs")

    # --- les mains
    for a in mains:
        aid = a.get("id")
        por = (a.get("porteur") or {}).get("id")
        if por:
            prefixe = "lieu:" if por in lieux_connus else "pers:"
            arc(prefixe + str(por), "main:" + str(aid), "tient", "mains/porteur")
        for mes in a.get("mesure") or []:
            adr = "{}.{}".format(aid, mes.get("id"))
            for dd in mes.get("depend_de") or []:
                arc(adr, dd, "depend_de", "mains/mesure")
        for s in a.get("seuils") or []:
            if s.get("promeut"):
                arc("main:" + str(aid), "echelle:" + s["promeut"], "promeut",
                    "mains/seuils")

    # --- les plans d'en face
    for pl in plans:
        for x in pl.get("verrous") or []:
            for b in x.get("bloque") or []:
                arc(x["id"], b, "bloque", "plans/verrous")
        for x in pl.get("clefs") or []:
            for b in x.get("ouvre") or []:
                arc(x["id"], b, "ouvre", "plans/clefs")
        for x in pl.get("actions") or []:
            for b in x.get("realise") or []:
                arc(x["id"], b, "realise", "plans/actions")
            for b in x.get("depend_de") or []:
                arc(x["id"], b, "depend_de", "plans/actions")
            if x.get("office"):
                cible = ("a_designer" if A_DESIGNER.search(plat_nom(x["office"]))
                         else "pers:" + x["office"])
                arc(x["id"], cible, "tient", "plans/actions")
        for x in pl.get("resonance") or []:
            arc(x.get("leur_piece", "?"), x.get("notre_affaire", "?"),
                "resonance", "plans/resonance", flou=True,
                texte=x.get("pourquoi"))
    return A


# ------------------------------------------------------------- le rapport

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pendantes", action="store_true")
    ap.add_argument("--ecrire", action="store_true")
    args = ap.parse_args()

    books = charger("books", [])
    intentions = charger("intentions", [])
    mains = charger("mains", [])
    evenements = charger("evenements", [])
    personnages = charger("personnages", [])
    plans_brut = charger("plans", {})
    plans = plans_brut.get("plans", []) if isinstance(plans_brut, dict) else plans_brut

    noeuds, doubles = indexer(books, intentions, mains, plans, evenements,
                              personnages)
    jr = charger("journal", {})
    joueur = (jr or {}).get("personnage_joueur_id") if isinstance(jr, dict) else None
    lieux_connus = {l.get("id") for l in charger("lieux", [])
                    if isinstance(l, dict) and l.get("id")}
    aretes = tisser(books, intentions, mains, plans, evenements,
                    personnages, joueur, lieux_connus)

    genres = collections.Counter(n["genre"] for n in noeuds.values())
    print("LE TISSU")
    print("  {} noeuds : {}".format(
        len(noeuds), " · ".join("{} {}".format(v, k)
                                for k, v in genres.most_common())))
    print("  {} aretes".format(len(aretes)))
    print()

    par_nature = collections.Counter(a["nature"] for a in aretes)
    print("PAR NATURE")
    for k, v in par_nature.most_common():
        print("  {:<18} {:>5}".format(k[:18], v))
    print()

    # --- LE CHIFFRE QUI DECIDE
    suivables = [a for a in aretes if not a["flou"]]
    pend = [a for a in suivables
            if a["de"] not in noeuds or a["vers"] not in noeuds]
    resolues = len(suivables) - len(pend)
    print("L'ADRESSAGE — le chiffre qui decide de la suite")
    print("  {} aretes suivables (les autres sont en prose)".format(len(suivables)))
    print("  {} resolvent des deux cotes  ({:.0f}%)".format(
        resolues, 100.0 * resolues / max(1, len(suivables))))
    print("  {} pendantes                  ({:.0f}%)".format(
        len(pend), 100.0 * len(pend) / max(1, len(suivables))))
    print("  {} floues, presentes mais non suivables".format(
        len(aretes) - len(suivables)))
    print("  seuil de decision : au-dela de 10% de pendantes, on repare")
    print("  l'adressage avant d'aller plus loin.")
    print()

    manquants = collections.Counter()
    for a in pend:
        for bout in (a["de"], a["vers"]):
            if bout not in noeuds:
                manquants[(a["nature"], bout)] += 1
    print("CE QUI NE RESOUT PAS — les vingt premiers")
    for (nature, bout), n in manquants.most_common(20):
        print("  {:<16} -> {:<28} {}".format(nature[:16], str(bout)[:28], n))
    if doubles:
        print()
        print("ADRESSES A DEUX GENRES : {}".format(len(doubles)))
        for k, v in doubles.most_common(8):
            print("  {} ({} fois)".format(k, v))

    if args.pendantes:
        print()
        print("LES PENDANTES EN CLAIR")
        for a in pend[:60]:
            print("  [{}] {} -> {}".format(a["nature"], a["de"], a["vers"]))
            if a["texte"]:
                print("      {}".format(a["texte"]))

    if args.ecrire:
        if not os.path.isdir(SORTIE):
            os.makedirs(SORTIE)
        p = os.path.join(SORTIE, "aretes.jsonl")
        with io.open(p, "w", encoding="utf-8") as fh:
            for a in aretes:
                fh.write(json.dumps(a, ensure_ascii=False) + "\n")
        q = os.path.join(SORTIE, "noeuds.json")
        with io.open(q, "w", encoding="utf-8") as fh:
            json.dump(noeuds, fh, ensure_ascii=False, indent=1)
        print()
        print("Tissu depose : {} / {}".format(
            os.path.relpath(p, RACINE), os.path.relpath(q, RACINE)))
        print("Derive et regenerable — les fichiers restent la source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
