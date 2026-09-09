# -*- coding: utf-8 -*-
"""
regles_partie.py — le lien entre le livre de règles de la partie et le code qui
les applique, dans les deux sens.

Le livre (`docs/regles-partie.md`) donne à chaque règle une adresse : un en-tête
`**R8 · preseance-blocage**` — le numéro est l'ordre de lecture, le slug est
l'adresse. Le code porte le slug en commentaire, `# regle: <slug>` (plusieurs,
séparés par des virgules), à l'endroit exact où la règle est appliquée ou
refusée. Ce module lit les deux, et :

- `verifier()` dit ce qui manque d'un côté ou de l'autre — une règle sans
  marqueur, un marqueur sans règle, un slug doublé, une règle déclarée
  `sans code` et pourtant marquée, une ligne « où » qui n'est plus à jour ;
- `ecrire()` regénère sous chaque règle la ligne « où : `module` (`fonction`) »
  entre `<!-- ou:debut -->` et `<!-- ou:fin -->`, fonction trouvée par la `def`
  qui précède le marqueur, jamais un numéro de ligne. Idempotent.

Une règle déclarée `— sans code : <raison>` dans son en-tête est une pratique
de l'arbitre, pas une vérification du greffe : elle est listée à part et ne
fait pas échouer. Rien ici ne touche `etat/`.

Façade : `python scripts/regles.py [--verifier | --ecrire]`.
"""
import glob
import io
import os
import re

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVRE = os.path.join(RACINE, "docs", "regles-partie.md")
# Où l'on cherche les marqueurs : le moteur, ses façades, et ce qui l'écrit à
# l'écran. Ajouter un motif ici quand une règle s'applique ailleurs.
SOURCES = ("scripts/noyau/partie_*.py", "scripts/partie.py", "scripts/partie_ia.py",
           "serveur/domaine/partie.js", "ecrans/modules/partie*.js")
# L'ordre des modules dans une ligne « où » : la recevabilité, puis
# l'application, puis le tour, puis ce qui montre.
ORDRE = ("partie_validite.py", "partie_greffe.py", "partie_tour.py", "partie_lecture.py",
         "partie_cartes.py", "partie_marques.py", "partie_gestes.py")

RE_TETE = re.compile(r"\*\*([A-Z]+\d+[a-z]?) · ([a-z0-9-]+)\*\*")
RE_MARQUEUR = re.compile(r"(?:#|//)\s*regle:\s*([a-z0-9, -]+)")
RE_DEF = re.compile(r"^\s*(?:def\s+(\w+)\s*\(|(?:async\s+)?function\s+(\w+)\s*\("
                    r"|(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?(?:\(|function))")
RE_ITEM = re.compile(r"^(\s*)(\d+\.|-|\*)\s+")
DEBUT, FIN = "<!-- ou:debut -->", "<!-- ou:fin -->"


# ------------------------------------------------------------------ le livre
def lire_livre(chemin=LIVRE):
    """Les règles du livre, dans l'ordre : {code, slug, ligne, table, indent,
    sans_code, raison}. `ligne` est l'index (0-based) de l'en-tête."""
    with io.open(chemin, encoding="utf-8") as f:
        lignes = f.read().split("\n")
    return lignes, lire_livre_depuis(lignes)


def _fin_de_bloc(lignes, i, indent):
    """Le premier index après le bloc de la règle qui commence en `i` : une
    ligne vide, un autre en-tête, un titre, une table, ou un item de liste qui
    n'est pas plus profond que le nôtre."""
    j = i + 1
    while j < len(lignes):
        l = lignes[j]
        if not l.strip() or RE_TETE.search(l) or l.startswith("#") or l.lstrip().startswith("|"):
            break
        if l.strip() in (DEBUT, FIN) or DEBUT in l:
            break
        item = RE_ITEM.match(l)
        if item and len(item.group(1)) < indent:
            break
        j += 1
    return j


# ------------------------------------------------------------------- le code
def lire_marqueurs(racine=RACINE):
    """Tous les marqueurs du code : [{slug, fichier, fonction, ligne}], dans
    l'ordre des fichiers puis des lignes. `fonction` est le nom de la `def` (ou
    `function`) qui précède, `None` au niveau du module."""
    out = []
    fichiers = []
    for motif in SOURCES:
        fichiers += sorted(glob.glob(os.path.join(racine, *motif.split("/"))))
    for chemin in fichiers:
        with io.open(chemin, encoding="utf-8") as f:
            lignes = f.read().split("\n")
        courante = None
        for i, l in enumerate(lignes):
            d = RE_DEF.match(l)
            if d:
                courante = next(g for g in d.groups() if g)
            m = RE_MARQUEUR.search(l)
            if not m:
                continue
            for slug in (s.strip() for s in m.group(1).split(",")):
                if slug:
                    out.append({"slug": slug, "fichier": os.path.basename(chemin),
                                "fonction": courante, "ligne": i + 1})
    return out


# ------------------------------------------------------------- la ligne « où »
def _ou(regle, marqueurs):
    if regle["sans_code"]:
        return "où : sans code (la raison est dans l'en-tête)"
    par_module = {}
    for m in marqueurs:
        if m["slug"] != regle["slug"]:
            continue
        fns = par_module.setdefault(m["fichier"], [])
        nom = m["fonction"] or "module"
        if nom not in fns:
            fns.append(nom)
    if not par_module:
        return "où : AUCUN MARQUEUR"
    rang = lambda f: (ORDRE.index(f) if f in ORDRE else len(ORDRE), f)
    return "où : " + ", ".join("`%s` (%s)" % (f, ", ".join("`%s`" % x for x in par_module[f]))
                               for f in sorted(par_module, key=rang))


def _sans_blocs(lignes):
    """Le livre sans ses blocs générés — ce sur quoi on regénère."""
    out, dedans = [], False
    for l in lignes:
        if l.strip() == DEBUT:
            dedans = True
            continue
        if l.strip() == FIN:
            dedans = False
            continue
        if not dedans:
            out.append(l)
    return out


def livre_regenere(lignes, regles, marqueurs):
    """Le texte du livre avec ses blocs « où » à jour. Une règle de liste reçoit
    son bloc sous son item, à l'indentation de l'item ; les règles d'une même
    table reçoivent un seul bloc sous la table, une ligne par règle."""
    lignes = _sans_blocs(lignes)
    regles = lire_livre_depuis(lignes)
    insertions = {}   # index d'insertion -> lignes
    for r in regles:
        if r["table"]:
            j = r["ligne"]
            while j < len(lignes) and lignes[j].lstrip().startswith("|"):
                j += 1
            insertions.setdefault(j, []).append("- `%s` — %s" % (r["slug"], _ou(r, marqueurs)))
        else:
            j = _fin_de_bloc(lignes, r["ligne"], r["indent"])
            pad = " " * r["indent"]
            insertions.setdefault(j, []).append(pad + _ou(r, marqueurs))
    out = []
    for i, l in enumerate(lignes):
        if i in insertions:
            pad = re.match(r"\s*", insertions[i][0]).group(0) if not insertions[i][0].startswith("- ") else ""
            out += [pad + DEBUT] + insertions[i] + [pad + FIN]
        out.append(l)
    if len(lignes) in insertions:
        out += [DEBUT] + insertions[len(lignes)] + [FIN]
    return "\n".join(out)


def lire_livre_depuis(lignes):
    """Les règles lues sur des lignes déjà en mémoire (voir `lire_livre`)."""
    regles = []
    for i, l in enumerate(lignes):
        for m in RE_TETE.finditer(l):
            item = RE_ITEM.match(l)
            indent = (len(item.group(1)) + len(item.group(2)) + 1) if item else 0
            bloc = " ".join(x.strip() for x in lignes[i:_fin_de_bloc(lignes, i, indent)])
            sc = re.search(r"sans code\s*:\s*(.+?)(?:\.(?:\s|$)|\|)", bloc)
            regles.append({"code": m.group(1), "slug": m.group(2), "ligne": i,
                           "table": l.lstrip().startswith("|"), "indent": indent,
                           "sans_code": sc is not None,
                           "raison": sc.group(1).strip() if sc else ""})
    return regles


# ------------------------------------------------------------------ vérifier
def verifier(chemin=LIVRE, racine=RACINE):
    """Rend (erreurs, sans_code, compte). `erreurs` vide = tout se tient."""
    lignes, regles = lire_livre(chemin)
    marqueurs = lire_marqueurs(racine)
    erreurs = []
    slugs = [r["slug"] for r in regles]
    for s in sorted(set(s for s in slugs if slugs.count(s) > 1)):
        erreurs.append("slug doublé dans le livre : %s" % s)
    codes = [r["code"] for r in regles]
    for c in sorted(set(c for c in codes if codes.count(c) > 1)):
        erreurs.append("numéro doublé dans le livre : %s" % c)
    marques = set(m["slug"] for m in marqueurs)
    for r in regles:
        if r["sans_code"] and r["slug"] in marques:
            erreurs.append("%s · %s est déclarée sans code et pourtant marquée" % (r["code"], r["slug"]))
        elif not r["sans_code"] and r["slug"] not in marques:
            erreurs.append("règle sans marqueur : %s · %s" % (r["code"], r["slug"]))
    for m in marqueurs:
        if m["slug"] not in slugs:
            erreurs.append("marqueur sans règle : %s (%s, %s, ligne %d)"
                           % (m["slug"], m["fichier"], m["fonction"] or "module", m["ligne"]))
    if livre_regenere(lignes, regles, marqueurs) != "\n".join(lignes):
        erreurs.append("les lignes « où » du livre ne sont plus à jour : python scripts/regles.py --ecrire")
    sans_code = [r for r in regles if r["sans_code"]]
    return erreurs, sans_code, {"regles": len(regles), "marqueurs": len(marqueurs),
                                "fichiers": len(set(m["fichier"] for m in marqueurs))}


def ecrire(chemin=LIVRE, racine=RACINE):
    """Regénère les blocs « où » du livre. Rend True si le fichier a changé."""
    lignes, regles = lire_livre(chemin)
    neuf = livre_regenere(lignes, regles, lire_marqueurs(racine))
    if neuf == "\n".join(lignes):
        return False
    with io.open(chemin, "w", encoding="utf-8", newline="") as f:
        f.write(neuf)
    return True


def main(argv):
    if "--ecrire" in argv:
        print("livre " + ("réécrit" if ecrire() else "déjà à jour") + " : " + os.path.relpath(LIVRE, RACINE))
        argv = [a for a in argv if a != "--ecrire"] + ["--verifier"]
    erreurs, sans_code, compte = verifier()
    print("%d règles nommées, %d marqueurs dans %d fichiers, %d sans code"
          % (compte["regles"], compte["marqueurs"], compte["fichiers"], len(sans_code)))
    if "--lister" in argv:
        _, regles = lire_livre()
        for r in regles:
            print("  %-5s %s%s" % (r["code"], r["slug"], " (sans code)" if r["sans_code"] else ""))
    if sans_code:
        print("sans code, listées à part :")
        for r in sans_code:
            print("  %s · %s — %s" % (r["code"], r["slug"], r["raison"]))
    if erreurs:
        print("NON — %d écart(s) entre le livre et le code" % len(erreurs))
        for e in erreurs:
            print("  " + e)
        return 1
    print("regles : OK")
    return 0
