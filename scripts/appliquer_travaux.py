# -*- coding: utf-8 -*-
# APPLIQUER LES TRAVAUX — verser dans etat/books.json ce que les hommes ont
# ecrit dans leurs cahiers pendant leur journee.
#
# POURQUOI CE SCRIPT EXISTE, et c'est une faute reparee. La regle est bonne :
# un agent n'ecrit jamais dans `etat/`, il propose dans `etat/staging/`, et le
# MJ arbitre — un seul ecrivain, jamais de course. Mais une proposition sans
# etape d'application ne vaut rien : le 28e de la 3e lune, neuf hommes ont
# travaille cinq heures chacun et rendu 120 changements de cahier, et
# `books.json` n'a pas bouge d'une ligne. Le travail existait dans des fichiers
# que personne ne lit. `appliquer.py` ne sait lire que les mutations de
# `tick.py` ; il fallait celui-ci.
#
# CE QU'IL SAIT FAIRE, ET CE QU'IL REFUSE DE DEVINER. Une entree dit son livre,
# sa ligne (entre guillemets) et sa colonne. Le script les resout par le TEXTE
# — pas par un numero, qui n'existe pas dans ces fichiers. Quand la resolution
# est ambigue, il ne tranche pas : il laisse l'entree en attente et la nomme.
# Un cahier a moitie ecrit de travers est pire qu'un cahier pas ecrit.
#
# Usage :
#     python scripts/appliquer_travaux.py                  ce qui serait fait
#     python scripts/appliquer_travaux.py --vraiment       ecrit
#     python scripts/appliquer_travaux.py --qui gerardys
#     python scripts/appliquer_travaux.py --reste          les non resolues seulement
import argparse
import io
import json
import os
import re
import sys
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
STAGING = os.path.join(ETAT, "staging", "travaux")


def plat(t):
    """Sans accents, sans casse, sans ponctuation : pour comparer des libelles."""
    t = unicodedata.normalize("NFD", t or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def entre_guillemets(t):
    """Les segments cites dans `ou` : « ... », " ... ", ' ... '."""
    out = []
    for motif in (r"«\s*(.+?)\s*»", r"“\s*(.+?)\s*”", r"\"(.+?)\""):
        out += re.findall(motif, t or "")
    return [x for x in out if len(x) > 2]


def charger(nom):
    p = os.path.join(ETAT, nom + ".json")
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def tables_de(livre):
    """Toutes les grilles d'un livre : la sienne, ou celles de ses `tables`.

    Un cahier d'affaire (`type: plan`) ne porte pas de colonnes au sommet : il
    porte plusieurs tables, chacune avec les siennes. Ne regarder que le sommet
    faisait refuser 115 propositions sur 120 — la faute etait ici, pas chez les
    hommes qui les avaient ecrites.
    """
    out = []
    if livre.get("colonnes"):
        out.append((livre.get("titre") or "", livre["colonnes"],
                    livre.setdefault("lignes", [])))
    for t in livre.get("tables") or []:
        if t.get("colonnes"):
            out.append((t.get("titre") or "", t["colonnes"],
                        t.setdefault("lignes", [])))
    return out


def viser(livre, ou):
    """Resout (colonnes, lignes, i, j) depuis le texte de `ou`.

    On cherche la ligne sur TOUTES ses cellules, pas seulement la premiere :
    un homme cite volontiers le numero d'une action, qui vit au milieu du rang.
    Rend (cible, motif) ; cible est None si c'est ambigu ou introuvable.
    """
    cites = [c for c in entre_guillemets(ou) if len(plat(c)) >= 4]
    # Les numeros d'action cites hors guillemets comptent aussi.
    cites += re.findall(r"\d{4,6}", ou or "")
    if not cites:
        return None, "rien de cite dans `ou`"

    grilles = tables_de(livre)
    if not grilles:
        return None, "ce livre ne porte aucune grille"

    # Une table peut etre nommee : on restreint si c'est le cas.
    restreint = [g for g in grilles
                 if any(plat(c) and plat(c) in plat(g[0]) for c in cites)]
    if restreint:
        grilles = restreint

    trouves = []
    for titre, colonnes, lignes in grilles:
        for i, l in enumerate(lignes):
            cellules = l.get("cellules") or []
            entier = plat(" | ".join(str(x) for x in cellules))
            for c in cites:
                pc = plat(c)
                if pc and len(pc) >= 4 and pc in entier:
                    trouves.append((titre, colonnes, lignes, i))
                    break
    vus, uniques = set(), []
    for t in trouves:
        cle = (t[0], t[3])
        if cle not in vus:
            vus.add(cle); uniques.append(t)
    if not uniques:
        return None, "aucune ligne ne porte ce qui est cite"
    if len(uniques) > 1:
        return None, "ambigu : {} lignes correspondent".format(len(uniques))

    titre, colonnes, lignes, i = uniques[0]
    js = []
    for c in cites:
        pc = plat(c)
        for j, nom in enumerate(colonnes):
            n = plat(nom)
            if pc and n and (pc in n or n in pc):
                js.append(j)
    js = sorted(set(js))
    if len(js) != 1:
        return (titre, colonnes, lignes, i, None), (
            "ligne trouvee, colonne " +
            ("ambigue" if js else "introuvable"))
    return (titre, colonnes, lignes, i, js[0]), "resolu"


# ------------------------------------------------------- LE FORMAT EN CLAIR
# `cahier2` : la meme chose, mais adressee. Pas d'heuristique, pas de devinette
# — on compare des chaines recopiees. Ce qui ne tombe pas juste est refuse et
# nomme, jamais approche. C'est le format qui rend le versement automatique ;
# la prose de `cahier` ne l'a jamais permis, et 95 changements sur 120 sont
# restes dans un fichier que personne ne lit.

def titre_nu(t):
    """Un titre sans sa decoration. Les tables s'appellent « 🔒 Verrous » et un
    homme recopie « Verrous » : quatre entrees sur quatre du Sanglier ont ete
    refusees la-dessus. Le refus etait juste — c'est la comparaison qui etait
    bete. Deux tables d'un meme volume ne different jamais par leur seul
    emoji, donc le retirer ne cree aucune ambiguite ; et si jamais il en
    creait une, `grille_nommee` refuse toujours plutot que de trancher.
    """
    import unicodedata as _u
    t = str(t or "")
    while t and not (t[0].isalnum() or _u.category(t[0]).startswith("L")):
        t = t[1:]
    return t.strip().lower()


def grille_nommee(livre, titre):
    """La grille visee par son titre — ou la seule qu'il y ait.

    Un volume peut ne porter qu'un tableau anonyme (`colonnes`/`lignes` au
    sommet, sans `tables`). Alors `table: null` est la reponse honnete, pas un
    oubli : il n'y a rien a recopier. On ne refuse donc pas — on prend la seule.
    """
    grilles = tables_de(livre)
    t_cherche = (titre or "").strip()
    if not t_cherche:
        return (grilles[0][1], grilles[0][2]) if len(grilles) == 1 else (None, None)
    for t, colonnes, lignes in grilles:
        if (t or "").strip() == t_cherche:
            return colonnes, lignes
    # Puis sans la decoration — mais seulement si UNE SEULE grille correspond.
    nu_cherche = titre_nu(t_cherche)
    proches = [(c, l) for t, c, l in grilles if titre_nu(t) == nu_cherche]
    if len(proches) == 1:
        return proches[0]
    return None, None


def champ_libre(livre, e, faire, qui):
    """Les cibles qui ne sont pas des cellules : `sous_titre`, une `page`.

    Un cahier n'est pas qu'une grille. Refuser ces cibles obligerait un homme a
    tordre sa proposition pour entrer dans mon format, ce qui est l'inverse du
    but. Rend (fait, motif) — fait est None si ce n'est pas un champ libre.
    """
    cible = (e.get("colonne") or e.get("table") or "").strip().lower()
    if cible in ("sous_titre", "sous-titre"):
        avant = livre.get("sous_titre") or ""
        if faire:
            livre["sous_titre"] = e.get("valeur") or ""
        return {"qui": qui, "livre": livre.get("id"), "quoi": "corriger",
                "ligne": "(sous-titre du volume)", "colonne": "sous_titre",
                "remplaçait": avant, "apres": e.get("valeur") or ""}, None
    if cible in ("pages", "page"):
        pages = livre.setdefault("pages", [])
        vise = (e.get("ligne") or "").strip()
        for i, pg in enumerate(pages):
            if str(pg).strip() == vise:
                if faire:
                    pages[i] = e.get("valeur") or ""
                return {"qui": qui, "livre": livre.get("id"), "quoi": "corriger",
                        "ligne": vise[:48], "colonne": "page",
                        "remplaçait": str(pg)[:60]}, None
        if (e.get("quoi") or "").strip().lower() == "ajouter" or not vise:
            if faire:
                pages.append(e.get("valeur") or "")
            return {"qui": qui, "livre": livre.get("id"), "quoi": "ajouter",
                    "ligne": "(page neuve)", "colonne": "page",
                    "remplaçait": ""}, None
        return None, "aucune page ne porte exactement ce texte"
    return None, None


def appliquer2(entrees, books, faire):
    index = {b.get("id"): b for b in books if isinstance(b, dict)}
    faits, restes = [], []
    for e in entrees:
        qui, lid = e["_qui"], e.get("livre")
        quoi = (e.get("quoi") or "").strip().lower()

        def refus(motif):
            restes.append(dict(e, _motif=motif))

        if e.get("introuvable"):
            refus("declare introuvable par lui-meme : {}".format(
                str(e["introuvable"])[:70])); continue
        livre = index.get(lid)
        if livre is None:
            refus("livre inconnu : {}".format(lid)); continue
        if quoi == "creer_table":
            titre = (e.get("table") or "").strip()
            cols = e.get("colonnes")
            if not titre or not isinstance(cols, list) or not cols:
                refus("creation de table sans titre ou sans colonnes"); continue
            if grille_nommee(livre, titre)[0] is not None:
                refus("cette table existe deja : {}".format(titre[:40])); continue
            # On la cree TOUJOURS en memoire, meme a blanc : sinon les lignes
            # qui la visent juste apres seraient comptees comme perdues, et le
            # rapport mentirait sur ce qui passe.
            livre.setdefault("tables", []).append(
                {"titre": titre, "colonnes": list(cols), "lignes": []})
            faits.append({"qui": qui, "livre": lid, "quoi": "table neuve",
                          "ligne": "{} colonnes".format(len(cols)),
                          "colonne": titre, "remplaçait": "",
                          "apres": ", ".join(str(c) for c in cols)})
            continue

        fait, motif = champ_libre(livre, e, faire, qui)
        if fait is not None:
            faits.append(fait); continue
        if motif:
            refus(motif); continue
        colonnes, lignes = grille_nommee(livre, e.get("table"))
        if colonnes is None:
            refus("aucune table de ce titre exact : {}".format(
                (e.get("table") or "")[:50])); continue

        if quoi == "ajouter":
            cells = e.get("cellules")
            if not isinstance(cells, list):
                refus("ajout sans `cellules`"); continue
            if len(cells) != len(colonnes):
                refus("ajout : {} cellules pour {} colonnes".format(
                    len(cells), len(colonnes))); continue
            # GARDE D'IDEMPOTENCE. Une correction reecrite a l'identique ne
            # coute rien ; un ajout rejoue DOUBLE la ligne. Sans ceci, relancer
            # le versement une seconde fois dedouble tout ce qui a ete cree —
            # et un cahier a lignes doubles ne se relit plus.
            tete = str(cells[0]).strip()
            if any(str((l.get("cellules") or [""])[0]).strip() == tete
                   for l in lignes):
                refus("deja pose : une ligne porte deja « {} »".format(tete[:40]))
                continue
            if faire:
                lignes.append({"cellules": [str(c) for c in cells]})
            faits.append({"qui": qui, "livre": lid, "quoi": "ajouter",
                          "ligne": str(cells[0])[:48], "colonne": e.get("table"),
                          "remplaçait": "",
                          "apres": " | ".join(str(c) for c in cells)})
            continue

        cible = None
        vise = (e.get("ligne") or "").strip()
        for i, l in enumerate(lignes):
            c0 = (l.get("cellules") or [""])[0]
            if str(c0).strip() == vise:
                cible = i
                break
        if cible is None:
            # PUIS PAR LE NUMERO. Un homme ecrit « 25012 — Le Guet n'est pas
            # coordonne » la ou la cellule dit « **25012** » : il a recopie le
            # numero ET ce que la ligne raconte. L'identite d'une ligne est son
            # numero, le reste est de la prose. On ne le devine que si UNE
            # SEULE ligne de la grille porte ce numero ; sinon on refuse,
            # comme avant.
            n = re.match(r"\**\s*(\d{3,6})", vise)
            if n:
                memes = [i for i, l in enumerate(lignes)
                         if re.match(r"\**\s*" + n.group(1) + r"",
                                     str((l.get("cellules") or [""])[0]).strip())]
                if len(memes) == 1:
                    cible = memes[0]
        if cible is None:
            refus("aucune ligne dont la premiere cellule soit exactement : {}"
                  .format((e.get("ligne") or "")[:50])); continue

        if quoi == "retirer":
            if faire:
                lignes[cible]["note"] = (
                    "RETIREE le 28e j., 3e lune, an 129, de la main de {} — {}"
                    .format(qui, e.get("valeur") or ""))[:1200]
            faits.append({"qui": qui, "livre": lid,
                          "quoi": "retirer (marquee, non effacee)",
                          "ligne": (e.get("ligne") or "")[:48],
                          "colonne": "note", "remplaçait": "",
                          "apres": e.get("valeur") or ""})
            continue

        j = None
        for k, nom in enumerate(colonnes):
            if str(nom).strip() == (e.get("colonne") or "").strip():
                j = k
                break
        if j is None:
            refus("aucune colonne dont l'en-tete soit exactement : {}"
                  .format((e.get("colonne") or "")[:50])); continue

        cellules = lignes[cible].setdefault("cellules", [])
        while len(cellules) < len(colonnes):
            cellules.append("")
        avant = cellules[j]
        if faire:
            cellules[j] = e.get("valeur") or ""
        faits.append({"qui": qui, "livre": lid, "quoi": quoi,
                      "ligne": (e.get("ligne") or "")[:48],
                      "colonne": colonnes[j], "remplaçait": str(avant),
                      "apres": e.get("valeur") or ""})
    return faits, restes


def appliquer(entrees, books, faire):
    # ECRITURE INTERDITE, et ce n'est pas une precaution : le 28e, ce chemin a
    # ecrit six valeurs dans la colonne du NUMERO au lieu de la colonne visee,
    # parce qu'il resout la colonne par ressemblance. Un plan de guerre a
    # moitie ecrit de travers est pire qu'un plan pas ecrit. Ce chemin ne sert
    # plus qu'a MONTRER ce qui n'a pas ete reemis en coordonnees.
    faire = False
    index = {b.get("id"): b for b in books if isinstance(b, dict)}
    faits, restes = [], []

    for e in entrees:
        qui, lid = e["_qui"], e.get("livre")
        quoi = (e.get("quoi") or "").strip().lower()
        ou, texte = e.get("ou") or "", e.get("texte") or ""
        livre = index.get(lid)

        def refus(motif):
            restes.append(dict(e, _motif=motif))

        if livre is None:
            refus("livre inconnu : {}".format(lid)); continue
        if not tables_de(livre):
            refus("ce livre ne porte aucune grille ({})".format(
                livre.get("type") or "?")); continue

        if quoi in ("corriger", "conclusion"):
            cible, motif = viser(livre, ou)
            if cible is None or cible[4] is None:
                refus(motif); continue
            titre, colonnes, lignes, i, j = cible
            cellules = lignes[i].setdefault("cellules", [])
            while len(cellules) < len(colonnes):
                cellules.append("")
            avant = cellules[j]
            if faire:
                cellules[j] = texte
            faits.append({"qui": qui, "livre": lid, "quoi": quoi,
                          "ligne": (str(cellules[0]) or "")[:48],
                          "colonne": colonnes[j],
                          "remplaçait": (str(avant) or "")[:60]})
            continue

        if quoi == "retirer":
            cible, motif = viser(livre, ou)
            if cible is None:
                refus(motif); continue
            titre, colonnes, lignes, i, _j = cible
            # On ne SUPPRIME jamais : une ligne morte garde sa place et dit
            # pourquoi elle est morte. Un plan dont on efface les renoncements
            # se refait deux fois.
            l = lignes[i]
            if faire:
                l["note"] = ("RETIRÉE le 28e j., 3e lune, an 129, de la main de "
                             "{} — {}".format(qui, texte))[:1200]
            faits.append({"qui": qui, "livre": lid, "quoi": "retirer (marquee, non effacee)",
                          "ligne": (l.get("cellules") or [""])[0][:48],
                          "colonne": "note", "remplaçait": ""})
            continue

        if quoi == "ajouter":
            # Une ligne neuve doit se decouper en cellules, et la prose d'un
            # homme ne le dit pas. On refuse plutot que d'aligner au hasard.
            refus("ajout d'une ligne : le decoupage en colonnes n'est pas dans "
                  "la proposition — a poser a la main")
            continue

        refus("verbe inconnu : {}".format(quoi))

    return faits, restes


def sceau(chemin):
    import hashlib
    if not os.path.isfile(chemin):
        return None
    with io.open(chemin, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def journaliser_registres(faits, faire):
    """LE JOURNAL DES REGISTRES — qui a change quelle cellule, et en quoi.

    POURQUOI. `books.json` ne porte AUCUNE provenance : pas de date, pas
    d'auteur, pas d'historique. Cent dix-neuf volumes, trois mille cent
    vingt-trois lignes, et rien qui dise d'ou vient une valeur ni ce qu'elle a
    remplace. Les seules traces existantes sont quatre instantanes pris a la
    main dans `etat/archive/` aux moments dangereux — dont l'un s'appelle
    `books-corrompu-par-heuristique-28e.json`, ce qui dit assez pourquoi on en
    veut une systematique.

    Le cout est nul : `appliquer2` connait deja l'auteur, la coordonnee exacte,
    et la valeur qu'il ecrase. Il ne manquait que la ligne posee et le fichier
    ou l'ecrire.

    On ne journalise que ce qui CHANGE quelque chose : reappliquer un
    versement reecrit les memes valeurs, et un journal plein de non-evenements
    ne se relit plus.
    """
    if not faits:
        return []
    chemin = os.path.join(ETAT, "registres.jsonl")
    monde = {}
    p = os.path.join(ETAT, "monde.json")
    if os.path.isfile(p):
        try:
            with io.open(p, encoding="utf-8") as fh:
                monde = json.load(fh)
        except ValueError:
            monde = {}
    jour = monde.get("date") or {}
    jour = {k: jour.get(k) for k in ("annee", "lune", "jour")}

    lignes = []
    for f in faits:
        avant, apres = str(f.get("remplaçait") or ""), str(f.get("apres") or "")
        if avant.strip() == apres.strip():
            continue
        lignes.append({
            "type": "registre", "jour": jour, "qui": f.get("qui"),
            "livre": f.get("livre"), "quoi": f.get("quoi"),
            "table": f.get("colonne") if f.get("quoi") == "ajouter" else None,
            "ligne": f.get("ligne"), "colonne": f.get("colonne"),
            "avant": avant, "apres": apres,
        })
    if faire and lignes:
        with io.open(chemin, "a", encoding="utf-8") as fh:
            for o in lignes:
                fh.write(json.dumps(o, ensure_ascii=False) + "\n")
    return lignes


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vraiment", action="store_true")
    ap.add_argument("--qui")
    ap.add_argument("--reste", action="store_true")
    args = ap.parse_args()

    entrees, entrees2 = [], []
    for nom in sorted(os.listdir(STAGING)):
        if not nom.endswith(".json"):
            continue
        qui = nom[:-5]
        if args.qui and qui != args.qui:
            continue
        with io.open(os.path.join(STAGING, nom), encoding="utf-8") as fh:
            s = json.load(fh)
        for e in s.get("cahier") or []:
            entrees.append(dict(e, _qui=qui))
        for e in s.get("cahier2") or []:
            entrees2.append(dict(e, _qui=qui))

    chemin_books = os.path.join(ETAT, "books.json")
    avant_books = sceau(chemin_books)
    books = charger("books")
    # Le format adresse d'abord : il est sur. La prose ensuite, et seulement
    # pour ce que personne n'a reemis en coordonnees.
    faits2, restes2 = appliquer2(entrees2, books, args.vraiment)
    deja = {(f["qui"], f["livre"], f["ligne"], f["colonne"]) for f in faits2}
    faits1, restes1 = appliquer([e for e in entrees], books, False)
    faits, restes = faits2, restes2
    if entrees2:
        print("EN COORDONNEES : {} appliques sur {} proposes.".format(
            len(faits2), len(entrees2)))
    else:
        faits, restes = appliquer(entrees, books, args.vraiment)

    if not args.reste:
        print("APPLICABLES : {} sur {}".format(len(faits), len(entrees)))
        for f in faits:
            print("  {:<16} {:<32} {}".format(
                f["qui"], f["livre"][:32], f["colonne"]))
            print("      {} — {}".format(f["quoi"], f["ligne"]))
        print()

    print("EN ATTENTE, a poser a la main : {}".format(len(restes)))
    for r in restes:
        print("  {:<16} {:<32} {}".format(
            r["_qui"], (r.get("livre") or "?")[:32], r["_motif"]))
        print("      {}".format((r.get("ou") or "")[:100]))

    trace = journaliser_registres(faits, args.vraiment)
    if trace:
        print()
        print("JOURNAL DES REGISTRES : {} changement(s) reel(s) vers "
              "etat/registres.jsonl".format(len(trace)))

    if args.vraiment:
        # Meme filet que verser_travaux.py : la session qui joue ecrit aussi
        # dans books.json, et ce script le reecrit EN ENTIER.
        if sceau(chemin_books) != avant_books:
            print("\nREFUSE : etat/books.json a bouge pendant le calcul — "
                  "une autre session ecrit. Relance, rien n'a ete touche.")
            return 1

        # L'INSTANTANE D'AVANT. Le journal dit quelle cellule a change ; il ne
        # rend pas un volume qu'on aurait abime en gros. Les quatre fichiers
        # `books-avant-*.json` de `etat/archive/` ont ete pris a la main, aux
        # moments ou l'on a senti le danger — dont un nomme
        # `books-corrompu-par-heuristique-28e`. On arrete de compter sur le
        # flair : chaque versement garde son avant.
        arch = os.path.join(ETAT, "archive", "books")
        if not os.path.isdir(arch):
            os.makedirs(arch)
        d = {}
        pm = os.path.join(ETAT, "monde.json")
        if os.path.isfile(pm):
            try:
                with io.open(pm, encoding="utf-8") as fh:
                    d = json.load(fh).get("date") or {}
            except ValueError:
                d = {}
        base = "avant-{}-{}-{}".format(d.get("annee"), d.get("lune"),
                                       d.get("jour"))
        n, cible = 1, os.path.join(arch, base + ".json")
        while os.path.isfile(cible):
            n += 1
            cible = os.path.join(arch, "{}-{}.json".format(base, n))
        with io.open(chemin_books, encoding="utf-8") as src:
            contenu = src.read()
        with io.open(cible, "w", encoding="utf-8") as dst:
            dst.write(contenu)

        with io.open(chemin_books, "w", encoding="utf-8") as fh:
            json.dump(books, fh, ensure_ascii=False, indent=1)
        print("\netat/books.json ecrit — {} cellules. Avant garde dans {}."
              .format(len(faits), os.path.relpath(cible, RACINE)))
    else:
        print("\nRien n'a ete ecrit. --vraiment pour appliquer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
