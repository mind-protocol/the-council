# -*- coding: utf-8 -*-
"""RUNTIME — une seule porte vers les CLI d'agents Claude et Codex.

Le jeu connait des sessions logiques (un homme, un jour ; un MJ de zone ;
un narrateur d'activation). Le fournisseur, lui, a son propre identifiant de
thread. Ce module garde cette traduction et rend toujours le vieux contrat
Claude ``{result, usage, ...}`` aux appelants.

Le choix global se fait avec ``python scripts/fournisseur.py`` ou, pour une
commande seulement, ``LE_CONSEIL_FOURNISSEUR=claude|codex``.
"""
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import uuid


RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
DOSSIER_RUNTIME = os.path.join(RACINE, ".agents-runtime")
CONFIG = os.path.join(DOSSIER_RUNTIME, "config.json")
SESSIONS = os.path.join(DOSSIER_RUNTIME, "sessions.json")
REQUETES = os.path.join(DOSSIER_RUNTIME, "requests")
ACTIVITES = os.path.join(DOSSIER_RUNTIME, "active")

FOURNISSEURS = {"claude": "claude", "codex": "codex", "chatgpt": "codex"}
MODELE_CODEX = "gpt-5.3-codex-spark"
EFFORT_CODEX = "low"


def _lire_json(chemin, defaut):
    if not os.path.exists(chemin):
        return defaut
    with io.open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _ecrire_json(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    temporaire = chemin + ".%s.tmp" % uuid.uuid4().hex
    with io.open(temporaire, "w", encoding="utf-8", newline="\n") as f:
        json.dump(valeur, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temporaire, chemin)


def configuration():
    d = _lire_json(CONFIG, {})
    brut = (os.environ.get("LE_CONSEIL_FOURNISSEUR") or
            os.environ.get("LE_CONSEIL_AGENT_PROVIDER") or
            d.get("fournisseur") or d.get("provider") or "claude")
    nom = FOURNISSEURS.get(str(brut).casefold())
    if not nom:
        raise RuntimeError("fournisseur d'agent inconnu : %s" % brut)
    return {
        "fournisseur": nom,
        "modele_codex": (os.environ.get("LE_CONSEIL_CODEX_MODELE") or
                          os.environ.get("LE_CONSEIL_CODEX_MODEL") or
                          d.get("modele_codex") or MODELE_CODEX),
        "effort_codex": (os.environ.get("LE_CONSEIL_CODEX_EFFORT") or
                          d.get("effort_codex") or EFFORT_CODEX),
        "modele_claude": (os.environ.get("LE_CONSEIL_CLAUDE_MODELE") or
                           os.environ.get("LE_CONSEIL_CLAUDE_MODEL") or
                           d.get("modele_claude")),
    }


def fournisseur():
    return configuration()["fournisseur"]


def choisir(nom, modele=None, effort=None):
    """Pose le choix local global. L'environnement reste prioritaire."""
    canonique = FOURNISSEURS.get(str(nom).casefold())
    if not canonique:
        raise ValueError("choisir claude, codex ou chatgpt")
    d = _lire_json(CONFIG, {})
    d["fournisseur"] = canonique
    if canonique == "codex":
        if modele:
            d["modele_codex"] = modele
        if effort:
            d["effort_codex"] = effort
    elif modele:
        d["modele_claude"] = modele
    _ecrire_json(CONFIG, d)
    return configuration()


def _modele(provider, demande):
    cfg = configuration()
    if provider == "codex":
        # Les CLI historiques donnent souvent `opus` ou `sonnet`. Ce ne sont
        # pas des choix Codex : la bascule globale doit suffire a elle seule.
        if demande and (str(demande).startswith("gpt-") or
                        "codex" in str(demande).casefold()):
            return str(demande)
        return cfg["modele_codex"]
    if demande and not (str(demande).startswith("gpt-") or
                        "codex" in str(demande).casefold()):
        return str(demande)
    return cfg.get("modele_claude")


def _effort(provider, demande):
    if provider == "codex":
        return str(demande or configuration()["effort_codex"])
    return str(demande) if demande else None


@contextlib.contextmanager
def _verrou(nom, timeout=1800):
    """Verrou inter-processus : deux CAST d'un meme homme se suivent."""
    dossier = os.path.join(DOSSIER_RUNTIME, "locks")
    os.makedirs(dossier, exist_ok=True)
    propre = hashlib.sha256(str(nom).encode("utf-8")).hexdigest()
    chemin = os.path.join(dossier, propre + ".lock")
    f = open(chemin, "a+b")
    f.seek(0, os.SEEK_END)
    if f.tell() == 0:
        f.write(b"\0")
        f.flush()
    debut = time.monotonic()
    pris = False
    try:
        while not pris:
            try:
                if os.name == "nt":
                    import msvcrt
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:  # pragma: no cover - banc principal Windows
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                pris = True
            except (OSError, IOError):
                if time.monotonic() - debut >= timeout:
                    raise TimeoutError("session occupee : %s" % nom)
                time.sleep(0.1)
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


@contextlib.contextmanager
def _activite(role, session_id):
    """Expose une session vraiment en calcul aux voyants de l'ecran.

    Le marqueur est pose seulement apres le verrou de session : un appel en
    attente derriere un autre n'est donc pas annonce comme actif. Le pid
    permet au serveur d'ignorer un reste laisse par un worker tue brutalement.
    """
    os.makedirs(ACTIVITES, exist_ok=True)
    chemin = os.path.join(ACTIVITES, "%s.json" % uuid.uuid4().hex)
    _ecrire_json(chemin, {
        "homme": str(role),
        "session": str(session_id),
        "pid": os.getpid(),
        "t": time.time(),
    })
    try:
        yield
    finally:
        try:
            os.unlink(chemin)
        except OSError:
            pass


def _session_codex(logique):
    return _entree_session(logique).get("codex_thread_id")


def _entree_session(logique):
    with _verrou("registre", timeout=30):
        return dict(_lire_json(SESSIONS, {}).get(str(logique)) or {})


def _poser_session_codex(logique, thread_id, modele, transcript=None,
                         manuel_sha256=None):
    with _verrou("registre", timeout=30):
        d = _lire_json(SESSIONS, {})
        entree = dict(d.get(str(logique)) or {})
        entree.update({
            "codex_thread_id": thread_id,
            "modele": modele,
            "dernier_transcript": transcript,
            "mis_a_jour": dt.datetime.now().astimezone().isoformat(),
        })
        if manuel_sha256:
            entree["manuel_sha256_codex"] = manuel_sha256
        d[str(logique)] = entree
        _ecrire_json(SESSIONS, d)


def _poser_empreinte_manuel(logique, fournisseur, empreinte):
    with _verrou("registre", timeout=30):
        d = _lire_json(SESSIONS, {})
        entree = dict(d.get(str(logique)) or {})
        entree["manuel_sha256_%s" % fournisseur] = empreinte
        entree["mis_a_jour"] = dt.datetime.now().astimezone().isoformat()
        d[str(logique)] = entree
        _ecrire_json(SESSIONS, d)


def _prompt_codex(manuel, cwd):
    chemin = os.path.join(cwd, "AGENTS.md")
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(u"# Manuel de ce réveil\n\n")
        f.write(manuel.strip() + u"\n\n")
        f.write(u"# Cadre technique\n\n"
                u"Tu es lancé sans interface depuis ce dossier neutre. "
                u"Respecte les chemins et les portes nommés dans le manuel. "
                u"Ta réponse finale est remise telle quelle au jeu.\n")
    return chemin


def _empreinte_manuel(manuel):
    return hashlib.sha256(manuel.encode("utf-8")).hexdigest()


def _retirer_prompt_codex(cwd):
    chemin = os.path.join(cwd, "AGENTS.md")
    try:
        os.remove(chemin)
    except FileNotFoundError:
        pass


def _preparer_prompt_codex(manuel, cwd, thread_id, entree):
    """Pose le gros manuel pour UN appel seulement s'il est neuf ou change.

    Le fichier est retire apres l'appel reussi : une reprise Codex garde son
    contexte de session et ne doit pas recharger 180 ko d'AGENTS.md a chaque
    reveil. L'empreinte rend les futures modifications injectables une fois.
    """
    empreinte = _empreinte_manuel(manuel)
    injecter = (not thread_id or
                entree.get("manuel_sha256_codex") != empreinte)
    if injecter:
        _prompt_codex(manuel, cwd)
    else:
        # Nettoie aussi les anciens fichiers persistants de l'ere ou le manuel
        # etait reecrit avant chaque resume.
        _retirer_prompt_codex(cwd)
    return empreinte, injecter


def _prompt_claude(manuel, cwd):
    chemin = os.path.join(cwd, "system-prompt.md")
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(manuel)
    return chemin


def _retirer_prompt_claude(cwd):
    chemin = os.path.join(cwd, "system-prompt.md")
    try:
        os.remove(chemin)
    except FileNotFoundError:
        pass


def _preparer_prompt_claude(manuel, cwd, reprendre, entree):
    """Retourne un prompt systeme seulement au bootstrap ou apres changement."""
    empreinte = _empreinte_manuel(manuel)
    injecter = (not reprendre or
                entree.get("manuel_sha256_claude") != empreinte)
    if injecter:
        prompt = _prompt_claude(manuel, cwd)
    else:
        _retirer_prompt_claude(cwd)
        prompt = None
    return empreinte, prompt, injecter


def _creation_sans_fenetre(detache=False):
    if os.name == "nt":
        return {"creationflags": 0x08000000 | (0x00000200 if detache else 0)}
    return {"start_new_session": True} if detache else {}


def _executer_flux(commande, message, cwd, env, timeout, on_event=None,
                   on_stderr=None, heartbeat=None, on_heartbeat=None,
                   transcript=None):
    processus = subprocess.Popen(
        commande, cwd=cwd, env=env, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8", errors="replace", bufsize=1,
        **_creation_sans_fenetre())
    processus.stdin.write(message)
    processus.stdin.close()
    messages = queue.Queue()

    def lire_flux(nom, flux):
        try:
            for ligne in iter(flux.readline, ""):
                messages.put((nom, ligne.rstrip("\r\n")))
        finally:
            messages.put((nom, None))

    for nom, flux in (("stdout", processus.stdout),
                      ("stderr", processus.stderr)):
        threading.Thread(target=lire_flux, args=(nom, flux), daemon=True,
                         name="agent-%s" % nom).start()

    # `timeout=None` : LA SESSION N'EXPIRE PAS. Un plafond ne se justifie que
    # s'il protege de quelque chose de nomme, et celui-ci ne protegeait de
    # rien : le processus rend la main quand il a fini. Ce qu'il faisait, en
    # revanche, se mesure — hann-bourbe, le 31.8, a travaille 20 appels
    # d'outils, fait son P.10, pose sa question a son arbitre, et le couperet
    # l'a tue au milieu : journee entiere perdue, zero octet ecrit, et le
    # traceback remonte dans sa propre pensee. Un plafond qui coupe un homme
    # au travail ne sauve rien ; il detruit ce qui etait presque fait.
    debut = time.monotonic()
    prochain = debut + (heartbeat or (timeout or 0) + 1)
    fin = (debut + timeout) if timeout else None
    ouverts, lignes, erreurs, evenements = 2, [], [], []
    while ouverts or processus.poll() is None:
        maintenant = time.monotonic()
        if fin is not None and maintenant >= fin:
            processus.kill()
            processus.wait(timeout=5)
            raise subprocess.TimeoutExpired(commande, timeout)
        bornes = [1.0, max(0.05, prochain - maintenant)]
        if fin is not None:
            bornes.append(max(0.05, fin - maintenant))
        attente = min(bornes)
        try:
            origine, ligne = messages.get(timeout=attente)
        except queue.Empty:
            origine, ligne = None, None
        if origine is not None:
            if ligne is None:
                ouverts -= 1
            elif origine == "stderr":
                erreurs.append(ligne)
                if on_stderr:
                    on_stderr(ligne)
            elif ligne:
                lignes.append(ligne)
                try:
                    ev = json.loads(ligne)
                except ValueError:
                    ev = None
                if ev is not None:
                    evenements.append(ev)
                    if on_event:
                        on_event(ev)
        maintenant = time.monotonic()
        if heartbeat and maintenant >= prochain:
            if on_heartbeat:
                on_heartbeat(round(maintenant - debut, 1))
            prochain = maintenant + heartbeat
    code = processus.wait()
    if transcript:
        with io.open(transcript, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"type": "le_conseil.user",
                                "message": message}, ensure_ascii=False) + "\n")
            for ev in evenements:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return code, lignes, erreurs, evenements, time.monotonic() - debut


def _normaliser_codex(evenements, modele, duree, logique, transcript):
    thread_id, resultat, usage = None, u"", {}
    gestes = []
    erreur = None
    for ev in evenements:
        typ = ev.get("type")
        if typ == "thread.started":
            thread_id = ev.get("thread_id")
        elif typ == "turn.completed":
            usage = ev.get("usage") or usage
        elif typ in ("turn.failed", "error"):
            erreur = ev.get("error") or ev.get("message") or erreur
        elif typ == "item.completed":
            item = ev.get("item") or {}
            if item.get("type") == "agent_message":
                resultat = item.get("text") or resultat
            elif item.get("type") in ("command_execution", "mcp_tool_call",
                                      "file_change"):
                cible = (item.get("command") or item.get("name") or
                         item.get("path") or item.get("id") or "")
                gestes.append(u"%s %s" % (item.get("type"), str(cible)[:160]))
    if erreur:
        raise RuntimeError(str(erreur)[:500])
    return {
        "type": "result", "subtype": "success", "result": resultat,
        "session_id": thread_id or logique, "logical_session_id": logique,
        "provider": "codex", "model": modele, "usage": usage,
        "duration_ms": int(duree * 1000), "duration_api_ms": 0,
        "total_cost_usd": 0.0, "num_turns": 1,
        "transcript_path": transcript, "gestes": gestes,
    }


def _est_mj(role):
    role = str(role or "")
    return role == "mj" or role.startswith("mj-")


def _commande_codex(cwd, modele, effort, add_dirs, transcript_sortie,
                    thread_id=None, sans_sandbox=False):
    commande = [
        "codex", "exec", "--ignore-user-config", "--ignore-rules",
        "--disable", "plugins", "--disable", "apps",
        "--disable", "memories", "--disable", "multi_agent",
        "--json", "--color", "never", "--skip-git-repo-check",
        "--cd", cwd,
        # Le manuel MJ assemble notamment le CLAUDE.md racine et depasse la
        # limite documentaire par defaut de Codex. Le bootstrap doit arriver
        # entier, meme s'il n'arrive desormais qu'une fois.
        "-c", "project_doc_max_bytes=524288",
        "--model", modele,
        "-c", 'model_reasoning_effort=%s' % json.dumps(effort),
        "--output-last-message", transcript_sortie,
    ]
    if sans_sandbox:
        # Un MJ tient le monde : pas de sandbox, pas de reviewer entre sa
        # decision et les portes du depot. C'est volontairement plus large
        # que workspace-write et reserve aux ids `mj` / `mj-*`.
        commande += ["--dangerously-bypass-approvals-and-sandbox"]
    else:
        # Les habitants ordinaires restent en workspace-write avec reviewer.
        commande += ["--approve-for-me"]
    for chemin in add_dirs:
        commande += ["--add-dir", chemin]
    if thread_id:
        commande += ["resume", thread_id, "-"]
    else:
        commande += ["-"]
    return commande


def _appel_codex(manuel, message, logique, modele, effort, timeout, cwd,
                  add_dirs, reprendre, env, on_event, on_stderr, heartbeat,
                  on_heartbeat, sans_sandbox=False):
    entree = _entree_session(logique)
    thread_id = entree.get("codex_thread_id")
    if reprendre is True and not thread_id:
        raise RuntimeError("aucun thread Codex pour reprendre %s" % logique)
    if reprendre is False:
        thread_id = None
        entree = {}
    manuel_sha256, prompt_injecte = _preparer_prompt_codex(
        manuel, cwd, thread_id, entree)
    final = os.path.join(cwd, ".dernier-message-%s.txt" % uuid.uuid4().hex)
    transcript = os.path.join(cwd, ".codex-%s.jsonl" % uuid.uuid4().hex)
    commande = _commande_codex(cwd, modele, effort, add_dirs, final,
                               thread_id, sans_sandbox=sans_sandbox)
    code, _lignes, erreurs, evenements, duree = _executer_flux(
        commande, message, cwd, env, timeout, on_event, on_stderr,
        heartbeat, on_heartbeat, transcript)
    rep = _normaliser_codex(evenements, modele, duree, logique, transcript)
    if not rep["result"] and os.path.exists(final):
        rep["result"] = io.open(final, encoding="utf-8",
                                errors="replace").read().strip()
    if code != 0:
        raise RuntimeError(("\n".join(erreurs) or
                            "codex a quitte avec le code %d" % code)[-800:])
    vrai = rep.get("session_id")
    if not vrai:
        raise RuntimeError("Codex n'a rendu aucun thread_id")
    _poser_session_codex(logique, vrai, modele, transcript,
                         manuel_sha256=manuel_sha256)
    if prompt_injecte:
        _retirer_prompt_codex(cwd)
    return rep


def _commande_claude(prompt_systeme, modele, effort, add_dirs, tools,
                      settings, sid, reprendre, stream,
                      sans_sandbox=False):
    # Meme invariant que Codex : aucune session n'est materiellement privee
    # d'ecriture. Un juge peut avoir pour CONSIGNE de ne rien modifier ; ce
    # n'est pas au runtime de lui casser les mains. L'ordre preserve les
    # outils demandes, puis ajoute seulement ceux qui manquent.
    outils = list(tools or [])
    for outil in ("Read", "Grep", "Glob", "Bash", "Write", "Edit"):
        if outil not in outils:
            outils.append(outil)
    commande = ["claude", "-p"]
    if prompt_systeme:
        commande += ["--system-prompt-file", prompt_systeme]
    for chemin in add_dirs:
        commande += ["--add-dir", chemin]
    if sans_sandbox:
        commande += ["--dangerously-skip-permissions"]
    else:
        commande += ["--restricted"]
    commande += ["--tools", ",".join(outils)]
    if "Bash" in outils:
        commande += ["--allowedTools", "Bash(python:*)"]
    commande += ["--output-format", "stream-json" if stream else "json"]
    if stream:
        commande += ["--verbose"]
    if not sans_sandbox:
        commande += ["--permission-mode", "acceptEdits"]
    if settings:
        commande += ["--settings", settings]
    if modele:
        commande += ["--model", modele]
    if effort:
        commande += ["--effort", effort]
    commande += ["--resume" if reprendre else "--session-id", sid]
    return commande


def _appel_claude(manuel, message, logique, modele, effort, timeout, cwd,
                   add_dirs, tools, settings, reprendre, env, on_event,
                   on_stderr, heartbeat, on_heartbeat,
                   sans_sandbox=False):
    stream = bool(on_event or on_stderr or heartbeat)
    essais = [reprendre] if reprendre is not None else [False, True]
    entree = _entree_session(logique)
    dernier = u""
    for reprise in essais:
        manuel_sha256, prompt, prompt_injecte = _preparer_prompt_claude(
            manuel, cwd, reprise, entree)
        commande = _commande_claude(prompt, modele, effort, add_dirs, tools,
                                    settings, logique, reprise, stream,
                                    sans_sandbox=sans_sandbox)
        if stream:
            code, lignes, erreurs, evs, _duree = _executer_flux(
                commande, message, cwd, env, timeout, on_event, on_stderr,
                heartbeat, on_heartbeat)
            resultat = next((ev for ev in reversed(evs)
                              if ev.get("type") == "result"), None)
            sortie = "\n".join(lignes)
        else:
            r = subprocess.run(commande, cwd=cwd, env=env,
                               input=message.encode("utf-8"),
                               capture_output=True, timeout=timeout,
                               **_creation_sans_fenetre())
            code = r.returncode
            sortie = r.stdout.decode("utf-8", "replace")
            erreurs = [r.stderr.decode("utf-8", "replace")]
            try:
                resultat = json.loads(sortie)
            except ValueError:
                resultat = None
        dernier = sortie + "\n" + "\n".join(erreurs)
        if "already in use" in dernier and reprendre is None:
            continue
        if code != 0:
            raise RuntimeError(("\n".join(erreurs) or
                                "claude a quitte avec le code %d" % code)[-800:])
        if not resultat:
            raise RuntimeError("le flux Claude s'est ferme sans resultat")
        resultat.setdefault("provider", "claude")
        resultat.setdefault("logical_session_id", logique)
        resultat.setdefault("session_id", logique)
        resultat.setdefault("model", modele or "defaut")
        _poser_empreinte_manuel(logique, "claude", manuel_sha256)
        if prompt_injecte:
            _retirer_prompt_claude(cwd)
        return resultat
    raise RuntimeError("ni creation ni reprise Claude n'ont abouti : %s" %
                       dernier[-400:])


def appeler(role, manuel, message, session_id, modele=None, effort=None,
            timeout=180, cwd=None, add_dirs=None, tools=None, reprendre=None,
            settings=None, env=None, on_event=None, on_stderr=None,
            heartbeat=None, on_heartbeat=None, compte_pour=None):
    """Appelle le fournisseur global et rend le contrat de reponse commun."""
    provider = fournisseur()
    modele = _modele(provider, modele)
    effort = _effort(provider, effort)
    cwd = os.path.abspath(cwd or RACINE)
    os.makedirs(cwd, exist_ok=True)
    add_dirs = [os.path.abspath(x) for x in (add_dirs or [])]
    environnement = dict(os.environ)
    environnement.update(env or {})
    environnement["LE_CONSEIL_QUI"] = str(role)
    sans_sandbox = _est_mj(role)
    # habitant.md §4 : les sessions sont de la memoire, pas une section
    # critique. Deux reprises du meme id peuvent vivre en parallele ; leur
    # entrelacement est le registre d'audiences du MJ. Seules les portes de
    # l'etat serialisent ce qui devient vrai.
    with _activite(role, session_id):
        debut_compute = time.time()
        succes, erreur_compute = False, None
        try:
            if provider == "codex":
                resultat = _appel_codex(
                    manuel, message, session_id, modele, effort, timeout, cwd,
                    add_dirs, reprendre, environnement, on_event, on_stderr,
                    heartbeat, on_heartbeat, sans_sandbox=sans_sandbox)
            else:
                resultat = _appel_claude(
                    manuel, message, session_id, modele, effort, timeout, cwd,
                    add_dirs, tools, settings, reprendre, environnement,
                    on_event, on_stderr, heartbeat, on_heartbeat,
                    sans_sandbox=sans_sandbox)
            succes = True
            return resultat
        except BaseException as e:
            erreur_compute = "%s: %s" % (type(e).__name__, str(e))
            raise
        finally:
            # Cette porte est plus basse que CALL/CAST : elle voit aussi les
            # expirations et les erreurs qui ne produiront jamais de rapport.
            try:
                from agents import compute
                compute.enregistrer(
                    role, compte_pour, session_id, provider, debut_compute,
                    time.time(), succes, erreur_compute)
            except Exception:
                pass  # la mesure ne doit jamais tuer le travail mesure


def lancer_cast(log, trace=None, **appel):
    """Lance la meme porte en detache ; le worker sait creer OU reprendre."""
    os.makedirs(REQUETES, exist_ok=True)
    requete = os.path.join(REQUETES, "%s.json" % uuid.uuid4().hex)
    provider = fournisseur()
    _ecrire_json(requete, {"appel": appel, "trace": trace,
                           "fournisseur": provider})
    worker = os.path.join(RACINE, "scripts", "agents", "runtime_worker.py")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "ab") as f:
        subprocess.Popen([sys.executable, worker, requete], cwd=RACINE,
                         stdin=subprocess.DEVNULL, stdout=f,
                         stderr=subprocess.STDOUT,
                         **_creation_sans_fenetre(detache=True))
    return {"cast": True, "log": log, "session": appel["session_id"],
            "provider": provider}
