# -*- coding: utf-8 -*-
"""RETOUR — ce qu'on fait du rapport quand l'homme rentre : le versement
sur-le-champ (pensees, travaux), et la proposition de tete.
"""
import io
import json
import os
import re

from etat.expose import tables

from agents.depeche.brief import (RACINE, ETAT, DEPOT_RAPPORTS, lire,
                                  _liste_etat, feuille_de_route,
                                  date_du_monde)

# ─────────────────────────────────────────────────────────────────────────────
# VERSER SUR LE CHAMP — il n'y a plus de guichet.
#
# Un homme rentrait, son rapport tombait dans `etat/rapports/`, et il y
# restait jusqu'a ce que quelqu'un lance `verser_travaux.py`. Trois fois dans la
# meme journee ses pensees sont restees a la porte : le depot ne portait pas
# l'identifiant de l'affaire, `verser` ne trouvait rien a rapprocher, et le
# travail d'une session entiere dormait dans un dossier que personne ne relit.
#
# Le rapport reste ecrit dans `etat/rapports/` — c'est la trace de sa journee et
# elle ne se jette pas — mais l'etat, lui, bouge tout de suite. Quand l'homme
# rentre d'une affaire qui n'existait pas encore, ON L'OUVRE avec le titre qu'il
# lui donne lui-meme : ce qu'il a travaille aujourd'hui est ce qu'il dit avoir
# travaille, et pas ce que le MJ avait prevu de lui faire travailler.
def verser_sur_le_champ(rapport, qui, date):
    """Ses pensees entrent dans `pensees.json`, a plat, datees et sourcees.

    Plus d'affaire a retrouver ni d'id a raccrocher : c'etait tout le travail
    de l'ancien guichet, et c'est ce qui le faisait rater. Une pensee porte son
    auteur, son jour, sa source et la salle ou il se tenait — et c'est assez
    pour que `dossier.py` la retrouve.

    PAS DE SOURCE, PAS DE PENSEE : une pensee sans source est REFUSEE ici, pas
    signalee plus tard. C'est la seule regle de l'ancien systeme qui meritait
    de survivre, et elle ne vaut que si elle mord a l'entree.
    """
    T = tables.lire("pensees", {"pensees": []})
    liste = T.setdefault("pensees", []) if isinstance(T, dict) else T
    quand = {"annee": date[0], "lune": date[1], "jour": date[2]}
    l = feuille_de_route().get(qui) or {}
    creux = l.get("questions_posees") or l.get("creux") or []
    salle_defaut = creux[0]["salle"] if creux else None

    vus = {((p.get("texte") or "")[:60], p.get("qui")) for p in liste
           if isinstance(p, dict)}
    pose, sans_source = 0, 0
    for bloc in rapport.get("travaux") or []:
        for x in bloc.get("pensees") or []:
            texte = (x.get("texte") or "").strip()
            if not texte:
                continue
            if not (x.get("source") or "").strip():
                sans_source += 1
                continue
            if (texte[:60], qui) in vus:
                continue
            liste.append({"qui": qui, "date": x.get("date") or dict(quand),
                          "source": x.get("source"), "texte": texte,
                          "salle": x.get("salle") or salle_defaut,
                          "affaire": bloc.get("affaire")})
            vus.add((texte[:60], qui))
            pose += 1
    if pose:
        tables.ecrire("pensees", T, indent=1)

    # Une conclusion ne se calcule pas : elle est ecrite ou elle ne l'est pas.
    if rapport.get("conclusion"):
        C = tables.lire("conclusions", {"conclusions": []})
        C.setdefault("conclusions", []).append({
            "qui": qui, "date": dict(quand),
            "affaire": (rapport.get("travaux") or [{}])[0].get("affaire"),
            "livre": rapport.get("livre"),
            "texte": rapport["conclusion"]})
        tables.ecrire("conclusions", C, indent=1)

    if sans_source:
        print(u"  (%d pensee(s) refusee(s) : pas de source, pas de pensee)"
              % sans_source)
    return pose


def proposer_la_tete(rapport, qui, date, sid):
    """Au retour d'une depeche, la tenue de la tete cesse d'etre un geste
    qu'on oublie : une proposition tombe en staging, comme apres un tick.

    Treize tetes en retard au 30 aout — dont Hask, gele huit jours de jeu
    pendant que ses cahiers vivaient — et une seule cause : rien dans la
    boucle ne reecrivait `intentions.json`, la tenue etait un geste manuel.

    CE QUE LE SCRIPT PROPOSE : l'arithmetique seule — `date_maj` au jour de
    la depeche. Il n'invente ni etape franchie ni croyance : un rapport ne
    declare pas structurellement « etape X faite », le deduire du texte
    serait une decision, et la machine donne la matiere, jamais la decision.
    Le MJ ajoute ses mutations (etapes, croyances) dans la MEME proposition
    avant `appliquer.py <fichier> --vraiment` — la `matiere` ci-dessous est
    la pour ca.

    Un fichier par homme et par jour de jeu (deterministe, re-ecrase par une
    depeche ulterieure du meme jour) ; rien si l'homme n'a pas de tete (PJ,
    dormant) ou si sa tete est deja au jour.
    """
    tetes = _liste_etat("intentions.json", "intentions")
    tete = next((t for t in tetes if t.get("personnage_id") == qui), None)
    if not tete:
        return None
    quand = {"annee": date[0], "lune": date[1], "jour": date[2]}
    if tete.get("date_maj") == quand:
        return None

    with io.open(os.path.join(ETAT, "intentions.json"), "rb") as f:
        sceau = __import__("hashlib").sha1(f.read()).hexdigest()
    matiere = {
        "journal": ["%s → %s" % (j.get("quoi", ""), j.get("resultat", "—"))
                    for j in (rapport.get("journal") or [])
                    if isinstance(j, dict)],
        "conclusion": bool(rapport.get("conclusion")) or any(
            t.get("conclusion") for t in rapport.get("travaux") or []
            if isinstance(t, dict)),
        "rapport": "etat/rapports/%s.json" % qui,
    }
    cible = os.path.join(ETAT, "staging",
                         "tete-%s-%d-%d-%d.json" % (qui, *date))
    tables.ecrire(cible, {
        "_pourquoi": ("Tete de %s apres sa depeche du %d.%d.%d (session %s). "
                      "Le script ne propose que date_maj ; ajoute ici tes "
                      "mutations d'etapes et de croyances d'apres la matiere, "
                      "puis applique le tout." % ((qui,) + date + (sid,))),
        "matiere": matiere,
        "empreintes": {"intentions": sceau},
        "mutations_proposees": [{
            "table": "intentions", "cible": qui, "operation": "tete",
            "champs": {"date_maj": quand},
        }],
    }, indent=1)
    print(u"  %-18s tete a tenir → %s" % (qui, os.path.relpath(cible, RACINE)))
    return cible


def _poser(chemin, contenu):
    d = os.path.dirname(chemin)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)

