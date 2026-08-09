# -*- coding: utf-8 -*-
# DEPECHER — envoyer un homme vivre sa journee, dans une session a lui.
#
# La piece qui manquait au bout de docs/session-travail.md : `convoquer.py` dit
# QUI doit une journee et redige son brief ; celui-ci le DEPECHE pour de bon,
# par `claude -p`, et rapporte ce qu'il a trouve.
#
# ─────────────────────────────────────────────────────────────────────────────
# POURQUOI ON NE LANCE PAS L'APPEL DEPUIS LE DEPOT. Mesure du 9 aout, deux
# appels identiques a un mot pres :
#
#     depuis le depot          89 051 jetons de contexte
#     depuis ailleurs          31 000 jetons de contexte
#
# La difference, c'est CLAUDE.md — le manuel du MJ, ses modes, son rendu, sa
# discipline d'ecriture d'etat — charge d'office par la decouverte automatique,
# et dont un sergent au role n'a pas l'usage. Huit fois le prix pour lire des
# regles d'affichage qui ne le concernent pas. On lance donc depuis un
# repertoire neutre, hors du depot, et l'on rouvre le depot par `--add-dir` :
# il garde ses yeux, il perd le manuel.
#
# C'est cette mesure, et elle seule, qui a fait scinder CLAUDE.md. `docs/
# metier.md` est la moitie qui parle a un homme : ce qu'il apporte, le peage
# avant d'ouvrir la bouche, les deux jets, comment il parle. Il est AUTONOME —
# son lexique de pied resout les cinq mots qu'il avait herites du manuel — et
# c'est lui, et rien d'autre, qu'on met dans le prompt systeme.
#
# ─────────────────────────────────────────────────────────────────────────────
# L'HOMME N'A QUE DES YEUX. Read, Grep, Glob, rien de plus. Il ne peut pas
# ecrire, donc il ne peut pas se tromper de fichier, donc la regle du seul
# ecrivain tient sans qu'on ait a lui faire confiance. Sa reponse FINALE est
# son rapport ; c'est ce script qui la pose dans etat/staging/travaux/.
# Le brief de `convoquer.py` dit « dans etat/staging/... » : la mission
# ci-dessous le corrige explicitement, sinon il perdrait un tour a tenter
# une ecriture qu'on lui refuse.
#
# ─────────────────────────────────────────────────────────────────────────────
# LA SESSION EST STABLE PAR HOMME ET PAR JOUR DE JEU. uuid5 sur
# « le-conseil/<homme>/<annee>.<lune>.<jour> » : deterministe, donc
# retrouvable sans registre a tenir, et neuve a chaque jour de jeu. C'est la
# bonne maille — la doctrine donne DEUX travaux par journee d'homme, et l'on
# veut que le second se souvienne de ce que le premier a trouve le matin, sans
# heriter de la veille.
#
# Mesure, pas supposition : `--session-id` REFUSE un id deja vu
# (« Session ID ... is already in use »). On tente donc --session-id, et l'on
# retombe sur --resume, qui reprend en place et rend le meme id.
#
# Usage :
#     python scripts/depecher.py --qui le-sanglier
#     python scripts/depecher.py --tous
#     python scripts/depecher.py --qui sara --sec      montre tout, n'appelle pas
#     python scripts/depecher.py --qui sara --mission "..."   consigne du jour
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livre  # le tri des volumes vit la-bas, et nulle part ailleurs
import affecter  # LE resolveur d'adresses : on ne relit plus `xyz` a la main

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETAT = os.path.join(RACINE, "etat")
DEPOT_RAPPORTS = os.path.join(ETAT, "staging", "travaux")
METIER = os.path.join(RACINE, "docs", "metier.md")

# Le sel de l'espace de noms. Le changer rend toutes les sessions orphelines
# d'un coup : c'est le seul geste qui reparte de zero proprement.
SEL = uuid.uuid5(uuid.NAMESPACE_URL, "le-conseil/depeches/v1")

OUTILS = ["Read", "Grep", "Glob"]


def lire(chemin, defaut=None):
    if not os.path.exists(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as f:
        return f.read()


def date_du_monde():
    m = json.loads(lire(os.path.join(ETAT, "monde.json"), "{}"))
    d = m.get("date", {})
    return d.get("annee", 0), d.get("lune", 0), d.get("jour", 0)


def identifiant_de_session(qui, date):
    """Stable par homme et par jour de jeu. Deterministe : aucun registre."""
    return str(uuid.uuid5(SEL, "%s/%d.%d.%d" % ((qui,) + date)))


def brief_de(qui):
    """Le dossier tel que `convoquer.py` le redige. On passe par le script
    plutot que par ses fonctions : sa signature interne peut bouger, sa
    sortie est le contrat."""
    r = subprocess.run(
        [sys.executable, os.path.join(RACINE, "scripts", "convoquer.py"),
         "--qui", qui, "--dossiers"],
        cwd=RACINE, capture_output=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    return r.stdout.decode("utf-8", "replace").strip()


def a_convoquer():
    r = subprocess.run(
        [sys.executable, os.path.join(RACINE, "scripts", "convoquer.py")],
        cwd=RACINE, capture_output=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    sortie = r.stdout.decode("utf-8", "replace")
    gens = []
    for ligne in sortie.split("\n"):
        m = re.match(r"^  ([a-z0-9][a-z0-9\-]+)\s{2,}\S", ligne)
        if m:
            gens.append(m.group(1))
    return gens


def les_pj():
    """Les sieges OCCUPES. On ne depeche jamais un personnage joueur : sa tete
    appartient a quelqu'un, et la faire vivre par une session serait parler a
    sa place. C'est une exclusion DURE — il n'y a pas de drapeau pour la
    lever, parce qu'il n'y a pas de cas ou l'on voudrait."""
    j = json.loads(lire(os.path.join(ETAT, "joueurs.json"), "[]"))
    if isinstance(j, dict):
        j = j.get("joueurs") or j.get("sieges") or []
    return {s.get("personnage_id") or s.get("id")
            for s in j if s.get("occupe")}


def salles_peuplees():
    """{salle: [ids]} d'apres les positions RESOLUES par scripts/presence.py.
    On ne lit pas `presence` brut : c'est le declaratif, `resolu` est ce qui
    tient compte des deplacements."""
    d = json.loads(lire(os.path.join(ETAT, "presence.json"), "{}"))
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
    C = json.loads(lire(os.path.join(ETAT, "corps.json"), "{}"))
    P = json.loads(lire(os.path.join(ETAT, "presence.json"), "{}"))
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

    P = json.loads(lire(os.path.join(ETAT, "presence.json"), "{}"))
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
    """Les identifiants de ses travaux ouverts, tels que `travaux.json` les
    porte. `convoquer.py` rend le TITRE de l'affaire et jamais son id ; un
    homme a qui l'on demande un `travail_id` sans le lui donner en invente
    un, et `verser_travaux.py` ne raccroche plus rien."""
    T = json.loads(lire(os.path.join(ETAT, "travaux.json"), "[]"))
    if isinstance(T, dict):
        T = T.get("travaux") or []
    siens = [t for t in T if t.get("qui") == qui
             and t.get("etat") not in ("rendu", "abandonne")]
    if not siens:
        return u"    (aucun travail ouvert — tu n'as rien a rendre aujourd'hui)"
    return u"\n".join(u"    %-28s %s" % (t.get("id"),
                                         (t.get("affaire") or u"")[:44])
                      for t in siens)


def manuel_de(qui):
    """Le CLAUDE.md de cet homme : son metier, et rien du manuel du MJ."""
    metier = lire(METIER)
    if metier is None:
        raise SystemExit("docs/metier.md est introuvable — rien a mettre dans "
                         "les mains de cet homme.")
    tete = (
        u"Tu es %s. Pas un assistant qui le joue : lui.\n\n"
        u"Ce fichier est ton metier. Il prime sur tout reflexe d'assistant : "
        u"tu ne resumes pas ce qu'on vient de te dire, tu ne proposes pas ton "
        u"aide, tu ne demandes pas la permission de continuer, et tu ne "
        u"commentes jamais ta propre tache. Tu fais ta journee et tu rends "
        u"ton rapport.\n\n"
        u"---\n\n"
    ) % qui
    return tete + metier


def mission(qui, brief, consigne):
    depot = os.path.join(RACINE, "").replace("\\", "/")
    gens = json.loads(lire(os.path.join(ETAT, 'personnages.json'), '[]'))
    if isinstance(gens, dict):
        gens = gens.get('personnages', [])
    noms = {g.get('id'): g.get('nom') or g.get('id') for g in gens}
    siens, maison = livre.index(qui, noms)
    etagere = u"""
════════════════════════════════════════════════════════════════════════
CE QUE TU PEUX OUVRIR — ton etagere, et rien de plus

Cette liste est CLOSE. Un volume qui n'y est pas ne t'est pas refuse : il
n'existe pas pour toi. Tu ne le cherches pas, tu ne le devines pas, tu ne
demandes pas pourquoi il n'y est pas. Les carnets des autres, ce qui est
range chez la reine, ce que d'autres yeux se reservent — tu n'en sais rien.

Ils sont POSES A COTE DE TOI, un fichier par volume, dans ./livres/ :
    Read  ./livres/<identifiant>.txt      pour en ouvrir un
    Grep  ... --path ./livres             pour chercher dans tous a la fois

N'ouvre JAMAIS etat/books.json : il porte les volumes de toute la maison,
il fait deux millions de signes, et tu y perdrais ta journee entiere.

%(siens)s%(maison)s
""" % {
        "siens": (u"  LES TIENS — tu les portes, ils sont toujours a portee\n"
                  + u"\n".join(siens) + u"\n\n") if siens else u"",
        "maison": (u"  CEUX DE LA MAISON — poses ou portes la ou tu es\n"
                   + u"\n".join(maison)) if maison else
                  u"  (rien d'autre que les tiens)",
    }
    return u"""%(brief)s
%(etagere)s
════════════════════════════════════════════════════════════════════════
CE QUI EST A TOI AUJOURD'HUI

Le depot est ouvert en lecture a cette adresse : %(depot)s

CE QUI EST GROS, ON LE FOUILLE — ON NE LE LIT PAS. Trois fichiers pesent
plus qu'une journee d'homme : etat/books.json (2 Mo — tu as ton etagere,
n'y touche pas), etat/paroles.json (570 ko), etat/actes.json (400 ko).
Sur les deux derniers : Grep un nom, une date, un mot, et Read seulement
autour de ce que tu as trouve. Un Read entier de l'un d'eux te coute ta
journee et ne te rend rien.

Le reste de etat/ se lit normalement.
`python scripts/dossier.py --sur <sujet>` n'est PAS a ta portee :
tu n'as que des yeux, lis les fichiers.

TU N'ECRIS RIEN. Tu n'as ni Write ni Edit ni Bash, et c'est voulu : ton
rapport ne se pose pas sur le disque par ta main. Le brief ci-dessus dit
« dans etat/staging/travaux/... » — ignore cette phrase-la, et cela seulement.

TA DERNIERE REPONSE EST TON RAPPORT, et elle ne contient QUE lui : un objet
JSON, sans phrase avant, sans phrase apres, sans bloc de code autour.

{
  "qui": "%(qui)s",
  "journal": [
    {"heure": "7h00", "duree": 20, "lieu": "<ou tu TRAVAILLES>",
     "quoi": "<ce que tu fais, a la troisieme personne>",
     "resultat": "<ce que ca t'a donne, en clair et chiffre>"},
    {"heure": "7h20", "duree": 15, "de": "<d'ou>", "a": "<vers ou>",
     "quoi": "<il descend au bourg, sa canne sous le bras>", "resultat": "—"}
  ],
  "travaux": [
    {"travail_id": "<un des identifiants donnes plus bas, EXACTEMENT>",
     "dernier_travail": %(aujourdhui)s,
     "pensees": [{"date": %(aujourdhui)s,
                  "source": "<ce que tu as touche, en clair>",
                  "texte": "<ce que ca t'a appris>"}],
     "conclusion": null}
  ],
  "cahier2": [
    {"livre": "...", "table": "...", "ligne": "...", "colonne": "...",
     "valeur": "..."}
  ]
}

TROIS CHOSES QUI FONT REJETER UNE JOURNEE ENTIERE, et qu'on ne devine pas :
· `travail_id` doit etre un identifiant de la liste ci-dessous, au signe pres ;
· chaque pensee porte sa `date`, en objet, et c'est %(aujourdhui)s ;
· la `conclusion` est DANS le travail qu'elle conclut, jamais a la racine —
  et elle reste `null` tant qu'elle n'est pas mure.

TES IDENTIFIANTS DE TRAVAIL — recopie-les au signe pres, on ne les devine pas :
%(travaux_ids)s

DEUX SORTES DE PAS, ET ELLES NE SE CONFONDENT PAS :
· un pas de TRAVAIL porte `lieu` — c'est la que tu cherches quelque chose ;
· un pas de MARCHE porte `de` et `a`, sans `lieu` — c'est toi qui te
  deplaces, son `resultat` peut valoir « — » et personne ne t'en tiendra
  rigueur. Un homme qui marche n'a pas echoue.

UNE PENSEE A CHAQUE PAS DE TRAVAIL. C'est la regle du jour et elle est
ferme : tout pas qui porte un `lieu` doit donner AU MOINS une pensee dans
`travaux`, avec sa `source` qui renvoie a ce pas-la. Un pas de travail sans
pensee est un pas SEC — tu es alle quelque part chercher quelque chose et tu
n'en rapportes rien —, et il se compte contre toi. Si la source n'a
reellement rien donne, ce n'est pas un pas sec : c'est une pensee qui dit ce
que tu as cherche, ou tu l'as cherche, et pourquoi ce n'etait pas la. Un
« non » etabli est un resultat ; un silence n'en est pas un.

Une matinee entiere dans vingt-deux ans de relevés donne beaucoup : ecris
autant de pensees qu'elle en a donnees. La rarete porte sur les AFFAIRES
touchees, jamais sur ce que tu en apprends.

LES BORNES, et elles sont dures :
· DEUX affaires touchees au plus dans la journee. Pas trois.
· PAS DE SOURCE, PAS DE PENSEE. Une pensee sans quelque chose que tu as
  reellement touche aujourd'hui n'existe pas. C'est la seule regle que ce
  rapport fait respecter mecaniquement.
· Tu inventes largement la MATIERE — des gens, des prix, des rancunes, un
  nom qu'on te donne au banc. Tu n'inventes JAMAIS le VERDICT : ce que la
  source pouvait rendre, elle le rend, et « rien » est une reponse honnete
  qui se journalise comme les autres.
· Une `conclusion` est de TA main, en toutes lettres, et elle part dans
  ton cahier. Tant qu'elle n'est pas mure, elle reste `null`.
· Rien de ce que tu n'as pas appris ne t'est connu. Ton brief est la
  totalite de ce que tu sais.

%(consigne)s""" % {
        "brief": brief, "depot": depot, "qui": qui, "etagere": etagere,
        "travaux_ids": travaux_ids(qui),
        "aujourdhui": json.dumps(
            dict(zip(("annee", "lune", "jour"), date_du_monde()))),
        "consigne": (u"CE QU'ON TE DEMANDE EN PLUS AUJOURD'HUI\n" + consigne
                     if consigne else u""),
    }


def poser_letagere(neutre, qui):
    """Materialise ses volumes en fichiers, un par volume, dans son dossier.

    C'EST LE SELECTEUR, ET IL EST PHYSIQUE. On aurait pu lui donner le
    lecteur en Bash et lui dire de s'en servir ; mais un outil qu'on autorise
    par motif de commande se contourne, et une consigne ne verrouille rien.
    La ou il travaille, il n'EXISTE que ce qu'il peut ouvrir. Le carnet de la
    reine n'est pas refuse : il n'est pas la.

    Effet de bord heureux : Grep sur ./livres/ lui donne la recherche
    plein-texte de son etagere, ce qui est exactement le geste d'un homme qui
    cherche dans ses registres — et qui evite les 547 000 jetons de
    etat/books.json, ou il s'est noye pendant huit minutes.
    """
    dossier = os.path.join(neutre, "livres")
    os.makedirs(dossier)
    n = 0
    for b in livre.etagere(qui):
        with io.open(os.path.join(dossier, "%s.txt" % b.get("id")), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(livre.rendre(b, large=True))
        n += 1
    return n


def appeler(qui, manuel, texte, sid, modele, minutes):
    """Tente --session-id ; retombe sur --resume si l'id a deja servi.

    LE MANUEL PASSE PAR UN FICHIER, PAS PAR LA LIGNE DE COMMANDE. Windows
    plafonne une ligne a 32 767 caracteres ; `docs/metier.md` en fait 32 000 a
    lui seul, et `--append-system-prompt` rendait un WinError 206 avant meme
    d'appeler. Le detour est meilleur que ce qu'il remplace : on ecrit un
    CLAUDE.md dans le repertoire neutre, et la decouverte automatique le
    ramasse. L'homme recoit donc SON manuel par le meme chemin que le MJ
    recoit le sien — c'est tout le sens d'avoir scinde le fichier.

    Le repertoire est hors du depot : la decouverte remonte l'arborescence, un
    sous-dossier de le-conseil2 aurait retrouve le manuel du MJ par-dessus.
    """
    neutre = tempfile.mkdtemp(prefix="depeche-%s-" % qui)
    poser_letagere(neutre, qui)
    with io.open(os.path.join(neutre, "CLAUDE.md"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(manuel)

    base = ["claude", "-p", "--output-format", "json", "--add-dir", RACINE,
            "--allowedTools"] + OUTILS + ["--permission-mode", "acceptEdits"]
    if modele:
        base += ["--model", modele]

    dernier = u""
    for tentative in (["--session-id", sid], ["--resume", sid]):
        # La mission passe par stdin pour la meme raison que le manuel par
        # un fichier : 11 ko d'argument s'ajoutent a tout le reste.
        r = subprocess.run(base + tentative, cwd=neutre,
                           input=texte.encode("utf-8"),
                           capture_output=True, timeout=minutes * 60)
        out = r.stdout.decode("utf-8", "replace")
        err = r.stderr.decode("utf-8", "replace")
        if "already in use" in out + err:
            continue  # la session existe deja : on la reprend en place
        if not out.strip():
            raise RuntimeError((err or "aucune sortie").strip()[:400])
        return json.loads(out)
    raise RuntimeError("ni --session-id ni --resume n'ont abouti : %s"
                       % dernier[:200])


def extraire_json(texte):
    """Sa reponse DEVRAIT etre du JSON nu. On tolere un bloc de code ou une
    phrase autour : un homme qui a bien travaille ne doit pas voir sa journee
    jetee pour trois backticks."""
    t = (texte or "").strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t).strip()
    try:
        return json.loads(t), None
    except Exception:
        pass
    d, f = t.find("{"), t.rfind("}")
    if d >= 0 and f > d:
        try:
            return json.loads(t[d:f + 1]), u"JSON degage d'un texte enrobe"
        except Exception as e:
            return None, u"illisible : %s" % e
    return None, u"aucun objet JSON dans la reponse"


def depecher(qui, consigne, modele, minutes, sec):
    date = date_du_monde()
    sid = identifiant_de_session(qui, date)
    brief = brief_de(qui)
    if not brief or "CONVOCATION" not in brief:
        print(u"  %-18s pas de dossier — %s" % (qui, (brief or u"")[:60]))
        return False
    manuel = manuel_de(qui)
    texte = mission(qui, brief, consigne)

    if sec:
        print(u"═" * 72)
        print(u"%s   session %s" % (qui, sid))
        print(u"  son CLAUDE.md  : %d caracteres (docs/metier.md + son nom)"
              % len(manuel))
        print(u"  mission        : %d caracteres" % len(texte))
        print(u"  outils         : %s" % " ".join(OUTILS))
        print(u"  lance depuis   : un repertoire neutre, --add-dir %s" % RACINE)
        print(u"─" * 72)
        print(texte)
        return True

    debut = time.time()
    try:
        rep = appeler(qui, manuel, texte, sid, modele, minutes)
    except Exception as e:
        print(u"  %-18s ECHEC — %s" % (qui, e))
        return False

    rapport, note = extraire_json(rep.get("result", ""))
    u_ = rep.get("usage", {}) or {}
    jetons = (u_.get("input_tokens", 0) + u_.get("cache_read_input_tokens", 0)
              + u_.get("cache_creation_input_tokens", 0))

    if rapport is None:
        brut = os.path.join(DEPOT_RAPPORTS, "%s.brut.txt" % qui)
        _poser(brut, rep.get("result", ""))
        print(u"  %-18s RAPPORT ILLISIBLE (%s) — brut dans %s"
              % (qui, note, os.path.relpath(brut, RACINE)))
        return False

    rapport.setdefault("qui", qui)
    rapport["_depeche"] = {
        "session": sid, "date_jeu": "%d.%d.%d" % date,
        "jetons": jetons, "secondes": round(time.time() - debut),
    }
    cible = os.path.join(DEPOT_RAPPORTS, "%s.json" % qui)
    _poser(cible, json.dumps(rapport, ensure_ascii=False, indent=2))

    p = sum(len(t.get("pensees", []) or []) for t in rapport.get("travaux", []) or [])
    print(u"  %-18s %2d pensee(s) · %2d etape(s) · %s · %5d j. · %3ds → %s%s"
          % (qui, p, len(rapport.get("journal", []) or []),
             u"conclusion" if rapport.get("conclusion") else u"—",
             jetons, rapport["_depeche"]["secondes"],
             os.path.relpath(cible, RACINE), u"  [%s]" % note if note else u""))
    return True


def _poser(chemin, contenu):
    d = os.path.dirname(chemin)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--qui", action="append", default=[],
                    help="un homme, repetable")
    ap.add_argument("--tous", action="store_true",
                    help="tous ceux qui doivent une journee")
    ap.add_argument("--salle", action="append", default=[],
                    help="toute une salle, PJ exclus — repetable")
    ap.add_argument("--salles", action="store_true",
                    help="dire quelles salles sont peuplees, et s'en tenir la")
    ap.add_argument("--autour", action="append", default=[],
                    help="tous ceux a portee de quelqu'un ou d'une salle")
    ap.add_argument("--rayon", type=float, default=10.0,
                    help="la portee en metres reels (defaut 10)")
    ap.add_argument("--front", type=int, default=4,
                    help="combien partent ensemble (1 = en file)")
    ap.add_argument("--mission", default="",
                    help="consigne du jour, en plus de son brief")
    ap.add_argument("--modele", default=None,
                    help="opus | sonnet | fable — defaut : celui de la session")
    ap.add_argument("--minutes", type=int, default=15,
                    help="delai avant abandon d'un homme")
    ap.add_argument("--sec", action="store_true",
                    help="montre tout, n'appelle rien, ne coute rien")
    a = ap.parse_args()

    if a.salles:
        pj = les_pj()
        print(u"LES SALLES PEUPLEES")
        for s, g in sorted(salles_peuplees().items(),
                           key=lambda x: (-len(x[1]), x[0] or u"")):
            if not s:
                continue
            hors = [q for q in g if q not in pj]
            print(u"  %-24s %2d a depecher%s" % (
                s, len(hors),
                u"   (%d PJ ecarte(s))" % (len(g) - len(hors))
                if len(g) - len(hors) else u""))
        return

    # On additionne les cibles, sans jamais retenir quelqu'un deux fois : la
    # meme personne peut etre nommee et se trouver dans une salle demandee.
    gens, vus = [], set()
    ecartes, aveugles = [], []
    autour = []
    for c in a.autour:
        d, e, av = dans_le_rayon(c, a.rayon)
        autour += d
        ecartes += e
        aveugles += av
        print(u"  a %g m de %s : %d homme(s)%s"
              % (a.rayon, c, len(d), u" + %d PJ" % len(e) if e else u""))
    if aveugles:
        # On ne tait jamais ce qu'on n'a pas pu voir.
        print(u"  sans adresse physique, donc hors du rayon quoi qu'il arrive :"
              u"\n    %s" % u", ".join(sorted(set(aveugles))))
    for source in (list(a.qui),
                   a_convoquer() if a.tous else [],
                   [q for s in a.salle for q in dans_la_salle(s)[0]],
                   autour):
        for q in source:
            if q not in vus:
                vus.add(q)
                gens.append(q)
    for s in a.salle:
        ecartes += dans_la_salle(s)[1]
    # Un PJ nomme a la main est ecarte comme les autres : la regle ne se
    # contourne pas en le demandant explicitement.
    pj = les_pj()
    nommes_pj = [q for q in gens if q in pj]
    gens = [q for q in gens if q not in pj]
    ecartes += nommes_pj
    if ecartes:
        print(u"  PJ ecarte(s), on ne les joue jamais : %s"
              % u", ".join(sorted(set(ecartes))))
    if not gens:
        raise SystemExit("Personne. --qui <homme>, --salle <salle>, --tous, "
                         "ou --salles pour voir.")

    date = date_du_monde()
    print(u"DEPECHER — le %d.%d.%d · %d homme(s)%s"
          % (date + (len(gens), u" · A SEC" if a.sec else u"")))
    ok = 0
    if a.sec or a.front <= 1 or len(gens) == 1:
        for qui in gens:
            if depecher(qui, a.mission, a.modele, a.minutes, a.sec):
                ok += 1
    else:
        # ILS PARTENT ENSEMBLE. Une journee d'homme se paie en minutes ; sept
        # en file en prendraient sept fois, et une salle entiere ne se
        # depecherait jamais. Ils n'ont rien a se dire, ne partagent aucun
        # fichier et n'ecrivent nulle part : chacun a son dossier, sa session
        # et son etagere, et le seul ecrivain reste ce processus-ci, a la fin.
        # `--front 1` rend la file a qui veut suivre un echec a la trace.
        import concurrent.futures as cf
        print(u"  (%d de front)" % min(a.front, len(gens)))
        with cf.ThreadPoolExecutor(max_workers=a.front) as pool:
            envoyes = {pool.submit(depecher, q, a.mission, a.modele,
                                   a.minutes, False): q for q in gens}
            for fini in cf.as_completed(envoyes):
                try:
                    if fini.result():
                        ok += 1
                except Exception as e:
                    print(u"  %-18s ECHEC — %s" % (envoyes[fini], e))
    if not a.sec:
        print(u"\n%d/%d rentres. Les rapports sont des PROPOSITIONS : "
              u"relis-les avant de verser." % (ok, len(gens)))
        print(u"  python scripts/verser_travaux.py  (ou a la main)")


if __name__ == "__main__":
    main()
