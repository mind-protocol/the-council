# -*- coding: utf-8 -*-
"""MJ — le reveil du seul maitre du jeu.

Le joueur reveille le MJ par son POST ou par un verbe du front. Les PNJ ne
l'appellent plus : ils agissent depuis leur etat et leurs sources, sans
demander de permission, d'information ou de verdict.

LA SESSION DU MJ EST SA MEMOIRE. Son identifiant est deterministe et SANS
date : il ne repart jamais de zero. Il n'existe plus d'arbitre geographique
ni d'identifiant `mj-<ville>` : la geographie informe le monde, elle ne cree
pas une autorite supplementaire.

Le vecu du MJ vit dans sa session continue ; son depot au fil (trace) est
differe — un transcript qui grandit se depouillerait en double a chaque
audience.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

from agents import chambre
from agents.depeche.brief import RACINE, OUTILS, lire, date_du_monde

# Le sel de l'espace de noms des sessions de zone. Le changer rend tous les
# MJ amnesiques d'un coup : c'est le seul geste qui reparte de zero.
SEL = uuid.uuid5(uuid.NAMESPACE_URL, "le-conseil/mj/v1")

MJ_SPECTACLE_MD = os.path.join(RACINE, "scripts", "agents", "prompts",
                               "mj-spectacle.md")
# LES REGLES DE LA PARTIE, AU MEME TITRE QUE LES AUTRES. Elles ont manque au
# manuel jusqu'au 3.9 : le MJ etait reveille sur un coup du conseil de guerre
# sans avoir jamais lu les regles du wargame, et il repartait faire autre
# chose. Un arbitre a qui l'on ne donne pas les regles n'arbitre pas.
MJ_PARTIE_MD = os.path.join(RACINE, "scripts", "agents", "prompts",
                            "mj-partie.md")
# ... ET LE LIVRE DE REGLES AVEC LUI (audit du 7.9, C1). Depuis le 7.9, le
# manuel ne porte plus les regles : il les CITE par adresse (R8, V1-V4, S1)
# et renvoie a docs/regles-partie.md, qui n'etait pas charge. Les deux ne se
# montent que si une partie est ACTIVE — `_courante.json` nomme une partie
# dont le jsonl existe ; un reveil ordinaire n'a rien a faire d'un wargame et
# y gagne ~9 000 jetons de systeme.
REGLES_PARTIE_MD = os.path.join(RACINE, "docs", "regles-partie.md")
SKILL_JUMP_MD = os.path.join(RACINE, "scripts", "agents", "skills",
                             "jump", "SKILL.md")
MANUEL_MJ_RACINE = os.path.join(RACINE, "CLAUDE.md")
FLUX = os.path.join(RACINE, "etat", "flux.jsonl")
FLUX_RETOURS_PARLOIR = os.path.join(
    RACINE, ".agents-runtime", "mj", "retours-parloir.jsonl")
CURSEUR_RETOURS_PARLOIR = os.path.join(
    RACINE, ".agents-runtime", "mj", "retours-parloir.lu")

# PLUS DE PLAFOND SUR UNE SESSION (31.8). « Trois minutes est un verdict, pas
# une journee » supposait qu'un arbitre repond vite ; la mesure dit autre
# chose. Le 31.8, hann-bourbe a fait son P.10, pose sa question a
# mj-portreal, et la session de l'arbitre a ete tuee a 180 secondes : le
# traceback est remonte dans la pensee de l'homme, sa journee entiere est
# partie, zero octet ecrit.
#
# CE PLAFOND NE PROTEGEAIT DE RIEN. Un processus rend la main quand il a fini
# — le couperet n'evite aucune fuite, il coupe seulement du travail en cours.
# `None` = pas d'expiration. Les deux noms restent pour qui veut borner
# explicitement un appel.
MINUTES = None
ETABLI_MINUTES = None


def identifiant_de_session():
    """Stable pour l'unique MJ, sans date : sa session est sa memoire."""
    return str(uuid.uuid5(SEL, "mj"))


def deposer_retour_parloir(de, joueur, texte, contexte_id=None, ref=None):
    """Flux append-only des réponses déjà rendues au navigateur du joueur."""
    os.makedirs(os.path.dirname(FLUX_RETOURS_PARLOIR), exist_ok=True)
    entree = {"id": str(uuid.uuid4()), "de": str(de),
              "joueur": str(joueur), "texte": str(texte),
              "contexte_id": (str(contexte_id) if contexte_id else None),
              "ref": (str(ref) if ref else None)}
    with io.open(FLUX_RETOURS_PARLOIR, "a", encoding="utf-8",
                 newline="\n") as f:
        f.write(json.dumps(entree, ensure_ascii=False) + u"\n")
    return entree


def _position_retours_parloir():
    try:
        with io.open(CURSEUR_RETOURS_PARLOIR, encoding="utf-8") as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def _retours_parloir_non_lus():
    debut = _position_retours_parloir()
    try:
        fin = os.path.getsize(FLUX_RETOURS_PARLOIR)
        with open(FLUX_RETOURS_PARLOIR, "rb") as f:
            f.seek(min(debut, fin))
            brut = f.read(fin - min(debut, fin)).decode("utf-8", "replace")
    except OSError:
        return [], debut
    entrees = []
    for ligne in brut.splitlines():
        try:
            valeur = json.loads(ligne)
            if isinstance(valeur, dict):
                entrees.append(valeur)
        except ValueError:
            continue
    return entrees, fin


def _marquer_retours_parloir_lus(position):
    os.makedirs(os.path.dirname(CURSEUR_RETOURS_PARLOIR), exist_ok=True)
    temporaire = CURSEUR_RETOURS_PARLOIR + ".%s.tmp" % uuid.uuid4().hex
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        f.write(str(int(position)))
    os.replace(temporaire, CURSEUR_RETOURS_PARLOIR)


def _sain(nom):
    if not re.match(r"^[a-z0-9][a-z0-9_.\-]*$", nom or ""):
        raise SystemExit(u"identifiant de zone illisible : %r" % nom)
    return nom


def _partie_active():
    """L'identifiant de la partie en cours (etat/parties/_courante.json nomme
    une partie dont le jsonl existe), ou None. La matiere vit dans
    temps/reprise.py, pour que la feuille de reprise et le reveil du MJ
    fassent le meme test. Ne leve jamais."""
    try:
        from temps import reprise as _reprise
        return _reprise.partie_courante()
    except Exception:
        return None


def _bloc_partie():
    """« LA PARTIE EN COURS » : dix lignes tirees de `partie.py --etat` et de
    la derniere ligne `tour` du jsonl — ce qu'on attend de l'arbitre (audit
    du 7.9, C2). Vide si aucune partie n'est active ou si le greffe ne repond
    pas dans les 20 s : jamais bloquant, jamais une raison de ne pas se
    reveiller."""
    try:
        from temps import reprise as _reprise
        pid = _reprise.partie_courante()
        if not pid:
            return u""
        feuille = _reprise.feuille_partie(pid, timeout=20)
        if not feuille:
            return u""
        return (u"\nLA PARTIE EN COURS — %s (etat/parties/%s.jsonl)\n%s\n"
                % (pid, pid, feuille))
    except Exception:
        return u""


def _manuel(modes=None):
    """Constitution, spectacle, skills du mode et cahier du MJ — et, quand
    une partie est active, le manuel de l'arbitre et le livre de regles."""
    constitution = lire(MANUEL_MJ_RACINE)
    if constitution is None:
        raise SystemExit("CLAUDE.md manque au MJ principal.")
    spectacle = lire(MJ_SPECTACLE_MD)
    if spectacle is None:
        raise SystemExit("scripts/agents/prompts/mj-spectacle.md manque au MJ.")
    blocs = [constitution, spectacle]
    if _partie_active():
        partie = lire(MJ_PARTIE_MD)
        if partie is None:
            raise SystemExit("scripts/agents/prompts/mj-partie.md manque au MJ.")
        regles = lire(REGLES_PARTIE_MD)
        if regles is None:
            raise SystemExit("docs/regles-partie.md manque au MJ arbitre.")
        blocs.append(partie)
        blocs.append(u"# Le livre de règles de la partie\n\n" + regles.strip())
    if u"jump" in (modes or []):
        skill_jump = lire(SKILL_JUMP_MD)
        if skill_jump is None:
            raise SystemExit(
                "scripts/agents/skills/jump/SKILL.md manque au brief Jump.")
        blocs.append(u"# Skill actif pour ce reveil\n\n" + skill_jump.strip())
    cahier = lire(os.path.join(chambre.chemin("mj"), "claude.md"))
    if cahier and cahier.strip():
        blocs.append(u"# Ta maniere, de ta main\n\n" + cahier.strip())
    return u"\n\n---\n\n".join(blocs) + u"\n"


def reveiller_en_cast(de, mot, contexte_id=None, ref=None):
    """Reveil autorise du MJ (front joueur ou dev) — billet + spawn detache
    de reveiller.py : le motif de `parloir --dire` vers un MJ, offert aux
    lanceurs explicites. Le mot voyage
    avec le reveil, donc marque lu ; la suite arrive par les canaux.

    PAS DE LIMITE DE CADENCE ICI (tranche par le dev le 31.8, apres la
    tempete de la nuit) : un throttle n'aurait fait que ralentir le meme
    ping-pong. La cause etait dans le CADRE du reveil, qui commandait un
    billet-reponse a chaque reveil ; la regle qui tient est celle du peage
    de la parole, dans _message — une correspondance FINIT."""
    from agents.expose import billet
    canal, nouveau = billet.deposer(
        de, "mj", mot, contexte_id=contexte_id, ref=ref, statut=True)
    if not nouveau:
        return canal, False
    chambre.marquer_lu("mj", de)
    drapeaux = {}
    if os.name == "nt":  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP — detache SANS console visible (spam de terminaux du 31.8)
        drapeaux["creationflags"] = 0x08000000 | 0x00000200
    else:
        drapeaux["start_new_session"] = True
    subprocess.Popen(
        [sys.executable, os.path.join(RACINE, "scripts", "reveiller.py"),
         "--de", de, mot],
        cwd=RACINE, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, **drapeaux)
    return canal, True


def _message(de, mot, verbe, modes=None):
    """Le reveil ne porte que deux choses : qui te reveille, et voici son
    mot — plus l'etiquette du moment (habitant.md §4 : la date est une
    etiquette, jamais un verrou)."""
    if verbe == u"JOUEUR":
        message = (u"[JOUEUR] %s vient de parler ou d'agir — an %d, %de "
                   u"lune, %de jour.\n%s\n"
                   u"Ce reveil est une adresse de travail, pas une voix "
                   u"d'habitant a arbitrer. Traite toutes les ACTIONS du brief "
                   u"dans l'ordre et reponds au joueur dans son flux — jamais "
                   u"par billet ou parloir.\n"
                   u"CADRE DU TOUR PJ — ta PREMIERE action est toujours de "
                   u"pousser dans le flux un item visible adresse a %s : "
                   u"une ouverture courte, vraie dans le mode courant, sans "
                   u"parole de PNJ inventee. Puis tu accomplis le travail. "
                   u"Ta DERNIERE action avant de rendre la main est toujours "
                   u"un SECOND item visible adresse au meme PJ : il porte le "
                   u"resultat effectivement atteint ou le battement qui lui "
                   u"rend la prise. Aucun appel d'outil, ecriture d'etat ou "
                   u"message technique ne vient apres cet item final. Ces "
                   u"deux items sont distincts ; une seule poussee ne compte "
                   u"pas a la fois comme debut et comme fin.\n"
                   u"SORTIE : `python scripts/append_flux.py '<json item>' "
                   u"--pour %s`, des qu'une tranche est prete, puis de nouveau "
                   u"plus tard dans le meme tour. Un refus se corrige avant "
                   u"l'appel suivant. `suites` reste facultatif.\n"
                   % ((de,) + date_du_monde() + (mot.strip(), de, de)))
        if u"run" in (modes or []):
            message += (
                u"RUN ACTIF — GARDE DE SORTIE : tu tiens le personnage a sa "
                u"place. Une transition, une porte qui s'ouvre, un rapport "
                u"annonce ou un homme qui attend ne sont PAS une reponse. "
                u"Continue jusqu'au contenu substantiel et a ses consequences. "
                u"Si un PNJ doit parler, depeche-le ou interroge sa session : "
                u"n'invente pas sa parole et n'arrete pas le run en attendant. "
                u"Rends la bride quand le battement substantiel est accompli ; "
                u"un item `suites` peut l'expliciter, mais n'est jamais requis.\n")
        if u"jump" in (modes or []):
            message += (
                u"JUMP 1 ACTIF — le bloc ROUTAGE contient l'unique événement "
                u"cible, son sous-graphe et son contexte MJ numérique. Le "
                u"skill système `jump-scene` est actif pour ce seul réveil : "
                u"exécute-le en entier, de la complétion du graphe jusqu'aux "
                u"mises à jour des PNJ et à la scène visible. Meuble le flux "
                u"au fur et à mesure sans inventer de PNJ, avance réellement "
                u"la clock, et ne rends pas la main au milieu du Jump.\n")
        return message + _bloc_partie()
    return (u"[%s] %s te reveille — an %d, %de lune, %de jour.\n"
            u"Son mot : « %s »\n"
            u"Tu es l'arbitre : ce mot est la voix d'un autre — reponds en "
            u"arbitre, jamais dans sa pensee.\n"
            u"SI son mot appelle une reponse, elle ne lui parvient que par "
            u"billet (python scripts/parloir.py --dire --de <toi> --a %s "
            u"\"...\") — ce que tu ecris ici sans billet reste dans ton "
            u"registre. MAIS UN BILLET PAIE SON PEAGE : il porte un fait "
            u"nouveau, une decision, ou une question dont tu attends la "
            u"reponse pour agir — sinon TU TE TAIS. Jamais d'accuse, de "
            u"merci, de complement qui redit, de reformulation de ce que "
            u"l'autre sait : une correspondance qui n'a plus rien a "
            u"s'apprendre EST FINIE, et le silence est sa fin normale "
            u"(mesure du 31.8 : deux correspondants polis se sont reveilles "
            u"l'un l'autre seize fois en six minutes).\n"
            % ((verbe, de) + date_du_monde() + (mot.strip(), de))
            + _bloc_partie())


def appeler_mj(de, mot, verbe, modele=None, minutes=MINUTES, refs=None,
               routage=None):
    """Traite un appel du front joueur et rend son verdict sur stdout."""
    mj = "mj"
    sid = identifiant_de_session()
    sa_chambre = chambre.ouvrir(mj)
    actions_joueur = (_actions_en_attente(de)
                      if verbe == u"JOUEUR" else [])
    if refs is not None:
        actions_joueur = _filtrer_actions_refs(actions_joueur, refs)
    modes_joueur = _modes_actions(actions_joueur)
    manuel = _manuel(modes=modes_joueur)
    if verbe == u"JOUEUR":
        from agents import portage
        mot = portage.brief_message_joueur(de, refs=refs)
    texte = _message(de, mot, verbe, modes=modes_joueur)
    retours_parloir, position_retours = _retours_parloir_non_lus()
    if retours_parloir:
        texte += (u"\n\nRETOURS DU PARLOIR DEJA AFFICHES AUX JOUEURS :\n"
                  + json.dumps(retours_parloir, ensure_ascii=False, indent=2)
                  + u"\nIls sont deja dans le flux web : ne les repousse pas. "
                    u"Mets seulement leurs consequences en scene.\n")
    if routage:
        texte += (u"\n\nROUTAGE DE CONTEXTE DEJA EXECUTE POUR CETTE ACTION :\n"
                  + json.dumps(routage, ensure_ascii=False, indent=2)
                  + u"\nCe bloc est une adresse de travail hors fiction. "
                    u"Respecte notamment l'interdit de doubler une route "
                    u"d'homme deja servie.\n")

    # LE PAS-DE-TIR EST STABLE, ET C'EST UNE CONDITION DE LA MEMOIRE (mesure
    # du 30.8, reveils-jouets du pas 4) : un --session-id n'est unique que
    # PAR REPERTOIRE de lancement — deux mkdtemp donnent deux sessions au
    # meme id, et le second reveil repartait de zero en silence. Un dossier
    # fixe par MJ, hors du depot (la decouverte de CLAUDE.md remonte
    # l'arborescence), rend le conflit d'id — donc le --resume.
    neutre = os.path.join(tempfile.gettempdir(), "le-conseil-mj")
    os.makedirs(neutre, exist_ok=True)
    from agents.expose import runtime as agent_runtime
    debut_flux = _position_flux()
    appels = []

    def appeler_le_mj(message):
        refs_env = [str(r) for r in (refs or []) if r]
        rep = agent_runtime.appeler(
            role=mj, manuel=manuel, message=message, session_id=sid,
            modele=modele,
            timeout=(minutes * 60) if minutes else None, cwd=neutre,
            add_dirs=[RACINE, sa_chambre], tools=OUTILS, reprendre=None,
            env={"LE_CONSEIL_QUI": str(mj), "LE_CONSEIL_MJ": str(mj),
                 "LE_CONSEIL_REF": u",".join(refs_env)})
        appels.append(rep)
        return rep

    rep = appeler_le_mj(texte)
    jump_attendu = _actions_sont_jump(actions_joueur)
    rapport_attendu = (_actions_exigent_replique(actions_joueur)
                       or _a_interroge_un_pnj(rep))
    rapport_cache = (rapport_attendu
                     and u"replique" not in _types_flux_depuis(debut_flux))
    if rapport_cache:
        rep = appeler_le_mj(
            u"[CONTINUER LE RUN — SORTIE REFUSEE] Tu as rendu la main avant "
            u"d'avoir accompli le laisser-faire. Reprends exactement ou tu "
            u"t'es arrete. Une "
            u"porte qui s'ouvre ou un rapport annonce n'est qu'une amorce. "
            u"Obtiens la parole des PNJ par depeche/parloir si elle est "
            u"necessaire. Si tu as deja obtenu leur rapport, un resume en "
            u"`recit` le cache au joueur : pousse au moins une `replique` "
            u"avec `locuteur_id`, tiree de leurs mots reels, puis joue ses "
            u"consequences. `suites` n'est pas obligatoire. N'efface pas les "
            u"items deja ecrits ; complete-les.")
        rapport_attendu = rapport_attendu or _a_interroge_un_pnj(rep)
    types_tour = _types_flux_depuis(debut_flux)
    if jump_attendu:
        for _ in range(3):
            manques = _manques_jump(routage, debut_flux)
            if not manques:
                break
            rep = appeler_le_mj(
                u"[CONTINUER JUMP — SORTIE INTERMEDIAIRE REFUSEE] Tu es "
                u"encore au milieu du Jump : %s. Une tranche de décor meuble "
                u"l'attente mais ne clôt rien. Reprends maintenant, avance "
                u"réellement la clock, applique l'unique événement cible et "
                u"joue sa scène substantielle. Ne rends pas la main et ne "
                u"passe pas à l'événement suivant."
                % u" ; ".join(manques))
            types_tour = _types_flux_depuis(debut_flux)
        manques = _manques_jump(routage, debut_flux)
        if manques:
            raise RuntimeError("jump inachevé : %s" % u" ; ".join(manques))
    if rapport_attendu and u"replique" not in types_tour:
        raise RuntimeError(
            "rapport invisible : aucune replique de PNJ n'a ete poussee")
    _marquer_retours_parloir_lus(position_retours)
    sys.stderr.write(u"(mj : %s, session %s)\n" % (
        rep.get("provider") or "agent", sid[:8]))
    # L'inbox est une file, pas une memoire. Le modele ne porte plus la
    # suppression : le lanceur connait exactement les pieces presentes AVANT
    # le tour et ne retire que celles-la, seulement apres un appel reussi a la
    # porte et une vraie ecriture constatee. Un POST arrive pendant la session
    # reste donc pour le reveil suivant.
    if (actions_joueur and types_tour
            and any(_a_pousse_flux(r) for r in appels)):
        _retirer_actions(actions_joueur)
    return (rep.get("result") or u"").strip()


def _position_flux():
    try:
        return os.path.getsize(FLUX)
    except OSError:
        return 0


def _items_flux_depuis(position):
    """Items reellement ajoutes depuis le reveil, sans intermediaire."""
    try:
        with open(FLUX, "rb") as f:
            f.seek(position)
            brut = f.read().decode("utf-8", "replace")
    except OSError:
        return []
    items = []
    for ligne in brut.splitlines():
        try:
            item = json.loads(ligne)
            if isinstance(item, dict):
                items.append(item)
        except ValueError:
            continue
    return items


def _types_flux_depuis(position):
    return [item.get("type") for item in _items_flux_depuis(position)
            if item.get("type")]


def _date_tuple(date):
    date = date or {}
    return tuple(int(date.get(cle, 0) or 0)
                 for cle in ("annee", "lune", "jour", "minute"))


def _manques_jump(routage, position_flux):
    """Preuves observables qu'un Jump n'est plus une préparation en cours."""
    preparation = ((routage or {}).get("jump") or {})
    evenement = preparation.get("event") or {}
    event_id = str(evenement.get("id") or "")
    cible = _date_tuple(evenement.get("date_prevue"))
    if not event_id or not preparation.get("contexte_id"):
        return [u"cible ou contexte_id absent du brief"]

    manques = []
    try:
        from plan.expose import graphe_causal
        noeuds, aretes = graphe_causal.charger_tissu()
        if not graphe_causal.extraire(event_id, noeuds, aretes).get("complet"):
            manques.append(u"sous-graphe causal encore troué")
    except Exception as exc:
        manques.append(u"graphe causal invérifiable (%s)" % exc)

    programmes = _lire_json(
        os.path.join(RACINE, "etat", "evenements.json"), [])
    if isinstance(programmes, dict):
        programmes = programmes.get("evenements") or []
    courant = next((e for e in programmes if isinstance(e, dict)
                    and str(e.get("id") or "") == event_id), None)
    if courant is None:
        manques.append(u"événement cible absent de evenements.json")
    elif str(courant.get("statut") or "").casefold() not in (
            "resolu", "résolu", "devie", "dévié", "annule", "annulé"):
        manques.append(u"événement cible pas encore résolu ou dévié")

    substantiels = {u"recit", u"replique", u"geste", u"evenement",
                    u"salle", u"table", u"marque"}
    items = _items_flux_depuis(position_flux)
    scene_a_la_cible = any(
        item.get("type") in substantiels
        and _date_tuple(item.get("date")) >= cible
        for item in items)
    if not scene_a_la_cible:
        manques.append(u"aucune scène substantielle estampillée à la cible")

    dates_flux = [_date_tuple(item.get("date")) for item in items
                  if item.get("date")]
    monde = _lire_json(os.path.join(RACINE, "etat", "monde.json"), {})
    clock = max([_date_tuple(monde.get("date"))] + dates_flux)
    if clock < cible:
        manques.append(u"clock encore antérieure à la cible")
    return manques


def _lire_json(chemin, defaut):
    try:
        with io.open(chemin, encoding="utf-8") as fichier:
            return json.load(fichier)
    except (OSError, ValueError, TypeError):
        return defaut


def _a_pousse_flux(rep):
    return any("append_flux.py" in str(geste)
               for geste in (rep.get("gestes") or []))


def _actions_en_attente(personnage):
    dossier = os.path.join(RACINE, "etat", "inbox", _sain(personnage))
    if not os.path.isdir(dossier):
        return []
    return [os.path.join(dossier, nom) for nom in sorted(os.listdir(dossier))
            if nom.startswith("action-") and nom.endswith(".json")
            and os.path.isfile(os.path.join(dossier, nom))]


def _modes_actions(chemins):
    modes = []
    for chemin in chemins:
        try:
            with io.open(chemin, encoding="utf-8") as f:
                mode = (json.load(f) or {}).get("mode")
            if mode and mode not in modes:
                modes.append(str(mode))
        except Exception:
            continue
    return modes


def _filtrer_actions_refs(chemins, refs):
    """Isole les actions que le selecteur vient effectivement de router."""
    refs = {str(ref) for ref in refs}
    retenues = []
    for chemin in chemins:
        try:
            with io.open(chemin, encoding="utf-8") as f:
                action = json.load(f) or {}
            if str(action.get("ref") or "") in refs:
                retenues.append(chemin)
        except Exception:
            continue
    return retenues


def _actions_exigent_replique(chemins):
    motifs = (u"rapport", u"parole", u"replique", u"réplique")
    for chemin in chemins:
        try:
            with io.open(chemin, encoding="utf-8") as f:
                action = json.load(f) or {}
            texte = str(action.get("texte") or "").casefold()
            if action.get("mode") == "run" and any(m in texte for m in motifs):
                return True
        except Exception:
            continue
    return False


def _actions_sont_jump(chemins):
    for chemin in chemins:
        try:
            with io.open(chemin, encoding="utf-8") as f:
                if str((json.load(f) or {}).get("mode") or "").casefold() == "jump":
                    return True
        except Exception:
            continue
    return False


def _a_interroge_un_pnj(rep):
    gestes = u"\n".join(str(g) for g in (rep.get("gestes") or []))
    return "parloir.py" in gestes or "depecher.py" in gestes


def _retirer_actions(chemins):
    for chemin in chemins:
        try:
            os.remove(chemin)
        except FileNotFoundError:
            pass
def main():
    """L'entree de scripts/reveiller.py : reveiller l'unique MJ."""
    import argparse
    ap = argparse.ArgumentParser(description=main.__doc__)
    ap.add_argument("--de", required=True,
                    help="qui reveille — le personnage du siege qui a poste")
    ap.add_argument("--modele", default=None)
    # PLUS DE PLAFOND, ET LES DIX MINUTES ETAIENT DEJA UNE RUSTINE. Le 31.8
    # au matin j'avais releve ce reveil de 180 s a 600 parce qu'un MJ coupe
    # en plein tour ne rend rien au joueur, sans laisser de trace (le serveur
    # le spawn DETACHE et ne lit pas sa sortie). La bonne question n'etait
    # pas « a combien » : c'etait « de quoi ce plafond protege-t-il ». De
    # rien — un processus rend la main quand il a fini. Ce qu'il faisait, en
    # revanche, se mesure : une journee d'homme perdue le meme jour.
    # Defaut : pas d'expiration. Le drapeau reste, pour un banc qui veut
    # borner explicitement.
    ap.add_argument("--timeout", type=float, default=None, metavar="SECONDES",
                    help="borner l'appel a N secondes ; par defaut la session"
                         " n'expire pas")
    ap.add_argument("texte", nargs="*",
                    help="son mot (defaut : va lire l'inbox et le flux)")
    a = ap.parse_args()
    if a.timeout is not None and a.timeout <= 0:
        ap.error("le timeout se compte en secondes et doit etre positif")
    minutes = (a.timeout / 60.0) if a.timeout else None
    mot = u" ".join(a.texte)
    verbe = u"POST" if mot else u"JOUEUR"
    print(appeler_mj(a.de, mot, verbe, modele=a.modele, minutes=minutes))
