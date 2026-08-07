# -*- coding: utf-8 -*-
"""Fabrique les medaillons du fil a partir des portraits peints.

Le jeu ne sert QUE `ecrans/portraits/<id>.svg` : c'est ce que lisent
`serveur.js` (route /entites) et `scripts/append_flux.py` (portraits inlines
dans les items `salle`). Les toiles generees a l'exterieur vivent en PNG dans
`portraits/` et n'atteignaient jamais l'ecran.

Ce script fait le pont, sans toucher au code : il enferme chaque PNG, reduit
et recadre en rond, dans un SVG a l'anneau heraldique — le meme contenant que
les medaillons placeholder qu'il remplace. Rien d'autre a brancher.

    python scripts/medaillons.py            # etat des lieux, n'ecrit rien
    python scripts/medaillons.py --vraiment # fabrique
    python scripts/medaillons.py --vraiment --seulement rhaenyra,daemon

Les placeholders remplaces partent dans `ecrans/portraits/archive/` : ils
restent le repli si l'on retire un jour un PNG.
"""

import base64
import io
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(RACINE, "portraits")
CIBLE = os.path.join(RACINE, "ecrans", "portraits")
ARCHIVE = os.path.join(CIBLE, "archive")

# 256 px pour un rond affiche autour de 64 : la marge sert les ecrans denses
# et le survol. Au-dela on paie du flux pour rien — chaque salle inline tous
# les presents d'un coup.
COTE = 256
QUALITE = 72


def medaillon(chemin_png):
    """Le PNG, carre par le centre, reduit, et troue en rond. -> bytes webp."""
    im = Image.open(chemin_png).convert("RGB")
    # Recadrage carre par le HAUT et non par le centre : ces toiles sont des
    # bustes, le visage y est dans le tiers superieur. Un carre centre coupe
    # le front.
    l, h = im.size
    if l != h:
        cote = min(l, h)
        gauche = (l - cote) // 2
        haut = 0 if h > l else (h - cote) // 2
        im = im.crop((gauche, haut, gauche + cote, haut + cote))
    im = im.resize((COTE, COTE), Image.LANCZOS)

    # Le rond est fait ici, dans l'alpha, plutot que par un clipPath SVG :
    # un clipPath ne s'applique pas de la meme facon a une image inline selon
    # les moteurs, et le fil rejoue des centaines de medaillons.
    masque = Image.new("L", (COTE * 4, COTE * 4), 0)
    ImageDraw.Draw(masque).ellipse((0, 0, COTE * 4 - 1, COTE * 4 - 1), fill=255)
    masque = masque.resize((COTE, COTE), Image.LANCZOS)
    rond = im.convert("RGBA")
    rond.putalpha(masque)

    tampon = io.BytesIO()
    rond.save(tampon, "WEBP", quality=QUALITE, method=6)
    return tampon.getvalue()


def svg(pid, nom, webp):
    """Le contenant : anneau heraldique + la toile en data URI."""
    b64 = base64.b64encode(webp).decode("ascii")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" '
        'role="img" aria-label="%s">\n'
        "  <title>%s</title>\n"
        '  <circle cx="64" cy="64" r="63" fill="#1d1a1c"/>\n'
        '  <circle cx="64" cy="64" r="57.5" fill="#141009"/>\n'
        '  <image x="12" y="12" width="104" height="104" '
        'href="data:image/webp;base64,%s"/>\n'
        '  <circle cx="64" cy="64" r="52" fill="none" '
        'stroke="#0b0908" stroke-opacity=".55" stroke-width="1.5"/>\n'
        "</svg>\n"
    ) % (nom.replace('"', "&quot;"), nom.replace("<", "&lt;"), b64)


def main():
    vraiment = "--vraiment" in sys.argv
    seulement = None
    if "--seulement" in sys.argv:
        seulement = set(sys.argv[sys.argv.index("--seulement") + 1].split(","))

    gens = json.load(io.open(
        os.path.join(RACINE, "etat", "personnages.json"), encoding="utf-8"))
    if isinstance(gens, dict):
        gens = gens["personnages"]
    noms = {p["id"]: p.get("nom", p["id"]) for p in gens}

    fait = manque = 0
    for pid in sorted(noms):
        if seulement and pid not in seulement:
            continue
        png = os.path.join(SOURCE, pid + ".png")
        if not os.path.exists(png):
            manque += 1
            continue
        sortie = os.path.join(CIBLE, pid + ".svg")
        if not vraiment:
            print("  a fabriquer  %s" % pid)
            fait += 1
            continue
        # Le placeholder qu'on ecrase n'est pas perdu : il redevient le repli
        # le jour ou l'on retire la toile.
        if os.path.exists(sortie) and b"data:image" not in io.open(sortie, "rb").read():
            os.makedirs(ARCHIVE, exist_ok=True)
            shutil.copy2(sortie, os.path.join(ARCHIVE, pid + ".svg"))
        contenu = svg(pid, noms[pid], medaillon(png))
        io.open(sortie, "w", encoding="utf-8").write(contenu)
        print("  %-24s %6.1f Ko" % (pid, len(contenu) / 1024.0))
        fait += 1

    print("\n%d medaillon(s) %s, %d personnage(s) sans toile peinte."
          % (fait, "fabrique(s)" if vraiment else "a fabriquer", manque))
    if not vraiment and fait:
        print("Relancer avec --vraiment pour ecrire.")


if __name__ == "__main__":
    main()
