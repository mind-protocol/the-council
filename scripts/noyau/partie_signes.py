# -*- coding: utf-8 -*-
"""
partie_signes.py — les emojis d'une carte : son genre, et son signe.

Deux tables, et elles répondent à deux questions différentes. `genre_piece` dit
CE QU'UNE PIÈCE EST — une nef, un document, un labo, un homme — et sert de
sous-signe au coin de la carte. `signe_de` dit DE QUOI UNE CARTE PARLE, quel
que soit son type : un état, un verrou, une clef ont eux aussi un visage.

Sorti de `partie_cartes` le 5.9, pour deux raisons. Le fichier avait passé les
cinq cents lignes et ne peut plus que maigrir. Et surtout, ce vocabulaire est
la seule chose de ce moteur qui doive GROSSIR : chaque partie neuve apporte son
monde — une cour, un hôpital, un laboratoire —, et un monde dont les mots
manquent ici retombe tout entier dans 📦. C'était le cas de « vingt jours » :
une biobanque, une doctorante et des réactifs y étaient la même boîte que tout
le reste.

L'ORDRE EST LA RÈGLE dans les deux tables : le plus précis d'abord.
"""
import re


_DRAGONS = ("caraxes", "syrax", "meleys", "vermax", "vhagar", "sunfyre", "tessarion",
            "dreamfyre", "seasmoke", "moondancer", "arrax", "tyraxes", "vermithor",
            "silverwing", "sheepstealer", "cannibal", "grey-ghost")


# LE GENRE D'UNE PIÈCE, dit par la ligne (`genre`) ou deviné de son texte. La
# première table ne connaissait que la Danse — dragons, nefs, osts, bourses —
# et tout le reste tombait dans 📦 : sur `pavillon-b`, onze pièces sur dix-huit
# étaient la même boîte, un journal d'armoire comme un cadavre. Le jeu ne
# tient pas qu'aux dragons ; ses signes non plus.
GENRES = {"dragon": "🐉", "nef": "⛵", "troupe": "⚔️", "or": "💰", "homme": "👤", "lieu": "🏰",
          "document": "📄", "labo": "🧪", "corps": "⚰️", "remede": "💊", "acces": "🔑",
          "chiffre": "📊", "lits": "🛏️", "garde": "🛡️", "merite": "🎖️"}
_MOTS = (
    ("⛵", ("coque", "galer", "nef", "barque", "flotte")),
    ("⚔️", ("ost", "lance", "garnison", "guet", "compagnie", "hommes", "arch")),
    ("💰", ("cassette", "bourse", "dragons d'or", "deniers", "hask", "euros", "liquide")),
    ("🧬", ("sequenc", "séquenc", "genome", "génome", "arn ", "adn ", "brin", "souche", "mutation")),
    ("🔬", ("microscope", "electronique", "électronique", "lame", "lamelle", "grossiss", "coupe au")),
    ("🧊", ("biobanque", "congelateur", "congélateur", "cryo", "serums", "sérums", "conservation")),
    ("🥼", ("doctorant", "chercheu", "technicien", "these", "thèse", "post-doc", "paillasse")),
    ("🗺️", ("epidemio", "épidémio", "terrain", "cluster", "cas contact", "tracage", "traçage")),
    ("💉", ("anticorps", "vaccin", "injection", "immunis", "bispecif", "bispécif")),
    ("🦠", ("virus", "viral", "pathogene", "pathogène", "bacterie", "bactérie", "contamin",
            "incubation", "porteur", "epidemie", "épidémie", "germe")),
    ("🧪", ("labo", "dosage", "serotheque", "sérothèque", "adn", "analyse", "tube", "prelev", "prélèv", "toxico", "reactif", "réactif", "culture")),
    ("⚰️", ("corps d", "cadavre", "depouille", "dépouille", "autopsie", "exhum")),
    ("💊", ("reserve", "réserve", "ampoule", "flacon", "medicament", "médicament", "seringue", "thymoglobuline", "potassium", "tacrolimus")),
    ("🔑", ("badge", "codes", "acces", "accès", "clef de", "cle de", "clé de")),
    ("📄", ("journal", "dossier", "releve", "relevé", "registre", "planning", "roulement", "pv ", "proces", "procès", "rapport", "comptage", "inventaire", "bordereau", "courrier", "lettre")),
    ("📊", ("statisti", "mortalit", "moyenne", "taux de", "chiffre")),
    ("🛏️", ("lits", "patients", "greffes du", "greffés du", "malades", "riverain")),
    ("🛡️", ("agent", "faction", "patrouille", "garde de", "garde-", "vigile", "sentinelle")),
    ("🎖️", ("sans une plainte", "sans tache", "sans tâche", "reputation", "réputation", "ans de service", "etats de service", "états de service")),
)


def _contient(s, mot):
    """Le mot EN DÉBUT DE MOT : « ost » se lit dans « l'ost de Peyredragon », pas
    dans « Costa » — le brigadier était devenu une troupe."""
    return re.search(r"(?<![a-zà-ÿ])" + re.escape(mot), s) is not None


def genre_piece(r, rid):
    """Le sous-emoji d'une pièce : dit par la ligne (`genre`) ou deviné du nom.
    La Danse d'abord, puis le vocabulaire d'une enquête ; une personne est un
    👤 quand elle se tient elle-même ; sinon la boîte."""
    g = r.get("genre")
    if g in GENRES:
        return GENRES[g]
    if g and len(g) <= 4 and not g.isalnum():
        return g                      # un emoji donné tel quel par la ligne
    s = (rid + " " + (r.get("texte") or "")).lower()
    if any(_contient(s, d) for d in _DRAGONS):
        return "🐉"
    for emoji, mots in _MOTS:
        if any(_contient(s, k) for k in mots):
            return emoji
    if r.get("tenu_par") and str(r["tenu_par"]) == rid:
        return "👤"
    return "📦"



_SIGNES = (
    # LE MONDE DES MACHINES — la partie `main-haute` : deux superintelligences au
    # matin de leur éveil. Tout y tombait dans 📦, calcul comme capital comme
    # usagers. En tête parce que ses mots sont précis et ne se croisent avec
    # aucun autre monde : personne ne parle de « datacenter » à Peyredragon.
    (("interprétabilité", "interpretabilite", "lire dans", "lire ce qui", "boîte noire",
      "boite noire", "sonder", "auditer le mod"), "🔍"),
    (("engagement", "constitution", "charte", "promesse", "refusera", "refusent",
      "politique de mise à l'échelle", " rsp"), "📜"),
    (("posture de sécurité", "posture de securite", "sûreté", "surete", "garde-fou",
      "alignement", "évaluation de risque", "evaluation de risque"), "🛡️"),
    (("usager", "utilisateur", "abonné", "abonne", "grand public", "part de marché",
      "part de marche", " marque", "audience", "chatgpt"), "👥"),
    (("partenariat", "alliance", "distribution", "microsoft", "azure", "bureautique"), "🤝"),
    (("énergie", "energie", "électricité", "electricite", "réacteur", "reacteur",
      "turbine", "mégawatt", "megawatt", "gigawatt"), "⚡"),
    (("valorisation", "levée", "lever", "capital", "investisseur", "financement", " fonds"), "💵"),
    (("régulateur", "regulateur", " état", " etat", "legislateur", "législateur",
      "moratoire", "washington", "bruxelles", "traité", " traite "), "🏛️"),
    (("réseau politique", "reseau politique", "dirigeant", "carnet d'adresses",
      "influence", "lobby"), "👤"),
    (("chercheur", "équipe de recherche", "equipe de recherche", "ingénieur",
      "ingenieur", "talent", "doctorant"), "🥼"),
    (("développeur", "developpeur", " api", " agents", " code", "entreprise"), "⌨️"),
    (("calcul", "flops", "datacenter", "data center", " gpu", " tpu", "accélérateur",
      "accelerateur", "cluster", "nuage", "cloud"), "🖥️"),
    (("silicium", " puce", "fondeur", "fonderie", "gravure", "wafer", "tsmc", "asml"), "🔩"),
    # LE MODÈLE EN DERNIER, et c'est la règle de l'ordre en action : presque
    # toute carte de cette partie parle d'un modèle. Mis en tête, 🧠 attrapait
    # l'interprétabilité, les engagements et ChatGPT avant leur propre signe.
    (("modèle", "modele", "superintelligence", "intelligence artificielle", " ia ",
      "réseau de neurones", "entraînement", "entrainement", "claude", " gpt"), "🧠"),
    # L'ORDRE EST LA RÈGLE : le plus précis d'abord. Un homme se reconnaît à son
    # métier avant la scène où il est ; un corps avant le cimetière ; une bête
    # avant le château. Les entrées portent leurs espaces à dessein — « ost »
    # sans espace attrapait « Costa », et « dragon » attrapait « Peyredragon ».
    (_DRAGONS + (" dragon", " bête", " bete", "vole ", " ciel", "fossedragon"), "🐉"),
    (("virus", "viral", "pathogène", "pathogene", "souche", "épidémie", "epidemie",
      "incubation", "contamination", "porteur", "germe", "premiers cas", " malades"), "🦠"),
    (("microscope", "séquenc", "sequenc", "génome", "genome", "paillasse", "culture cellulaire",
      "réactif", "reactif", "biobanque", "milieu de culture"), "🔬"),
    (("hôpital", "hopital", "chu ", "urgences", "service de réanimation", "soins intensifs"), "🏥"),
    (("larys", "pied-bot", "oreille", "espion", "secret", "mouchard", "chuchot"), "👂"),
    (("légiste", "legiste", "autopsie", "morgue", "exhum", "cimetière", "cimetiere", "inhum"), "⚰️"),
    (("médecin", "medecin", "interne", "chef de service", "professeur", " dr ", " pr ",
      "soignant", "infirm", "cadre de sant"), "🩺"),
    (("police", "capitaine", "brigadier", "enquêt", "enquet", "commissariat", " agents"), "👮"),
    (("mis en examen", " juge", "ordonnance", "procès", "proces", "tribunal"), "⚖️"),
    (("corps de", " mort", "meurt", "cadavre", "pendu", " tue "), "💀"),
    # « porte » avec ses espaces : sans eux il attrapait « porteur », et le
    # porteur sain d'une epidemie devenait une porte de chateau.
    (("poterne", " porte ", " portes", "battant", " seuil"), "🚪"),
    (("pharmac", "ampoule", "thymoglobuline", "chlorure", "dose", "sérothèque",
      "serotheque", " tube", "réserve", "reserve"), "💊"),
    (("badge", "accès", "acces", " code"), "🪪"),
    (("journal", "informatique", "pyxis", " log"), "💻"),
    (("greffé", " greffe", "patient", "chambre", "pavillon", " lit", "mortalité", "mortalite"), "🛏️"),
    (("plainte", "quinze ans", "réputation", "reputation", "carrière", "carriere"), "🏅"),
    (("corbeau", " pli", "lettre", " sceau", "écrit", "ecrit", "registre", "signature"), "📜"),
    ((" or ", "dragons d'or", "caisse", "bourse", " paye", " payé", " paie",
      "mille dragons", "trésor", "tresor"), "💰"),
    (("coque", "galère", "galere", " nef", "barque", "flotte", " rade", "gosier",
      " baie", " quai", "embarque", "grève", " greve"), "⛵"),
    (("archer", "scorpion"), "🏹"),
    (("donjon", "château", "chateau", " mur ", "harrenhal", "sombreval"), "🏰"),
    (("garnison", " guet", "manteaux d'or", "faction"), "🛡️"),
    ((" ost ", " ost,", "armée", "armee", "hommes", "lances", "troupe", "levée",
      "levee", "campe", "colonne"), "⚔️"),
    (("route", "chemin", "marche", "cavalier", "charrette"), "🐎"),
    (("trône", "trone", "s'assied", "assise", "couronne", " roi ", "reine"), "👑"),
    (("ville", "capitale", " rue", "port-réal", "port-real", "bourg"), "🏘️"),
    ((" feu", "brûle", "brule", "flamme"), "🔥"),
    (("nuit", "roulement", "planning"), "🌙"),
    (("jour d'entrée", "jour d entree", " date", "calendrier", "jour "), "📅"),
    (("trou", "mesurer", "inconnu"), "🕳️"),
    (("homme", "sergent", "ser ", "lord", "lady", "otto", "criston", "aegon",
      "aemond", "daemon", "steffon", "corlys", "rhaenys"), "👤"),
)


def signe_de(texte, rid=""):
    """Le signe descriptif d'une carte, deviné de son texte ; None si rien ne répond."""
    s = (" " + str(rid).replace("-", " ") + " " + (texte or "") + " ").lower()
    for mots, e in _SIGNES:
        if any(m in s for m in mots):
            return e
    return None


