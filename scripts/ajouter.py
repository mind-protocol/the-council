# Ajoute UN enregistrement a une table d'empilement, sans jamais reecrire ce
# qu'on n'a pas lu a l'instant meme.
#
# Usage :
#     python scripts/ajouter.py actes '{"id":"acte-042", ...}'
#     python scripts/ajouter.py vues --fichier v.json
#     python scripts/ajouter.py paroles '<json>' '<json>' ...
#
# POURQUOI. A deux MJ, l'ecriture du monde est optimiste : chacun edite, et l'on
# rattrape apres coup. Ca marche pour tout, SAUF une chose — la reecriture d'un
# tableau entier. Je lis actes.json, je reflechis deux minutes, l'autre session y
# ajoute un acte, j'ecris ma version : son acte a disparu, et personne ne le
# saura jamais. Ce n'est pas un conflit a arbitrer, c'est une perte silencieuse.
#
# Ce script ne supprime pas la course : il la reduit a rien. Il relit le fichier
# et le reecrit dans la meme milliseconde, au lieu d'etaler l'operation sur toute
# ma duree de reflexion. Pour les quatre tables ou l'on EMPILE, c'est le seul
# geste d'ecriture autorise quand deux sessions jouent.
#
# Les autres tables (personnages, relations, maisons, monde, intentions) restent
# editables a la main : on y modifie une fiche existante, les collisions y sont
# rares, visibles, et reparables en une ligne.
import io, json, os, sys, tempfile

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Table -> la clef qui porte la liste, ou None si le fichier EST la liste.
TABLES = {
    "actes": None,
    "paroles": None,
    "info": None,
    "annales": None,
    "objectifs": None,
    "vues": "vues",
}


def chemin(table, joueur=None):
    """Le fichier de la table — dans le dossier du joueur s'il y en a un.

    Les croyances (vues, jetons, objectifs) appartiennent a un joueur : a deux,
    elles vivent dans etat/joueurs/<id>/. Repli sur etat/ si ce dossier n'existe
    pas encore, pour qu'une partie seule ne voie aucune difference.
    """
    if joueur:
        p = os.path.join(racine, "etat", "joueurs", joueur, table + ".json")
        if os.path.exists(p):
            return p
    return os.path.join(racine, "etat", table + ".json")


def ecrire_atomique(p, donnees):
    """Fichier temporaire puis remplacement : jamais de fichier a moitie ecrit."""
    d = os.path.dirname(p)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with io.open(fd, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def ajouter(table, enregistrements, joueur=None):
    if table not in TABLES:
        raise SystemExit(
            "Table inconnue : %s. Tables d'empilement : %s.\n"
            "Les autres se modifient a la main (on y edite une fiche, on n'empile pas)."
            % (table, ", ".join(sorted(TABLES))))
    p = chemin(table, joueur)
    # --- la fenetre etroite commence ici -----------------------------------
    with io.open(p, encoding="utf-8") as f:
        donnees = json.load(f)
    clef = TABLES[table]
    liste = donnees if clef is None else donnees.setdefault(clef, [])
    if not isinstance(liste, list):
        raise SystemExit("%s ne porte pas une liste : rien n'a ete ecrit." % p)

    # Un id deja present veut dire que l'autre session l'a pose avant nous, ou
    # qu'on rejoue le meme appel. Dans les deux cas on ne double pas.
    connus = set(x.get("id") for x in liste if isinstance(x, dict))
    poses = []
    for e in enregistrements:
        eid = e.get("id") if isinstance(e, dict) else None
        if eid and eid in connus:
            print("deja present, ignore : %s" % eid)
            continue
        liste.append(e)
        connus.add(eid)
        poses.append(eid or "(sans id)")
    if not poses:
        return []
    ecrire_atomique(p, donnees)
    # --- et elle finit la -------------------------------------------------
    return poses


def main(argv):
    if not argv:
        raise SystemExit(__doc__ or "usage : ajouter.py <table> '<json>' [...]")
    table = argv[0]
    reste = argv[1:]
    joueur = None
    if "--joueur" in reste:
        i = reste.index("--joueur")
        joueur = reste[i + 1]
        reste = reste[:i] + reste[i + 2:]
    enregistrements = []
    if reste and reste[0] == "--fichier":
        for p in reste[1:]:
            with io.open(p, encoding="utf-8") as f:
                d = json.load(f)
            enregistrements.extend(d if isinstance(d, list) else [d])
    else:
        for brut in reste:
            d = json.loads(brut)
            enregistrements.extend(d if isinstance(d, list) else [d])
    if not enregistrements:
        raise SystemExit("rien a ajouter")
    poses = ajouter(table, enregistrements, joueur)
    print("%s : %d ajoute(s) — %s" % (table, len(poses), ", ".join(poses)) if poses
          else "%s : rien de nouveau" % table)


if __name__ == "__main__":
    main(sys.argv[1:])
