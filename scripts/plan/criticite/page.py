# -*- coding: utf-8 -*-
"""PAGE — la mise en page du classement : largeur, titres, cales, statuts.
"""
import sys

from plan.expose import nu, sans_emoji, FINI, premier_mot

LARGEUR = 100

def titre(t):
    sys.stdout.write(u"\n" + t + u"\n" + u"─" * LARGEUR + u"\n")


def cale(t, n):
    t = nu(t)
    return (t[:n - 1] + u"…") if len(t) > n else t.ljust(n)


def statut(p):
    t = sans_emoji(p["etat"] or u"")
    return cale(t, 14) if t else u"—"


def prix(livres):
    """{numero: la prose du prix}. Elle est portee par la CLEF — « 💰 Ce
    qu'elle coute et ce qu'elle ferme » — et `charger()` ne la remonte pas :
    l'index derive ne la porte pas non plus, a dessein. On la relit ici, pour
    l'imprimer telle quelle. On n'en tire aucun nombre : diviser par de la
    prose ne se fait pas, et lui coller un bareme serait inventer le seul
    chiffre que personne n'a ecrit."""
    out = {}
    from plan.expose import numero_de as _numero_de, col as _col
    for b in livres:
        for t in (b.get("tables") or []):
            cols = t.get("colonnes") or []
            i = _col(cols, u"coûte|coute|le prix")
            if i is None:
                continue
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
                if len(c) > i and c and c[i]:
                    m = _numero_de(c[0])
                    if m:
                        out.setdefault(m.group(1), c[i])
    return out


def faite(p):
    return bool(FINI.match(premier_mot(p["etat"]) or u""))

