# -*- coding: utf-8 -*-
# La carte muette — un conseil qui nomme des places et ne touche jamais la table.
#
# POURQUOI CE FICHIER EXISTE, ET POURQUOI IL RESSEMBLE À `tunnel.py`. La règle
# est écrite deux fois — dans `CLAUDE.md` (« un acteur pose la pièce dès que ce
# qu'il dit a un endroit ») et dans `docs/metier.md` (« La main sur la table »).
# Elle a été écrite le 2e jour de la 4e lune. Voici ce que le flux disait ce
# jour-là, AVANT qu'on l'écrive, et il n'y a aucune raison de croire qu'une
# doctrine de plus y changerait quoi que ce soit :
#
#     3428 items de parole ou de geste
#       23 portent une main sur la carte ............. 0,7 %
#      505 nomment un LIEU et un NOMBRE
#        0 de ces 505 posent quoi que ce soit ........ 100 %
#
#     corlys  « Quatre-vingt-dix voiles en croissant sur le Gosier, Votre Grâce.
#               Lamarck en arsenal, Marée-Haute en… »
#
# Quatre-vingt-dix voiles, trois places nommées, et la table peinte n'a rien vu
# passer. C'est le geste le plus sous-employé du jeu, et le seul qui transforme
# une réplique en énoncé.
#
# CE QU'IL COMPTE, ET CE QU'IL NE JUGE PAS. Un déclencheur, c'est un `replique`
# ou un `geste` qui nomme une place connue ET un nombre, sans rien poser. On ne
# lit pas l'intention, on ne pèse pas la prose : on compte des noms de lieux et
# des chiffres, exactement comme le tunnel compte des signes.
#
# IL Y A DES FAUX POSITIFS, ET C'EST PRÉVU. « Six jours de colonne vers
# Sombreval », « trois cents âmes du bourg » nomment un lieu et un nombre sans
# rien devoir à la table. On ne réclame donc JAMAIS une main par déclencheur :
# on regarde la TRANCHE. Zéro main sur trois occasions, c'est un conseil qui
# parle de places sans jamais y toucher ; une main sur trois suffit à dire que
# le geste est dans les mœurs.
#
# ON AVERTIT, ON NE REFUSE PAS ENCORE — et c'est délibéré. Le tunnel a appris
# qu'un avis qui n'arrête rien ne s'arrête pas de passer, et il a raison ; mais
# il a posé son plafond APRÈS avoir mesuré, pas avant. Partant de 0,7 %,
# n'importe quel seuil mordrait, ce qui ne prouve rien. `REFUS` reste donc à
# `None` le temps d'une journée de jeu ; on le pose au vu du nouveau chiffre.
# Régler un plafond sur une intuition, c'est ce qu'on vient de reprocher à la
# note du sommet du plan.
#
# CE QU'IL NE SAURA JAMAIS FAIRE : l'échiquier. La carte se déclenche sur un
# lieu, qui est un mot ; l'échiquier se déclenche sur un argument qui EST une
# chaîne, et aucun compteur ne voit ça. Pour lui il n'y a que la doctrine — et
# le fait que `montre` remonte tout seul les adresses citées dans le texte.
# Mieux vaut le dire que prétendre le contraire.
import io
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PARLANTS = ("replique", "geste")
DECLENCHEURS = 3      # à partir de combien d'occasions muettes on le dit
REFUS = None          # le plafond dur, à poser au vu de la mesure du lendemain

# Les nombres qui comptent sur une carte s'écrivent aussi en toutes lettres —
# « quatre-vingt-dix voiles » est le meilleur exemple du dépôt, et un motif qui
# ne connaîtrait que les chiffres l'aurait manqué.
CHIFFRE = re.compile(
    u"\\b\\d+\\b|\\b(deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|"
    u"treize|quatorze|quinze|seize|vingt|trente|quarante|cinquante|soixante|"
    u"cent|cents|mille)\\b", re.I)

# Ce que le genre d'un jeton doit être, deviné sur le mot qui accompagne le
# nombre. C'est une SUGGESTION collée dans l'avis, jamais une écriture : celui
# qui parle sait mieux que ce motif ce qu'il pose.
GENRES = [(u"voile|coque|quille|galère|galere|nef|barque|flotte", u"flotte"),
          (u"dragon|aile|bête|bete", u"dragon"),
          (u"cavalier|cheval|monture", u"cavalerie"),
          (u"homme|lance|épée|epee|pique|manteau|garde|guet", u"armee"),
          (u"muid|grain|pain|vivre|tonneau|mouton", u"vivres"),
          (u"pli|corbeau|lettre|cage", u"pli")]


# LES EAUX N'ONT PAS DE FICHE. `lieux.json` tient vingt et une PLACES — des
# châteaux, des villes, des îles —, et pas une seule étendue d'eau. Or le
# meilleur exemple du dépôt est « quatre-vingt-dix voiles en croissant sur le
# GOSIER » : un détroit, une flotte, un nombre, et rien pour l'attraper. Ces
# noms-là se posent donc à la main, et c'est assumé — ils sont cinq, ils ne
# bougeront pas, et leur donner une fiche de lieu serait leur promettre une
# garnison et un suzerain qu'ils n'auront jamais.
EAUX = {u"Gosier": u"gosier", u"Néra": u"nera", u"Trident": u"trident",
        u"baie de la Néra": u"baie-nera", u"détroit": u"detroit"}


def _lieux():
    """{nom écrit -> id de place}. Trois sources, et aucune n'est de trop :
    `lieux.json` pour les places, les tables de guerre de chaque siège pour ce
    qu'on y a réellement posé, les eaux à la main. Les noms de moins de quatre
    lettres sont écartés — « Œil » ou « Bas » attraperaient la moitié de la
    prose."""
    out = dict(EAUX)
    try:
        d = json.load(io.open(os.path.join(RACINE, "etat", "lieux.json"),
                              encoding="utf-8"))
        L = d if isinstance(d, list) else (d.get("lieux") or [])
        for x in L:
            n = (x.get("nom") or u"").strip()
            if len(n) > 3:
                out[n] = x.get("id") or n.lower()
            # « Lamarck (Marée-Haute) » porte DEUX noms dans une seule cellule,
            # et c'est le second qu'on prononce à table.
            for alt in re.findall(u"\\(([^)]{4,})\\)", n):
                out[alt.strip()] = x.get("id") or n.lower()
    except Exception:
        pass
    # Ce que les tables de guerre portent déjà : un id qu'on a posé un jour est
    # un endroit dont on parle. On le rend lisible faute de mieux.
    try:
        import glob
        vus = set()

        def marche(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "ou" and isinstance(v, str):
                        vus.add(v)
                    marche(v)
            elif isinstance(o, list):
                for x in o:
                    marche(x)
        for f in glob.glob(os.path.join(RACINE, "etat", "joueurs", "*", "jetons.json")):
            marche(json.load(io.open(f, encoding="utf-8")))
        for i in vus:
            n = i.replace(u"-", u" ").strip()
            if len(n) > 3 and n.capitalize() not in out:
                out[n.capitalize()] = i
    except Exception:
        pass
    return out


def _genre(texte):
    t = texte.lower()
    for motif, g in GENRES:
        if re.search(motif, t):
            return g
    return u"armee"


def _pose(it):
    """Cet item touche-t-il la table ? Un `montre` de LIVRE n'y touche pas — il
    ouvre un registre, ce qui est un autre geste et ne dit rien d'un endroit."""
    if it.get("type") == "table":
        return True
    m = it.get("montre") or {}
    return bool(m.get("jetons") or m.get("traits") or m.get("zones"))


def avis(items, argv=None):
    """Écrit sur stderr les occasions manquées. Ne bloque rien tant que `REFUS`
    est None ; lève alors la même erreur que le tunnel quand il sera posé."""
    argv = sys.argv if argv is None else argv
    if "--muet" in argv or "--tunnel" in argv:
        return
    lieux = _lieux()
    if not lieux:
        return
    motif = re.compile(u"|".join(re.escape(n) for n in
                                 sorted(lieux, key=len, reverse=True)))

    mains = sum(1 for it in items if _pose(it))
    manques = []
    for it in items:
        if it.get("type") not in PARLANTS or _pose(it):
            continue
        t = it.get("texte") or u""
        pl = motif.findall(t)
        nb = CHIFFRE.search(t)
        if pl and nb:
            manques.append((it.get("locuteur_id") or it.get("acteur_id") or u"?",
                            pl[0], lieux[pl[0]], nb.group(0), _genre(t)))

    if len(manques) < DECLENCHEURS or mains:
        return

    e = sys.stderr
    e.write(u"\n  🗺️  LA TABLE EST RESTÉE MUETTE — %d occasions, aucune main.\n"
            % len(manques))
    for qui, place, ident, n, g in manques[:3]:
        e.write(u"      %s nomme « %s » et « %s » et ne pose rien.\n"
                % (qui, place, n))
        # LA SUGGESTION NE DEVINE PAS CE QU'IL VOULAIT DIRE. Elle pose la place
        # et le genre lu sur le mot qui accompagne le nombre, et laisse `force`
        # et `nom` à celui qui parle : « quatre-vingt-dix » n'est pas un chiffre,
        # et « Trois Sombreval » n'est le nom de rien.
        e.write(u'        "montre": {"jetons": [{"id": "%s-%s", "genre": "%s",'
                u' "camp": "noir", "ou": "%s", "force": %s, "nom": "…"}]}\n'
                % (g, ident, g, ident, n if n.isdigit() else u"…"))
    if len(manques) > 3:
        e.write(u"      … et %d autres.\n" % (len(manques) - 3))
    e.write(u"      Une réplique qui nomme un lieu ET un nombre pose la pièce :"
            u" on ne dit pas\n      « la flotte tiendra le Gosier », on met trois"
            u" doigts dessus. `--muet` passe outre.\n")

    if REFUS is not None and len(manques) >= REFUS:
        raise SystemExit(u"  ⛔ poussée refusée : %d occasions, aucune main sur"
                         u" la carte." % len(manques))
