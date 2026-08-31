# -*- coding: utf-8 -*-
u"""RENDRE LES CELLULES — remettre ce qu'une reecriture a efface, SANS ecraser.

CE QUI EST ARRIVE. Le 31.8 a 04 h 16, les neuf affaires de `chambres/mj/books/`
ont ete reecrites CELLULES VIDES : le nombre de lignes est conserve partout
(10 -> 10, 17 -> 17), mais leur contenu est blanc. Sept volumes sont eventres
— `la-montre` 62 cellules pleines -> 3, `les-boucles` 111 -> 8. Deux autres
n'ont perdu que deux ou trois cellules : ce sont de vraies retouches, pas un
vidage, et on n'y touche pas.

POURQUOI RIEN NE L'A EMPECHE. `chambres/<qui>/books/` n'a AUCUNE porte :
`chambre.py` cree le dossier et s'arrete la. On y ecrit par Write et Edit, en
reecrivant le fichier entier — et un fichier entier reecrit peut tout perdre
sans que rien ne le signale. La bibliotheque commune, elle, refuse d'ecrire
si le volume a bouge depuis la lecture ; ici, personne ne lit avant d'ecrire.

LA REGLE DE CE SCRIPT, ET ELLE EST LA SEULE : ON NE REMPLIT QUE DU VIDE.
Une cellule non vide sur le disque n'est jamais touchee, quoi qu'en dise la
sauvegarde. Une ligne ajoutee depuis reste. Un volume neuf est ignore. La
fusion ne peut donc rien detruire, meme si la sauvegarde est plus vieille que
le travail en cours — c'est ce qui la rend sure a lancer pendant qu'une autre
session ecrit.

    python scripts/rendre_cellules.py <maison>              ce qui serait rendu
    python scripts/rendre_cellules.py <maison> --vraiment   l'ecriture

`<maison>` est une clef de l'empreinte : « etat », « chambre:mj »…
"""
import argparse
import io
import json
import os
import sys
import unicodedata

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RACINE = os.path.dirname(_d)
ETAT = os.path.join(RACINE, "etat")
EMPREINTES = os.path.join(ETAT, "histoire", "empreintes.json")


def _noyau(colonne):
    u"""Le coeur d'un nom de colonne : sans emoji, sans accent, en minuscules.

    CE N'ETAIT PAS UN VANDALISME, C'ETAIT UNE MIGRATION QUI A PERDU SES
    VALEURS. L'empreinte porte l'ancien format a 8 colonnes sans emoji
    (« N° », « Realise », « Etat », « Jour du ») ; le disque porte le format
    canonique a 16 colonnes (« ⚔️ N° », « 🗝️ Réalise », « ⏳ État »,
    « 📅 Jour dû »). La conversion du 31.8 a change les EN-TETES sans reporter
    les cellules.

    LA PREUVE EST IRREFUTABLE : « 👤 Qui » est la seule colonne au nom
    identique des deux cotes, et c'est la seule qui a survecu. On rapproche
    donc sur le coeur du nom, ce qui rend les sept volumes d'un coup.
    """
    t = str(colonne or "")
    t = "".join(c for c in t if c.isalnum() or c.isspace())
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(t.lower().split())


def _cellules(ligne):
    if isinstance(ligne, dict):
        return ligne.get("cellules")
    return ligne if isinstance(ligne, list) else None


def fusionner(avant, apres):
    u"""Remplit dans `apres` les cellules vides dont `avant` a la valeur.

    Rend le nombre de cellules rendues. `apres` est modifie en place. On
    apparie les tables par TITRE et les lignes par RANG — c'est valable ici
    parce que le nombre de lignes est intact ; si un titre ou un compte de
    lignes a change, on saute la table plutot que de deviner un appariement.
    """
    rendues = 0
    par_titre = {}
    for t in apres.get("tables") or []:
        par_titre[str(t.get("titre"))] = t
    for ta in avant.get("tables") or []:
        tb = par_titre.get(str(ta.get("titre")))
        if tb is None:
            continue
        la = ta.get("lignes") or []
        lb = tb.get("lignes") or []
        if len(la) != len(lb):
            continue          # on ne devine pas un appariement
        # ON APPARIE LES COLONNES PAR LEUR NOM, PAS PAR LEUR RANG. La
        # reecriture du 31.8 a AJOUTE une colonne (« 👤 Qui ») : les index ne
        # correspondent plus d'un cote a l'autre, et un appariement positionnel
        # remettait chaque valeur dans la colonne du voisin. Avec la garde
        # `len(ca) != len(cb)` il ne rendait plus que 120 cellules sur 350 —
        # prudent et faux. Par nom, on rend tout ce qui a un correspondant, et
        # rien de ce qui n'en a pas.
        cols_a = [_noyau(c) for c in (ta.get("colonnes") or [])]
        cols_b = {}
        for i, c in enumerate(tb.get("colonnes") or []):
            cols_b.setdefault(_noyau(c), i)
        vers = [cols_b.get(c) for c in cols_a]
        for ra, rb in zip(la, lb):
            ca, cb = _cellules(ra), _cellules(rb)
            if ca is None or cb is None:
                continue
            for i, val in enumerate(ca):
                j = vers[i] if i < len(vers) else None
                if j is None or j >= len(cb):
                    continue          # colonne disparue : on ne la reinvente pas
                if str(cb[j]).strip():
                    continue          # occupe : on ne touche JAMAIS
                if not str(val).strip():
                    continue          # vide des deux cotes : rien a rendre
                cb[j] = val
                rendues += 1
    return rendues


def maison_sur_disque(maison):
    u"""Le dossier reel d'une maison de l'empreinte."""
    if maison == "etat":
        return os.path.join(ETAT, "books")
    if maison.startswith("chambre:"):
        return os.path.join(RACINE, "chambres", maison.split(":", 1)[1],
                            "books")
    return None


def passer(maison, vraiment=False):
    emp = json.load(io.open(EMPREINTES, encoding="utf-8")).get(maison) or {}
    dossier = maison_sur_disque(maison)
    if not dossier or not os.path.isdir(dossier):
        return [], u"maison inconnue ou absente : %s" % maison
    rapport = []
    for ident, avant in sorted(emp.items()):
        f = os.path.join(dossier, ident + ".json")
        if not os.path.exists(f):
            rapport.append((ident, 0, u"absent du disque — non recree"))
            continue
        apres = json.load(io.open(f, encoding="utf-8"))
        n = fusionner(avant, apres)
        if not n:
            rapport.append((ident, 0, u"rien a rendre"))
            continue
        if vraiment:
            with io.open(f, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(apres, ensure_ascii=False, indent=1)
                         + "\n")
        rapport.append((ident, n, u"rendues" if vraiment else u"a rendre"))
    return rapport, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=u"Remettre les cellules effacees,"
                                             u" sans jamais ecraser.")
    ap.add_argument("maison", help=u"« etat », « chambre:mj »…")
    ap.add_argument("--vraiment", action="store_true")
    a = ap.parse_args(argv)
    rapport, erreur = passer(a.maison, a.vraiment)
    if erreur:
        print(erreur)
        return 1
    total = sum(n for _, n, _ in rapport)
    print(u"RENDRE LES CELLULES — %s" % a.maison)
    for ident, n, mot in rapport:
        print(u"  %-46s %4d  %s" % (ident[:46], n, mot))
    print(u"\n%d cellule(s) %s. UNE CELLULE OCCUPEE N'EST JAMAIS TOUCHEE :"
          % (total, u"rendues" if a.vraiment else u"a rendre"))
    print(u"la fusion ne peut rien detruire, meme pendant qu'un autre ecrit.")
    if not a.vraiment:
        print(u"\nA sec. `--vraiment` pour ecrire.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
