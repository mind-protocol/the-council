# -*- coding: utf-8 -*-
"""Où chacun va, et à quelle heure — la table qui fait bouger la ville.

    python scripts/monde/besoins.py                (Port-Réal)
    python scripts/monde/besoins.py peyredragon    (le bourg et le château)

Une foule crédible ne se scripte pas et ne se simule pas non plus. Elle sort de
trois choses, et de rien d'autre :

  1. UN BESOIN, pas une jauge. Trente lignes disent ce qu'un rôle doit faire
     dans sa journée : de l'eau trois fois, du pain une fois, le travail à la
     cloche, la taverne au soir. Ce n'est pas une envie qui monte : c'est une
     habitude, et une ville est faite d'habitudes.

  2. UNE ADRESSE, résolue au BÂTIMENT et pas à la personne. « Où Wat prend-il
     son eau ? » — au puits le plus proche de chez lui. Donc on résout une fois
     pour chacun des 48 377 bâtiments, jamais pour les 400 000 corps. Et l'on
     y gagne ce qui rend une ville lisible : Wat va TOUJOURS au même puits, et
     l'on finit par reconnaître les visages du coin de la rue.

  3. UN DÉPHASAGE tiré de l'identité — pas un tirage au sort, un hachage. Deux
     voisins ne sortent jamais à la même minute, et pourtant rien n'est stocké.

Ce que ça produit sans qu'on l'ait écrit : la bousculade au puits à l'aube, la
file du pain à la fournée, les rues vides à l'heure du repas, les tavernes qui
se remplissent quand le jour tombe, et après le couvre-feu plus rien qui bouge
sauf les manteaux d'or. Aucune de ces scènes n'est écrite nulle part.

Ce script ne fait bouger personne : il pose la table et les adresses. Le
mouvement se calcule à l'affichage — `position(corps, t)` est une fonction
PURE, sans état, dans ecrans/modules/monde/journee.js. C'est la même règle que
`scripts/presence.py` tient déjà pour le château : la position ne se stocke
pas, elle se calcule.
"""
import json, io, os, math, sys
from collections import defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")

# ---------------------------------------------------------------------------
# QUEL LIEU — un bourg de pêche n'a pas les besoins d'une capitale
# ---------------------------------------------------------------------------
# Même convention d'appel que `peupler.py` : le mécanisme ne bouge pas d'un
# lieu à l'autre — un besoin, une adresse résolue au bâtiment, un déphasage tiré
# de l'identité. Ce qui change, ce sont les TABLES, écrites en clair plus bas,
# une par lieu.
LIEUX = {"port-real": "portreal", "peyredragon": "peyredragon"}
LIEU = (sys.argv[1] if len(sys.argv) > 1 else "port-real").lower()
if LIEU not in LIEUX:
    sys.exit("lieu inconnu : %s — attendus : %s" % (LIEU, ", ".join(LIEUX)))
PREFIXE = LIEUX[LIEU]

B = json.load(io.open(os.path.join(MONDE, PREFIXE + ".bati.json"), encoding="utf-8"))
C = {n: k for k, n in enumerate(B["_colonnes"])}
BAT = B["bati"]
if "porte_x" not in C:
    raise SystemExit(
        "Le bâti n'a pas de portes — relance scripts/monde/%s."
        % ("usages.py" if PREFIXE == "portreal" else "peyredragon_portes.py"))

# ---------------------------------------------------------------------------
# LES SERVICES — ce qu'un bâtiment doit pouvoir trouver près de lui
# ---------------------------------------------------------------------------
# Un service par besoin quotidien, et rien de plus : ce qui ne se visite qu'une
# fois l'an n'a pas besoin d'adresse, on le cherchera le jour venu. L'ordre de
# cette liste EST celui des colonnes de `dessert` — ne le change pas sans
# refaire tourner le script.
SERVICES = [
    ("puits",       ["puits"]),
    ("echoppe",     ["echoppe"]),
    ("boulangerie", ["boulangerie"]),
    ("taverne",     ["taverne"]),
    ("marche",      ["marche-quartier"]),
    ("septuaire",   ["septuaire-quartier", "vieux-septuaire"]),
    ("etuve",       ["etuve"]),
]

# ---------------------------------------------------------------------------
# LES BESOINS — trente lignes pour quatre cent mille journées
# ---------------------------------------------------------------------------
# `service` : où l'on va (nom dans SERVICES), ou "travail" pour le lieu de
#             travail du corps, ou null pour rester chez soi.
# `par_jour`: combien de fois. `heures` : le centre de chaque fenêtre, en
#             minutes depuis minuit. `largeur` : la demi-largeur, en minutes.
#
# LA LARGEUR EST LE SEUL VRAI RÉGLAGE DU SYSTÈME. À zéro, quarante ménages
# sortent à six heures pile et la ville est un mécanisme d'horlogerie. Trop
# large, la journée s'aplatit et il n'y a plus d'heure de pointe. Entre les
# deux, il y a une foule.
#
# ET PERSONNE N'A DE MONTRE. C'est la correction de fond de cette table : les
# largeurs d'ici étaient celles d'un atelier moderne — vingt minutes autour de
# six heures quarante suppose qu'on sait qu'il est six heures quarante. On ne le
# sait pas. On sait qu'il fait jour, qu'on a faim, que la cloche a sonné il y a
# un moment. L'écart à l'heure prévue se compte donc en DEMI-HEURES, sauf pour
# les deux ou trois choses que la ville entend en même temps : la cloche de
# l'office, la fournée, la relève. Celles-là restent serrées, et c'est
# précisément parce qu'elles sont serrées qu'on les reconnaît comme des signaux.
#
# `duree_var` : de combien on s'écarte de la durée écrite, en fraction. Compter
# les minutes qu'on passe au puits est aussi une idée d'horloger — un tiers par
# défaut (voir journee.js), davantage pour ce qui traîne.
#
# `duree` : combien de minutes on reste sur place. `rangs` / `age` / `jours` :
# à qui et quand ce besoin s'applique — sans filtre, il vaut pour tout le monde.
#
# `part` : la fraction de ceux qui y ont droit et qui le font vraiment. C'est
# le garde-fou contre l'absurde arithmétique : accorder l'étuve à toute la
# ville une fois la semaine, c'est mille trois cents personnes par étuve et par
# jour, et une ville où quatre habitants sur dix se lavent en même temps le
# mardi après-midi. Tirée du même hachage que les heures : stable, gratuite.
BESOINS = [
    # --- l'eau : le premier flux d'une ville, très loin devant le pain ------
    # Trois allers par jour et par foyer, portée courte. Ce n'est pas le maître
    # qui y va : c'est le plus jeune du feu, et c'est ce qui met des enfants
    # dans la rue au petit matin.
    # On y va « le matin », « vers midi », « avant la nuit » — pas à 6h15.
    dict(id="eau", service="puits", par_jour=3, heures=[375, 720, 1110],
         largeur=85, duree=12, duree_var=0.6,
         rangs=["famille", "valet"], age=[8, 55]),

    # --- le pain : cuit hors du logis, donc une sortie par jour ------------
    # La fournée, elle, est un vrai signal : le pain sort chaud à une heure que
    # tout le quartier connaît, et l'on n'y va pas trois heures plus tard. C'est
    # l'un des rares endroits où l'on GARDE une fenêtre étroite.
    dict(id="pain", service="boulangerie", par_jour=1, heures=[400],
         largeur=35, duree=10, duree_var=0.5, rangs=["famille"], age=[10, 70]),

    # --- le travail : à la cloche, et l'on n'y va que si l'on n'y dort pas -
    # `travail` renvoie au bâtiment où le corps travaille. Pour l'écrasante
    # majorité c'est celui où il loge : le besoin ne produit alors AUCUN
    # trajet, et c'est juste — l'échoppe est au rez-de-chaussée.
    # On part au jour levé, et le jour ne se lève pas à la minute : une heure
    # d'écart entre le premier et le dernier n'a rien d'extravagant.
    # ON NE TRAVAILLE PAS NEUF HEURES SANS LEVER LA TÊTE, et c'est le trou que
    # cette table avait : un bloc unique de 6 h 30 à 15 h 30. Le résultat se
    # voyait à l'écran — de midi et demi à trois heures et demie, la ville
    # entière était sous un toit et les rues étaient vides, à l'heure même où
    # une ville médiévale est la plus bruyante.
    # On coupe donc la journée en deux, comme elle l'a toujours été : on
    # travaille du jour levé au repas, on mange, on repart. Le nombre d'heures
    # travaillées ne change pas ; ce qui change, c'est qu'il y a deux allers et
    # deux retours dans les rues au lieu d'un.
    dict(id="labeur", service="travail", par_jour=1, heures=[390],
         largeur=60, duree=310, duree_var=0.15,
         rangs=["maitre", "compagnon", "valet"]),
    dict(id="labeur-releve", service="travail", par_jour=1, heures=[800],
         largeur=55, duree=225, duree_var=0.18,
         rangs=["maitre", "compagnon", "valet"]),

    # --- LE REPAS DE MIDI ---------------------------------------------------
    # Le repas principal se prend au milieu du jour, et tout le monde ne le
    # prend pas chez soi : le compagnon et le journalier mangent où ils
    # peuvent. La taverne sert à manger avant de servir à boire — c'est le même
    # bâtiment, ce n'est pas la même heure, et il fallait le dire.
    dict(id="dinee", service="taverne", par_jour=1, heures=[725],
         largeur=45, duree=50, duree_var=0.4,
         rangs=["compagnon", "valet"], age=[14, 70], part=0.4),
    # Ceux qui ne s'attablent pas vont chercher de quoi manger : la sortie la
    # plus courte de la table, et l'une des plus fréquentes.
    dict(id="croute", service="echoppe", par_jour=1, heures=[715],
         largeur=50, duree=18, duree_var=0.5, age=[8, 78], part=0.45),

    # --- LES COURSES DU MÉTIER ----------------------------------------------
    # Ce qui fait qu'un atelier n'est pas une boîte fermée : on livre, on va
    # chercher, on porte un ouvrage. C'est le maître et le compagnon qui
    # sortent, pas la maisonnée — et ça peuple l'après-midi, qui restait vide.
    dict(id="commission", service="echoppe", par_jour=1, heures=[880],
         largeur=140, duree=30, duree_var=0.6,
         rangs=["maitre", "compagnon"], part=0.4),

    # --- le marché : deux fois la semaine, la seule sortie longue ----------
    dict(id="marche", service="marche", par_jour=1, heures=[540], largeur=125,
         duree=70, duree_var=0.5,
         rangs=["maitre", "famille"], jours=[1, 4], age=[14, 70]),

    # --- le plein jour : ce qui manquait, et qui vidait la ville ------------
    # Mesuré avant d'écrire cette ligne : de huit heures à onze heures, mille
    # deux cent cinquante personnes dehors sur quatre cent mille — trois pour
    # mille. Une ville n'est jamais vide à dix heures du matin. Ce n'est pas un
    # besoin nommé, c'est TOUT LE RESTE : porter un pli, rendre un outil,
    # accompagner un enfant, aller voir sa sœur. On le prend à l'échoppe parce
    # que c'est le bâtiment le plus dense de Port-Réal — une pour cent dix
    # âmes —, donc le plus proche de n'importe quel seuil.
    dict(id="courses", service="echoppe", par_jour=1, heures=[555],
         largeur=195, duree=35, duree_var=0.7, age=[10, 75], part=0.5),

    # --- l'échoppe du soir : ce qui manquait entre le labeur et la taverne --
    # Le labeur finit à 15 h 30 et la taverne n'ouvre qu'à 20 h : sans cette
    # ligne, la ville est vide de seize à dix-neuf heures, ce qui n'arrive dans
    # aucune ville. L'échoppe est le lieu le plus dense de Port-Réal — une pour
    # cent dix âmes — et c'est là qu'on passe en rentrant.
    dict(id="emplettes", service="echoppe", par_jour=1, heures=[960], largeur=165,
         duree=25, duree_var=0.6, age=[12, 72], part=0.55),

    # --- le soir : ce qui remplit les rues quand le jour tombe -------------
    # On y va quand on y va, et l'on en sort quand on en sort : c'est la ligne
    # qui mérite le plus de variation de durée de toute la table.
    dict(id="taverne", service="taverne", par_jour=1, heures=[1200],
         largeur=115, duree=110, duree_var=0.65,
         rangs=["maitre", "compagnon", "valet"], age=[16, 70], part=0.35),

    # --- l'office : une fois la semaine, et les cloches synchronisent ------
    # Un signal PARTAGÉ est ce qui fait qu'une foule se lit comme une ville et
    # non comme des points browniens : ici la largeur est étroite exprès.
    # La cloche est la seule montre de la ville, et c'est une montre qu'on
    # ENTEND : la fenêtre reste étroite, et la durée avec — on sort de l'office
    # tous ensemble parce qu'il est fini.
    dict(id="office", service="septuaire", par_jour=1, heures=[480],
         largeur=12, duree=60, duree_var=0.08, jours=[6], part=0.45),

    # --- PARLER — le besoin qu'aucune table de ce genre n'écrit jamais -------
    # Tout ce qui précède fait sortir les gens pour PRENDRE quelque chose :
    # de l'eau, du pain, un ouvrage, un bain. Or la moitié de ce qu'on fait
    # dehors n'a pas d'objet — on s'arrête, on demande des nouvelles, on reste
    # un quart d'heure de trop. Une ville où personne ne s'attarde a des rues
    # qui se vident dès que la course est finie, et c'est exactement ce qu'on
    # voyait : des trajets, jamais un attroupement.
    #
    # ON NE PARLE PAS N'IMPORTE OÙ. Le puits est le lieu de la parole d'une
    # ville médiévale — on y vient pour l'eau et l'on y reste pour le reste —
    # et c'est aussi l'un des deux seuls endroits que la table tient pour être
    # à ciel ouvert. D'où deux lignes, et pas une : la causette du puits, qui
    # se répète, et la flânerie du marché, qui dure.
    #
    # Et ça compte pour le jeu, pas seulement pour l'image : un attroupement
    # est une COUVERTURE. Une troupe qui sort une malle à l'heure où trente
    # personnes bavardent devant le puits ne sort pas une malle de la même
    # façon qu'à trois heures du matin — et le joueur doit pouvoir le lire sur
    # le plan sans qu'on le lui dise.
    dict(id="causette", service="puits", par_jour=2, heures=[615, 1035],
         largeur=150, duree=28, duree_var=0.7,
         rangs=["famille", "valet", "compagnon"], age=[10, 80], part=0.32),
    # Au marché on traîne, même sans rien acheter — c'est la place publique de
    # ceux qui n'en ont pas.
    dict(id="badauds", service="marche", par_jour=1, heures=[870],
         largeur=200, duree=45, duree_var=0.65, age=[8, 78], part=0.18),

    dict(id="etuve", service="etuve", par_jour=1, heures=[840], largeur=130,
         duree=50, duree_var=0.55, jours=[3], age=[12, 65], part=0.12),
]

# La ronde du guet ne se range pas dans la table : c'est le seul métier dont le
# travail EST un déplacement, et il continue après le couvre-feu, quand plus
# rien d'autre ne bouge. On le dit à part pour que ce soit visible.
# Une ronde n'est pas une course : elle n'a pas de but, elle a un CIRCUIT. On
# ne lui invente pas de points de passage — on prend les adresses du poste
# (son puits, son échoppe, sa taverne, son marché) : ce sont de vrais endroits
# du quartier, et un guet qui passe au puits puis à la taverne fait exactement
# ce qu'un guet fait. Le tour choisi varie par hachage, donc deux hommes du
# même poste ne tournent pas ensemble.
# Ce qui se passe à ciel ouvert — voir la clef `plein_air` de la sortie. Le
# marché est un étal sous une bâche, pas une halle fermée : il compte dehors.
PLEIN_AIR = ["puits", "marche"]

# COMBIEN DE PLACE PREND UN ATTROUPEMENT — en mètres, par service.
# `journee.js` disperse les gens arrêtés dans un disque autour de leur
# destination, et ce disque avait un rayon FIXE : sept mètres, qu'ils soient
# douze ou trois mille. Le résultat se voit de loin — une tache ocre pleine,
# grosse comme un pâté de maisons, là où il devrait y avoir un marché.
#
# Or la foule d'un lieu se déduit de sa RARETÉ : Port-Réal a 457 puits et 16
# marchés pour les mêmes quatre cent mille habitants. Un puits sert deux
# rues, un marché sert un quartier entier — et occupe une place, pas un point.
# D'où ces rayons, qui sont ceux de l'emprise réelle du lieu : on ne disperse
# pas pour faire joli, on dit quelle surface la chose occupe au sol.
ETENDUE = {
    "puits": 5.,          # une margelle et ceux qui attendent leur tour
    "boulangerie": 4.,    # le seuil et deux pas de rue
    "echoppe": 4.,
    "taverne": 6.,        # la salle, et le banc devant
    "septuaire": 18.,     # un parvis
    "etuve": 8.,
    "marche": 55.,        # une PLACE — étals, allées, badauds
    "travail": 5.,
    "ronde": 4.,
    "poste": 6.,
}

RONDES = {
    "guet":          dict(par_jour=4, heures=[400, 760, 1120, 120], largeur=45, duree=30),
    "sergent":       dict(par_jour=2, heures=[430, 1150], largeur=40, duree=35),
    "capitaine-guet": dict(par_jour=1, heures=[520], largeur=60, duree=45),
}

# ---------------------------------------------------------------------------
# LES VEILLES — un guet ne fait pas des courses, il prend son quart
# ---------------------------------------------------------------------------
# Ce que RONDES décrivait, c'était quatre sorties d'une demi-heure : deux heures
# de service par jour pour deux mille hommes, et personne aux portes à quatre
# heures du matin. Or un guet ne va pas quelque part — IL TIENT UN POSTE, et il
# le tient sans interruption, ce qui est toute la différence entre une ville
# gardée et une ville où passent des gens armés.
#
# D'où trois quarts qui se relaient et couvrent les vingt-quatre heures. À tout
# instant, un tiers de l'effectif est dehors : ~660 manteaux d'or, dont une part
# aux portes et sur les murs, et une part en tournée. Le quart d'un homme se
# DÉDUIT de son identité (voir `journee.js`) — rien à écrire dans les corps,
# rien à tenir à jour, et le même homme reprend toujours le même quart.
#
# `quarts`   : [début, durée] en minutes. Celui qui déborde minuit est repris
#              la veille : c'est la nuit, et c'est le quart qui compte pour une
#              troupe qui travaille après le couvre-feu.
# `tours`    : combien de fois on quitte le poste pendant le quart, et pour
#              combien de temps. Entre deux tours, on est AU POSTE — c'est
#              l'état par défaut d'un homme de quart, et il fallait qu'il existe.
# `patrouilles` : ON NE PATROUILLE PAS SEUL. Le nombre de tournées distinctes
#              qu'un poste envoie par quart : deux hommes qui tombent sur la
#              même sortent ensemble et suivent le même circuit. Le régler bas,
#              c'est des groupes plus gros ; haut, des hommes isolés. À ~27
#              hommes de quart par corps de garde, douze donne des paires.
VEILLES = {
    "guet": dict(quarts=[[360, 480], [840, 480], [1320, 480]],
                 tours=3, duree=38, duree_var=.4, patrouilles=12),
    # Le sergent tient le poste plus qu'il ne le quitte : il fait le tour de ses
    # hommes une fois ou deux, pas davantage.
    "sergent": dict(quarts=[[360, 480], [840, 480], [1320, 480]],
                    tours=2, duree=45, duree_var=.35, patrouilles=6),
    # Un capitaine n'a pas de quart : il passe le jour, et l'on ne sait jamais
    # quand. C'est ce qui le rend redoutable pour ses propres hommes.
    "capitaine-guet": dict(quarts=[[420, 660]], tours=3, duree=55,
                           duree_var=.5, patrouilles=3),
    # La geôle ne se garde pas par tournées : on y est, ou l'on n'y est pas.
    "geolier": dict(quarts=[[360, 720], [1080, 720]], tours=0, duree=0,
                    duree_var=0, patrouilles=1),
    # Ceux du Donjon et de la douane tiennent un poste et n'en bougent pas :
    # leur ville, c'est une porte.
    "garde-donjon": dict(quarts=[[360, 480], [840, 480], [1320, 480]],
                         tours=1, duree=30, duree_var=.3, patrouilles=8),
    "garde-douane": dict(quarts=[[300, 600], [900, 540]], tours=1, duree=35,
                         duree_var=.3, patrouilles=2),
}
VEILLES_PEYREDRAGON = {}

# ---------------------------------------------------------------------------
# LE COUVRE-FEU — ce qui rend la garde possible
# ---------------------------------------------------------------------------
# ON NE GARDE PAS UNE VILLE EN LA SURVEILLANT : ON LA VIDE, ET L'ON GARDE CE QUI
# RESTE. C'est le fait central de `docs/recherche/les-gardes-et-patrouilles-de-
# ville.md` (§ 0), et il manquait entierement : `journee.js` envoyait les gens
# au puits a trois heures du matin, si bien que les seize guettes patrouillaient
# une ville qui ne dort jamais et que la retraite de l'Aieule ne fermait rien.
#
# La chaine va dans l'autre sens qu'on croit. Ce n'est pas le guet qui produit
# l'ordre nocturne, c'est l'ordre nocturne qui rend le guet possible : soixante
# hommes ne tiennent Paris que parce que la rue est legalement interdite.
#
# `retraite`  : la cloche du soir. On couvre les braises, on ferme les portes,
#               on vide les tavernes, on rentre. Ici l'Aieule du vieux septuaire
#               (voir scripts/ville/port-real-cloches.json).
# `ouverture` : le Ferrant. Les portes de la ville s'ouvrent apres lui, jamais
#               avant, et la journee recommence.
# `rentrer`   : les minutes qu'on laisse a qui est dehors pour rentrer chez lui
#               sans etre inquiete. Une taverne ne se vide pas au coup de cloche.
#
# ⚠ CES DEUX HEURES SONT FIXES, ET ELLES NE DEVRAIENT PAS L'ETRE. Les sources
# donnent partout une borne ASTRONOMIQUE — « du coucher au lever du soleil » —
# qui bouge de plusieurs heures dans l'annee. On pose des chiffres tant que le
# monde n'a pas de saisons ; le jour ou il en aura, c'est ici qu'on branchera le
# soleil, et nulle part ailleurs.
COUVRE_FEU = dict(retraite=1260, ouverture=330, rentrer=30,
                  cloche_retraite="septuaire-aieule",
                  cloche_ouverture="septuaire-ferrant")

# Le bourg de Peyredragon n'a ni muraille ni guet : la nuit y est noire, et
# personne ne la fait respecter. On garde les heures pour que les pecheurs et
# les cuisines du chateau se comportent pareil, sans qu'il y ait de delit.
COUVRE_FEU_PEYREDRAGON = dict(retraite=1260, ouverture=330, rentrer=60,
                              applique=False)

# ---------------------------------------------------------------------------
# PEYREDRAGON — un bourg de pêche, et une forteresse par-dessus
# ---------------------------------------------------------------------------
# Rien de la table de Port-Réal ne se recopie ici, et ce n'est pas une question
# d'échelle : ce n'est pas la même vie. Il n'y a sous les murs ni puits de
# quartier, ni rue d'Acier, ni marché — on y vit du poisson, du sel et de ce que
# le château commande. Ce que le bourg a : la grève où l'on rince et où l'on
# étend, le quai d'où partent les barques, le four à pain, le petit septuaire,
# la taverne, et le travail de celui qui ne dort pas où il travaille.
#
# Et le CHÂTEAU a sa propre boucle, qui n'est pas celle d'un bourgeois : on
# descend aux cuisines chercher l'eau, on mange à la grande salle deux fois le
# jour, et surtout ON MONTE AU CHEMIN DE RONDE — un homme d'armes ne va pas à
# l'échoppe, il prend son tour et il en redescend.
#
# `depuis` : le troisième champ d'une ligne de SERVICES. Il dit QUELS BÂTIMENTS
# ont cette adresse, et pas seulement lesquels la portent. Sans lui, la lingère
# des communs monterait au chemin de ronde et le pêcheur irait chercher son pain
# dans la cuisine de la reine : `journee.js` ne filtre un besoin que par RANG, et
# le rang ne distingue pas un valet d'écurie d'un homme d'armes. Un bâtiment hors
# de `depuis` reçoit -1, que `journee.js` lit déjà comme « pas d'adresse, donc
# pas de trajet ». Port-Réal n'en a pas besoin et ses lignes n'en portent pas.
BOURG = {"maison-pecheur", "sechoir", "hangar", "boucanerie", "saline",
         "entrepot", "echoppe", "taverne", "auberge", "tannerie", "boulangerie",
         "corderie", "brasserie", "voilerie", "forge-bourg", "septuaire-bourg",
         "corps-de-garde", "cabane"}
# Ceux dont le métier EST la muraille. Les autres salles du château sont la
# maison de la reine, et elles n'ont rien à faire sur le chemin de ronde.
GARNISON = {"chateau-baraques", "chateau-porte", "chateau-guet", "chateau-tour"}
CHATEAU = GARNISON | {
    "chateau-communs", "chateau-cuisines", "chateau-grande-salle",
    "chateau-antichambre", "chateau-appartements", "chateau-enfants",
    "chateau-hotes", "chateau-roukerie", "chateau-septuaire", "chateau-forge",
    "chateau-officine", "chateau-archives", "chateau-cellier", "chateau-froide",
    "chateau-etuves", "chateau-cachots", "chateau-fosses"}

SERVICES_PEYREDRAGON = [
    # Les séchoirs à filets sont l'équipement collectif du bourg : c'est là
    # qu'on étend, qu'on rince, qu'on prend l'eau du ruisseau et qu'on cause.
    # Le bourg n'a pas de puits maçonné, et l'on n'en invente pas un.
    ("greve",     ["sechoir"],                                   BOURG),
    # On ne va pas « au quai » : on va au hangar où dort sa barque.
    ("quai",      ["hangar"],                    {"maison-pecheur", "cabane"}),
    ("four",      ["boulangerie"],                               BOURG),
    ("taverne",   ["taverne", "auberge"],                        BOURG),
    # Chacun le sien : le bourg a son petit septuaire, le château sa chapelle.
    ("septuaire", ["septuaire-bourg", "chateau-septuaire"],        None),
    # Le puits est dans la cour des cuisines : l'eau et le feu, une seule course.
    ("cuisines",  ["chateau-cuisines"],                        CHATEAU),
    ("salle",     ["chateau-grande-salle"],                    CHATEAU),
    # Le chemin de ronde et lui seul : c'est LÀ qu'on prend son tour. Le mettre
    # avec les tours et les portes revenait à faire monter la garde à trente
    # pas de sa paillasse — les baraques touchent la porte du Dragon —, et l'on
    # ne voyait jamais personne traverser la cour. Les veilleurs qui logent déjà
    # dans une tour, eux, n'ont nulle part à aller : leur adresse est leur logis,
    # et `journee.js` ne fabrique aucun trajet pour ceux-là.
    ("guet",      ["chateau-guet"],                            GARNISON),
]

BESOINS_PEYREDRAGON = [
    # --- la grève : le flux du bourg, comme le puits est celui de la ville ---
    dict(id="greve", service="greve", par_jour=3, heures=[375, 735, 1095],
         largeur=90, duree=14, duree_var=0.65,
         rangs=["famille", "valet"], age=[8, 55]),

    # --- le pain : deux fours pour tout le bourg, une fournée le matin ------
    # La fournée est un signal : deux fours pour huit cents âmes, et le pain
    # sort chaud à une heure que le bourg entier connaît.
    dict(id="pain", service="four", par_jour=1, heures=[405], largeur=35,
         duree=12, duree_var=0.5, rangs=["famille"], age=[10, 70]),

    # --- la mer : on descend à la barque avant le jour, on rentre à none ----
    # C'est la journée de travail du bourg, et elle ne ressemble à aucune
    # journée d'atelier : elle commence dans le noir et elle se passe ailleurs.
    # La MARÉE est une montre, et la seule qui vaille au bourg : on ne part pas
    # quand on veut, on part quand l'eau le permet. La fenêtre reste donc
    # serrée — mais on ne rentre pas tous ensemble, et la durée varie beaucoup :
    # c'est le poisson qui décide de l'heure du retour, pas le pêcheur.
    # LA PECHE PASSE LE COUVRE-FEU. Un homme dehors avant le jour n'est pas un
    # noctivague s'il descend a sa barque : le couvre-feu arrete ceux qui n'ont
    # pas de raison, jamais ceux qui en ont une. `nuit` est cette raison-la, et
    # elle doit etre ECRITE — sinon c'est le MJ qui l'invente au cas par cas.
    dict(id="peche", service="quai", nuit=True, par_jour=1, heures=[330], largeur=50,
         duree=400, duree_var=0.3, rangs=["maitre", "valet"], age=[12, 68],
         part=0.8),

    # --- l'ouvrage du bourg, qui se fait DEHORS -----------------------------
    # Un bourg de pêche ne travaille pas dans des pièces : on étend les filets,
    # on sale, on fume, on répare les casiers, on radoube — sur la grève et sur
    # les quais, du matin au soir. Sans cette ligne, tout le monde est soit chez
    # soi soit sous un toit, et l'île paraît morte à onze heures du matin alors
    # que c'est l'heure où elle travaille le plus. C'est la ligne qui fait la
    # différence entre un bourg et un décor de bourg.
    dict(id="ouvrage", service="greve", par_jour=1, heures=[660], largeur=200,
         duree=300, duree_var=0.35,
         rangs=["maitre", "compagnon", "valet", "famille"], age=[12, 66],
         part=0.55),

    # --- le travail de celui qui ne dort pas où il travaille ----------------
    # Le sécheur, le saunier, le gardien d'entrepôt et l'homme du corps de garde
    # logent dans une maison de pêcheur et vont ailleurs. Pour tous les autres,
    # `travail` est le logis et le besoin ne produit aucun trajet.
    dict(id="labeur", service="travail", par_jour=1, heures=[390], largeur=60,
         duree=540, duree_var=0.15, rangs=["maitre", "compagnon", "valet"]),

    # --- le tour de garde : ce qui remplace la journée d'atelier ------------
    # TROIS tours et non deux, et le premier au milieu de la nuit : une place
    # forte dont le chemin de ronde est vide à deux heures du matin n'est pas
    # une place forte. La largeur est très ample exprès — une garde ne monte pas
    # d'un seul bloc, elle s'égrène, et c'est ce qui fait la relève.
    # La relève est le seul horaire tenu de la forteresse — on ne quitte pas son
    # tour quand on en a assez —, donc la DURÉE varie peu là où l'arrivée
    # s'égrène.
    dict(id="garde", service="guet", par_jour=3, heures=[90, 630, 1140],
         largeur=110, duree=200, duree_var=0.1,
         rangs=["compagnon", "valet"], age=[15, 55]),

    # --- l'eau et les cuisines du château -----------------------------------
    dict(id="eau-chateau", service="cuisines", par_jour=3,
         heures=[330, 690, 1050], largeur=80, duree=20, duree_var=0.6,
         rangs=["valet", "famille"], age=[10, 60]),

    # --- on mange en salle, et tout le château y descend --------------------
    # Le seul signal partagé de la forteresse : deux fois le jour, la cour se
    # vide d'un coup. C'est ce qui la fait lire comme une maison, et non comme
    # vingt-quatre salles voisines.
    # On ne fait pas attendre la table de la reine : fenêtre serrée, durée ferme.
    dict(id="repas", service="salle", par_jour=2, heures=[420, 1140],
         largeur=25, duree=45, duree_var=0.12,
         rangs=["maitre", "compagnon", "valet", "famille"], age=[6, 80]),

    # --- le soir au bourg ---------------------------------------------------
    dict(id="taverne", service="taverne", par_jour=1, heures=[1185],
         largeur=115, duree=105, duree_var=0.65,
         rangs=["maitre", "compagnon", "valet"], age=[16, 70], part=0.30),

    # --- l'office : le septième jour, et les deux septuaires sonnent --------
    dict(id="office", service="septuaire", par_jour=1, heures=[480],
         largeur=12, duree=60, duree_var=0.08, jours=[6], part=0.45),
]

# Le tour de garde de Peyredragon est DANS la table, pas à côté : ici il n'est
# pas l'exception d'un métier, c'est la journée de cent vingt hommes sur huit
# cents, et il a une destination — le chemin de ronde, les tours, les portes.
RONDES_PEYREDRAGON = {}

# La grève où l'on rince, le quai d'où l'on pousse la barque, et le chemin de
# ronde : les trois endroits du lieu où l'on est sous le ciel. Tout le reste —
# le four, la taverne, les cuisines, la grande salle, le septuaire — est sous un
# toit, et le château a un maillage qui le prouve à l'écran.
PLEIN_AIR_PEYREDRAGON = ["greve", "quai", "guet"]

if LIEU == "peyredragon":
    SERVICES = SERVICES_PEYREDRAGON
    BESOINS = BESOINS_PEYREDRAGON
    RONDES = RONDES_PEYREDRAGON
    VEILLES = VEILLES_PEYREDRAGON
    PLEIN_AIR = PLEIN_AIR_PEYREDRAGON
    COUVRE_FEU = COUVRE_FEU_PEYREDRAGON

# ---------------------------------------------------------------------------
# LA RÉSOLUTION — le plus proche de chaque service, pour chaque bâtiment
# ---------------------------------------------------------------------------
# À vol d'oiseau, et c'est voulu : l'ADRESSE se choisit sur ce qu'on voit du
# seuil, le CHEMIN se calcule ensuite sur les rues. Confondre les deux ferait
# payer un A* à quarante-huit mille bâtiments pour un résultat identique dans
# quatre-vingt-dix-neuf cas sur cent.
MAILLE = 200

def semer(usages):
    seau = defaultdict(list)
    for k, b in enumerate(BAT):
        if b[C["usage"]] in usages:
            x, y = b[C["porte_x"]], b[C["porte_y"]]
            seau[(int(x // MAILLE), int(y // MAILLE))].append((x, y, k))
    return seau

def plus_proche(seau, x, y):
    """Le plus proche, en élargissant l'anneau jusqu'à en trouver un."""
    ci, cj = int(x // MAILLE), int(y // MAILLE)
    for r in range(1, 40):
        meil, di_meil = 9e18, -1
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                # on ne rebalaie pas le cœur de l'anneau au tour suivant
                if r > 1 and abs(di) < r and abs(dj) < r: continue
                for (qx, qy, k) in seau.get((ci + di, cj + dj), ()):
                    d = (x - qx) ** 2 + (y - qy) ** 2
                    if d < meil: meil, di_meil = d, k
        # un anneau de plus après le premier trouvé : le plus proche en cases
        # n'est pas le plus proche en mètres
        if di_meil >= 0:
            for di in range(-r - 1, r + 2):
                for dj in range(-r - 1, r + 2):
                    for (qx, qy, k) in seau.get((ci + di, cj + dj), ()):
                        d = (x - qx) ** 2 + (y - qy) ** 2
                        if d < meil: meil, di_meil = d, k
            return di_meil, math.sqrt(meil)
    return -1, 0.0

print("… on résout les adresses de %d bâtiments" % len(BAT))
DESSERT = [[-1] * len(SERVICES) for _ in BAT]
portees = {}
for s, ligne in enumerate(SERVICES):
    # `depuis` est optionnel et n'existe qu'à Peyredragon : une ligne à deux
    # champs vaut pour tout le bâti, comme elle l'a toujours fait.
    nom_service, usages = ligne[0], ligne[1]
    depuis = ligne[2] if len(ligne) > 2 else None
    seau = semer(usages)
    if not seau:
        print("   %-14s aucun bâtiment de ce genre — personne n'ira nulle part" % nom_service)
        continue
    ds = []
    for k, b in enumerate(BAT):
        if depuis is not None and b[C["usage"]] not in depuis:
            continue          # ce bâtiment-là n'a pas cette adresse : -1
        j, d = plus_proche(seau, b[C["porte_x"]], b[C["porte_y"]])
        DESSERT[k][s] = j
        ds.append(d)
    ds.sort()
    if not ds:
        print("   %-14s aucun bâtiment n'a droit à cette adresse" % nom_service)
        continue
    portees[nom_service] = {"mediane_m": round(ds[len(ds) // 2], 1),
                            "p90_m": round(ds[int(len(ds) * 0.9)], 1),
                            "max_m": round(ds[-1], 1)}
    print("   %-14s %5d lieux — %5d desservis, portée médiane %5.0f m, "
          "p90 %5.0f m, max %5.0f m"
          % (nom_service, sum(len(v) for v in seau.values()), len(ds),
             portees[nom_service]["mediane_m"], portees[nom_service]["p90_m"],
             portees[nom_service]["max_m"]))

# ---------------------------------------------------------------------------
# L'ALTITUDE DE LA PORTE — le sol de la rue, pas l'étage du logis
# ---------------------------------------------------------------------------
# À Port-Réal, `b[z]` est le sol du bâtiment et la porte y est : rien à faire.
# À Peyredragon, le bâti compte aussi les salles du château, dont plusieurs sont
# des étages — les appartements de la reine sont donnés à 158 m, les cachots à
# 115, et la cour où l'on marche est à 124. Prendre `b[z]` pour altitude de
# porte y ferait attendre une chambrière à trente-quatre mètres au-dessus du
# pavé. On prend donc l'altitude de la CHAUSSÉE au point de la porte, ce qui est
# la définition même d'un seuil.
def hauteurs_de_porte():
    if PREFIXE != "peyredragon":
        return [b[C["z"]] for b in BAT]
    G = json.load(io.open(os.path.join(MONDE, PREFIXE + ".graph.json"),
                          encoding="utf-8"))
    segs = []
    for e in G["aretes"]:
        if e.get("couche") != "L1-surface":
            continue
        for a, b in zip(e["trace"], e["trace"][1:]):
            segs.append((a, b))
    out = []
    for b in BAT:
        x, y = b[C["porte_x"]], b[C["porte_y"]]
        meil, z = 9e18, b[C["z"]]
        for (p, q) in segs:
            ux, uy = q[0] - p[0], q[1] - p[1]
            n = ux * ux + uy * uy
            t = 0.0 if n == 0 else max(0.0, min(1.0, ((x - p[0]) * ux + (y - p[1]) * uy) / n))
            d = (x - p[0] - ux * t) ** 2 + (y - p[1] - uy * t) ** 2
            if d < meil:
                meil = d
                z = round((p[2] if len(p) > 2 else 0.0)
                          + ((q[2] if len(q) > 2 else 0.0) - (p[2] if len(p) > 2 else 0.0)) * t, 1)
        out.append(z)
    return out


ZPORTE = hauteurs_de_porte()

SORTIE = {
    "_lisez_moi": (
        "La table des BESOINS (ce qu'un rôle fait de sa journée, à quelle heure "
        "et pour combien de temps) et les ADRESSES de chaque bâtiment (le puits, "
        "la boulangerie, la taverne, le marché, le septuaire et l'étuve les plus "
        "proches de sa porte). Rien ici ne fait bouger personne : la position se "
        "CALCULE à l'affichage, par ecrans/modules/monde/journee.js. Engendré "
        "par scripts/monde/besoins.py — ne pas éditer à la main."
        if PREFIXE == "portreal" else
        "La table des BESOINS de Peyredragon (ce qu'un rôle fait de sa journée) "
        "et les ADRESSES de chaque bâtiment — la grève, le hangar à barques, le "
        "four, la taverne, le septuaire pour le bourg ; les cuisines, la grande "
        "salle et le chemin de ronde pour le château. Rien ici ne fait bouger "
        "personne : la position se CALCULE à l'affichage, par "
        "ecrans/modules/monde/journee.js. Engendré par "
        "scripts/monde/besoins.py peyredragon — ne pas éditer à la main."),
    "services": [ligne[0] for ligne in SERVICES],
    # QUELS SERVICES SE PASSENT DEHORS. Ce n'est pas un détail de rendu : c'est
    # la même règle que pour ceux qui dorment chez eux. Un homme arrêté aux
    # cuisines ou dans une échoppe est DANS LES MURS — le dessiner, c'est poser
    # un point sous un toit, que le maillage cache (mesuré à Peyredragon : vingt-
    # neuf personnes dans le cadre, un seul pixel visible) ou, pire, qu'il ne
    # cache pas et qui flotte alors à travers la pierre.
    # Le puits, la grève, le quai, l'étal du marché et le chemin de ronde sont à
    # ciel ouvert : ceux-là se voient, et ce sont eux qui font la place pleine.
    "plein_air": PLEIN_AIR,
    # La porte de chaque bâtiment, dans l'ordre du bâti : le point de chaussée
    # d'où l'on sort et où l'on arrive. Le navigateur n'a pas à charger tout le
    # bâti pour tracer un chemin — il lui faut ces trois nombres, et c'est tout.
    "portes": [[b[C["porte_x"]], b[C["porte_y"]], z] for b, z in zip(BAT, ZPORTE)],
    "besoins": BESOINS,
    "rondes": RONDES,
    "etendues": ETENDUE,
    "veilles": VEILLES,
    "couvre_feu": COUVRE_FEU,
    "portees": portees,
    # une ligne par bâtiment, dans l'ordre du bâti ; -1 = pas de service atteint
    "dessert": DESSERT,
}
io.open(os.path.join(MONDE, PREFIXE + ".besoins.json"), "w", encoding="utf-8").write(
    json.dumps(SORTIE, ensure_ascii=False, separators=(",", ":")))

print()
print("  %d services, %d besoins, %d lignes d'adresses"
      % (len(SERVICES), len(BESOINS), len(DESSERT)))
print("  -> monde/%s.besoins.json" % PREFIXE)
