# -*- coding: utf-8 -*-
"""Harnais : la mesure d'occupation et les invariants, sur un etat/ jetable.

    python scripts/tests/essai_occupation.py

Rien n'est lu ni ecrit dans le vrai depot : occupation.ETAT est detourne vers
un dossier temporaire, monte a la main pour chaque cas.
"""
from __future__ import print_function

import io
import json
import os
import sys
import tempfile
import time

import os as _os, sys as _sys  # le chemin des freres : scripts/ et scripts/noyau/
_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.basename(_d) != "scripts" and _os.path.dirname(_d) != _d:
    _d = _os.path.dirname(_d)
for _p in (_d, _os.path.join(_d, "noyau")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from temps.expose import occupation  # noqa: E402
from temps.expose import tick  # noqa: E402

RATES = []


def verifie(nom, obtenu, attendu):
    ok = obtenu == attendu
    print(("  ok   " if ok else "  RATE ") + nom
          + ("" if ok else "  -> obtenu %r, attendu %r" % (obtenu, attendu)))
    if not ok:
        RATES.append(nom)


def ecrire(chemin, contenu):
    d = os.path.dirname(chemin)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu if isinstance(contenu, str)
                else json.dumps(contenu, ensure_ascii=False, indent=2))


def monter(sieges, veilles=(), inbox=(), tetes=()):
    """Fabrique un etat/ jetable. veilles = [(nom, age_en_secondes)]."""
    base = tempfile.mkdtemp(prefix="essai-occupation-")
    maintenant = time.time()
    ecrire(os.path.join(base, "joueurs.json"), sieges)
    ecrire(os.path.join(base, "intentions.json"),
           [{"personnage_id": p, "echelle": "orbite"} for p in tetes])
    for nom, age in veilles:
        p = os.path.join(base, "veille", nom + ".json")
        ecrire(p, {})
        os.utime(p, (maintenant - age, maintenant - age))
    for pid, noms in inbox:
        for n, age in noms:
            p = os.path.join(base, "inbox", pid, n)
            ecrire(p, "{}")
            os.utime(p, (maintenant - age, maintenant - age))
        d = os.path.join(base, "inbox", pid)
        if not os.path.isdir(d):
            os.makedirs(d)
    occupation.ETAT = base
    return base


H = 3600


# --------------------------------------------------------------------------
print("\n1. LA MESURE — veille, inbox, seuil")
# --------------------------------------------------------------------------
monter(
    sieges=[
        {"personnage_id": "frais", "nom": "Frais", "occupe": False},
        {"personnage_id": "vieux", "nom": "Vieux", "occupe": True},
        {"personnage_id": "jamais", "nom": "Jamais", "occupe": False},
        {"personnage_id": "inboxe", "nom": "Inboxe", "occupe": False},
    ],
    veilles=[("frais", 5 * 60), ("vieux", 10 * H), ("inboxe", 30 * H)],
    inbox=[("inboxe", [("action-1.json", 60)])],
    tetes=["vieux", "jamais", "frais"],
)
m = {x["personnage_id"]: x for x in occupation.mesures()}
verifie("veille de 5 min -> assis", m["frais"]["occupe"], True)
verifie("veille de 10 h -> vacant", m["vieux"]["occupe"], False)
verifie("aucune veille du tout -> vacant", m["jamais"]["occupe"], False)
verifie("veille morte mais inbox pleine -> assis", m["inboxe"]["occupe"], True)
verifie("la derive est vue (vieux)", m["vieux"]["derive"], True)
verifie("la derive est vue (frais)", m["frais"]["derive"], True)
verifie("pas de derive quand le cache dit vrai", m["jamais"]["derive"], False)

print("\n   le seuil est bien LA constante, et une seule")
ancien = occupation.SEUIL_OCCUPATION_SECONDES
occupation.SEUIL_OCCUPATION_SECONDES = 12 * H
m = {x["personnage_id"]: x for x in occupation.mesures()}
verifie("seuil a 12 h : la veille de 10 h redevient assise",
        m["vieux"]["occupe"], True)
occupation.SEUIL_OCCUPATION_SECONDES = ancien

# --------------------------------------------------------------------------
print("\n2. CE QUI NE COMPTE PAS pour un souffle")
# --------------------------------------------------------------------------
monter(
    sieges=[{"personnage_id": "marlo-vasse", "occupe": True}],
    veilles=[("marlo-vasse", 26 * H), ("marlo", 60), ("mj", 60),
             ("mj-marlo", 60)],
    inbox=[("marlo-vasse", [(".gardez", 3 * 24 * H)])],
    tetes=["marlo-vasse"],
)
m = occupation.mesures()[0]
verifie("un .gardez n'est pas une action", m["inbox"], 0)
verifie("ni mj.json ni marlo.json ni mj-marlo.json ne comptent",
        m["occupe"], False)

print("\n   ... sauf si le siege les DECLARE")
monter(
    sieges=[{"personnage_id": "marlo-vasse", "occupe": True,
             "veille": ["marlo-vasse", "mj-marlo"]}],
    veilles=[("marlo-vasse", 26 * H), ("mj-marlo", 60)],
    tetes=["marlo-vasse"],
)
m = occupation.mesures()[0]
verifie("veille declaree -> comptee", m["occupe"], True)
verifie("et c'est bien elle qu'on nomme", m["session_veille"], "mj-marlo")

# --------------------------------------------------------------------------
print("\n3. LES MARQUES DE MAIN — quitte_a et assis_a")
# --------------------------------------------------------------------------
maintenant = time.time()
monter(
    sieges=[{"personnage_id": "parti", "occupe": True,
             "quitte_a": maintenant - 60},
            {"personnage_id": "assis", "occupe": False,
             "assis_a": maintenant - 60}],
    veilles=[("parti", 300)],  # veille FRAICHE, mais anterieure au depart
    tetes=["parti"],
)
m = {x["personnage_id"]: x for x in occupation.mesures()}
verifie("une veille anterieure au depart ne rallume pas le siege",
        m["parti"]["occupe"], False)
verifie("s'asseoir vaut souffle, meme sans veille", m["assis"]["occupe"], True)

# --------------------------------------------------------------------------
print("\n4. LE RAFRAICHISSEMENT — et son refus")
# --------------------------------------------------------------------------
base = monter(
    sieges=[
        {"personnage_id": "a-tete", "occupe": True, "pnj": ["x"],
         "note": "ne doit pas disparaitre"},
        {"personnage_id": "sans-tete", "occupe": True},
        {"personnage_id": "reveille", "occupe": False},
    ],
    veilles=[("a-tete", 30 * H), ("sans-tete", 30 * H), ("reveille", 60)],
    tetes=["a-tete"],
)
chg, refuses, _ = occupation.rafraichir(True, crier=False)
apres = json.load(io.open(os.path.join(base, "joueurs.json"), encoding="utf-8"))
par_id = {s["personnage_id"]: s for s in apres}
verifie("le siege avec tete bascule vacant", par_id["a-tete"]["occupe"], False)
verifie("le siege SANS tete reste occupe", par_id["sans-tete"]["occupe"], True)
verifie("et il est signale comme refuse",
        [x["personnage_id"] for x in refuses], ["sans-tete"])
verifie("le siege reveille bascule occupe", par_id["reveille"]["occupe"], True)
verifie("les autres champs sont intacts", par_id["a-tete"]["pnj"], ["x"])
verifie("la note aussi", par_id["a-tete"]["note"], "ne doit pas disparaitre")
verifie("aucun .tmp ne traine",
        [n for n in os.listdir(base) if n.endswith(".tmp")], [])

print("\n   marquer() ne touche qu'une clef")
occupation.marquer("a-tete", "assis_a")
apres = json.load(io.open(os.path.join(base, "joueurs.json"), encoding="utf-8"))
par_id = {s["personnage_id"]: s for s in apres}
verifie("assis_a pose", isinstance(par_id["a-tete"].get("assis_a"), float), True)
verifie("les voisins sont intacts", par_id["sans-tete"]["occupe"], True)
occupation.marquer("a-tete", "quitte_a")
apres = json.load(io.open(os.path.join(base, "joueurs.json"), encoding="utf-8"))
par_id = {s["personnage_id"]: s for s in apres}
verifie("quitter efface assis_a", "assis_a" in par_id["a-tete"], False)


# --------------------------------------------------------------------------
print("\n5. LES INVARIANTS de tick.py --verifier")
# --------------------------------------------------------------------------
class Rapport(object):
    def __init__(self):
        self.dits = []

    def dire(self, gravite, ou, quoi):
        self.dits.append((gravite, ou, quoi))

    def cherche(self, morceau, gravite=None):
        return [d for d in self.dits if morceau in d[2]
                and (gravite is None or d[0] == gravite)]


class FauxEtat(object):
    def __init__(self, sieges, mesures):
        self.sieges = sieges
        self.mesures_sieges = {m["personnage_id"]: m for m in mesures}
        self.sieges_drapeau = {s["personnage_id"]: bool(s.get("occupe", True))
                               for s in sieges}
        self.sieges_occupes = {p for p, m in self.mesures_sieges.items()
                               if m["occupe"]}
        self.sieges_vacants = {p for p, m in self.mesures_sieges.items()
                               if not m["occupe"]}


def mesure(pid, occupe, raison="essai", inbox=0, inbox_age=None,
           dormant=False, cache=None):
    return {"personnage_id": pid, "occupe": occupe, "raison": raison,
            "inbox": inbox, "inbox_age_s": inbox_age,
            "inbox_dormant": dormant, "cache": cache,
            "veille_age_s": None, "derive": False, "a_tete": True}


print("\n   a. le cache a derive")
e = FauxEtat(
    [{"personnage_id": "dort", "occupe": True},
     {"personnage_id": "reveille", "occupe": False}],
    [mesure("dort", False), mesure("reveille", True)])
r = Rapport()
tick.verifier_occupation(e, r)
verifie("marque occupe et plus rien ne respire -> GRAVE",
        len(r.cherche("donc il DORT", "grave")), 1)
verifie("marque vacant et il respire -> avertissement",
        len(r.cherche("cache perime", "avertissement")), 1)

print("\n   b. la note contredit la mesure")
e = FauxEtat(
    [{"personnage_id": "nicolas-reynolds", "occupe": True,
      "note": "VACANT pour l'instant : il a donc une tete."},
     {"personnage_id": "prose", "occupe": True,
      "note": "Quand ce siege est occupe, Rhaenyra doit avoir une tete."}],
    [mesure("nicolas-reynolds", True), mesure("prose", False)])
r = Rapport()
tick.verifier_occupation(e, r)
verifie("note VACANT sur un siege assis -> avertissement",
        len(r.cherche("dit VACANT mais le siege est mesure assis")), 1)
verifie("le mot 'occupe' en prose minuscule n'accuse personne",
        len(r.cherche("dit OCCUPE mais")), 0)

print("\n   c. deux sieges alternes assis en meme temps")
e = FauxEtat(
    [{"personnage_id": "rhaenyra", "occupe": True},
     {"personnage_id": "marlo-vasse", "occupe": True,
      "alterne_avec": "rhaenyra"}],
    [mesure("rhaenyra", True), mesure("marlo-vasse", True)])
r = Rapport()
tick.verifier_occupation(e, r)
verifie("l'impossible est GRAVE",
        len(r.cherche("tous deux mesures assis", "grave")), 1)

e = FauxEtat(
    [{"personnage_id": "rhaenyra", "occupe": True},
     {"personnage_id": "marlo-vasse", "occupe": False,
      "alterne_avec": "rhaenyra"}],
    [mesure("rhaenyra", True), mesure("marlo-vasse", False)])
r = Rapport()
tick.verifier_occupation(e, r)
verifie("un seul des deux assis : rien a dire",
        len(r.cherche("tous deux mesures assis")), 0)

e = FauxEtat(
    [{"personnage_id": "m", "occupe": True,
      "note": "Siege ALTERNE : jamais en meme temps que Rhaenyra."}],
    [mesure("m", True)])
r = Rapport()
tick.verifier_occupation(e, r)
verifie("une note qui dit ALTERNE sans le champ -> avertissement",
        len(r.cherche("ne porte pas `alterne_avec`")), 1)

e = FauxEtat(
    [{"personnage_id": "m", "occupe": True, "alterne_avec": "fantome"}],
    [mesure("m", True)])
r = Rapport()
tick.verifier_occupation(e, r)
verifie("alterne_avec qui ne designe pas un siege -> avertissement",
        len(r.cherche("qui n'est pas un siege")), 1)

print("\n   d. l'inbox qui ne bouge plus")
e = FauxEtat(
    [{"personnage_id": "fige", "occupe": True}],
    [mesure("fige", True, inbox=12, inbox_age=3 * 24 * H, dormant=True)])
r = Rapport()
tick.verifier_occupation(e, r)
verifie("un inbox dormant est signale",
        len(r.cherche("tenu occupe par 12 action", "avertissement")), 1)

# --------------------------------------------------------------------------
print("")
if RATES:
    print("%d CAS RATE(S) : %s" % (len(RATES), ", ".join(RATES)))
    sys.exit(1)
print("tous les cas passent.")
