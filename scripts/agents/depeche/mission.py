# -*- coding: utf-8 -*-
"""MISSION — le texte de mission servi a l'homme, l'etagere posee dans sa
session, l'archive du prompt, et l'appel par la porte Claude/Codex.

L'HOMME TRAVAILLE AVEC ACCES AU DEPOT (decision du 31.8) : la sandbox des
calls n'a pas produit d'isolation utile et a ete retiree du runtime commun.
Les outils nommes par --tools restent son vocabulaire, pas une frontiere de
permission ;
  - LE HOOK-OREILLE EST MORT LE 31.8.2026 : le sursis qui passait un
    --settings explicite pour armer `parloir.py --ecouter` est leve. Un
    homme en session n'entend plus en cours de route — une parole qui lui
    arrive est un billet au canal de sa chambre, servi en percept a son
    prochain reveil (l'anachronisme absorbe, c'est le modele) ;
  - sa chambre et le depot restent montes ensemble : la premiere porte sa
    memoire, le second porte les sources et les portes qu'il doit employer.

CALL ET CAST (habitant.md §4) : on appelle quand on a besoin de la reponse
(attendre=True — le comportement historique), on depeche quand on lance une
vie (attendre=False — spawn detache, stdout dans fil/ de sa chambre, la
suite arrive par les canaux). Le defaut CLI reste le call tant que les
reveils-bancs 3-5 n'ont pas tourne.
"""
import io
import json
import os
import re
import tempfile
import time

from etat.expose import tables

from agents.depeche.brief import (RACINE, ETAT, DEPOT_RAPPORTS,
                                  livre,
                                  OUTILS, PARLOIR_PY, travaux_ids,
                                  SEL, lire, date_du_monde,
                                  identifiant_de_session, brief_de,
                                  feuille_de_route, travaux_ouverts_de,
                                  dossier_journee)
from agents.depeche.pas_de_tir import (poser_letagere,  # noqa: F401 — reexporte
                                       poser_la_memoire)
from agents.depeche.manuel import manuel_de, contexte_message
from agents.depeche.trous import ses_trous, sa_charge_ailleurs, on_lattend
from agents.depeche.retour import verser_sur_le_champ, _poser
from agents.depeche.chambre_locale import rendre as rendre_chambre_locale

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
    from agents.expose import chambre as _ch
    sa_chambre = _ch.chemin(qui).replace("\\", "/")
    chambre_locale = rendre_chambre_locale(_ch.chemin(qui))
    # Un seul MJ arbitre tous les gestes. Le lieu de l'homme reste une
    # information de fiction ; il ne fabrique plus une autorite runtime.
    arbitre = "mj"
    # LES BILLETS ENTRENT EN PERCEPT (habitant.md §3) : « Untel t'a écrit :
    # "…" » — jamais une invitation à ouvrir un fichier (2/2 ignorée aux
    # essais). Le curseur n'avance qu'au lancement réussi (marquer_lus, dans
    # depecher) : un départ raté ne mange pas les billets.
    billets = u""
    for b in _ch.non_lus(qui):
        d = b.get("date")
        if isinstance(d, dict):
            d = u"%s.%s.%s" % (d.get("annee", u"?"), d.get("lune", u"?"),
                               d.get("jour", u"?"))
        quand = u" (%s%s)" % (d or u"", u", %s" % b["heure"]
                              if b.get("heure") else u"")
        billets += (u"\n%s t'a écrit%s : « %s »\n"
                    % (b.get("de") or b.get("avec"),
                       quand if quand != u" ()" else u"",
                       (b.get("texte") or u"").strip()))
    if billets:
        billets = (u"\n## On t'a écrit\n" + billets +
                   u"\nCes mots te sont arrivés : ils font partie de ta journée."
                   u" Réponds-y à ta façon — dans tes gestes, tes cahiers, ou en"
                   u" notant ta réponse dans ta chambre pour la lui porter.\n")
    ajout = billets + ajout
    # LA OU IL S'ETAIT LAISSE : le mot qu'il s'est laisse hier (demain.md,
    # ecrit par depecher en fin de journee) se relit en tete de la journee
    # neuve — puis sera ecrase par la conclusion de ce soir. L'ordre :
    # injecte au reveil N+1, ecrase en fin de N+1.
    hier = u""
    chemin_demain = os.path.join(_ch.chemin(qui), "demain.md")
    if os.path.exists(chemin_demain):
        with io.open(chemin_demain, encoding="utf-8") as f:
            mot_dhier = f.read().strip()
        if mot_dhier:
            hier = (u"\n## Là où tu t'étais laissé\n\n" + mot_dhier +
                    u"\n\nC'est le mot que tu t'es laissé hier. Reprends de"
                    u" là, ou contredis-le — c'est le tien.\n")
    return u"""%(contexte)s

---

# Cette journée
%(hier)s
Ton contexte vivant est déjà auprès de toi. Le dépôt %(depot)s matérialise le
monde que tes yeux et tes mains peuvent consulter. Ton étagère se trouve dans
`./livres/`, un fichier par volume. `Read`, `Grep` et `Glob` servent à toucher
ces sources ; `Grep` localise un passage dans les grands journaux avant sa
lecture.

## Ton arbitre, et tes trois verbes

Ton MJ est `%(arbitre)s`. Quand ton geste engage le monde, tu le
lui adresses par l'un des trois verbes — le verdict revient comme retour de
commande, dans le fil de ta pensée :

    python %(parloir)s --tenter --de %(qui)s --a %(arbitre)s "je pars sur mon cheval"
    python %(parloir)s --faire --de %(qui)s --a %(arbitre)s "je déplace ce livre"
    python %(parloir)s --demander --de %(qui)s --a %(arbitre)s "l'histoire de cette tour ?"

TENTER : tu tentes, l'arbitre tranche en coulisse. FAIRE : tu proposes un
changement au monde. DEMANDER : tu demandes ce que le monde dit — la réponse
vient des registres seuls.

Écrire à quelqu'un, c'est le billet : il le lira à son réveil, et ton mot le
réveille s'il dort.

    python %(parloir)s --dire --de %(qui)s --a <untel> "..."

## Ta chambre

Ta chambre est le dossier `%(chambre)s` — elle est à toi, et à toi seul.

- `claude.md` : ta manière, de ta main. Amende-le quand ta journée te contredit.
- `brouillons/` : ce qui mûrit. Rature, reprends, ne rends que le propre.
- `fil/` : les traces de tes journées passées — relis-les si un souvenir te manque.
- `relations/<untel>/claude.md` : ce que TU retiens de chacun.

%(chambre_locale)s

Rien dans ta chambre ne fait foi sur le monde : elle est ta mémoire et ton
caractère. Ce qui doit devenir vrai passe par tes gestes dans la journée.

## Ton retour

Plus de formulaire : ta journée EST ton retour. Ce que tu apprends, écris-le
dans tes cahiers et ta chambre à mesure ; ce que tu conclus, note-le où tu
sauras le retrouver. Ta dernière réponse est ta conclusion à toi — ce que ta
journée a changé, et ce que tu comptes faire ensuite, dit à ta façon, en
quelques lignes au plus. Tu te la laisses comme on se laisse un mot sur sa
table : c'est elle que tu retrouveras à ton prochain réveil.

Tes affaires ouvertes, pour mémoire :

%(travaux_ids)s
%(ajout)s""" % {
        "chambre": sa_chambre,
        "chambre_locale": chambre_locale.rstrip(),
        "arbitre": arbitre,
        "hier": hier,
        "depot": depot,
        "parloir": PARLOIR_PY,
        "qui": qui,
        "aujourdhui": json.dumps(aujourdhui, ensure_ascii=False),
        "travaux_ids": travaux_ids(qui),
        "ajout": ajout,
        "contexte": contexte_message(qui, contexte).strip(),
    }


DEPECHES = os.path.join(ETAT, "depeches")


def archiver_le_prompt(qui, sid, manuel, texte):
    """Garde sur disque CE QUI A REELLEMENT ETE INJECTE, avant l'appel.

    Le manuel partait dans un `mkdtemp` que personne ne relit et que le systeme
    balaie : on pouvait donc lire toute la journee d'un homme sans jamais savoir
    ce qu'il avait recu en entrant. La question « il est coherent » ou « on le
    re-briefe a chaque reveil » n'avait pas de piece pour la trancher.

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


def appeler(qui, manuel, texte, sid, modele, minutes, attendre=True):
    """Appelle la porte globale ; cree ou reprend la session logique.

    LE MANUEL PASSE PAR UN FICHIER. Windows plafonne une ligne a 32 767
    caracteres : la porte ecrit system-prompt.md pour Claude ou AGENTS.md
    pour Codex, dans le meme repertoire neutre.

    Le repertoire est hors du depot : la decouverte remonte l'arborescence, un
    sous-dossier de le-conseil2 aurait retrouve le manuel du MJ par-dessus.
    SA CHAMBRE est montee en plus du depot (chambre.ouvrir + --add-dir) :
    l'habitant ecrit chez lui, et chez lui seulement — rien dans chambres/
    ne fait foi, la porte-etat garde le reste.

    attendre=False est le CAST : spawn detache (Popen sans wait), stdout vers
    un log dans fil/ de sa chambre, retour immediat {cast, log, session}. Un
    Le CAST passe par un worker detache. Il prend le meme verrou et sait donc
    reprendre une session deja nee, comme le CALL.

    PLUS D'OREILLE : le hook-parloir est mort le 31.8.2026. La session ne
    recoit aucun --settings — une parole qui arrive pendant sa journee est
    un billet au canal, servi en percept a son prochain reveil.
    """
    from agents.expose import chambre as _ch
    sa_chambre = _ch.ouvrir(qui)
    # SOUS CLAUDE, IL TRAVAILLE CHEZ LUI. Le `mkdtemp` par depeche avait deux
    # motifs ecrits, et un seul tenait. « Le selecteur est physique » est faux :
    # `--add-dir RACINE` monte le depot entier, et hann-bourbe a lu
    # `chambres/hann-bourbe/../` dans sa session du 31.8. Ne restait que la
    # decouverte de CLAUDE.md — un sous-dossier du depot aurait colle le
    # manuel du MJ par-dessus le sien.
    #
    # SA CHAMBRE REGLE CE MOTIF-LA SANS LE PRIX. Elle porte son propre
    # AGENTS.md/CLAUDE.md, donc la decouverte trouve LE SIEN et s'arrete la.
    # Et le prix du neutre etait reel : ONZE dossiers de projet pour le seul
    # hann-bourbe, un par depeche, chacun avec un transcript orphelin — le
    # `--session-id` promet une continuite que le cwd jetable defait. Chez
    # lui, `livres/` et `ma-memoire/` persistent d'une journee a l'autre, ce
    # qui est exactement ce qu'on veut d'un homme qui a une memoire.
    #
    # CODEX GARDE LE NEUTRE : son manuel s'ecrit en AGENTS.md a la racine du
    # cwd, et l'ecrire dans sa chambre ecraserait celui qu'on vient de dire
    # sien. Un fournisseur, un logement.
    from agents.expose import runtime as _rt
    sous_claude = (_rt.configuration() or {}).get("fournisseur") == "claude"
    neutre = (sa_chambre if sous_claude
              else tempfile.mkdtemp(prefix="depeche-%s-" % qui))
    # SON NOM DANS SON ENVIRONNEMENT. `LE_CONSEIL_QUI` existait comme
    # convention et n'etait JAMAIS posee — une lecture dans tout le depot,
    # zero ecriture. Sans elle, le journal des affaires ne peut pas dire QUI
    # a ferme une action : il ne verrait qu'un nom d'outil.
    poser_letagere(neutre, qui)
    # Ce que le message ne porte plus doit exister la ou il pointe.
    poser_la_memoire(neutre, qui)
    archiver_le_prompt(qui, sid, manuel, texte)
    from agents.expose import runtime as agent_runtime
    parametres = {
        "role": qui, "manuel": manuel, "message": texte,
        # PAS D'EXPIRATION (31.8) : `minutes=None` -> `timeout=None`, et le
        # processus rend la main quand il a fini. Le plafond ne protegeait
        # de rien et coupait des journees entieres au milieu.
        "session_id": sid, "modele": modele,
        "timeout": (minutes * 60) if minutes else None,
        "cwd": neutre, "add_dirs": [RACINE, sa_chambre],
        "tools": OUTILS, "reprendre": None,
        "env": {"LE_CONSEIL_QUI": str(qui)},
    }

    if not attendre:
        # LE CAST — on lance une vie, on ne la regarde pas vivre. La mission
        # part par un fichier tenu ouvert en stdin ; le fil de sa chambre
        # recoit la sortie, datee, relisible.
        horo = time.strftime("%Y%m%d-%H%M%S")
        log = os.path.join(sa_chambre, "fil", "depeche-%s.log" % horo)
        etiquette = u"%d.%d.%d" % date_du_monde()
        return agent_runtime.lancer_cast(
            log, trace={"qui": qui, "etiquette": etiquette}, **parametres)

    return agent_runtime.appeler(**parametres)


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


def depecher(qui, consigne, modele, minutes, sec, attendre=True):
    date = date_du_monde()
    sid = identifiant_de_session(qui, date)
    brief = brief_de(qui)
    # LA GARDE PORTE SUR CE QUI EMPECHE SA JOURNEE, pas sur un mot du dossier.
    # Elle cherchait « CONVOCATION », que l'ancien brief tenait de
    # `convoquer.py` ; le brief neuf calcule les creux lui-meme et ne l'ecrit
    # plus — la garde etait donc toujours vraie et PLUS PERSONNE NE PARTAIT.
    # Les deux vrais motifs sont les deux sorties precoces de `brief_de`.
    empeche = None
    # UN SIEGE OCCUPE N'EST PAS DEPECHE : quand un joueur incarne cet homme,
    # sa journee est vecue par le siege — une depeche parallele donnerait
    # deux volontes au meme corps le meme jour. L'anachronisme tolere le
    # desordre des dates, pas la double volonte (decision du 30.8).
    joueurs = tables.lire(os.path.join(ETAT, "joueurs.json"), [])
    if isinstance(joueurs, dict):
        joueurs = joueurs.get("joueurs", [])
    for j in joueurs or []:
        if isinstance(j, dict) and j.get("occupe") and not j.get("regie") \
                and (j.get("personnage_id") or j.get("id")) == qui:
            empeche = u"son siege est occupe — un joueur l'incarne"
            break
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
        # LA LIGNE DISAIT « repertoire neutre » QUOI QU'IL ARRIVE — un texte
        # fige, qui ment depuis que le cwd depend du fournisseur. Un `--sec`
        # sert a voir ce qui VA se passer : il rend le vrai chemin.
        from agents.expose import runtime as _rt2
        from agents.expose import chambre as _ch2
        _claude = (_rt2.configuration() or {}).get("fournisseur") == "claude"
        print(u"  lance depuis   : %s"
              % (_ch2.chemin(qui) if _claude
                 else u"un repertoire neutre (jetable)"))
        print(u"  --add-dir      : %s" % RACINE)
        print(u"─" * 72)
        print(texte)
        return True

    debut = time.time()
    try:
        rep = appeler(qui, manuel, texte, sid, modele, minutes,
                      attendre=attendre)
    except Exception as e:
        print(u"  %-18s ECHEC — %s" % (qui, e))
        return False

    # LE LANCEMENT A PRIS : son reveil a tout vu — les billets sont lus.
    # Avant ce point (echec du depart), les curseurs n'ont pas bouge.
    from agents.expose import chambre as _ch
    _ch.marquer_lus(qui)

    if not attendre:
        # Parti en cast : sa journee vit sans nous. Pas de rapport a parser —
        # le retour d'une journee, c'est l'etat de sa chambre plus ses
        # versements (habitant.md §1) ; son log dit ou la regarder.
        print(u"  %-18s parti detache → %s"
              % (qui, os.path.relpath(rep["log"], RACINE)))
        return True

    # LE VECU AU FIL, TOUJOURS : le lanceur le depose explicitement, sans
    # faire dependre la memoire de l'homme d'un hook de fournisseur.
    from agents.expose import trace as _tr
    try:
        _tr.deposer(qui, sid, etiquette=u"%d.%d.%d" % date,
                    transcript=rep.get("transcript_path"),
                    provider=rep.get("provider"))
    except Exception:
        pass  # un fil qui manque ne vaut pas une journee perdue

    rapport, note = extraire_json(rep.get("result", ""))
    u_ = rep.get("usage", {}) or {}
    jetons = (u_.get("input_tokens", 0) + u_.get("cache_read_input_tokens", 0)
              + u_.get("cache_creation_input_tokens", 0))

    if rapport is None:
        # PLUS UN ECHEC : le gabarit JSON est retire (habitant.md pas 3).
        # Sa derniere reponse est une phrase d'homme ; sa journee vit dans
        # sa chambre (fil/, brouillons/, cahiers) et ses versements.
        phrase = (rep.get("result") or u"").strip()
        brut = os.path.join(DEPOT_RAPPORTS, "%s.brut.txt" % qui)
        _poser(brut, phrase)
        # LE MOT SUR SA TABLE : sa conclusion s'ecrit dans sa chambre,
        # ECRASEE a chaque journee — c'est le mot le plus recent qui compte,
        # le fil garde l'historique. Elle sera reinjectee a son prochain
        # reveil (« La ou tu t'etais laisse », mission()).
        if phrase:
            with io.open(os.path.join(_ch.chemin(qui), "demain.md"), "w",
                         encoding="utf-8", newline="\n") as f:
                f.write(phrase + u"\n")
        print(u"  %-18s %5d j. · %3ds — sa phrase : %s"
              % (qui, jetons, round(time.time() - debut),
                 re.sub(r"\s+", u" ", phrase)[:160] or u"(muette)"))
        return True

    rapport.setdefault("qui", qui)
    rapport["_depeche"] = {
        "session": sid, "date_jeu": "%d.%d.%d" % date,
        "jetons": jetons, "secondes": round(time.time() - debut),
    }
    cible = os.path.join(DEPOT_RAPPORTS, "%s.json" % qui)
    tables.ecrire(cible, rapport)
    verse = verser_sur_le_champ(rapport, qui, date)

    p = sum(len(t.get("pensees", []) or []) for t in rapport.get("travaux", []) or [])
    print(u"  %-18s %2d pensee(s) [%d versee(s)] · %2d etape(s) · %s · %5d j. · %3ds → %s%s"
          % (qui, p, verse, len(rapport.get("journal", []) or []),
             u"conclusion" if rapport.get("conclusion") else u"—",
             jetons, rapport["_depeche"]["secondes"],
             os.path.relpath(cible, RACINE), u"  [%s]" % note if note else u""))
    return True
