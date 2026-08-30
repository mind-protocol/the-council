# -*- coding: utf-8 -*-
"""PASSER — un livre change de main, ou se pose sur une table.

    python scripts/passer.py                             # ce que chacun porte
    python scripts/passer.py carnet-marlo                # où est ce volume
    python scripts/passer.py carnet-marlo --a rhaenyra --vraiment
    python scripts/passer.py leve-de-la-gadoue --pose table-peinte --vraiment
    python scripts/passer.py carnet-marlo --a rhaenyra --ouvert --vraiment

POURQUOI UN SCRIPT POUR DEUX CHAMPS. Montrer, présenter et passer sont trois
gestes différents, et le troisième est le seul qui soit IRRÉVERSIBLE sans un
autre geste : l'objet n'est plus chez celui qui l'avait. Tout le reste en
découle sans une ligne d'affichage — `books.js` sait déjà qu'un carnet suit son
porteur et qu'un registre reste où on l'a posé. Passer un livre, c'est donc
réécrire une adresse, et c'est tout.

Ce qu'on gagne à le faire ici plutôt qu'à la main :
  - les deux adresses s'excluent (`acteur_id` OU `salle_id`, jamais les deux) ;
  - l'acte s'écrit dans la foulée, avec ses témoins — un volume qui change de
    main devant six personnes est un fait, et six personnes s'en souviendront ;
  - `prive` ne suit pas bêtement l'objet : un carnet qu'on tenait caché reste
    caché chez le nouveau porteur, et le script le DIT au lieu de le taire.

LE BROUILLARD. Passer donne l'objet, pas la mémoire de ce qu'il contient :
`books.js` le montrera désormais sous l'onglet du nouveau porteur, et l'ancien
ne l'y trouvera plus. C'est voulu. Si l'on veut qu'un homme se souvienne de ce
qu'il a lu avant de le rendre, ça s'écrit dans sa tête, pas dans le volume.
"""
import io, json, os, sys, tempfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Deux etages de plus qu'a la racine : scripts/plan/ (voir scripts/CLAUDE.md).
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOOKS = os.path.join(RACINE, "etat", "books.json")
from etat.expose import ajouter  # noqa: E402  — on réutilise son écriture atomique et sa fenêtre étroite
import bibliotheque  # noqa: E402


def charger(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def date_du_monde():
    try:
        return charger(os.path.join(RACINE, "etat", "monde.json")).get("date")
    except Exception:
        return None


def horloge(pid):
    """L'heure de CELUI qui donne — pas celle du monde.

    `monde.date` n'est que le minimum des fronts (voir serveur.js) : dater un
    acte avec elle le placerait dans le passé de la scène où il se produit.
    """
    try:
        h = charger(os.path.join(RACINE, "etat", "horloges.json"))
        if pid and h.get(pid):
            return h[pid]
    except Exception:
        pass
    return date_du_monde()


def nom_de(pid):
    if not pid:
        return None
    try:
        gens = charger(os.path.join(RACINE, "etat", "personnages.json"))
        liste = gens if isinstance(gens, list) else gens.get("personnages", [])
        for p in liste:
            if p.get("id") == pid:
                return p.get("nom") or pid
    except Exception:
        pass
    return pid.replace("-", " ")


def ou_est(b):
    if b.get("acteur_id"):
        return "porté par %s%s" % (nom_de(b["acteur_id"]),
                                   " (tenu pour lui)" if b.get("prive") else "")
    if b.get("salle_id"):
        return "posé en %s%s" % (b["salle_id"],
                                 ", à " + b["lieu_id"] if b.get("lieu_id") else "")
    return "nulle part — ce volume n'a pas d'adresse"


def etagere(books, filtre=None):
    for b in books:
        if filtre and b.get("id") != filtre:
            continue
        print("  %-34s %s" % (b.get("id"), ou_est(b)))
        print("  %-34s « %s »" % ("", b.get("titre") or "sans titre"))


def main(argv):
    books = bibliotheque.charger(os.path.join(RACINE, "etat"))
    if not isinstance(books, list):
        raise SystemExit("etat/books.json ne porte pas une liste.")

    if not argv:
        etagere(books)
        print("\nPour en passer un : passer.py <id> --a <acteur> --vraiment")
        return

    livre_id = argv[0]
    reste = argv[1:]

    def prendre(drapeau):
        if drapeau in reste:
            i = reste.index(drapeau)
            v = reste[i + 1] if i + 1 < len(reste) else None
            del reste[i:i + 2]
            return v
        return None

    vers = prendre("--a")
    salle = prendre("--pose")
    lieu = prendre("--lieu")
    quoi = prendre("--acte")
    temoins = prendre("--temoins")
    vraiment = "--vraiment" in reste
    ouvert = "--ouvert" in reste
    prive = "--prive" in reste

    livre = next((b for b in books if b.get("id") == livre_id), None)
    if not livre:
        print("Aucun livre « %s ». L'étagère :" % livre_id)
        etagere(books)
        raise SystemExit(1)

    if not vers and not salle:
        etagere(books, livre_id)
        return

    if vers and salle:
        raise SystemExit("--a ou --pose, jamais les deux : un livre est dans une "
                         "main ou sur une table.")

    avant = ou_est(livre)
    donneur = livre.get("acteur_id")

    # Ce qui change. Les deux adresses s'excluent : on efface l'autre, sans quoi
    # un carnet passé de main resterait « aussi » sur la table où il était.
    neuf = dict(livre)
    if vers:
        neuf["acteur_id"] = vers
        neuf.pop("salle_id", None)
        neuf.pop("lieu_id", None)
    else:
        neuf["salle_id"] = salle
        if lieu:
            neuf["lieu_id"] = lieu
        elif not neuf.get("lieu_id"):
            neuf["lieu_id"] = "peyredragon"
        neuf.pop("acteur_id", None)
        # Un volume posé sur une table n'est plus un secret de personne : le
        # garder `prive` le rendrait invisible à tout le monde, y compris à
        # celui qui vient de le poser. C'est le seul cas où l'on tranche seul.
        if neuf.pop("prive", None):
            print("  · il était tenu caché : posé sur une table, il ne l'est plus.")
    if ouvert:
        neuf.pop("prive", None)
    if prive:
        neuf["prive"] = True

    apres = ou_est(neuf)
    print("« %s »" % (livre.get("titre") or livre_id))
    print("  avant : %s" % avant)
    print("  après : %s" % apres)
    if neuf.get("prive") and vers and vers != donneur:
        print("  · %s le garde pour lui (--ouvert pour qu'il puisse être lu à vue)."
              % nom_de(vers))

    if not vraiment:
        print("\nRien n'a été écrit. Ajoutez --vraiment.")
        return

    # --- la fenêtre étroite : relire, muter, réécrire dans la même seconde ---
    session_livres = bibliotheque.ouvrir(os.path.join(RACINE, "etat"))
    frais = session_livres.livres
    cible = next((b for b in frais if b.get("id") == livre_id), None)
    if cible is None:
        raise SystemExit("le livre a disparu de books.json entre-temps : rien écrit.")
    for clef in ("acteur_id", "salle_id", "lieu_id", "prive"):
        cible.pop(clef, None)
        if clef in neuf:
            cible[clef] = neuf[clef]
    # L'étagère se range du plus frais au plus ancien : un volume qui vient de
    # changer de main est ce qu'il y a de plus frais sur la table.
    quand_maj = horloge(donneur or vers)
    if quand_maj:
        cible["date_maj"] = dict(quand_maj)
    session_livres.sauver()
    print("\nbooks.json : écrit.")

    # L'acte. Un volume qui change de main devant témoins est un fait, et c'est
    # par là qu'il devient réclamable plus tard — « vous me l'avez donné ».
    acteur = donneur or vers
    quand = horloge(acteur)
    if vers:
        defaut = "%s remet « %s » à %s." % (
            nom_de(donneur) if donneur else "On", livre.get("titre") or livre_id,
            nom_de(vers))
    else:
        defaut = "« %s » est posé en %s." % (livre.get("titre") or livre_id, salle)
    acte = {
        "id": "passe-%s-%s%s" % (
            livre_id,
            (vers or salle),
            "-%d" % quand["minute"] if isinstance(quand, dict) and "minute" in quand else ""),
        "date": quand,
        "acteur_id": acteur,
        "lieu_id": livre.get("lieu_id") or "peyredragon",
        "quoi": quoi or defaut,
        "temoins": [t for t in (temoins or "").split(",") if t],
        "connu_de": [x for x in {donneur, vers} if x],
    }
    poses = ajouter.ajouter("actes", [acte])
    print("actes.json : %s" % (", ".join(poses) if poses else "rien de nouveau"))


