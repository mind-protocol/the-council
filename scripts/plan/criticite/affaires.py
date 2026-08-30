# -*- coding: utf-8 -*-
"""AFFAIRES — le total d'une affaire, et sa veille (l'histoire datee).
"""
import io
import json
import os
import re
import sys
import time

from plan.expose import nu, sans_emoji
from plan.criticite.page import faite
from plan.criticite.graphe import POIDS

# Trois etages de plus qu'a la racine : scripts/plan/criticite/.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
#
# LA SEULE CHOSE QUE CE DISPOSITIF AIT LE DROIT D'ECRIRE. Tout le reste se
# recalcule : c'est meme sa regle, et c'est pour ca qu'aucun score ne vit dans
# `books.json`. Le PASSE, lui, ne se recalcule pas. Le plan d'hier n'existe plus
# nulle part une fois `books.json` reecrit, et sans trace on ne peut jamais
# repondre a la seule question qui vaille au conseil du matin : est-ce que ca
# monte ou est-ce que ca descend ?
#
# UNE LIGNE PAR CHANGEMENT, ET NON UNE PAR JOUR. La page demande `/criticite` a
# chaque ouverture de volume ; un instantane par appel remplirait le fichier de
# milliers de lignes IDENTIQUES. C'est ce risque-la, et lui seul, qui avait fait
# poser un garde-fou de vingt heures — un garde-fou de TEMPS contre un mal de
# CONTENU. Il coutait ce qu'il protegeait : un plan remanie trois fois dans la
# journee ne laissait qu'une trace, et l'on ne pouvait plus dire laquelle des
# trois ecritures avait fait bouger le score. On garde donc la ligne quand les
# scores different de la derniere posee, et jamais autrement — un fichier ou
# chaque ligne dit un changement reel n'a pas besoin d'etre rationne.
#
# CE QUE CA NE COUTE PAS. Le calcul, lui, ne tourne pas plus souvent : le
# serveur le cache sur la taille et la date de `books.json` et de
# `poids-etats.json`, donc il retombe deja exactement une fois par ecriture. Et
# une ligne pese deux kilo-octets : cent remaniements dans une journee font deux
# cents kilo-octets, ce qui n'est pas un sujet.
#
# L'ECART NE SE PREND PAS CONTRE LA LIGNE PRECEDENTE, et c'est ce qui rend la
# densite inoffensive : il se prend contre la plus recente ligne d'au moins
# vingt heures — « depuis hier », et non « depuis la derniere fois que quelqu'un
# a touche au plan ». Des lignes plus serrees rendent cette base plus juste, pas
# plus bruyante.
#
# APPEND-ONLY, UNE LIGNE PAR JOUR, JAMAIS DE RELECTURE COMPLETE. C'est un
# `.jsonl` comme le flux : on ajoute a la fin, et l'on ne lit que la queue.
HISTOIRE = os.path.join(RACINE, "etat", "criticite-histoire.jsonl")
HEURES = 20 * 3600


def totaux_par_affaire(lignes, attendu, pieces, affaires):
    """{affaire: {score, pas, goulots, restant, tenu_par}}."""
    tenu = {nu(b.get("titre")): (b.get("tenu_par") or u"") for b in affaires}
    out = {}
    for c, pt, n, p in lignes:
        a = p["affaire"] or u"— sans affaire —"
        o = out.setdefault(a, {"score": 0.0, "pas": 0, "goulots": 0, "restant": 0,
                               "tenu_par": tenu.get(a, u"")})
        o["score"] += c + attendu.get(n, 0)
        o["pas"] += 1
        if c > 0:
            o["goulots"] += 1
        if not faite(p):
            o["restant"] += 1
    for o in out.values():
        o["score"] = round(o["score"], 1)
    return out


def _quand():
    """L'horodatage reel, et pas la date du monde : on compare des MESURES,
    et deux mesures d'un meme jour de jeu peuvent etre separees d'une semaine
    de travail. La date du monde est notee a cote, pour la lecture."""
    import time
    return time.time()


def _regime():
    """L'empreinte du bareme en vigueur : les notes, et rien d'autre. Deux
    mesures prises sous deux baremes ne se soustraient pas — c'est la meme
    raison qui interdit de comparer un compte en muids a un compte en tonneaux."""
    try:
        d = json.load(io.open(POIDS, encoding="utf-8"))
        notes = d.get("notes") if isinstance(d.get("notes"), dict) else d
        cle = json.dumps(notes, sort_keys=True, ensure_ascii=False)
    except Exception:
        cle = u"tout-a-un"
    import hashlib
    return hashlib.sha1(cle.encode("utf-8")).hexdigest()[:8]


def veille(totaux, date_monde):
    """Ajoute `avant` et `ecart` a chaque affaire, et pose l'instantane du jour.

    Ne leve JAMAIS : une trace indisponible ne doit pas empecher un calcul. Le
    tableau sort alors sans ecart, ce qui se voit."""
    maintenant = _quand()
    lu = []
    try:
        if os.path.exists(HISTOIRE):
            with io.open(HISTOIRE, encoding="utf-8") as f:
                for l in f:
                    l = l.strip()
                    if l:
                        try:
                            lu.append(json.loads(l))
                        except ValueError:
                            pass
    except Exception:
        lu = []
    # ON NE COMPARE PAS DEUX MESURES PRISES A DES ECHELLES DIFFERENTES, et c'est
    # la faute que cette trace a failli commettre le premier jour. Ce matin le
    # plan pesait 4417 tous etats a 1 ; ce soir 2008 avec les notes posees sur
    # les objectifs finaux. L'ecart de 2409 n'est PAS du travail : c'est un
    # changement de regle. Affiche en « −2409 depuis hier », il aurait fait
    # croire a un effondrement le jour meme ou l'on venait de recoller le plan.
    #
    # Chaque instantane porte donc l'empreinte de son bareme. Un ecart ne se
    # calcule qu'entre deux lignes de meme empreinte ; sinon on ne dit rien —
    # « pas d'ecart » est une reponse honnete, « −2409 » ne l'est pas.
    reg = _regime()
    passees = [x for x in lu
               if maintenant - (x.get("quand") or 0) >= HEURES
               and x.get("regime", reg) == reg]
    avant = passees[-1] if passees else None
    for a, o in totaux.items():
        v = ((avant or {}).get("affaires") or {}).get(a)
        o["avant"] = v
        o["ecart"] = None if v is None else round(o["score"] - v, 1)
    # On pose la ligne quand les scores ont BOUGE, pas quand l'horloge a tourne.
    # Une affaire qui apparait ou disparait compte comme un changement : c'est
    # une comparaison de dictionnaires entiers, pas de valeurs une a une.
    scores = {a: o["score"] for a, o in totaux.items()}
    if not lu or (lu[-1].get("affaires") or {}) != scores:
        try:
            with io.open(HISTOIRE, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({
                    "quand": maintenant, "date": date_monde,
                    "regime": _regime(), "affaires": scores,
                }, ensure_ascii=False) + u"\n")
        except Exception as e:
            sys.stderr.write(u"  (trace non posee : %s)\n" % e)
    return totaux

