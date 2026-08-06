# -*- coding: utf-8 -*-
"""Crée le schéma du monde dans la base Airtable (source de vérité du jeu).

Idempotent : les tables déjà présentes sont sautées. Écrit la carte des ids
(table/champ) dans airtable_ids.json à la racine du projet.
"""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]

def env(name):
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"{name} absent du .env")

KEY = env("AIRTABLE_API_KEY")
BASE = env("AIRTABLE_BASE_ID")
META = f"https://api.airtable.com/v0/meta/bases/{BASE}/tables"

def call(url, method="GET", payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def text(name):
    return {"name": name, "type": "singleLineText"}

def long_text(name):
    return {"name": name, "type": "multilineText"}

def number(name):
    return {"name": name, "type": "number", "options": {"precision": 0}}

def select(name, *choices):
    return {"name": name, "type": "singleSelect",
            "options": {"choices": [{"name": c} for c in choices]}}

def checkbox(name):
    return {"name": name, "type": "checkbox",
            "options": {"icon": "check", "color": "greenBright"}}

def link(name, table_id):
    return {"name": name, "type": "multipleRecordLinks",
            "options": {"linkedTableId": table_id}}

def attachments(name):
    return {"name": name, "type": "multipleAttachments"}

existing = {t["name"]: t for t in call(META)["tables"]}
ids = {"base": BASE, "tables": {}}

def ensure_table(name, fields, description=""):
    if name in existing:
        print(f"{name} : déjà présente")
        t = existing[name]
    else:
        t = call(META, "POST", {"name": name, "description": description, "fields": fields})
        print(f"{name} : créée")
        existing[name] = t
    ids["tables"][name] = {
        "id": t["id"],
        "fields": {f["name"]: f["id"] for f in t["fields"]},
    }
    return t["id"]

def ensure_field(table_name, field):
    t = existing[table_name]
    have = {f["name"] for f in t["fields"]}
    if field["name"] in have:
        return
    f = call(f"{META}/{t['id']}/fields", "POST", field)
    t["fields"].append(f)
    ids["tables"][table_name]["fields"][f["name"]] = f["id"]
    print(f"{table_name}.{field['name']} : champ ajouté")

ALLEGEANCES = ("noir", "vert", "neutre")

lieux = ensure_table("Lieux", [
    text("Nom"), text("Id"), text("Région"),
    select("Type", "chateau", "ville", "ile", "ruine"),
    number("Jours de Port-Réal"),
], "Lieux de Westeros ; Jours de Port-Réal = délai corbeau/cheval")

maisons = ensure_table("Maisons", [
    text("Nom"), text("Id"), text("Devise"), long_text("Blason"),
    link("Siège", lieux),
    select("Allégeance affichée", *ALLEGEANCES),
    select("Allégeance réelle", *ALLEGEANCES),
    number("Or"), number("Revenus par lune"),
    number("Levées dispo"), number("Levées max"),
    select("Statut", "intacte", "mobilisee", "assiegee", "tombee"),
    checkbox("Canon"),
], "Allégeance réelle ≠ affichée = trahison en germe. JAMAIS montrée au joueur.")

personnages = ensure_table("Personnages", [
    text("Nom"), text("Id"), link("Maison", maisons), text("Titre"),
    number("Naissance"), long_text("Traits"), long_text("Objectifs"),
    text("Manière"), long_text("Physique"),
    attachments("Portrait"), long_text("Prompt Ideogram"),
    select("État", "actif", "dormant", "mort"),
    link("Lieu", lieux),
    select("Condition", "libre", "otage", "prisonnier", "blesse"),
], "État actif = simulé à chaque battement (~10-15 max)")

relations = ensure_table("Relations", [
    text("Relation"), link("Source", personnages), link("Cible", personnages),
    number("Opinion"), long_text("Liens"), checkbox("Connue du joueur"),
], "Directionnelles : A→B ≠ B→A. Opinion -100..+100.")

evenements = ensure_table("Événements", [
    text("Titre"), text("Id"), text("Date prévue"),
    select("Type", "canon", "emergent", "programme"),
    number("Importance"), long_text("Description"),
    link("Lieu", lieux), link("Acteurs", personnages),
    long_text("Conditions de déviation"),
    select("Statut", "a_venir", "resolu", "devie", "annule"),
    long_text("Effets"),
], "La file du moteur. Le canon se produit sauf déviation. Dates AAA-LL-JJ (ex 129-03-03).")

ensure_table("Infos", [
    text("Résumé"), link("Événement", evenements), long_text("Version"),
    select("Source", "corbeau", "mestre", "rumeur", "temoin"),
    number("Fiabilité"), text("Date apprise"),
], "Ce que le JOUEUR sait — jamais confondu avec la vérité. Événement vide = fausse rumeur.")

ensure_table("Paroles", [
    text("Contenu"), text("Date"), link("Lieu", lieux),
    link("Locuteur", personnages), link("Destinataires", personnages),
    checkbox("Secret"), text("Scène"),
], "Ce qui a été DIT : promesses, menaces, aveux. Mémoire conversationnelle des PNJ.")

ensure_table("Actes", [
    text("Description"), text("Date"), link("Lieu", lieux),
    link("Acteur", personnages), link("Témoins", personnages),
    long_text("Connu de"),
], "Ce qui a été FAIT.")

ensure_table("Intentions", [
    text("Id"), link("Personnage", personnages),
    long_text("Pensées"), long_text("Intentions"), text("MàJ"),
], "La tête des PNJ actifs. JAMAIS montrée au joueur.")

ensure_table("Monde", [
    text("Clé"), text("Date"), text("Phase"), number("Tension"),
    long_text("Déviations"), link("Maison du joueur", maisons),
], "Singleton : un seul enregistrement, Clé = 'etat'.")

ensure_table("Scènes", [
    text("Titre"), text("Date"), link("Lieu", lieux),
    link("Participants", personnages), long_text("Résumé"),
    long_text("Choix fait"), checkbox("Courante"), long_text("Beat en cours"),
    long_text("Choix proposés"),
], "Le journal de la partie.")

ensure_field("Lieux", link("Contrôle", maisons))
ensure_field("Maisons", link("Suzerain", maisons))

# Recharge les ids (champs inverses créés automatiquement inclus)
for t in call(META)["tables"]:
    if t["name"] in ids["tables"]:
        ids["tables"][t["name"]]["fields"] = {f["name"]: f["id"] for f in t["fields"]}

(ROOT / "airtable_ids.json").write_text(
    json.dumps(ids, ensure_ascii=False, indent=2), encoding="utf-8")
print("airtable_ids.json écrit")
