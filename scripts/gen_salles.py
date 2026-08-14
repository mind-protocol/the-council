# -*- coding: utf-8 -*-
"""Peint les vues de salle via l'API Ideogram (v3), pour le fil du jeu.

    python scripts/gen_salles.py                 # toutes celles qui manquent
    python scripts/gen_salles.py roukerie bourg  # celles-la seulement
    python scripts/gen_salles.py --refaire bourg # meme si le fichier existe

Sortie : `ecrans/salles/<id de la salle>.jpg`, ou l'id est celui de `plans.js`.
Deposer le fichier SUFFIT : `vue-salle.js` le pose dans le fil au changement de
salle, sans que le MJ ecrive quoi que ce soit. Rien a declarer ailleurs.

DEUX CHOSES A NE PAS DEFAIRE, payees par l'essai :

1. REALISTIC *et* le vocabulaire de la prise de vue. Le `style_type` seul ne
   suffit pas : tant que le prompt dit « oil painting », REALISTIC peint une
   toile un peu plus fine au lieu de rendre une piece. C'est le couple qui
   donne le grain de la pierre et le chant taille de la Table Peinte.
2. La salle est VIDE. Un decor habite raconte une scene precise et ne peut plus
   servir aux autres — et il contredirait la galerie des presents, qui, elle,
   dit la verite de qui est la.

Les toiles des GENS restent des huiles peintes (`gen_portraits.py`) : des
visages peints dans un monde solide. C'est voulu, pas une derive.
"""
import sys
from pathlib import Path

import requests
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "ecrans" / "salles"
ENDPOINT = "https://api.ideogram.ai/v1/ideogram-v3/generate"
LARGEUR = 1100          # le fil ne fait jamais mieux ; au-dela on paie du reseau
QUALITE = 82

STYLE = (
    "Highly detailed photorealistic interior, dark fantasy medieval castle, "
    "volumetric candlelight and cold daylight from window slits, deep shadow, "
    "muted palette, fine material detail in carved wood and rough black stone, "
    "empty room with no people. "
)
DEHORS = (
    "Highly detailed photorealistic view, dark fantasy medieval setting, "
    "overcast northern sea light, wet stone and mud, muted palette, fine "
    "material detail, no people. "
)
# SOUS TERRE, IL N'Y A PAS DE FENETRE — et c'est le premier essai qui l'a appris :
# le bloc d'interieur affirme « lumiere du jour par les meurtrieres », si bien que
# l'archive (trois etages sous la salle du levant), les cachots (sous la cour) et
# les galeries (quatre-vingts pas SOUS LA MER) sont sortis en plein jour, fenetres
# ouvertes sur le ciel. Une salle enterree prend donc ce bloc-ci, et le negatif
# qui va avec.
SOUS = (
    "Highly detailed photorealistic underground interior hewn from black volcanic "
    "rock, deep beneath a castle, no windows and no daylight whatsoever, lit only by "
    "lantern flame and candles, darkness swallowing the far end, damp seeping stone, "
    "muted palette, fine material detail, empty with no people. "
)
# Les fosses ne sont pas une piece : c'est une caverne du Dragonmont. Le mot
# « castle » y appelait une salle a arcades — on le retire.
FEU = (
    "Highly detailed photorealistic volcanic cavern, an enormous natural cave under a "
    "mountain, no architecture and no masonry, no windows, lit by glowing lava "
    "fissures and embers, sulphurous smoke, vast scale, muted palette, fine material "
    "detail, empty with no people. "
)
FIN = (
    ", wide establishing view, full bleed, edge to edge, no canvas border, "
    "no picture frame, no text, no watermark, no figures, no people"
)
# Ce qu'on refuse, salle par salle. Ideogram le prend en `negative_prompt` — plus
# sur que de l'ecrire en creux dans le prompt, ou « no windows » finit par peindre
# des fenetres.
SANS_JOUR = "window, windows, daylight, sky, sunlight, sun, outdoors"

# Barralfond : pas de maconnerie du tout. Un barral geant creuse et ce qu'on a
# taille dedans, au nord du Mur — bois pale, seve rouge, os, bronze et neige. Le
# bloc d'interieur du chateau y peindrait de la pierre noire et des voutes ; on
# lui en donne un a lui, et le negatif refuse la pierre.
BOIS = (
    "Highly detailed photorealistic interior hollowed from the living trunk of a "
    "colossal pale weirwood tree, walls of bone-white grained wood weeping red sap, "
    "no masonry and no cut stone anywhere, lit by low fires and horn lanterns, cold "
    "northern light from a gap far above, muted palette of bone, red and moss, fine "
    "grain and carving detail, empty with no people. "
)
RACINE_SOUS = (
    "Highly detailed photorealistic underground chamber among the living roots of a "
    "colossal tree, pale roots the thickness of columns crossing overhead and "
    "underfoot, packed black earth, no masonry and no cut stone, no windows and no "
    "daylight whatsoever, lit only by horn lanterns, darkness swallowing the far end, "
    "muted palette, fine grain detail, empty with no people. "
)
NEIGE = (
    "Highly detailed photorealistic view, dark fantasy far north beyond a great wall "
    "of ice, flat grey snow light, frost and bare black trees, muted palette, fine "
    "material detail, no people. "
)
SANS_PIERRE = "cut stone, masonry, brick, castle wall, arches, vaulting, columns of stone"

# Peyredragon : pierre volcanique noire, maconnerie valyrienne, mer dure.
# Une entree ici = une salle qui peut avoir sa vue. L'id est celui de plans.js.
SALLES = {
    # ---- Barralfond, au nord du Mur ---------------------------------------
    "clairiere": (NEIGE,
        "a clearing in a snowbound northern forest around the base of a colossal pale "
        "weirwood, low turf and hide huts ringed by a raised bank of exposed roots, a "
        "communal fire pit with a bronze cauldron, drying racks, carved bone markers "
        "standing in the snow, red leaves fallen on white ground"),
    "la-souche": (BOIS,
        "the hollow heart of a colossal weirwood trunk, a wide round chamber of "
        "bone-white wood with red sap running in the grain, the inner walls covered "
        "floor to roof with carved lines and tallies, a great flat stump used as a "
        "work table at the centre, low fire, carved wooden stools",
        SANS_PIERRE),
    "arbre-des-ages": (BOIS,
        "a platform high in the branches of a colossal pale weirwood, built of lashed "
        "timber among bone-white limbs and red leaves, a great cut cross-section of "
        "trunk mounted upright showing hundreds of growth rings scored with marks, "
        "cold grey sky and snow forest far below",
        SANS_PIERRE),
    "etabli": (BOIS,
        "a woodworker's workshop hollowed into a pale tree trunk, a long scarred bench "
        "under a row of horn lanterns, bronze gouges and bone awls racked on the wall, "
        "shavings and red sap on the floor, a half-carved panel clamped on the bench, "
        "a small forge glowing at the far end",
        SANS_PIERRE),
    "lit-des-racines": (RACINE_SOUS,
        "a low earthen chamber deep under a great tree, pale roots the thickness of "
        "columns crossing overhead and running away into darkness in every direction, "
        "knotted cords strung between roots as markers, a single horn lantern set on "
        "the packed earth, cold damp air",
        SANS_JOUR + ", " + SANS_PIERRE),
    "bassin-noir": (RACINE_SOUS,
        "a perfectly still round pool of black water under the roots of a great tree, "
        "the water like dark glass reflecting pale roots overhead, a rim of smooth "
        "worn wood around it, notched tally sticks laid on the rim, one lantern "
        "doubled in the reflection",
        SANS_JOUR + ", " + SANS_PIERRE),

    "table-peinte": (STYLE,
        "the round chamber at the top of a black stone keep, a colossal carved wooden "
        "table filling the floor, shaped as a whole continent with painted hills, rivers "
        "and castles, worn smooth by hands, iron candle-stands around it, high narrow "
        "windows over a stormy sea, black volcanic stone walls, heavy timber beams"),
    "roukerie": (STYLE,
        "a castle rookery high in a black stone tower, rows of wooden cages holding "
        "ravens along the walls, black feathers and droppings on the sill, a slanted "
        "writing desk with an open register and an inkpot, sealed scrolls in "
        "pigeonholes, one shutter open on a grey sky"),
    "tour-dragon-mer": (STYLE,
        "the upper chamber of a tall black stone tower facing the open sea, tall arched "
        "windows on three sides, a broad stone sill worn smooth by elbows, a heavy "
        "carved bed and a banded sea chest, storm light on the water far below"),
    "appartements-reine": (STYLE,
        "a royal bedchamber in a black stone castle, a great carved four-poster bed with "
        "heavy drawn curtains, iron-banded travelling chests, a low fire in a deep "
        "hearth, a single studded door with a heavy drawbar"),
    "grande-salle": (STYLE,
        "a great hall in a black stone castle, two long trestle tables running its "
        "length, a raised dais at the far end, iron sconces on the walls, high dark "
        "rafters, dragons carved into the black stone"),
    "antichambre": (STYLE,
        "a narrow stone antechamber, one long worn wooden bench against the wall, a "
        "heavy closed door at the far end, a single candle bracket, flagstones hollowed "
        "by waiting feet"),
    "porte-dragon": (DEHORS,
        "a castle gatehouse with a raised iron portcullis, a dragon carved into the "
        "black stone arch above it, a guardroom bench and a tally board, a paved way "
        "passing under the arch, black volcanic walls"),
    "porte-de-mer": (DEHORS,
        "a low postern gate at the foot of a black stone curtain wall, wet steps rising "
        "from a stone quay, an iron-bound door, a brazier for the night watch, rope and "
        "salt stains on the stone"),
    "bourg": (DEHORS,
        "a small fishing town below high black castle walls, low stone and turf houses, "
        "drying racks hung with split fish, upturned boats on the shingle, a narrow "
        "lower street of packed mud, woodsmoke, grey sea beyond"),
    "salle-levant": (STYLE,
        "a small east-facing chamber in a black stone castle, one plain oak table laid "
        "for six with benches, a sideboard of pewter, a tall narrow window with the "
        "first dawn light falling across the boards, a cold hearth"),
    "archives": (SOUS,
        "a deep vaulted undercroft used as an archive, three tiers of shelving crammed "
        "with rolled parchments and bound registers, a leaning ladder, one lantern on a "
        "reading slope, black stone beaded with damp, very cold", SANS_JOUR),
    "fosses": (FEU,
        "smoking caverns of a volcanic mountain, sulphurous haze, glowing fissures "
        "across the rock floor, enormous scorch marks and claw-gouged stone, a hollowed "
        "nesting pit, shed scales the size of shields, embers in the dark", SANS_JOUR),
    "galeries": (SOUS,
        "narrow mining galleries far beneath the sea, veins of black volcanic glass "
        "gleaming in candlelight, timber props and wedges, chisels and wicker baskets, "
        "a low dripping roof, dust hanging in the candle beam", SANS_JOUR),
    "cachots": (SOUS,
        "cells cut into raw rock beneath a courtyard, iron-barred doors standing open, "
        "old straw on the floor, a drain cut in the stone, one guttering torch, empty "
        "and very cold", SANS_JOUR),
    "cuisines": (STYLE,
        "a great castle kitchen, open fires and turning spits, heavy scarred chopping "
        "blocks, copper and iron pots hanging in rows, sacks and baskets stacked along "
        "the wall, flour dust hanging in the light from a high vent"),
    "grand-escalier": (DEHORS,
        "three hundred steps cut into a cliff of black volcanic rock descending to the "
        "sea, a knotted rope handrail on iron pins, spray on the lower treads, gulls, "
        "ships small on the water far below, castle walls above"),
    "quai": (DEHORS,
        "a stone quay at the foot of a castle cliff, bollards and iron mooring rings, "
        "coils of tarred rope, crates and barrels stacked under a lean-to, one moored "
        "single-masted boat, grey choppy water"),
    "chemin-ronde": (DEHORS,
        "the top walk of a castle curtain wall facing the open sea, heavy crenellations, "
        "a watch brazier on iron legs, flagstones worn hollow by boots, wind-driven "
        "spray, grey water to the horizon"),
    "cour": (DEHORS,
        "a castle courtyard paved in black stone, a stone well with a bucket and windlass, "
        "handcarts and barrels against the wall, straw trodden into the mud between the "
        "cobbles, high black walls all round, a wide gate arch"),
}


def cle_api():
    for ligne in (RACINE / ".env").read_text(encoding="utf-8").splitlines():
        if ligne.startswith("IDEOGRAM_API_KEY="):
            return ligne.split("=", 1)[1].strip()
    raise SystemExit("IDEOGRAM_API_KEY introuvable dans .env")


def peindre(cle, ident):
    fiche = SALLES[ident]
    style, sujet = fiche[0], fiche[1]
    negatif = fiche[2] if len(fiche) > 2 else None
    champs = {
        "prompt": (None, style + sujet + FIN),
        "aspect_ratio": (None, "16x9"),
        "rendering_speed": (None, "TURBO"),
        "style_type": (None, "REALISTIC"),
        "num_images": (None, "1"),
    }
    if negatif:
        champs["negative_prompt"] = (None, negatif)
    reponse = requests.post(ENDPOINT, headers={"Api-Key": cle}, files=champs, timeout=180)
    reponse.raise_for_status()
    image = requests.get(reponse.json()["data"][0]["url"], timeout=180)
    image.raise_for_status()
    brut = SORTIE / (ident + ".brut.png")
    brut.write_bytes(image.content)
    im = Image.open(brut).convert("RGB")
    im = im.resize((LARGEUR, round(LARGEUR * im.height / im.width)), Image.LANCZOS)
    im.save(SORTIE / (ident + ".jpg"), quality=QUALITE, optimize=True)
    brut.unlink()


def main():
    args = [a for a in sys.argv[1:] if a != "--refaire"]
    refaire = "--refaire" in sys.argv
    inconnus = [a for a in args if a not in SALLES]
    if inconnus:
        raise SystemExit("salle(s) inconnue(s) : " + ", ".join(inconnus))
    cle = cle_api()
    SORTIE.mkdir(parents=True, exist_ok=True)
    for ident in (args or list(SALLES)):
        if (SORTIE / (ident + ".jpg")).exists() and not refaire:
            print("saute " + ident + " (existe)", flush=True)
            continue
        try:
            peindre(cle, ident)
            print("ok    " + ident, flush=True)
        except Exception as erreur:
            print("ECHEC " + ident + " : " + str(erreur), flush=True)


if __name__ == "__main__":
    main()
