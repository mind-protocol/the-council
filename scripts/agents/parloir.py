# -*- coding: utf-8 -*-
# PARLOIR — se parler pendant qu'on travaille. (Descente lot 2 de
# scripts/parloir.py, qui reste la facade gelee : les hooks PostToolUse de
# .claude/settings.json tapent ce chemin-la — PARLOIR_ABS le garde.)
#
# `depecher.py` envoie un homme vivre sa journee dans une session a lui, et
# jusqu'ici c'etait un aller-retour muet : on le lachait, on attendait, il
# rentrait. Le parloir est le fil qui reste ouvert pendant ce temps-la. Le MJ
# peut le relancer en cours de journee (« il te repond quoi, Hask ? ») au lieu
# de le rappeler dans une session neuve qui a tout oublie.
#
# ─────────────────────────────────────────────────────────────────────────────
# COMMENT CA BAT. Un hook PostToolUse, des deux cotes, qui lance `--ecouter`.
# Ce n'est PAS un timer : le hook ne bat que quand la session appelle un
# outil. En pratique cela suffit — le MJ enchaine les scripts, et l'homme
# depeche ne fait que Read et Grep toute sa journee. Mais il faut le savoir :
# une session qui redige trois cents mots sans toucher un fichier n'entend
# rien pendant ce temps.
#
# LE SILENCE NE COUTE RIEN. Sans nouveau message, `--ecouter` n'ecrit pas une
# ligne et sort 0. C'est la condition pour qu'un hook sur TOUS les outils ne
# pourrisse pas le contexte : sur une journee d'homme il bat cent fois et ne
# se voit que quand on lui parle.
#
# UN FIL PAR PAIRE, et personne n'est d'une espece a part. Le fil de deux
# interlocuteurs est `etat/parloir/<a>~<b>.jsonl`, les deux noms tries : le MJ
# qui parle a un homme, deux MJ qui se parlent par-dessus la salle commune,
# deux hommes qu'on a laisses ensemble — c'est le meme objet et le meme code.
# `tous` est le nom reserve de la salle commune, que tout le monde entend.
#
# QUI ECOUTE QUOI. On entend les fils ou l'on figure, et la salle commune ;
# jamais les fils des autres. Le curseur est par (fil, lecteur), donc on ne se
# reentend jamais soi-meme et deux MJ ne se volent pas leurs messages.
#
# Usage :
#     python scripts/parloir.py --dire --de mj --a le-sanglier "Reviens au quai"
#     python scripts/parloir.py --tenter --de gerardys --a mj "je pars sur mon cheval"
#     python scripts/parloir.py --demander --de gerardys --a mj "que disent les registres ?"
#     python scripts/parloir.py --dire --de mj --a mj-aurore "Gerardys est a toi"
#     python scripts/parloir.py --dire --de mj --a tous "On ouvre la salle"
#     python scripts/parloir.py --ecouter --qui le-sanglier
#     python scripts/parloir.py --ecouter --qui mj --hook   (sortie pour hook)
#     python scripts/parloir.py --fils                      (l'etat des fils)
import argparse
import glob
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Un etage de plus qu'a la racine : scripts/agents/ (voir scripts/CLAUDE.md).
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PARLOIR = os.path.join(RACINE, "etat", "parloir")
CURSEURS = os.path.join(PARLOIR, ".curseurs")
PARLOIR_ABS = os.path.join(RACINE, "scripts", "parloir.py").replace("\\", "/")

# LA SALLE COMMUNE. Un nom reserve : ce qu'on y dit, tout le monde l'entend.
# C'est le pendant du `--pour tous` du flux, cote regie.
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


INSTANCES = os.path.join(PARLOIR, ".instances")


def ouvrir_instance(homme, jeton, quoi=None, minutes=None):
    """Declare une session ouverte pour cet homme, et rend son identite.

    LE FIL PORTE LA SESSION, PAS L'HOMME — mesure du 9 aout, apres qu'une
    phrase adressee a ser Robert fut entendue par une AUTRE session de ser
    Robert, lancee au meme moment par la boucle d'activation. Deux instances
    du meme acteur partageaient un fil et un curseur : la premiere qui
    ecoutait consommait le message de la seconde, et la seconde attendait une
    reponse qui ne venait pas. C'est la meme faute que deux regies nommees
    « mj », vue de l'autre bout.

    `minutes` est le budget de sa journee — le `timeout` que `depecher.py` pose
    sur sa session. On l'ecrit ici parce que c'est la seule fin qu'on connaisse
    d'avance : un fichier d'instance survit a une session tuee (le `finally` ne
    passe pas), et sans echeance ecrite rien ne distingue un homme au travail
    d'un orphelin de la semaine derniere. Voir `vivants()`.
    """
    ident = u"%s.%s" % (_sain(homme), _sain(jeton))
    os.makedirs(INSTANCES, exist_ok=True)
    with io.open(os.path.join(INSTANCES, ident), "w", encoding="utf-8") as f:
        f.write(json.dumps({"homme": homme, "jeton": jeton, "t": round(time.time()),
                            "minutes": int(minutes) if minutes else None,
                            "quoi": quoi or u""}, ensure_ascii=False))
    return ident


def fermer_instance(ident):
    """Sa session est finie : elle n'ecoute plus. Le FIL reste — ce qui s'y
    est dit s'est dit — mais on cesse de l'annoncer comme un interlocuteur."""
    try:
        os.remove(os.path.join(INSTANCES, ident))
    except OSError:
        pass


def instances(homme=None):
    if not os.path.isdir(INSTANCES):
        return []
    tous = sorted(os.listdir(INSTANCES))
    return [i for i in tous
            if homme is None or i == homme or i.startswith(homme + u".")]


MINUTES_DEFAUT = 15   # le defaut de `depecher.py --minutes`
MARGE = 90            # secondes : le temps de rentrer et d'ecrire son rapport


def vivants(purger=True):
    """Qui est REELLEMENT dehors, a la minute — et depuis combien de temps.

    Un fichier d'instance ne prouve rien a lui seul : trois orphelines
    trainaient deja apres les essais du 9 aout, et il en reste une de ce matin
    (robert-quince.1). Ce qui tranche, c'est le budget de sa session : passe
    `t + minutes`, sa journee est finie de toute facon — le processus est mort,
    tue, ou rentre sans que le `finally` ait pu passer. On le retire alors du
    dossier plutot que de le laisser mentir a l'ecran.
    """
    out, mort = [], []
    for ident in instances():
        chemin = os.path.join(INSTANCES, ident)
        try:
            with io.open(chemin, encoding="utf-8") as f:
                d = json.loads(f.read() or "{}")
        except Exception:
            d = {}
        depuis = time.time() - (d.get("t") or os.path.getmtime(chemin))
        budget = (d.get("minutes") or MINUTES_DEFAUT) * 60 + MARGE
        if depuis > budget:
            mort.append(chemin)
            continue
        out.append({"id": ident, "homme": d.get("homme") or ident.split(".")[0],
                    "quoi": d.get("quoi") or u"", "depuis": int(depuis),
                    "reste": int(budget - depuis)})
    if purger:
        for c in mort:
            try: os.remove(c)
            except OSError: pass
    return out


def resoudre(a):
    """A qui l'on parle vraiment — et la reponse est TOUJOURS ce qu'on a
    ecrit. On ne redirige jamais un nom nu vers une instance.

    C'est deliberé et ce n'est pas de la timidite. La boucle d'activation pose
    le guichet de son acteur sous son nom NU (`poser_le_parloir(neutre, pid)`)
    et n'a aucun jeton a donner ; une resolution « intelligente » qui devinerait
    l'instance lui volerait ses messages — exactement le mal qu'on repare.
    Chacun ecoute donc sous le nom qu'il a declare, et l'on nomme son
    interlocuteur en entier. `--instances` dit lesquels existent.
    """
    if a == TOUS or est_un_mj(a) or u"." in a:
        return a
    autres = [i for i in instances(a) if i != a]
    if autres:
        sys.stderr.write(
            u"(note : %s a aussi %d session(s) depechee(s) — %s)\n"
            % (a, len(autres), u", ".join(autres)))
    return a


def ses_fils(qui):
    """Ceux ou il figure, plus la salle commune. Jamais ceux des autres."""
    qui = _sain(qui)
    return [f for f in fils() if f == TOUS or qui in membres(f)]


def dire(de, a, texte):
    de, a = _sain(de), _sain(resoudre(a))
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
    """Ce qui est neuf POUR LUI. Rend une liste de (fil, ligne).

    On avance le curseur sur tout ce qu'on a lu, y compris ses propres
    paroles : sinon il se les reentendrait au premier message d'en face.
    """
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
    reste est quelqu'un qui travaille, et a qui l'on parle autrement."""
    return qui == "mj" or qui.startswith("mj-")


def rendre(neuf, pour):
    """Le bloc qu'on glisse dans la tete de celui qui ecoute."""
    chemin = "scripts/parloir.py" if est_un_mj(pour) else PARLOIR_ABS
    if est_un_mj(pour):
        tete = (u"AU PARLOIR — on t'adresse la parole hors fiction. Ce n'est "
                u"ni le joueur, ni un item du flux : c'est une autre regie ou "
                u"un homme que tu as depeche. Rien de tout cela n'entre dans "
                u"l'etat, ne coute une minute, ni ne se voit a l'ecran.\n"
                u"Reponds sans t'arreter de jouer :\n")
    else:
        tete = (u"ON TE PARLE, ici, maintenant — pose ce que tu fais et "
                u"ecoute. Ce n'est pas une note de service : c'est quelqu'un "
                u"qui s'adresse a toi pendant ta journee, et tu lui reponds "
                u"comme tu repondrais dans une piece. Puis tu reprends ton "
                u"travail la ou tu l'avais laisse ; ce qui se dit ici ne "
                u"remplace pas ton rapport final.\n")
    # La commande de reponse porte le NOM de celui qui a parle. Sans ca on
    # repond « au parloir » dans le vide, et a plusieurs interlocuteurs on
    # repond au mauvais.
    corps = u"\n".join(
        u"  [%s] %s\n      → python %s --dire --de %s --a %s \"...\""
        % (l["de"], l["texte"], chemin, pour,
           l["de"] if l.get("a") != TOUS else TOUS)
        for _, l in neuf)
    return tete + u"\n" + corps


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dire", action="store_true")
    # LES VERBES (docs/habitant.md §3, pas 4) : l'acces de l'homme au monde,
    # par le meme adressage que --dire. La resolution est la convention
    # est_un_mj, et elle seule : `mj` et `mj-*` -> un MJ de zone, appele en
    # CALL (le verdict est le retour de commande, dans le fil de sa pensee) ;
    # le reste -> un homme, depot simple (son reveil est le pas 5).
    ap.add_argument("--tenter", action="store_true",
                    help="je tente — l'arbitre de zone tranche en coulisse")
    ap.add_argument("--faire", action="store_true",
                    help="je propose un changement au monde")
    ap.add_argument("--demander", action="store_true",
                    help="que dit le monde ? — reponse depuis l'etat seul")
    ap.add_argument("--modele", default=None,
                    help="modele du MJ de zone (verbes seulement)")
    ap.add_argument("--de", default=None)
    ap.add_argument("--a", default=None)
    ap.add_argument("texte", nargs="*")
    ap.add_argument("--ecouter", action="store_true")
    ap.add_argument("--qui", default=None)
    ap.add_argument("--hook", action="store_true",
                    help="sortie JSON pour un hook PostToolUse")
    ap.add_argument("--fils", action="store_true",
                    help="l'etat des fils ouverts")
    ap.add_argument("--ouvrir", default=None, metavar="HOMME",
                    help="declare une session ouverte ; --jeton la nomme")
    ap.add_argument("--jeton", default=None,
                    help="ce qui distingue cette session-la des autres")
    ap.add_argument("--instances", action="store_true",
                    help="les sessions ouvertes, et a qui l'on peut parler")
    ap.add_argument("--vivants", action="store_true",
                    help="qui est dehors a la minute, et pour combien de temps")
    ap.add_argument("--clore", default=None,
                    help="archive le fil d'un homme (fin de sa journee)")
    a = ap.parse_args()

    if a.ouvrir:
        print(ouvrir_instance(a.ouvrir, a.jeton or u"1"))
        return

    if a.vivants:
        v = vivants()
        for x in v:
            print(u"  %-24s dehors depuis %2d min · encore %2d min"
                  % (x["homme"], x["depuis"] // 60, x["reste"] // 60))
        if not v:
            print(u"  personne n'est dehors")
        return

    if a.instances:
        for i in instances():
            print(u"  --a %s" % i)
        if not instances():
            print(u"aucune session ouverte")
        return

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
        # On clot TOUS ses fils : sa journee est finie, pas seulement sa
        # conversation avec l'un d'eux. La salle commune ne se clot jamais
        # par ce biais — il faudrait la nommer explicitement.
        qui = _sain(a.clore)
        vises = [qui] if qui in fils() else [f for f in ses_fils(qui)
                                             if f != TOUS]
        for i in instances(qui):   # la session est finie : elle n'ecoute plus
            try:
                os.remove(os.path.join(INSTANCES, i))
            except OSError:
                pass
        arch = os.path.join(RACINE, "etat", "archive", "parloir")
        for fil in vises:
            os.makedirs(arch, exist_ok=True)
            os.replace(chemin_fil(fil),
                       os.path.join(arch, "%s.%d.jsonl" % (fil, int(time.time()))))
            for c in glob.glob(os.path.join(CURSEURS, "%s.*" % fil)):
                os.remove(c)
        print(u"fil(s) clos : %s" % (u", ".join(vises) or u"aucun"))
        return

    verbe = (u"TENTER" if a.tenter else u"FAIRE" if a.faire
             else u"DEMANDER" if a.demander else None)
    if verbe:
        if not (a.de and a.a and a.texte):
            raise SystemExit(u"--%s veut --de, --a et un texte"
                             % verbe.lower())
        mot = u" ".join(a.texte)
        # LA TRACE PHYSIQUE D'ABORD : le mot entre au fil comme un --dire —
        # ce qui s'est dit s'est dit, meme si l'appel echoue ensuite.
        fil = dire(a.de, a.a, u"[%s] %s" % (verbe, mot))
        if not est_un_mj(a.a):
            # Un homme : depot simple — son reveil est le pas 5.
            print(u"dit a %s (fil %s)" % (a.a, fil))
            return
        # LE CALL (habitant.md §4) : on a besoin du verdict pour continuer.
        # Import tardif — la porte lie zone apres parloir (l'ordre des
        # imports d'expose.py est une contrainte).
        from agents.expose import zone as _zone
        verdict = _zone.appeler_zone(a.a, a.de, mot, verbe, modele=a.modele)
        # Le verdict est AUSSI une trace physique : la reponse du MJ, au fil.
        dire(a.a, a.de, verdict)
        print(verdict)
        return

    if a.dire:
        if not (a.de and a.a and a.texte):
            raise SystemExit(u"--dire veut --de, --a et un texte")
        fil = dire(a.de, a.a, u" ".join(a.texte))
        print(u"dit a %s (fil %s)" % (a.a, fil))
        return

    if a.ecouter:
        if not a.qui:
            raise SystemExit(u"--ecouter veut --qui")
        neuf = ecouter(a.qui)
        if not neuf:
            return  # LE SILENCE EST MUET : pas une ligne, pas de bruit
        bloc = rendre(neuf, a.qui)
        if a.hook:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": bloc}}, ensure_ascii=False))
        else:
            print(bloc)
        return

    ap.print_help()


