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
# LE DERNIER ETAT CONNU SANS PERTE. Voir `poser()` : c'est la seule source de
# `rendre_cellules.py`, et elle ne se laisse remplacer que par une passe qui
# n'a RIEN vu disparaitre.
SECOURS = os.path.join("histoire", "empreintes-sans-perte.json")
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


def _ecrire(chemin, instantane):
    dossier = os.path.dirname(chemin)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(chemin, "w", encoding="utf-8") as f:
        f.write(json.dumps(instantane, ensure_ascii=False, indent=1))


def poser(instantane, pertes=0, aveugle=False):
    u"""Pose l'empreinte — et le SECOURS seulement si rien n'a disparu.

    CE QUI EST ARRIVE LE 129.4.9, ET IL FAUT L'ECRIRE ICI. A 04 h 16 une
    conversion d'en-tetes a vide les cellules de sept volumes de
    `chambres/mj/books/`. A 04 h 49 min 45 s, CETTE fonction a pose sur le
    disque l'instantane du desastre : dans la meme seconde, la passe a
    journalise « 20 verrou.retiree, 15 clef.retiree » — elle a donc VU la
    perte — et elle a ecrase la seule copie qui la contenait encore.
    `rendre_cellules.py`, ecrit une demi-heure plus tot pour reparer par
    l'empreinte, n'avait plus rien a rendre. Le filet a ete range pendant la
    chute.

    LA REGLE, ET ELLE N'A PAS DE SEUIL. On ne demande pas « combien de lignes
    perdues justifient de garder une copie » : une seule ligne mesuree en vaut
    la peine, et tout chiffre qu'on poserait ici mangerait en silence les
    pertes plus petites que lui. Alors : le secours n'est remplace que par une
    passe qui n'a vu DISPARAITRE rien du tout. Une passe qui constate une
    perte, meme d'une ligne, meme relancee dix fois, ne peut pas y toucher.

    LE PRIX EST BORNE ET IL EST PAYE VOLONTIERS : un fichier de plus, et un
    secours qui peut vieillir. Vieux n'est pas dangereux ici — `rendre_
    cellules.py` NE REMPLIT QUE DU VIDE et ne touche jamais une cellule
    occupee, donc une source perimee ne peut rien detruire ; elle peut
    seulement avoir moins a rendre.

    LA PORTE DE DERRIERE, FERMEE LE 9e AU SOIR. `pertes = 0` a deux sens
    opposes et le code n'en voyait qu'un : « j'ai compare et rien n'a disparu »
    — et « JE N'AI RIEN PU COMPARER ». Sur une passe vierge (`avant` vide),
    aucune perte n'est calculee, `poser()` recoit zero, et le secours est
    remplace par ce qui traine sur le disque. Or `avant` est vide des que
    `empreintes.json` manque OU ne se parse pas : `_lire()` avale toutes les
    exceptions et rend None, donc une ecriture interrompue suffit a rendre une
    passe « vierge » sur un monde qui ne l'est pas. Un `--amorcer` lance de
    bonne foi le lendemain d'un degat aurait ecrase le secours du degat.

    D'ou `aveugle` : une passe qui n'a pas su comparer ne pose le secours que
    s'il n'existe pas encore. Elle ne peut plus jamais en remplacer un. Le prix
    est un secours qui vieillit d'un jour de plus, et il est nul — voir
    ci-dessus, `rendre_cellules.py` ne remplit que du vide.
    """
    _ecrire(os.path.join(ETAT, EMPREINTES), instantane)
    if pertes:
        return
    if aveugle and os.path.isfile(os.path.join(ETAT, SECOURS)):
        return
    _ecrire(os.path.join(ETAT, SECOURS), instantane)


def pertes_de(anciens, volumes):
    u"""Le nombre de lignes DISPARUES entre l'empreinte et le disque.

    Une ligne « retiree » n'est pas seulement une ligne supprimee : une ligne
    dont les cellules ont ete videes en place en produit une aussi, et c'est
    exactement le degat du 129.4.9 — gabarit conserve, contenu parti. On
    compte donc le meme evenement que le journal, sans le reecrire.
    """
    n = 0
    for ident in set(list(anciens) + list(volumes)):
        a, b = anciens.get(ident), volumes.get(ident)
        if a == b:
            continue
        for e in histoire.evenements_du_volume(a, b):
            if str(e.get("quoi") or "").endswith(".retiree"):
                n += 1
    return n


def passer(vraiment=False, amorcer=False):
    u"""Rend (comptes, total, vierge, courant, pertes)."""
    courant = maisons()
    avant = empreinte_posee()
    comptes, total, pertes = {}, 0, {}

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
        # ON COMPTE LES PERTES DANS TOUS LES CAS, meme a sec : c'est le
        # chiffre qui decide du secours, et c'est aussi celui qu'il faut
        # pouvoir lire AVANT d'ecrire quoi que ce soit.
        p = pertes_de(anciens, volumes)
        if p:
            pertes[maison] = p
        total += n
    # Les maisons DISPARUES comptent aussi : une chambre effacee emporte ses
    # affaires, et c'est un evenement.
    for maison in sorted(set(avant) - set(courant)):
        comptes[maison] = comptes.get(maison, 0)

    if vraiment:
        # `vierge` VAUT AVEUGLE, et c'est tout le point : cette passe n'a
        # compare avec rien, donc son zero de pertes ne prouve rien. La garde
        # se relit a l'APPEL, jamais a la definition.
        poser(courant, sum(pertes.values()), aveugle=vierge)
    return comptes, total, vierge, courant, pertes


def main(argv=None):
    ap = argparse.ArgumentParser(description=u"RECONCILIER — le journal des"
                                             u" affaires ecrites a la main.")
    ap.add_argument("--vraiment", action="store_true",
                    help=u"emet les evenements et pose l'empreinte")
    ap.add_argument("--amorcer", action="store_true",
                    help=u"pose l'empreinte SANS rien emettre")
    a = ap.parse_args(argv)
    comptes, total, vierge, courant, pertes = passer(a.vraiment or a.amorcer,
                                                     a.amorcer)
    print(u"RECONCILIER — %d maison(s), %d volume(s)"
          % (len(courant), sum(len(v) for v in courant.values())))
    for maison, volumes in sorted(courant.items()):
        print(u"  %-22s %3d affaire(s)   %s%s"
              % (maison, len(volumes),
                 (u"%d evenement(s)" % comptes.get(maison, 0))
                 if not vierge else u"—",
                 (u"   ⚠ %d DISPARUE(S)" % pertes[maison])
                 if pertes.get(maison) else u""))

    # LA PERTE SE DIT FORT, ET AU MOMENT OU ELLE PASSE. Le 129.4.9, la passe
    # a journalise 35 lignes disparues sans qu'aucune ligne de sortie ne le
    # dise : on l'a decouvert deux heures plus tard, en ouvrant les volumes.
    if pertes:
        print(u"\n⚠ %d LIGNE(S) ONT DISPARU DU DISQUE DEPUIS L'EMPREINTE."
              % sum(pertes.values()))
        print(u"Une ligne « disparue » est aussi bien une ligne SUPPRIMEE"
              u" qu'une ligne VIDEE en")
        print(u"place — gabarit conserve, contenu parti. Si ce n'est pas"
              u" voulu :")
        print(u"    python scripts/rendre_cellules.py <maison> --secours "
              u"    puis --vraiment")
        print(u"Le secours (`etat/histoire/empreintes-sans-perte.json`) n'a"
              u" PAS ete touche par")
        print(u"cette passe : il ne se laisse remplacer que par une passe qui"
              u" ne perd rien.")
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
