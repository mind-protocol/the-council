# -*- coding: utf-8 -*-
# PURGE — ce qui a ete ecrit dans une fenetre de temps — et, sur ordre, ce qu'on en retire.
#
# Usage :
#     python scripts/purger.py --du 25:886 --au 25:1100
#     python scripts/purger.py --du 25:886 --au 25:1100 --qui aurore-inchauspe
#     python scripts/purger.py --du 25:886 --au 25:1100 --vraiment
#
# POURQUOI. Effacer des items du flux ne defait pas l'etat. Le 25e, quatre-vingt-
# seize items ont ete coupes ; deux paroles ont ete retirees a la main, et une
# troisieme est restee — parce qu'on l'avait cherchee par MOTS-CLES et qu'elle
# n'en contenait aucun. Elle a continue a piloter des decisions royales qui
# n'avaient plus eu lieu.
#
# Une fenetre de temps ne ment pas, un vocabulaire si. Ce script cherche donc par
# DATE, et seulement par date — puis affiche tout, et ne supprime que si on le
# lui ordonne. Il ne touche jamais au flux : le flux se coupe a la main, et c'est
# tres bien ainsi.
import json, os, re, sys, unicodedata


from etat.expose import tables  # LA PORTE de etat/ : une lecture, une ecriture, une semantique d'erreur
import racines  # ou vit l'etat, et de quel monde il est
racine = racines.racine()  # le MONDE, pas le depot
etat = racines.etat()

# Fichier -> clef portant la liste (None = le fichier EST la liste).
# pensees.json y est entre le 31.8 : le monde etait revenu au 129.4.3 et la
# fenetre du 4e ne montrait rien, alors que TRENTE-QUATRE pensees du 4e y
# dormaient. Une table absente de cette liste est un angle mort parfait — la
# purge affirme le vide et se trompe. Toute table du JOUE doit y figurer.
TABLES = [
    ("actes.json", None), ("paroles.json", None), ("info.json", None),
    ("annales.json", None), ("evenements.json", None), ("jetons.json", None),
    ("plis.json", None), ("pensees.json", None),
]
PAR_JOUEUR = ["objectifs.json", "vues.json", "jetons.json"]


def sans_accents(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def borne(txt):
    """« 25:886 » ou « 25 » -> (jour, minute)."""
    if ":" in txt:
        j, m = txt.split(":", 1)
        return int(j), int(m)
    return int(txt), None


def dans(x, d0, d1, lune=None, clef="date"):
    """La piece tombe-t-elle dans la fenetre ?

    `clef` vaut « date » — CE QUI A EU LIEU — et c'est le seul champ que la
    purge supprime. « date_prevue » est L'AVENIR PROGRAMME du monde : la mort
    de Lucerys au 9e, les trente evenements « prog- » des jours suivants. Les
    confondre, c'est effacer le futur en croyant nettoyer le passe ; le 31.8
    une fenetre du 4e au 12e visait cinquante-quatre pieces dont TRENTE-QUATRE
    n'etaient que des rendez-vous a venir.
    """
    d = x.get(clef) or {}
    if not isinstance(d, dict) or d.get("jour") is None:
        return False
    if lune is not None and d.get("lune") not in (None, lune):
        return False
    j, m = d.get("jour"), d.get("minute")
    j0, m0 = d0
    j1, m1 = d1
    if j < j0 or j > j1:
        return False
    if j == j0 and m0 is not None and (m is None or m < m0):
        return False
    if j == j1 and m1 is not None and (m is None or m > m1):
        return False
    return True


def charge(p):
    d = tables.lire(p, None)
    if d is None:
        return None, None
    if isinstance(d, list):
        return d, None
    for k, v in d.items():
        if isinstance(v, list):
            return v, (d, k)
    return None, None


def ecrire(p, liste, enveloppe):
    if enveloppe:
        d, k = enveloppe
        d[k] = liste
        contenu = d
    else:
        contenu = liste
    tables.ecrire(p, contenu, indent=1)


def resume(x):
    for cle in ("quoi", "texte", "description", "titre"):
        if x.get(cle):
            t = re.sub(r"\s+", " ", str(x[cle])).strip()
            return t[:200] + (" […]" if len(t) > 200 else "")
    return re.sub(r"\s+", " ", json.dumps(x, ensure_ascii=False))[:160]


def main(argv):
    d0 = d1 = None
    qui, lune, vraiment = None, None, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--du" and i + 1 < len(argv):
            d0 = borne(argv[i + 1]); i += 2
        elif a == "--au" and i + 1 < len(argv):
            d1 = borne(argv[i + 1]); i += 2
        elif a == "--qui" and i + 1 < len(argv):
            qui = sans_accents(argv[i + 1]); i += 2
        elif a == "--lune" and i + 1 < len(argv):
            lune = int(argv[i + 1]); i += 2
        elif a == "--vraiment":
            vraiment = True; i += 1
        else:
            i += 1
    if d0 is None or d1 is None:
        raise SystemExit(
            "usage : purger.py --du <jour[:minute]> --au <jour[:minute]> "
            "[--qui <id>] [--lune <n>] [--vraiment]\n"
            "  Sans --vraiment, il ne fait que MONTRER. C'est le mode a employer d'abord.")

    fichiers = [(os.path.join(etat, n), n, k) for n, k in TABLES]
    jdir = os.path.join(etat, "joueurs")
    if os.path.isdir(jdir):
        for j in sorted(os.listdir(jdir)):
            for n in PAR_JOUEUR:
                p = os.path.join(jdir, j, n)
                if os.path.exists(p):
                    fichiers.append((p, "joueurs/%s/%s" % (j, n), None))

    print("FENETRE : du %s au %s%s%s" % (
        "%de %s" % (d0[0], "" if d0[1] is None else "%02dh%02d" % (d0[1] // 60, d0[1] % 60)),
        "%de %s" % (d1[0], "" if d1[1] is None else "%02dh%02d" % (d1[1] // 60, d1[1] % 60)),
        ("  filtre : %s" % qui) if qui else "",
        "   (MODE MONTRER)" if not vraiment else "   (SUPPRESSION REELLE)"))

    total = 0
    for p, nom, _ in fichiers:
        liste, env = charge(p)
        if liste is None:
            continue
        vises, prevus = [], []
        for x in liste:
            if not isinstance(x, dict):
                continue
            if qui and qui not in sans_accents(json.dumps(x, ensure_ascii=False)):
                continue
            if dans(x, d0, d1, lune, "date"):
                vises.append(x)
            elif dans(x, d0, d1, lune, "date_prevue"):
                prevus.append(x)
        if prevus:
            print("\n== %s : %d rendez-vous A VENIR dans la fenetre — NON touches" % (nom, len(prevus)))
            for x in prevus[:8]:
                print("     . %s" % (x.get("id") or x.get("titre") or "?"))
            if len(prevus) > 8:
                print("     . … et %d autres" % (len(prevus) - 8))
        if not vises:
            continue
        total += len(vises)
        print("\n== %s  (%d)" % (nom, len(vises)))
        for x in vises:
            print("  - %s" % (x.get("id") or x.get("titre") or "?"))
            print("      " + resume(x))
        if vraiment:
            restants = [x for x in liste if x not in vises]
            ecrire(p, restants, env)

    print("\n%d enregistrement(s) %s." % (total, "SUPPRIME(S)" if vraiment else "trouve(s)"))
    if total and not vraiment:
        print("Relisez la liste. Si elle est juste, relancez la meme commande avec --vraiment.")
    if not total:
        print("Rien dans cette fenetre. Verifiez le jour et la lune avant de conclure au vide.")
    if vraiment:
        print("RAPPEL : le flux ne bouge pas tout seul. Coupez-le a la main si ce n'est pas fait,")
        print("et remettez monde.date et horloges.json a l'instant ou l'on reprend.")


