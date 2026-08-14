# -*- coding: utf-8 -*-
"""LES TEXTURES — la table des matières d'ambientCG, et de quoi les rapatrier.

    python scripts/monde/textures.py            ce qui manque, ce qui est là
    python scripts/monde/textures.py --tirer    télécharge ce qui manque

POURQUOI CE FICHIER EXISTE. `monde/textures/` est dans `.gitignore` : cent
cinquante mégaoctets de JPG n'ont rien à faire dans l'historique d'un dépôt, et
`monde/` est de toute façon engendré et régénérable — c'est le contrat écrit
dans `bati.py`. Mais un dossier ignoré sans script pour le remplir, c'est un
monde qui ne se rebâtit pas sur une machine neuve : on lance Blender, les
images manquent, et le rendu sort en aplat sans que rien ne se plaigne. Une
texture absente ne casse pas un rendu, elle le rend faux — et un rendu faux ne
se remarque jamais.

CE QUI EST ICI ET NULLE PART AILLEURS : le choix. Quelle photo pour quelle
matière de `batir.py`, et pourquoi celle-là. Ce n'est pas une liste de
courses — c'est la décision, et elle se relit.

CE QUI N'EST PAS TEXTURÉ, ET C'EST VOULU. La moitié des matières de `batir.py`
ne sont pas des surfaces du monde : `secret`, `portail`, `egout`, `tunnel`,
`hall`, `cave` et les huit couleurs de `MAT_CAT` sont une LÉGENDE. Elles
« font apparaître le port, les tanneries et la rue d'Acier sans qu'on les
dessine ». Leur coller une photo dessus ne les embellit pas : ça crève le seul
outil de lecture qu'on ait sur trente mille volumes. Elles restent en aplat, et
toute envie de les texturer un jour doit d'abord dire par quoi on remplace le
code de couleurs.

TOUT CECI NE SERT QUE BLENDER. Le rasteriseur de `materialisation/rendu.py` ne
lit aucune image : il peint l'appareil au pixel depuis `APPAREILLEES` et
`ASSISE_M` de `palette.py`. Les deux chemins de rendu sont indépendants, et
c'est très bien ainsi — celui de la page n'a pas à charger 158 Mo.
"""
import io, os, sys, zipfile

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(RACINE, "monde", "textures")

# La résolution est un choix, pas un défaut. À la distance de caméra des vues de
# `monde/rendus/`, le 4K ne se voit pas et pèse quatre fois plus.
VARIANTE = "2K-JPG"

# On ne garde que ces trois cartes. L'AmbientOcclusion et le Displacement sont
# inutiles sur des boîtes extrudées — rien à occlure, rien à déplacer —, et le
# Metalness d'une pierre est un fichier de zéros. NormalGL et non NormalDX :
# c'est la convention de Blender, l'autre inverse l'axe Y.
CARTES = ("Color", "NormalGL", "Roughness")

# ---------------------------------------------------------------------------
# LE CHOIX — clef = le nom de la matière tel que `batir.py` l'appelle
# ---------------------------------------------------------------------------
# On a d'abord choisi des roches NATURELLES (Rock051, Rock058) pour la muraille
# et les edifices. Le rendu les a refusees, et il avait raison : Rock051 est une
# falaise moussue au litage diagonal — sur un mur, la diagonale se lit comme un
# defaut —, et Rock058 est un schiste bleu nuit qui donnait au Donjon ROUGE des
# murs de marine. Une roche n'est pas un appareil : ce qu'il faut ici, ce sont
# des pierres POSEES, avec des joints et des assises horizontales. D'ou les
# « Bricks0XX », qui chez ambientCG couvrent aussi le moellon et la pierre de
# taille. La lecon vaut d'etre gardee : on ne choisit pas une texture sur son
# nom, on la regarde.
CHOIX = {
    "muraille":  ("Bricks083",        "moellon calcaire assise par assise — l'enceinte, avec ses joints"),
    "edifice":   ("Bricks094",        "brique rouge sombre et lessivee : le Donjon ROUGE, et sa couleur d'origine (0.46,0.30,0.26)"),
    "porte":     ("Bricks083",        "les corps de garde sont du même appareil que l'enceinte"),
    "bati culte":   ("Bricks084",     "pierre de taille claire du Septuaire — accorde le (0.78,0.74,0.64) du script"),
    "bati civique": ("Bricks084",     "meme pierre de prestige que le culte"),
    "toit":      ("RoofingTiles013A", "tuile canal irreguliere, bonne echelle en 2K"),
    "toit haut": ("ThatchedRoof001A", "le chaume que la palette connait deja et que la 3D n'avait pas"),
    "taudis":    ("ThatchedRoof001A", "un taudis n'a pas de tuile"),
    "quai":      ("PavingStones070",  "pave use, joints larges — pas le dallage regulier moderne"),
    "cour":      ("PavingStones070",  "meme pave que le quai"),
    "artere":    ("PavingStones136",  "pavage sale, plus contraste que celui du quai"),
    "rue":       ("PavingStones136",  "idem — une rue est pavee, une ruelle non"),
    "ruelle":    ("Ground081",        "terre battue : une ruelle de Port-Real n'est pas pavee"),
    "escalier":  ("Planks023A",       "bois brut de charpente"),
    "hangar":    ("Planks023A",       "meme bois que les escaliers du port"),
    "terre":     ("Ground068",        "sol sec neutre pour le terrain, tuile bien a 8 m"),
    # `greve` et `basalte` ont eu leur entree ici, et c'etait une faute : ce sont
    # des matieres de `materialisation/palette.py`, que `batir.py` n'appelle
    # jamais. Elles tiraient 58 Mo pour un rasteriseur qui ne lit aucune image.
    # Les clefs de cette table sont les noms passes a `matiere()`, rien d'autre.
    # `nera` (l'eau) n'a VOLONTAIREMENT pas d'entree : une nappe d'eau se fait au
    # shader (Roughness 0.02 et une normale animee), jamais avec une photo — une
    # photo d'eau fige les vagues et se repete a l'oeil des la seconde tuile.
}

ASSETS = sorted({a for a, _ in CHOIX.values()})

# ---------------------------------------------------------------------------
# L'ÉCHELLE — combien de mètres couvre une tuile de l'image
#
# C'est le chiffre qui decide si un mur fait trois metres ou trente : une photo
# posee a la mauvaise taille donne un decor sans echelle, exactement le mal que
# `palette.py` combat avec ses assises peintes au pixel. Il ne s'invente donc
# pas — quand ambientCG publie la mesure, on la prend.
#
# DEUX mesures, et pas une : ces tuiles ne sont pas toutes carrees. Bricks083
# fait 300 x 150 cm et Bricks094 180 x 90 — une echelle uniforme les etirerait du
# double en hauteur, et un appareil etire est exactement le defaut qu'on cherche
# a corriger. On garde donc (horizontale, verticale) : la projection boite donne
# l'horizontale aux deux axes du sol et la verticale a l'axe Z, ce qui tombe
# juste sur un mur comme sur un toit.
#
# `True` = mesure publiee par ambientCG (dimensionX / dimensionY, en cm).
# `False` = ARBITRE ICI, parce que la fiche est a zero. C'est un jugement, il se
#           discute, et il est marque pour qu'on sache lequel on regarde.
TAILLE_M = {
    "Bricks083":        (3.00, 1.50, True),
    "Bricks094":        (1.80, 0.90, True),
    "PavingStones070":  (1.15, 1.15, True),
    "RoofingTiles013A": (2.90, 2.90, True),
    "Bricks084":        (2.00, 2.00, False),
    "ThatchedRoof001A": (2.00, 2.00, False),   # la longueur d'une botte de chaume
    "PavingStones136":  (2.00, 2.00, False),   # accorde au pave mesure de PavingStones070
    "Ground081":        (2.50, 2.50, False),
    "Ground068":        (4.00, 4.00, False),   # le terrain : le plus large, il se voit de loin
    "Planks023A":       (2.00, 2.00, False),   # une planche de charpente
}


# ---------------------------------------------------------------------------
# LES TEXTURES DU JEU — le grain, et rien que le grain
#
# Le décor 3D de la page (`ecrans/modules/monde/`) n'est pas le .blend : 48 000
# bâtiments y sont DES INSTANCES d'une seule boîte, et leur couleur vient de
# `palette.js` par catégorie de métier — c'est ce qui « fait apparaître le port,
# les tanneries et la rue d'Acier sans qu'on les dessine ». Y coller des photos
# en couleur effacerait cette lecture, qui est le seul repère sur trente mille
# volumes.
#
# D'où le parti : on n'envoie au navigateur que la LUMINANCE. La photo donne le
# grain, le joint, l'assise — donc l'échelle, qui est ce qui manque vraiment —,
# et la teinte reste celle de la légende, que le shader multiplie par-dessus.
# Deux images en tout, deux cent kilooctets, contre 114 Mo si l'on avait servi
# les originaux : ce n'est pas une économie, c'est la seule version correcte.
#
# Elles sont VERSIONNÉES, elles (contrairement à `monde/textures/`) : ce sont des
# ressources de jeu, au même titre que les portraits, et un dépôt fraîchement
# cloné doit pouvoir servir la page sans lancer un téléchargement de 114 Mo.
WEB = {
    "murs.jpg": ("Bricks083", "le moellon des maisons, de la courtine et des portes"),
    "toits.jpg": ("RoofingTiles013A", "la tuile canal des toits"),
    "edifices.jpg": ("Bricks094", "la brique du Donjon Rouge et des monuments"),
    "rues.jpg": ("PavingStones136", "le pave des arteres, rues et ruelles"),
    "sol.jpg": ("Ground068", "la terre du terrain — pas la couronne, trop lointaine"),
}
WEB_DOSSIER = os.path.join(RACINE, "ecrans", "textures")
WEB_PX = 512          # au-delà, on paie du réseau pour un grain qu'on ne voit pas
WEB_MOYENNE = 210     # la luminance moyenne visée — voir plus bas


def dossier(asset):
    return os.path.join(DOSSIER, asset)


def cartes(asset):
    """{carte: chemin} pour les images presentes sur le disque."""
    d = dossier(asset)
    out = {}
    for c in CARTES:
        f = os.path.join(d, "%s_%s_%s.jpg" % (asset, VARIANTE, c))
        if os.path.exists(f):
            out[c] = f
    return out


def complet(asset):
    return len(cartes(asset)) == len(CARTES)


def manquants():
    return [a for a in ASSETS if not complet(a)]


def tirer(asset):
    """Telecharge et deballe un asset. Rend True s'il est complet apres coup."""
    import urllib.request
    url = "https://ambientcg.com/get?file=%s_%s.zip" % (asset, VARIANTE)
    print("   %-18s telechargement..." % asset, end="", flush=True)
    # L'User-Agent par defaut d'urllib (« Python-urllib/3.x ») se prend un 403 :
    # ambientCG filtre les robots anonymes. On se nomme, comme le ferait curl.
    rq = urllib.request.Request(url, headers={
        "User-Agent": "le-conseil/1.0 (rapatriement de textures CC0)"})
    try:
        with urllib.request.urlopen(rq, timeout=180) as r:
            brut = r.read()
    except Exception as e:
        print(" echec (%s)" % e)
        return False
    d = dossier(asset)
    if not os.path.isdir(d):
        os.makedirs(d)
    gardes = 0
    with zipfile.ZipFile(io.BytesIO(brut)) as z:
        for nom in z.namelist():
            base = os.path.basename(nom)
            if not any(base.endswith("_%s.jpg" % c) for c in CARTES):
                continue
            with open(os.path.join(d, base), "wb") as f:
                f.write(z.read(nom))
            gardes += 1
    print(" %d cartes, %.0f Mo tires" % (gardes, len(brut) / 1e6))
    return complet(asset)


def fabriquer_web():
    """Les deux images du jeu, en niveaux de gris. Rend le nombre d'echecs.

    La NORMALISATION compte autant que la reduction. Une photo de moellon a une
    luminance moyenne autour de 0,45 : multipliee par la couleur de categorie,
    elle assombrirait toute la ville de moitie, et la legende de `palette.js`
    ne serait plus la couleur qu'on y a ecrite. On recentre donc la moyenne sur
    WEB_MOYENNE en gardant le contraste, et on releve le plancher : un joint
    noir a zero avalerait la teinte au lieu de la nuancer.
    """
    try:
        from PIL import Image, ImageStat
    except ImportError:
        print("  PIL manque — « pip install Pillow »")
        return 1
    if not os.path.isdir(WEB_DOSSIER):
        os.makedirs(WEB_DOSSIER)
    rates = 0
    for nom, (asset, pourquoi) in sorted(WEB.items()):
        src = cartes(asset).get("Color")
        if not src:
            print("   %-12s MANQUE %s — tire-la d'abord" % (nom, asset))
            rates += 1
            continue
        im = Image.open(src).convert("L").resize((WEB_PX, WEB_PX), Image.LANCZOS)
        moy = ImageStat.Stat(im).mean[0] or 1.0
        im = im.point(lambda v: max(60, min(255, int(WEB_MOYENNE + (v - moy) * 0.9))))
        out = os.path.join(WEB_DOSSIER, nom)
        im.save(out, "JPEG", quality=82, optimize=True)
        print("   %-12s %s  (%s, %.0f ko)"
              % (nom, pourquoi, asset, os.path.getsize(out) / 1024))
    return rates


def main():
    veut_tirer = "--tirer" in sys.argv[1:]
    if "--web" in sys.argv[1:]:
        print("  ecrans/textures/ — %d px, niveaux de gris :" % WEB_PX)
        return fabriquer_web()
    if not os.path.isdir(DOSSIER):
        os.makedirs(DOSSIER)

    absents = manquants()
    if veut_tirer:
        if not absents:
            print("  les %d textures sont deja la — rien a tirer." % len(ASSETS))
            return 0
        print("  %d texture(s) a tirer dans monde/textures/ :" % len(absents))
        rates = [a for a in absents if not tirer(a)]
        if rates:
            print("  echec sur : %s" % ", ".join(rates))
            return 1
        print("  complet.")
        return 0

    print("  monde/textures/ — %s, cartes %s" % (VARIANTE, ", ".join(CARTES)))
    for a in ASSETS:
        pour = sorted(m for m, (x, _) in CHOIX.items() if x == a)
        print("   %-18s %-9s %s"
              % (a, "present" if complet(a) else "MANQUE", ", ".join(pour)))
    if absents:
        print("\n  %d manquante(s) — « python scripts/monde/textures.py --tirer »"
              % len(absents))
        return 1
    print("\n  les %d textures sont la." % len(ASSETS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
