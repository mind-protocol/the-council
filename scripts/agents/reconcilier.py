# -*- coding: utf-8 -*-
u"""RECONCILIER — le journal des affaires ecrites A LA MAIN.

DEUX MAISONS, ET UNE SEULE AVAIT UNE PORTE. Les affaires vivent a deux
adresses : `etat/books/` — la bibliotheque commune, dont `bibliotheque.
Session.sauver()` emet desormais le journal — et `chambres/<qui>/books/`, les
cahiers a soi. Cette seconde maison N'A AUCUNE PORTE : `chambre.py` cree le
dossier et s'arrete la ; les 9 affaires du MJ y sont ecrites a la main, par
Write et Edit. Il n'existe donc aucun point d'emission a instrumenter.

LA RECONCILIATION N'EST PAS UN RATTRAPAGE, C'EST LE MECANISME PRINCIPAL ICI.
On garde une empreinte du dernier etat connu, on la compare au disque, et l'on
emet les ecarts. Le prix est dans le nom : ces evenements portent
`certitude: "constate"` et non `"declare"` — on sait QUE la ligne a bouge,
jamais QUI l'a bougee ni QUAND exactement, seulement entre deux passages.
C'est la meme epistemologie que les jetons de la table de guerre, et elle
vaut mieux qu'un `par` invente.

Elle sert aussi de FILET a la bibliotheque commune : un homme depeche qui
ecrit dans `etat/books/*.json` par Write contourne la porte, et seule une
comparaison au disque le rattrape.

    python scripts/reconcilier.py              ce qui serait emis
    python scripts/reconcilier.py --vraiment   emet et pose l'empreinte
    python scripts/reconcilier.py --amorcer    pose l'empreinte SANS emettre
"""
import argparse
import glob
import io
import json
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(_d) != "scripts" and os.path.dirname(_d) != _d:
    _d = os.path.dirname(_d)
for _p in (_d, os.path.join(_d, "noyau")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import histoire  # noqa: E402 — noyau : le seul frere importable

RACINE = os.path.dirname(_d)
ETAT = os.path.join(RACINE, "etat")
CHAMBRES = os.path.join(RACINE, "chambres")
EMPREINTES = os.path.join("histoire", "empreintes.json")
JOURNAL_CHAMBRES = os.path.join("histoire", "chambres.jsonl")


def _lire(chemin):
    try:
        return json.load(io.open(chemin, encoding="utf-8"))
    except Exception:
        return None


def maisons():
    u"""Rend {maison : {id_volume : volume}} pour les deux adresses.

    Une « maison » est `etat` pour la bibliotheque commune, et
    `chambre:<qui>` pour chaque cahier. On garde le nom du proprietaire dans
    la clef : c'est ce qui permettra de lire le journal du MJ seul, ou celui
    d'un personnage seul, sans les melanger.
    """
    out = {}
    commune = {}
    for f in glob.glob(os.path.join(ETAT, "books", "affaire-*.json")):
        v = _lire(f)
        if v and v.get("id"):
            commune[v["id"]] = v
    if commune:
        out["etat"] = commune
    for f in glob.glob(os.path.join(CHAMBRES, "*", "books", "*.json")):
        qui = f.replace("\\", "/").split("/")[-3]
        v = _lire(f)
        if not v:
            continue
        ident = v.get("id") or os.path.basename(f)[:-5]
        v = dict(v, id=ident)
        out.setdefault("chambre:%s" % qui, {})[ident] = v
    return out


def empreinte_posee():
    return _lire(os.path.join(ETAT, EMPREINTES)) or {}


def poser(instantane):
    chemin = os.path.join(ETAT, EMPREINTES)
    dossier = os.path.dirname(chemin)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(chemin, "w", encoding="utf-8") as f:
        f.write(json.dumps(instantane, ensure_ascii=False, indent=1))


def passer(vraiment=False, amorcer=False):
    u"""Rend (comptes, total). Ecrit seulement si `vraiment`."""
    courant = maisons()
    avant = empreinte_posee()
    comptes, total = {}, 0

    # PREMIERE FOIS : on ne deverse pas 51 affaires comme si elles venaient
    # d'etre creees a la seconde. On pose l'empreinte et l'on ne dit rien —
    # le journal commence a partir de maintenant, et il le dira.
    vierge = not avant
    for maison, volumes in sorted(courant.items()):
        anciens = avant.get(maison) or {}
        if vierge:
            comptes[maison] = 0
            continue
        fichier = (histoire.FICHIER if maison == "etat"
                   else JOURNAL_CHAMBRES)
        n = 0
        if vraiment and not amorcer:
            n = histoire.journaliser(anciens, volumes, ETAT,
                                     certitude="constate",
                                     outil="reconcilier",
                                     fichier=fichier, maison=maison)
        else:
            for ident in set(list(anciens) + list(volumes)):
                a, b = anciens.get(ident), volumes.get(ident)
                if a != b:
                    n += len(histoire.evenements_du_volume(a, b))
        comptes[maison] = n
        total += n
    # Les maisons DISPARUES comptent aussi : une chambre effacee emporte ses
    # affaires, et c'est un evenement.
    for maison in sorted(set(avant) - set(courant)):
        comptes[maison] = comptes.get(maison, 0)

    if vraiment:
        poser(courant)
    return comptes, total, vierge, courant


def main(argv=None):
    ap = argparse.ArgumentParser(description=u"RECONCILIER — le journal des"
                                             u" affaires ecrites a la main.")
    ap.add_argument("--vraiment", action="store_true",
                    help=u"emet les evenements et pose l'empreinte")
    ap.add_argument("--amorcer", action="store_true",
                    help=u"pose l'empreinte SANS rien emettre")
    a = ap.parse_args(argv)
    comptes, total, vierge, courant = passer(a.vraiment or a.amorcer,
                                             a.amorcer)
    print(u"RECONCILIER — %d maison(s), %d volume(s)"
          % (len(courant), sum(len(v) for v in courant.values())))
    for maison, volumes in sorted(courant.items()):
        print(u"  %-22s %3d affaire(s)   %s"
              % (maison, len(volumes),
                 (u"%d evenement(s)" % comptes.get(maison, 0))
                 if not vierge else u"—"))
    if vierge:
        print(u"\nPREMIERE PASSE : l'empreinte n'existait pas. On la pose sans"
              u" rien emettre —")
        print(u"un journal qui s'ouvrirait en declarant 51 affaires « creees »"
              u" a la seconde")
        print(u"mentirait sur son propre commencement. L'histoire part de"
              u" maintenant.")
    else:
        print(u"\n%d evenement(s) %s, tous en `certitude: constate` : on sait"
              % (total, u"emis" if a.vraiment and not a.amorcer
                 else u"a emettre"))
        print(u"QUE la ligne a bouge, jamais qui l'a bougee ni quand"
              u" exactement.")
    if not a.vraiment and not a.amorcer:
        print(u"\nA sec. `--vraiment` pour emettre, `--amorcer` pour poser"
              u" l'empreinte seule.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
