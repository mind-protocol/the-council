# -*- coding: utf-8 -*-
"""CONTROLE — verifier() (appele par tick --verifier via la garde des
sieges) et reancrer() : signaler les cibles disparues, reancrer au meme
metier dans le rayon mesure.
"""
import math

from agents.affectation.lecture import _bati
from agents.affectation.lecture import (RAYON_REANCRAGE, OCCUPANTS, GENRES,
                                        DEFAUT_MONDE, charger_bati,
                                        charger_pieces, fiche_piece,
                                        monde_de, charger_liens, ecrire,
                                        fiche_bati, position, adresse,
                                        corps_par_id, identifiants, sortir,
                                        LIENS)

def verifier(L, bati=None, C=None):
    """Ce qui ne tient plus. Appelé aussi par `tick.py --verifier`.

    Le bâti n'est plus passé en argument : chaque affectation dit SON monde, et
    l'on va chercher le bon. (Les deux paramètres restent acceptés pour les
    appelants d'avant, et sont ignorés.)
    """
    maux = []
    for clef, a in sorted(L["affectations"].items()):
        genre, _, ident = clef.partition(":")
        if genre not in GENRES:
            maux.append("[%s] genre inconnu — attendus : %s"
                        % (clef, ", ".join(GENRES)))
            continue
        m = monde_de(a)
        if m not in _bati.mondes():
            maux.append("[%s] monde inconnu : %s — engendré nulle part "
                        "(mondes présents : %s)"
                        % (clef, m, ", ".join(_bati.mondes()) or "aucun"))
            continue
        connus = identifiants(genre)
        if a.get("piece"):
            if not fiche_piece(m, a["piece"]):
                maux.append("[%s] pièce « %s » absente des intérieurs de « %s » "
                            "— le monde ne l'a pas creusée"
                            % (clef, a["piece"], m))
            if connus is not None and ident not in connus:
                maux.append("[%s] plus aucun %s de cet id" % (clef, genre))
            continue
        try:
            bati, C = _bati.charger(m)
        except _bati.MondeInconnu as e:
            maux.append("[%s] %s" % (clef, e))
            continue
        i = a.get("bat")
        # Le serveur écrit la position d'un marcheur en `personnage:<id>`, sans
        # `bat` : ce n'est pas une affectation qui aurait perdu sa cible, c'est
        # un homme entre deux portes. Le signaler à chaque pas ferait crier le
        # vérificateur pour tout le monde qui bouge.
        if genre == "personnage" and i is None:
            continue
        if not isinstance(i, int) or i < 0 or i >= len(bati):
            maux.append("[%s] bâtiment %r hors du monde engendré « %s » — il a "
                        "ete regenere, ou l'index est faux" % (clef, i, m))
            continue
        connus = identifiants(genre)
        if connus is not None and ident not in connus:
            maux.append("[%s] plus aucun %s de cet id : l'affectation pointe "
                        "vers un bâtiment bien réel, pour une chose disparue"
                        % (clef, genre))
        attendu = a.get("usage")
        if attendu and bati[i][C["usage"]] != attendu:
            maux.append("[%s] le bâtiment %d est devenu un %s, il était un %s"
                        % (clef, i, bati[i][C["usage"]], attendu))
        # LES MÈTRES ÉCRITS SONT L'INTENTION, LE RANG N'EST QU'UN CACHE — et
        # c'est ce qui décide de ce qu'on a le droit de reprocher ici.
        #
        # Ce contrôle comparait `xyz` à la position du bâtiment avec un seuil de
        # deux mètres. Or `reancrer` ne réécrit JAMAIS `xyz` — délibérément :
        # sans quoi chaque régénération re-ancrerait sur le voisin d'à côté,
        # puis sur le voisin du voisin, et l'adresse dériverait au hasard de
        # cent cinquante mètres par passage sans que personne le voie. Le prix
        # de ce choix est qu'une affectation replacée garde un écart résiduel —
        # et le contrôle le dénonçait comme une panne. Quatorze alertes qui ne
        # s'éteignaient plus, dans un relevé que `tick.py --verifier` lit à
        # chaque début de session : la seule chose qu'un tel avertissement
        # enseigne est de ne plus lire les avertissements.
        #
        # On ne se plaint donc que lorsque la résolution est MAUVAISE : plus
        # rien du bon métier à portée. Le résidu d'un réancrage réussi se lit
        # où il doit se lire — dans `--reancrer`, qui l'imprime en clair.
        xyz = a.get("xyz")
        if xyz:
            d = math.hypot(bati[i][C["x"]] - xyz[0], bati[i][C["y"]] - xyz[1])
            if d > RAYON_REANCRAGE:
                maux.append("[%s] le bâtiment %d est à %.0f m des mètres "
                            "écrits, et plus rien du bon métier n'est à portée "
                            "— l'adresse est perdue, il faut la reposer à la "
                            "main" % (clef, i, d))
    return maux


def reancrer(L, monde, vraiment):
    """Remettre chaque affectation sur le bâtiment qui est À SA POSITION.

    LE RANG N'EST PAS UNE ADRESSE DURABLE, et c'est écrit depuis toujours :
    « le rang n'est stable que tant que bati.json n'est pas réengendré ». Le
    28e, le monde a été refait — quarante-huit mille bâtiments devenus
    quarante-cinq mille — et les quatorze affectations ont glissé avec. La
    porte de Fer désignait une échoppe à trois kilomètres.

    LES MÈTRES, EUX, TIENNENT. `--affecter` écrit `xyz` en même temps que le
    rang, précisément pour ce jour-là : la position est la vraie adresse, le
    rang n'en est qu'un raccourci. On relit donc la position et l'on redonne
    le rang.

    ET L'ON NE RÉÉCRIT PAS `xyz`. C'est le point qui a manqué de se perdre : il
    serait tentant de recaler les mètres sur le bâtiment qu'on vient de choisir,
    ce qui ferait taire `--verifier` d'un coup. Ce serait échanger un faux
    avertissement contre une dérive muette — chaque régénération ancrerait sur
    le voisin, puis sur le voisin du voisin, et au bout de quatre passages la
    Gaffe serait à trois rues de la porte sans qu'une seule ligne l'ait dit.
    L'intention ne bouge pas ; c'est le contrôle qui a appris à ne se plaindre
    que du vrai (voir `verifier`).

    ON CHERCHE D'ABORD LE BON MÉTIER. Une affectation dit ce qu'elle attend
    (`usage`) : le corps de garde de la porte de Fer est un corps de garde.
    Prendre le plus proche TOUT COURT, c'est risquer de nommer « porte de
    Fer » la maison d'à côté parce qu'elle est à deux mètres de moins. On
    prend donc le plus proche DU MÉTIER ATTENDU dans un rayon raisonnable, et
    l'on ne retombe sur le plus proche tout court qu'à défaut — en le disant.
    """
    bati, C = charger_bati(monde)
    ix, iy, iu = C["x"], C["y"], C["usage"]
    # Un lieu nommé « Le change » que le jeu rapporterait comme une échoppe
    # serait faux DANS LA FICTION, là où cent trente-six mètres ne sont qu'un
    # semis qui a glissé. Mieux vaut le bon métier un peu déplacé que le mauvais
    # métier pile sur le point. (Le chiffre est en tête de fichier : `verifier`
    # s'en sert aussi, et il faut qu'ils disent la même chose.)
    RAYON = RAYON_REANCRAGE
    A = L["affectations"]
    lignes, change = [], 0
    for clef in sorted(A):
        v = A[clef]
        if not isinstance(v, dict) or v.get("bat") is None:
            continue
        if monde_de(v) != monde:
            continue
        xyz = v.get("xyz")
        if not xyz:
            lignes.append(("  %-34s pas de mètres écrits : on ne peut pas la "
                           "replacer" % clef, None))
            continue
        attendu = v.get("usage")
        best_u = best_t = None
        for i, r in enumerate(bati):
            d = math.hypot(r[ix] - xyz[0], r[iy] - xyz[1])
            if best_t is None or d < best_t[0]:
                best_t = (d, i)
            if attendu and r[iu] == attendu and (best_u is None or d < best_u[0]):
                best_u = (d, i)
        choix, par = (best_u, "métier") if (best_u and best_u[0] <= RAYON) else (best_t, "position")
        if not choix:
            continue
        d, i = choix
        avant = v["bat"]
        note = ""
        if par == "position" and attendu:
            note = "  ** aucun %s à moins de %d m : pris au plus proche (%s) **" % (
                attendu, RAYON, bati[i][iu])
        if i == avant:
            lignes.append(("  %-34s bat %-6d inchangé (%.0f m)" % (clef, i, d), None))
            continue
        change += 1
        lignes.append(("  %-34s bat %-6d -> %-6d  %.0f m, par %s%s"
                       % (clef, avant, i, d, par, note), (clef, i)))
    for txt, _ in lignes:
        print(txt)
    print()
    if not change:
        print("  rien à replacer : tout est déjà en place.")
        return
    if not vraiment:
        print("  %d affectations à replacer. Rien n'est écrit." % change)
        print("  → python scripts/affecter.py --reancrer --vraiment")
        return
    for _, maj in lignes:
        if maj:
            A[maj[0]]["bat"] = maj[1]
    ecrire(LIENS, L)
    print("  %d affectations replacées dans %s." % (change, LIENS))

