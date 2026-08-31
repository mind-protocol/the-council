import re
import os
import sys

# Patch fournisseur.py
with open("scripts/fournisseur.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("(\"claude\", \"codex\", \"chatgpt\")", "(\"claude\", \"codex\", \"chatgpt\", \"gemini\")")
with open("scripts/fournisseur.py", "w", encoding="utf-8") as f:
    f.write(text)

# Patch runtime.py
with open("scripts/agents/runtime.py", "r", encoding="utf-8") as f:
    text = f.read()

# FOURNISSEURS
text = text.replace(
    "FOURNISSEURS = {\"claude\": \"claude\", \"codex\": \"codex\", \"chatgpt\": \"codex\"}",
    "FOURNISSEURS = {\"claude\": \"claude\", \"codex\": \"codex\", \"chatgpt\": \"codex\", \"gemini\": \"gemini\"}"
)

# configuration()
cfg_old = """        "modele_claude": (os.environ.get("LE_CONSEIL_CLAUDE_MODELE") or
                           os.environ.get("LE_CONSEIL_CLAUDE_MODEL") or
                           d.get("modele_claude")),
    }"""
cfg_new = """        "modele_claude": (os.environ.get("LE_CONSEIL_CLAUDE_MODELE") or
                           os.environ.get("LE_CONSEIL_CLAUDE_MODEL") or
                           d.get("modele_claude")),
        "modele_gemini": (os.environ.get("LE_CONSEIL_GEMINI_MODELE") or
                           os.environ.get("LE_CONSEIL_GEMINI_MODEL") or
                           d.get("modele_gemini")),
    }"""
text = text.replace(cfg_old, cfg_new)

# choisir()
choisir_old = """    elif modele:
        d["modele_claude"] = modele
    _ecrire_json(CONFIG, d)"""
choisir_new = """    elif canonique == "gemini" and modele:
        d["modele_gemini"] = modele
    elif modele:
        d["modele_claude"] = modele
    _ecrire_json(CONFIG, d)"""
text = text.replace(choisir_old, choisir_new)

# _modele()
modele_old = """    if demande and not (str(demande).startswith("gpt-") or
                        "codex" in str(demande).casefold()):
        return str(demande)
    return cfg.get("modele_claude")"""
modele_new = """    if provider == "gemini":
        return str(demande) if demande else cfg.get("modele_gemini")
    if demande and not (str(demande).startswith("gpt-") or
                        "codex" in str(demande).casefold()):
        return str(demande)
    return cfg.get("modele_claude")"""
text = text.replace(modele_old, modele_new)

# _appel_gemini code to inject
gemini_code = """
def _preparer_prompt_gemini(manuel, cwd, reprendre, entree):
    empreinte = _empreinte_manuel(manuel)
    injecter = (not reprendre or
                entree.get("manuel_sha256_gemini") != empreinte)
    chemin = os.path.join(cwd, "system-prompt-gemini.md")
    if injecter:
        with io.open(chemin, "w", encoding="utf-8", newline="\\n") as f:
            f.write(manuel)
        prompt = chemin
    else:
        try:
            os.remove(chemin)
        except FileNotFoundError:
            pass
        prompt = None
    return empreinte, prompt, injecter

def _commande_gemini(prompt_systeme, modele, add_dirs, sid, reprendre):
    # TODO: Ajustez les arguments CLI selon votre vrai binaire Gemini
    commande = ["gemini"]
    if prompt_systeme:
        commande += ["--system-prompt-file", prompt_systeme]
    for chemin in add_dirs:
        commande += ["--add-dir", chemin]
    if modele:
        commande += ["--model", modele]
    commande += ["--resume" if reprendre else "--session-id", sid]
    # Options similaires a claude (sortie json attendue par appeler)
    commande += ["--output-format", "json"]
    return commande

def _appel_gemini(manuel, message, logique, modele, effort, timeout, cwd,
                  add_dirs, tools, settings, reprendre, env):
    entree = _entree_session(logique)
    essais = [reprendre] if reprendre is not None else [False, True]
    dernier = ""
    for reprise in essais:
        manuel_sha256, prompt, prompt_injecte = _preparer_prompt_gemini(
            manuel, cwd, reprise, entree)
        commande = _commande_gemini(prompt, modele, add_dirs, logique, reprise)
        
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
            
        dernier = sortie + "\\n" + "\\n".join(erreurs)
        if "already in use" in dernier and reprendre is None:
            continue
        if code != 0:
            raise RuntimeError(("\\n".join(erreurs) or
                                "gemini a quitte avec le code %d" % code)[-800:])
        if not resultat:
            raise RuntimeError("le flux Gemini s\\'est ferme sans resultat")
            
        resultat.setdefault("provider", "gemini")
        resultat.setdefault("logical_session_id", logique)
        resultat.setdefault("session_id", logique)
        resultat.setdefault("model", modele or "defaut")
        _poser_empreinte_manuel(logique, "gemini", manuel_sha256)
        
        if prompt_injecte and prompt:
            try:
                os.remove(prompt)
            except (OSError, TypeError):
                pass
        return resultat
    raise RuntimeError("ni creation ni reprise Gemini n\\'ont abouti : %s" % dernier[-400:])

def appeler("""

text = text.replace("def appeler(", gemini_code)

appeler_old = """            if provider == "codex":
                resultat = _appel_codex(
                    manuel, message, session_id, modele, effort, timeout, cwd,
                    add_dirs, reprendre, environnement, on_event, on_stderr,
                    heartbeat, on_heartbeat)
            else:
                resultat = _appel_claude(
                    manuel, message, session_id, modele, effort, timeout, cwd,
                    add_dirs, tools, settings, reprendre, environnement,
                    on_event, on_stderr, heartbeat, on_heartbeat)"""

appeler_new = """            if provider == "codex":
                resultat = _appel_codex(
                    manuel, message, session_id, modele, effort, timeout, cwd,
                    add_dirs, reprendre, environnement, on_event, on_stderr,
                    heartbeat, on_heartbeat)
            elif provider == "gemini":
                resultat = _appel_gemini(
                    manuel, message, session_id, modele, effort, timeout, cwd,
                    add_dirs, tools, settings, reprendre, environnement)
            else:
                resultat = _appel_claude(
                    manuel, message, session_id, modele, effort, timeout, cwd,
                    add_dirs, tools, settings, reprendre, environnement,
                    on_event, on_stderr, heartbeat, on_heartbeat)"""

text = text.replace(appeler_old, appeler_new)

with open("scripts/agents/runtime.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Patch OK")
