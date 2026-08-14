# -*- coding: utf-8 -*-
"""BATAILLE — cuire une bataille, et la faire tomber dans la partie.

    python scripts/bataille.py                       ou en est-on
    python scripts/bataille.py --cuire               cuire (defauts du four)
    python scripts/bataille.py --cuire --hommes 9500 --duree 900
    python scripts/bataille.py --dater 3 1200        elle a lieu le 3e jour a 20h00
    python scripts/bataille.py --dater 3 1200 --lune 5
    python scripts/bataille.py --maintenant          ou elle en est, et qui percoit quoi
    python scripts/bataille.py --eteindre            plus de bataille en cours
    python scripts/bataille.py --recit               ce qui s y est passe, en clair

POURQUOI CE SCRIPT. Les morceaux existaient tous et aucun ne se tenait par la
main : `scripts/monde/sac.js` cuit, `serveur/croiser.js` fait percevoir, et
entre les deux il fallait ecrire un JSON a la main en sachant quoi mettre
dedans. Un v1 tient en trois gestes — on cuit, on date, on joue — et c'est ici.

LES DEUX MOITIES, ET ELLES NE VIVENT PAS AU MEME ENDROIT :

  `monde/<lieu>.sac.*`   CE QUI S'EST PASSE. Engendre, regenerable, bete. On
                         peut le refaire vingt fois, il ne concerne personne
                         tant qu'il n'est pas date.
  `etat/bataille.json`   QUAND CA TOMBE DANS LA PARTIE. Une decision de MJ,
                         donc de l'etat de jeu. Sans ce fichier, aucun joueur
                         ne croisera jamais rien : une bataille cuite n'est
                         pas une bataille en cours.

C'est la meme separation que partout ici, et elle a une consequence agreable :
on peut cuire pendant une seance sans rien changer a la seance, et decider
apres coup si — et quand — ca a eu lieu.
"""
import io
import json
import os
import subprocess
import sys

# La console de Windows est en cp1252 et le script parle avec des fleches : sans
# cette ligne, `--cuire` meurt sur un `→` apres avoir tout bien fait. C'est
# la convention de la maison (voir reprise.py, bilan.py, criticite.py).
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat", "bataille.json")
MONDE = os.path.join(RACINE, "monde")
CROISER = os.path.join(RACINE, "serveur", "croiser.js")


def sortir(m):
    print(m)
    sys.exit(1)


def lire(p, defaut=None):
    try:
        with io.open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defaut


def hhmm(m):
    return "%dh%02d" % (int(m) // 60 % 24, int(m) % 60)


def duree_dite(minutes):
    """« 40 min », « 3 h », « 2 jours » — personne ne lit 2226 minutes."""
    m = int(round(minutes))
    if m < 120:
        return "%d min" % m
    if m < 2880:
        return "%d h" % round(m / 60.0)
    return "%d jours" % round(m / 1440.0)


def mmss(s):
    """Les secondes de bataille, comme les annales les ecrivent."""
    s = int(s)
    return "%d′%02d″" % (s // 60, s % 60)


def date_monde():
    m = lire(os.path.join(RACINE, "etat", "monde.json")) or {}
    return m.get("date") or {}


# LA LUNE COMPTE. Une date de partie, c'est annee/lune/jour/minute — et un
# `debut` qui n'a que le jour tombe le 3e jour de CHAQUE lune. Cette fonction
# est le pendant exact de `enMinutes` dans `serveur/croiser.js` : si l'une
# change, l'autre change.
def en_minutes(d, ref=None):
    if not d or not isinstance(d.get("jour"), int):
        return None
    ref = ref or {}
    a = d.get("annee", ref.get("annee", 0))
    l = d.get("lune", ref.get("lune", 1))
    return ((a * 12 + l) * 30 + d["jour"]) * 1440 + (d.get("minute") or 0)


def debut_de(cours):
    """Le debut de la bataille, lune et annee comprises.

    Les fichiers ecrits avant que la lune compte n'ont que `jour` et `minute`.
    On les lit dans la lune qui court — ce que le MJ voulait dire en tapant
    `--dater 3 1200` — et on le DIT, parce qu'un fichier incomplet qu'on
    complete en silence est un fichier qu'on ne corrigera jamais.
    """
    d = dict((cours or {}).get("debut") or {})
    ici = date_monde()
    manque = [c for c in ("annee", "lune") if c not in d]
    for c in manque:
        d[c] = ici.get(c, 129 if c == "annee" else 1)
    return d, manque


def dire_date(d):
    return "%s%s jour de la %se lune, %s" % (
        d.get("jour"), "er" if d.get("jour") == 1 else "e",
        d.get("lune", "?"), hhmm(d.get("minute", 0)))


# --- ou en est-on -----------------------------------------------------------
def etat(lieu="portreal"):
    man = lire(os.path.join(MONDE, lieu + ".sac.json"))
    ann = lire(os.path.join(MONDE, lieu + ".sac.annales.json"))
    cours = lire(ETAT)

    if not man:
        print("  aucun sac cuit pour « %s »." % lieu)
        print("  → python scripts/bataille.py --cuire")
    else:
        print("  LE SAC — %s, %s hommes, %s s de bataille"
              % (man.get("porte"), man.get("hommes"), man.get("duree_s")))
        print("    %s corps, %s images, cuit en %s s"
              % (man.get("corps"), man.get("images"), man.get("cuisson_s")))
        i = man.get("issue") or {}
        print("    issue : %s morts, %s fuyards, verrou %s"
              % (i.get("morts"), i.get("fuyards"),
                 (i.get("verrou") or {}).get("etat")))
        if ann:
            q = ann.get("par_quoi") or {}
            print("    annales : %s faits — %s"
                  % (ann.get("faits"),
                     ", ".join("%s %s" % (v, k) for k, v in
                               sorted(q.items(), key=lambda p: -p[1])[:6])))
        else:
            print("    (pas d'annales — ce sac est anterieur a leur ecriture,"
                  " recuisez-le)")

    print()
    if not cours:
        print("  ELLE N'A PAS LIEU. Aucun joueur ne croisera rien.")
        print("  → python scripts/bataille.py --dater <jour> <minute>")
    else:
        d = cours.get("debut") or {}
        print("  ELLE A LIEU — %s%s jour, a %s (sac « %s »)"
              % (d.get("jour"), "er" if d.get("jour") == 1 else "e",
                 hhmm(d.get("minute", 0)), cours.get("sac")))
        print("    tout pas de balade a portee la fera percevoir :"
              " vu, entendu, ou trouve par terre.")


# --- cuire ------------------------------------------------------------------
def cuire(reste):
    four = os.path.join(RACINE, "scripts", "monde", "sac.js")
    if not os.path.exists(four):
        sortir("  pas de four : scripts/monde/sac.js est introuvable.")
    cmd = ["node", four] + reste
    print("  " + " ".join(cmd) + "\n")
    # LE FOUR PARLE PENDANT QU'IL TRAVAILLE, et on le laisse parler : une
    # cuisson longue sans un mot est une cuisson qu'on croit plantee.
    r = subprocess.run(cmd, cwd=RACINE)
    if r.returncode:
        sortir("\n  le four a rendu %d — rien n'a ete date." % r.returncode)
    print()
    etat()


# --- dater ------------------------------------------------------------------
def dater(jour, minute, lieu="portreal", lune=None, annee=None, vraiment=True):
    man = lire(os.path.join(MONDE, lieu + ".sac.json"))
    if not man:
        sortir("  aucun sac cuit pour « %s » — on ne date pas ce qui n'existe pas."
               % lieu)
    if not lire(os.path.join(MONDE, lieu + ".sac.annales.json")):
        print("  ATTENTION : ce sac n'a pas d'annales. Il porte des corps mais")
        print("  aucun fait — donc rien a percevoir. Recuisez-le.\n")
    # LA LUNE ET L'ANNEE VIENNENT DU MONDE, et elles s'ecrivent. Sans elles, la
    # nuit se rejouait a l'identique le meme jour de chaque lune — la porte
    # tombait une seconde fois trente jours plus tard, et rien nulle part
    # n'expliquait pourquoi. On peut les forcer (`--lune`, `--annee`) pour dater
    # une bataille dans une autre lune que celle qui court.
    ici = date_monde()
    d = {"sac": lieu, "debut": {
        "annee": int(annee) if annee is not None else ici.get("annee", 129),
        "lune": int(lune) if lune is not None else ici.get("lune", 1),
        "jour": int(jour), "minute": int(minute)}}
    if vraiment:
        with io.open(ETAT, "w", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=1))
    fin = int(minute) + (man.get("duree_s") or 0) / 60
    print("  la bataille a lieu le %s." % dire_date(d["debut"]))
    print("  duree : %s s — elle se termine a %s%s."
          % (man.get("duree_s"), hhmm(fin), " le lendemain" if fin >= 1440 else ""))
    # OU EN EST LE MONDE PAR RAPPORT A ELLE. Dater dans le passe d'un siege est
    # une faute qu'on ne voit pas autrement : cet homme a deja vecu cette
    # heure-la sans rien croiser, et ce qu'il aurait du percevoir est perdu.
    t0 = en_minutes(d["debut"])
    for pid, h in sorted((lire(os.path.join(RACINE, "etat", "horloges.json"))
                          or {}).items()):
        dt = (en_minutes(h) or 0) - t0
        if dt > 0:
            print("  ATTENTION : %s est deja au-dela (%s) — ce siege a passe"
                  " cette heure-la sans rien croiser." % (pid, duree_dite(dt)))
    print("  ecrit dans etat/bataille.json")


# --- ou en est-elle, et qui en percoit quoi ---------------------------------
# LA QUESTION QUE LE MJ SE POSE VRAIMENT. Le manuel l'ecrit partout : « avant
# de narrer un fait, le joueur a-t-il une source pour savoir cela ? » Pour une
# bataille cuite, cette question a une reponse EXACTE — trois portees, une
# position, une minute — et jusqu'ici le MJ devait la deviner. Il pouvait lire
# le recit complet, c'est-a-dire tout ce que son joueur n'a pas le droit de
# savoir, ce qui est la pire aide possible.
#
# ON NE REECRIT PAS LA PERCEPTION ICI. `serveur/croiser.js` tient la table des
# portees ; on l'appelle par sa ligne de commande. Deux implementations d'un
# meme brouillard, ce sont deux brouillards, et l'on passe ses soirees a
# chercher lequel ment. C'est la doctrine du four, qui importe `bataille2d.js`
# au lieu de le refaire.
def position(pid, corps, presence):
    """Ou se tient cet homme, en metres — l'homme d'abord, sa salle ensuite."""
    aff = corps.get("affectations") or {}
    p = (presence.get("presence") or {}).get(pid) or {}
    salle = p.get("salle")
    for cle in ["personnage:" + pid] + ([("salle:" + salle), ("lieu:" + salle)]
                                        if salle else []):
        a = aff.get(cle)
        if a and isinstance(a.get("xyz"), list) and len(a["xyz"]) >= 2:
            return a["xyz"], cle, a.get("monde")
    return None, None, None


def percu(x, y, d):
    """Ce qu'on percoit de la bataille depuis (x, y) a cette date."""
    try:
        r = subprocess.run(
            ["node", CROISER, "port-real", str(x), str(y),
             str(d.get("annee", 0)), str(d.get("lune", 1)),
             str(d.get("jour", 0)), str(d.get("minute", 0))],
            cwd=RACINE, capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout) if r.stdout.strip() else None
    except Exception:
        return None


def tranche_lisible(lieu, s0, s1, niveau=2):
    """Les lignes du niveau demande entre deux secondes de bataille.

    On passe par `scripts/monde/annales.js` — la table des niveaux vit la-bas
    et nulle part ailleurs. En rendre une copie ici la ferait diverger au
    premier fait qu'on ajoute au four.
    """
    outil = os.path.join(RACINE, "scripts", "monde", "annales.js")
    src = os.path.join(MONDE, lieu + ".sac.annales.json")
    try:
        r = subprocess.run(
            ["node", outil, src, "--niveau", str(niveau), "--depuis", str(int(s0)),
             "--jusqu-a", str(int(s1)), "--par", "temps", "--tranche", "0",
             "--sortie", "-", "--muet"],
            cwd=RACINE, capture_output=True, text=True, timeout=60,
            encoding="utf-8")
        # Le document est du markdown : les faits sont les lignes en puce.
        return [l[2:] for l in (r.stdout or "").splitlines() if l.startswith("- ")]
    except Exception:
        return []


def maintenant(lieu="portreal"):
    cours = lire(ETAT)
    if not cours:
        sortir("  aucune bataille datee. → python scripts/bataille.py --dater"
               " <jour> <minute>")
    ann = lire(os.path.join(MONDE, lieu + ".sac.annales.json")) or {}
    faits = ann.get("detail") or []
    recit = ann.get("recit") or []
    man = lire(os.path.join(MONDE, lieu + ".sac.json")) or {}
    debut, manque = debut_de(cours)
    t0 = en_minutes(debut)
    duree = man.get("duree_s") or 0

    print("  LA NUIT — %s, %s hommes, %s s"
          % (man.get("porte"), man.get("hommes"), duree))
    print("  elle commence le %s." % dire_date(debut))
    if manque:
        print("  (etat/bataille.json ne dit pas %s : lu dans la lune qui court."
              % " ni ".join({"annee": "l'annee", "lune": "la lune"}[c]
                            for c in manque))
        print("   → redatez-la pour de bon : python scripts/bataille.py --dater"
              " %d %d)" % (debut["jour"], debut.get("minute", 0)))
    print()

    horloges = lire(os.path.join(RACINE, "etat", "horloges.json")) or {}
    corps = lire(os.path.join(RACINE, "etat", "corps.json")) or {}
    presence = lire(os.path.join(RACINE, "etat", "presence.json")) or {}
    sieges = [s for s in (lire(os.path.join(RACINE, "etat", "joueurs.json")) or [])
              if s.get("occupe") and not s.get("regie")]

    for s in sieges:
        pid = s.get("personnage_id")
        d = horloges.get(pid) or date_monde()
        ecoule = (en_minutes(d) or 0) - t0          # en minutes
        print("  %s — %s" % (pid.upper(), dire_date(d)))
        if ecoule < 0:
            print("    a son heure, elle n'a pas encore commence : dans %s."
                  % duree_dite(-ecoule))
        elif ecoule * 60 > duree:
            print("    a son heure, elle est finie depuis %s."
                  % duree_dite(ecoule - duree / 60))
        else:
            print("    A SON HEURE, ELLE COURT : %s de bataille ecoulees."
                  % mmss(ecoule * 60))
        xyz, cle, monde = position(pid, corps, presence)
        if not xyz:
            print("    aucune adresse physique : rien ne peut lui parvenir.")
            print("    → scripts/affecter.py, ou une balade qui lui en donne une.\n")
            continue
        if monde and monde != "port-real":
            print("    a %s — hors de portee de cette nuit.\n" % monde)
            continue
        r = percu(xyz[0], xyz[1], d)
        print("    ou : %s (%s, %d %d)" % (
            ((presence.get("presence") or {}).get(pid) or {}).get("lieu") or "?",
            cle, xyz[0], xyz[1]))
        if not r or not (r["vu"] or r["entendu"] or r["traces"]):
            print("    rien ne lui parvient d'ici, a cette minute.\n")
            continue
        for e in r["vu"]:
            print("    VU      %s — a %s pas, %s" % (e["quoi"], e["pas"], e["ou"]))
        for e in r["entendu"]:
            print("    ENTENDU %s — %s%s" % (e["quoi"], e.get("ou") or "?",
                                             ", " + e["vers"] if e.get("vers") else ""))
        for e in r["traces"]:
            print("    TRACE   %s — a %s pas, depuis %s min"
                  % (e["quoi"], e["pas"], e.get("depuis_min")))
        if r.get("arret"):
            print("    → CA ARRETE SA MARCHE.")
        print()

    # CE QUI TOMBE DANS LE QUART D'HEURE — et l'horloge qui sert d'ancre n'est
    # PAS la plus avancee. C'est la regle du monde (les acteurs agissent au
    # present du siege le plus en avance), et elle ne vaut pas ici : le siege le
    # plus avance est le plus souvent celui qui est ailleurs et deux jours plus
    # loin, et l'on affichait alors « 0 fait » pendant qu'un homme se tenait
    # sous la porte. L'ancre est donc le siege qui EST DANS LA NUIT, le moins
    # avance d'entre eux — celui pour qui le quart d'heure suivant est encore a
    # jouer. Ce n'est pas le recit entier : ce que le joueur n'a pas le droit de
    # savoir n'aide pas le MJ, ca le gene.
    dedans = []
    for s in sieges:
        pid = s.get("personnage_id")
        e = ((en_minutes(horloges.get(pid) or date_monde()) or 0) - t0) * 60
        if 0 <= e <= duree:
            dedans.append((e, pid))
    if not dedans:
        print("  AUCUN SIEGE N'EST DANS CETTE NUIT — rien a preparer pour"
              " l'instant.")
        return
    s0, pid = min(dedans)
    s1 = s0 + 900
    total = len([f for f in faits if s0 <= f["t"] < s1])
    print("  LE QUART D'HEURE QUI VIENT POUR %s (a %s de bataille)"
          % (pid.upper(), mmss(s0)))
    # AU NIVEAU 2, PAS EN ENTIER. A dix-sept cents hommes, un quart d'heure
    # pese trois cent cinquante faits dont l'immense majorite sont des hommes
    # rattrapes et remis en ligne : un mur qu'on ne lit pas, donc un outil dont
    # on ne se sert plus. `scripts/monde/annales.js` tient deja le classement —
    # on l'appelle au lieu de le recopier ici.
    lignes = tranche_lisible(lieu, s0, s1)
    if lignes:
        for l in lignes[:14]:
            print("    " + l)
        if len(lignes) > 14:
            print("    … et %d autres" % (len(lignes) - 14))
        print("    (%d faits en tout sur ce quart d'heure ; ci-dessus, ce qu'un"
              " rapport retiendrait)" % total)
    else:
        print("    rien qu'un rapport retiendrait, sur %d faits." % total)
    print("    → le detail : node scripts/monde/annales.js monde/%s"
          ".sac.annales.json --niveau 3 --depuis %d --jusqu-a %d --sortie -"
          % (lieu, s0, s1))


def eteindre():
    if os.path.exists(ETAT):
        os.remove(ETAT)
        print("  etat/bataille.json retire — plus aucune bataille en cours.")
        print("  (le sac reste dans monde/ : on peut la redater quand on veut.)")
    else:
        print("  il n'y en avait pas.")


def recit(lieu="portreal", combien=40):
    ann = lire(os.path.join(MONDE, lieu + ".sac.annales.json"))
    if not ann:
        sortir("  pas d'annales pour « %s »." % lieu)
    for l in (ann.get("recit") or [])[:combien]:
        print("  " + l)
    reste = len(ann.get("recit") or []) - combien
    if reste > 0:
        print("  … et %d autres" % reste)


def main():
    a = sys.argv[1:]
    if "--cuire" in a:
        i = a.index("--cuire")
        return cuire(a[:i] + a[i + 1:])
    if "--dater" in a:
        i = a.index("--dater")
        if len(a) < i + 3:
            sortir("  --dater attend <jour> <minute>  (ex. --dater 3 1200)")
        opt = lambda n: (a[a.index(n) + 1] if n in a and len(a) > a.index(n) + 1
                         else None)
        return dater(a[i + 1], a[i + 2], lune=opt("--lune"), annee=opt("--annee"))
    if "--eteindre" in a:
        return eteindre()
    if "--maintenant" in a:
        return maintenant()
    if "--recit" in a:
        return recit()
    etat()


main()
