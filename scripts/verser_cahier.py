# -*- coding: utf-8 -*-
# Verse les `cahier2` des rapports dans etat/books.json — les changements de
# registre qu'un homme depeche a rapportes de sa journee, en coordonnees.
#
# POURQUOI CE SCRIPT EXISTE. Une journee d'homme rend trois choses : son
# `journal` (sa trace), ses `pensees` (versees sur-le-champ par depecher.py), et
# son `cahier2` — ce qu'il a change AUX REGISTRES. La troisieme n'avait plus de
# consommateur : `verser_travaux.py` a ete supprime par la refonte de la boucle
# des acteurs, et `depecher.py` continuait de le nommer en rentrant. Resultat
# mesure le 129.3.30 : 99 changements de registre ecrits par vingt et un hommes,
# et pas une ligne de books.json touchee. Un homme qui tient un compte et dont le
# compte n'entre jamais dans le livre travaille pour rien, et le joueur lit un
# registre perime en croyant lire le registre.
#
# CE QU'IL NE FAIT PAS, ET C'EST LE POINT. Il ne devine pas. Une coordonnee qui
# ne se resout pas exactement n'est pas rapprochee au plus proche : elle est
# REFUSEE et dite en clair. Un verseur qui rattrape les a-peu-pres ecrit dans la
# mauvaise ligne une fois sur dix, et personne ne s'en apercoit — c'est pire que
# de ne rien verser. Il n'invente pas non plus une colonne, un tableau ni un
# livre : ce qui manque se cree a la main, en connaissance de cause.
#
# Usage :
#     python scripts/verser_cahier.py                 # a sec — montre tout
#     python scripts/verser_cahier.py --qui sara      # un homme, repetable
#     python scripts/verser_cahier.py --vraiment      # ecrit
import argparse, glob, io, json, os, re, sys, tempfile, unicodedata

import rapporteurs

import bibliotheque

# La console Windows est en cp1252 : un embleme ou un tiret cadratin dans le
# rapport tuait le script APRES le calcul, et le meme plantage attendait sur
# --vraiment. Un rapport ne doit jamais pouvoir faire tomber le versement.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(RACINE, "etat", "books.json")
RAPPORTS = os.path.join(RACINE, "etat", "rapports")


def lire(chemin):
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def ecrire(chemin, donnees):
    """Relit, ecrit dans un temporaire, remplace. Meme geste qu'ajouter.py."""
    d = os.path.dirname(chemin)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    os.close(fd)
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=1)
        f.write(u"\n")
    os.replace(tmp, chemin)


# --- normalisation ---------------------------------------------------------
# Les en-tetes de books.json portent des emoji ("⏳ État"), les hommes ecrivent
# souvent le mot nu ("Etat"). On compare sur le squelette : sans emoji, sans
# accents, sans ponctuation, sans casse.
def squelette(s):
    if s is None:
        return u""
    s = unicodedata.normalize("NFD", unicode_(s))
    s = u"".join(c for c in s if unicodedata.category(c) != "Mn")
    s = u"".join(c for c in s if not unicodedata.category(c).startswith("S"))
    s = re.sub(r"[^0-9a-zA-Z]+", u" ", s.lower()).strip()
    return s


def unicode_(s):
    try:
        return s if isinstance(s, str) else str(s)
    except Exception:
        return u""


# --- resolution ------------------------------------------------------------
def trouver_livre(books, livre_id):
    for v in books:
        if v.get("id") == livre_id:
            return v
    return None


def trouver_table(volume, nom):
    """Rend (colonnes, lignes, ou_ecrire) ou None.

    `ou_ecrire` est une fonction qui pose les lignes au bon endroit — le volume
    a une table unique (colonnes/lignes a la racine) ou plusieurs (tables[]).
    """
    if volume.get("tables"):
        cands = volume["tables"]
        cible = squelette(nom)
        # exact sur le squelette, puis inclusion — un homme ecrit "Actions"
        # la ou le livre porte "⚔️ Actions", et "Verrous" pour "🔒 Verrous".
        for t in cands:
            if squelette(t.get("titre")) == cible:
                return t
        if cible:
            proches = [t for t in cands
                       if cible and cible in squelette(t.get("titre"))]
            if len(proches) == 1:
                return proches[0]
        return None
    # volume a table unique : le nom donne doit correspondre au titre du volume
    # ou etre vide/generique. On ne refuse pas sur ce point — il n'y a qu'une
    # table, il n'y a rien a confondre.
    return volume


def trouver_colonne(colonnes, nom):
    cible = squelette(nom)
    if not cible:
        return None
    sq = [squelette(c) for c in colonnes]
    if cible in sq:
        return sq.index(cible)
    proches = [i for i, c in enumerate(sq) if cible in c or c in cible]
    if len(proches) == 1:
        return proches[0]
    return None


RE_LIGNE_N = re.compile(r"^ligne\s+(\d+)$", re.I)


def colonne_est_un_numero(colonnes):
    """Le premier en-tete porte-t-il un identifiant, ou un libelle ?

    « ⚔️ N° » et « 🪶 N° » portent des ids qu'on retrouve dans la cellule ;
    « L'affaire » et « 📅 Jour » portent du texte, et le rang d'une ligne n'y
    est ecrit nulle part. C'est ce qui departage « 48 = la 48e ligne » de
    « 8121 = l'action 8121 ».
    """
    if not colonnes:
        return False
    sq = squelette(colonnes[0])
    return sq in ("n", "no", "num", "numero") or sq.startswith("n ")


def trouver_ligne(lignes, ref, colonnes=None, hauteur=None):
    """Rend un index, la chaine 'neuve', ou None si ca ne se resout pas.

    Quatre facons dont un homme designe une ligne, et pas une de plus :
      · « ligne 12 », « 12 »  — le rang, a partir de 1
      · « 24033 », « O18 »    — l'identifiant, en premiere cellule
      · le debut du libelle   — un prefixe d'une cellule, s'il ne matche qu'une
      · « ligne neuve »       — on ajoute au bas

    `hauteur` est le nombre de lignes AU CHARGEMENT, pas maintenant : les rangs
    ont ete ecrits contre le registre tel qu'il etait ce matin, et deux hommes
    qui ouvrent chacun une ligne neuve dans « ce qui pend » decaleraient le
    rang du troisieme. Les ajouts vont toujours au bas, donc un rang ancien
    reste juste ; c'est seulement « la ligne d'apres » qu'il faut mesurer sur
    la hauteur d'origine.
    """
    brut = unicode_(ref).strip()
    if hauteur is None:
        hauteur = len(lignes)
    if squelette(brut) in ("ligne neuve", "neuve", "ligne nouvelle"):
        return "neuve"
    m = RE_LIGNE_N.match(brut)
    if m is None and re.match(r"^\d+$", brut) and not colonne_est_un_numero(colonnes or []):
        # un nombre nu dans un tableau dont la premiere colonne porte du texte
        # ne peut etre qu'un rang : aucune cellule ne le contient.
        m = re.match(r"^(\d+)$", brut)
    if m:
        i = int(m.group(1)) - 1
        return i if 0 <= i < hauteur else None
    cible = squelette(brut)
    if not cible:
        return None
    # l'identifiant, en premiere cellule
    for i, l in enumerate(lignes):
        cel = l.get("cellules") or []
        if cel and squelette(cel[0]) == cible:
            return i
    # le libelle, en prefixe de n'importe quelle cellule
    proches = []
    for i, l in enumerate(lignes):
        for c in (l.get("cellules") or []):
            sq = squelette(c)
            if sq and (sq.startswith(cible) or cible.startswith(sq)) and \
                    min(len(sq), len(cible)) >= 8:
                proches.append(i)
                break
    if len(set(proches)) == 1:
        return proches[0]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qui", action="append", help="un homme, repetable")
    ap.add_argument("--vraiment", action="store_true", help="ecrire pour de bon")
    ap.add_argument("--encore", action="store_true",
                    help="reprendre un rapport deja verse (double les lignes neuves)")
    args = ap.parse_args()

    session_livres = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
    books = session_livres.livres
    fichiers = sorted(glob.glob(os.path.join(RAPPORTS, "*.json")))

    poses, refus, differes = [], [], []
    hauteurs = {}
    traites = []
    for f in fichiers:
        try:
            rap = lire(f)
        except Exception as e:
            refus.append((os.path.basename(f), None, u"rapport illisible : %s" % e))
            continue
        qui = rap.get("qui") or os.path.basename(f)[:-5]
        if args.qui and qui not in args.qui:
            continue
        # Un rapport se verse UNE fois. Sans cette marque, la seconde passe
        # reecrirait les memes valeurs sans dommage — mais rouvrirait une
        # deuxieme fois chaque « ligne neuve », et un registre double ne se
        # repare pas a la lecture.
        if rap.get("_cahier_verse") and not args.encore:
            continue
        traites.append((f, rap))
        for e in (rap.get("cahier2") or []):
            livre_id = e.get("livre")
            volume = trouver_livre(books, livre_id)
            if volume is None:
                refus.append((qui, e, u"livre inconnu : %s" % livre_id))
                continue
            table = trouver_table(volume, e.get("table"))
            if table is None:
                refus.append((qui, e, u"tableau introuvable dans %s : %r"
                              % (livre_id, e.get("table"))))
                continue
            colonnes = table.get("colonnes") or []
            lignes = table.setdefault("lignes", [])
            ic = trouver_colonne(colonnes, e.get("colonne"))
            if ic is None:
                refus.append((qui, e, u"colonne introuvable : %r (le tableau a %s)"
                              % (e.get("colonne"), u" · ".join(colonnes))))
                continue
            if id(table) not in hauteurs:
                hauteurs[id(table)] = len(lignes)
            il = trouver_ligne(lignes, e.get("ligne"), colonnes,
                               hauteurs[id(table)])
            if il is None:
                # Une ligne qui ne se resout pas n'est pas forcement une faute :
                # c'est le plus souvent une ligne NEUVE qu'un homme ouvre et
                # remplit colonne par colonne — O18 dans le plan des offices, la
                # 48e de « ce qui pend », l'entree de sept heures chez la reine.
                # On ne tranche pas ici : on met de cote et l'on regroupe, parce
                # qu'une ligne neuve ne se decide qu'en voyant TOUTES les
                # colonnes qu'on lui destine.
                differes.append((qui, e, volume, table, colonnes, lignes, ic))
                continue
            if il == "neuve":
                cel = [u""] * len(colonnes)
                cel[ic] = unicode_(e.get("valeur"))
                lignes.append({"cellules": cel})
                poses.append((qui, livre_id, table.get("titre") or volume.get("titre"),
                              u"(ligne neuve)", colonnes[ic], u"", e.get("valeur")))
                continue
            cel = lignes[il].setdefault("cellules", [])
            while len(cel) < len(colonnes):
                cel.append(u"")
            avant = cel[ic]
            cel[ic] = unicode_(e.get("valeur"))
            poses.append((qui, livre_id, table.get("titre") or volume.get("titre"),
                          e.get("ligne"), colonnes[ic], avant, e.get("valeur")))

    # --- les lignes neuves, une fois toutes les colonnes connues -----------
    groupes = []
    for item in differes:
        ref = unicode_(item[1].get("ligne")).strip()
        cle = (id(item[3]), squelette(ref))
        for g in groupes:
            if g["cle"] == cle:
                g["items"].append(item)
                break
        else:
            groupes.append({"cle": cle, "ref": ref, "items": [item]})

    for g in groupes:
        qui, e0, volume, table, colonnes, lignes, _ = g["items"][0]
        ref = g["ref"]
        if not squelette(ref):
            # « — » n'est pas une ligne : c'est un homme qui n'a pas su dire
            # laquelle. Ouvrir une ligne neuve la-dessus poserait au registre
            # une entree que personne ne saurait relire.
            for it in g["items"]:
                refus.append((it[0], it[1],
                              u"ligne non designee (%r) — on n'ouvre pas une "
                              u"ligne neuve sans nom" % ref))
            continue
        m = RE_LIGNE_N.match(ref)
        rang = m.group(1) if m else (ref if re.match(r"^\d+$", ref) else None)
        premiere = None
        if colonne_est_un_numero(colonnes):
            # l'identifiant s'ecrit dans la premiere cellule
            premiere = ref
        elif rang is not None:
            # un RANG, et il n'a de sens que s'il designe la ligne d'apres :
            # ecrire la 48e d'un tableau qui en a 12 poserait une ligne dont
            # personne ne saura jamais ou elle devait aller.
            h = hauteurs.get(id(table), len(lignes))
            if int(rang) != h + 1:
                for it in g["items"]:
                    refus.append((it[0], it[1],
                                  u"ligne %s d'un tableau qui en avait %d — ni "
                                  u"existante, ni la suivante" % (rang, h)))
                continue
        else:
            # un libelle : il devient la premiere cellule de la ligne neuve
            premiere = ref
        cel = [u""] * len(colonnes)
        if premiere is not None:
            cel[0] = premiere
        for (q, e, _v, _t, cols, _l, ic) in g["items"]:
            cel[ic] = unicode_(e.get("valeur"))
        lignes.append({"cellules": cel})
        for (q, e, _v, _t, cols, _l, ic) in g["items"]:
            poses.append((q, volume.get("id"),
                          table.get("titre") or volume.get("titre"),
                          u"LIGNE NEUVE %s" % ref, cols[ic], u"", e.get("valeur")))

    def court(s, n=70):
        s = unicode_(s).replace(u"\n", u" ")
        return s if len(s) <= n else s[:n - 1] + u"…"

    out = sys.stdout
    out.write(u"VERSER CAHIER — %d pose(s), %d refus%s\n"
              % (len(poses), len(refus), u"" if args.vraiment else u"  · A SEC"))
    out.write(u"=" * 72 + u"\n")
    for (qui, livre, tab, ligne, col, avant, apres) in poses:
        out.write(u"%s\n  %s / %s / %s / %s\n" % (qui, livre, court(tab, 34),
                                                  court(ligne, 34), court(col, 34)))
        out.write(u"    - %s\n    + %s\n" % (court(avant), court(apres)))
    if refus:
        out.write(u"\nREFUSES — rien n'a ete ecrit pour ceux-la :\n")
        for (qui, e, motif) in refus:
            out.write(u"  [%s] %s\n" % (qui, motif))
            if e:
                out.write(u"       valeur restee au rapport : %s\n"
                          % court(e.get("valeur"), 90))

    if args.vraiment and poses:
        try:
            session_livres.sauver()
        except bibliotheque.BibliothequeModifiee as exc:
            raise SystemExit(u"REFUS : %s" % exc)
        for (chemin_rap, rap) in traites:
            rap["_cahier_verse"] = True
            ecrire(chemin_rap, rap)
        rapporteurs.battre("verser-cahier", u"%d changements" % len(poses))
        out.write(u"\n%d changement(s) ecrits dans etat/books.json\n" % len(poses))
        out.write(u"%d rapport(s) marques verses — ils ne repasseront plus.\n"
                  % len(traites))
    elif not args.vraiment:
        out.write(u"\nRien n'a ete ecrit. --vraiment pour verser.\n")


if __name__ == "__main__":
    main()
