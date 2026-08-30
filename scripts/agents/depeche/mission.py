# -*- coding: utf-8 -*-
"""MISSION — le texte de mission servi a l'homme, l'etagere et le parloir
poses dans sa session, l'archive du prompt, et l'appel claude -p.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time

from etat.expose import tables

from agents.depeche.brief import (RACINE, ETAT, DEPOT_RAPPORTS,
                                  livre,
                                  OUTILS, PARLOIR_PY, travaux_ids,
                                  OUTIL_PARLOIR, SEL, lire, date_du_monde,
                                  identifiant_de_session, brief_de,
                                  feuille_de_route, travaux_ouverts_de,
                                  dossier_journee)
from agents.depeche.manuel import (manuel_de, contexte_message,
                                   message_tentative, manuel_narrateur_local,
                                   memoire_activation, etagere_systeme)
from agents.depeche.narrateur import (contrat_rapport_narrateur,
                                      _mission_historique)
from agents.depeche.trous import ses_trous, sa_charge_ailleurs, on_lattend
from agents.depeche.retour import (verser_sur_le_champ, proposer_la_tete,
                                   _poser)

def mission(qui, brief, consigne, contexte=None):
    """Donne l'interface du jour ; l'identité et le contexte vivent au système."""
    depot = os.path.join(RACINE, "").replace("\\", "/")
    aujourdhui = dict(zip(("annee", "lune", "jour"), date_du_monde()))
    contexte = contexte or dossier_journee(qui, brief)
    ajout = (u"\n## L'élan particulier de ce jour\n\n" + consigne.strip() + u"\n"
             if consigne and consigne.strip() else u"")
    # Ses cahiers d'abord — c'est ce dont il répond. Puis ce qui tombe sur lui
    # de dehors, et qu'aucun chemin ne lui portait.
    ajout = ses_trous(qui) + sa_charge_ailleurs(qui) + on_lattend(qui) + ajout
    return u"""%(contexte)s

---

# Cette journée

Ton contexte vivant est déjà auprès de toi. Le dépôt %(depot)s matérialise le
monde que tes yeux et tes mains peuvent consulter. Ton étagère se trouve dans
`./livres/`, un fichier par volume. `Read`, `Grep` et `Glob` servent à toucher
ces sources ; `Grep` localise un passage dans les grands journaux avant sa
lecture.

Le parloir apporte une parole au milieu de ton travail. Lorsqu'une parole y
arrive, cette commande porte ta réponse dans la pièce :

    python %(parloir)s --dire --de %(qui)s --a mj "..."

Puis ta journée continue depuis ce nouvel échange.

## Ton rapport

Ta dernière réponse prend exactement la forme de cet objet JSON :

{
  "qui": "%(qui)s",
  "journal": [
    {
      "heure": "7h00",
      "duree": 20,
      "lieu": "lieu du geste",
      "quoi": "geste accompli, à la troisième personne",
      "resultat": "fait obtenu ou absence précisément établie"
    }
  ],
  "travaux": [
    {
      "travail_id": "identifiant exact donné plus bas",
      "dernier_travail": %(aujourdhui)s,
      "pensees": [
        {
          "date": %(aujourdhui)s,
          "source": "personne, lieu, objet ou registre touché",
          "texte": "ce que cette rencontre a appris"
        }
      ],
      "conclusion": null
    }
  ],
  "cahier2": [
    {
      "livre": "...",
      "table": "...",
      "ligne": "...",
      "colonne": "...",
      "valeur": "..."
    }
  ]
}

Une marche porte `de` et `a` à la place de `lieu`. Une découverte porte sa
source et sa date. Une conclusion mûre prend place dans l'affaire qu'elle
conclut. Les changements de registre prennent leurs coordonnées dans
`cahier2`.

Tes identifiants de travail :

%(travaux_ids)s
%(ajout)s""" % {
        "depot": depot,
        "parloir": PARLOIR_PY,
        "qui": qui,
        "aujourdhui": json.dumps(aujourdhui, ensure_ascii=False),
        "travaux_ids": travaux_ids(qui),
        "ajout": ajout,
        "contexte": contexte_message(qui, contexte).strip(),
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


def poser_le_parloir(neutre, qui):
    """Le hook qui lui met une oreille. Rend le chemin du fichier de reglages.

    UN HOOK N'EST PAS UNE HORLOGE : il bat apres chaque appel d'OUTIL, et
    seulement la. Un homme qui reflechit longtemps sans rien ouvrir n'entend
    rien pendant ce temps. En pratique cela suffit — sa journee entiere est
    faite de Read et de Grep —, mais c'est la limite du procede et il faut la
    connaitre avant de s'etonner d'un silence.

    Le matcher est `*` a dessein : on veut l'entendre au plus tot, pas
    seulement quand il lit. Le cout est nul tant que personne ne lui parle —
    `parloir.py --ecouter` n'ecrit RIEN sans message neuf, et un hook muet
    n'entre pas dans le contexte.
    """
    d = os.path.join(neutre, ".claude")
    os.makedirs(d, exist_ok=True)
    cible = os.path.join(d, "settings.json")
    py = sys.executable.replace("\\", "/")
    ecoute = "%s %s --ecouter --qui %s --hook" % (py, PARLOIR_PY, qui)
    with io.open(cible, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "env": {"LE_CONSEIL_QUI": qui},
            "hooks": {
                "PostToolUse": [{"matcher": "*", "hooks": [
                    {"type": "command", "command": ecoute, "timeout": 15}]}],
            }}, ensure_ascii=False, indent=2))
    return cible


DEPECHES = os.path.join(ETAT, "depeches")


def archiver_le_prompt(qui, sid, manuel, texte):
    """Garde sur disque CE QUI A REELLEMENT ETE INJECTE, avant l'appel.

    Le manuel partait dans un `mkdtemp` que personne ne relit et que le systeme
    balaie : on pouvait donc lire toute la journee d'un homme sans jamais savoir
    ce qu'il avait recu en entrant. La question « il est coherent » ou « on le
    re-briefe a chaque reveil » n'avait pas de piece pour la trancher.

    La boucle d'activation, elle, archive deja son `system_prompt` dans
    `etat/activations/` — c'est le meme geste, porte au chemin manuel, qui
    etait le seul des deux a n'avoir aucune trace.

    On ecrit AVANT l'appel et non apres : une session qui meurt en cours doit
    laisser son prompt, sinon il manque exactement quand il sert le plus.
    """
    horo = "%s-%06d" % (time.strftime("%Y%m%d-%H%M%S"),
                        int(time.time() * 1e6) % 1000000)
    return tables.ecrire(os.path.join(DEPECHES, "%s-%s.json" % (horo, qui)), {
        "qui": qui,
        "session": sid,
        "date_jeu": "%s.%s.%s" % date_du_monde(),
        "system_prompt": manuel,
        "mission": texte,
    }, indent=1)


def appeler(qui, manuel, texte, sid, modele, minutes, parloir=True):
    """Tente --session-id ; retombe sur --resume si l'id a deja servi.

    LE MANUEL PASSE PAR --system-prompt-file. Windows plafonne une ligne a
    32 767 caracteres ; le fichier garde donc le prompt hors des arguments,
    mais sans le faire passer pour un CLAUDE.md decouvert automatiquement.
    L'homme recoit explicitement SON manuel systeme et n'herite plus de celui
    du MJ lorsque le depot est rouvert par --add-dir.

    Le repertoire est hors du depot : la decouverte remonte l'arborescence, un
    sous-dossier de le-conseil2 aurait retrouve le manuel du MJ par-dessus.
    """
    neutre = tempfile.mkdtemp(prefix="depeche-%s-" % qui)
    poser_letagere(neutre, qui)
    prompt_systeme = os.path.join(neutre, "system-prompt.md")
    with io.open(prompt_systeme, "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(manuel)
    archiver_le_prompt(qui, sid, manuel, texte)
    # LE FIL PORTE LA SESSION, PAS L'HOMME. Deux dépêches du même acteur
    # peuvent tourner en même temps — la mienne et celle de la boucle
    # d'activation, le 9 août — et sous un seul nom elles se volaient les
    # messages. Le jeton vient de l'identifiant de session : deterministe,
    # donc retrouvable, et distinct par instance.
    identite = qui
    if parloir:
        from agents.expose import parloir as _p
        identite = _p.ouvrir_instance(qui, sid.replace("-", "")[:8],
                                      os.path.basename(neutre), minutes)
    reglages = poser_le_parloir(neutre, identite) if parloir else None

    outils = list(OUTILS) + ([OUTIL_PARLOIR] if parloir else [])
    base = ["claude", "-p", "--output-format", "json",
            "--system-prompt-file", prompt_systeme,
            "--add-dir", RACINE, "--allowedTools"] + outils
    if reglages:
        # Le hook doit etre charge sans dependre de la reconnaissance du
        # repertoire neutre comme projet.
        base += ["--settings", reglages]
    base += ["--permission-mode", "acceptEdits"]
    if modele:
        base += ["--model", modele]

    dernier = u""
    try:
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
    finally:
        # SA SESSION EST FINIE : ELLE N'ECOUTE PLUS. Sans ce `finally`, une
        # depeche morte laisse son instance ouverte, et l'on continue de lui
        # parler dans un fil que plus personne ne lit — trois orphelines
        # tramaient deja apres les essais du 9 aout.
        if parloir and identite != qui:
            try:
                from agents.expose import parloir as _p
                _p.fermer_instance(identite)
            except Exception:
                pass


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
    # LA GARDE PORTE SUR CE QUI EMPECHE SA JOURNEE, pas sur un mot du dossier.
    # Elle cherchait « CONVOCATION », que l'ancien brief tenait de
    # `convoquer.py` ; le brief neuf calcule les creux lui-meme et ne l'ecrit
    # plus — la garde etait donc toujours vraie et PLUS PERSONNE NE PARTAIT.
    # Les deux vrais motifs sont les deux sorties precoces de `brief_de`.
    empeche = None
    if not brief:
        empeche = u"aucun dossier"
    elif u"Aucune tete dans intentions.json" in brief:
        empeche = u"pas de tete dans intentions.json"
    elif u"AUCUN CREUX" in brief:
        empeche = u"aucun creux aujourd'hui — il travaille, il ne pense pas"
    if empeche:
        print(u"  %-18s ne part pas — %s" % (qui, empeche))
        return False
    contexte = dossier_journee(qui, brief)
    manuel = manuel_de(qui, mode="journee", contexte=contexte)
    texte = mission(qui, brief, consigne, contexte=contexte)

    if sec:
        print(u"═" * 72)
        print(u"%s   session %s" % (qui, sid))
        print(u"  prompt système : %d caractères (nouvelle version seule)"
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
    tables.ecrire(cible, rapport)
    verse = verser_sur_le_champ(rapport, qui, date)
    proposer_la_tete(rapport, qui, date, sid)

    p = sum(len(t.get("pensees", []) or []) for t in rapport.get("travaux", []) or [])
    print(u"  %-18s %2d pensee(s) [%d versee(s)] · %2d etape(s) · %s · %5d j. · %3ds → %s%s"
          % (qui, p, verse, len(rapport.get("journal", []) or []),
             u"conclusion" if rapport.get("conclusion") else u"—",
             jetons, rapport["_depeche"]["secondes"],
             os.path.relpath(cible, RACINE), u"  [%s]" % note if note else u""))
    return True

