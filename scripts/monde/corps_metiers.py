# -*- coding: utf-8 -*-
# CORPS_METIERS — la matiere sociale de l'incarnation : metiers plausibles par
# quartier, grands noms loges d'office, sexe probable d'un poste. Matiere de
# scripts/corps.py (lot 2), deplacee telle quelle ; corps.py importe d'ici.

# ---------------------------------------------------------------------------
# INCARNER — apparier les personnages aux corps de la ville
# ---------------------------------------------------------------------------
# Une fiche sans corps n'est nulle part : le mestre existe, et il n'a ni rue,
# ni voisins, ni distance jusqu'au Donjon Rouge. L'appariement ne se tire pas au
# sort — on cherche le corps qui POURRAIT DÉJÀ ÊTRE LUI, et l'on prend un corps
# quelconque seulement faute de mieux.
#
# Le titre est la meilleure source dont on dispose : « Sergent du Guet à la
# porte de la Gadoue » dit le métier ET le quartier. `personnages.json` n'a pas
# de champ sexe (voir docs/schema.md) — on le lit dans les mots du titre, et
# quand rien ne le dit, on n'en fait pas un critère plutôt que de deviner.

# Un mot du titre -> les rôles qui lui correspondent, du plus proche au moins.
METIERS = [
    (("guet", "manteau"),            ["sergent", "capitaine-guet", "guet"]),
    (("gardien des dragons", "dragon"), ["gardien-dragons", "premier-gardien"]),
    (("alchimiste", "pyromant"),     ["sage-alchimiste", "alchimiste"]),
    (("septon", "septa", "foi"),     ["septon-superieur", "septon", "septa"]),
    (("mestre", "clerc", "role", "registre"), ["clerc-royal", "clerc-port", "clerc"]),
    (("port", "maitre du port"),     ["maitre-port", "clerc-port", "facteur"]),
    (("chantier", "bris", "bois"),   ["marchand-bois", "fendeur", "charbonnier"]),
    (("tenanciere", "taverne", "gaffe"), ["tavernier", "servante"]),
    (("close", "matrone", "fille"),  ["matrone", "fille"]),
    (("marchand", "marchande", "echoppe"), ["marchand", "commis", "etalier"]),
    (("preteu", "change", "usur"),   ["changeur", "clerc"]),
    (("forge", "acier"),             ["forgeron", "compagnon"]),
    (("boulang", "four"),            ["boulanger", "mitron"]),
    (("greve", "gamin", "gosse"),    ["enfant"]),
    (("veuve",),                     ["aieul", "epouse", "chef-de-feu"]),
    (("roi", "reine", "prince", "princesse", "main du roi", "garde royale"),
                                     ["officier-donjon", "intendant-royal", "clerc-royal"]),
    (("lord", "dame", "ser "),       ["maitre-maison", "officier-donjon"]),
    (("chuchoteur", "espion"),       ["logeur", "servante", "commis"]),
]
# Un mot du titre -> le quartier où l'on doit chercher.
QUARTIERS = [
    ("culpucier", "Le Culpucier"), ("crochet", "Le Crochet"),
    ("gadoue", "Le bourg de la Gadoue"), ("acier", "La rue d'Acier"),
    ("port", "Le port et ses hangars"), ("quai", "Le port et ses hangars"),
    ("greve", "Le port et ses hangars"), ("ville haute", "La ville haute"),
]
# LES GRANDS NE PRENNENT LE CORPS DE PERSONNE. Habiller Aegon II du corps d'un
# intendant de vingt-cinq ans n'est pas « le physicaliser », c'est en faire un
# domestique et voler sa place à quelqu'un. Ces gens-là habitent des lieux que
# la foule ne modélise pas — le Donjon Rouge est un maillage, pas un semis — et
# leur position vient des scènes, comme au château (scripts/presence.py).
# On les nomme, on dit où ils logent, et l'on n'apparie pas.
GRANDS = ("roi", "reine", "prince", "princesse", "main du roi", "lord commandant",
          "garde royale", "douairiere", "grand mestre")
DEMEURES = {"donjon-rouge": ("roi", "reine", "prince", "princesse", "main du roi",
                             "garde royale", "douairiere", "grand mestre")}

FEMININS = ("reine", "princesse", "dame", "septa", "tenanciere", "marchande",
            "veuve", "gamine", "maitresse", "cavaliere", "matrone", "soeur",
            "epouse-soeur", "douairiere", "fille")
MASCULINS = ("roi", "prince", "lord", "ser ", "sergent", "mestre", "septon",
             "maitre", "commis", "frere", "gamin", "capitaine", "messire")


def sexe_probable(p):
    t = sans_accent((p.get("titre") or "") + " " + (p.get("nom") or ""))
    f = any(m in t for m in FEMININS)
    h = any(m in t for m in MASCULINS)
    if f and not h: return "f"
    if h and not f: return "h"
    return None            # on ne devine pas : ce ne sera pas un critère


