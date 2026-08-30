#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exporte tout ce qui touche Aurore Inchauspé en fichiers .txt dans export/.

Un fichier par nature de matière : la fiche, le siège, ses paroles, ses actes,
ses livres, ses journées, ce que le fil lui a servi, et les mentions résiduelles
partout ailleurs. Lecture seule sur etat/ — rien n'est écrit hors de export/.
"""
import json
import os
import re
import sys

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import bibliotheque
from etat.expose import tables  # LA PORTE de etat/

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SORTIE = os.path.join(RACINE, "export")
ID = "aurore-inchauspe"
MOTS = re.compile(r"aurore|inchausp", re.I)

os.makedirs(SORTIE, exist_ok=True)
_ecrits = []


def lire(rel):
    # Un fichier vide ou tronque — l'inbox en porte trois de zero octet — ne
    # doit pas faire tomber tout l'export. On rend ce qu'on peut lire : c'est
    # le seul endroit ou l'on rattrape TableAbimee, et c'est un export.
    try:
        return tables.lire(os.path.join(RACINE, rel), None)
    except tables.TableAbimee:
        return None


def lignes_jsonl(rel):
    p = os.path.join(RACINE, rel)
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for n, l in enumerate(f, 1):
            l = l.strip()
            if not l:
                continue
            try:
                out.append((n, json.loads(l)))
            except json.JSONDecodeError:
                pass
    return out


def texte(o):
    return json.dumps(o, ensure_ascii=False)


def touche(o):
    return bool(MOTS.search(texte(o)))


def bloc(o):
    return json.dumps(o, ensure_ascii=False, indent=2)


def ecrire(nom, titre, morceaux):
    """morceaux : liste de (sous-titre, corps) ; les corps vides sont annoncés."""
    chemin = os.path.join(SORTIE, nom)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(titre + "\n" + "=" * len(titre) + "\n\n")
        for st, corps in morceaux:
            f.write("--- " + st + " " + "-" * max(0, 68 - len(st)) + "\n\n")
            f.write((corps.rstrip() if corps.strip() else "(rien)") + "\n\n")
    _ecrits.append((nom, os.path.getsize(chemin)))
    return chemin


def date_de(o):
    d = o.get("date") if isinstance(o, dict) else None
    if isinstance(d, dict):
        return "%s AC, %se lune, %se j." % (d.get("annee"), d.get("lune"), d.get("jour"))
    return str(d) if d else ""


# ---------------------------------------------------------------- 01 la fiche
perso = next((p for p in (lire("etat/personnages.json") or []) if p["id"] == ID), None)
maison = None
if perso:
    maison = next((m for m in (lire("etat/maisons.json") or [])
                   if m.get("id") == perso.get("maison_id")), None)
lieu = None
if perso:
    lieu = next((l for l in (lire("etat/lieux.json") or [])
                 if l.get("id") == perso.get("lieu_id")), None)
ecrire("01-fiche.txt", "AURORE INCHAUSPÉ — la fiche", [
    ("Personnage (etat/personnages.json)", bloc(perso) if perso else ""),
    ("Sa maison (etat/maisons.json)", bloc(maison) if maison else ""),
    ("Son lieu (etat/lieux.json)", bloc(lieu) if lieu else ""),
])

# ---------------------------------------------------------------- 02 le siège
joueurs = lire("etat/joueurs.json") or []
siege = next((j for j in joueurs if j.get("personnage_id") == ID), None)
horloges = lire("etat/horloges.json") or {}
ecrire("02-siege.txt", "AURORE — le siège", [
    ("Siège (etat/joueurs.json)", bloc(siege) if siege else ""),
    ("Son horloge (etat/horloges.json)", bloc(horloges.get(ID))),
    ("Ses réglages de narrateur", bloc(lire("etat/joueurs/%s/reglages.json" % ID))),
    ("Tête archivée en s'asseyant (etat/archive/tetes/)", "\n\n".join(
        "# " + n + "\n" + bloc(lire("etat/archive/tetes/" + n))
        for n in sorted(os.listdir(os.path.join(RACINE, "etat/archive/tetes")))
        if ID in n) if os.path.isdir(os.path.join(RACINE, "etat/archive/tetes")) else ""),
    ("Entrée dans intentions.json (doit être absente : siège occupé)", "\n".join(
        bloc(i) for i in (lire("etat/intentions.json") or [])
        if i.get("personnage_id") == ID) or "(absente — conforme)"),
])

# --------------------------------------------------- 03 journal et objectifs
journal = lire("etat/joueurs/%s/journal.json" % ID) or {}
scenes = journal.get("scenes", [])
ecrire("03-journal-scenes.txt", "AURORE — son journal, scène par scène", [
    ("En-tête", bloc({k: v for k, v in journal.items() if k != "scenes"})),
    ("Scènes closes (%d)" % len(scenes), "\n\n".join(bloc(s) for s in scenes)),
])

objs = lire("etat/joueurs/%s/objectifs.json" % ID) or []
ecrire("04-objectifs.txt", "AURORE — ses desseins", [
    ("etat/joueurs/%s/objectifs.json (%d)" % (ID, len(objs)),
     "\n\n".join(bloc(o) for o in objs)),
])

# ---------------------------------------------------------------- 05 paroles
paroles = lire("etat/paroles.json") or []
dites = [p for p in paroles if p.get("locuteur_id") == ID]
recues = [p for p in paroles if p.get("destinataire_id") == ID
          or ID in (p.get("destinataires") or [])]
temoin = [p for p in paroles if ID in (p.get("temoins") or [])
          and p not in dites and p not in recues]
autres = [p for p in paroles if touche(p) and p not in dites + recues + temoin]
ecrire("05-paroles.txt", "AURORE — les paroles", [
    ("Ce qu'elle a dit (%d)" % len(dites), "\n\n".join(bloc(p) for p in dites)),
    ("Ce qu'on lui a dit (%d)" % len(recues), "\n\n".join(bloc(p) for p in recues)),
    ("Ce qu'elle a entendu comme témoin (%d)" % len(temoin),
     "\n\n".join(bloc(p) for p in temoin)),
    ("Autres paroles qui la nomment (%d)" % len(autres),
     "\n\n".join(bloc(p) for p in autres)),
])

# ----------------------------------------------------------------- 06 actes
actes = lire("etat/actes.json") or []
faits = [a for a in actes if a.get("acteur_id") == ID]
subis = [a for a in actes if a.get("cible_id") == ID and a not in faits]
vus = [a for a in actes if (ID in (a.get("temoins") or [])
       or ID in (a.get("connu_de") or [])) and a not in faits + subis]
cites = [a for a in actes if touche(a) and a not in faits + subis + vus]
ecrire("06-actes.txt", "AURORE — les actes", [
    ("Ce qu'elle a fait (%d)" % len(faits), "\n\n".join(bloc(a) for a in faits)),
    ("Ce qu'on a fait sur elle (%d)" % len(subis), "\n\n".join(bloc(a) for a in subis)),
    ("Ce qu'elle a vu ou su (%d)" % len(vus), "\n\n".join(bloc(a) for a in vus)),
    ("Autres actes qui la nomment (%d)" % len(cites), "\n\n".join(bloc(a) for a in cites)),
])

# -------------------------------------------------------------- 07 relations
rels = lire("etat/relations.json") or []
depuis = [r for r in rels if r.get("source_id") == ID]
vers = [r for r in rels if r.get("cible_id") == ID]
liens = (lire("etat/liens.json") or {}).get("liens", [])
ecrire("07-relations.txt", "AURORE — ses relations", [
    ("Ce qu'elle pense des autres (%d)" % len(depuis), "\n\n".join(bloc(r) for r in depuis)),
    ("Ce que les autres pensent d'elle (%d)" % len(vers), "\n\n".join(bloc(r) for r in vers)),
    ("Liens de la table (etat/liens.json)",
     "\n\n".join(bloc(l) for l in liens if touche(l))),
])

# ---------------------------------------------------------------- 08 livres
books = bibliotheque.charger(tables.ETAT)
siens = [b for b in books if b.get("acteur_id") == ID]
lanomment = [b for b in books if touche(b) and b not in siens]


def rendre_livre(b):
    t = ["# %s — %s" % (b.get("id"), b.get("titre"))]
    for k in ("sous_titre", "type", "acteur_id", "salle_id", "prive", "embleme", "couleur"):
        if b.get(k) not in (None, ""):
            t.append("  %s: %s" % (k, b[k]))
    if b.get("colonnes"):
        t.append("  colonnes: " + " | ".join(str(c) for c in b["colonnes"]))
    for l in b.get("lignes", []) or []:
        if isinstance(l, list):
            t.append("    - " + " | ".join("" if c is None else str(c) for c in l))
        else:
            t.append("    - " + texte(l))
    for k, v in b.items():
        if k not in ("id", "titre", "sous_titre", "type", "acteur_id", "salle_id",
                     "prive", "embleme", "couleur", "colonnes", "lignes"):
            t.append("  %s: %s" % (k, texte(v)))
    return "\n".join(t)


ecrire("08-livres.txt", "AURORE — les livres", [
    ("Les livres qu'elle porte (%d)" % len(siens), "\n\n".join(rendre_livre(b) for b in siens)),
    ("Les livres qui la nomment (%d)" % len(lanomment),
     "\n\n".join(rendre_livre(b) for b in lanomment)),
])

# ------------------------------------------------------- 09 journées et pensées
travaux = (lire("etat/travaux.json") or {}).get("travaux", [])
if isinstance(travaux, dict):
    sien = [travaux[ID]] if ID in travaux else []
else:
    sien = [t for t in travaux if t.get("qui") == ID or touche(t)]
journees = [(n, o) for n, o in lignes_jsonl("etat/journees.jsonl") if touche(o)]
arch = os.path.join(RACINE, "etat/archive/journees")
arch_f = sorted(n for n in os.listdir(arch) if ID in n) if os.path.isdir(arch) else []
stag = os.path.join(RACINE, "etat/rapports")
stag_f = sorted(n for n in os.listdir(stag) if ID in n) if os.path.isdir(stag) else []
ecrire("09-journees-et-pensees.txt", "AURORE — ses journées de travail", [
    ("Ses affaires dans etat/travaux.json (%d)" % len(sien),
     "\n\n".join(bloc(t) for t in sien)),
    ("Journées du registre (etat/journees.jsonl, %d)" % len(journees),
     "\n\n".join("# ligne %d\n%s" % (n, bloc(o)) for n, o in journees)),
    ("Journées archivées", "\n\n".join("# " + n + "\n" + bloc(lire("etat/archive/journees/" + n))
                                       for n in arch_f)),
    ("Travaux rendus", "\n\n".join("# " + n + "\n" + bloc(lire("etat/rapports/" + n))
                                       for n in stag_f)),
])

# ------------------------------------------------- 10 ce qu'elle croit / voit
ecrire("10-ce-quelle-croit.txt", "AURORE — sa table de guerre et ses vues", [
    ("Ses jetons (etat/joueurs/%s/jetons.json)" % ID,
     bloc(lire("etat/joueurs/%s/jetons.json" % ID))),
    ("Ses vues — dernières positions connues", bloc(lire("etat/joueurs/%s/vues.json" % ID))),
])

# ---------------------------------------------------------- 11 notes de régie
def fichier_texte(rel):
    p = os.path.join(RACINE, rel)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


veille_dir = os.path.join(RACINE, "etat/veille")
notes_veille = []
if os.path.isdir(veille_dir):
    for n in sorted(os.listdir(veille_dir)):
        c = fichier_texte("etat/veille/" + n)
        if MOTS.search(c) or MOTS.search(n):
            notes_veille.append("##### " + n + "\n" + c.rstrip())
ecrire("11-notes-de-regie.txt", "AURORE — notes hors fiction (régie)", [
    ("etat/joueurs/%s/notes.txt" % ID, fichier_texte("etat/joueurs/%s/notes.txt" % ID)),
    ("etat/joueurs/%s/note-du-principal.md" % ID,
     fichier_texte("etat/joueurs/%s/note-du-principal.md" % ID)),
    ("Veille et notes entre MJ (etat/veille/)", "\n\n".join(notes_veille)),
])

# --------------------------------------------------------------- 12 le fil
flux = lignes_jsonl("etat/flux.jsonl")
pour_elle = [(n, o) for n, o in flux if ID in (o.get("pour") or [])]
la_nomment = [(n, o) for n, o in flux if touche(o) and (n, o) not in pour_elle]


def rendre_item(n, o):
    ent = "[l.%d] %s" % (n, o.get("type", "?"))
    for k in ("date", "moment", "lieu", "locuteur_id", "acteur_id"):
        v = o.get(k)
        if v:
            ent += " | %s=%s" % (k, date_de(o) if k == "date" else v)
    corps = o.get("texte") or ""
    reste = {k: v for k, v in o.items()
             if k not in ("type", "date", "moment", "lieu", "locuteur_id",
                          "acteur_id", "texte", "portrait_svg", "pour")}
    s = ent + "\n" + (corps.strip() + "\n" if corps else "")
    if reste:
        s += "  ." + texte(reste)[:1500] + "\n"
    return s


ecrire("12-le-fil-mentions.txt", "AURORE — items publics ou d'autres sièges qui la nomment", [
    ("etat/flux.jsonl (%d)" % len(la_nomment),
     "\n".join(rendre_item(n, o) for n, o in la_nomment)),
])

# Son écran est long (des milliers d'items) : un fichier par jour de jeu,
# la date courant du dernier item qui en portait une.
jours = []
courant = "sans-date"
for n, o in pour_elle:
    d = o.get("date")
    if isinstance(d, dict) and d.get("jour"):
        courant = "%03d-%d-%02d" % (d.get("annee", 0), d.get("lune", 0), d["jour"])
    if not jours or jours[-1][0] != courant:
        jours.append((courant, []))
    jours[-1][1].append((n, o))
# regrouper les tranches d'un même jour éparpillées
groupes = {}
for cle, items in jours:
    groupes.setdefault(cle, []).extend(items)
for cle in sorted(groupes):
    items = groupes[cle]
    ecrire("12-fil-%s.txt" % cle,
           "AURORE — son écran, %s (%d items)" % (cle, len(items)),
           [("etat/flux.jsonl, items portant pour=%s" % ID,
             "\n".join(rendre_item(n, o) for n, o in items))])

# --------------------------------------------- 13 mentions partout ailleurs
DEJA = {"etat/personnages.json", "etat/paroles.json", "etat/actes.json",
        "etat/relations.json", "etat/books.json", "etat/flux.jsonl",
        "etat/joueurs.json", "etat/journees.jsonl", "etat/travaux.json",
        "etat/liens.json", "etat/horloges.json"}
ailleurs = []
for nom in sorted(os.listdir(os.path.join(RACINE, "etat"))):
    rel = "etat/" + nom
    if not nom.endswith(".json") or rel in DEJA:
        continue
    d = lire(rel)
    if d is None or not MOTS.search(texte(d)):
        continue
    trouves = []
    it = d if isinstance(d, list) else (
        [{k: v} for k, v in d.items()] if isinstance(d, dict) else [])
    for e in it:
        if touche(e):
            trouves.append(bloc(e))
    ailleurs.append("##### " + rel + " (%d entrées)\n" % len(trouves) +
                    "\n\n".join(trouves))
# sous-dossiers d'état
for sous in ("etat/plis.json",):
    pass
mentions_docs = []
for rep in ("docs", "musiques", "analyse"):
    d = os.path.join(RACINE, rep)
    if not os.path.isdir(d):
        continue
    for base, _dirs, fics in os.walk(d):
        for n in sorted(fics):
            if not n.endswith((".md", ".txt", ".json")):
                continue
            rel = os.path.relpath(os.path.join(base, n), RACINE).replace("\\", "/")
            c = fichier_texte(rel)
            if MOTS.search(c):
                hits = [l.strip() for l in c.splitlines() if MOTS.search(l)]
                mentions_docs.append("##### " + rel + " (%d lignes)\n" % len(hits) +
                                     "\n".join("  " + h for h in hits))
ecrire("13-mentions-ailleurs.txt", "AURORE — mentions dans le reste de l'état", [
    ("Tables d'état non couvertes par les autres fichiers", "\n\n".join(ailleurs)),
    ("Documentation, analyses, chansons", "\n\n".join(mentions_docs)),
])

# ------------------------------------------------------------- 14 l'inbox
inbox = os.path.join(RACINE, "etat/inbox", ID)
actions = []
if os.path.isdir(inbox):
    for n in sorted(os.listdir(inbox)):
        actions.append("##### " + n + "\n" + bloc(lire("etat/inbox/%s/%s" % (ID, n))))
parloir = []
pdir = os.path.join(RACINE, "etat/parloir")
if os.path.isdir(pdir):
    for base, _d, fics in os.walk(pdir):
        for n in sorted(fics):
            rel = os.path.relpath(os.path.join(base, n), RACINE).replace("\\", "/")
            c = fichier_texte(rel)
            if MOTS.search(c) or MOTS.search(n):
                parloir.append("##### " + rel + "\n" + c.rstrip())
ecrire("14-inbox-et-parloir.txt", "AURORE — ce qui n'est pas encore traité", [
    ("etat/inbox/%s/ (%d actions en attente)" % (ID, len(actions)), "\n\n".join(actions)),
    ("Fils du parloir la concernant", "\n\n".join(parloir)),
])

# ----------------------------------------------------------------- 00 index
horloge = horloges.get(ID) or {}
entete = [
    "Personnage : %s — %s" % (perso.get("nom") if perso else ID,
                              perso.get("titre") if perso else ""),
    "Identifiant d'état : " + ID,
    "Siège : %s (jeton %s, %s)" % (
        (siege or {}).get("role"), (siege or {}).get("jeton"),
        "occupé" if (siege or {}).get("occupe") else "vacant"),
    "Son horloge : %s AC, %se lune, %se jour, minute %s" % (
        horloge.get("annee"), horloge.get("lune"), horloge.get("jour"),
        horloge.get("minute")),
    "Lieu : " + str((perso or {}).get("lieu_id")),
]
ecrire("00-index.txt", "AURORE INCHAUSPÉ — export complet", [
    ("Qui elle est", "\n".join(entete)),
    ("Les fichiers de cet export", "\n".join(
        "  %-32s %7d octets" % (n, t) for n, t in sorted(_ecrits))),
    ("Comment il a été fait",
     "Lecture seule de etat/, docs/, musiques/, analyse/.\n"
     "Sélection : identifiant exact (%s) dans les champs d'acteur, plus toute\n"
     "entrée dont le texte contient « aurore » ou « inchausp ».\n"
     "Regénérable par : python scripts/analyse/exporter_aurore.py" % ID),
])

sys.stdout.reconfigure(encoding="utf-8")
for n, t in sorted(_ecrits):
    print("%-34s %8d" % (n, t))
