# -*- coding: utf-8 -*-
# PARLOIR — l'adressage de la parole. (Descente lot 2 de scripts/parloir.py,
# la facade gelee.)
#
# ─────────────────────────────────────────────────────────────────────────────
# LE HOOK-OREILLE EST MORT LE 31.8.2026. L'ancien modele posait un hook
# PostToolUse (`--ecouter --hook`) dans chaque session pour qu'un homme
# entende en cours de route ; plus rien ne l'arme. Le modele est celui des
# canaux (docs/habitant.md §2-§4) : une parole qui t'arrive est un BILLET au
# canal de la paire, tu la recois en PERCEPT a ton prochain reveil — et le
# geste d'ecrire est le reveilleur. L'anachronisme absorbe : un homme en
# session n'entend plus au milieu de sa journee, il lit a son reveil.
# `--ecouter` reste lisible pour la salle commune, mais rien ne le bat.
# ─────────────────────────────────────────────────────────────────────────────
#
# CE QUI VIT ICI :
#   --dire   vers un homme : billet au canal de chambre + reveil cast
#            (billet.ecrire) — present ou absent, plus de distinction ;
#            vers une zone (mj, mj-*) : billet au canal + reveil CAST de la
#            zone (les zones sont des institutions publiques : le canal
#            s'ouvre au premier mot) ;
#            vers `tous` : la criee — etat/parloir/tous.jsonl (une criee
#            n'est pas une paire, elle ne migre pas en canal).
#   --tenter / --faire / --demander : les verbes (habitant.md §3) — la
#            demande ET le verdict se deposent au CANAL homme~zone, le
#            verdict revient en CALL (zone.appeler_zone, inchange).
#   --penser : un reveil de soi-meme — la pensee est un cast a soi
#            (depecher detache, la pensee en elan du jour) ; aucun arbitre,
#            aucun canal : le vecu et demain.md se deposent chez lui.
#
# Usage :
#     python scripts/parloir.py --dire --de mj --a le-sanglier "Reviens au quai"
#     python scripts/parloir.py --tenter --de gerardys --a mj "je pars sur mon cheval"
#     python scripts/parloir.py --demander --de gerardys --a mj "que disent les registres ?"
#     python scripts/parloir.py --dire --de mj --a mj-aurore "Gerardys est a toi"
#     python scripts/parloir.py --dire --de mj --a tous "On ouvre la salle"
#     python scripts/parloir.py --fils                      (les fils restants)
import argparse
import glob
import io
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Un etage de plus qu'a la racine : scripts/agents/ (voir scripts/CLAUDE.md).
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARLOIR = os.path.join(RACINE, "etat", "parloir")
CURSEURS = os.path.join(PARLOIR, ".curseurs")

# LA SALLE COMMUNE. Un nom reserve : ce qu'on y dit, tout le monde l'entend.
# C'est le pendant du `--pour tous` du flux, cote regie — et le seul fil
# jsonl qui survive au modele des canaux.
TOUS = "tous"


def _sain(nom):
    """Un identifiant sert de nom de fichier : on ne laisse pas passer un
    chemin. Ce n'est pas de la paranoia — `--a ../../etat/monde.json` serait
    une ecriture dans l'etat par la porte de derriere."""
    if not re.match(r"^[a-z0-9][a-z0-9_.\-]*$", nom or ""):
        raise SystemExit(u"identifiant illisible : %r" % nom)
    return nom


def nom_du_fil(de, a):
    """Le fil d'une paire, dans un ordre stable — sinon `mj~sara` et
    `sara~mj` seraient deux conversations pour une seule."""
    if a == TOUS:
        return TOUS
    return u"~".join(sorted((_sain(de), _sain(a))))


def membres(fil):
    return fil.split(u"~")


def chemin_fil(fil):
    return os.path.join(PARLOIR, "%s.jsonl" % fil)


def chemin_curseur(fil, lecteur):
    return os.path.join(CURSEURS, "%s.%s" % (fil, _sain(lecteur)))


def fils():
    return sorted(os.path.basename(p)[:-6]
                  for p in glob.glob(os.path.join(PARLOIR, "*.jsonl")))


def ses_fils(qui):
    """Ceux ou il figure, plus la salle commune. Jamais ceux des autres."""
    qui = _sain(qui)
    return [f for f in fils() if f == TOUS or qui in membres(f)]


def dire(de, a, texte):
    """Le depot au fil jsonl — ne sert plus qu'a la criee (`--a tous`).
    Une paire passe par les canaux de chambres (billet.deposer)."""
    de, a = _sain(de), _sain(a)
    fil = nom_du_fil(de, a)
    os.makedirs(PARLOIR, exist_ok=True)
    ligne = {"t": round(time.time()), "de": de, "a": a, "texte": texte}
    with io.open(chemin_fil(fil), "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + u"\n")
    return fil


def _lignes(fil):
    p = chemin_fil(fil)
    if not os.path.exists(p):
        return []
    with io.open(p, encoding="utf-8") as f:
        out = []
        for l in f:
            l = l.strip()
            if l:
                try:
                    out.append(json.loads(l))
                except ValueError:
                    pass
        return out


def _curseur(fil, lecteur):
    p = chemin_curseur(fil, lecteur)
    if not os.path.exists(p):
        return 0
    try:
        with io.open(p, encoding="utf-8") as f:
            return int(f.read().strip() or 0)
    except ValueError:
        return 0


def _poser_curseur(fil, lecteur, n):
    os.makedirs(CURSEURS, exist_ok=True)
    with io.open(chemin_curseur(fil, lecteur), "w", encoding="utf-8") as f:
        f.write(u"%d" % n)


def ecouter(qui, avancer=True):
    """Ce qui est neuf POUR LUI dans les fils jsonl restants (la criee).
    MORT COMME OREILLE depuis le 31.8.2026 : aucun hook ne l'arme plus —
    reste une lecture manuelle. Rend une liste de (fil, ligne)."""
    qui = _sain(qui)
    a_lire = ses_fils(qui)
    neuf = []
    for fil in a_lire:
        lignes = _lignes(fil)
        depuis = _curseur(fil, qui)
        for l in lignes[depuis:]:
            if l.get("de") != qui:
                neuf.append((fil, l))
        if avancer and len(lignes) > depuis:
            _poser_curseur(fil, qui, len(lignes))
    return neuf


def est_un_mj(qui):
    """Convention, et c'est la seule de tout le fichier : un identifiant qui
    commence par « mj » est une regie — `mj`, `mj-aurore`, `mj-nlr`. Tout le
    reste est quelqu'un qui travaille, et a qui l'on ecrit un billet."""
    return qui == "mj" or qui.startswith("mj-")


def _reveiller_zone_detachee(mj, de, texte):
    """Le reveil CAST d'une zone — spawn detache de scripts/reveiller.py
    (le motif de zone.lancer_etabli_detache). On lance une vie, on ne la
    regarde pas vivre : la suite arrive par les canaux."""
    drapeaux = {}
    if os.name == "nt":  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP — detache SANS console visible (spam de terminaux du 31.8)
        drapeaux["creationflags"] = 0x08000000 | 0x00000200
    else:
        drapeaux["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, os.path.join(RACINE, "scripts", "reveiller.py"),
         "--qui", mj, "--de", de, texte],
        cwd=RACINE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, **drapeaux)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dire", action="store_true")
    # LES VERBES (docs/habitant.md §3) : l'acces de l'homme au monde, par le
    # meme adressage que --dire. La resolution est la convention est_un_mj,
    # et elle seule : `mj` et `mj-*` -> un MJ de zone, appele en CALL (le
    # verdict est le retour de commande, dans le fil de sa pensee).
    ap.add_argument("--tenter", action="store_true",
                    help="je tente — l'arbitre de zone tranche en coulisse")
    ap.add_argument("--faire", action="store_true",
                    help="je propose un changement au monde")
    ap.add_argument("--demander", action="store_true",
                    help="que dit le monde ? — reponse depuis l'etat seul")
    # PENSER (habitant.md §3) : un reveil de soi-meme — la pensee est un
    # cast a soi. Aucun arbitre, aucun canal : la pensee part en elan du
    # jour, la session vit ce moment interieur, le vecu et la conclusion
    # (demain.md, fil/) se deposent chez lui par la machinerie existante.
    ap.add_argument("--penser", action="store_true",
                    help="un reveil de soi-meme — cast a soi, aucun arbitre")
    ap.add_argument("--modele", default=None,
                    help="modele du reveil (verbes et --dire)")
    ap.add_argument("--de", default=None)
    ap.add_argument("--a", default=None)
    ap.add_argument("texte", nargs="*")
    ap.add_argument("--ecouter", action="store_true",
                    help="MORT (31.8.2026) : plus rien ne l'arme — lecture "
                         "manuelle des fils restants (la criee)")
    ap.add_argument("--qui", default=None)
    ap.add_argument("--fils", action="store_true",
                    help="l'etat des fils jsonl restants")
    ap.add_argument("--clore", default=None,
                    help="archive les fils jsonl restants d'un nom")
    a = ap.parse_args()

    if a.fils:
        if not fils():
            print(u"aucun fil ouvert")
            return
        for fil in fils():
            lignes = _lignes(fil)
            dern = lignes[-1] if lignes else {}
            print(u"  %-20s %3d ligne(s)   dernier : [%s] %s"
                  % (fil, len(lignes), dern.get("de", u"—"),
                     (dern.get("texte") or u"")[:48]))
        return

    if a.clore:
        qui = _sain(a.clore)
        vises = [qui] if qui in fils() else [f for f in ses_fils(qui)
                                             if f != TOUS]
        arch = os.path.join(RACINE, "etat", "archive", "parloir")
        for fil in vises:
            os.makedirs(arch, exist_ok=True)
            os.replace(chemin_fil(fil),
                       os.path.join(arch, "%s.%d.jsonl" % (fil, int(time.time()))))
            for c in glob.glob(os.path.join(CURSEURS, "%s.*" % fil)):
                os.remove(c)
        print(u"fil(s) clos : %s" % (u", ".join(vises) or u"aucun"))
        return

    if a.penser:
        if not (a.de and a.texte):
            raise SystemExit(u"--penser veut --de et un texte (sa pensee)")
        if a.a:
            raise SystemExit(u"--penser ne prend pas de --a : on se "
                             u"reveille soi-meme")
        pensee = u" ".join(a.texte)
        _sain(a.de)
        # Le cast a soi : la pensee est l'elan particulier du jour
        # (mission(), « L'elan particulier de ce jour »).
        from agents.expose import depecher as _dep
        _dep.depecher(a.de, pensee, a.modele, 15, False, attendre=False)
        return

    verbe = (u"TENTER" if a.tenter else u"FAIRE" if a.faire
             else u"DEMANDER" if a.demander else None)
    if verbe:
        if not (a.de and a.a and a.texte):
            raise SystemExit(u"--%s veut --de, --a et un texte"
                             % verbe.lower())
        if not est_un_mj(a.a):
            raise SystemExit(
                u"un verbe s'adresse a un arbitre de zone (mj, mj-*), pas a "
                u"%r — pour parler a quelqu'un : --dire" % a.a)
        mot = u" ".join(a.texte)
        _sain(a.de)
        # LA TRACE PHYSIQUE D'ABORD : la demande entre au CANAL homme~zone —
        # ce qui s'est dit s'est dit, meme si l'appel echoue ensuite.
        # Imports tardifs — la porte lie zone et billet apres parloir
        # (l'ordre des imports d'expose.py est une contrainte).
        from agents.expose import billet as _b
        from agents.expose import zone as _zone
        from agents import chambre as _ch
        canal = _b.deposer(a.de, a.a, u"[%s] %s" % (verbe, mot))
        # LE CALL (habitant.md §4) : on a besoin du verdict pour continuer.
        verdict = _zone.appeler_zone(a.a, a.de, mot, verbe, modele=a.modele)
        # Le verdict est AUSSI une trace : la reponse du MJ, au meme canal.
        _b.deposer(a.a, a.de, verdict)
        # L'echange a ete vecu en direct des deux cotes : le re-servir en
        # percept au prochain reveil serait du double.
        _ch.marquer_lu(a.de, a.a)
        _ch.marquer_lu(a.a, a.de)
        print(verdict)
        return

    if a.dire:
        if not (a.de and a.a and a.texte):
            raise SystemExit(u"--dire veut --de, --a et un texte")
        texte = u" ".join(a.texte)
        _sain(a.de), _sain(a.a)
        if a.a == TOUS:
            # LA CRIEE : pas une paire — le fil jsonl demeure.
            fil = dire(a.de, a.a, texte)
            print(u"dit a %s (fil %s)" % (a.a, fil))
            return
        # ECRIRE = REVEILLER (habitant.md §4). Present ou absent, plus de
        # distinction d'instance : le billet part au canal, le destinataire
        # le recoit en percept a son prochain reveil — que ce reveil soit
        # celui qu'on caste a l'instant ou un autre deja en cours.
        if a.a == "dev":
            # DEV N'EST JAMAIS DEPECHE (docs/habitant.md, nom reserve) — et
            # mesure du 31.8 : cinq sessions depeche-dev nees des billets des
            # arbitres. Le billet arrive, le developpeur le lit en personne.
            from agents.expose import billet as _b
            canal = _b.deposer(a.de, a.a, texte)
            print(u"billet a dev (canal %s) — jamais depeche, il lira"
                  % os.path.relpath(canal, RACINE))
            return
        if est_un_mj(a.a):
            # Une zone est une institution publique : le canal s'ouvre au
            # premier mot, et le mot part avec le reveil (cast) — DOSE par
            # le cooldown anti-tempete de zone.reveiller_en_cast (31.8).
            from agents.expose import zone as _z
            canal, parti = _z.reveiller_en_cast(a.a, a.de, texte)
            print(u"billet a %s (canal %s) — %s"
                  % (a.a, os.path.relpath(canal, RACINE),
                     u"zone reveillee en cast" if parti else
                     u"cast recent, le billet attend son prochain reveil"))
            return
        from agents.expose import billet as _b
        canal, rep = _b.ecrire(a.de, a.a, texte, modele=a.modele)
        print(u"billet a %s (canal %s) — reveille en cast, log %s"
              % (a.a, os.path.relpath(canal, RACINE),
                 os.path.relpath(rep["log"], RACINE)))
        return

    if a.ecouter:
        if not a.qui:
            raise SystemExit(u"--ecouter veut --qui")
        neuf = ecouter(a.qui)
        for fil, l in neuf:
            print(u"  [%s → %s] %s" % (l.get("de"), fil, l.get("texte")))
        return

    ap.print_help()
