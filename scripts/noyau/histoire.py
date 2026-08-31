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

LES DEUX PORTES. Une écriture par `bibliotheque.Session` émet et avance son
empreinte dans la même section critique. Les hommes dépêchés ont aussi `Write`
et `Edit` sur le dépôt : le runtime réconcilie automatiquement à leur retour,
même sur erreur ou expiration. Chaque ligne porte donc `certitude` :
« declare » quand l'événement est émis au moment de l'écriture, « constate »
quand le diff du disque l'a établi après coup.

CE QUI EST SUIVI. Actions, clefs, verrous et états-cibles dans les affaires ;
moyens et offices dans leurs registres plats ; mesures, seuils et mandats dans
les documents `mains.json`. `actes.json` reste le registre des faits du monde,
jamais celui des mutations de ces documents.
"""
import io
import json
import os
import re
import time
import unicodedata
import uuid
import contextlib

FICHIER = os.path.join("histoire", "affaires.jsonl")
EMPREINTES = os.path.join("histoire", "empreintes.json")
SECOURS = os.path.join("histoire", "empreintes-sans-perte.json")
VERROU = os.path.join("histoire", ".journal.lock")

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
    tables_volume = volume.get("tables") or []
    if not tables_volume and (volume.get("colonnes") or volume.get("lignes")):
        tables_volume = [{"titre": volume.get("titre"),
                          "colonnes": volume.get("colonnes") or [],
                          "lignes": volume.get("lignes") or []}]
    for t in tables_volume:
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
                "colonnes": [str(x) for x in cols],
            }
        return out
    return {}


def _changements(avant, apres, ignorer=()):
    u"""Diff cellule par cellule, avec le nom de colonne quand il existe."""
    a = (avant or {}).get("cellules") or []
    b = (apres or {}).get("cellules") or []
    cols = ((apres or {}).get("colonnes")
            or (avant or {}).get("colonnes") or [])
    ignores = set(ignorer)
    out = []
    for i in range(max(len(a), len(b))):
        av = a[i] if i < len(a) else None
        ap = b[i] if i < len(b) else None
        if av == ap or i in ignores:
            continue
        out.append({"colonne": cols[i] if i < len(cols) else str(i),
                    "avant": av, "apres": ap})
    return out


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


def _diff_champs(avant, apres, ignorer=()):
    ignores = set(ignorer)
    out = []
    for cle in sorted(set((avant or {}).keys()) | set((apres or {}).keys())):
        if cle in ignores or (avant or {}).get(cle) == (apres or {}).get(cle):
            continue
        out.append({"champ": cle, "avant": (avant or {}).get(cle),
                    "apres": (apres or {}).get(cle)})
    return out


def _par_id(liste):
    return {str(x.get("id")): x for x in (liste or [])
            if isinstance(x, dict) and x.get("id") is not None}


def evenements_des_mains(avant, apres):
    u"""Toutes les mutations structurées d'un document mains.json."""
    ev = []
    maison = (apres or avant or {}).get("maison_id")
    anciennes = _par_id((avant or {}).get("mains"))
    nouvelles = _par_id((apres or {}).get("mains"))
    for ident in sorted(set(anciennes) | set(nouvelles)):
        a, b = anciennes.get(ident), nouvelles.get(ident)
        base = {"affaire": ident, "main": ident, "maison": maison}
        if a is None:
            ev.append(dict(base, quoi="main.creee", apres=b))
            continue
        if b is None:
            ev.append(dict(base, quoi="main.retiree", avant=a))
            continue
        meta = _diff_champs(a, b, ignorer=("mesure", "seuils"))
        if meta:
            ev.append(dict(base, quoi="main.modifiee", changements=meta))
        ma, mb = _par_id(a.get("mesure")), _par_id(b.get("mesure"))
        for mid in sorted(set(ma) | set(mb)):
            x, y = ma.get(mid), mb.get(mid)
            sous = dict(base, mesure=mid)
            if x is None:
                ev.append(dict(sous, quoi="mesure.creee", apres=y))
            elif y is None:
                ev.append(dict(sous, quoi="mesure.retiree", avant=x))
            else:
                changements = _diff_champs(x, y)
                if changements:
                    ev.append(dict(sous, quoi="mesure.changee",
                                   avant=x.get("valeur"),
                                   apres=y.get("valeur"),
                                   changements=changements))
        sa, sb = _par_id(a.get("seuils")), _par_id(b.get("seuils"))
        for sid in sorted(set(sa) | set(sb)):
            x, y = sa.get(sid), sb.get(sid)
            sous = dict(base, seuil=sid)
            if x is None:
                ev.append(dict(sous, quoi="seuil.cree", apres=y))
            elif y is None:
                ev.append(dict(sous, quoi="seuil.retire", avant=x))
            else:
                changements = _diff_champs(x, y)
                if changements:
                    ev.append(dict(sous, quoi="seuil.modifie",
                                   changements=changements))
    return ev


# Les tables suivies, et ce qu'on sait dire de chacune. La colonne de droite
# est volontairement pauvre pour les cibles et les verrous : voir l'en-tete.
SUIVIES = [
    (u"⚔️ Actions", "action"),
    (u"🗝️ Clefs", "clef"),
    (u"🎯 États cibles", "cible"),
    (u"🔒 Verrous", "verrou"),
    (u"Les moyens", "moyen"),
    (u"Les offices", "office"),
]


def evenements_du_volume(avant, apres):
    u"""Les evenements d'UN volume, entre deux versions. Liste de dicts."""
    if (apres or avant or {}).get("_type_document") == "mains":
        return evenements_des_mains(avant, apres)
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
                brut = (b or {}).get("etat") if genre == "action" else \
                       (b or {}).get("etat") if genre == "moyen" else \
                       (b or {}).get("decision") if genre == "clef" else None
                ev.append(dict(base, quoi="%s.%s"
                               % (genre, "creee" if genre in
                                  ("action", "moyen", "office")
                                  else "posee"), apres=brut,
                               ligne_apres=(b or {}).get("cellules") or []))
                continue
            if b is None:
                brut = (a or {}).get("etat") if genre == "action" else \
                       (a or {}).get("etat") if genre == "moyen" else \
                       (a or {}).get("decision") if genre == "clef" else None
                ev.append(dict(base, quoi="%s.retiree" % genre, avant=brut,
                               ligne_avant=(a or {}).get("cellules") or []))
                continue
            if genre == "action":
                cols = b.get("colonnes") or a.get("colonnes") or []
                i_etat = _colonne(cols, u"⏳ État", u"État", u"Etat")
                i_fait = _colonne(cols, u"Jour fait")
                if decaper(a["etat"]) != decaper(b["etat"]):
                    nom = _transition(a["etat"], b["etat"])
                    if nom:
                        ev.append(dict(base, quoi=nom,
                                       avant=a["etat"], apres=b["etat"],
                                       changements=_changements(a, b)))
                if a["jour_fait"] != b["jour_fait"]:
                    ev.append(dict(base, quoi="action.datee",
                                   avant=a["jour_fait"],
                                   apres=b["jour_fait"]))
                autres = _changements(a, b, ignorer=[x for x in
                                      (i_etat, i_fait) if x is not None])
                if autres:
                    ev.append(dict(base, quoi="action.modifiee",
                                   changements=autres))
            elif genre == "clef":
                cols = b.get("colonnes") or a.get("colonnes") or []
                i_dec = _colonne(cols, u"⚖️ Décision", u"Décision")
                if a["decision"] != b["decision"]:
                    ev.append(dict(base, quoi="clef.decidee",
                                   avant=a["decision"], apres=b["decision"],
                                   changements=_changements(a, b)))
                autres = _changements(a, b,
                                      ignorer=[] if i_dec is None else [i_dec])
                if autres:
                    ev.append(dict(base, quoi="clef.modifiee",
                                   changements=autres))
            elif genre == "moyen":
                cols = b.get("colonnes") or a.get("colonnes") or []
                i_etat = _colonne(cols, u"🔎 État", u"État", u"Etat")
                if decaper(a["etat"]) != decaper(b["etat"]):
                    ev.append(dict(base, quoi="moyen.etat",
                                   avant=a["etat"], apres=b["etat"],
                                   changements=_changements(a, b)))
                autres = _changements(a, b,
                                      ignorer=[] if i_etat is None else [i_etat])
                if autres:
                    ev.append(dict(base, quoi="moyen.modifie",
                                   changements=autres))
            elif a["cellules"] != b["cellules"]:
                # CIBLES ET VERROUS : aucune colonne d'etat, donc aucun
                # « atteinte » ni « leve » possible. On dit ce qu'on sait :
                # la ligne a bouge.
                ev.append(dict(base, quoi="%s.modifiee" % genre,
                               changements=_changements(a, b)))
    return ev


def _qui():
    u"""L'auteur, si le lanceur a bien pose son nom dans l'environnement.

    `LE_CONSEIL_QUI` existait comme convention et n'etait JAMAIS posee — une
    lecture dans tout le depot, zero ecriture. Les lanceurs la posent
    desormais ; a defaut on rend None et la ligne le dira.
    """
    return (os.environ.get("LE_CONSEIL_QUI")
            or os.environ.get("LE_CONSEIL_MJ") or None)


def _provenance_contexte():
    u"""Métadonnées exactes seulement quand l'écriture a lieu dans le call."""
    valeurs = {
        "contexte_id": os.environ.get("LE_CONSEIL_CONTEXTE"),
        "session_id": os.environ.get("LE_CONSEIL_SESSION"),
        "ref": os.environ.get("LE_CONSEIL_REF"),
        "mode_appel": os.environ.get("LE_CONSEIL_MODE"),
    }
    return {k: v for k, v in valeurs.items() if v}


def _monde(etat):
    u"""La date du monde du siege principal, si on la tient. DEUX HORLOGES :
    c'est l'absence de celle-ci sur les billets qui rendait « les X dernieres
    heures de jeu » impossible. On ne refait pas l'erreur."""
    try:
        with io.open(os.path.join(etat, "horloges.json"),
                     encoding="utf-8") as f:
            h = json.load(f)
        with io.open(os.path.join(etat, "joueurs.json"),
                     encoding="utf-8") as f:
            j = json.load(f)
        js = j.get("joueurs") if isinstance(j, dict) else j
        principal = next((s.get("personnage_id") for s in (js or [])
                          if s.get("role") == "principal"), None)
        return h.get(principal)
    except Exception:
        return None


def _document(ident, volume, maison):
    mid = (volume or {}).get("maison_id")
    if (volume or {}).get("_type_document") == "mains" and mid:
        return "etat/maisons/%s/documents/mains.json" % mid
    if mid:
        return "etat/maisons/%s/documents/books/%s.json" % (mid, ident)
    if str(maison).startswith("chambre:"):
        return "chambres/%s/books/%s.json" % (str(maison).split(":", 1)[1],
                                               ident)
    return "etat/books/%s.json" % ident


def journaliser(avants, apres, etat, certitude="declare", outil=None,
                fichier=None, maison="etat", par=None):
    u"""Ecrit les evenements de tous les volumes touches. Rend leur nombre.

    NE LEVE JAMAIS : un journal qui casse une ecriture d'etat serait un
    remede pire que le mal. L'appelant enveloppe, mais on se garde aussi ici.
    """
    try:
        import tables
        lignes = []
        quand = time.strftime("%Y-%m-%dT%H:%M:%S")
        monde = _monde(etat)
        qui = _qui() if par is None else par
        par_outil = outil or os.path.basename(__import__("sys").argv[0] or "?")
        for ident in set(list(avants) + list(apres)):
            a, b = avants.get(ident), apres.get(ident)
            if a == b:
                continue
            for e in evenements_du_volume(a, b):
                e.update({"quand": quand, "monde": monde, "par": qui,
                          "outil": par_outil, "certitude": certitude,
                          # OU VIT L'AFFAIRE. La maison_id du livre nomme la
                          # bibliotheque possedee ; l'argument `maison` garde
                          # les cahiers de chambres et les anciens appels. Un
                          # journal qui n'en couvrirait qu'une ferait croire
                          # a l'exhaustivite ; le champ les separe.
                          "maison": ((b or a or {}).get("maison_id")
                                      or maison),
                          "document": _document(ident, b or a, maison),
                          "transition_id": uuid.uuid4().hex})
                # Une porte qui tient avant/apres dans le call sait d'ou vient
                # l'ecriture. Une reconciliation `constate`, elle, peut avoir
                # ramasse le geste concurrent d'un autre : ne lui colle jamais
                # la session qui a seulement declenche l'observation.
                if certitude == "declare":
                    e.update(_provenance_contexte())
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


@contextlib.contextmanager
def verrou(etat, timeout=30):
    u"""Sérialise journal + empreinte entre CALL, CAST et serveur."""
    chemin = os.path.join(etat, VERROU)
    dossier = os.path.dirname(chemin)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    f = open(chemin, "a+b")
    debut = time.time()
    pris = False
    try:
        while not pris:
            try:
                if os.name == "nt":
                    import msvcrt
                    f.seek(0)
                    if not f.read(1):
                        f.seek(0)
                        f.write(b"0")
                        f.flush()
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:  # pragma: no cover
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                pris = True
            except OSError:
                if time.time() - debut >= timeout:
                    raise TimeoutError("journal des affaires occupé")
                time.sleep(0.05)
        yield
    finally:
        if pris:
            try:
                if os.name == "nt":
                    import msvcrt
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                else:  # pragma: no cover
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        f.close()


def _json(chemin, defaut):
    try:
        with io.open(chemin, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defaut


def _ecrire_json(chemin, valeur):
    dossier = os.path.dirname(chemin)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    temporaire = chemin + ".%s.tmp" % uuid.uuid4().hex
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        json.dump(valeur, f, ensure_ascii=False, indent=1)
        f.write(u"\n")
    os.replace(temporaire, chemin)


def actualiser_empreinte(avants, apres, etat):
    u"""Aligne l'empreinte sur une écriture déjà journalisée par la porte."""
    touches = [i for i in set(list(avants) + list(apres))
               if avants.get(i) != apres.get(i)]
    if not touches:
        return
    chemin = os.path.join(etat, EMPREINTES)
    secours = os.path.join(etat, SECOURS)
    empreinte = _json(chemin, {})
    copie_sure = _json(secours, {})
    pertes = False
    for ident in touches:
        a, b = avants.get(ident), apres.get(ident)
        volume = b or a or {}
        clef = "maison:%s" % volume.get("maison_id") \
               if volume.get("maison_id") else "etat"
        groupe = empreinte.setdefault(clef, {})
        if b is None:
            groupe.pop(ident, None)
        else:
            groupe[ident] = b
        pertes = pertes or any(str(e.get("quoi") or "").endswith(".retiree")
                               for e in evenements_du_volume(a, b))
        if not pertes:
            groupe_s = copie_sure.setdefault(clef, {})
            if b is None:
                groupe_s.pop(ident, None)
            else:
                groupe_s[ident] = b
    _ecrire_json(chemin, empreinte)
    if not pertes:
        _ecrire_json(secours, copie_sure)


def journaliser_et_actualiser(avants, apres, etat, **options):
    u"""Transaction logique : append des transitions puis avance le curseur."""
    with verrou(etat):
        n = journaliser(avants, apres, etat, **options)
        actualiser_empreinte(avants, apres, etat)
        return n


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
