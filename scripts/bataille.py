# -*- coding: utf-8 -*-
"""BATAILLE — cuire une bataille, et la faire tomber dans la partie.

    python scripts/bataille.py                       ou en est-on
    python scripts/bataille.py --cuire               cuire (defauts du four)
    python scripts/bataille.py --cuire --hommes 9500 --duree 900
    python scripts/bataille.py --dater 3 1200        elle a lieu le 3e jour a 20h00
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
def dater(jour, minute, lieu="portreal", vraiment=True):
    man = lire(os.path.join(MONDE, lieu + ".sac.json"))
    if not man:
        sortir("  aucun sac cuit pour « %s » — on ne date pas ce qui n'existe pas."
               % lieu)
    if not lire(os.path.join(MONDE, lieu + ".sac.annales.json")):
        print("  ATTENTION : ce sac n'a pas d'annales. Il porte des corps mais")
        print("  aucun fait — donc rien a percevoir. Recuisez-le.\n")
    d = {"sac": lieu, "debut": {"jour": int(jour), "minute": int(minute)}}
    if vraiment:
        with io.open(ETAT, "w", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=1))
    print("  la bataille a lieu le %d%s jour, a %s."
          % (int(jour), "er" if int(jour) == 1 else "e", hhmm(int(minute))))
    print("  duree : %s s — elle se termine a %s."
          % (man.get("duree_s"), hhmm(int(minute) + (man.get("duree_s") or 0) / 60)))
    print("  ecrit dans etat/bataille.json")


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
        return dater(a[i + 1], a[i + 2])
    if "--eteindre" in a:
        return eteindre()
    if "--recit" in a:
        return recit()
    etat()


main()
