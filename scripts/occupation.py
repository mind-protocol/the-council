# -*- coding: utf-8 -*-
"""Qui est ASSIS — mesure, et non declaration.

    python scripts/occupation.py               # la mesure, siege par siege
    python scripts/occupation.py --rafraichir --vraiment

POURQUOI CE FICHIER EXISTE. `etat/joueurs.json` portait un champ `occupe`
tenu a la main. Personne ne le rebasculait : les quatre sieges sont restes a
`true` pendant que deux d'entre eux n'etaient plus joues. Or `occupe` a un
effet dur — `boucle_activation.py` EXCLUT les sieges occupes de la file
d'activation. Deux sieges se sont donc retrouves ni joues par un humain, ni
actives par la machine : ils dormaient. Et rien ne pouvait le voir, parce que
le seul invariant tenu par `tick.py --verifier` etait « occupe -> pas de tete »
— un etat parfaitement coherent avec lui-meme, et faux.

LA DEFINITION, ARRETEE PAR LE PROPRIETAIRE : « occupe » veut dire ACTIF
RECEMMENT. Ce n'est pas une declaration, c'est une mesure.

    occupe  <=>  la veille de sa session date de moins de SEUIL
            OU   son inbox contient au moins un fichier

Rien d'autre. Le champ `occupe` de `etat/joueurs.json` reste ecrit, mais
seulement comme CACHE de ce calcul, pour que les lecteurs existants (le
serveur, `depecher.py`, `append_flux.py`, `parvenir.py`…) n'aient pas a
apprendre a mesurer. Il se recalcule au debut de la boucle d'activation et par
`sieges.py`.

QUELS FICHIERS DE VEILLE COMPTENT — la regle, et sa raison.

`etat/veille/` melange des noms de session de toutes provenances :
`aurore-inchauspe.json` (le siege), `mj-aurore.json` (sa regie),
`mj-nicolas.json`, `mj.json` (le MJ principal), plus des noms courts abandonnes
(`aurore.json`, `marlo.json`) et des bricoles (`fix-verif.json`,
`mj-monde.json`). Un nom de session est libre : `veille.py <ce-que-je-veux>`
cree le fichier.

REGLE : pour un siege, ne compte que la veille dont le nom est son
`personnage_id` — sauf si le siege declare lui-meme d'autres noms, dans un
champ `veille: ["...", "..."]` de son entree de `etat/joueurs.json`.

Pourquoi celle-la :

  * Le signal voulu est « la session de CE joueur respire ». `personnage_id`
    est le seul nom dont on sache avec certitude a quel siege il appartient.
  * `mj.json` est ambigu PAR CONSTRUCTION : le MJ principal tient le monde et
    plusieurs PNJ, il ne designe aucun siege. Le compter rendrait un siege
    occupe parce que quelqu'un d'autre travaille — exactement le mensonge
    qu'on repare.
  * `mj-<nom>` designe bien une regie de siege, mais par une convention que
    rien n'applique et que rien ne verifie. On ne devine pas : on laisse le
    siege le DECLARER. C'est une ligne dans son entree, et elle se relit.
  * Les noms courts (`aurore.json`, `marlo.json`) sont des veilles mortes.
    Les prendre au plus recent ne coute rien aujourd'hui ; le jour ou une
    session les reveille, ils ressusciteraient une mesure qui ne veut plus
    rien dire.

DEUX MARQUES DE MAIN, et pas plus. S'asseoir et se lever sont des gestes datés
qui doivent battre la mesure le temps qu'elle rattrape :

  * `assis_a`  — pose par `sieges.py --asseoir` : s'asseoir EST une presence,
    elle vaut comme un souffle jusqu'a ce que la session commence a respirer
    d'elle-meme.
  * `quitte_a` — pose par `sieges.py --quitter` : tout signal ANTERIEUR a ce
    moment ne compte plus. Sans quoi une veille fraiche de trois minutes
    rallumerait le siege qu'on vient de quitter.

CE QU'ON NE FAIT JAMAIS. Un rafraichissement ne rend PAS vacant un siege qui
n'a pas de tete dans `intentions.json` : ce serait le livrer a la file
d'activation sans savoir ce qu'il veut. Dans ce cas on garde le cache tel quel
et on CRIE. Un basculement silencieux vers un etat impossible est precisement
le defaut qu'on repare ; on ne le remplace pas par un autre.
"""
from __future__ import print_function

import argparse
import io
import json
import os
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")


# --------------------------------------------------------------------------
# LE SEUIL — un seul endroit, et il se change ici.
# --------------------------------------------------------------------------
# Deux heures de temps REEL. Ce n'est pas une constante physique : c'est la
# duree au-dela de laquelle une session qui n'a pas respire est presumee
# partie. Plus court, on rend vacant un joueur parti se faire un cafe ; plus
# long, on laisse dormir un siege une demi-journee. La variable d'environnement
# n'est la que pour les essais — la valeur de reference est celle-ci.
SEUIL_OCCUPATION_MINUTES = 120
try:
    SEUIL_OCCUPATION_MINUTES = int(
        os.environ.get("LE_CONSEIL_SEUIL_OCCUPATION_MINUTES")
        or SEUIL_OCCUPATION_MINUTES)
except (TypeError, ValueError):
    pass
SEUIL_OCCUPATION_SECONDES = SEUIL_OCCUPATION_MINUTES * 60


# --------------------------------------------------------------------------
# Lecture
# --------------------------------------------------------------------------

def _lire_json(chemin, defaut):
    if not os.path.exists(chemin):
        return defaut
    try:
        with io.open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError, IOError):
        return defaut


# --------------------------------------------------------------------------
# LES SIEGES QUI NE JOUENT PAS CE MONDE-CI — un seul predicat, partout.
# --------------------------------------------------------------------------
# `etat/joueurs.json` est le roster que le SERVEUR lit pour ouvrir une page :
# tout ce qui doit apparaitre au selecteur de siege y figure. Or deux choses
# peuvent y figurer sans appartenir au monde de la Danse :
#
#   * la REGIE (`regie: true`) — Corneille, qui n'incarne personne et regarde ;
#   * une AUTRE PARTIE (`partie: "<nom>"`) — les Sept Chandelles, une troupe de
#     theatre a Port-Real six lunes avant le present de la Danse
#     (docs/troupe.md). Ce sont de vrais personnages, avec un corps et une
#     bouche — mais pas dans CE monde-ci.
#
# La distinction compte, et c'est pourquoi on n'a pas reutilise `regie` pour
# eux : un siege de regie ne joue personne nulle part, un siege d'une autre
# partie joue quelqu'un ailleurs. Ce que les deux partagent est etroit et
# suffit ici : ils n'ont ni fiche dans `personnages.json`, ni tete dans
# `intentions.json`, ni horloge, ni presence, et les mesurer comme des sieges
# de la Danse ne produirait que des fautes a reparer qui n'en sont pas.
#
# Un siege SANS champ `partie` appartient a la partie courante : les cinq
# sieges de la Danse n'ont donc rien a declarer, et rien ne bouge pour eux.
PARTIE_COURANTE = "danse"


def hors_monde(siege):
    """Ce siege est-il hors des boucles de la partie courante ?

    Vrai pour la regie et pour tout siege declarant une `partie` autre que
    celle-ci. Faux pour tout le reste, y compris un siege sans `partie` — le
    defaut est d'etre du monde, sans quoi une entree mal ecrite disparaitrait
    en silence des verifications, ce qui est exactement le contraire du but.
    """
    if not isinstance(siege, dict):
        return False
    if siege.get("regie"):
        return True
    p = siege.get("partie")
    return bool(p) and str(p) != PARTIE_COURANTE


def roster():
    """Les sieges de etat/joueurs.json, tolerant sur l'enveloppe.

    UN SIEGE DE REGIE N'EST PAS UN SIEGE. Corneille (`regie: true`) n'incarne
    personne : pas de fiche dans personnages.json, pas de tete dans
    intentions.json, pas d'horloge. Mesurer son occupation n'aurait aucun sens
    — vacante et sans tete, elle serait signalee en faute par
    `tick.py --verifier` a chaque passage et journalisee `vacant_sans_tete` a
    chaque cycle d'activation, pour un siege qui n'a rien a jouer. On l'ecarte
    donc ici, en un seul endroit : tout ce qui MESURE passe par ce roster
    (tick, boucle d'activation, sieges.py), tandis que ce qui SERT le jeu — le
    serveur, ses jetons, sa bascule — lit joueurs.json directement et la voit.

    Meme sort, meme raison, pour les sieges d'une AUTRE PARTIE : voir
    `hors_monde()` juste au-dessus.
    """
    r = _lire_json(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(r, dict):
        r = r.get("joueurs") or r.get("sieges") or []
    return [s for s in r if isinstance(s, dict) and s.get("personnage_id")
            and not hors_monde(s)]


def tetes_ecrites():
    """Les personnage_id qui ont une entree dans intentions.json."""
    t = _lire_json(os.path.join(ETAT, "intentions.json"), [])
    if not isinstance(t, list):
        return set()
    return {x.get("personnage_id") for x in t
            if isinstance(x, dict) and x.get("personnage_id")}


def sessions_du_siege(siege):
    """Les noms de veille qui comptent pour ce siege. Voir l'entete."""
    declares = siege.get("veille")
    if isinstance(declares, str):
        declares = [declares]
    if isinstance(declares, (list, tuple)) and declares:
        return [str(x) for x in declares if x]
    return [siege["personnage_id"]]


def _mtime(chemin):
    try:
        return os.path.getmtime(chemin)
    except OSError:
        return None


def souffle_veille(siege):
    """(nom de session, mtime) le plus recent parmi ses veilles. Ou (None, None)."""
    meilleur, quand = None, None
    for session in sessions_du_siege(siege):
        m = _mtime(os.path.join(ETAT, "veille", session + ".json"))
        if m is not None and (quand is None or m > quand):
            meilleur, quand = session, m
    return meilleur, quand


def souffle_inbox(siege):
    """(nombre d'ACTIONS en attente, mtime de la plus recente) dans son inbox.

    Une action est un fichier ecrit par le serveur : `action-<horodatage>.json`
    (voir `serveur/serveur.js`, POST /action). Les fichiers caches n'en sont
    pas : `etat/inbox/marlo-vasse/.gardez` est un jalon qui tient le dossier
    dans git, il date du 7 aout et il aurait tenu ce siege occupe POUR
    TOUJOURS — le defaut qu'on repare, remis en place par la porte de service.
    """
    dossier = os.path.join(ETAT, "inbox", siege["personnage_id"])
    try:
        noms = [n for n in os.listdir(dossier)
                if not n.startswith(".") and n.endswith(".json")
                and os.path.isfile(os.path.join(dossier, n))]
    except OSError:
        return 0, None
    quand = None
    for n in noms:
        m = _mtime(os.path.join(dossier, n))
        if m is not None and (quand is None or m > quand):
            quand = m
    return len(noms), quand


def _horodatage(valeur):
    """Une marque `assis_a`/`quitte_a` : secondes epoch, ou None."""
    try:
        return float(valeur)
    except (TypeError, ValueError):
        return None


def mesurer(siege, maintenant=None, tetes=None):
    """LA MESURE d'un siege. Ne lit que le disque, n'ecrit rien.

    Rend un dictionnaire lisible tel quel : c'est ce que `sieges.py` imprime,
    et c'est ce que le verificateur compare au cache.
    """
    maintenant = time.time() if maintenant is None else maintenant
    pid = siege["personnage_id"]
    session, veille_a = souffle_veille(siege)
    inbox_n, inbox_a = souffle_inbox(siege)
    quitte_a = _horodatage(siege.get("quitte_a"))
    assis_a = _horodatage(siege.get("assis_a"))

    def apres_le_depart(quand):
        return quand is not None and (quitte_a is None or quand > quitte_a)

    veille_age = None if veille_a is None else max(0.0, maintenant - veille_a)
    inbox_age = None if inbox_a is None else max(0.0, maintenant - inbox_a)

    # L'ordre des raisons est celui de la definition : l'inbox d'abord (une
    # action non traitee veut dire que quelqu'un vient de cliquer), la veille
    # ensuite, la marque de main en dernier recours.
    occupe, raison = False, "aucun signal"
    if inbox_n > 0 and (inbox_a is None or apres_le_depart(inbox_a)):
        occupe, raison = True, "%d action(s) dans son inbox" % inbox_n
    elif (veille_age is not None and veille_age < SEUIL_OCCUPATION_SECONDES
            and apres_le_depart(veille_a)):
        occupe = True
        raison = "veille '%s' il y a %s" % (session, dire_age(veille_age))
    elif (assis_a is not None
            and maintenant - assis_a < SEUIL_OCCUPATION_SECONDES
            and apres_le_depart(assis_a)):
        occupe = True
        raison = "assis a la main il y a %s" % dire_age(maintenant - assis_a)
    elif veille_age is not None and not apres_le_depart(veille_a):
        raison = "aucun signal depuis qu'on a quitte le siege"
    elif veille_age is not None:
        raison = "veille '%s' perimee (%s)" % (session, dire_age(veille_age))

    tetes = tetes_ecrites() if tetes is None else tetes
    cache = bool(siege.get("occupe", True))
    return {
        "personnage_id": pid,
        "nom": siege.get("nom") or pid,
        "role": siege.get("role") or "second",
        "session_veille": session,
        "veille_age_s": veille_age,
        "inbox": inbox_n,
        "inbox_age_s": inbox_age,
        "quitte_a": quitte_a,
        "assis_a": assis_a,
        "occupe": occupe,
        "raison": raison,
        "cache": cache,
        "derive": cache != occupe,
        "a_tete": pid in tetes,
        # Un siege tenu occupe par un inbox qui ne bouge plus : le seul cas ou
        # la definition arretee peut mentir dans le sens « occupe pour
        # toujours ». On ne change pas la regle, on rend le cas visible.
        "inbox_dormant": bool(
            inbox_n > 0 and inbox_age is not None
            and inbox_age >= SEUIL_OCCUPATION_SECONDES
            and (veille_age is None
                 or veille_age >= SEUIL_OCCUPATION_SECONDES)),
    }


def mesures(maintenant=None):
    tetes = tetes_ecrites()
    return [mesurer(s, maintenant, tetes) for s in roster()]


def occupes(maintenant=None):
    """Les sieges MESURES occupes. Ne lit pas le cache."""
    return {m["personnage_id"] for m in mesures(maintenant) if m["occupe"]}


def vacants(maintenant=None):
    return {m["personnage_id"] for m in mesures(maintenant) if not m["occupe"]}


def dire_age(secondes):
    if secondes is None:
        return "jamais"
    secondes = int(secondes)
    if secondes < 90:
        return "%d s" % secondes
    if secondes < 5400:
        return "%d min" % (secondes // 60)
    if secondes < 172800:
        return "%d h %02d" % (secondes // 3600, (secondes % 3600) // 60)
    return "%d j" % (secondes // 86400)


# --------------------------------------------------------------------------
# Le rafraichissement du cache
# --------------------------------------------------------------------------

class SansTete(Exception):
    """Un siege mesure vacant qui n'a pas de tete. On ne bascule pas."""


def rafraichir(vraiment=False, maintenant=None, crier=True):
    """Recale le champ `occupe` de etat/joueurs.json sur la mesure.

    Ecriture optimiste, comme partout ici : on relit le fichier JUSTE avant
    d'ecrire, on ne touche QUE la clef `occupe` de chaque entree, et l'on pose
    par `os.replace` — une autre session qui edite `pnj` ou `note` au meme
    moment ne perd rien de plus qu'un champ.

    Rend (changements, refuses, mesures). `changements` = ce qui a bascule ;
    `refuses` = les sieges mesures vacants SANS tete, laisses tels quels.
    """
    releve = mesures(maintenant)
    changements = [m for m in releve if m["derive"]]
    refuses = [m for m in changements if not m["occupe"] and not m["a_tete"]]
    a_ecrire = {m["personnage_id"]: m["occupe"] for m in changements
                if not (not m["occupe"] and not m["a_tete"])}

    if refuses and crier:
        for m in refuses:
            sys.stderr.write(
                u"ERREUR occupation : le siege '%s' n'est plus actif "
                u"(%s) mais n'a AUCUNE tete dans intentions.json. On le "
                u"laisse marque occupe : le rendre vacant le livrerait a la "
                u"boucle d'activation sans savoir ce qu'il veut.\n"
                u"  Ecrivez-lui sa tete, puis : python scripts/sieges.py "
                u"--quitter %s --vraiment\n"
                % (m["personnage_id"], m["raison"], m["personnage_id"]))

    if not vraiment or not a_ecrire:
        return changements, refuses, releve

    chemin = os.path.join(ETAT, "joueurs.json")
    with io.open(chemin, encoding="utf-8") as f:
        frais = json.load(f)
    entrees = frais
    if isinstance(frais, dict):
        entrees = frais.get("joueurs") or frais.get("sieges") or []
    touche = False
    for entree in entrees:
        if not isinstance(entree, dict):
            continue
        pid = entree.get("personnage_id")
        if pid in a_ecrire and bool(entree.get("occupe", True)) != a_ecrire[pid]:
            entree["occupe"] = a_ecrire[pid]
            touche = True
    if not touche:
        return changements, refuses, releve
    temporaire = chemin + ".occupation.tmp"
    with io.open(temporaire, "w", encoding="utf-8") as f:
        json.dump(frais, f, ensure_ascii=False, indent=2)
        f.write(u"\n")
    os.replace(temporaire, chemin)
    return changements, refuses, releve


def marquer(pid, clef, maintenant=None):
    """Pose `assis_a` ou `quitte_a` sur un siege. Meme prudence d'ecriture."""
    if clef not in ("assis_a", "quitte_a"):
        raise ValueError(clef)
    maintenant = time.time() if maintenant is None else maintenant
    chemin = os.path.join(ETAT, "joueurs.json")
    with io.open(chemin, encoding="utf-8") as f:
        frais = json.load(f)
    entrees = frais
    if isinstance(frais, dict):
        entrees = frais.get("joueurs") or frais.get("sieges") or []
    touche = False
    for entree in entrees:
        if isinstance(entree, dict) and entree.get("personnage_id") == pid:
            entree[clef] = round(float(maintenant), 3)
            entree.pop("quitte_a" if clef == "assis_a" else "assis_a", None)
            touche = True
    if not touche:
        return False
    temporaire = chemin + ".occupation.tmp"
    with io.open(temporaire, "w", encoding="utf-8") as f:
        json.dump(frais, f, ensure_ascii=False, indent=2)
        f.write(u"\n")
    os.replace(temporaire, chemin)
    return True


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def imprimer(releve):
    if not releve:
        print("aucun siege dans etat/joueurs.json")
        return
    largeur = max(len(m["personnage_id"]) for m in releve)
    print("  seuil : %d minutes de temps reel sans souffle -> vacant"
          % SEUIL_OCCUPATION_MINUTES)
    print("")
    for m in releve:
        print("  {:<{w}}  {:<7} veille {:<8} inbox {:<4} {:<12} {}".format(
            m["personnage_id"],
            "ASSIS" if m["occupe"] else "vacant",
            dire_age(m["veille_age_s"]),
            m["inbox"],
            "tete ecrite" if m["a_tete"] else "SANS TETE",
            m["raison"], w=largeur))
        ennuis = []
        if m["derive"]:
            ennuis.append("le cache de joueurs.json dit '%s' : perime"
                          % ("occupe" if m["cache"] else "vacant"))
        if not m["occupe"] and not m["a_tete"]:
            ennuis.append("VACANT SANS TETE — il ne fera rien hors ecran")
        if m["occupe"] and m["a_tete"]:
            ennuis.append("OCCUPE AVEC UNE TETE — on le joue a sa place")
        if m["inbox_dormant"]:
            ennuis.append("tenu occupe par un inbox qui ne bouge plus depuis "
                          "%s — actions jamais traitees ?"
                          % dire_age(m["inbox_age_s"]))
        for e in ennuis:
            print("  {:<{w}}  -> {}".format("", e, w=largeur))


def main():
    ap = argparse.ArgumentParser(
        description="Qui est assis : la mesure, pas le drapeau.")
    ap.add_argument("--rafraichir", action="store_true",
                    help="recaler le cache `occupe` de etat/joueurs.json")
    ap.add_argument("--vraiment", action="store_true", help="ecrire pour de bon")
    ap.add_argument("--json", action="store_true", help="la mesure brute")
    args = ap.parse_args()

    if args.json:
        print(json.dumps(mesures(), ensure_ascii=False, indent=2))
        return
    if args.rafraichir:
        changements, refuses, releve = rafraichir(args.vraiment)
        imprimer(releve)
        print("")
        if not changements:
            print("  le cache est deja juste : rien a recaler.")
        for m in changements:
            marque = " (REFUSE : sans tete)" if m in refuses else ""
            print("  %s : %s -> %s%s" % (
                m["personnage_id"],
                "occupe" if m["cache"] else "vacant",
                "occupe" if m["occupe"] else "vacant", marque))
        if changements and not args.vraiment:
            print("\n  (rien n'a ete ecrit — ajoutez --vraiment)")
        return
    imprimer(mesures())


if __name__ == "__main__":
    main()
