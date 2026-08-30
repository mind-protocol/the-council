# -*- coding: utf-8 -*-
"""TROUS — ce que son plan montre a un homme : ses trous classes par
criticite, sa charge ailleurs, et ce qu'on attend de lui.
"""
import re as _re
import sys

from agents.depeche.brief import lire, ETAT

# ─────────────────────────────────────────────── ce que son plan montre
# LES TROUS DE SES PROPRES CAHIERS. Ce n'est pas une file de demandes qu'on lui
# assigne : c'est ce qu'un homme competent voit en ouvrant son cahier, et sur
# quoi il travaille sans qu'on le lui ordonne. Le manuel pose « pas de source,
# pas de pensee » — ceci EST une source, au meme titre qu'un registre depouille.
#
# LA BORNE EST DURE : le schema donne trois a cinq etapes a une tete du
# quartier, et le plus charge des hommes porte quatre-vingts trous. On lui en
# montre CINQ, les plus debloquants, et il prend ce qu'il peut porter. Ce qu'il
# laisse reste ; un homme qui laisse vingt trous ouverts trois lunes durant est
# une information sur lui, pas un defaut d'ici.
#
# RIEN NE S'ECRIT : ni ici, ni dans `intentions.json`. Il ecrit son etape de sa
# main, pendant sa session. On lui donne la matiere, jamais la decision.
#
# La derivation n'est pas refaite ici : elle vient d'`etat_du_plan.py`, qui la
# tient de `couverture.py` — un seul lecteur du graphe, une seule verite.
#
# ─── CE QUI RANGE LES CINQ, ET POURQUOI CA A CHANGE ──────────────────────────
#
# C'etait `force()`, un bareme ecrit a la main : 0 pour une rupture, 1 pour « le
# seul verrou qui l'en separe », 1+N pour « un verrou sur N », 20 pour une
# action, 60 pour le reste. Il classe la GRAVITE DU DEFAUT, et il ne connait du
# plan que le cahier qu'il regarde. Deux trous egalement « seuls verrous » y
# sont donc a egalite, meme quand l'un tient onze etats cibles et l'autre zero.
#
# On les range desormais par ce que la piece visee TIENT REELLEMENT —
# `criticite.py`, perte plus ce qu'on lui doit ailleurs. C'est la seule mesure
# qui traverse les trente-six cahiers, et c'est tout l'interet : les cinq lignes
# qu'un homme lit le matin sont les cinq qui ouvrent le plus de plan, et non les
# cinq dont le defaut se decrit le plus gravement.
#
# LES RUPTURES RESTENT EN TETE, ET CE N'EST PAS UNE POLITESSE ENVERS L'ANCIEN
# BAREME. Une chaine cassee au milieu ne remonte a aucun etat cible : sa piece
# vaut donc ZERO au contrefactuel, par construction. Ranger sur le seul score
# les enterrerait toutes — la mesure dirait « sans consequence » de ce qui est
# precisement le plus casse. Le guide est net : une action qui ne remonte a rien
# n'a pas de raison strategique demontree, elle se supprime ou se requalifie.
# On garde donc deux etages : les ruptures d'abord, le score ensuite.
#
# CE QUE CA NE FAIT PAS. Le routage ne bouge pas : un homme ne voit que les
# cahiers dont il est `tenu_par`. Le score sait pourtant dire quelle piece tombe
# sur QUEL office, ce qui permettrait de lui montrer ce qui est de sa charge
# dans les cahiers d'un autre — c'est le gain suivant, et il est plus gros que
# celui-ci. Il attend une decision : ouvrir la reserve d'un homme aux affaires
# qu'il ne tient pas, c'est changer ce qu'est un cahier.
TROUS_MONTRES = 5


def _scores(vue_de=None):
    """{numero: perte + attendu}. Vide si le calcul echoue — on retombe alors
    sur `force()`, et l'homme part quand meme."""
    try:
        from plan.expose import criticite
        import plan_modele as PM
        pieces = PM.charger(vue_de)["pieces"]
        lignes, _base, _poids, _s, _m, dehors = criticite.calculer(pieces)
        crit = {n: c for c, pt, n, p in lignes}
        # `dehors` porte ce qui, dans un AUTRE cahier, attend cette piece : on
        # l'ajoute a sa perte, parce qu'un homme doit voir ce qu'il fait
        # attendre ailleurs autant que ce qu'il bloque chez lui.
        att = {n: sum(crit.get(m, 0) for m in ms) for n, ms in dehors.items() if ms}
        return {n: crit.get(n, 0) + att.get(n, 0) for n in set(crit) | set(att)}
    except Exception as e:
        sys.stderr.write(u"  (criticite indisponible, on retombe sur force() : %s)\n" % e)
        return {}


import re as _re
import sys
_NUM_ACTE = _re.compile(r"\d{3,6}")


def _rang(m, scores, force):
    """Les ruptures d'abord, puis le plus debloquant. Le numero de la piece se
    lit sur la clef de l'acte, qui l'y a deja mis (`clef/28017`, `office/220`)."""
    if not scores:
        return (force(m), m["acte"])
    rupture = 0 if m.get("nature") == "rupture" else 1
    ns = _NUM_ACTE.findall(m.get("acte") or u"")
    return (rupture, -(scores.get(ns[0], 0) if ns else 0), m["acte"])


def ses_trous(qui, combien=TROUS_MONTRES):
    try:
        from plan.expose import etat_du_plan as plan
        from plan.expose import nu
        import plan_modele as PM
        modele = PM.charger(qui)
        pieces, affaires = modele["pieces"], modele["affaires"]
        siennes = [b for b in affaires if (b.get("tenu_par") or u"") == qui]
        tout = []
        for b in siennes:
            nom = nu(b["titre"])
            for m in plan.missions_de(nom, pieces):
                # CE QUI N'EST PAS DE SON RESSORT NE PART PAS AVEC LUI. « Deux
                # plans, ou un seul ? » est une décision de maison ; la poser à
                # un homme dépêché, c'est lui donner un travail qu'il ne peut
                # pas faire et occuper la première ligne de sa réserve avec.
                # Elle reste au conseil, dans `etat_du_plan.py --qui`.
                if m["acte"].startswith(u"registre/"):
                    continue
                tout.append((m, nom))
        scores = _scores(qui)
        tout.sort(key=lambda x: _rang(x[0], scores, plan.force))
        if not tout:
            return u""
        lignes = [u"%d. %s\n   (%s)" % (i, plan.phrase(m), nom)
                  for i, (m, nom) in enumerate(tout[:combien], 1)]
        reste = (u"\n\nLe plan en montre %d autres sur tes affaires. Elles attendront."
                 % (len(tout) - combien)) if len(tout) > combien else u""
        return (u"\n## Ce que ton plan montre, ce matin\n\n"
                u"Tes cahiers portent des trous que personne ne t'a demandé de "
                u"combler — c'est ton affaire, et tu les vois comme on voit un "
                u"compte qui ne tombe pas juste. Les plus débloquants d'abord :\n\n"
                + u"\n".join(lignes) + reste
                + u"\n\nPrends ce que ta journée peut porter, et laisse le reste. "
                  u"Ce ne sont pas des ordres : ce sont les trous du plan. Ce que "
                  u"tu en fais s'écrit de ta main, dans tes pensées et ton "
                  u"cahier.\n")
    except Exception as e:
        # Une dépêche ne tombe JAMAIS pour un défaut de cette greffe : sans ses
        # trous, l'homme part quand même, et la raison se lit sur la sortie.
        sys.stderr.write(u"  (trous indisponibles pour %s : %s)\n" % (qui, e))
        return u""


# ─────────────────────── CE QUI TOMBE SUR LUI HORS DE SES CAHIERS
#
# LE ROUTAGE NE TENAIT QUE SUR `tenu_par`, ET C'ETAIT TROP ETROIT. Un homme
# repond de pas ecrits noir sur blanc sous SON office, dans le cahier d'un
# autre ; et il tient des moyens que d'autres engagent sans que son nom soit sur
# la ligne. Personne ne les lui cachait — aucun chemin ne les lui portait. Sur
# les vingt-six titulaires, la mesure disait Gerardys aveugle a 54 % et lord
# Corlys a 100 %.
#
# ─── CE QU'ON A ESSAYE D'ABORD, ET QUI DONNE ZERO ────────────────────────────
#
# Passer ces deux canaux par `missions_de`, comme le seau des cahiers. Mesure :
# 268 missions sur 44 cahiers, dont ZERO tombant sur l'office d'un autre. Un
# trou vise un verrou ou une clef, et NI L'UN NI L'AUTRE NE PORTE D'OFFICE —
# seules les actions en ont un. La ou une mission vise bien une action, cette
# action est du cahier qu'on regarde, donc de son propre tenant.
#
# « Sa charge ailleurs » n'est donc pas un ensemble de defauts : c'est un
# ensemble d'AFFECTATIONS. Un pas de l'office de Corlys pose dans le cahier de
# maitre Rulf et parfaitement redige ne produit aucun trou — et c'est pourtant
# exactement ce que Corlys doit savoir. L'unite est le PAS, non fait.
#
# ─── LA BORNE QUI TIENT TOUT ─────────────────────────────────────────────────
#
# A ET B SE FONT, C SE REPOND. C'est la reponse a la question que ce fichier
# laissait ouverte depuis le debut — « ouvrir la reserve d'un homme aux affaires
# qu'il ne tient pas, c'est changer ce qu'est un cahier ». On ne l'ouvre pas :
# on ajoute deux canaux d'une AUTRE NATURE. Un homme n'ecrit jamais dans le
# cahier d'un autre ; sur sa charge il va voir le tenant, sur ce qu'on lui tire
# il envoie un mot. Sans cette borne, deux mains ecrivent la meme ligne et l'on
# perd la seule chose que `tenu_par` garantissait.
#
# ─── DES PLACES FIXES, PARCE QUE LE VOLUME LE COMMANDE ───────────────────────
#
# Gerardys porte 133 pas qui tirent sur ses moyens. Fusionner les trois seaux
# dans un seul tri de cinq lignes ferait disparaitre SON cahier sous la charge
# des autres, ce qui est exactement l'inverse du but. Donc : 3 places au sien,
# un bloc de 3 lignes par canal, plafonne en dur. Le tunnel ne se contourne pas
# parce que la matiere est bonne.
TROUS_AILLEURS = 3

# « faite », « close », « ✅ faite », « FAITE le 3e j. de la 4e lune… » : la
# colonne d'etat est de la prose, et un homme y ecrit sa preuve a la suite du
# mot. On teste donc le DEBUT, jamais l'egalite.
_FAIT = _re.compile(u"^\\s*\\**\\s*(faites?|faits?|closes?|✅)", _re.I)


def _restants(paquet):
    """Les pas d'un seau qui restent à faire, le plus lourd en tête. Un pas fait
    ne tire plus rien : il n'a rien à faire dans une réserve."""
    return [(s, n, p) for s, n, p in paquet
            if p.get("genre") == "action" and not _FAIT.match(p.get("etat") or u"")]


def _par_cahier(paquet):
    """Groupé par cahier, les cahiers les plus lourds d'abord. On ne liste pas
    des pas : on nomme des VOLUMES, avec le compte et le poids dedans."""
    par = {}
    for s, n, p in paquet:
        d = par.setdefault(p.get("affaire") or u"— hors cahier —",
                           {"s": 0.0, "n": 0, "tete": None})
        d["s"] += s
        d["n"] += 1
        if d["tete"] is None:
            d["tete"] = p            # le paquet arrive déjà trié par poids
    return sorted(par.items(), key=lambda x: -x[1]["s"])


def sa_charge_ailleurs(qui, combien=TROUS_AILLEURS):
    """Les pas dont SON office répond, dans le cahier d'un autre. Ça se FAIT :
    il va voir le tenant du volume, et le pas est à lui."""
    try:
        from plan.expose import criticite
        _vu, sien, _tire = criticite.charge_de(qui)
        groupes = _par_cahier(_restants(sien))
        if not groupes:
            return u""
        lignes = [u"- **%s** — %d pas sous ton office. Le plus lourd : « %s »"
                  % (a, d["n"], (d["tete"] or {}).get("nom", u"?"))
                  for a, d in groupes[:combien]]
        reste = (u"\n\nIl y en a dans %d autre(s) cahier(s)." % (len(groupes) - combien)
                 if len(groupes) > combien else u"")
        return (u"\n## Ta charge, dans les cahiers des autres\n\n"
                u"Ces pas-là portent TON office. Le cahier est à un autre, le "
                u"travail est à toi — et personne ne te l'a dit jusqu'ici, "
                u"parce qu'aucun chemin ne te le portait.\n\n"
                + u"\n".join(lignes) + reste
                + u"\n\nTu vas voir le tenant du volume, et vous réglez. **Tu "
                  u"n'écris pas dans le cahier d'un autre** : ce qui s'y change "
                  u"se change par sa main, ou par la tienne s'il te la donne.\n")
    except Exception as e:
        sys.stderr.write(u"  (charge ailleurs indisponible pour %s : %s)\n" % (qui, e))
        return u""


def on_lattend(qui, combien=TROUS_AILLEURS):
    """Les pas qui engagent un moyen qu'il tient, sans que son nom soit sur la
    ligne. Ça se RÉPOND : ce n'est pas son travail, c'est quelqu'un qui attend."""
    try:
        from plan.expose import criticite
        _vu, _sien, tire = criticite.charge_de(qui)
        groupes = _par_cahier(_restants(tire))
        if not groupes:
            return u""
        # AGREGE PAR DEMANDEUR, JAMAIS LISTE. Les 133 pas de Gerardys en clair
        # sont un mur ; ce qui l'interesse est QUI attend et SUR QUOI.
        lignes = []
        for a, d in groupes[:combien]:
            ms = u" ".join((d["tete"] or {}).get("moyens") or []) or u"—"
            lignes.append(u"- **%s** — %d pas engagent ce que tu tiens (%s)"
                          % (a, d["n"], ms))
        reste = (u"\n\nEt %d autre(s) cahier(s) attendent de même."
                 % (len(groupes) - combien) if len(groupes) > combien else u"")
        return (u"\n## Ce qu'on attend de toi sans te l'avoir demandé\n\n"
                u"Ces cahiers-là engagent un moyen dont tu réponds. **Ce n'est "
                u"pas ton travail** : ce sont des gens bloqués par toi, qui ne "
                u"savent peut-être pas qu'ils t'attendent.\n\n"
                + u"\n".join(lignes) + reste
                + u"\n\nTu réponds — un mot, une heure, un refus net. Ce que tu "
                  u"ne peux pas donner, dis-le tout de suite plutôt que de le "
                  u"laisser attendre.\n")
    except Exception as e:
        sys.stderr.write(u"  (ce qu'on lui tire indisponible pour %s : %s)\n" % (qui, e))
        return u""

