# -*- coding: utf-8 -*-
"""Donner un CORPS à chaque habitant de Port-Réal.

    python scripts/monde/peupler.py     (après usages.py, avant ou après batir.py)

Jusqu'ici la ville était vide : quarante-huit mille bâtiments, un métier chacun,
et personne dedans. La population n'existait que comme un chiffre déduit du
plancher. Ce script la fait exister une âme à la fois.

Un « corps physique » (`physicalactor`) n'est pas un personnage : c'est un
emplacement occupé. Il porte un id, un nom, un rôle, un âge, et une POSITION EN
MÈTRES dans le monde bâti — l'étage compris. Il ne pense rien, ne veut rien,
n'a pas d'intentions : c'est du mobilier vivant, et c'est exactement ce qu'il
faut pour que le MJ puisse ensuite :

  - LIER un personnage existant à un corps — et voilà que le mestre a une
    maison, une rue, un étage, des voisins nommés ;
  - EN PROMOUVOIR un nouveau — on prend le tavernier du Crochet qui existait
    déjà, avec son nom et son adresse, et on lui écrit une fiche.

Le lien ne s'écrit JAMAIS ici : ce fichier est engendré et se réécrit à chaque
passage. Les liens vivent dans `etat/corps.json`, tenus par `scripts/corps.py`.

Rien d'aléatoire dans la STRUCTURE : qui habite où découle du métier du
bâtiment et de son plancher. Le hasard ne sert qu'aux noms, aux âges et au
placement fin dans la parcelle — et il est ensemencé, donc rejouable.

Ce qui sort, trois fichiers pour trois lecteurs :

    monde/portreal.gens.json    le MANIFESTE — colonnes, rôles, maille, compte
                                de chaque cellule. 9 ko, le seul qu'on lise
                                en entier.
    monde/gens/<i>-<j>.json     les corps, en cellules de 250 m. Pour le MJ,
                                par scripts/corps.py.
    monde/gens/<i>-<j>.bin      leur double dense, 8 octets par corps. Pour le
                                rendu seul, par ecrans/modules/monde/gens.js.
"""
import json, io, os, math, random, struct, sys, unicodedata
from collections import Counter, defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(os.path.dirname(ICI))
MONDE = os.path.join(RACINE, "monde")

R = random.Random(1290323)

# ---------------------------------------------------------------------------
# QUEL LIEU — un bourg de pêcheurs n'est pas une capitale
# ---------------------------------------------------------------------------
# Le mécanisme est le même partout : le plancher donne les âmes, l'usage donne
# les postes, la parcelle donne la place. Ce qui change d'un lieu à l'autre,
# ce sont les TABLES — les métiers qu'on y trouve, la densité de ses quartiers,
# et le compte qu'on vise. Elles sont écrites en clair plus bas, une par lieu ;
# ce bloc ne fait que dire laquelle on prend.
LIEUX = {"port-real": "portreal", "peyredragon": "peyredragon"}
LIEU = (sys.argv[1] if len(sys.argv) > 1 else "port-real").lower()
if LIEU not in LIEUX:
    sys.exit("lieu inconnu : %s — attendus : %s" % (LIEU, ", ".join(LIEUX)))
PREFIXE = LIEUX[LIEU]

B = json.load(io.open(os.path.join(MONDE, PREFIXE + ".bati.json"), encoding="utf-8"))
C = {n: k for k, n in enumerate(B["_colonnes"])}
BAT = B["bati"]

# ---------------------------------------------------------------------------
# LES NOMS — du petit peuple, pas des maisons
# ---------------------------------------------------------------------------
# Un manant n'a pas de patronyme : il a un surnom, et ce surnom dit son métier,
# son défaut, ou d'où il vient. C'est ce qui rend une foule lisible : « Wat le
# Boiteux » se retient, « Wat Pyle » non.
H = ["Wat", "Hobb", "Jon", "Tom", "Dick", "Ben", "Pate", "Lem", "Rennifer", "Bryen",
     "Gendry", "Mott", "Hugh", "Hal", "Dobber", "Osmund", "Rafford", "Cutjack",
     "Alyn", "Hoster", "Robin", "Elder", "Gwayne", "Owen", "Barth", "Sam",
     "Kyle", "Podrick", "Torrhen", "Willem", "Denys", "Erryk", "Luthor", "Mern",
     "Ossy", "Perkin", "Quent", "Rolly", "Symon", "Tobho", "Ulf", "Vayon",
     "Warryn", "Yoren", "Addam", "Bertram", "Corliss", "Davos", "Emmon"]
F = ["Mya", "Bella", "Jeyne", "Talla", "Willa", "Elza", "Kyra", "Mariya", "Nella",
     "Osha", "Pia", "Ravella", "Senelle", "Tanda", "Ursula", "Vylla", "Wylla",
     "Alys", "Bessa", "Cass", "Dorcas", "Elenei", "Frenya", "Gilly", "Hela",
     "Ilyne", "Jonquil", "Kella", "Layna", "Mordane", "Nan", "Orla", "Perra",
     "Roslin", "Sarra", "Tyta", "Umma", "Violette", "Weasel", "Ysilla"]
# Le surnom s'accorde : « Kella le Muet » sonne faux et se voit tout de suite
# dans une liste de mille noms. Les deux listes partagent les surnoms neutres.
NEUTRES = ["aux Dents", "des Quais", "de la Gadoue", "sans Pouce", "aux Poings",
           "des Marches", "aux Corbeaux", "des Ruelles", "aux Chiens",
           "du Crochet", "de la Néra", "sans Feu"]
SURNOMS_H = ["le Boiteux", "le Muet", "le Gros", "le Borgne", "le Noir", "le Long",
             "le Chauve", "le Pieux", "le Vieux", "le Jeune", "le Rouge",
             "le Sournois", "le Fendu", "le Lent", "le Sourd", "le Puant",
             "le Doux", "le Trois-Doigts", "le Veuf"] + NEUTRES
SURNOMS_F = ["la Boiteuse", "la Rousse", "la Muette", "la Sèche", "la Borgne",
             "la Grasse", "la Guêpe", "la Noire", "la Longue", "la Pieuse",
             "la Vieille", "la Jeune", "la Rouge", "la Blonde", "la Criarde",
             "la Menue", "la Douce", "la Veuve", "la Sourde"] + NEUTRES

def slug(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    out = []
    for c in s.lower():
        out.append(c if c.isalnum() else "-")
    r = "".join(out)
    while "--" in r: r = r.replace("--", "-")
    return r.strip("-")

def nom(sexe):
    prenom = R.choice(H if sexe == "h" else F)
    # un sur deux porte un surnom : trop, et la ville sonne comme une farce
    if R.random() < 0.55:
        return prenom + " " + R.choice(SURNOMS_H if sexe == "h" else SURNOMS_F)
    return prenom

# ---------------------------------------------------------------------------
# LES POSTES — qui tient une maison de ce métier, et avec quels bras
# ---------------------------------------------------------------------------
# `rang` : maitre (celui à qui l'on parle), compagnon (qui sait faire), valet
# (des bras), famille (qui vit là sans y travailler).
# `n` : (min, max) — le max n'est atteint que par les grandes parcelles.
# `loge` : le maître habite au-dessus de la boutique. C'est la règle en ville ;
# les exceptions (entrepôt, grenier, corps de garde) sont écrites en clair.
# `deloge` : ce poste ne DORT PAS où il travaille. Tant que toute l'équipe
# logeait sous le toit du métier, la ville n'avait aucune navette : le portefaix
# dormait dans l'entrepôt, l'homme du guet dans son corps de garde, et deux
# cents rues restaient vides à l'aube. Un valet de ces métiers-là loge donc dans
# un logement du quartier — ou d'un quartier plus pauvre — et garde son lien à
# son lieu de travail par la colonne `travail`.
# `chance` : ce poste ne se tire PAS sur la taille de la parcelle, mais à la
# fréquence dite ici. Certaines parcelles ne mesurent rien du métier qu'on y
# fait — un puits est une margelle de quelques pas qui dessert mille âmes —, si
# bien qu'un poste tiré sur leur plancher ne sort jamais, et le rôle reste
# déclaré sans qu'un seul corps le porte. On dit alors la chose en clair : une
# margelle sur trois a son porteur d'eau, et cela ne regarde pas ses murs.
def p(role, nom_role, sexe, rang, n=(1, 1), deloge=False, chance=None):
    return dict(role=role, nom=nom_role, sexe=sexe, rang=rang, n=n,
                deloge=deloge, chance=chance)

MAISONNEE = [  # ce qui s'ajoute quand `loge` : la famille du maître
    p("epouse", "Épouse", "f", "famille"),
    p("enfant", "Enfant", None, "famille", (0, 4)),
    p("aieul", "Aïeul", None, "famille", (0, 1)),
]

POSTES = {
 # --- LES INSTITUTIONS ------------------------------------------------------
 # Cinq lieux que le graphe nommait et que personne n'habitait. Les chiffres
 # sont ceux du canon de 129 AC, pas des ordres de grandeur choisis à l'œil.
 #
 # Le Guet de Port-Réal, ce sont DEUX MILLE manteaux d'or : six casernes en
 # portent les quatre cinquièmes, les quatorze corps de garde des portes le
 # reste. Ce sont des hommes de rien qui logent en ville et prennent leur tour
 # — d'où le `deloge` sur le simple guet, et pas sur le sergent qui couche à la
 # caserne.
 "caserne":            (False, [p("capitaine-guet", "Capitaine du Guet", "h", "maitre"),
                                p("sergent", "Sergent du guet", "h", "compagnon", (4, 6)),
                                p("guet", "Homme du guet", "h", "valet", (236, 248), deloge=True)]),
 # Soixante-dix-sept veilleurs de dragons en canon : un premier gardien et ses
 # soixante-seize. Autour d'eux, ce qu'il faut pour nourrir des bêtes de dix
 # tonnes — des valets et des bouchers d'appoint.
 "fosse-dragons":      (False, [p("premier-gardien", "Premier gardien des dragons", "h", "maitre"),
                                p("gardien-dragons", "Gardien des dragons", "h", "compagnon", (76, 76)),
                                p("valet-fosse", "Valet de la Fosse", "h", "valet", (14, 22)),
                                p("boucher-dragons", "Boucher des dragons", "h", "valet", (6, 10))]),
 # Le Donjon Rouge : neuf corps de logis, et dans chacun ce qui fait tourner une
 # forteresse — la garnison, les offices, la domesticité.
 "donjon-rouge":       (False, [p("officier-donjon", "Officier du Donjon", "h", "maitre"),
                                p("clerc-royal", "Clerc du roi", "h", "compagnon", (1, 3)),
                                p("intendant-royal", "Intendant royal", "h", "compagnon", (0, 1)),
                                p("garde-donjon", "Garde du Donjon", "h", "valet", (14, 22)),
                                p("domestique", "Domestique du Donjon", None, "valet", (10, 18))]),
 # Le grand septuaire de la ville en 129 AC : on y chante sept fois le jour, et
 # il faut du monde pour ça.
 "vieux-septuaire":    (False, [p("septon-superieur", "Septon supérieur", "h", "maitre"),
                                p("septon", "Septon", "h", "compagnon", (6, 10)),
                                p("septa", "Septa", "f", "compagnon", (8, 14)),
                                p("novice", "Novice", None, "valet", (20, 34)),
                                p("bedeau", "Bedeau", "h", "valet", (4, 8))]),
 # Les sages et leurs apprentis : quelques dizaines, pas davantage — la Guilde
 # est une confrérie moribonde en 129 AC, et c'est ce qui la rend dangereuse.
 "guilde-alchimistes": (False, [p("sage-alchimiste", "Sage de la Guilde", "h", "maitre"),
                                p("alchimiste", "Alchimiste", "h", "compagnon", (4, 8)),
                                p("apprenti-alchimiste", "Apprenti alchimiste", "h", "valet", (6, 12))]),
 # Rien n'est déchargé sur les quais sans que ce bureau le compte et le taxe.
 "bureau-port":        (False, [p("maitre-port", "Maître de port", "h", "maitre"),
                                p("clerc-port", "Clerc du port", "h", "compagnon", (2, 4)),
                                p("garde-douane", "Garde de la douane", "h", "valet", (4, 8))]),

 # --- le culte et le civique ------------------------------------------------
 # Le puits est le flux dominant de la ville — deux ou trois allers par foyer et
 # par jour — mais personne n'y habite : une margelle, une chaîne, et parfois un
 # porteur d'eau qui monte les seaux à ceux qui paient.
 # Il ne dort pas dans le puits : il loge en ville et vient tirer au seau.
 "puits":              (False, [p("porteur-eau", "Porteur d'eau", None, "valet", (0, 1),
                                  deloge=True, chance=0.35)]),
 "septuaire-quartier": (False, [p("septon", "Septon", "h", "maitre"),
                                p("septa", "Septa", "f", "compagnon", (0, 2)),
                                p("bedeau", "Bedeau", "h", "valet", (1, 2))]),
 "grenier":            (False, [p("grenetier", "Grenetier", "h", "maitre"),
                                p("compteur", "Compteur de muids", "h", "compagnon"),
                                p("portefaix", "Portefaix", "h", "valet", (2, 6))]),
 "corps-de-garde":     (False, [p("sergent", "Sergent du guet", "h", "maitre"),
                                p("guet", "Homme du guet", "h", "valet", (38, 48), deloge=True)]),
 "geole":              (False, [p("geolier", "Geôlier", "h", "maitre"),
                                p("porte-clefs", "Porte-clefs", "h", "valet", (2, 4))]),
 "auberge":            (True,  [p("aubergiste", "Aubergiste", None, "maitre"),
                                p("servante", "Servante", "f", "valet", (1, 4)),
                                p("marmiton", "Marmiton", "h", "valet", (1, 2)),
                                p("palefrenier", "Palefrenier", "h", "valet", (0, 2))]),
 "ecurie":             (True,  [p("loueur", "Loueur de chevaux", "h", "maitre"),
                                p("palefrenier", "Palefrenier", "h", "valet", (2, 5))]),

 # --- ce qui pue ------------------------------------------------------------
 "tannerie":           (True,  [p("tanneur", "Tanneur", "h", "maitre"),
                                p("apprenti-tanneur", "Apprenti tanneur", "h", "compagnon", (1, 3)),
                                p("ecarnisseur", "Écharneur", "h", "valet", (1, 3))]),
 "abattoir":           (True,  [p("boucher", "Boucher", "h", "maitre"),
                                p("saigneur", "Saigneur", "h", "valet", (2, 5), deloge=True)]),
 # Le bout de la chaîne du déchet : ce qui sort des foyers finit ici, en aval et
 # sous le vent, avec les tanneries pour voisines.
 "fosse-vidange":      (False, [p("vidangeur", "Vidangeur", "h", "maitre"),
                                p("aide-vidangeur", "Aide-vidangeur", "h", "valet", (2, 5))]),
 "teinturerie":        (True,  [p("teinturier", "Teinturier", None, "maitre"),
                                p("apprenti-teinturier", "Apprenti teinturier", None, "compagnon", (1, 3))]),
 "poterie":            (True,  [p("potier", "Potier", "h", "maitre"),
                                p("tourneur", "Tourneur", "h", "compagnon", (1, 2)),
                                p("enfourneur", "Enfourneur", "h", "valet", (1, 2))]),

 # --- le port ---------------------------------------------------------------
 "entrepot":           (False, [p("facteur", "Facteur de marchand", "h", "maitre"),
                                p("gardien", "Gardien d'entrepôt", "h", "valet", (1, 2), deloge=True),
                                p("portefaix", "Portefaix", "h", "valet", (2, 8), deloge=True)]),
 "corderie":           (True,  [p("cordier", "Cordier", "h", "maitre"),
                                p("fileur", "Fileur de chanvre", None, "valet", (2, 6), deloge=True)]),
 "voilerie":           (True,  [p("voilier", "Maître voilier", "h", "maitre"),
                                p("couseuse", "Couseuse de voiles", "f", "compagnon", (2, 6))]),
 "bordel":             (False, [p("matrone", "Matrone", "f", "maitre"),
                                p("fille", "Fille de joie", "f", "compagnon", (3, 9)),
                                p("videur", "Videur", "h", "valet", (1, 2))]),

 # --- le feu ----------------------------------------------------------------
 "forge":              (True,  [p("forgeron", "Forgeron", "h", "maitre"),
                                p("compagnon", "Compagnon forgeron", "h", "compagnon", (0, 2)),
                                p("souffleur", "Souffleur de soufflet", "h", "valet", (1, 2))]),
 "boulangerie":        (True,  [p("boulanger", "Boulanger", None, "maitre"),
                                p("mitron", "Mitron", "h", "valet", (1, 3))]),
 "brasserie":          (True,  [p("brasseur", "Brasseur", "h", "maitre"),
                                p("brassier", "Aide-brasseur", "h", "valet", (1, 4))]),
 # Le maillon qui manquait entre le grain et les neuf cent soixante fournils.
 "moulin":             (True,  [p("meunier", "Meunier", "h", "maitre"),
                                p("aide-meunier", "Aide-meunier", "h", "valet", (1, 2))]),
 # Le deuxième tonnage de la ville : tout ce qui chauffe et tout ce qui cuit en
 # brûle, et rien de tout cela n'entrait nulle part jusqu'ici.
 "chantier-bois":      (False, [p("marchand-bois", "Marchand de bois", "h", "maitre"),
                                p("charbonnier", "Charbonnier", "h", "compagnon", (1, 2)),
                                p("fendeur", "Fendeur de bûches", "h", "valet", (2, 5))]),

 # --- le commerce -----------------------------------------------------------
 "taverne":            (True,  [p("tavernier", "Tavernier", None, "maitre"),
                                p("servante", "Servante", "f", "valet", (1, 3)),
                                p("garcon", "Garçon de salle", "h", "valet", (0, 2))]),
 # Un marché secondaire par vingt-huit mille âmes : ce qui met un achat à moins
 # d'un quart de lieue au lieu d'une lieue de marche.
 "marche-quartier":    (False, [p("clerc-halle", "Clerc de halle", "h", "maitre"),
                                p("etalier", "Étalier", None, "compagnon", (6, 14)),
                                p("balayeur", "Balayeur", None, "valet", (1, 3))]),
 "echoppe":            (True,  [p("marchand", "Marchand", None, "maitre"),
                                p("commis", "Commis", None, "valet", (0, 2))]),
 "change":             (True,  [p("changeur", "Changeur", "h", "maitre"),
                                p("clerc", "Clerc de change", "h", "compagnon", (1, 2)),
                                p("garde-coffre", "Garde de coffre", "h", "valet", (1, 2))]),
 "etuve":              (True,  [p("etuviste", "Étuviste", None, "maitre"),
                                p("frotteur", "Frotteur", None, "valet", (1, 3))]),

 # --- l'habitat : on n'y travaille pas, on y vit --------------------------
 "manse":              (True,  [p("maitre-maison", "Maître de maison", "h", "maitre"),
                                p("intendant", "Intendant", "h", "compagnon", (0, 1)),
                                p("servante", "Servante", "f", "valet", (1, 4)),
                                p("garde-maison", "Garde de maison", "h", "valet", (0, 2))]),
 "maison-officier":    (True,  [p("maitre-maison", "Maître de maison", "h", "maitre"),
                                p("servante", "Servante", "f", "valet", (0, 2))]),
 "taudis":             (True,  [p("chef-de-feu", "Chef de feu", None, "maitre"),
                                p("logeur", "Locataire", None, "famille", (0, 3))]),
 "cabane":             (True,  [p("chef-de-feu", "Chef de feu", None, "maitre")]),
 "maison":             (True,  [p("chef-de-feu", "Chef de feu", None, "maitre"),
                                p("servante", "Servante", "f", "valet", (0, 1))]),
}

# le métier d'un maître donne son âge : on n'est pas maître voilier à dix-huit
# ans, et l'on n'est plus fille de joie à cinquante.
AGES = {"maitre": (28, 58), "compagnon": (18, 45), "valet": (14, 40),
        "famille": (0, 0)}   # la famille est traitée à part


# ---------------------------------------------------------------------------
# LE COMPTE — combien d'âmes ce bâtiment doit porter
# ---------------------------------------------------------------------------
# Port-Réal compte quatre cent mille âmes, et ce chiffre ne se décrète pas : il
# se DÉDUIT du plancher, comme dans usages.py, où la même table sert déjà à
# doser les métiers. Dix millions de mètres carrés de plancher, vingt-six au
# fond par âme, et le compte tombe tout seul.
#
# La conséquence : un bâtiment n'abrite pas UN ménage, il en abrite autant que
# ses planchers. Le taudis de quatre étages du Culpucier loge onze mètres
# carrés par tête — six ou sept foyers empilés dans la même cage d'escalier,
# et c'est précisément ce qui fait le Culpucier. La manse de la ville haute en
# loge un seul, sur cinq cents mètres carrés, et c'est ce qui fait la ville
# haute. Le même mécanisme dit les deux.
DENSITE = {"Le Culpucier": 11.0, "La ville": 24.0, "La ville haute": 70.0,
           "Le Crochet": 45.0, "La rue d'Acier": 28.0, "Les tanneries": 30.0,
           "Le port et ses hangars": 200.0}

# La CIBLE est le seul chiffre qu'on décrète, parce que c'est celui du canon :
# Port-Réal, quatre cent mille âmes. La table ci-dessus ne dit alors plus une
# densité absolue mais un RAPPORT entre quartiers — le Culpucier six fois plus
# serré que la ville haute —, et l'on met tout à l'échelle d'un facteur pour
# tomber sur le compte. C'est ce qui rend le peuplement solide quand le bâti
# change : engendrer mille maisons de plus ne fait pas mille habitants de plus,
# ça resserre la densité de tout le monde d'un cheveu.
CIBLE = 400000

# ---------------------------------------------------------------------------
# PEYREDRAGON — le bourg sous les murs
# ---------------------------------------------------------------------------
# Ce n'est pas une petite Port-Réal : c'est un village de pêche adossé à une
# forteresse. Pas de marché, pas de guilde, pas de rue d'Acier — on y vit du
# poisson, du sel et de ce que le château commande. Les métiers ci-dessous sont
# ceux que `peyredragon_usages.py` pose sur le bâti, et pas un de plus.
#
# Le CHÂTEAU n'est pas peuplé ici : ses volumes ne sont pas des feux du bourg,
# ils viennent des salles du plan (`materialisation/lieux.py`) et n'ont pas de
# colonne `usage` habitable. La garnison et la maison de la reine se tiennent
# dans `etat/personnages.json`, où elles sont nommées — un corps physique
# anonyme n'y apprendrait rien à personne.
POSTES_PEYREDRAGON = {
 "maison-pecheur":  (True,  [p("pecheur", "Pêcheur", "h", "maitre"),
                             p("mousse", "Mousse", "h", "valet", (0, 2))]),
 "sechoir":         (False, [p("secheur", "Sécheur de morue", None, "valet", (1, 3), deloge=True)]),
 "hangar":          (False, [p("gardien", "Gardien d'entrepôt", "h", "valet", (1, 2), deloge=True)]),
 "boucanerie":      (True,  [p("boucanier", "Boucanier", None, "maitre"),
                             p("ecarnisseur", "Écharneur", None, "valet", (1, 2))]),
 "saline":          (False, [p("saunier", "Saunier", None, "compagnon", (1, 3), deloge=True)]),
 "entrepot":        (False, [p("gardien", "Gardien d'entrepôt", "h", "valet", (1, 2), deloge=True)]),
 "echoppe":         (True,  [p("marchand", "Marchand", None, "maitre"),
                             p("commis", "Commis", None, "valet", (0, 1))]),
 "taverne":         (True,  [p("tavernier", "Tavernier", None, "maitre"),
                             p("garcon", "Garçon de salle", None, "valet", (1, 2))]),
 "auberge":         (True,  [p("aubergiste", "Aubergiste", None, "maitre"),
                             p("servante", "Servante", "f", "valet", (1, 3))]),
 "tannerie":        (True,  [p("tanneur", "Tanneur", "h", "maitre"),
                             p("apprenti-tanneur", "Apprenti tanneur", "h", "valet", (1, 2))]),
 "boulangerie":     (True,  [p("boulanger", "Boulanger", None, "maitre"),
                             p("mitron", "Mitron", None, "valet", (1, 2))]),
 "corderie":        (True,  [p("cordier", "Cordier", "h", "maitre"),
                             p("fileur", "Fileur de chanvre", None, "valet", (1, 2))]),
 "brasserie":       (True,  [p("brasseur", "Brasseur", None, "maitre"),
                             p("brassier", "Aide-brasseur", None, "valet", (1, 2))]),
 "voilerie":        (True,  [p("voilier", "Maître voilier", "h", "maitre"),
                             p("couseuse", "Couseuse de voiles", "f", "compagnon", (1, 3))]),
 "forge-bourg":     (True,  [p("forgeron", "Forgeron", "h", "maitre"),
                             p("souffleur", "Souffleur de soufflet", None, "valet", (0, 1))]),
 "septuaire-bourg": (True,  [p("septon", "Septon", "h", "maitre"),
                             p("novice", "Novice", None, "valet", (0, 1))]),
 # Le corps de garde du bourg tient le pied du grand escalier : ce sont des
 # hommes de la garnison qui prennent leur tour, pas des habitants. Ils dorment
 # au château — donc `deloge`, et leur logement se prend dans le bourg faute de
 # mieux, ce qui est déjà la règle ailleurs.
 "corps-de-garde":  (False, [p("sergent", "Sergent de la garnison", "h", "compagnon"),
                             p("garde-donjon", "Garde de Peyredragon", "h", "valet", (6, 10), deloge=True)]),
}

# --- LE CHÂTEAU ------------------------------------------------------------
# Les salles du château ne sont pas des feux du bourg : leurs volumes sont posés
# par `peyredragon_chateau.py`, qui les tire du plan. Leurs effectifs sont FERMES
# (min = max) et c'est voulu — on n'a pas cent hommes parce que la caserne est
# grande, on a une caserne parce qu'on a décidé cent hommes. Une garnison se
# décrète ; elle ne se déduit pas d'un plancher.
#
# Chaque poste que tient un personnage nommé de `etat/personnages.json` n'a
# qu'une seule place : c'est là que `scripts/corps.py` accroche la fiche, et
# c'est ce qui empêche d'avoir deux mestres à Peyredragon.
def f(role, nom_role, sexe, rang, n, deloge=False):
    """Un poste à effectif ferme."""
    return p(role, nom_role, sexe, rang, (n, n), deloge=deloge)

POSTES_CHATEAU = {
 "chateau-baraques":     (False, [f("capitaine-garde", "Capitaine de la garde", "h", "maitre", 1),
                                  f("sergent-garnison", "Sergent de la garnison", "h", "compagnon", 8),
                                  f("homme-armes", "Homme d'armes", "h", "valet", 96)]),
 "chateau-porte":        (False, [f("sergent-garnison", "Sergent de la garnison", "h", "compagnon", 1),
                                  f("homme-armes", "Homme d'armes", "h", "valet", 5)]),
 "chateau-guet":         (False, [f("veilleur", "Veilleur", "h", "valet", 8)]),
 "chateau-tour":         (False, [f("veilleur", "Veilleur", "h", "valet", 3)]),
 "chateau-communs":      (False, [f("castellan", "Castellan", "h", "maitre", 1),
                                  f("intendant-chateau", "Intendant du château", None, "compagnon", 1),
                                  f("servante", "Servante", "f", "valet", 10),
                                  f("valet-chateau", "Valet du château", "h", "valet", 6),
                                  f("blanchisseuse", "Blanchisseuse", "f", "valet", 4)]),
 "chateau-cuisines":     (False, [f("maitre-queux", "Maître queux", None, "maitre", 1),
                                  f("cuisinier", "Cuisinier", None, "compagnon", 3),
                                  f("marmiton", "Marmiton", None, "valet", 6),
                                  f("tournebroche", "Tournebroche", None, "valet", 2)]),
 "chateau-grande-salle": (False, [f("senechal", "Sénéchal", "h", "maitre", 1),
                                  f("echanson", "Échanson", None, "valet", 2)]),
 "chateau-antichambre":  (False, [f("huissier", "Huissier", "h", "compagnon", 1)]),
 "chateau-appartements": (False, [f("femme-chambre", "Femme de chambre", "f", "valet", 4)]),
 "chateau-enfants":      (False, [f("nourrice", "Nourrice", "f", "compagnon", 1),
                                  f("berceuse", "Berceuse", "f", "valet", 2)]),
 "chateau-hotes":        (False, [f("valet-chateau", "Valet du château", "h", "valet", 3)]),
 "chateau-roukerie":     (False, [f("mestre", "Mestre", "h", "maitre", 1),
                                  f("corbier", "Corbier", None, "valet", 2)]),
 "chateau-septuaire":    (False, [f("septa", "Septa", "f", "maitre", 1),
                                  f("novice", "Novice", None, "valet", 1)]),
 "chateau-forge":        (False, [f("forgeron-armes", "Forgeron d'armes", "h", "maitre", 1),
                                  f("apprenti-forge", "Apprenti forgeron", "h", "valet", 2)]),
 "chateau-officine":     (False, [f("apothicaire", "Apothicaire", None, "maitre", 1),
                                  f("aide-officine", "Aide d'officine", None, "valet", 1)]),
 "chateau-archives":     (False, [f("clerc-archives", "Clerc de l'archive", None, "compagnon", 1)]),
 "chateau-cellier":      (False, [f("bouteiller", "Bouteiller", "h", "maitre", 1),
                                  f("valet-cellier", "Valet de cellier", None, "valet", 2)]),
 "chateau-froide":       (False, [f("garde-manger", "Garde-manger", None, "compagnon", 1)]),
 "chateau-etuves":       (False, [f("chauffeur-etuves", "Chauffeur d'étuves", None, "valet", 2)]),
 "chateau-cachots":      (False, [f("geolier", "Geôlier", "h", "maitre", 1),
                                  f("porte-clefs", "Porte-clefs", "h", "valet", 2)]),
 "chateau-fosses":       (False, [f("premier-gardien", "Premier gardien des dragons", "h", "maitre", 1),
                                  f("gardien-dragons", "Gardien des dragons", "h", "compagnon", 8),
                                  f("valet-fosse", "Valet des fosses", None, "valet", 4)]),
}

if LIEU == "peyredragon":
    POSTES = dict(POSTES_PEYREDRAGON)
    POSTES.update(POSTES_CHATEAU)
    # Un seul quartier habité par des feux, et une densité de village : on tient
    # plus au large sous les murs qu'au Culpucier, et beaucoup moins au large
    # qu'en ville haute. Le château n'a pas de densité : ses effectifs sont
    # fermes, et le nombre d'âmes qu'il porte ne dépend d'aucun plancher.
    DENSITE = {"Le bourg sous les murs": 22.0}
    # Le bourg de Peyredragon, quelques centaines d'âmes. Il n'y a pas de
    # chiffre canon : celui-ci sort du bâti — vingt-six feux de pêcheurs et une
    # quarantaine d'ateliers ne nourrissent pas une ville.
    CIBLE = 600

def plancher(b):
    return b[C["facade_m"]] * b[C["profondeur_m"]] * max(1, b[C["etages"]])

# Les bâtiments à effectif FERME ne comptent pas dans ce calcul : leur peuple
# est décrété, pas déduit d'un plancher. Les laisser entrer ici reviendrait à
# faire maigrir le bourg de tout ce que pèse le château — six mille mètres de
# plancher de garnison contre quatre mille de village —, et le pêcheur paierait
# les tours de guet.
FERMES = set(POSTES_CHATEAU) if LIEU == "peyredragon" else set()
BRUT = sum(plancher(b) / DENSITE.get(b[C["quartier"]], 30.0)
           for b in BAT if b[C["usage"]] not in FERMES)
FACTEUR = CIBLE / BRUT if BRUT else 1.0

def ames(b, q, facteur):
    return max(1, int(round(plancher(b) / DENSITE.get(q, 30.0) * facteur)))


# ---------------------------------------------------------------------------
# LA TAILLE — grande ou petite POUR ICI, et pas pour Port-Réal
# ---------------------------------------------------------------------------
# Ce que la parcelle peut porter en bras ne se lit pas en mètres carrés : il se
# lit en RANG. Une échelle absolue — soixante mètres carrés valent zéro, sept
# cent soixante valent un — est vraie d'une capitale et fausse partout ailleurs :
# à Peyredragon, où la plus grande maison du bourg fait cent quarante-sept
# mètres carrés, elle collait TOUT le bâti contre le zéro. Conséquence visible
# et absurde : chaque poste dont le minimum est zéro — l'aïeul, le mousse, le
# novice, le souffleur, le commis — ne sortait jamais, et l'on obtenait un
# village de six cents âmes sans un seul grand-parent.
#
# On prend donc les bornes DANS LE BÂTI DU LIEU, aux quantiles ci-dessous : le
# petit fond de parcelle du lieu vaut zéro, la grande maison du lieu vaut un, et
# le reste s'interpole. Une petite parcelle de Peyredragon est petite pour
# Peyredragon.
#
# Les deux quantiles ne sont pas choisis au hasard : ce sont exactement ceux où
# tombaient les anciennes constantes dans le bâti de Port-Réal (60 m² ≈ le
# deuxième centile, 760 m² ≈ le quatre-vingt-dix-neuvième). La capitale garde
# donc la répartition qu'elle avait, et c'est le reste du royaume qui cesse
# d'être mesuré à son aune.
Q_PETIT, Q_GRAND = 0.02, 0.99

# Sur le bâti DÉDUIT seulement. Une grande salle de six cent soixante mètres et
# des fosses à dragons de seize cents tirent le quantile haut si loin que toutes
# les maisons du bourg redeviennent « petites » — et le village reperd ses
# aïeuls le jour où l'on peuple le château. Ce qui se mesure ici, c'est l'écart
# entre les parcelles dont l'effectif dépend de leur taille ; les autres n'ont
# rien à y faire.
_PLANCHERS = sorted(plancher(b) for b in BAT if b[C["usage"]] not in FERMES)

def _quantile(f):
    k = int(round(f * (len(_PLANCHERS) - 1)))
    return _PLANCHERS[max(0, min(len(_PLANCHERS) - 1, k))]

PETIT, GRAND = _quantile(Q_PETIT), _quantile(Q_GRAND)
# Un hameau de dix cabanes toutes pareilles n'aurait plus d'écart du tout : on
# garde un mètre carré de marge pour ne pas diviser par zéro, et tout le monde y
# est alors « petit », ce qui est la vérité.
if GRAND - PETIT < 1.0:
    GRAND = PETIT + 1.0


def taille(b):
    """Ce que la parcelle peut porter en bras, entre 0 et 1."""
    return max(0.0, min(1.0, (plancher(b) - PETIT) / (GRAND - PETIT)))


def combien(n, t, chance=None):
    lo, hi = n
    if hi <= lo: return lo
    if chance is not None:
        # la parcelle ne dit rien de ce poste : c'est la fréquence qui tranche.
        return hi if R.random() < chance else lo
    # la taille tire vers le haut, le hasard froisse : deux tavernes de même
    # gabarit n'ont pas le même nombre de bras.
    v = lo + (hi - lo) * (0.35 * t + 0.65 * R.random() * (0.4 + t))
    return max(lo, min(hi, int(round(v))))


# ---------------------------------------------------------------------------
# LE PLACEMENT — dans la parcelle, et à l'étage
# ---------------------------------------------------------------------------
# Le bâtiment donne son centre (x, y), son sol (z), son cap et son emprise.
# On sème les corps dans le rectangle, orienté par le cap : deux habitants ne
# sont pas au même point, et l'on peut donc désigner « celui du fond ».
# L'étage suit le rang : on travaille en bas, on dort en haut.
ETAGE_M = 2.9

def place(b, rang):
    cap = b[C["cap"]]
    fa, pr = b[C["facade_m"]], b[C["profondeur_m"]]
    u = (R.random() - 0.5) * fa * 0.70
    v = (R.random() - 0.5) * pr * 0.70
    cs, sn = math.cos(cap), math.sin(cap)
    x = b[C["x"]] + u * cs - v * sn
    y = b[C["y"]] + u * sn + v * cs
    et = max(1, b[C["etages"]])
    if rang in ("famille",):
        n = R.randint(min(1, et - 1), et - 1) if et > 1 else 0
    elif rang == "maitre":
        n = 1 if et > 1 and R.random() < 0.6 else 0
    else:
        n = 0 if et == 1 else R.randint(0, et - 1)
    z = b[C["z"]] + n * ETAGE_M + 0.9
    return round(x, 1), round(y, 1), round(z, 1), n


# ---------------------------------------------------------------------------
# ON PEUPLE
# ---------------------------------------------------------------------------
print("… on peuple %d bâtiments" % len(BAT))
# `travail` est l'index du bâtiment où le corps TRAVAILLE ; `bat` reste celui où
# il dort. Les deux sont égaux pour l'écrasante majorité — on travaille chez soi
# en ville —, et c'est justement pour que l'exception se voie qu'on la nomme.
COLONNES = ["id", "nom", "role", "rang", "sexe", "age", "usage", "bat",
            "quartier", "x", "y", "z", "etage", "travail"]
GENS = []
vus = Counter()
par_role = Counter()
sans_postes = Counter()

def ident(n, role):
    """Un id dérivé du nom et du rôle — lisible, stable, unique."""
    base = "%s-%s" % (slug(n), slug(role))
    vus[base] += 1
    k = vus[base]
    return base if k == 1 else "%s-%d" % (base, k)

# --- où loge celui qui ne dort pas à son travail ---------------------------
# On ne loge pas un portefaix dans une manse noble : le pauvre prend ce qui
# reste. Deux fois sur trois il habite le quartier de son travail, une fois sur
# trois un quartier franchement plus pauvre — c'est le loyer qui décide, pas
# l'envie, et c'est ce qui remplit le Culpucier d'hommes qui vont ailleurs.
LOGEABLE = ("taudis", "cabane", "maison", "maison-officier")
TAUDIS = ("taudis", "cabane")
if LIEU == "peyredragon":
    # Le bourg n'a qu'un toit habitable : la maison de pêcheur. Elle sert donc
    # aussi de logement au sécheur et au garde qui n'y travaillent pas — on se
    # serre, faute d'autre chose sous les murs.
    LOGEABLE = ("maison-pecheur",)
    TAUDIS = ("maison-pecheur",)
LOGEMENTS = defaultdict(list)
PAUVRES = []
for _i, _b in enumerate(BAT):
    _u = _b[C["usage"]]
    if _u in LOGEABLE:
        LOGEMENTS[_b[C["quartier"]]].append(_i)
        if _u in TAUDIS:
            PAUVRES.append(_i)

def logement(q):
    proches = LOGEMENTS.get(q)
    if PAUVRES and (not proches or R.random() < 0.35):
        return R.choice(PAUVRES)
    return R.choice(proches)

# Ce qui ne se sous-loue pas : on ne prend pas une chambre au Donjon Rouge, ni
# dans une caserne, ni au fond d'un puits.
SANS_LOCATAIRE = {"puits", "fosse-vidange", "marche-quartier", "chantier-bois",
                  "caserne", "fosse-dragons", "donjon-rouge", "vieux-septuaire",
                  "guilde-alchimistes", "bureau-port"}
if LIEU == "peyredragon":
    # On ne sous-loue ni le corps de garde, ni ce qui pue, ni ce qui n'a pas de
    # plancher : un séchoir à filets n'est pas un toit.
    SANS_LOCATAIRE = {"corps-de-garde", "sechoir", "saline", "boucanerie",
                      "tannerie", "hangar", "entrepot"} | set(POSTES_CHATEAU)

deloges = Counter()


def poser(b, i, usage, q, po, maitre_sexe, travail=None):
    """Un corps, à partir d'un poste. Rend le sexe du maître s'il vient d'être posé."""
    sexe = po["sexe"] or R.choice(("h", "f"))
    if po["rang"] == "maitre":
        maitre_sexe = sexe
    if po["role"] == "epouse":
        # « épouse » veut dire le conjoint du maître, pas une femme : un poste
        # tenu par une femme a un mari.
        if maitre_sexe is None: return maitre_sexe
        sexe = "h" if maitre_sexe == "f" else "f"
    if po["rang"] == "famille":
        age = R.randint(0, 16) if po["role"] == "enfant" else (
              R.randint(58, 78) if po["role"] == "aieul" else R.randint(20, 50))
    else:
        a0, a1 = AGES[po["rang"]]
        age = R.randint(a0, a1)
    nm = nom(sexe)
    role = po["role"] if po["role"] != "epouse" else ("epoux" if sexe == "h" else "epouse")
    x, y, z, et = place(b, po["rang"])
    if travail is None: travail = i
    GENS.append([ident(nm, role), nm, role, po["rang"], sexe, age,
                 usage, i, q, x, y, z, et, travail])
    par_role[role] += 1
    if travail != i: deloges[role] += 1
    return maitre_sexe


# Le foyer qui n'est pas celui du maître : les gens qui louent une chambre au
# troisième et n'ont rien à voir avec la boutique du bas. C'est par eux que la
# ville atteint son compte, et c'est la vérité d'une ville médiévale — un
# bâtiment n'abrite pas un ménage, il en abrite autant que ses planchers.
FOYER = [
    p("chef-de-feu", "Chef de feu", None, "maitre"),
    p("epouse", "Épouse", "f", "famille"),
    p("enfant", "Enfant", None, "famille", (0, 4)),
    p("aieul", "Aïeul", None, "famille", (0, 1)),
]

def tourner(facteur):
    """Un passage complet. Rend le nombre de corps posés."""
    del GENS[:]
    vus.clear(); par_role.clear(); sans_postes.clear(); deloges.clear()
    for i, b in enumerate(BAT):
        peupler_un(i, b, facteur)
    return len(GENS)


def peupler_un(i, b, facteur):
    usage = b[C["usage"]]
    conf = POSTES.get(usage)
    if conf is None:
        sans_postes[usage] += 1
        return
    loge, postes = conf
    t = taille(b)
    q = b[C["quartier"]]
    vise = ames(b, q, facteur)
    avant = len(GENS)

    # 1. le métier : qui tient la maison et avec quels bras
    liste = list(postes) + (MAISONNEE if loge else [])
    maitre_sexe = None
    for po in liste:
        for _ in range(combien(po["n"], t, po["chance"])):
            if po["deloge"]:
                # il travaille ici, il dort ailleurs : son corps est posé dans
                # son logement, et `travail` garde le fil jusqu'à son métier.
                j = logement(q)
                bj = BAT[j]
                poser(bj, j, usage, bj[C["quartier"]], po, None, travail=i)
            else:
                maitre_sexe = poser(b, i, usage, q, po, maitre_sexe)

    # 2. le compte : on loge des foyers de plus jusqu'à remplir le plancher.
    #    Si le métier déborde déjà le quota, on ne coupe rien — un corps de
    #    garde est ce qu'il est, et il n'a pas de locataires.
    # On s'arrête au foyer PRÈS, pas à l'âme près : un ménage ne se coupe pas
    # en deux. Le seuil est la moitié d'un foyer moyen — sans lui, chaque
    # bâtiment déborde d'un demi-ménage et la ville prend soixante-dix mille
    # âmes de trop.
    if usage in SANS_LOCATAIRE: return
    garde = 0
    while vise - (len(GENS) - avant) >= 2 and garde < 200:
        garde += 1
        ms = None
        for po in FOYER:
            for _ in range(combien(po["n"], t, po["chance"])):
                ms = poser(b, i, usage, q, po, ms)


# Deux passages, et c'est tout : le premier dit de combien on tombe à côté (les
# équipes de métier débordent leur quota dans les petites parcelles, l'arrondi
# au foyer rogne dans les autres), le second corrige le facteur d'autant. On
# atterrit à moins d'un pour cent de la cible sans jamais bricoler la table des
# densités — elle continue de ne dire que le rapport entre quartiers.
#
# La CIBLE ne compte que les âmes DÉDUITES : celles des effectifs fermes ne se
# corrigent pas, et les faire entrer dans l'asservissement reviendrait à rogner
# le bourg de tout ce que pèse la garnison — le pêcheur paierait les tours de
# guet une seconde fois.
KUSAGE = COLONNES.index("usage")

def deduits(_n):
    return sum(1 for g in GENS if g[KUSAGE] not in FERMES)

tourner(FACTEUR)
n1 = deduits(None)
print("   premier jet : %s âmes" % format(n1, ",d").replace(",", " "))
FACTEUR *= CIBLE / max(1, n1)
tourner(FACTEUR)

ROLES = {}
# `FOYER` en fait partie autant que les postes : le chef de feu est le rôle le
# plus nombreux de la ville, et il n'est dans AUCUNE table de postes ailleurs
# qu'au taudis. Tant qu'un seul lieu existait, il entrait par cette porte de
# côté ; un bourg sans taudis le faisait disparaître de la table des rôles
# alors qu'il en peuplait la moitié.
for usage, (loge, postes) in POSTES.items():
    for po in postes + (MAISONNEE if loge else []):
        ROLES.setdefault(po["role"], {"nom": po["nom"], "rang": po["rang"]})
for po in FOYER:
    ROLES.setdefault(po["role"], {"nom": po["nom"], "rang": po["rang"]})
ROLES.setdefault("epoux", {"nom": "Époux", "rang": "famille"})

# ---------------------------------------------------------------------------
# ON DÉCOUPE — un fichier par cellule, jamais un monolithe
# ---------------------------------------------------------------------------
# Quatre cent mille corps font cinquante mégaoctets, et un navigateur n'avale
# pas ça pour montrer une rue. La règle est la même que pour tout le reste du
# décor : on ne charge que ce qu'on regarde.
#
# La maille est de 250 m parce que c'est la portée de vue à hauteur d'homme :
# une caméra en tient neuf autour d'elle (750 m de côté), soit deux ou trois
# mégaoctets, et le reste de la ville n'existe pas tant qu'on n'y va pas.
#
# `portreal.gens.json` cesse d'être la donnée et devient le MANIFESTE : les
# colonnes, les rôles, la maille, et le compte de chaque cellule. C'est le seul
# fichier qu'on lit en entier, et il pèse quelques kilo-octets.
CELLULE_M = 250
# Port-Réal garde `monde/gens/` — c'est là que le serveur et `gens.js` sont
# allés le chercher depuis le début, et déplacer une donnée servie en direct
# pour faire joli ne vaut jamais la panne. Tout autre lieu prend son
# sous-dossier. Le manifeste porte le chemin dans `dossier` : c'est lui qui
# fait foi, pas la convention.
DOSSIER = os.path.join(MONDE, "gens") if PREFIXE == "portreal" \
    else os.path.join(MONDE, "gens", PREFIXE)
if os.path.isdir(DOSSIER):
    for f in os.listdir(DOSSIER):
        if f.endswith(".json") or f.endswith(".bin"):
            os.remove(os.path.join(DOSSIER, f))
else:
    os.makedirs(DOSSIER)

KX, KY = COLONNES.index("x"), COLONNES.index("y")
paniers = defaultdict(list)
for g in GENS:
    paniers[(int(g[KX] // CELLULE_M), int(g[KY] // CELLULE_M))].append(g)

# ---------------------------------------------------------------------------
# LE DOUBLE BINAIRE — ce dont le RENDU a besoin, et rien d'autre
# ---------------------------------------------------------------------------
# Le JSON reste la vérité du corps : c'est lui que le MJ interroge pour savoir
# qui tient la taverne. Mais dessiner une foule ne demande ni nom, ni id, ni
# quartier — seulement où poser la silhouette et laquelle poser. Transporter
# cent trente octets pour en utiliser huit est le seul obstacle sérieux avant
# d'animer quatre cent mille corps : d'où ce double, quarante fois plus léger.
#
# Structure de TABLEAUX (SoA), pas tableau de structures : le rendu lit une
# colonne entière d'un coup pour remplir un attribut d'instance, et une vue
# typée se pose alors directement sur le tampon, sans une seule recopie.
#
# L'ORDRE EST CELUI DU TABLEAU `gens` DU JSON DE LA MÊME CELLULE, à l'index
# près. C'est ce qui fait tenir les deux moitiés ensemble : l'instance n° 412
# qu'on vient de cliquer à l'écran est le 412e corps du JSON, et l'on retrouve
# son nom, son métier et son bâtiment sans index supplémentaire.
ROLES_INDEX = sorted(ROLES.keys())
ROLE_N = {r: k for k, r in enumerate(ROLES_INDEX)}
OCTETS_PAR_CORPS = 12
DISPOSITION = ("uint16 x[n], uint16 y[n], uint16 z[n], uint16 bat[n], "
               "uint16 travail[n], uint8 role[n], uint8 age_sexe[n] — x et y "
               "en cm relatifs à (x0, y0) de la cellule, z en cm absolus, bat "
               "et travail = index dans " + PREFIXE + ".bati.json, role = index dans "
               "roles_index, âge = bits 0-6, sexe femme = bit 7 ; "
               "little-endian, sans en-tête, même ordre que le tableau gens "
               "du JSON.")

KZ = COLONNES.index("z")
KROLE, KSEXE, KAGE = (COLONNES.index("role"), COLONNES.index("sexe"),
                      COLONNES.index("age"))
KBAT, KTRAV = COLONNES.index("bat"), COLONNES.index("travail")

def borne(v, hi):
    return 0 if v < 0 else (hi if v > hi else v)

def binaire(lot, x0, y0):
    """Le double dense d'une cellule, colonne par colonne."""
    n = len(lot)
    xs, ys, zs, bs, ts, rs, asx = [], [], [], [], [], [], []
    for g in lot:
        xs.append(borne(int(round((g[KX] - x0) * 100)), 65535))
        ys.append(borne(int(round((g[KY] - y0) * 100)), 65535))
        zs.append(borne(int(round(g[KZ] * 100)), 65535))
        # le domicile et le lieu de travail : sans eux, une silhouette ne sait
        # pas d'ou elle part et ne peut aller nulle part. 48 377 batiments
        # tiennent dans un uint16, on ne paie donc que deux octets chacun.
        bs.append(borne(int(g[KBAT]), 65535))
        ts.append(borne(int(g[KTRAV]), 65535))
        rs.append(ROLE_N.get(g[KROLE], 0))
        # l'âge tient dans sept bits parce que personne ne passe 127 ans ; le
        # huitième dit le sexe, et l'on gagne un octet par corps sur la ville.
        asx.append(borne(int(g[KAGE]), 127) | (128 if g[KSEXE] == "f" else 0))
    return (struct.pack("<%dH" % n, *xs) + struct.pack("<%dH" % n, *ys)
            + struct.pack("<%dH" % n, *zs) + struct.pack("<%dH" % n, *bs)
            + struct.pack("<%dH" % n, *ts) + struct.pack("<%dB" % n, *rs)
            + struct.pack("<%dB" % n, *asx))

cellules = {}
for (ci, cj), lot in sorted(paniers.items()):
    clef = "%d-%d" % (ci, cj)
    x0, y0 = ci * CELLULE_M, cj * CELLULE_M
    io.open(os.path.join(DOSSIER, clef + ".json"), "w", encoding="utf-8").write(
        json.dumps({"_colonnes": COLONNES, "cellule": [ci, cj], "gens": lot},
                   ensure_ascii=False, separators=(",", ":")))
    with open(os.path.join(DOSSIER, clef + ".bin"), "wb") as f:
        f.write(binaire(lot, x0, y0))
    cellules[clef] = {"n": len(lot), "x0": x0, "y0": y0}

SORTIE = {
    "_lisez_moi": (
        "MANIFESTE des corps physiques de Port-Réal. Un corps n'est pas un "
        "personnage : c'est un emplacement occupé, avec un nom, un rôle et une "
        "position en mètres (étage compris). Les corps eux-mêmes sont dans "
        "monde/gens/<i>-<j>.json, une maille de 250 m — on ne charge que les "
        "cellules qu'on regarde ; monde/gens/<i>-<j>.bin en est le double "
        "dense, pour le rendu seul (voir la clé binaire). Engendré par "
        "scripts/monde/peupler.py : CES "
        "FICHIERS SE RÉÉCRIVENT ENTIÈREMENT à chaque passage, n'y écrivez rien "
        "à la main. Les liens vers etat/personnages.json vivent dans "
        "etat/corps.json, tenus par scripts/corps.py."),
    "_type": "physicalactor",
    "_colonnes": COLONNES,
    "_roles": ROLES,
    "cellule_m": CELLULE_M,
    "dossier": os.path.relpath(DOSSIER, RACINE).replace(os.sep, "/"),
    # Le double dense, pour le rendu seul : même découpage, même ordre, huit
    # octets par corps au lieu de cent trente.
    "binaire": {
        "suffixe": ".bin",
        "octets_par_corps": OCTETS_PAR_CORPS,
        "echelle_cm": 100,
        "roles_index": ROLES_INDEX,
        "disposition": DISPOSITION,
    },
    "total": len(GENS),
    "cellules": cellules,
}
io.open(os.path.join(MONDE, PREFIXE + ".gens.json"), "w", encoding="utf-8").write(
    json.dumps(SORTIE, ensure_ascii=False, separators=(",", ":")))

# ---------------------------------------------------------------------------
print()
print("  %s corps posés dans %s bâtiments"
      % (format(len(GENS), ",d").replace(",", " "),
         format(len(BAT), ",d").replace(",", " ")))
par_q = Counter(g[COLONNES.index("quartier")] for g in GENS)
for q, n in par_q.most_common():
    print("   %-28s %7d" % (q, n))
print()
for r, n in par_role.most_common(12):
    print("   %-22s %7d" % (ROLES[r]["nom"], n))
if deloges:
    print()
    print("  %s corps dorment ailleurs qu'à leur travail (travail != bat) :"
          % format(sum(deloges.values()), ",d").replace(",", " "))
    for r, n in deloges.most_common():
        print("   %-22s %7d" % (ROLES[r]["nom"], n))
if sans_postes:
    print()
    print("  usages sans table de postes (personne n'y a été posé) :")
    for u, n in sans_postes.most_common():
        print("   %-22s %6d" % (u, n))
print()
print("  %d cellules de %d m dans %s/ — la plus peuplée en porte %d"
      % (len(cellules), CELLULE_M, SORTIE["dossier"],
         max(c["n"] for c in cellules.values())))
print("  -> monde/%s.gens.json (le manifeste)" % PREFIXE)
