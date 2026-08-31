# -*- coding: utf-8 -*-
"""PORTAGE — le brief court d'un message joueur au MJ (D.34).

Un message joueur n'a pas besoin d'un second manuel : il a besoin d'adresses.
Ce module lui donne les actions exactes encore en inbox, une fenetre courte du
fil canonique de ce siege avec ses numeros de lignes, puis seulement quelques
lignes de registre qui repondent aux noms ou references effectivement cites.

La recherche est celle de matiere.dossier_registres (D.36 : rend
(lignes, voisines, ailleurs), filtre CONJONCTIF sur les sujets). Jamais
bloquant : un inbox vide, un JSON casse ou une extraction vide n'ajoutent
rien — la matiere est un confort, jamais une condition.
"""
import io
import json
import os
import re

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

FLUX = os.path.join(RACINE, "etat", "flux.jsonl")
FIL_MAX = 8
TEXTE_FIL_MAX = 220
LIGNES_MAX = 3      # le reste est pointe, pas recopie dans le reveil
CELLULE_MAX = 160

# Des majuscules qui ne nomment personne : les demarrages de phrase usuels.
_VIDES = {"le", "la", "les", "un", "une", "des", "je", "tu", "il", "elle",
          "on", "nous", "vous", "ils", "elles", "ce", "cette", "ces", "mon",
          "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "et", "ou",
          "mais", "donc", "que", "qui", "quoi", "dans", "pour", "avec",
          "sans", "sur", "sous", "vers", "chez", "si", "quand", "comme"}


def sujets_du_texte(texte):
    """Les nombres et les noms propres d'un message, normalises
    (matiere.sans_accents) — ce qu'on peut chercher dans un registre."""
    from agents import matiere
    sujets = []
    for nombre in re.findall(r"\d+", texte or u""):
        if nombre not in sujets:
            sujets.append(nombre)
    for mot in re.findall(u"\\b[A-ZÀ-Ý][\\wà-ÿ\\-]{2,}\\b", texte or u""):
        s = matiere.sans_accents(mot)
        if s not in _VIDES and s not in sujets:
            sujets.append(s)
    return sujets[:8]


def matiere_du_message(personnage, actions=None):
    """La section « CE QUE LES REGISTRES ARRETENT » pour les messages du
    personnage en inbox (les fichiers action-*.json presents sont les non
    traites ; le lanceur les retire apres une vraie poussee) — ou u"" si rien
    ne s'y prete."""
    try:
        from agents import matiere
        textes = []
        actions = (_actions_en_attente(personnage)
                   if actions is None else actions)
        for _chemin, action in reversed(actions):
            if action.get("texte"):
                textes.append(str(action["texte"]))
        if not textes:
            return u""
        sujets = sujets_du_texte(u" ".join(textes))
        if not sujets:
            return u""
        # Tous les sujets d'abord (le filtre est conjonctif) ; si rien ne
        # porte tout, chaque sujet seul, jusqu'au plafond. Un nombre seul ne
        # se cherche jamais : la recherche est en sous-chaine, et « 9 » se
        # trouve dans chaque numero de piece (mesure au banc du 31.8).
        lignes, _, _ = matiere.dossier_registres(sujets)
        if not lignes and len(sujets) > 1:
            for s in sujets:
                if s.isdigit():
                    continue
                seules, _, _ = matiere.dossier_registres([s])
                lignes.extend(x for x in seules if x not in lignes)
                if len(lignes) >= LIGNES_MAX:
                    break
        if not lignes:
            return u""
        rendues = []
        for volume, table, cellules in lignes[:LIGNES_MAX]:
            texte = u" | ".join(str(c) for c in cellules)
            if len(texte) > CELLULE_MAX:
                texte = texte[:CELLULE_MAX] + u"…"
            rendues.append(u"  · [%s / %s] %s" % (volume, table or u"—",
                                                  texte))
        return (u"\nCE QUE LES REGISTRES ARRETENT sur son message :\n"
                + u"\n".join(rendues) + u"\n")
    except Exception:
        return u""


def _actions_en_attente(personnage):
    dossier = os.path.join(RACINE, "etat", "inbox", personnage)
    actions = []
    if not os.path.isdir(dossier):
        return actions
    candidats = [os.path.join(dossier, nom)
                  for nom in sorted(os.listdir(dossier))
                  if nom.startswith("action-") and nom.endswith(".json")]
    for chemin in candidats:
        try:
            with io.open(chemin, encoding="utf-8") as f:
                action = json.load(f)
            if isinstance(action, dict):
                actions.append((chemin, action))
        except Exception:
            continue
    return actions


def _visible_pour(item, personnage):
    audience = item.get("pour")
    if isinstance(audience, list):
        return personnage in audience or "tous" in audience
    return audience in (personnage, "tous")


def _aplatir(texte):
    return re.sub(r"\s+", " ", str(texte or "")).strip()


def _texte_du_fil(item):
    texte = _aplatir(item.get("texte"))
    options = item.get("options") or []
    if options:
        choix = [str(o.get("texte") or o.get("id")) for o in options
                 if isinstance(o, dict) and (o.get("texte") or o.get("id"))]
        if choix:
            texte += (" | options: " if texte else "options: ") + " / ".join(choix)
    if len(texte) > TEXTE_FIL_MAX:
        texte = texte[:TEXTE_FIL_MAX - 1] + u"…"
    return texte


def _items_visibles_du_flux(personnage):
    visibles = []
    try:
        with io.open(FLUX, encoding="utf-8", errors="replace") as f:
            for numero, ligne in enumerate(f, 1):
                try:
                    item = json.loads(ligne)
                except ValueError:
                    continue
                if isinstance(item, dict) and _visible_pour(item, personnage):
                    visibles.append((numero, item))
    except OSError:
        pass
    return visibles


def _ligne_de_l_action(visibles, action):
    ref = str(action.get("ref") or "")
    if ref:
        for numero, item in reversed(visibles):
            if str(item.get("ref") or "") == ref:
                return numero
    cherche = _aplatir(action.get("texte"))
    if not cherche:
        return None
    for numero, item in reversed(visibles):
        if _aplatir(item.get("texte")) == cherche:
            return numero
    return None


def fil_du_joueur(personnage, limite=FIL_MAX, visibles=None):
    """Pointe et montre la fin visible du flux canonique de ce siege."""
    visibles = (_items_visibles_du_flux(personnage)
                if visibles is None else visibles)

    out = [u"FIL CANONIQUE DU PJ : %s" % os.path.abspath(FLUX)]
    if not visibles:
        out.append(u"  Aucun item adresse a %s." % personnage)
        return u"\n".join(out)
    fenetre = visibles[-max(1, int(limite)):]
    out.append(u"  Fenetre jointe : %d derniers items visibles ; chaque L<n> "
               u"est la ligne exacte du JSONL." % len(fenetre))
    for numero, item in fenetre:
        marque = item.get("locuteur_id") or item.get("qui") or "-"
        heure = item.get("heure") or "--"
        out.append(u"  L%d · %s · %s · %s | %s" % (
            numero, heure, item.get("type") or "?", marque,
            _texte_du_fil(item)))
    return u"\n".join(out)


def brief_message_joueur(personnage, refs=None):
    """Le seul contexte repete a chaque POST du joueur."""
    actions = _actions_en_attente(personnage)
    if refs is not None:
        refs = {str(ref) for ref in refs}
        actions = [(chemin, action) for chemin, action in actions
                   if str(action.get("ref") or "") in refs]
    visibles = _items_visibles_du_flux(personnage)
    inbox = os.path.abspath(os.path.join(RACINE, "etat", "inbox", personnage))
    out = [u"== BRIEF MESSAGE JOUEUR — %s" % personnage,
           u"INBOX CANONIQUE : %s" % inbox]
    if not actions:
        out.append(u"  Aucune action-* presente.")
    else:
        for chemin, action in actions:
            ligne_flux = _ligne_de_l_action(visibles, action)
            out.append(u"  ACTION %s · ref %s · mode %s · recue %s" % (
                os.path.abspath(chemin), action.get("ref") or "—",
                action.get("mode") or action.get("type") or "—",
                action.get("recu_a") or "—"))
            out.append(u"    TEXTE EXACT : %s" % str(action.get("texte") or ""))
            out.append(u"    DANS LE FLUX : %s" % (
                "L%d" % ligne_flux if ligne_flux else
                "INTROUVABLE — l'inbox est la source de cette action"))
    out.extend([u"", fil_du_joueur(personnage, visibles=visibles)])
    registres = matiere_du_message(personnage, actions=actions).strip()
    if registres:
        out.extend([u"", registres])
    out.extend([
        u"",
        u"Le reste n'est pas recopie ici. Si le fil ne suffit pas : "
        u"`python scripts/reprise.py --qui %s`, puis ouvre seulement les "
        u"adresses qu'il pointe." % personnage,
    ])
    return u"\n".join(out).strip() + u"\n"
