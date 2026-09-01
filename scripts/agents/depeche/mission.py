# -*- coding: utf-8 -*-
"""MISSION — le texte de mission servi a l'homme, l'archive du prompt, et
l'appel par la porte Claude/Codex.

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
                                  OUTILS, PARLOIR_PY, travaux_ids,
                                  SEL, lire, date_du_monde,
                                  id_item_affaire, identifiant_de_session, brief_de,
                                  feuille_de_route, travaux_ouverts_de,
                                  dossier_journee)
from agents.depeche.pas_de_tir import poser_la_memoire
from agents.depeche.manuel import manuel_de, contexte_message
from agents.depeche.contexte_affaire import focaliser
from agents.depeche.trous import ses_trous, sa_charge_ailleurs, on_lattend
from agents.depeche.retour import verser_sur_le_champ, _poser
from agents.depeche.chambre_locale import rendre as rendre_chambre_locale
import documents_maison

MODES_BRIEF = ("journee", "reponse", "discussion")


def instructions_mode(mode, beats_jump=False):
    """Ajoute les indications de transport propres au mode."""
    if mode not in MODES_BRIEF:
        raise ValueError("mode de brief inconnu : %s" % mode)
    if mode == "reponse":
        base = u"""# Mode réponse

Consulte le fichier `messages-au-joueur.md` indiqué sous `# Ta chambre` si une
entrée correspond à ce destinataire, à ce contexte ou à cette ref. Tu peux
partir de ce texte, le confronter aux faits utiles, puis répondre avec ta propre
compréhension.
"""
        if not beats_jump:
            return base
        return base + u"""

## Beats d'attente du Jump

Rends un objet JSON nu : `reponse` contient ta réponse normale et
`beats_attente` contient zéro à trois petits battements que le MJ pourra
pousser pendant qu'il attend les autres hommes. Chaque beat a `type`
(`replique`, `geste` ou `recit`), `texte`, `duree` et `noeuds` (au moins un
identifiant exact du sous-graphe fourni dans la demande). Tu es l'auteur de
chaque parole ou geste. Appuie chaque détail sur les faits disponibles,
consacre ces beats à l'attente dans ce sous-graphe et porte le verdict dans la
réponse finale."""
    if mode == "discussion":
        return u"""# Mode discussion

Consulte le fichier `messages-au-joueur.md` indiqué sous `# Ta chambre` si une
entrée correspond à ce destinataire, à ce contexte ou à cette ref. Tu peux
partir de ce texte, le confronter aux faits utiles, puis répondre avec ta propre
compréhension.
"""
    return None


def cible_rapport(qui, contexte_id=None, brut=False):
    """Le depot historique, sans collision entre deux affaires d'un homme."""
    nom = str(qui)
    if contexte_id is not None:
        nom += "--contexte-" + id_item_affaire(contexte_id)
    return os.path.join(DEPOT_RAPPORTS,
                        nom + (".brut.txt" if brut else ".json"))


def mission(qui, brief, consigne, contexte=None, contexte_id=None, ref=None,
            mode="journee", billet_de=None, beats_jump=False):
    """Donne l'interface du jour ; l'identité et le contexte vivent au système."""
    court = instructions_mode(mode, beats_jump=beats_jump)
    if contexte_id is not None:
        contexte_id = id_item_affaire(contexte_id)
    aujourdhui = dict(zip(("annee", "lune", "jour"), date_du_monde()))
    contexte = contexte or dossier_journee(qui, brief)
    if contexte_id is not None and not contexte.get("contexte_affaire"):
        contexte = focaliser(contexte, contexte_id)
    titre_consigne = (u"La demande" if court else
                      u"L'élan particulier de ce jour")
    ajout = (u"\n## %s\n\n%s\n" % (titre_consigne, consigne.strip())
             if consigne and consigne.strip() else u"")
    if contexte_id is not None:
        ajout = (u"\n## Le fil de cette affaire\n\n"
                 u"L'item d'affaire `%s` donne son identité à cet appel, à ta "
                 u"session, à ton vécu et à ton mot de reprise.\n" % contexte_id
                 + ajout)
    if ref:
        ajout = (u"\n## Origine de cet appel\n\n"
                 u"Le message joueur qui a ouvert cet appel porte la ref "
                 u"`%s`. Conserve-la avec toute réponse liée à ce message.\n"
                 % ref) + ajout
    # Ses cahiers d'abord — c'est ce dont il répond. Puis ce qui tombe sur lui
    # de dehors, et qu'aucun chemin ne lui portait.
    if mode == "journee" and contexte_id is None:
        ajout = ses_trous(qui) + sa_charge_ailleurs(qui) + on_lattend(qui) + ajout
    from agents.expose import chambre as _ch
    sa_chambre = _ch.chemin(qui).replace("\\", "/")
    if mode != "journee":
        chambre_locale = u""
    elif contexte_id is None:
        chambre_locale = rendre_chambre_locale(_ch.chemin(qui))
    else:
        focus = contexte["contexte_affaire"]
        volume = (focus.get("volumes") or [None])[0]
        source = u""
        if volume:
            canonique = documents_maison.sources_livres(ETAT).get(volume)
            _maison, autorises = documents_maison.documents_pour(ETAT, qui)
            if canonique and canonique in autorises:
                source = u" Le cahier source est `%s`." % canonique.replace("\\", "/")
        chambre_locale = (u"## Le dossier local de cet item\n\n"
                           u"Ton fil propre est `%s`.%s Consacre cet appel à "
                           u"ce fil, à son cahier source et à la chaîne de "
                           u"l'état qu'il sert.\n" % (
                               _ch.fil(qui, contexte_id).replace("\\", "/"),
                               source))
    # LES BILLETS ENTRENT EN PERCEPT (habitant.md §3) : « Untel t'a écrit :
    # "…" » — jamais une invitation à ouvrir un fichier (2/2 ignorée aux
    # essais). Le curseur n'avance qu'au lancement réussi (marquer_lus, dans
    # depecher) : un départ raté ne mange pas les billets.
    billets = u""
    non_lus = _ch.non_lus(qui) if mode == "journee" else []
    if contexte_id is not None:
        non_lus = [b for b in non_lus
                   if str(b.get("contexte_id") or "") == str(contexte_id)]
    if billet_de is not None:
        non_lus = [b for b in non_lus if b.get("de") == billet_de]
    for b in non_lus:
        d = b.get("date")
        if isinstance(d, dict):
            d = u"%s.%s.%s" % (d.get("annee", u"?"), d.get("lune", u"?"),
                               d.get("jour", u"?"))
        quand = u" (%s%s)" % (d or u"", u", %s" % b["heure"]
                              if b.get("heure") else u"")
        provenance = []
        if b.get("contexte_id") is not None:
            provenance.append(u"contexte %s" % b["contexte_id"])
        if b.get("ref"):
            provenance.append(u"ref %s" % b["ref"])
        provenance = (u" [%s]" % u" · ".join(provenance)
                      if provenance else u"")
        billets += (u"\n%s t'a écrit%s%s : « %s »\n"
                    % (b.get("de") or b.get("avec"),
                       quand if quand != u" ()" else u"",
                       provenance,
                       (b.get("texte") or u"").strip()))
    if billets:
        billets = (u"\n## On t'a écrit\n" + billets +
                   u"\nCes mots te sont arrivés : ils font partie de ta journée."
                   u" Ce qu'ils changent dans tes gestes, tes pensées ou tes"
                   u" relations dépend de tes propres raisons.\n")
    ajout = billets + ajout
    if court:
        return u"""%(contexte)s

---

%(instructions)s
%(ajout)s""" % {
            "contexte": contexte_message(qui, contexte).strip(),
            "instructions": court,
            "ajout": ajout,
        }
    # LA OU IL S'ETAIT LAISSE : le mot qu'il s'est laisse hier (demain.md,
    # ecrit par depecher en fin de journee) se relit en tete de la journee
    # neuve — puis sera ecrase par la conclusion de ce soir. L'ordre :
    # injecte au reveil N+1, ecrase en fin de N+1.
    hier = u""
    chemin_demain = (os.path.join(_ch.chemin(qui), "demain.md")
                     if contexte_id is None else
                     os.path.join(_ch.fil(qui, contexte_id), "demain.md"))
    if os.path.exists(chemin_demain):
        with io.open(chemin_demain, encoding="utf-8") as f:
            mot_dhier = f.read().strip()
        if mot_dhier:
            hier = (u"\n## Là où tu t'étais laissé\n\n" + mot_dhier +
                    u"\n\nC'est le mot que tu t'es laissé hier. Reprends de"
                    u" là, ou transforme-le — c'est le tien.\n")
    return u"""%(contexte)s

---

# Cette journée
%(hier)s
Ton contexte vivant est déjà auprès de toi. Les documents de ta maison sont
énumérés dans ton prompt système. `Read`, `Grep` et `Glob` servent à les
consulter directement à leur adresse canonique.

Écrire à quelqu'un, c'est le billet : il le lira à son réveil, et ton mot le
réveille s'il dort.

    python %(parloir)s --dire --de %(qui)s --a <untel> "..."

## Ta chambre

Ta chambre est le dossier `%(chambre)s` — elle est à toi, et à toi seul.

- `claude.md` : ta manière, de ta main. Amende-le à mesure que ta journée transforme ta manière.
- `brouillons/` : ce qui mûrit. Rature, reprends et rends le propre.
- `fil/` : les traces de tes journées passées — relis-les pour raviver un souvenir.
- `relations/<untel>/claude.md` : ce que TU retiens de chacun.

%(chambre_locale)s

Ta chambre porte ta mémoire et ton caractère. Tes gestes dans la journée
inscrivent leurs résultats dans le monde par les portes adaptées.

## Ton retour

Ta journée EST ton retour. Ce que tu apprends, écris-le
dans tes cahiers et ta chambre à mesure ; ce que tu conclus, note-le où tu
sauras le retrouver. Ta dernière réponse est ta conclusion à toi — ce que ta
journée a changé, et ce que tu comptes faire ensuite, dit à ta façon, en
quelques lignes claires. Tu te la laisses comme on se laisse un mot sur sa
table : c'est elle que tu retrouveras à ton prochain réveil.

Tes affaires ouvertes, pour mémoire :

%(travaux_ids)s
%(ajout)s""" % {
        "chambre": sa_chambre,
        "chambre_locale": chambre_locale.rstrip(),
        "hier": hier,
        "parloir": PARLOIR_PY,
        "qui": qui,
        "aujourdhui": json.dumps(aujourdhui, ensure_ascii=False),
        "travaux_ids": (travaux_ids(qui) if contexte_id is None else
                         "- `%s` — item de cet appel." % contexte_id),
        "ajout": ajout,
        "contexte": contexte_message(qui, contexte).strip(),
    }


DEPECHES = os.path.join(ETAT, "depeches")


def archiver_le_prompt(qui, sid, manuel, texte, contexte_id=None, ref=None,
                       mode="journee"):
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
        "contexte_id": contexte_id,
        "ref": ref,
        "mode": mode,
        "date_jeu": "%s.%s.%s" % date_du_monde(),
        "system_prompt": manuel,
        "mission": texte,
    }, indent=1)


def appeler(qui, manuel, texte, sid, modele, minutes, attendre=True,
            contexte_id=None, ref=None, mode="journee", effort=None):
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
    Le CAST passe par un worker detache et sait reprendre une session deja nee,
    comme le CALL. Aucun verrou ne serialise les appels.

    PLUS D'OREILLE : le hook-parloir est mort le 31.8.2026. La session ne
    recoit aucun --settings — une parole qui arrive pendant sa journee est
    un billet au canal, servi en percept a son prochain reveil.
    """
    if contexte_id is not None:
        contexte_id = id_item_affaire(contexte_id)
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
    # Ce que le message ne porte plus doit exister la ou il pointe.
    poser_la_memoire(neutre, qui)
    archiver_le_prompt(qui, sid, manuel, texte, contexte_id=contexte_id,
                       ref=ref, mode=mode)
    from agents.expose import runtime as agent_runtime
    from agents import work_identity
    work_key = work_identity.cle_depeche(
        qui, contexte_id, ref, sid)
    identity = work_identity.admettre(work_key)
    work_identity.noter(identity, progress="admis", next_step="compute",
                        state="running")
    parametres = {
        "role": qui, "manuel": manuel, "message": texte,
        # PAS D'EXPIRATION (31.8) : `minutes=None` -> `timeout=None`, et le
        # processus rend la main quand il a fini. Le plafond ne protegeait
        # de rien et coupait des journees entieres au milieu.
        "session_id": sid, "modele": modele, "effort": effort,
        "timeout": (minutes * 60) if minutes else None,
        "cwd": neutre, "add_dirs": [RACINE, sa_chambre],
        "tools": OUTILS, "reprendre": None,
        "work_identity": identity,
        "env": {"LE_CONSEIL_QUI": str(qui),
                "LE_CONSEIL_CONTEXTE": str(contexte_id or ""),
                "LE_CONSEIL_REF": str(ref or ""),
                "LE_CONSEIL_SESSION": str(sid),
                "LE_CONSEIL_MODE": str(mode)},
    }

    if not attendre:
        # LE CAST — on lance une vie, on ne la regarde pas vivre. La mission
        # part par un fichier tenu ouvert en stdin ; le fil de sa chambre
        # recoit la sortie, datee, relisible.
        horo = time.strftime("%Y%m%d-%H%M%S")
        fil = _ch.fil(qui, contexte_id=contexte_id, creer=True)
        log = os.path.join(fil, "depeche-%s.log" % horo)
        etiquette = u"%d.%d.%d" % date_du_monde()
        return agent_runtime.lancer_cast(
            log, trace={"qui": qui, "etiquette": etiquette,
                        "contexte_id": contexte_id, "ref": ref}, **parametres)

    try:
        return agent_runtime.appeler(**parametres)
    except BaseException:
        work_identity.terminer_attempt(identity, None, "failed", term=False)
        raise


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


def depecher(qui, consigne, modele, minutes, sec, attendre=True,
             contexte_id=None, ref=None, mode="journee", beats_jump=False,
             event_jump=None, forcer_creux=False, effort=None):
    instructions_mode(mode, beats_jump=beats_jump)
    if contexte_id is not None:
        contexte_id = id_item_affaire(contexte_id)
    date = date_du_monde()
    sid = identifiant_de_session(qui, date, contexte_id=contexte_id)
    brief = brief_de(qui)
    # LA GARDE PORTE SUR CE QUI EMPECHE SA JOURNEE, pas sur un mot du dossier.
    # Elle cherchait « CONVOCATION », que l'ancien brief tenait de
    # `convoquer.py` ; le brief neuf calcule les creux lui-meme et ne l'ecrit
    # plus — la garde etait donc toujours vraie et PLUS PERSONNE NE PARTAIT.
    # Une tete absente n'est plus un motif de refus : l'identite historique,
    # les sources et la mission suffisent a reveiller quelqu'un. Objectifs et
    # croyances absents restent inconnus ; le depecheur ne les invente pas.
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
    elif u"AUCUN CREUX" in brief and not forcer_creux:
        empeche = u"aucun creux aujourd'hui — il travaille, il ne pense pas"
    if empeche:
        print(u"  %-18s ne part pas — %s" % (qui, empeche))
        return False
    contexte = dossier_journee(qui, brief)
    if contexte_id is not None:
        try:
            contexte = focaliser(contexte, contexte_id)
        except ValueError as e:
            print(u"  %-18s ne part pas — %s" % (qui, e))
            return False
    if beats_jump:
        from agents import jump_beats as _beats
        file_beats = _beats.lire(contexte_id, ref)
        if not file_beats or file_beats.get("event_id") != str(event_jump):
            print(u"  %-18s ne part pas — file de beats Jump absente" % qui)
            return False
        consigne = (consigne.rstrip() + u"\n\nSous-graphe autorisé pour les "
                    u"beats : " + u", ".join(file_beats["noeuds"]))
    manuel = manuel_de(qui, mode="journee", contexte=contexte)
    texte = mission(qui, brief, consigne, contexte=contexte,
                    contexte_id=contexte_id, ref=ref, mode=mode,
                    beats_jump=beats_jump)

    if sec:
        from agents.expose import runtime as _rt2
        from agents.expose import chambre as _ch2
        print(u"═" * 72)
        print(u"%s   session %s" % (qui, sid))
        if contexte_id is not None:
            print(u"  contexte       : %s" % contexte_id)
            print(u"  fil de chambre : %s" % os.path.relpath(
                _ch2.fil(qui, contexte_id), RACINE))
        print(u"  mode           : %s" % mode)
        print(u"  prompt système : %d caractères (nouvelle version seule)"
              % len(manuel))
        print(u"  mission        : %d caracteres" % len(texte))
        print(u"  outils         : %s" % " ".join(OUTILS))
        # LA LIGNE DISAIT « repertoire neutre » QUOI QU'IL ARRIVE — un texte
        # fige, qui ment depuis que le cwd depend du fournisseur. Un `--sec`
        # sert a voir ce qui VA se passer : il rend le vrai chemin.
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
                      attendre=attendre, contexte_id=contexte_id, ref=ref,
                      mode=mode, effort=effort)
    except Exception as e:
        print(u"  %-18s ECHEC — %s" % (qui, e))
        return False

    # LE LANCEMENT A PRIS : son reveil a tout vu — les billets sont lus.
    # Avant ce point (echec du depart), les curseurs n'ont pas bouge.
    from agents.expose import chambre as _ch
    # Le brief focalise n'a pas servi les billets generaux : il ne doit donc
    # pas les consommer en silence. Ils restent pour le prochain reveil large.
    if mode == "journee" and contexte_id is None:
        _ch.marquer_lus(qui)

    if not attendre:
        # Parti en cast : sa journee vit sans nous. Pas de rapport a parser —
        # le retour d'une journee, c'est l'etat de sa chambre plus ses
        # versements (habitant.md §1) ; son log dit ou la regarder.
        print(u"  %-18s parti detache → %s"
              % (qui, os.path.relpath(rep["log"], RACINE)))
        return True

    from agents import work_identity as _work_identity
    _identity = rep.get("continuous_work_identity")
    _compute_event_id = rep.get("compute_event_id")

    def _terme(artifact=None):
        if _identity:
            _work_identity.terminer_attempt(
                _identity, _compute_event_id, "succeeded", term=True,
                artifact=artifact)

    # LE VECU AU FIL, TOUJOURS : le lanceur le depose explicitement, sans
    # faire dependre la memoire de l'homme d'un hook de fournisseur.
    from agents.expose import trace as _tr
    try:
        _tr.deposer(qui, sid, etiquette=u"%d.%d.%d" % date,
                    transcript=rep.get("transcript_path"),
                    provider=rep.get("provider"),
                    contexte_id=contexte_id, ref=ref)
    except Exception:
        pass  # un fil qui manque ne vaut pas une journee perdue

    rapport, note = extraire_json(rep.get("result", ""))
    u_ = rep.get("usage", {}) or {}
    jetons = (u_.get("input_tokens", 0) + u_.get("cache_read_input_tokens", 0)
              + u_.get("cache_creation_input_tokens", 0))

    if mode != "journee":
        phrase = (rep.get("result") or u"").strip()
        if beats_jump:
            structure, _note = extraire_json(phrase)
            if not isinstance(structure, dict) or not structure.get("reponse"):
                print(u"  %-18s ECHEC — réponse Jump structurée absente" % qui)
                return False
            from agents import jump_beats as _beats
            ajoutes = _beats.ajouter(
                event_jump, contexte_id, ref, qui,
                structure.get("beats_attente") or [])
            phrase = str(structure["reponse"]).strip()
            print(u"  %-18s %d beat(s) d'attente préparé(s)" %
                  (qui, len(ajoutes)))
            print(u"REPONSE DE %s :\n%s" % (qui, phrase))
        print(u"  %-18s %5d j. · %3ds — %s : %s"
              % (qui, jetons, round(time.time() - debut), mode,
                 re.sub(r"\s+", u" ", phrase)[:220] or u"(muette)"))
        _terme()
        return True

    if rapport is None:
        # PLUS UN ECHEC : le gabarit JSON est retire (habitant.md pas 3).
        # Sa derniere reponse est une phrase d'homme ; sa journee vit dans
        # sa chambre (fil/, brouillons/, cahiers) et ses versements.
        phrase = (rep.get("result") or u"").strip()
        brut = cible_rapport(qui, contexte_id, brut=True)
        _poser(brut, phrase)
        # LE MOT SUR SA TABLE : sa conclusion s'ecrit dans sa chambre,
        # ECRASEE a chaque journee — c'est le mot le plus recent qui compte,
        # le fil garde l'historique. Elle sera reinjectee a son prochain
        # reveil (« La ou tu t'etais laisse », mission()).
        if phrase:
            mot = (os.path.join(_ch.chemin(qui), "demain.md")
                   if contexte_id is None else
                   os.path.join(_ch.fil(qui, contexte_id, creer=True),
                                "demain.md"))
            with io.open(mot, "w",
                         encoding="utf-8", newline="\n") as f:
                f.write(phrase + u"\n")
        print(u"  %-18s %5d j. · %3ds — sa phrase : %s"
              % (qui, jetons, round(time.time() - debut),
                 re.sub(r"\s+", u" ", phrase)[:160] or u"(muette)"))
        _terme(brut)
        return True

    rapport.setdefault("qui", qui)
    rapport["_depeche"] = {
        "session": sid, "date_jeu": "%d.%d.%d" % date,
        "contexte_id": contexte_id,
        "ref": ref,
        "jetons": jetons, "secondes": round(time.time() - debut),
    }
    cible = cible_rapport(qui, contexte_id)
    tables.ecrire(cible, rapport)
    verse = verser_sur_le_champ(rapport, qui, date)

    p = sum(len(t.get("pensees", []) or []) for t in rapport.get("travaux", []) or [])
    print(u"  %-18s %2d pensee(s) [%d versee(s)] · %2d etape(s) · %s · %5d j. · %3ds → %s%s"
          % (qui, p, verse, len(rapport.get("journal", []) or []),
             u"conclusion" if rapport.get("conclusion") else u"—",
             jetons, rapport["_depeche"]["secondes"],
             os.path.relpath(cible, RACINE), u"  [%s]" % note if note else u""))
    _terme(cible)
    return True
