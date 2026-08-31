# -*- coding: utf-8 -*-
"""CENS — compter ce qu'un dossier de cahiers contient, et REFUSER qu'il en
contienne moins apres qu'une main y soit passee.

POURQUOI. Le 9e jour de la 4e lune, une passe de format a traverse les onze
volumes de `chambres/mj/books/`. Elle a proprement ajoute l'Ouverture en huit
champs et les Affaires liees a tous ; elle a vide les tables Etats cibles,
Verrous et Clefs de SEPT d'entre eux, jusqu'au squelette. Personne ne l'a vu :
ni pendant, ni le lendemain. Les fichiers sont restes valides, les tables ont
garde leurs titres, les lignes ont garde leur nombre de cellules — et les
cellules etaient vides.

ET AUCUNE DES DEUX COPIES N'A SERVI, PARCE QU'AUCUNE N'A ETE PRISE PAR
QUELQU'UN QUI SAVAIT QU'IL Y AVAIT QUELQUE CHOSE A SAUVER :

  04h16       la conversion vide les cellules des sept volumes ;
  04h31       `rendre_cellules.py` est ecrit pour reparer depuis
              etat/histoire/empreintes.json — a cette minute-la, l'empreinte
              tient encore le texte, c'etait a une commande ;
  04h49m45s   `reconcilier --vraiment` journalise 62 disparitions — il VOIT
              la perte — puis pose l'etat creux par-dessus cette empreinte ;
  04h52       la sauvegarde de main est prise, sur du vide vieux de 36 min.

Le dossier n'etait pas non plus dans git : pas exclu par `.gitignore`, le mot
n'y est pas — simplement neuf et jamais ajoute.

CE QU'ON MESURE ICI, ET POURQUOI CE N'EST PAS CE QU'ON CROIT.

On m'a demande de compter les LIGNES PLEINES. J'ai compte, sur le degat lui-
meme : la table « ⚔️ Actions » de `affaire-le-brouillard.json` porte sept
lignes de seize cellules ; il en reste UNE de pleine par ligne, la colonne
« 👤 Qui », parce que c'est la seule dont l'en-tete n'avait pas change de nom.
Sept lignes sur sept restent donc PLEINES au sens ou une ligne est pleine des
qu'une cellule y tient. Le compte des lignes pleines de cette table est
inchange. La table est vide a 94%.

    ON COMPTE DONC LES CELLULES, PAS LES LIGNES.

Second point, du meme degat : ce volume a GAGNE 41 cellules pleines dans les
deux tables neuves pendant qu'il en perdait 165 dans les quatre anciennes. Un
total par fichier peut donc rester plat, ou monter, sur un fichier eventre. On
compare table par table, jamais en somme.

Troisieme point : la copie doit etre prise par le GARDE, avant, comme premier
geste. Ni la main qui fait la passe, ni la passe qui CONSTATE l'ecart ne
peuvent la prendre : la premiere ne sait pas encore qu'elle casse, la seconde
sait deja qu'il est trop tard. Une copie perimee est pire que pas de copie,
parce qu'elle donne l'illusion d'un recours — d'ou l'ecrasement a chaque
recensement, et la revalidation de la copie contre le releve avant toute
restitution.

USAGE.

    python scripts/plan/cens.py --recenser chambres/mj/books
        compte, ecrit le releve sous etat/cens/, et prend la copie de tous les
        fichiers AVANT que la main y touche. C'est ce qu'on lance en premier.

    python scripts/plan/cens.py --verifier chambres/mj/books
        recompte apres la passe et compare. Sort 0 si rien n'a baisse, 2 si
        une seule table a perdu une seule cellule. Ne modifie rien.

    python scripts/plan/cens.py --verifier chambres/mj/books --restaurer
        remet, depuis la copie du releve, LES SEULS FICHIERS QUI ONT BAISSE.
        Les autres ne sont pas touches : le travail neuf reste.

    python scripts/plan/cens.py --verifier chambres/mj/books --accepter "motif"
        quand la baisse est voulue et assumee. Le motif est ecrit dans le
        releve suivant. Sans motif, pas d'acceptation.

Ne depend d'aucun autre module du plan, exprès : il doit pouvoir tourner sur
un dossier de cahiers de chambre, que `plan/couverture` ne lit pas.
"""
import io
import json
import os
import shutil
import sys
import unicodedata


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CENS = os.path.join(RACINE, "etat", "cens")


# ------------------------------------------------------------------ lecture

def _texte(x):
    if x is None:
        return u""
    if isinstance(x, (dict, list)):
        return json.dumps(x, ensure_ascii=False)
    try:
        return x if isinstance(x, type(u"")) else str(x)
    except Exception:
        return u""


def pleine(cellule):
    """Une cellule est pleine si elle porte autre chose que du blanc.

    Les tirets de remplissage (`—`, `-`, `n/a`) comptent pour VIDES : ce sont
    des trous ecrits a la main, et le jour ou une passe les remplace par du
    vide on n'a rien perdu. Tout le reste compte, meme un seul caractere.
    """
    s = _texte(cellule).replace(u"**", u"").strip()
    s = u" ".join(s.split())
    return s not in (u"", u"-", u"—", u"–", u"n/a", u"N/A", u".", u"·")


def cellules_de(ligne):
    """Une ligne s'ecrit en liste nue ou en {"cellules": [...]}. Les deux."""
    if isinstance(ligne, list):
        return ligne
    if isinstance(ligne, dict):
        c = ligne.get("cellules")
        if isinstance(c, list):
            return c
    return []


def clef_de_table(titre, rang):
    """La clef d'appariement d'une table entre deux releves.

    Sans emoji, sans accents, sans casse : une passe de format qui reecrit
    « 🎯 Etats cibles » en « 🎯 États cibles » ne doit pas faire croire qu'une
    table a disparu et qu'une autre est nee. Le rang sert de dernier recours
    quand deux tables portent le meme nom nu dans un meme volume.
    """
    s = _texte(titre)
    s = u"".join(c for c in s if unicodedata.category(c) != "So" and c != u"️")
    s = unicodedata.normalize("NFD", s)
    s = u"".join(c for c in s if unicodedata.category(c) != "Mn")
    s = u" ".join(s.replace(u"**", u"").split()).lower()
    return s or u"table sans titre #{}".format(rang)


def recenser_livre(livre):
    """Le compte d'un volume, table par table."""
    tables = {}
    vues = {}
    for rang, t in enumerate(livre.get("tables") or []):
        if not isinstance(t, dict):
            continue
        clef = clef_de_table(t.get("titre"), rang)
        if clef in vues:
            vues[clef] += 1
            clef = u"{} #{}".format(clef, vues[clef])
        else:
            vues[clef] = 1
        lignes = t.get("lignes") or []
        n_cell = n_pleines = n_lignes_pleines = 0
        for ligne in lignes:
            cs = cellules_de(ligne)
            n_cell += len(cs)
            p = sum(1 for c in cs if pleine(c))
            n_pleines += p
            if p:
                n_lignes_pleines += 1
        tables[clef] = {
            "titre": _texte(t.get("titre")),
            "rang": rang,
            "colonnes": len(t.get("colonnes") or []),
            "lignes": len(lignes),
            "lignes_pleines": n_lignes_pleines,
            "cellules": n_cell,
            "cellules_pleines": n_pleines,
        }
    return {
        "titre": _texte(livre.get("titre")),
        "tables": tables,
        "cellules_pleines": sum(x["cellules_pleines"] for x in tables.values()),
    }


def fichiers_de(dossier):
    if not os.path.isdir(dossier):
        sys.exit(u"Aucun dossier : {}".format(dossier))
    return sorted(n for n in os.listdir(dossier)
                  if n.endswith(".json") and not n.startswith("_")
                  and os.path.isfile(os.path.join(dossier, n)))


def recenser_dossier(dossier):
    livres, illisibles = {}, {}
    for nom in fichiers_de(dossier):
        chemin = os.path.join(dossier, nom)
        try:
            with io.open(chemin, encoding="utf-8") as f:
                livre = json.load(f)
        except Exception as mal:
            illisibles[nom] = u"{}".format(mal)
            continue
        if not isinstance(livre, dict):
            illisibles[nom] = u"la racine n'est pas un objet"
            continue
        livres[nom] = recenser_livre(livre)
    return livres, illisibles


# ------------------------------------------------------------------ releve

def empreinte(dossier):
    rel = os.path.relpath(os.path.abspath(dossier), RACINE)
    return rel.replace(os.sep, "-").replace("/", "-").strip("-.") or "racine"


def chemin_releve(dossier):
    return os.path.join(CENS, empreinte(dossier) + ".json")


def chemin_copie(dossier):
    return os.path.join(CENS, empreinte(dossier) + "-copie")


def ecrire_releve(dossier, livres, illisibles, motif=None):
    import datetime
    if not os.path.isdir(CENS):
        os.makedirs(CENS)
    releve = {
        "dossier": os.path.relpath(os.path.abspath(dossier), RACINE),
        "pris_le": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "livres": livres,
        "illisibles": illisibles,
    }
    if motif:
        releve["baisse_acceptee"] = motif
    with io.open(chemin_releve(dossier), "w", encoding="utf-8") as f:
        f.write(_texte(json.dumps(releve, ensure_ascii=False, indent=1)))
    return releve


def lire_releve(dossier):
    p = chemin_releve(dossier)
    if not os.path.isfile(p):
        return None
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def prendre_copie(dossier):
    """LA COPIE SE PREND ICI, AVANT. C'est tout l'objet de ce script.

    On efface la copie precedente : une copie ancienne d'un dossier deja
    corrompu vaut moins que rien, elle donne l'illusion d'un recours.
    """
    cible = chemin_copie(dossier)
    if os.path.isdir(cible):
        shutil.rmtree(cible)
    os.makedirs(cible)
    n = 0
    for nom in fichiers_de(dossier):
        shutil.copy2(os.path.join(dossier, nom), os.path.join(cible, nom))
        n += 1
    return cible, n


# ------------------------------------------------------------- comparaison

def comparer(avant, apres):
    """Les ecarts, table par table. Une baisse d'une seule cellule compte.

    Rend (baisses, disparus, gains) : `baisses` porte les tables qui ont perdu
    des cellules pleines, `disparus` les volumes qui ne sont plus la du tout.
    """
    baisses, disparus, gains = [], [], []
    for nom, av in sorted(avant.items()):
        ap = apres.get(nom)
        if ap is None:
            disparus.append((nom, av["cellules_pleines"]))
            continue
        for clef, ta in sorted(av["tables"].items()):
            tb = ap["tables"].get(clef)
            if tb is None:
                baisses.append({
                    "livre": nom, "table": ta["titre"], "clef": clef,
                    "avant": ta["cellules_pleines"], "apres": 0,
                    "lignes_avant": ta["lignes_pleines"], "lignes_apres": 0,
                    "note": u"table disparue du volume",
                })
                continue
            if tb["cellules_pleines"] < ta["cellules_pleines"]:
                note = u""
                if tb["cellules_pleines"] == 0 and ta["cellules_pleines"]:
                    note = u"VIDEE — plus une seule cellule"
                elif tb["lignes_pleines"] >= ta["lignes_pleines"]:
                    note = (u"le compte des LIGNES pleines n'a pas bouge "
                            u"({}) — seul le compte des cellules le voit"
                            .format(tb["lignes_pleines"]))
                baisses.append({
                    "livre": nom, "table": tb["titre"], "clef": clef,
                    "avant": ta["cellules_pleines"],
                    "apres": tb["cellules_pleines"],
                    "lignes_avant": ta["lignes_pleines"],
                    "lignes_apres": tb["lignes_pleines"],
                    "note": note,
                })
            elif tb["cellules_pleines"] > ta["cellules_pleines"]:
                gains.append((nom, tb["titre"],
                              tb["cellules_pleines"] - ta["cellules_pleines"]))
    return baisses, disparus, gains


# -------------------------------------------------------------------- sortie

def _sortie_large():
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                      errors="replace")
    except Exception:
        pass


def dire_releve(dossier, livres, illisibles, copie=None, n_copies=0):
    print(u"CENS DE {}".format(dossier))
    total = 0
    for nom, l in sorted(livres.items()):
        total += l["cellules_pleines"]
        print(u"  {:<48} {:>5} cellules pleines, {} tables".format(
            nom[:48], l["cellules_pleines"], len(l["tables"])))
        for clef, t in sorted(l["tables"].items(), key=lambda kv: kv[1]["rang"]):
            marque = u"   <- VIDE" if t["cellules_pleines"] == 0 and t["cellules"] else u""
            print(u"        {:<38} {:>4}/{:<4} cellules   {} lignes{}".format(
                (t["titre"] or clef)[:38], t["cellules_pleines"],
                t["cellules"], t["lignes"], marque))
    print(u"  ---")
    print(u"  {} volumes, {} cellules pleines en tout".format(len(livres), total))
    for nom, mal in sorted(illisibles.items()):
        print(u"  ILLISIBLE {} : {}".format(nom, mal))
    if copie:
        print(u"  copie de {} fichiers prise AVANT toute passe : {}".format(
            n_copies, os.path.relpath(copie, RACINE)))


def dire_ecarts(baisses, disparus, gains):
    if disparus:
        print(u"VOLUMES DISPARUS :")
        for nom, n in disparus:
            print(u"  {} — {} cellules pleines perdues avec lui".format(nom, n))
    if baisses:
        print(u"TABLES QUI ONT PERDU DES CELLULES :")
        perdu = 0
        for b in baisses:
            perdu += b["avant"] - b["apres"]
            print(u"  {} / {}".format(b["livre"], b["table"]))
            print(u"      {} -> {} cellules pleines  (-{})  ·  lignes pleines "
                  u"{} -> {}".format(b["avant"], b["apres"],
                                     b["avant"] - b["apres"],
                                     b["lignes_avant"], b["lignes_apres"]))
            if b["note"]:
                print(u"      {}".format(b["note"]))
        print(u"  ---")
        print(u"  {} cellules pleines perdues sur {} tables".format(
            perdu, len(baisses)))
    if gains:
        print(u"CE QUI A GAGNE (pour memoire — ne compense rien) :")
        for nom, titre, n in gains[:12]:
            print(u"  {} / {}  +{}".format(nom, titre[:40], n))


# ----------------------------------------------------------------------- cli

def main(argv):
    _sortie_large()
    args = list(argv[1:])

    def opt(nom, avec_valeur=False):
        if nom not in args:
            return None if avec_valeur else False
        i = args.index(nom)
        args.pop(i)
        if not avec_valeur:
            return True
        return args.pop(i) if i < len(args) else None

    restaurer = opt("--restaurer")
    motif = opt("--accepter", True)
    mode = None
    for m in ("--recenser", "--verifier"):
        v = opt(m, True)
        if v is not None:
            mode, dossier = m, v
    if mode is None:
        print(__doc__)
        return 1
    if not os.path.isabs(dossier):
        dossier = os.path.join(RACINE, dossier)

    livres, illisibles = recenser_dossier(dossier)

    if mode == "--recenser":
        copie, n = prendre_copie(dossier)
        ecrire_releve(dossier, livres, illisibles, motif)
        dire_releve(dossier, livres, illisibles, copie, n)
        print(u"")
        print(u"  Fais ta passe. Puis : python scripts/plan/cens.py "
              u"--verifier {}".format(os.path.relpath(dossier, RACINE)))
        return 0

    ancien = lire_releve(dossier)
    if ancien is None:
        print(u"AUCUN RELEVE PREALABLE pour {}.".format(dossier))
        print(u"On ne peut pas dire si quelque chose a baisse : il n'y a rien")
        print(u"a quoi comparer. Lance --recenser AVANT la passe, pas apres.")
        dire_releve(dossier, livres, illisibles)
        return 1

    baisses, disparus, gains = comparer(ancien.get("livres") or {}, livres)
    print(u"CENS — {} (releve du {})".format(dossier, ancien.get("pris_le")))
    print(u"")
    dire_ecarts(baisses, disparus, gains)

    if not baisses and not disparus:
        print(u"RIEN N'A BAISSE. {} volumes, {} cellules pleines.".format(
            len(livres), sum(l["cellules_pleines"] for l in livres.values())))
        ecrire_releve(dossier, livres, illisibles)
        prendre_copie(dossier)
        print(u"  Le releve et la copie sont repris sur cet etat.")
        return 0

    if motif:
        print(u"")
        print(u"BAISSE ACCEPTEE : {}".format(motif))
        ecrire_releve(dossier, livres, illisibles, motif)
        prendre_copie(dossier)
        return 0

    print(u"")
    print(u"REFUSE. Une passe de format n'a pas le droit de faire baisser le")
    print(u"compte des cellules pleines d'une table. La copie prise avant la")
    print(u"passe est intacte : {}".format(
        os.path.relpath(chemin_copie(dossier), RACINE)))
    if restaurer:
        # LA COPIE SE VERIFIE AVANT DE RENDRE. C'est la seule voie de ce
        # script qui ecrase du travail vivant : elle ne s'ouvre que si la
        # copie porte EXACTEMENT le compte que le releve lui attribue. Une
        # copie prise apres un degat — le cas meme d'ou vient ce script — ne
        # doit pas pouvoir se reverser par-dessus autre chose.
        cible = chemin_copie(dossier)
        copies, _ = recenser_dossier(cible) if os.path.isdir(cible) else ({}, {})
        touches = sorted(set(b["livre"] for b in baisses) |
                         set(n for n, _ in disparus))
        rendus = 0
        for nom in touches:
            src = os.path.join(cible, nom)
            attendu = (ancien.get("livres") or {}).get(nom)
            if not os.path.isfile(src) or nom not in copies or attendu is None:
                print(u"  PAS DE COPIE utilisable pour {} — rien a rendre, "
                      u"et c'est perdu si personne ne l'a ailleurs."
                      .format(nom))
                continue
            ecarts = [c for c, t in attendu["tables"].items()
                      if (copies[nom]["tables"].get(c) or {}).get(
                          "cellules_pleines") != t["cellules_pleines"]]
            if ecarts:
                print(u"  REFUSE de rendre {} : la copie ne porte pas le compte"
                      u" du releve".format(nom))
                print(u"    ({} table(s) en desaccord — cette copie a ete prise"
                      u" apres un degat)".format(len(ecarts)))
                continue
            shutil.copy2(src, os.path.join(dossier, nom))
            rendus += 1
        print(u"  {} volume(s) restaure(s) ; les autres n'ont pas ete "
              u"touches.".format(rendus))
    else:
        print(u"  Pour rendre les seuls volumes qui ont baisse :")
        print(u"    python scripts/plan/cens.py --verifier {} --restaurer"
              .format(os.path.relpath(dossier, RACINE)))
        print(u"  Si la baisse est voulue, dis pourquoi :")
        print(u"    ... --accepter \"le motif\"")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
