# -*- coding: utf-8 -*-
u"""porter_jour_du.py — remettre les echeances la ou on les lit.

POURQUOI. Avant `normaliser_etats.py`, la date DUE d'une action vivait dans la
prose de sa cellule d'etat : « a faire — avant le 30e ». Le lecteur du plan la
trouvait en se rabattant sur cette cellule. La normalisation a mis un mot dans
l'etat et versé la prose en « Note » : les dates n'ont rien perdu, mais plus
personne ne va les y chercher, et le compte des echeances est tombe de
vingt-cinq a sept. Ce script les porte dans la colonne `📅 Jour dû`, qui est
l'endroit ou couverture.py les lit deja (`i_jour`).

CE QU'IL PORTE, ET CE QU'IL LAISSE. Seules les dates ABSOLUES montent :
« avant le 30e », « le 4e de la 4e lune », « dû le 17e ». Les formes en J−N
sont relatives au jour d'entree, qui n'est pas arrete : elles restent a la
note, ou elles sont justes. On n'ecrase jamais un `Jour dû` deja rempli.

    python scripts/porter_jour_du.py              a blanc
    python scripts/porter_jour_du.py --vraiment   ecrit, avec sauvegarde
"""
import io, os, re, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "scripts"))
import couverture as C
import bibliotheque

BOOKS = os.path.join(RACINE, "etat", "books.json")
COL_JOUR = u"📅 Jour dû"

# « avant le 4e de la 4e lune » d'abord : la forme longue prime sur la courte,
# sinon « le 4e » serait pris seul et la lune perdue.
ABSOLUE = [
    re.compile(r"((?:avant\s+|d[uû]\s+)?le\s+\d{1,2}e(?:\s+\w+)?\s+de\s+la\s+\d{1,2}e(?:\s+lune)?)", re.I),
    re.compile(r"((?:avant|d[uû])\s+le\s+\d{1,2}e(?:\s+au\s+(?:soir|matin))?)", re.I),
]


def trouver(note):
    for rx in ABSOLUE:
        m = rx.search(note or u"")
        if m:
            return u" ".join(m.group(1).split())
    return u""


def passer(ecrire=False):
    session_livres = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
    livres = session_livres.livres
    portees, deja, sans, colonnes, clos = [], 0, 0, 0, 0
    for livre in livres:
        for t in (livre.get("tables") or []):
            g = (C.genre_de((t or {}).get("titre") or u"")
                 or C.genre_de(livre.get("titre") or u""))
            if g != "action":
                continue
            cols = (t or {}).get("colonnes") or []
            i_note = C.col(cols, u"^note$")
            if i_note is None:
                continue
            i_etat = C.col(cols, u"^état$|^etat$")
            i_jour = C.col(cols, u"jour dû|jour du")
            if i_jour is None:
                cols.append(COL_JOUR)
                i_jour = len(cols) - 1
                colonnes += 1
                for ligne in (t.get("lignes") or []):
                    ligne["cellules"].append(u"")
            for ligne in (t.get("lignes") or []):
                c = ligne.get("cellules") or []
                while len(c) < len(cols):
                    c.append(u"")
                num = C.NUM.search(C.nu(c[0]) or u"")
                if not num:
                    continue
                if C.nu(c[i_jour]):
                    deja += 1
                    continue
                # Une ligne close n'a plus de terme, et sa note porte souvent
                # une AUTRE date que le sien — 21222, payee et recue, remontait
                # « avant le 4e », qui est la date des bourses et non la sienne.
                if (i_etat is not None and i_etat < len(c)
                        and C.nu(c[i_etat]) in (u"faite", u"close", u"abandonnée")):
                    clos += 1
                    continue
                d = trouver(C.nu(c[i_note]) if i_note < len(c) else u"")
                if not d:
                    sans += 1
                    continue
                c[i_jour] = d
                portees.append((num.group(1), C.nu(livre.get("titre")), d))
    if ecrire:
        session_livres.sauver()
    return portees, deja, sans, colonnes, clos


if __name__ == "__main__":
    vraiment = "--vraiment" in sys.argv
    portees, deja, sans, colonnes, clos = passer(ecrire=vraiment)
    out = io.open(1, "w", encoding="utf-8", closefd=False)
    out.write(u"%s — %d date(s) portée(s) · %d déjà remplie(s) · %d sans date "
              u"absolue · %d colonne(s) créée(s) · %d close(s) écartée(s)\n"
              % (u"ÉCRIT" if vraiment else u"À BLANC",
                 len(portees), deja, sans, colonnes, clos))
    for n, aff, d in portees:
        out.write(u"  %-8s %-46s %s\n" % (n, aff[:46], d))
    out.flush()
