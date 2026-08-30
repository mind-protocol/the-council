# -*- coding: utf-8 -*-
"""CHAMBRE — le domicile d'un habitant (docs/habitant.md §2).

LA SEULE REGLE, ET ELLE EST DE GEOGRAPHIE : RIEN DANS chambres/ NE FAIT FOI.
La chambre est de la memoire et du caractere ; la verite vit dans etat/, et
tout ce qui doit devenir vrai passe par la porte (tables, versements,
staging). Une chambre peut se tromper sur le monde — c'est meme son droit.

Tout ce qui pense a une chambre : les hommes, les MJ de zone (mj,
mj-peyredragon…), le MJ du joueur. Memes fonctions pour tous, aucune branche
speciale — un MJ sans fiche dans personnages.json recoit simplement un cahier
plus nu.

    chambres/<id>/
       claude.md            sa maniere, DE SA MAIN — seedee UNE FOIS depuis la
                            fiche, plus jamais touchee par nous
       fil/                 les traces de ses sessions
       books/               ses volumes, sous sa main
       brouillons/          l'iteratif — ce qui murit avant de se verser
       relations/<autre>/
          claude.md         ce que LUI retient de l'autre (subjectif)
          discussion.json   le canal — canonique chez l'un des deux
          .lu               le curseur de lecture de CE cote-ci du canal
"""
import io
import json
import os

from etat.expose import tables  # LA PORTE de etat/ — meme pour une lecture

# Deux etages au-dessus : scripts/agents/ -> la racine du depot.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CHAMBRES = os.path.join(RACINE, "chambres")

DOSSIERS = ("fil", "books", "brouillons", "relations")

ENTETE = u"Ce cahier est à moi. Je l'amende quand ma journée me contredit."


def chemin(qui):
    """Le domicile de cet habitant : chambres/<qui>/, a la racine du depot."""
    return os.path.join(CHAMBRES, qui)


def _fiche(qui):
    """La fiche de personnages.json, ou {} — un MJ n'en a pas, et c'est bien."""
    donnees = tables.lire(os.path.join(RACINE, "etat", "personnages.json"), [])
    if isinstance(donnees, dict):
        donnees = donnees.get("personnages") or []
    return next((p for p in donnees
                 if isinstance(p, dict) and p.get("id") == qui), {})


def _voix(fiche):
    """La maniere ecrite AVANT les ajouts doctrinaux universels — meme coupe
    que depeche/brief.py : la voix seedee est la sienne, pas le manuel de
    conduite qu'on a colle a tout le monde."""
    texte = str((fiche or {}).get("maniere") or "").strip()
    marqueurs = (
        " Se debrouille seul", " Se débrouille seul", " Competent :",
        " Compétent :", " OUVRE PAR :", " DEUXIEME PHRASE",
        " REPRIS,", " AUCUNE ",
    )
    coupures = [texte.find(m) for m in marqueurs if texte.find(m) >= 0]
    if coupures:
        texte = texte[:min(coupures)].strip()
    return texte


def _seed(qui):
    """Le gabarit du premier claude.md — court, a la premiere personne,
    sur le ton de chambres/gerardys/claude.md. Ecrit UNE FOIS ; ensuite
    c'est sa main, et sa derive est la personnalite qui evolue."""
    fiche = _fiche(qui)
    nom = fiche.get("nom") or qui
    lignes = [u"# Ma manière — %s" % nom, u"", ENTETE, u""]
    corps = []
    for t in fiche.get("traits") or []:
        corps.append(u"- %s" % t)
    voix = _voix(fiche)
    if voix:
        corps.append(u"- %s" % voix)
    if corps:
        lignes.append(u"Ce qu'on disait de moi le jour où ce cahier s'ouvre "
                      u"— à moi d'écrire la suite :")
        lignes.append(u"")
        lignes += corps
    else:
        lignes.append(u"Ce cahier s'ouvre vide. Ma manière s'écrira ici, "
                      u"journée après journée.")
    lignes.append(u"")
    return u"\n".join(lignes)


def ouvrir(qui):
    """Cree l'arborescence SI ABSENTE et rend le chemin de la chambre.

    Le claude.md est seede une fois depuis la fiche ; s'il existe deja, on
    n'y touche JAMAIS — c'est sa main. Idempotent : rouvrir une chambre
    vivante ne change rien.
    """
    dossier = chemin(qui)
    for d in DOSSIERS:
        os.makedirs(os.path.join(dossier, d), exist_ok=True)
    cahier = os.path.join(dossier, "claude.md")
    if not os.path.exists(cahier):
        with io.open(cahier, "w", encoding="utf-8", newline="\n") as f:
            f.write(_seed(qui))
    return dossier


def canal(a, b):
    """Le chemin canonique du discussion.json de la paire — et il n'y en a
    QU'UN : chez le premier des deux dans l'ordre lexical, sous
    relations/<autre>/. L'autre y accede par ce meme chemin.

    Cree les deux relations/<autre>/ (chacun a son cote : sa fiche sur
    l'autre, son curseur .lu). Tolerance de migration : si le fichier
    canonique n'existe pas mais que la paire a deja un discussion.json chez
    le second (les chambres posees a la main avant cette regle), c'est LUI
    qu'on rend — un canal ne se coupe pas en deux fichiers. La migration
    douce (chantier, pas 7) le ramenera au canonique.
    """
    premier, second = sorted((a, b))
    cote_premier = os.path.join(chemin(premier), "relations", second)
    cote_second = os.path.join(chemin(second), "relations", premier)
    os.makedirs(cote_premier, exist_ok=True)
    os.makedirs(cote_second, exist_ok=True)
    canonique = os.path.join(cote_premier, "discussion.json")
    herite = os.path.join(cote_second, "discussion.json")
    if not os.path.exists(canonique) and os.path.exists(herite):
        return herite
    return canonique


def _entrees(fichier):
    if not os.path.exists(fichier):
        return []
    with io.open(fichier, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("entrees") or [] if isinstance(d, dict) else []


def _curseur(qui, autre):
    """Le fichier .lu de SON cote : combien d'entrees du canal il a deja
    vues. Un entier nu — le plus simple qui tienne."""
    return os.path.join(chemin(qui), "relations", autre, ".lu")


def non_lus(qui):
    """Les entrees de ses canaux adressees a lui et posterieures a son
    dernier reveil — ce que le brief injecte en percept (« Untel t'a
    ecrit : "…" », jamais une invitation a ouvrir un fichier).

    Rend [{avec, de, date, heure, texte}], dans l'ordre des canaux puis des
    entrees. Ne bouge PAS le curseur : c'est `marquer_lus` qui grave le
    reveil, une fois le brief servi.
    """
    base = os.path.join(chemin(qui), "relations")
    if not os.path.isdir(base):
        return []
    nouveaux = []
    for autre in sorted(os.listdir(base)):
        if not os.path.isdir(os.path.join(base, autre)):
            continue
        entrees = _entrees(canal(qui, autre))
        lu = 0
        c = _curseur(qui, autre)
        if os.path.exists(c):
            try:
                with io.open(c, encoding="utf-8") as f:
                    lu = int(f.read().strip() or 0)
            except (ValueError, OSError):
                lu = 0
        for e in entrees[lu:]:
            if e.get("de") != qui:
                nouveaux.append({"avec": autre, "de": e.get("de"),
                                 "date": e.get("date"),
                                 "heure": e.get("heure"),
                                 "texte": e.get("texte")})
    return nouveaux


def marquer_lus(qui):
    """Avance tous ses curseurs a la fin des canaux : son reveil a tout vu.
    A appeler quand le brief est parti — pas avant, pour qu'un lancement
    qui echoue ne mange pas les billets."""
    base = os.path.join(chemin(qui), "relations")
    if not os.path.isdir(base):
        return
    for autre in sorted(os.listdir(base)):
        if not os.path.isdir(os.path.join(base, autre)):
            continue
        n = len(_entrees(canal(qui, autre)))
        with io.open(_curseur(qui, autre), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(u"%d" % n)
