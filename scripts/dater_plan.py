# -*- coding: utf-8 -*-
u"""dater_plan.py — porter l'echelle J−N dans la colonne « Jour du ».

POURQUOI. `porter_jour_du.py` a monte les dates ABSOLUES de la note vers la
colonne `📅 Jour dû` : vingt-six. Il a laisse la ou elles etaient les formes
RELATIVES, parce que le jour d'entree n'etait pas arrete. Elles y sont
restees, et personne ne va les lire : le rapport de plan compte 588 actions
« sans date ni amont » sur 609, alors que 480 portent un J−N parfaitement
ecrit — dans « Ce qu'on fait », dans la note, dans le cout, dans l'office.
Une date qui vit dans six colonnes differentes n'a pas d'adresse.

CE QU'IL FAIT. Pour chaque action dont la colonne `📅 Jour dû` est VIDE, il
cherche sa forme relative selon l'ordre de `jours_relatifs.candidat` et la
porte dans la colonne, sous la forme canonique unique : `J−22`, `J−22…J−18`,
`chaque jour dès J−36`. Il n'ecrase JAMAIS une cellule remplie — donc les
vingt-six dates absolues restent, et repasser le script ne fait rien : c'est
son idempotence, et elle est de construction, pas de precaution.

CE QU'IL NE FAIT PAS. Il ne resout aucun J−N en date de lune : le jour
d'entree n'existe pas (verrou 11001), et une date absolue ecrite dans un
cahier violerait la clef 11110. Il ne touche pas aux actions closes, dont la
note porte souvent la date d'une AUTRE affaire. Il n'ecrit pas dans un
cahier qui n'a pas de colonne d'action.

    python scripts/dater_plan.py                a blanc, c'est le defaut
    python scripts/dater_plan.py --affaire ral  a blanc, une affaire seulement
    python scripts/dater_plan.py --detail       chaque ligne, avec sa source
    python scripts/dater_plan.py --vraiment     ecrit, avec sauvegarde horodatee

DEUX PLUMES SUR CE FICHIER. `etat/books.json` est ecrit par la session de jeu
et par les agents de couverture. Le script relit le fichier juste avant
d'ecrire et refuse si son empreinte a bouge depuis la lecture.
"""
import io, os, re, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import couverture as C                     # noqa: E402
import jours_relatifs as JR                # noqa: E402
import bibliotheque                        # noqa: E402

BOOKS = os.path.join(RACINE, "etat", "books.json")
COL_JOUR = u"\U0001F4C5 Jour dû"
CLOS = (u"faite", u"close", u"abandonnée", u"abandonnee")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def entetes(cols):
    u"""{en-tete minuscule sans emoji -> index}. Les colonnes se REPERENT par
    leur nom : aucun cahier n'a le meme ordre, et deux d'entre eux n'ont pas
    les memes colonnes du tout."""
    out = {}
    for i, c in enumerate(cols):
        out[C.sans_emoji(C.nu(c)).strip().lower()] = i
    return out


def passer(ecrire=False, filtre=None):
    session_livres = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
    livres = session_livres.livres
    portees, deja, clos, muettes, colonnes = [], 0, 0, 0, 0
    for livre in livres:
        for t in (livre.get("tables") or []):
            g = (C.genre_de((t or {}).get("titre") or u"")
                 or C.genre_de(livre.get("titre") or u""))
            if g != "action":
                continue
            if filtre and filtre not in C.sans_emoji(C.nu(livre.get("titre")) or u"").lower() \
                    and filtre not in str(livre.get("id") or u"").lower():
                continue
            cols = (t or {}).get("colonnes") or []
            idx = entetes(cols)
            i_jour = idx.get(u"jour dû", idx.get(u"jour du"))
            if i_jour is None:
                cols.append(COL_JOUR)
                i_jour = len(cols) - 1
                colonnes += 1
                for l in (t.get("lignes") or []):
                    cel = l["cellules"] if isinstance(l, dict) else l
                    cel.append(u"")
                idx[u"jour dû"] = i_jour
            i_etat = idx.get(u"état", idx.get(u"etat", idx.get(u"où ça en est")))
            for l in (t.get("lignes") or []):
                cel = l["cellules"] if isinstance(l, dict) else l
                while len(cel) < len(cols):
                    cel.append(u"")
                if not C.NUM.search(C.nu(cel[0]) or u""):
                    continue
                num = C.NUM.search(C.nu(cel[0])).group(1)
                if C.nu(cel[i_jour]):
                    deja += 1
                    continue
                # Une action close n'a plus de terme, et sa prose porte souvent
                # la date d'une autre affaire. Meme garde que porter_jour_du.py.
                if i_etat is not None and i_etat < len(cel) \
                        and any(x in C.nu(cel[i_etat]).lower() for x in CLOS):
                    clos += 1
                    continue
                cellules = {k: C.nu(cel[i]) for k, i in idx.items() if i < len(cel)}
                f, source = JR.candidat(cellules)
                if not f:
                    muettes += 1
                    continue
                cel[i_jour] = JR.canonique(f)
                portees.append((num, C.sans_emoji(C.nu(livre.get("titre"))),
                                cel[i_jour], source))
    if ecrire:
        try:
            session_livres.sauver()
        except bibliotheque.BibliothequeModifiee as exc:
            raise SystemExit(u"REFUS : %s" % exc)
    return portees, deja, clos, muettes, colonnes


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--aide" in args or "-h" in args:
        sys.stdout.write(__doc__)
        raise SystemExit(0)
    vraiment = "--vraiment" in args
    detail = "--detail" in args
    filtre = args[args.index("--affaire") + 1].lower() if "--affaire" in args else None
    portees, deja, clos, muettes, colonnes = passer(vraiment, filtre)
    sys.stdout.write(
        u"%s — %d date(s) relative(s) portée(s) · %d cellule(s) déjà "
        u"remplie(s) · %d close(s) écartée(s) · %d sans forme relative · "
        u"%d colonne(s) créée(s)\n"
        % (u"ÉCRIT" if vraiment else u"À BLANC — rien n'a été écrit",
           len(portees), deja, clos, muettes, colonnes))
    par = {}
    for n, aff, v, s in portees:
        par.setdefault(aff, []).append((n, v, s))
    for aff in sorted(par, key=lambda x: -len(par[x])):
        sys.stdout.write(u"  %-46s %3d\n" % (aff[:46], len(par[aff])))
        if detail:
            for n, v, s in par[aff]:
                sys.stdout.write(u"      %-8s %-18s <- %s\n" % (n, v, s))
    if not vraiment:
        sys.stdout.write(u"\n  → --vraiment pour écrire par la bibliothèque.\n")
