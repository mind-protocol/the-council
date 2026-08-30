# -*- coding: utf-8 -*-
"""BRIEF — les constantes de la depeche, la lecture du monde, et le brief
d'un homme : sa feuille de route, ses travaux ouverts, son dossier de
journee, qui est ou.
"""
import io
import json
import os
import re
import sys
import uuid

import bibliotheque
# LE SEUL point de contact du paquet avec livre et bibliotheque (noyau,
# container plan) : les autres modules reprennent `livre` d'ici.
import livre  # le tri des volumes vit la-bas, et nulle part ailleurs
from agents.expose import affecter  # LE resolveur d'adresses
from etat.expose import tables  # LA PORTE de etat/

# Trois etages de plus qu'a la racine : scripts/agents/depeche/.
RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
ETAT = os.path.join(RACINE, "etat")
DEPOT_RAPPORTS = os.path.join(ETAT, "rapports")
METIER = os.path.join(RACINE, "docs", "metier.md")
MANUEL_MJ = os.path.join(RACINE, "CLAUDE.md")

# Le sel de l'espace de noms. Le changer rend toutes les sessions orphelines
# d'un coup : c'est le seul geste qui reparte de zero proprement.
# v2 force une session neuve après le passage au prompt système explicite :
# reprendre une session v1 conserverait précisément le contexte global pollué.
SEL = uuid.uuid5(uuid.NAMESPACE_URL, "le-conseil/depeches/v5")

OUTILS = ["Read", "Grep", "Glob", "Bash"]

# LE PARLOIR — sa bouche, quand on lui parle pendant sa journee. Il l'appelle
# par Bash, qu'il a desormais en entier (voir l'en-tete).
PARLOIR_PY = os.path.join(RACINE, "scripts", "parloir.py").replace("\\", "/")
OUTIL_PARLOIR = "Bash(python %s:*)" % PARLOIR_PY

def lire(chemin, defaut=None):
    if not os.path.exists(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as f:
        return f.read()


def date_du_monde():
    """Le jour LE PLUS AVANCE des sieges occupes — pas `monde.date`.

    `monde.date` porte l'horloge la moins avancee : c'est celle du siege
    principal, et elle ne bouge que quand LUI joue. Les autres sieges avancent
    la leur par `append_flux.py`, chacun a son rythme. Mesure du 129.4.1 :
    monde au 3.30 pendant que les trois sieges occupes etaient au 4.1 — un
    homme depeche sur `monde.date` aurait revecu le 30e une seconde fois, et
    ses pensees seraient tombees, datees d'hier, a cote de celles d'hier.

    On prend donc le maximum, jamais le minimum : une journee deja vecue ne se
    rejoue pas, tandis qu'un homme depeche un jour trop tot est simplement en
    avance sur le siege qui traine.
    """
    m = tables.lire(os.path.join(ETAT, "monde.json"), {})
    d = m.get("date", {})
    jours = [(d.get("annee", 0), d.get("lune", 0), d.get("jour", 0))]
    joueurs = tables.lire(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs", [])
    occupes = set()
    for j in joueurs or []:
        if isinstance(j, dict) and j.get("occupe") and not j.get("regie"):
            occupes.add(j.get("personnage_id") or j.get("id"))
    horloges = tables.lire(os.path.join(ETAT, "horloges.json"), {})
    for qui, h in (horloges or {}).items():
        if qui in occupes and isinstance(h, dict):
            jours.append((h.get("annee", 0), h.get("lune", 0), h.get("jour", 0)))
    return max(jours)


def identifiant_de_session(qui, date):
    """Stable par homme et par jour de jeu. Deterministe : aucun registre."""
    return str(uuid.uuid5(SEL, "%s/%d.%d.%d" % ((qui,) + date)))


_FEUILLE = {}


def feuille_de_route():
    """Qui a du temps aujourd'hui, combien de questions, et DANS QUELLE SALLE.

    Remplace `convoquer.py` en entier. L'ancien disait qui « doit une journee »
    d'apres un compteur d'excitation qui montait sans sources et retombait d'un
    point par jour ; le neuf lit ce que la journee dit d'elle-meme — le
    quartier, les creux, la force sur le graphe (`evaluer.force_narrative`).

    Une entree : {qui, force, questions, creux_total, questions_posees:[{de, a,
    salle}]}. C'est la salle qui compte autant que la duree : une question
    posee a la roukerie n'a pas les memes sources qu'une posee au bourg.
    """
    if _FEUILLE:
        return _FEUILLE
    try:
        from temps.expose import evaluer
        A, N = evaluer.lire_tissu()
        for l in evaluer.force_narrative(A, N, lambda t="": None):
            _FEUILLE[l["qui"]] = l
    except Exception as e:
        _FEUILLE["__erreur__"] = {"qui": "__erreur__", "motif": str(e)[:160]}
    return _FEUILLE


def _heure(m):
    return "%dh%02d" % ((int(m) // 60) % 24, int(m) % 60)


def brief_de(qui):
    """Sa journee telle que l'etat la dit : ses creux, ce qu'il sait deja.

    PAS DE SOURCE, PAS DE PENSEE — la contrainte d'entree est la seule chose de
    l'ancien systeme qui meritait de survivre. Ce qui change : la source n'est
    plus declaree d'avance dans une liste de courses tenue a la main. Elle est
    CE QUI EST A PORTEE DU CREUX — les livres poses dans la salle, les gens qui
    s'y trouvent au meme moment, les mesures dont il est porteur. Le creux dit
    ou il est ; l'etat dit ce qu'il y a la.
    """
    l = feuille_de_route().get(qui) or {}
    pensees = [p for p in _liste_etat("pensees.json", "pensees")
               if p.get("qui") == qui]
    concl = [c for c in _liste_etat("conclusions.json", "conclusions")
             if c.get("qui") == qui]
    livres = _liste_etat("books.json", "books")

    out = ["== SA JOURNEE — ce que l'etat en dit"]
    if not l:
        out.append("  Aucune tete dans intentions.json : il n'a pas de journee.")
        return "\n".join(out)
    if not l.get("creux"):
        out.append("  AUCUN CREUX aujourd'hui (%s). Il ne pense pas : il"
                   " travaille, et travailler est une action visible."
                   % (l.get("hors_quartier") or "journee fermee"))
        return "\n".join(out)

    out.append("  force %s sur le graphe · %d minutes libres · %d question(s)"
               % (l.get("force"), l.get("creux_total") or 0,
                  l.get("questions") or 0))
    out.append("")
    out.append("  SES CREUX — quand il a le temps, et OU il se tient alors :")
    par_salle = {}
    for c in l.get("questions_posees") or l.get("creux") or []:
        out.append("    %s -> %s  %-20s %4d min%s" % (
            _heure(c["de"]), _heure(c["a"]), c["salle"], c["minutes"],
            "   (%s)" % c["pourquoi"] if c.get("pourquoi") else ""))
        par_salle.setdefault(c["salle"], 0)
    # CE QUI EST A PORTEE DE CES SALLES-LA : les livres qu'on peut y ouvrir.
    a_portee = [b for b in livres if b.get("salle_id") in par_salle]
    sien = [b for b in livres if b.get("acteur_id") == qui]
    if a_portee or sien:
        out.append("")
        out.append("  CE QU'IL PEUT TOUCHER SANS SORTIR DE SES CREUX :")
        for b in sien:
            out.append("    (sur lui) %s — %s" % (b.get("id"), b.get("titre")))
        for b in a_portee:
            out.append("    [%s] %s — %s" % (b.get("salle_id"), b.get("id"),
                                             b.get("titre")))
    if concl:
        out.append("")
        out.append("  CE QU'IL A DEJA CONCLU, de sa main (ne pas le refaire) :")
        for c in concl:
            out.append("    %s  → %s" % (c.get("affaire"),
                                         c.get("livre") or "aucun cahier"))
    if pensees:
        def rang(p):
            d = p.get("date") or {}
            return (d.get("annee", 0), d.get("lune", 0), d.get("jour", 0))
        recentes = sorted(pensees, key=rang, reverse=True)[:8]
        out.append("")
        out.append("  CE QU'IL SAIT DEJA (%d pensees, les %d dernieres) — pour"
                   " qu'il ne retrouve pas ce qu'il a deja trouve :"
                   % (len(pensees), len(recentes)))
        for p in recentes:
            out.append("    · %s" % re.sub(r"\s+", " ",
                                           str(p.get("texte") or ""))[:220])
    return "\n".join(out)


def _liste_etat(nom, cle):
    if nom == "books.json":
        return bibliotheque.charger(ETAT)
    donnees = tables.lire(os.path.join(ETAT, nom), [])
    if isinstance(donnees, dict):
        donnees = donnees.get(cle) or []
    return donnees if isinstance(donnees, list) else []


def _voix_incarnee(personnage):
    """Garde l'empreinte personnelle et coupe l'ancienne doctrine ajoutée.

    Plusieurs ``maniere`` ont reçu au fil du jeu un même manuel de conduite.
    Le prompt neuf conserve la voix écrite avant ces ajouts universels.
    """
    texte = str((personnage or {}).get("maniere") or "").strip()
    marqueurs = (
        " Se debrouille seul", " Se débrouille seul", " Competent :",
        " Compétent :", " OUVRE PAR :", " DEUXIEME PHRASE",
        " REPRIS,", " AUCUNE ",
    )
    coupures = [texte.find(m) for m in marqueurs if texte.find(m) >= 0]
    if coupures:
        texte = texte[:min(coupures)].strip()
    return texte


def _relations_de(qui, noms):
    relations = _liste_etat("relations.json", "relations")
    resultat = []
    for relation in relations:
        source = relation.get("source_id")
        cible = relation.get("cible_id")
        if qui not in (source, cible):
            continue
        resultat.append({
            "source_id": source,
            "source": noms.get(source, source),
            "cible_id": cible,
            "cible": noms.get(cible, cible),
            "opinion": relation.get("opinion"),
            "liens": relation.get("liens") or [],
        })
    return resultat


def _affaires_du_brief(brief):
    """Extrait du brief les affaires vécues, avant son ancien mode d'emploi."""
    texte = str(brief or "")
    debut = texte.find("POURQUOI ON LE CONVOQUE")
    fin = texte.find("CE QU'IL RAPPORTE")
    if debut >= 0:
        texte = texte[debut:fin if fin > debut else None]
    texte = texte.replace("ce qu'il n'a pas encore touche :",
                          "ses prochaines sources :")
    texte = texte.replace("ce qu’il n’a pas encore touché :",
                          "ses prochaines sources :")
    return texte.strip(" =\n")


def travaux_ouverts_de(qui):
    """Ce que cet homme a ÉCRIT — la pièce centrale de la greffe documentaire.

    La mémoire d'un dépêché n'est pas sa tête d'`intentions.json` (treize
    têtes en retard au 30 août, dont Hask gelé huit jours de jeu pendant
    qu'il se corrigeait neuf fois par écrit) : c'est ses pensées datées et
    sa dernière conclusion de sa main. `memoire_activation()` savait déjà
    les servir (`travaux_ouverts`), mais AUCUN chemin ne les peuplait —
    ni ici, ni la boucle d'activation, dont le `travaux = []` était codé
    en dur. L'homme reprend là où SA plume s'est arrêtée, pas là où le
    dernier quart d'heure l'a laissé.

    Lecture bornée : le dernier rapport (`etat/rapports/<qui>.json`), et si
    aucun travail n'y porte de conclusion, la première conclusion trouvée en
    remontant les archives (`etat/archive/travaux/<date>/<qui>.json`), une
    seule. Quatre pensées par travail, comme la boucle d'activation.
    """
    ouverts = []

    def _verser(travail, source):
        ouverts.append({
            "id": travail.get("travail_id") or travail.get("id"),
            "affaire": travail.get("travail_id") or travail.get("id"),
            "pensees_recentes": (travail.get("pensees") or [])[-4:],
            "conclusion": travail.get("conclusion"),
            "source": source,
        })

    rapport = tables.lire(
        os.path.join(ETAT, "rapports", "%s.json" % qui), {})
    for t in (rapport.get("travaux") or []):
        if isinstance(t, dict):
            _verser(t, "dernier rapport")

    if not any(o["conclusion"] for o in ouverts):
        base = os.path.join(ETAT, "archive", "travaux")
        for jour in sorted(os.listdir(base) if os.path.isdir(base) else [],
                           reverse=True):
            f = os.path.join(base, jour, "%s.json" % qui)
            if not os.path.isfile(f):
                continue
            archive = tables.lire(f, {})
            conclu = next((t for t in (archive.get("travaux") or [])
                           if isinstance(t, dict) and t.get("conclusion")),
                          None)
            if conclu:
                _verser(conclu, "archive du %s" % jour)
                break
    return ouverts


def dossier_journee(qui, brief):
    """Rassemble l'identité et la situation vivante d'une journée."""
    personnages = _liste_etat("personnages.json", "personnages")
    noms = {p.get("id"): p.get("nom") or p.get("id")
            for p in personnages if isinstance(p, dict) and p.get("id")}
    personnage = next((p for p in personnages if p.get("id") == qui), {})
    personnage = {k: personnage.get(k) for k in
                   ("id", "nom", "titre", "naissance", "traits", "objectifs",
                    "maniere", "portrait", "etat", "condition", "lieu_id")
                   if k in personnage}

    intentions = _liste_etat("intentions.json", "intentions")
    intention = next((i for i in intentions
                      if i.get("personnage_id") == qui), {})
    intention = {k: intention.get(k) for k in
                 ("personnage_id", "croyances", "ignore", "intention",
                  "declencheurs", "attitude_joueur", "mandat", "date_maj")
                 if k in intention}

    presence = tables.lire(os.path.join(ETAT, "presence.json"), {})
    resolus = ((presence.get("resolu") or {}).get("gens") or {}) \
        if isinstance(presence, dict) else {}
    position = resolus.get(qui) or {}
    salle_id = position.get("salle")
    presents = [{"id": pid, "nom": noms.get(pid, pid)}
                for pid, ou in resolus.items() if salle_id and
                ou.get("salle") == salle_id]
    presents.sort(key=lambda p: (p["nom"].casefold(), p["id"]))

    return {
        "date_du_monde": dict(zip(("annee", "lune", "jour"),
                                   date_du_monde())),
        "personnage": personnage,
        "salle_actuelle": {
            "id": salle_id,
            "nom": position.get("lieu") or salle_id or personnage.get("lieu_id"),
            "personnes": presents,
        },
        "intention": intention,
        "relations": _relations_de(qui, noms),
        "affaires_du_jour": _affaires_du_brief(brief),
        "travaux_ouverts": travaux_ouverts_de(qui),
    }


def a_convoquer():
    """Qui vaut d'etre depeche aujourd'hui : ceux a qui la journee laisse du
    temps, les plus forts d'abord. Un homme sans creux n'est pas convocable —
    il ne penserait pas, il ferait semblant."""
    f = feuille_de_route()
    ayants = [l for l in f.values() if l.get("questions")]
    ayants.sort(key=lambda l: -l.get("force", 0))
    return [l["qui"] for l in ayants]


def les_pj():
    """Les sieges OCCUPES. On ne depeche jamais un personnage joueur : sa tete
    appartient a quelqu'un, et la faire vivre par une session serait parler a
    sa place. C'est une exclusion DURE — il n'y a pas de drapeau pour la
    lever, parce qu'il n'y a pas de cas ou l'on voudrait."""
    j = tables.lire(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(j, dict):
        j = j.get("joueurs") or j.get("sieges") or []
    return {s.get("personnage_id") or s.get("id")
            for s in j if s.get("occupe")}


def salles_peuplees():
    """{salle: [ids]} d'apres les positions RESOLUES par scripts/presence.py.
    On ne lit pas `presence` brut : c'est le declaratif, `resolu` est ce qui
    tient compte des deplacements."""
    d = tables.lire(os.path.join(ETAT, "presence.json"), {})
    gens = ((d.get("resolu") or {}).get("gens") or {})
    par_salle = {}
    for qui, ou in gens.items():
        par_salle.setdefault(ou.get("salle"), []).append(qui)
    return par_salle


def dans_la_salle(salle):
    """Qui depecher dans cette salle. Rend (a_depecher, pj_ecartes)."""
    gens = sorted(salles_peuplees().get(salle, []))
    pj = les_pj()
    return [q for q in gens if q not in pj], [q for q in gens if q in pj]


def positions():
    """{personnage_id: (x, y, z)} — en metres reels, comme partout ici.

    Deux chemins, dans cet ordre. Le corps PROPRE d'abord (`etat/corps.json`,
    `corps[]`), qui est une adresse a lui. Sinon la position de la SALLE ou il
    se tient, prise dans les `affectations` : c'est une approximation assumee
    et c'est la bonne — deux hommes dans la meme piece sont a portee de voix,
    et c'est tout ce qu'un rayon de dix metres cherche a dire.

    Un corps EMPRUNTE (`liens`) n'est pas resolu ici : ses coordonnees vivent
    dans `monde/gens/`, qui pese quatre cent mille ames et se regenere. Ces
    gens-la retombent sur la position de leur salle, ce qui suffit.
    """
    C = tables.lire(os.path.join(ETAT, "corps.json"), {})
    P = tables.lire(os.path.join(ETAT, "presence.json"), {})
    af = C.get("affectations") or {}
    gens = ((P.get("resolu") or {}).get("gens") or {})

    ou = {}
    for c in (C.get("corps") or []):
        if c.get("x") is not None:
            ou[c["personnage_id"]] = (c["x"], c["y"], c.get("z") or 0)
    for qui, p in gens.items():
        if qui in ou:
            continue
        s = p.get("salle")
        # Une salle du plan que le monde a creusee a des metres SANS qu'aucune
        # affectation ne l'ait dit : c'est `affecter.adresse` qui le sait, et
        # c'est ce qui sortait trente-deux personnes du rayon en silence.
        xyz = affecter.adresse(s) if s else None
        if xyz:
            ou[qui] = xyz
    return ou


def position_de(cible, ou):
    """La cible d'un rayon : quelqu'un, ou une salle."""
    if cible in ou:
        return ou[cible]
    return affecter.adresse(cible)


def dans_le_rayon(cible, metres):
    """Rend (a_depecher, pj_ecartes, sans_position).

    `sans_position` n'est pas du bruit : ce sont des gens qui sont peut-etre
    la et que le rayon ne peut pas voir, faute d'adresse physique pour leur
    salle. On les NOMME — un rayon qui les tairait donnerait une salle a
    moitie vide sans le dire, et l'on croirait avoir depeche tout le monde.
    """
    ou = positions()
    centre = position_de(cible, ou)
    if centre is None:
        raise SystemExit(
            u"« %s » n'a pas d'adresse physique — ni corps, ni salle affectee.\n"
            u"  python scripts/affecter.py    pour lui en donner une" % cible)

    P = tables.lire(os.path.join(ETAT, "presence.json"), {})
    tous = ((P.get("resolu") or {}).get("gens") or {})
    pj = les_pj()
    dedans, ecartes, aveugles = [], [], []
    for qui in sorted(tous):
        p = ou.get(qui)
        if p is None:
            aveugles.append(qui)
            continue
        d = sum((a - b) ** 2 for a, b in zip(p, centre)) ** 0.5
        if d > metres:
            continue
        (ecartes if qui in pj else dedans).append(qui)
    return dedans, ecartes, aveugles


def travaux_ids(qui):
    """LES CREUX DE SA JOURNEE, a la place des identifiants d'affaires.

    On lui demandait de raccrocher chaque pensee a un `travail_id` — et faute
    de le lui donner, il en inventait un que rien ne rattrapait ensuite. Une
    pensee se rattache desormais a un CREUX : une heure et une salle, deux
    choses qu'il vit et qu'il n'a aucune raison d'inventer.
    """
    l = feuille_de_route().get(qui) or {}
    creux = l.get("questions_posees") or l.get("creux") or []
    if not creux:
        return (u"    (aucun creux aujourd'hui — tu n'as pas le temps de "
                u"penser : tu travailles, et travailler se voit)")
    return u"\n".join(u"    %s-%s  %-20s %4d min" % (
        _heure(c["de"]), _heure(c["a"]), c["salle"], c["minutes"])
        for c in creux)

