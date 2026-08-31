# -*- coding: utf-8 -*-
"""LE TEST DOIT ECHOUER SUR L'ANCIEN CODE, sinon il ne prouve rien.

On rejoue ici l'ANCIEN deposer() — copie mot pour mot de billet.py avant le
129.4.4 — sur le meme canal abime que le test, et on mesure ce qu'il en reste.
Sans ce passage, « 4 passed » ne dit que « la maison tient debout aujourd'hui ».
"""
import io
import json
import os
import shutil
import tempfile

CANAL_SAIN = {
    "canal": ["alicent", "mj-aurore"],
    "entrees": [{"de": "alicent", "date": {"annee": 129, "lune": 3, "jour": 9},
                 "texte": u"vingt-et-une entrees de correspondance"}] * 21,
}
TRONQUE = u'{\n "canal": ["alicent", "mj-aurore"],\n "entrees": [{"de": "ali'


def ancien_deposer(fichier, de, a, texte):
    """billet.py l.30-51, tel qu'il etait."""
    d = {}
    if os.path.exists(fichier):
        try:
            with io.open(fichier, encoding="utf-8") as f:
                d = json.load(f)
        except ValueError:
            d = {}
    if not isinstance(d, dict):
        d = {}
    d.setdefault("canal", sorted((de, a)))
    d.setdefault("entrees", []).append(
        {"de": de, "date": {"annee": 129, "lune": 4, "jour": 4},
         "texte": texte})
    with io.open(fichier, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=2))


dossier = tempfile.mkdtemp()
try:
    for nom, contenu in (("sain.json", json.dumps(CANAL_SAIN)),
                         ("abime.json", TRONQUE)):
        p = os.path.join(dossier, nom)
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(contenu)
        avant = len(json.loads(contenu)["entrees"]) if nom == "sain.json" \
            else u"illisible (21 entrees dessous)"
        ancien_deposer(p, "mj-aurore", "alicent", u"un billet de plus")
        with io.open(p, encoding="utf-8") as f:
            apres = len(json.load(f)["entrees"])
        print(u"%-12s avant=%-28s apres=%s entree(s)" % (nom, avant, apres))
finally:
    shutil.rmtree(dossier, ignore_errors=True)

print()
print(u"Le second est la perte : 21 entrees remplacees par 1, code de sortie 0,")
print(u"aucune exception. C'est ce cas-la que le test neuf fait planter.")
