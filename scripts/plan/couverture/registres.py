# -*- coding: utf-8 -*-
"""REGISTRES — les quatre index derives des cahiers, et leur garde d'ecart.
"""
import json
import os
import re

import bibliotheque

from plan.couverture.lecture import (nu, sans_emoji, genre_de, numero_de,
                                     RACINE)

# Le suffixe des tables calculees. Il vit ici parce que deriver() le pose et
# que ecart_registres() le verifie ; ecrire.py le reprend pour les blocs.
CALCULE = u" — calculé, ne pas écrire à la main"

# ═══════════════════════════════════════════════ LES REGISTRES DÉRIVÉS
#
# UN SEUL PLAN. Les cahiers d'affaire sont la vérité ; les quatre registres par
# type sont un INDEX, régénéré depuis eux et jamais écrit à la main. La règle du
# guide — « quand l'affaire et le registre se contredisent, c'est le registre qui
# a raison » — supposait un registre tenu ; il ne l'était plus (108 lignes contre
# 1312), et deux copies d'un même plan n'est pas un défaut de propreté : c'est
# une machine à envoyer les hommes contre des fantômes. Voir docs/echiquier.md.
#
# `plan-moyens` ET `plan-offices` N'EN SONT PAS, ET NE LE SERONT JAMAIS. Ce ne
# sont pas des copies : ce sont les SOURCES de l'inventaire M/O. Six moyens et
# dix-sept offices n'existent nulle part ailleurs, et quarante-huit numéros M/O
# sont cités par les actions des cahiers, qui ne les définissent jamais. On ne
# dérive pas d'un vide — les régénérer « par symétrie » n'en laisserait rien.
REGISTRES = {u"plan-etats-cibles": "etat", u"plan-verrous": "verrou",
             u"plan-clefs": "clef", u"plan-actions": "action"}

# ─── QUATRE COLONNES, ET UNE SEULE DE SENS. Pourquoi celles-là.
#
# La forme minimale — numéro, nom, affaire, renvoi — pesait un dixième et TUAIT
# LA RECHERCHE PAR CONTENU : « quelle clef parle des coques » ne rendait plus
# rien, et c'est exactement ce pour quoi on ouvre un index. On garde donc la
# seule colonne qui IDENTIFIE la chose.
#
# Ce qu'on retire — la preuve, le levé-quand, le prix, la dépendance, l'office,
# les moyens, l'avancement, le `📍 Où` — sert à TRAVAILLER, donc appartient au
# cahier. L'index dit où la chose est écrite ; il ne la refait pas.
#
# ET LE VRAI GAIN N'EST PAS LES OCTETS : ce qui reste est ce qui ne bouge
# presque jamais. Un nom et une définition changent rarement — Le Sanglier en a
# corrigé cinq en une nuit, et c'était un événement. Les colonnes qu'on retire
# sont les plus volatiles de toutes : un avancement bouge chaque jour, un office
# à chaque nomination. MOINS L'INDEX PORTE DE CHOSES QUI CHANGENT, MOINS IL A
# D'OCCASIONS DE MENTIR. C'est la même raison qui a fait dériver ces registres,
# poussée d'un cran.
SENS = {"etat": u"✅ Ce qui doit être vrai", "verrou": u"📌 Ce qui est vrai aujourd'hui",
        "clef": u"💡 Le principe", "action": u"📝 Ce qu'on fait"}
NUMERO = {"etat": u"🎯 N°", "verrou": u"🔒 N°", "clef": u"🗝️ N°", "action": u"⚔️ N°"}
NOM = {"etat": u"🏷️ L'état", "verrou": u"🏷️ Le verrou", "clef": u"🏷️ La clef",
       "action": u"🏷️ L'action"}
AFFAIRE = u"🏰 Affaire"


def colonnes_de(genre):
    return [NUMERO[genre], NOM[genre], SENS[genre], AFFAIRE]

# LA TRANSPOSITION SE FAIT PAR EN-TÊTE, JAMAIS PAR RANG : les deux formes n'ont
# pas les colonnes dans le même ordre. Exact d'abord, puis ces alias explicites —
# et rien d'autre. Un repli par inclusion a déjà coûté huit chaînes : `sq("N°")`
# vaut « n », qui est un sous-mot de « ou ca en est », et la colonne d'avancement
# atterrissait en position 0, à la place du numéro.
ALIAS = {u"ce qu'on fait, et ou": u"ce qu'on fait",
         u"ou ca en est": u"etat",
         u"ce qu'elle coute et ce qu'elle ferme": u"le prix",
         u"la preuve attendue": u"la preuve",
         u"retenue": u"decision"}

# CE QUI NE DESCEND PAS, ET CE N'EST PAS UNE PERTE. Quatre colonnes de cahier
# n'ont aucun logis au registre : `📍 Où` (pour les actions — l'état cible, lui,
# a bien la sienne), `⛓️ Dépend de`, `🚪 Ce que cela ferme`, `📅 Jour dû`. Le
# registre dérivé est donc PLUS PAUVRE que les cahiers, et c'est sa nature : un
# index n'a pas à tout porter, il a à dire où la chose est écrite. Le jour où
# quelqu'un criera à la perte d'information, la réponse est cette phrase-ci.


def _sq(s):
    """L'en-tête réduit à ce qui l'identifie : sans signe, sans accent, sans casse."""
    s = sans_emoji(s).lower().replace(u"’", u"'")
    for a, b in ((u"àâä", u"a"), (u"éèêë", u"e"), (u"îï", u"i"),
                 (u"ôö", u"o"), (u"ùûü", u"u"), (u"ç", u"c")):
        for c in a:
            s = s.replace(c, b)
    return u" ".join(s.split())


def lire_cahiers(livres):
    """Les pièces de plan telles qu'elles sont ÉCRITES dans les cahiers :
    en-tête → cellule, plus le nom de l'affaire qui les porte. C'est la matière
    de l'index, et elle ne vient de nulle part ailleurs."""
    par_genre = {g: {} for g in set(REGISTRES.values())}
    tous = {}
    for b in livres:
        # LES CAHIERS `nera-*` N'ALIMENTENT PAS CES REGISTRES — ils sont d'un
        # AUTRE SIÈGE. Le plan de la Néra a ses propres index dans le coffret
        # `boite-plan-nera` (`nera-etats`, `nera-verrous`, `nera-clefs`,
        # `nera-actions`) ; les six d'ici vivent dans `boite-grand-plan`. Verser
        # les 49 pièces de la Néra dans l'index de la reine mélangerait deux
        # plans que rien ne relie — et leur M01 n'est même pas le nôtre : c'est
        # « La porte de la Gadoue », quand le nôtre est « Les voiles du Gosier ».
        if not str(b.get("id") or u"").startswith("affaire-"):
            continue
        for t in (b.get("tables") or []):
            g = genre_de(t.get("titre") or u"")
            if g not in par_genre:
                continue
            cols = t.get("colonnes") or []
            for l in (t.get("lignes") or []):
                c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
                if len(c) < 2 or not c[0] or not c[1]:
                    continue
                m = numero_de(c[0])
                if not m:
                    continue
                par_genre[g][m.group(1)] = {
                    "brut": c[0], "nom": c[1], "affaire": nu(b.get("titre")),
                    "cellules": dict(zip([_sq(x) for x in cols], c))}
                tous.setdefault(m.group(1), set()).add(g)
    return par_genre, tous


def deriver(livres):
    """Refait les quatre registres depuis les cahiers. Ne touche à rien : rend
    ce qu'il ÉCRIRAIT, plus la liste de ce qu'il refuse de toucher.

    ON N'EFFACE JAMAIS PAR OMISSION. Le temps précédent effaçait explicitement,
    sous garde ; celui-ci pourrait effacer par silence, ce qui est bien pire —
    une ligne qui disparaît d'un index régénéré ne laisse pas de trace. Deux
    familles sont donc CONSERVÉES telles quelles, et dites à chaque passage :

      · sans cahier — aucune source ne la produit (21010, 21020 : la clef et son
        verrou dont les trois actions portent « CÉDÉ AU 6000 » dans leur propre
        prose, et qui attendent un repointage qu'un homme seul peut décider) ;
      · nom divergent — un cahier porte bien ce numéro, mais sous un autre nom.
        Ce peut être un renommage (23000 : « Donjon ouvert » devenu « Le Donjon
        a changé de main sans combat dans les murs ») ou un NUMÉRO RECYCLÉ par
        une autre affaire (le bloc 7xxx, où « La ville de Port-Réal » a cédé la
        place au Trident et à Harrenhal). Les deux se ressemblent trait pour
        trait et ne se distinguent pas au calcul. Écraser un recyclage, ce
        serait perdre la dernière trace d'une affaire entière. On refuse.
    """
    cah, tous = lire_cahiers(livres)
    sorties = {}
    for b in livres:
        bid = str(b.get("id") or u"")
        if bid not in REGISTRES:
            continue
        g = REGISTRES[bid]
        neuves_cols = colonnes_de(g)
        # OÙ LIRE LE SENS DANS LA FORME QU'ON TROUVE SUR LE DISQUE. Les lignes
        # conservées viennent de l'ancienne forme (huit ou neuf colonnes) ou de
        # la neuve (quatre), selon qu'on repasse ou non. On repère donc la
        # colonne de sens dans les en-têtes ACTUELS du registre : exact d'abord,
        # puis un préfixe ancré — « ce qu'on fait, et où » commence par « ce
        # qu'on fait ». Le préfixe ne sert QUE sur les en-têtes du registre,
        # jamais sur ceux des cahiers, où il rouvrirait le repli par inclusion
        # qui a fait atterrir l'avancement à la place du numéro.
        vieilles = [_sq(x) for x in (b.get("colonnes") or [])]
        cible = _sq(SENS[g])
        i_sens = next((i for i, k in enumerate(vieilles) if k == cible), None)
        if i_sens is None:
            i_sens = next((i for i, k in enumerate(vieilles) if k.startswith(cible)), None)
        i_aff = next((i for i, k in enumerate(vieilles) if k == u"affaire"), None)

        anciennes = {}
        for l in (b.get("lignes") or []):
            c = [nu(x) for x in ((l if isinstance(l, list) else l.get("cellules")) or [])]
            if not c or not c[0]:
                continue
            m = numero_de(c[0])
            if m:
                anciennes[m.group(1)] = c

        def transposer(c, motif):
            """Une ligne conservée passe à la forme neuve : deux formes dans un
            même tableau est une invitation à la confusion, et ce qu'elle perd
            est justement ce qui ne devait plus y être."""
            return {"cellules": [
                c[0],
                c[1] if len(c) > 1 else u"",
                c[i_sens] if (i_sens is not None and i_sens < len(c)) else u"",
                (c[i_aff] if (i_aff is not None and i_aff < len(c)) else u"") or motif]}

        lignes, gardees, sans_logis = {}, [], set()
        for n, p in cah[g].items():
            v = anciennes.get(n)
            if v is not None and len(v) > 1 and sans_emoji(v[1]) != sans_emoji(p["nom"]):
                lignes[n] = transposer(v, u"—")
                gardees.append((n, u"nom divergent", v[1], p["nom"]))
                continue
            # LES DEUX PREMIÈRES COLONNES SE PRENNENT AU RANG, et elles seules :
            # le numéro et le nom sont en tête de toute table de plan, quel que
            # soit l'en-tête écrit au-dessus — `charger()` en fait déjà
            # l'hypothèse. Ça sauve les cinq verrous d'un cahier dont la table
            # porte par erreur les en-têtes des clefs : sans ça, l'index recevait
            # cinq lignes sans nom, ce qui est pire qu'une ligne absente.
            # LES SYNONYMES SE PRENNENT DANS LA TABLE, JAMAIS PAR INCLUSION. Un
            # cahier peut porter l'ancien en-tête du registre — `📝 Ce qu'on
            # fait, et où` pour `📝 Ce qu'on fait`. On accepte donc la cible et
            # tout en-tête que la table d'alias fait pointer sur elle, et rien
            # d'autre : pas de préfixe, pas d'inclusion, pas d'alias daté. « Ce
            # qui est vrai au matin du 30e » ne descendra pas, et c'est voulu —
            # il deviendrait « du 31e », et le repli qui l'attraperait est celui
            # qui a fait atterrir l'avancement à la place du numéro.
            cible = _sq(SENS[g])
            sens = None
            for k in [cible, ALIAS.get(cible)] + [a for a, v in ALIAS.items() if v == cible]:
                if k and k in p["cellules"]:
                    sens = p["cellules"][k]
                    break
            if sens is None:
                # UNE COLONNE SANS LOGIS EST DITE, jamais perdue en silence — avec
                # le cahier qui la lui refuse, pour qu'on sache où aligner
                # l'en-tête. La cellule reste vide dans l'INDEX ; le cahier, lui,
                # garde tout. Un index n'a pas à tout porter.
                sans_logis.add(p["affaire"][:34])
                sens = u""
            lignes[n] = {"cellules": [p["brut"], p["nom"], sens, p["affaire"]]}
        for n, c in anciennes.items():
            if n not in lignes:
                # TROIS MOTIFS, PAS UN. « Aucun cahier ne connaît ce numéro » et
                # « un cahier le connaît, mais d'un autre rang » ne se soignent
                # pas de la même main : le second est une collision de numéro
                # (44001, action ici et verrou au cahier de la présence), et
                # c'est un homme qui tranche laquelle des deux garde l'adresse.
                autre = sorted(tous.get(n, set()) - {g})
                motif = (u"genre " + u"/".join(autre)) if autre else u"sans cahier"
                lignes[n] = transposer(c, u"—")
                gardees.append((n, motif, c[1] if len(c) > 1 else u"", u""))
        # L'ORDRE EST LE NUMÉRO, toujours. Un index dont l'ordre dépend de celui
        # de lecture des livres produit un diff a chaque passage, et le bruit est
        # exactement ce sous quoi la prochaine divergence se cacherait.
        neuves = [lignes[n] for n in sorted(lignes, key=lambda x: (len(x), x))]
        titre = nu(b.get("titre"))
        if not titre.endswith(CALCULE):
            titre += CALCULE
        sorties[bid] = {"lignes": neuves, "titre": titre, "colonnes": neuves_cols,
                        "gardees": sorted(gardees), "sans_logis": sorted(sans_logis),
                        "avant": len(anciennes)}
    return sorties


def ecart_registres(livres=None):
    """Ce qui a été écrit à la main dans un registre dérivé. Pour tick.py.

    Sans cette garde, quelqu'un y posera une ligne de bonne foi dans six
    semaines, et l'on refera à l'identique la nuit qu'on vient de passer.

    LE TROU QU'ELLE A FAILLI AVOIR, et c'est la comparaison seule qui l'a
    trouvé : une main qui retouche un NOM dans le registre y crée une
    divergence — et la règle de conservation, qui refuse d'écraser un nom
    divergent, reproduit alors fidèlement la retouche. L'écart se referme sur
    lui-même et la garde ne voit rien. Or le nom est la colonne qui compte : la
    faute qu'on a payée le 30e était un nom.

    D'où deux sorties, et non une. La structure (lignes, colonnes, titre) se
    compare ; les noms divergents SE COMPTENT ET SE NOMMENT à chaque passage.
    Dix aujourd'hui : le jour où la liste en portera onze, quelqu'un aura
    écrit dans l'index. On ne peut pas distinguer une retouche d'une divergence
    ancienne par le calcul — on peut rendre la liste visible, et c'est assez."""
    if livres is None:
        livres = bibliotheque.charger(os.path.join(RACINE, "etat"))
    ecarts, divergences = [], []
    sorties = deriver(livres)
    for b in livres:
        bid = str(b.get("id") or u"")
        if bid not in sorties:
            continue
        s = sorties[bid]
        divergences += [(bid, n) for n, motif, a, c in s["gardees"]
                        if motif == u"nom divergent"]
        # LES COLONNES COMPTENT AUTANT QUE LES LIGNES, depuis que le générateur
        # les possède : un registre dont on aurait rajouté une colonne à la main
        # produit exactement le même compte de lignes, et la garde qui ne
        # regarderait que ce compte passerait à côté. C'est la faute que ce
        # fichier entier existe pour empêcher.
        a = json.dumps([b.get("colonnes") or [], b.get("lignes") or []],
                       ensure_ascii=False, sort_keys=True)
        n = json.dumps([s["colonnes"], s["lignes"]], ensure_ascii=False, sort_keys=True)
        if a != n:
            ecarts.append((bid, len(b.get("lignes") or []), len(s["lignes"])))
        elif not nu(b.get("titre")).endswith(CALCULE):
            ecarts.append((bid, -1, -1))
    return ecarts, sorted(divergences)
