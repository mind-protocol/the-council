# -*- coding: utf-8 -*-
u"""ACTIVITE / AFFAIRES — la photo, et le mouvement lu dans les journaux.

DEUX CHOSES QUI NE SE MELANGENT PAS, et c'est tout le module :

  LA PHOTO se calcule depuis les volumes, a l'instant. Elle repond « ou en
  sont les affaires », et elle marche depuis toujours.

  LE MOUVEMENT se LIT dans `etat/histoire/*.jsonl`. Il repond « qu'est-ce qui
  a bouge, quand, par qui » — et il ne sait rien d'avant l'ouverture du
  journal. On le dit au lieu de rendre un tableau vide qui aurait l'air d'un
  calme plat.

LES DEUX HORLOGES SERVENT ENFIN. Chaque ligne de journal porte `quand` (le
mur) et `monde` (la date de fiction), donc `--monde N` fenetre ici aussi —
c'est precisement ce que les billets ne permettaient pas.
"""
import collections
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

import histoire  # noqa: E402
from agents import reconcilier  # noqa: E402

ETAT = os.path.join(os.path.dirname(_d), "etat")
JOURNAUX = (("etat", histoire.FICHIER),
            ("chambres", reconcilier.JOURNAL_CHAMBRES))


def minute_absolue(d):
    u"""La date du monde en minutes. Meme calcul que temps/horloges.py — on
    ne l'importe pas pour ne pas lier ce module a ce container."""
    if not d:
        return None
    try:
        return ((((int(d["annee"]) * 12 + int(d["lune"]) - 1) * 30
                  + int(d["jour"]) - 1) * 1440) + int(d.get("minute") or 0))
    except (KeyError, TypeError, ValueError):
        return None


def photo():
    u"""{maison : {affaire : Counter}} + les etats hors vocabulaire + les
    volumes DESALIGNES.

    UN VOLUME DESALIGNE EST UNE FAUTE D'ECRITURE, PAS DE LECTURE. Capte le
    31.8 sur `affaire-la-chute-de-sombreval`, creee par la boucle : les
    colonnes declarent `N° | L'action | Realise | …` et les cellules portent
    `<texte de l'action> | rhaenyra | a faire | …` — tout est decale d'un
    cran, et l'etat se loge dans la colonne « Realise ». Aucun lecteur ne
    peut redresser ca ; on le SIGNALE, sinon l'affaire compte zero action
    reconnue et passe pour vide.
    """
    par, sales, tordus = {}, collections.Counter(), []
    for maison, volumes in reconcilier.maisons().items():
        dedans = {}
        for ident, v in volumes.items():
            c = collections.Counter()
            for num, ligne in histoire._index(v, u"⚔️ Actions").items():
                f = histoire.famille(ligne["etat"])
                if f is None:
                    brut = histoire.decaper(ligne["etat"])
                    sales[brut[:38] or "(vide)"] += 1
                c[f or "hors vocabulaire"] += 1
            if c:
                dedans[ident] = c
            # Des lignes, un en-tete d'etat, et RIEN de reconnu : le decalage.
            if c and not any(k for k in c if k != "hors vocabulaire"):
                tordus.append((maison, ident, sum(c.values())))
        if dedans:
            par[maison] = dedans
    return par, sales, tordus


def lire_journaux():
    out = []
    for nom, fichier in JOURNAUX:
        chemin = os.path.join(ETAT, fichier)
        try:
            for l in io.open(chemin, encoding="utf-8"):
                l = l.strip()
                if l:
                    try:
                        out.append(json.loads(l))
                    except ValueError:
                        continue
        except IOError:
            continue
    return out


def dans_la_fenetre(e, args, present_minute):
    if args.tout:
        return True
    if args.monde is not None:
        m = minute_absolue(e.get("monde"))
        if m is None or present_minute is None:
            return False
        return (present_minute - m) <= args.monde * 60
    # Le mur : les lignes portent un ISO local, on compare en chaine.
    import time
    limite = time.strftime("%Y-%m-%dT%H:%M:%S",
                           time.localtime(time.time() - args.heures * 3600))
    return (e.get("quand") or "") >= limite


def rendre(args, titre):
    par, sales, tordus = photo()
    titre(u"OU EN SONT LES AFFAIRES — la photo")
    total = collections.Counter()
    for maison in sorted(par):
        lignes = par[maison]
        somme = collections.Counter()
        for c in lignes.values():
            somme.update(c)
        total.update(somme)
        # PAS DE POURCENTAGE D'AVANCEMENT, ET C'EST DELIBERE. Il n'en existe
        # pas ici : le denominateur grossit tout seul (la boucle cree des
        # actions en continu — une a ete captee pendant qu'on ecrivait ce
        # module), « a faire » compte du travail jamais commence, et les
        # etats sales ou desalignes le corrompent. Un chiffre dont la hausse
        # ne ferait rien decider est du decor. On rend les comptes bruts.
        print(u"  %-16s %3d affaire(s) · %4d action(s) · %s"
              % (maison, len(lignes), sum(somme.values()),
                 u" · ".join(u"%s %d" % (k, v)
                             for k, v in somme.most_common())))
    print(u"  %-16s %s" % (u"tout",
          u" · ".join(u"%s %d" % (k, v) for k, v in total.most_common())))
    if sales:
        print(u"")
        print(u"  HORS VOCABULAIRE — %d action(s). Ce ne sont pas des erreurs"
              u" de lecture :" % sum(sales.values()))
        print(u"  la colonne d'etat raconte au lieu de nommer. On les montre,"
              u" on ne les range pas.")
        for k, n in sales.most_common(6):
            print(u"    %3d  %s" % (n, k))

    if tordus:
        print(u"")
        print(u"  COLONNES DESALIGNEES — %d affaire(s). Les cellules ne"
              u" tombent pas en face" % len(tordus))
        print(u"  de leur en-tete : l'etat se loge dans une autre colonne."
              u" Faute d'ECRITURE,")
        print(u"  qu'aucun lecteur ne peut redresser.")
        for maison, ident, n in tordus[:6]:
            print(u"    %-16s %-46s %3d action(s)" % (maison, ident[:46], n))

    # LES AFFAIRES QUI NE BOUGENT PAS SONT LE SUJET, pas celles qui avancent.
    dorment = []
    for maison, lignes in par.items():
        for ident, c in lignes.items():
            reste = sum(v for k, v in c.items() if k != "faite")
            if c.get("faite", 0) == 0 and reste:
                dorment.append((maison, ident, reste))
    if dorment:
        print(u"")
        print(u"  PAS UNE SEULE ACTION FAITE — %d affaire(s) :" % len(dorment))
        for maison, ident, reste in sorted(dorment,
                                           key=lambda x: -x[2])[:args.top]:
            print(u"    %-16s %-46s %3d a faire" % (maison, ident[:46], reste))

    ev = lire_journaux()
    titre(u"CE QUI A BOUGE — le mouvement, lu dans les journaux")
    if not ev:
        print(u"  LES DEUX JOURNAUX SONT VIDES, et ce n'est pas un calme plat :")
        print(u"  ils ont ete ouverts le 31.8 et ne savent RIEN d'avant. La")
        print(u"  photo ci-dessus reste juste ; le mouvement se remplira a la")
        print(u"  premiere ecriture par la porte, ou au prochain passage de")
        print(u"  `python scripts/reconcilier.py --vraiment`.")
        return
    present = None
    try:
        h = json.load(io.open(os.path.join(ETAT, "horloges.json"),
                              encoding="utf-8"))
        present = max([x for x in (minute_absolue(v) for v in h.values())
                       if x is not None] or [None])
    except Exception:
        present = None
    gardes = [e for e in ev if dans_la_fenetre(e, args, present)]
    print(u"  %d evenement(s) dans la fenetre, sur %d au journal"
          % (len(gardes), len(ev)))
    quoi = collections.Counter(e.get("quoi") for e in gardes)
    print(u"  %s" % u" · ".join(u"%s %d" % (k, v)
                                for k, v in quoi.most_common(10)))
    par_qui = collections.Counter(e.get("par") or u"(inconnu)"
                                  for e in gardes)
    cert = collections.Counter(e.get("certitude") for e in gardes)
    print(u"")
    print(u"  par qui   : %s" % u", ".join(u"%s %d" % (k, v)
                                           for k, v in par_qui.most_common(8)))
    print(u"  certitude : %s" % u", ".join(u"%s %d" % (k, v)
                                           for k, v in cert.most_common()))
    # DEUX SILENCES DIFFERENTS, ET LES CONFONDRE ETAIT UNE FAUTE : un
    # « constate » sans auteur est NORMAL (la reconciliation ne peut pas
    # savoir) ; un « declare » sans auteur est un TROU (l'ecriture est passee
    # par la porte, mais le lanceur n'avait pas pose LE_CONSEIL_QUI).
    muets_c = sum(1 for e in gardes
                  if not e.get("par") and e.get("certitude") == "constate")
    muets_d = sum(1 for e in gardes
                  if not e.get("par") and e.get("certitude") != "constate")
    if muets_c:
        print(u"  %d sans auteur en `constate` — normal : la reconciliation"
              u" sait QUE" % muets_c)
        print(u"  la ligne a bouge, jamais qui l'a bougee.")
    if muets_d:
        print(u"  %d sans auteur en `declare` — UN TROU : l'ecriture est"
              u" passee par la" % muets_d)
        print(u"  porte, mais son lanceur n'avait pas pose `LE_CONSEIL_QUI`.")
    bougees = collections.Counter(e.get("affaire") for e in gardes)
    if bougees:
        print(u"")
        print(u"  %-52s %s" % (u"les affaires qui ont bouge", u"evenements"))
        for k, v in bougees.most_common(args.top):
            print(u"    %-50s %3d" % (str(k)[:50], v))
