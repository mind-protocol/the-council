# -*- coding: utf-8 -*-
u"""HISTOIRE — le journal type des affaires : une ligne par evenement.

POURQUOI ICI, ET PAS AILLEURS. `bibliotheque.Session.sauver()` tient
`self._avant` et calcule `touches` : il a le diff complet sous la main et il
le jetait. C'est aussi le SEUL endroit qui voit toutes les plumes qui passent
par la porte — les seize scripts Python et la route serveur d'un coup. On
descend donc le diff d'un cran au lieu d'instrumenter seize appelants.

CE QU'ON N'INVENTE PAS, ET C'EST LA MOITIE DU MODULE. Mesure du 31.8 sur les
51 affaires : la table « 🎯 Etats cibles » n'a AUCUNE colonne d'etat, et
« 🔒 Verrous » n'en a pas davantage — « 🔓 Leve quand » est une CONDITION, pas
un etat. On ne peut donc pas dire qu'un objectif est atteint ni qu'un verrou
est leve : la donnee ne le porte pas. Ce module emet pour eux `posee`,
`retiree`, `modifiee` — rien de plus. Seules les ACTIONS (colonne « ⏳ Etat »)
et les CLEFS (colonne « ⚖️ Decision ») portent un etat qu'on peut suivre.

CE QUI ECHAPPE, ET QU'ON DIT. Les hommes depeches ont `Write` et `Edit` : ils
ecrivent dans `etat/books/*.json` sans passer par la porte. Ces ecritures-la
n'emettent rien. Chaque ligne porte donc `certitude` : « declare » quand
l'evenement est emis au moment de l'ecriture, « constate » quand une passe de
reconciliation l'a deduit apres coup.
"""
import io
import json
import os
import re
import time
import unicodedata

FICHIER = os.path.join("histoire", "affaires.jsonl")

# Les etats d'action, apres decapage. Le vocabulaire du dépôt, tel que
# `plan/normaliser_etats.py` l'a fixe — plus les deux synonymes qu'on lit
# encore dans les volumes (« close » vaut faite, « engagee » vaut en cours).
FAITE = ("faite", "close", "closes", "fait")
EN_COURS = ("en cours", "engagee", "engagée", "encours")
BLOQUEE = ("bloquee", "bloquée")
A_FAIRE = ("a faire", "à faire")
ABANDON = ("abandonnee", "abandonnée")

_GRAS = re.compile(r"\*+")
_QUEUE = re.compile(r"\s+[—–-]\s+.*$", re.S)


def decaper(valeur):
    u"""Un etat lisible, sans le gras markdown ni la prose qui suit.

    30 des 100 « en cours » sont ecrits `**en cours**` : un compteur naif se
    trompe de 30 %. On decape pour COMPARER, jamais pour reecrire le volume —
    la ligne du journal garde aussi la valeur brute.
    """
    t = _GRAS.sub("", str(valeur or "")).strip()
    t = _QUEUE.sub("", t).strip()
    return t.lower()


def famille(etat):
    e = decaper(etat)
    if e in FAITE:
        return "faite"
    if e in EN_COURS:
        return "en cours"
    if e in BLOQUEE:
        return "bloquee"
    if e in A_FAIRE:
        return "a faire"
    if e in ABANDON:
        return "abandonnee"
    return None            # hors vocabulaire : on l'expose, on ne devine pas


def _cellules(ligne):
    if isinstance(ligne, dict):
        return ligne.get("cellules") or []
    return ligne if isinstance(ligne, list) else []


def _colonne(colonnes, *motifs):
    for i, c in enumerate(colonnes or []):
        for m in motifs:
            if m in str(c):
                return i
    return None


def _titre_court(t):
    return (str(t or "").split(u"—")[0]).strip()


def _noyau(t):
    u"""Le coeur d'un titre de table : sans emoji, sans accent, en minuscules.

    LE 129.4.9 A COUTE QUINZE ETATS CIBLES A CE SEUL DETAIL. `_index`
    comparait le titre par EGALITE STRICTE contre `SUIVIES`, dont les quatre
    entrees sont accentuees. Sept volumes de `chambres/mj/books/` portent
    « 🎯 Etats cibles » SANS accent : leur table etait donc invisible au
    journal. Quand une conversion d'en-tetes les a vides, la passe de
    reconciliation a fidelement emis 20 `verrou.retiree`, 15 `clef.retiree`,
    27 `action.retiree` — et ZERO `cible.retiree`. Les quinze etats cibles
    perdus n'ont laisse aucune trace nulle part, non parce qu'ils etaient
    vides, mais parce que personne ne les regardait.

    LA PREUVE EST DISCRIMINANTE, ET ELLE A ETE MESUREE : les 8 seuls
    evenements `cible.*` du journal viennent des 3 volumes accentues
    (appareil-de-reprise, le-saut, chiffre-arrete) et d'eux seuls. Aucun des
    sept autres n'en a jamais emis un.

    ET LE PRIX ETAIT PLUS HAUT QUE LE JOURNAL : `reconcilier.pertes_de()`
    compte les `.retiree` pour decider s'il preserve `empreintes-sans-perte
    .json`. Un vidage qui n'aurait touche QUE les etats cibles non accentues
    rendait donc `pertes = 0`, et le secours se faisait ecraser par le
    desastre — la garde neuve reproduisait exactement la panne qu'elle
    empeche.

    `_colonne` ci-dessus tolerait deja « État » ou « Etat » pour les EN-TETES.
    La moitie de l'invariant etait ecrite depuis le debut ; elle ne l'etait
    pas pour les titres de table.
    """
    s = _titre_court(t)
    s = "".join(c for c in s if c.isalnum() or c.isspace())
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


def _index(volume, nom_table):
    u"""Rend {n° : {champ : valeur}} pour une table du volume, ou {}.

    On apparie sur le NOYAU du titre (voir `_noyau`) : accent et emoji ne
    doivent pas decider si une table existe. La premiere table dont le noyau
    correspond gagne, comme avant.
    """
    vise = _noyau(nom_table)
    for t in volume.get("tables") or []:
        if _noyau(t.get("titre")) != vise:
            continue
        cols = t.get("colonnes") or []
        i_num = 0
        i_tit = 1 if len(cols) > 1 else None
        i_etat = _colonne(cols, u"⏳ État", u"État", u"Etat")
        i_dec = _colonne(cols, u"⚖️ Décision", u"Décision")
        i_fait = _colonne(cols, u"Jour fait")
        out = {}
        for l in t.get("lignes") or []:
            c = _cellules(l)
            if not c:
                continue
            num = _GRAS.sub("", str(c[i_num])).strip()
            if not num:
                continue
            out[num] = {
                "titre": str(c[i_tit]).strip() if i_tit is not None
                         and i_tit < len(c) else "",
                "etat": str(c[i_etat]) if i_etat is not None
                        and i_etat < len(c) else None,
                "decision": str(c[i_dec]) if i_dec is not None
                            and i_dec < len(c) else None,
                "jour_fait": str(c[i_fait]).strip() if i_fait is not None
                             and i_fait < len(c) else "",
                "cellules": [str(x) for x in c],
            }
        return out
    return {}


def _transition(av, ap):
    u"""Le nom de l'evenement pour un changement d'etat d'action.

    On ne rend un mot du vocabulaire que si LES DEUX cotes sont reconnus.
    Sinon `action.etat`, avec le brut : un etat qu'on ne sait pas ranger doit
    se VOIR, c'est ainsi qu'on decouvre les 30 « en cours » en gras.
    """
    fa, fb = famille(av), famille(ap)
    if fa is None or fb is None:
        return "action.etat"
    if fa == fb:
        return None
    if fb == "faite":
        return "action.fermee"
    if fa == "faite":
        return "action.rouverte"
    if fb == "abandonnee":
        return "action.abandonnee"
    if fb == "bloquee":
        return "action.bloquee"
    if fa == "bloquee":
        return "action.debloquee"
    if fb == "en cours":
        return "action.engagee"
    return "action.etat"


# Les tables suivies, et ce qu'on sait dire de chacune. La colonne de droite
# est volontairement pauvre pour les cibles et les verrous : voir l'en-tete.
SUIVIES = [
    (u"⚔️ Actions", "action"),
    (u"🗝️ Clefs", "clef"),
    (u"🎯 États cibles", "cible"),
    (u"🔒 Verrous", "verrou"),
]


def evenements_du_volume(avant, apres):
    u"""Les evenements d'UN volume, entre deux versions. Liste de dicts."""
    ev = []
    a_id = (apres or avant).get("id")
    commun = {"affaire": a_id,
              "chambre": (apres or {}).get("tenu_par")
                         or (avant or {}).get("tenu_par"),
              "boite": (apres or {}).get("boite") or (avant or {}).get("boite"),
              "office": (apres or {}).get("office") or (avant or {}).get("office")}

    if avant is None:
        ev.append(dict(commun, quoi="affaire.ouverte",
                       titre=(apres or {}).get("titre")))
    elif apres is None:
        ev.append(dict(commun, quoi="affaire.close",
                       titre=(avant or {}).get("titre")))
    else:
        # « Les affaires dans leur chambre » : changer de main ou de boite est
        # un evenement au meme titre qu'une action fermee.
        if avant.get("tenu_par") != apres.get("tenu_par"):
            ev.append(dict(commun, quoi="affaire.confiee",
                           avant=avant.get("tenu_par"),
                           apres=apres.get("tenu_par")))
        if avant.get("boite") != apres.get("boite"):
            ev.append(dict(commun, quoi="affaire.rangee",
                           avant=avant.get("boite"), apres=apres.get("boite")))

    for nom_table, genre in SUIVIES:
        ia = _index(avant or {}, nom_table)
        ib = _index(apres or {}, nom_table)
        for num in sorted(set(ia) | set(ib)):
            a, b = ia.get(num), ib.get(num)
            base = dict(commun, ou=num,
                        titre=(b or a or {}).get("titre"))
            # Une action se CREE, une clef ou un verrou se POSE : le mot doit
            # se lire, pas seulement se decliner.
            if a is None:
                ev.append(dict(base, quoi="%s.%s"
                               % (genre, "creee" if genre == "action"
                                  else "posee")))
                continue
            if b is None:
                ev.append(dict(base, quoi="%s.retiree" % genre))
                continue
            if genre == "action":
                if decaper(a["etat"]) != decaper(b["etat"]):
                    nom = _transition(a["etat"], b["etat"])
                    if nom:
                        ev.append(dict(base, quoi=nom,
                                       avant=a["etat"], apres=b["etat"]))
                if not a["jour_fait"] and b["jour_fait"]:
                    ev.append(dict(base, quoi="action.datee",
                                   apres=b["jour_fait"]))
            elif genre == "clef" and a["decision"] != b["decision"]:
                ev.append(dict(base, quoi="clef.decidee",
                               avant=a["decision"], apres=b["decision"]))
            elif a["cellules"] != b["cellules"]:
                # CIBLES ET VERROUS : aucune colonne d'etat, donc aucun
                # « atteinte » ni « leve » possible. On dit ce qu'on sait :
                # la ligne a bouge.
                ev.append(dict(base, quoi="%s.modifiee" % genre))
    return ev


def _qui():
    u"""L'auteur, si le lanceur a bien pose son nom dans l'environnement.

    `LE_CONSEIL_QUI` existait comme convention et n'etait JAMAIS posee — une
    lecture dans tout le depot, zero ecriture. Les lanceurs la posent
    desormais ; a defaut on rend None et la ligne le dira.
    """
    return (os.environ.get("LE_CONSEIL_QUI")
            or os.environ.get("LE_CONSEIL_MJ") or None)


def _monde(etat):
    u"""La date du monde du siege principal, si on la tient. DEUX HORLOGES :
    c'est l'absence de celle-ci sur les billets qui rendait « les X dernieres
    heures de jeu » impossible. On ne refait pas l'erreur."""
    try:
        h = json.load(io.open(os.path.join(etat, "horloges.json"),
                              encoding="utf-8"))
        j = json.load(io.open(os.path.join(etat, "joueurs.json"),
                              encoding="utf-8"))
        js = j.get("joueurs") if isinstance(j, dict) else j
        principal = next((s.get("personnage_id") for s in (js or [])
                          if s.get("role") == "principal"), None)
        return h.get(principal)
    except Exception:
        return None


def journaliser(avants, apres, etat, certitude="declare", outil=None,
                fichier=None, maison="etat"):
    u"""Ecrit les evenements de tous les volumes touches. Rend leur nombre.

    NE LEVE JAMAIS : un journal qui casse une ecriture d'etat serait un
    remede pire que le mal. L'appelant enveloppe, mais on se garde aussi ici.
    """
    try:
        import tables
        lignes = []
        quand = time.strftime("%Y-%m-%dT%H:%M:%S")
        monde = _monde(etat)
        qui = _qui()
        par_outil = outil or os.path.basename(__import__("sys").argv[0] or "?")
        for ident in set(list(avants) + list(apres)):
            a, b = avants.get(ident), apres.get(ident)
            if a == b:
                continue
            for e in evenements_du_volume(a, b):
                e.update({"quand": quand, "monde": monde, "par": qui,
                          "outil": par_outil, "certitude": certitude,
                          # OU VIT L'AFFAIRE. Elles ont DEUX maisons —
                          # etat/books (la bibliotheque commune) et
                          # chambres/<qui>/books (les cahiers a soi). Un
                          # journal qui n'en couvrirait qu'une ferait croire
                          # a l'exhaustivite ; le champ les separe.
                          "maison": maison})
                lignes.append(json.dumps(e, ensure_ascii=False))
        if not lignes:
            return 0
        chemin = os.path.join(etat, fichier or FICHIER)
        dossier = os.path.dirname(chemin)
        if not os.path.isdir(dossier):
            os.makedirs(dossier)
        with io.open(chemin, "a", encoding="utf-8") as f:
            f.write(u"\n".join(lignes) + u"\n")
        return len(lignes)
    except Exception:
        return 0


def lire(etat, depuis=None):
    u"""Le journal, en objets. `depuis` : un horodatage ISO minimal."""
    chemin = os.path.join(etat, FICHIER)
    out = []
    try:
        for l in io.open(chemin, encoding="utf-8"):
            l = l.strip()
            if not l:
                continue
            try:
                e = json.loads(l)
            except ValueError:
                continue
            if depuis and (e.get("quand") or "") < depuis:
                continue
            out.append(e)
    except IOError:
        return []
    return out
