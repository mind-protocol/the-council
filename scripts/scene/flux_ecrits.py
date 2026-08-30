# -*- coding: utf-8 -*-
# FLUX_ECRITS — deux avis du pousseur de flux : les renvois poses dans la
# phrase (le lien [texte](adresse) doit resoudre), et l'item `ecrit` (ce qu'on
# ANNONCE doit etre ECRIT dans le livre annonce). Des defs pures, sans etat de
# la poussee en cours. Matiere de scripts/append_flux.py (lot 2), deplacee
# telle quelle ; flux.py, le script, importe d'ici.
import io
import json
import os
import re
import sys
import unicodedata

from etat.expose import tables  # LA PORTE de etat/
from scene.flux_scribe import racine, bibliotheque  # un seul importeur du registre (lot 3 : la porte de plan/)

# ---- Les renvois poses dans la phrase -------------------------------------
# `[les neufs](44022)` ouvre l'affaire a la ligne ; `[le Sanglier](hallis-roon)`
# pose la question au narrateur. Une cible que l'etat ne connait pas ne
# s'allume pas a l'ecran : elle reste du texte nu, sans que personne le sache.
# Le script ne refuse rien — il DIT ce qui ne menera nulle part, au moment ou
# l'on pousse, pendant qu'il est encore temps de corriger le numero.
RENVOI = re.compile(r"\[([^\]\[<>\n]{1,80})\]\(([A-Za-z0-9][A-Za-z0-9_-]{0,60})\)")


def _adresses_connues():
    numeros, ids = {}, set()
    try:
        livres = bibliotheque.charger(tables.ETAT)
        for v in livres:
            tables = v.get("tables") or []
            if v.get("colonnes"):
                tables = tables + [{"colonnes": v.get("colonnes"),
                                    "lignes": v.get("lignes") or []}]
            for t in tables:
                cols = t.get("colonnes") or []
                if not cols or "N°" not in str(cols[0]):
                    continue
                for l in (t.get("lignes") or []):
                    cells = l.get("cellules") or []
                    c = cells[0] if cells else None
                    m = re.match(r"\s*(?:\*\*)?\s*(\d{4,6})\b", str(c or ""))
                    if not m:
                        continue
                    # l'intitule de la ligne, pour proposer la forme toute faite
                    lib = str(cells[1] if len(cells) > 1 else "")
                    lib = re.sub(r"^\s*[^\w\s(]+\s*", "", lib).replace("**", "")
                    numeros[m.group(1)] = lib.strip()
    except Exception:
        pass
    for f_ in ("personnages.json", "lieux.json", "maisons.json"):
        try:
            with io.open(os.path.join(racine, "etat", f_), encoding="utf-8") as f:
                for e in json.load(f):
                    if e.get("id"):
                        ids.add(e["id"])
        except Exception:
            pass
    ids.update(["caraxes", "vhagar", "meleys", "syrax", "vermax", "arrax",
                "revefeu", "sunfyre", "gosier"])
    return numeros, ids


# Ce qui se DIT dans la salle, et rien d'autre : un numero cite dans une
# replique doit mener quelque part ; le meme numero dans une cle technique
# (`demande.id`, `ref`) ne regarde pas le joueur.
DITS = ("texte", "titre", "quoi", "detail", "sous_titre")


def _ce_qui_se_dit(it):
    bouts = []

    def marche(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, (dict, list)):
                    marche(v)
                elif k in DITS and isinstance(v, str):
                    bouts.append(v)
        elif isinstance(x, list):
            for v in x:
                marche(v)
    marche(it)
    return "\n".join(bouts)


def avis_renvois(items):
    trouves, dits = [], []
    for it in items:
        dit = _ce_qui_se_dit(it)
        dits.append((it, dit))
        poses = RENVOI.findall(json.dumps(it, ensure_ascii=False))
        if poses:
            trouves.append((it, poses))
    numeros, ids = _adresses_connues()

    # LE NUMERO CITE NU — le defaut qu'on veut voir disparaitre. Personne
    # n'ecrira le lien parce que la doctrine le demande : on le rappelle a
    # l'instant ou l'on pousse, avec la forme toute faite a recopier.
    signales = set()
    for it, dit in dits:
        # ce qui est deja pose en lien ne se rappelle pas deux fois
        nu = RENVOI.sub(" ", dit)
        for n in re.findall(r"(?<!\d)(\d{4,6})(?!\d)", nu):
            if n in signales or n not in numeros:
                continue
            signales.add(n)
            lib = numeros[n] or "…"
            sys.stderr.write(
                "AVIS : le n° %s est cite NU dans « %s ».\n"
                "  Le joueur ne peut ni savoir de quoi il s'agit, ni aller le"
                " lire.\n"
                "  Ecrivez plutot : [%s](%s)\n"
                "  — le libelle est ce que la personne DIT, pas le numero.\n"
                % (n, it.get("type", "?"), lib, n))

    for it, poses in trouves:
        for label, cible in poses:
            if re.match(r"^\d{4,6}$", cible):
                if cible not in numeros:   # numeros : n° → intitule de la ligne
                    sys.stderr.write(
                        "AVIS : le renvoi « %s » pointe le n° %s, qui n'existe"
                        " dans aucune affaire.\n"
                        "  Il restera du TEXTE NU a l'ecran. Verifiez le"
                        " numero dans etat/books.json.\n" % (label, cible))
            elif cible not in ids:
                sys.stderr.write(
                    "AVIS : le renvoi « %s » pointe « %s », qui n'a de fiche"
                    " ni dans personnages, ni dans lieux, ni dans maisons.\n"
                    "  Il restera du TEXTE NU a l'ecran.\n" % (label, cible))
        # Deux renvois par piece, pas davantage : une replique dont chaque
        # groupe nominal est cliquable redevient un menu — exactement ce que
        # le champ libre permanent existe pour eviter.
        if len(poses) > 2:
            sys.stderr.write(
                "AVIS : %d renvois dans une seule piece (%s).\n"
                "  Deux au plus, comme les appuis en gras : au-dela, la phrase"
                " se lit comme un menu.\n"
                % (len(poses), it.get("type", "?")))


def sans_accents_simple(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


# ---- L'item `ecrit` : ce qu'on ANNONCE doit etre ECRIT ---------------------
# `ecrit` dit au joueur « voila ce qui vient d'etre porte au registre », et
# chaque entree s'ouvre d'un clic sur le volume. CLAUDE.md pose la regle dure :
# on l'ecrit APRES avoir ecrit pour de bon dans books.json, jamais avant — une
# entree qui ne s'ouvre pas est pire que pas d'entree.
#
# LE 1er DE LA 4e LUNE, la regle a saute, et par un homme qui travaillait bien.
# Le Sanglier a pousse un `ecrit` annoncant qu'il venait de requalifier la piece
# 23002 — alors que son changement dormait encore, NON VERSE, dans
# etat/rapports/le-sanglier.json (clef `cahier2`). Le lien n'etait pas mort : le
# volume s'ouvrait, et la ligne montrait l'ANCIENNE valeur. Le joueur cliquait,
# lisait le passe, et croyait lire le present. Ce n'est pas une faute d'homme,
# c'est un defaut d'outil : rien ne l'en empechait, rien ne l'a averti.
#
# Trois verifications, de la plus benigne a la seule qui compte :
#   1. le livre nomme existe (meme garde que `montre`, voir extrait_du_livre) ;
#   2. une ADRESSE citee dans la famille de numeros du volume existe bien chez
#      lui — 23999 annonce dans un volume qui va de 23000 a 23300 ne s'ouvrira
#      sur rien. On ne verifie que ca, parce que le reste d'une entree (`titre`,
#      `quoi`) est du texte libre : un chiffre y est aussi souvent un compte
#      d'hommes qu'une adresse, et l'eprouver produirait du bruit, pas un garde ;
#   3. AUCUN changement ne dort, non verse, pour ce volume — le cas du Sanglier,
#      et le seul que rien ne signalait.
#
# ON AVERTIT, ON NE REFUSE PAS. Le tunnel refuse deja au double de ses seuils, et
# empiler les refus rendrait l'outil impraticable pour des acteurs qui viennent
# d'apprendre a s'en servir ; surtout, un refus ici bloquerait aussi l'entree
# honnete qui parle d'une AUTRE ligne du meme volume, et le remede
# (`verser_cahier.py --vraiment`) verse TOUS les rapports d'un coup — ce n'est
# pas un geste qu'on arrache a quelqu'un au milieu d'une scene. Mais un avis
# qu'on ne lit pas n'est pas un avis : celui-la est encadre et se voit.
def _volumes():
    try:
        return {v.get("id"): v for v in bibliotheque.charger(
                os.path.join(racine, "etat"))
                if isinstance(v, dict) and v.get("id")}
    except Exception:
        return {}


def _tables_du_volume(v):
    """Les tableaux du volume — `tables[]`, ou la table unique de la racine."""
    ts = [t for t in (v.get("tables") or []) if isinstance(t, dict)]
    if v.get("colonnes"):
        ts.append({"titre": v.get("titre"), "colonnes": v.get("colonnes"),
                   "lignes": v.get("lignes") or []})
    return ts


def _numeros_du_volume(v):
    """Les numeros de piece que CE volume porte, en premiere cellule.

    Meme lecture que `_adresses_connues`, restreinte a un volume : ce sont les
    adresses vers lesquelles une entree d'`ecrit` peut legitimement pointer.
    """
    n = set()
    for t in _tables_du_volume(v):
        cols = t.get("colonnes") or []
        if not cols or "N°" not in str(cols[0]):
            continue
        for l in (t.get("lignes") or []):
            cel = l.get("cellules") or []
            m = re.match(r"\s*(?:\*\*)?\s*(\d{3,6})\b", str(cel[0] if cel else ""))
            if m:
                n.add(m.group(1))
    return n


def _cahiers_en_attente():
    """Ce qu'un homme a CHANGE aux registres et qui n'est pas encore verse.

    Un rapport porte `_cahier_verse` une fois passe par verser_cahier.py (qui
    l'ecrit lui-meme, pour qu'un cahier ne se verse pas deux fois). Sans cette
    marque, ce que contient `cahier2` n'est qu'une PROPOSITION : books.json
    porte toujours l'ancienne valeur.

    Rend {livre_id: [(qui, entree), ...]}.
    """
    attente = {}
    dossier = os.path.join(racine, "etat", "rapports")
    try:
        noms = sorted(os.listdir(dossier))
    except OSError:
        return attente
    for nom in noms:
        if not nom.endswith(".json"):
            continue
        try:
            with io.open(os.path.join(dossier, nom), encoding="utf-8") as f:
                rap = json.load(f)
        except Exception:
            continue
        if not isinstance(rap, dict) or rap.get("_cahier_verse"):
            continue
        qui = rap.get("qui") or nom[:-5]
        for e in (rap.get("cahier2") or []):
            if isinstance(e, dict) and e.get("livre"):
                attente.setdefault(e["livre"], []).append((qui, e))
    return attente


def avis_ecrits(items):
    ecrits = [it for it in items if it.get("type") == "ecrit"]
    if not ecrits:
        return
    V = _volumes()
    attente = _cahiers_en_attente()
    dejaDit = set()
    for it in ecrits:
        for e in (it.get("entrees") or []):
            if not isinstance(e, dict):
                continue
            lid = e.get("livre")
            titre = str(e.get("titre") or "")
            quoi = str(e.get("quoi") or "")
            if not lid:
                sys.stderr.write(
                    "AVIS : entree d'`ecrit` sans `livre` (« %s ») — elle se lira,\n"
                    "  mais elle n'ouvrira rien. On ne feint pas un lien mort.\n"
                    % titre[:60])
                continue
            v = V.get(lid)
            if v is None:
                sys.stderr.write(
                    "AVIS : aucun livre « %s » — cette entree d'`ecrit` ne menera\n"
                    "  nulle part a l'ecran. Le volume s'ecrit dans etat/books.json\n"
                    "  AVANT qu'on l'annonce au joueur.\n" % lid)
                continue

            # 2. l'adresse citee, quand elle est de la famille du volume
            nums = _numeros_du_volume(v)
            familles = set((len(n), n[:2]) for n in nums)
            for n in re.findall(r"(?<!\d)(\d{3,6})(?!\d)", titre + " " + quoi):
                if (len(n), n[:2]) in familles and n not in nums:
                    soeurs = sorted(x for x in nums
                                    if (len(x), x[:2]) == (len(n), n[:2]))
                    sys.stderr.write(
                        "AVIS : l'entree annonce la piece %s de « %s », qui n'y existe\n"
                        "  pas (le volume porte %s…%s). Le joueur ouvrira le volume\n"
                        "  et ne trouvera pas la ligne annoncee.\n"
                        % (n, lid, soeurs[0], soeurs[-1]))

            # 3. le changement qui dort — la faute du Sanglier
            if lid in attente and lid not in dejaDit:
                dejaDit.add(lid)
                pend = attente[lid]
                # La meme ligne, ou une autre du meme volume ? On le dit, parce
                # que ce n'est pas la meme faute : l'une est un mensonge a
                # l'ecran, l'autre un simple voisinage.
                dit = titre + " " + quoi
                precises = [(q, x) for (q, x) in pend
                            if str(x.get("ligne") or "") and
                            str(x.get("ligne")) in dit]
                barre = "!" * 72
                sys.stderr.write(
                    "\n%s\nATTENTION — VOUS ANNONCEZ UNE ECRITURE QUI N'EST PAS FAITE.\n"
                    "  « %s » porte %d changement(s) proposes et NON VERSES :\n"
                    % (barre, lid, len(pend)))
                for (q, x) in pend[:4]:
                    sys.stderr.write(
                        "    · %s — %s / %s / %s\n"
                        % (q, x.get("table") or "?", x.get("ligne") or "?",
                           x.get("colonne") or "?"))
                if len(pend) > 4:
                    sys.stderr.write("    · … et %d autre(s)\n" % (len(pend) - 4))
                if precises:
                    sys.stderr.write(
                        "  ET C'EST LA LIGNE QUE VOUS ANNONCEZ (%s). books.json porte\n"
                        "  encore l'ANCIENNE valeur : le joueur cliquera votre entree\n"
                        "  et lira le passe en croyant lire le present.\n"
                        % ", ".join(sorted(set(str(x.get("ligne"))
                                               for (_q, x) in precises))))
                else:
                    sys.stderr.write(
                        "  Ce n'est peut-etre pas la ligne que vous annoncez — mais le\n"
                        "  volume que le joueur va ouvrir n'est pas a jour pour autant.\n")
                sys.stderr.write(
                    "  A FAIRE, avant de pousser :\n"
                    "    python scripts/verser_cahier.py --qui %s          (a sec)\n"
                    "    python scripts/verser_cahier.py --qui %s --vraiment\n"
                    "  L'item est ecrit quand meme (le flux est append-only) : versez,\n"
                    "  verifiez le volume, et rectifiez d'une ligne s'il le faut.\n"
                    "%s\n" % (pend[0][0], pend[0][0], barre))


