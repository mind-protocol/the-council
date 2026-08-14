# -*- coding: utf-8 -*-
"""LE BÂTI — un seul endroit qui sait ouvrir `monde/<nom>.bati.json`.

    python scripts/monde/bati.py                 les mondes engendrés
    python scripts/monde/bati.py peyredragon     le compte et les usages

POURQUOI. Le chemin du bâti était recopié en dur dans trois lecteurs qui ne se
parlent pas — `scripts/affecter.py`, `scripts/corps.py`, et le décor
`ecrans/modules/monde/bati.js` —, et tous les trois disaient « portreal ». Il y
avait pourtant un second monde engendré, `monde/peyredragon.bati.json`, avec
exactement les mêmes colonnes : il était INJOIGNABLE. Aucune salle de
Peyredragon ne pouvait être affectée, donc le siège du personnage joueur n'avait
aucun mètre — alors que le fichier existait sur le disque depuis des semaines.

La leçon est petite et elle vaut d'être écrite : un chemin en dur ne se voit pas
comme un manque de fonctionnalité, il se voit comme un monde qui n'existe pas.
Le lecteur unique rend le second monde visible par construction, et la liste des
mondes cesse d'être une chose qu'on croit savoir.

LE CONTRAT, le même que partout ailleurs autour de `monde/` : ce dossier est
ENGENDRÉ et régénérable, on n'y écrit jamais depuis le jeu. Ici on ne fait que
lire, et on refuse bruyamment plutôt que de rendre un bâti vide : une liste de
bâtiments silencieusement vide donnerait des distances fausses au lieu d'une
erreur, et une distance fausse ne se remarque jamais.
"""
import io, json, os, sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(RACINE, "monde")

DEFAUT = "portreal"

# Quel script engendre quel monde — pour que le message d'erreur dise la
# commande à taper, et non seulement le fichier qui manque.
ENGENDRE_PAR = {
    "portreal": "python scripts/monde/batir.py",
    "peyredragon": ("python scripts/monde/peyredragon_chateau.py "
                    "puis peyredragon_portes.py et peyredragon_usages.py"),
}


class MondeInconnu(Exception):
    """Un monde qu'on ne sait pas ouvrir — nom inconnu, ou fichier absent."""


def chemin(monde=DEFAUT):
    return os.path.join(DOSSIER, "%s.bati.json" % monde)


def mondes():
    """Les mondes réellement présents sur le disque, par ordre alphabétique."""
    if not os.path.isdir(DOSSIER):
        return []
    return sorted(n[:-len(".bati.json")] for n in os.listdir(DOSSIER)
                  if n.endswith(".bati.json"))


def charger(monde=DEFAUT):
    """(bati, colonnes) — la liste des bâtiments et le dict {nom: index}.

    Lève `MondeInconnu` avec un message qui dit quoi taper. Les appelants en
    ligne de commande l'attrapent et sortent avec un code non nul.
    """
    monde = monde or DEFAUT
    f = chemin(monde)
    if not os.path.exists(f):
        dispo = mondes()
        quoi = ENGENDRE_PAR.get(monde)
        raise MondeInconnu(
            "monde/%s.bati.json manque%s.%s"
            % (monde,
               "" if quoi is None else " — lance d'abord %s" % quoi,
               ("\n  mondes disponibles : %s" % ", ".join(dispo)) if dispo
               else "\n  aucun monde engendré dans monde/."))
    B = json.load(io.open(f, encoding="utf-8"))
    if "bati" not in B or "_colonnes" not in B:
        raise MondeInconnu("monde/%s.bati.json n'a pas la forme attendue "
                           "(clefs « bati » et « _colonnes »)." % monde)
    return B["bati"], {n: k for k, n in enumerate(B["_colonnes"])}


def main():
    a = sys.argv[1:]
    if not a:
        dispo = mondes()
        if not dispo:
            print("  aucun monde engendré dans monde/.")
            return 1
        for m in dispo:
            bati, _ = charger(m)
            print("  %-14s %6d bâtiments%s"
                  % (m, len(bati), "   (défaut)" if m == DEFAUT else ""))
        return 0
    try:
        bati, C = charger(a[0])
    except MondeInconnu as e:
        print("  %s" % e)
        return 1
    usages = {}
    for b in bati:
        usages[b[C["usage"]]] = usages.get(b[C["usage"]], 0) + 1
    print("  %s — %d bâtiments" % (a[0], len(bati)))
    for u, n in sorted(usages.items(), key=lambda t: -t[1]):
        print("   %-24s %4d" % (u, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
