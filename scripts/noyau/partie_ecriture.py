# -*- coding: utf-8 -*-
"""
partie_ecriture.py — comment une ligne ENTRE dans le jsonl d'une partie.

Sorti de partie_greffe.py le 7.9 (audit A6, A10, A11, B5). Le greffe replie
et applique ; ici vit ce qui touche le disque, et dans cet ordre, sous verrou :

1. `verrou(chemin)` — `<chemin>.lock`, `msvcrt` sur Windows, `fcntl` ailleurs,
   comme le journal des affaires (histoire.py). Deux processus (le serveur pour
   un siège, le MJ ou `partie_ia.py` pour l'autre) chargés avant l'écriture de
   l'un produisaient le même `n` : charmed-2 en a trois, successeurs un.
2. `dernier_n_sur_disque(p)` — on relit le fichier : les lignes qu'un autre a
   ajoutées depuis notre chargement sont rattrapées dans la position, et le
   `n` neuf suit celui du DISQUE, pas celui de la mémoire.
3. la validité, puis l'application SUR LA POSITION AVANT D'ÉCRIRE : une ligne
   que la position ne sait pas prendre est refusée et la position remise —
   avant, elle était déjà au livre quand l'application levait, et le chargement
   suivant cassait.
4. l'append, précédé d'un saut de ligne si une demi-ligne traînait.

`rattraper(p, bruts, depuis)` est aussi le chargement : une ligne qui n'est
pas du JSON (tronquée par un append en cours) est ignorée avec un
avertissement, jamais une exception.
"""
import contextlib
import copy
import io
import json
import os
import time

REGISTRES = ("tour", "etats", "ressources", "blocages", "cles", "maillons", "menaces", "consignes")


def _g():
    import partie_greffe as g
    return g


@contextlib.contextmanager
def verrou(chemin, timeout=5.0):
    """Le verrou d'écriture d'une partie, tenu le temps de relire, d'appliquer
    et d'écrire. `TimeoutError` passé `timeout` secondes : on ne devine pas."""
    if os.path.dirname(chemin):
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
    f = io.open(chemin + ".lock", "a+b")
    pris, debut = False, time.time()
    try:
        while not pris:
            try:
                if os.name == "nt":
                    import msvcrt
                    f.seek(0)
                    if not f.read(1):
                        f.write(b"0")
                        f.flush()
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:  # pragma: no cover
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                pris = True
            except OSError:
                if time.time() - debut >= timeout:
                    raise TimeoutError("la partie %s est en cours d'écriture ailleurs" % chemin)
                time.sleep(0.05)
        yield
    finally:
        if pris:
            try:
                if os.name == "nt":
                    import msvcrt
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                else:  # pragma: no cover
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        f.close()


def rattraper(p, bruts, depuis):
    """Replie dans `p` les lignes brutes à partir de la `depuis`-ième non vide."""
    vues = 0
    for brut in bruts:
        brut = brut.strip()
        if not brut:
            continue
        vues += 1
        if vues <= depuis:
            continue
        try:
            ligne = json.loads(brut)
        except ValueError:
            p.avertissements.append("ligne %d illisible (tronquée ?) : ignorée — %s" % (vues, brut[:60]))
            continue
        p.lignes.append(ligne)
        p._appliquer(ligne)


def dernier_n_sur_disque(p):
    """(dernier `n` du fichier, le fichier finit-il sur un saut de ligne). La
    position est rattrapée au passage si le fichier a grandi sans nous."""
    if not os.path.exists(p.chemin):
        return 0, True
    with io.open(p.chemin, "r", encoding="utf-8") as f:
        texte = f.read()
    rattraper(p, texte.split("\n"), len(p.lignes))
    n = max([int(x.get("n") or 0) for x in p.lignes] or [0])
    return n, (texte == "" or texte.endswith("\n"))


def ecrire(p, l):
    """La seule porte d'écriture d'une partie. Rend la liste des refus ; vide =
    la ligne est au livre et dans la position."""
    import partie_tour
    l = dict(l)
    with verrou(p.chemin):
        n, propre = dernier_n_sur_disque(p)
        if l.get("coup") == "agir" and l.get("realise"):
            # Un maillon qui répond à un ❓ ne compte pas pour le tour : la
            # question est gratuite, la réponse l'est aussi (règle 5).
            cible = (p.cles.get(l["realise"]) or p.menaces.get(l["realise"])
                     or p.blocages.get(l["realise"]) or {})
            if cible.get("suspendue_par"):  # regle: reponse-gratuite
                l["repond"] = cible["suspendue_par"]
        refus = p.verifier(l)
        if refus:
            return refus
        l["n"] = n + 1
        l.setdefault("tour", p.tour if l["coup"] != "tour" else p.tour + 1)
        if l["coup"] == "tour":  # regle: passage-du-tour
            l["tour"] = p.tour + 1
            l.update(partie_tour.ligne(p, l["tour"]))
        # APPLIQUER D'ABORD, ÉCRIRE ENSUITE (A11).
        sauve = {k: copy.deepcopy(getattr(p, k)) for k in REGISTRES}
        try:
            p._appliquer_brut(l)
        except Exception as e:  # noqa: BLE001 — tout ce qui lève est un refus, jamais une ligne écrite
            for k, v in sauve.items():
                setattr(p, k, v)
            return ["%s : la ligne ne s'applique pas à la position (%s) ; rien n'est écrit" % (l["coup"], e)]
        with io.open(p.chemin, "a", encoding="utf-8") as f:
            if not propre:
                f.write("\n")   # une demi-ligne traînait : on ne colle pas la nôtre dessus
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
        p.lignes.append(l)
    return []
