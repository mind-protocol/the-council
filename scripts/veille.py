# Le detecteur de fumee : qu'est-ce qui a bouge dans etat/ depuis mon dernier tour ?
#
# Usage :
#     python scripts/veille.py rhaenyra          -> ce qui a change depuis mon
#                                                   dernier passage, puis rearme
#     python scripts/veille.py rhaenyra --voir   -> regarde sans rearmer
#
# POURQUOI. A deux MJ, l'ecriture du monde est optimiste : on edite chacun de son
# cote et l'on rattrape apres coup. Mais « rattraper si necessaire » ne se
# declenche que si je M'APERCOIS qu'il y a eu quelque chose. Sans signal, ma
# memoire de conversation reste sur un etat que l'autre session a modifie sous
# mes pieds, et je continue de jouer un monde qui n'existe plus.
#
# Ce script ne bloque rien et n'arbitre rien — c'est une alarme, pas une serrure.
# Il dit « personnages.json et intentions.json ont bouge » ; a moi de les relire
# avant d'ecrire quoi que ce soit. Premier geste du tour, avec le rearmement du
# guetteur.
import hashlib, io, json, os, sys

racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
etat = os.path.join(racine, "etat")
veilles = os.path.join(etat, "veille")

# flux.jsonl est append-only et bouge a chaque item : il sonnerait en continu
# sans rien apprendre a personne. L'inbox a deja son guetteur.
IGNORE = {"flux.jsonl", "veille", "inbox", "staging", "joueurs.json"}


def empreintes():
    """sha1 de chaque table — l'horodatage ment sur les copies et les touch."""
    out = {}
    for nom in sorted(os.listdir(etat)):
        if nom in IGNORE or not nom.endswith(".json"):
            continue
        p = os.path.join(etat, nom)
        if not os.path.isfile(p):
            continue
        with io.open(p, "rb") as f:
            out[nom] = hashlib.sha1(f.read()).hexdigest()
    # Les croyances par joueur comptent aussi : c'est la que deux sessions
    # ecrivent le plus, meme si elles ne s'y marchent pas dessus.
    d = os.path.join(etat, "joueurs")
    if os.path.isdir(d):
        for j in sorted(os.listdir(d)):
            dj = os.path.join(d, j)
            if not os.path.isdir(dj):
                continue
            for nom in sorted(os.listdir(dj)):
                if not nom.endswith(".json"):
                    continue
                with io.open(os.path.join(dj, nom), "rb") as f:
                    out["joueurs/%s/%s" % (j, nom)] = hashlib.sha1(f.read()).hexdigest()
    return out


def main(argv):
    if not argv:
        raise SystemExit("usage : veille.py <nom-de-session> [--voir]")
    session = argv[0]
    rearmer = "--voir" not in argv
    os.makedirs(veilles, exist_ok=True)
    p = os.path.join(veilles, session + ".json")

    maintenant = empreintes()
    avant = None
    if os.path.exists(p):
        try:
            with io.open(p, encoding="utf-8") as f:
                avant = json.load(f)
        except Exception:
            avant = None

    if avant is None:
        if rearmer:
            with io.open(p, "w", encoding="utf-8") as f:
                json.dump(maintenant, f, ensure_ascii=False, indent=1)
        print("veille armee pour « %s » — %d tables suivies. Rien a signaler "
              "au premier passage." % (session, len(maintenant)))
        return

    changees = [n for n, h in maintenant.items() if avant.get(n) != h]
    disparues = [n for n in avant if n not in maintenant]
    if rearmer:
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump(maintenant, f, ensure_ascii=False, indent=1)

    if not changees and not disparues:
        print("RIEN N'A BOUGE depuis votre dernier tour. Votre memoire de l'etat "
              "est encore juste.")
        return
    print("A BOUGE depuis votre dernier tour — RELISEZ ces tables avant d'ecrire :")
    for n in changees:
        print("  " + n)
    for n in disparues:
        print("  " + n + "  (disparue)")


if __name__ == "__main__":
    main(sys.argv[1:])
