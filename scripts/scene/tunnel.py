# -*- coding: utf-8 -*-
# TUNNEL — un homme qui dévide au lieu de distiller.
#
# POURQUOI CE FICHIER EXISTE. Un acteur dépêché rentre avec une journée entière :
# quatorze pensées, une conclusion, cinq étapes, et c'est de la bonne matière —
# c'est bien le problème. La faute du MJ est alors de RECOPIER ce bloc en
# répliques successives. Le joueur reçoit un mur, il ne peut plus répondre sans
# appuyer sur Couper, et la salle cesse d'être une salle.
#
# CLAUDE.md le dit déjà, deux fois : « quatorze pensées donnent trois à six
# phrases. On distille, on ne dévide pas », et « des tranches de 2 à 4 items,
# ~30 à 50 s de lecture ». C'est précisément le genre de règle qu'on oublie au
# moment où l'on en aurait besoin, parce que la matière est trop bonne pour
# qu'on ait envie de la tailler. Une doctrine ne tient pas contre ça ; un
# compteur, si.
#
# CE QUI A CHANGÉ LE 12e — DEUX AVEUX. Les deux joueurs ont signalé le même mal
# le même jour, et l'avis sur la sortie d'erreur n'y avait rien fait.
#
#   1. UN AVIS QUI N'ARRÊTE RIEN NE S'ARRÊTE PAS DE PASSER. On lisait le
#      reproche, on trouvait la matière trop bonne, on poussait quand même. Il y
#      a donc désormais un PLAFOND DUR au double du seuil : au-delà, la poussée
#      est REFUSÉE. `--tunnel` passe outre — pour le mur voulu (un registre relu
#      tout haut, une lettre lue en entier, une chanson), et pour lui seul.
#
#   2. LE MUR N'EST PAS QUE DE LA LONGUEUR, C'EST DU NOMBRE D'AFFAIRES. Un
#      conseiller qui rentre ouvre onze fils en dix lignes : chacun est juste,
#      chacun appelle une décision, et le joueur en sort avec plus de travail
#      qu'il n'en avait. On compte donc aussi LES FILS OUVERTS — les demandes,
#      les blocs de suites, les questions rendues au joueur — et LES VOIX, parce
#      qu'une tranche où quatre hommes apportent chacun leur affaire est un mur
#      même quand chaque pièce est courte.
#
# Ce garde-fou NE JUGE TOUJOURS PAS LA PROSE : il compte des signes, des tours
# de parole et des mains tendues. Il n'a d'opinion sur rien d'autre.

import math
import sys

ITEM = 700       # signes, pour UNE réplique / geste / récit
TRANCHE = 2200   # signes de PNJ dans le même appel
SUITE = 4        # répliques d'affilée du MÊME locuteur
VOIX = 3         # locuteurs différents dans le même appel
FILS = 1         # affaires rendues au joueur dans le même appel

MUR = 2          # au-delà de ce multiple d'un seuil, on refuse la poussée

BAVARDS = ("replique", "geste", "recit")
CADENCES = BAVARDS + ("reponse", "suites", "table", "evenement", "breve",
                      "objectif", "marque")
CARACTERES_PAR_MINUTE = 1500


def cadencer(it):
    """Pose le délai web minimal correspondant au débit de lecture.

    Le navigateur joue les items séquentiellement et attend `delai_s` avant
    chacun : le plafond porte donc naturellement sur plusieurs poussées, pas
    seulement sur la tranche courante. Les entrées joueur et le hors-fiction
    ne passent pas par ce débit narratif.
    """
    if it.get("type") not in CADENCES:
        return 0
    minimum = int(math.ceil(
        len(it.get("texte") or "") * 60.0 / CARACTERES_PAR_MINUTE))
    actuel = it.get("delai_s", 0)
    try:
        actuel = float(actuel)
    except (TypeError, ValueError):
        actuel = 0
    it["delai_s"] = max(actuel, minimum)
    return it["delai_s"]


def _fils(it):
    """Ce que cet item RETOURNE au joueur comme travail à faire. (durs, mous)

    DURS : une `demande` accrochée à une réplique, un bloc de `suites`. Ce sont
    des mains tendues déclarées, sans interprétation possible — elles seules
    peuvent faire refuser une poussée.

    MOUS : une pièce de PNJ qui se termine sur une question, c'est-à-dire un
    homme qui renvoie sa décision à la table. Le signe est bon mais il ne
    distingue pas une question posée au joueur d'une question posée à un autre
    PNJ, et le cross-talk est voulu ; ça reste donc un avis, jamais un refus.
    """
    durs = 0
    mous = 0
    if it.get("demande"):
        durs += 1
    if it.get("type") == "suites":
        durs += 1
    if it.get("type") in ("replique", "geste"):
        if (it.get("texte") or "").rstrip().endswith("?"):
            mous += 1
    return durs, mous


def avis(items, argv=None):
    """Écrit sur stderr ce qui dépasse, refuse ce qui dépasse le double."""
    argv = sys.argv if argv is None else argv
    if "--tunnel" in argv:
        return

    total = 0
    suite = 0
    dernier = None
    longs = []
    trop_de_suite = None
    voix = []
    fils = 0
    fils_durs = 0

    for it in items:
        d, m = _fils(it)
        fils += d + m
        fils_durs += d

        if it.get("type") not in BAVARDS:
            suite, dernier = 0, None
            continue

        n = len(it.get("texte") or "")
        total += n
        if n > ITEM:
            longs.append((it.get("locuteur_id") or it.get("acteur_id")
                          or it.get("type"), n))

        qui = it.get("locuteur_id")
        if qui and qui not in voix:
            voix.append(qui)
        if qui and qui == dernier:
            suite += 1
        else:
            suite, dernier = 1, qui
        if suite > SUITE and trop_de_suite is None:
            trop_de_suite = (qui, suite)

    ecrire = sys.stderr.write

    if trop_de_suite:
        qui, n = trop_de_suite
        ecrire("TUNNEL : %s enchaine %d repliques dans le meme appel.\n" % (qui, n))
        ecrire("  Un homme rentre de session RAPPORTE ; il ne recite pas sa journee.\n")
        ecrire("  Distillez, et rendez la main : le joueur doit pouvoir repondre.\n")

    for qui, n in longs[:3]:
        ecrire("TUNNEL : %s, %d signes en une piece (au-dela de %d).\n"
               % (qui, n, ITEM))
        ecrire("  Coupez en deux, ou taillez : ce qui ne tranche rien ne se dit pas.\n")

    if total > TRANCHE:
        ecrire("TUNNEL : %d signes de PNJ dans cette tranche (au-dela de %d).\n"
               % (total, TRANCHE))
        ecrire("  CLAUDE.md : des tranches de 2 a 4 items, ~30 a 50 s de lecture.\n")
        ecrire("  Poussez ce qui est mur, gardez le reste — le flux est append-only.\n")

    if len(voix) > VOIX:
        ecrire("TUNNEL : %d voix dans la meme tranche (%s).\n"
               % (len(voix), ", ".join(voix[:6])))
        ecrire("  Une tranche ou chacun apporte SON affaire est un mur, meme courte.\n")
        ecrire("  Un homme, une affaire ; les autres attendent la tranche suivante.\n")

    if fils > FILS:
        ecrire("TUNNEL : %d affaires rendues au joueur dans la meme tranche.\n" % fils)
        ecrire("  On FERME avant d'ouvrir. Une seule chose a trancher a la fois ;\n")
        ecrire("  le reste est deja fait quand il l'apprend, ou attend son tour.\n")

    # Le plafond dur. Il ne juge rien de plus que ci-dessus : il refuse.
    refus = []
    if total > MUR * TRANCHE:
        refus.append("%d signes de PNJ (plafond %d)" % (total, MUR * TRANCHE))
    if longs and max(n for _, n in longs) > MUR * ITEM:
        refus.append("une piece de %d signes (plafond %d)"
                     % (max(n for _, n in longs), MUR * ITEM))
    if fils_durs > MUR * FILS:
        refus.append("%d mains tendues au joueur (plafond %d)"
                     % (fils_durs, MUR * FILS))
    if len(voix) > MUR * VOIX:
        refus.append("%d voix (plafond %d)" % (len(voix), MUR * VOIX))

    if refus:
        ecrire("\nTUNNEL - POUSSEE REFUSEE : %s.\n" % " ; ".join(refus))
        ecrire("  Rien n'a ete ecrit. Taillez et repoussez en deux tranches :\n")
        ecrire("  le flux est append-only, appeler ce script deux fois ne coute rien.\n")
        ecrire("  Si le mur est VOULU (un registre relu tout haut, une lettre lue\n")
        ecrire("  en entier, une chanson), repoussez la meme chose avec --tunnel.\n")
        raise SystemExit(2)
