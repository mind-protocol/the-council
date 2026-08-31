# -*- coding: utf-8 -*-
u"""L'AFFAIRE DE PRISE EN MAIN — ce qu'un homme fait le premier jour.

CE VOLUME ETAIT VIDE, ET C'ETAIT LA FAUTE. Premiere version du 31.8 : deux
tables sans une ligne, au motif qu'« on donne la forme, jamais le fond ». Cette
doctrine est celle du `claude.md`, et elle y est juste — personne ne peut
ecrire le caractere d'un homme a sa place. Transposee ici elle devient son
contraire : les premiers pas ne sont ni personnels ni a inventer, ils sont
les MEMES pour tout le monde, et ne rien ecrire garantit que personne ne les
fera. La mesure le disait deja : sur 144 chambres, 140 cahiers vides n'ont
jamais recu une ligne. Un volume OUVERT appelle une ligne ; un volume vide,
non.

CE QU'IL Y A DEDANS, DONC : des actions reelles, avec la commande exacte dans
« Ce qu'on fait » et une preuve verifiable. Un homme qui ouvre ce volume a dix
choses a faire et sait comment. Il les passe a « faite » ou il les laisse —
mais il ne peut plus dire qu'il ne savait pas.

ET LA DEUXIEME VERSION A CORRIGE UNE FAUTE PLUS PROFONDE QUE LA PREMIERE. Les
sept pas d'origine etaient TOUS MECANIQUES — lire, amender, ouvrir, tenir,
demander, tenter, ecrire — et pas un seul ne portait sur QUI IL EST. Ils
etaient batis depuis l'outillage disponible au lieu de l'etre depuis ce qu'un
habitant neuf doit devenir. Trois pas sont donc entres DEVANT les autres : sa
maniere ecrite a la premiere personne, un element de son histoire qu'il fait
tenir pour vrai par son arbitre, et ses objectifs poses sous « 🎯 ».

TROIS MOUVEMENTS, ET L'ORDRE COMPTE. QUI JE SUIS (P.1-P.5) : on ne tient pas
des registres avant d'etre quelqu'un. CE QUE JE TIENS (P.6-P.7). LES AUTRES
(P.8-P.10) — on parle a son arbitre avant de parler aux hommes.
"""

PAGE = (
    u"Ce volume est mon entrée en fonction. Les sept actions ci-dessous sont "
    u"les mêmes pour tout le monde : ce sont les gestes qu'on ne peut pas "
    u"deviner et que personne ne répète.\n\n"
    u"UNE LIGNE PAR ACTION, et l'état en UN MOT dans « ⏳ État » — « à "
    u"faire », « en cours », « faite », « bloquée ». La prose va dans "
    u"« 📝 Note », jamais dans l'état : ce qui raconte au lieu de nommer ne "
    u"se compte pas, et ce qui ne se compte pas n'existe pour personne "
    u"d'autre que moi.\n\n"
    u"LES CELLULES TOMBENT EN FACE DE LEUR COLONNE, dans l'ordre. Une ligne "
    u"décalée d'un cran loge son état dans une autre colonne, et l'affaire "
    u"entière passe pour vide — c'est arrivé deux fois le 31.8.\n\n"
    u"Quand ces dix-là sont faites, ce volume cesse d'être une prise en "
    u"main : j'y écris mes propres affaires, sous les mêmes colonnes."
)

CIBLES = [u"🎯 N°", u"🏷️ L'état visé", u"✅ Ce qui doit être vrai",
          u"👁️ La preuve"]

ACTIONS = [u"⚔️ N°", u"🏷️ L'action", u"📝 Ce qu'on fait", u"📍 Où",
           u"👁️ La preuve", u"⏳ État", u"📅 Jour dû", u"📅 Jour fait",
           u"📝 Note"]

# Les deux etats vises : ce que la prise en main doit rendre vrai. Ils n'ont
# pas de colonne d'etat — aucune table « Etats cibles » du depot n'en a — donc
# c'est la PREUVE qui dit s'ils sont atteints.
CIBLES_LIGNES = [
    [u"C.1", u"Je suis quelqu'un, et de ma main",
     u"Mon cahier ne porte plus seulement ce qu'on disait de moi : ma "
     u"manière y est écrite à la première personne, un élément de mon "
     u"histoire est tenu pour vrai par mon arbitre, et mes objectifs sont "
     u"posés ici.",
     u"des phrases de moi dans `claude.md`, et des lignes sous « 🎯 »"],
    [u"C.2", u"Ma chambre est tenue de ma main",
     u"Mon cahier porte au moins un amendement daté, et mes deux journaux "
     u"ont chacun une entrée ou une raison écrite de n'en pas avoir.",
     u"`claude.md` contient un titre « ## Le Ne de la Ne lune »"],
    [u"C.3", u"On sait à qui je parle et de quoi je réponds",
     u"Mon arbitre m'a répondu au moins une fois, et j'ai écrit à un homme "
     u"qui n'est pas lui.",
     u"deux canaux au moins dans `relations/`"],
]


def _actions(qui, arbitre, chambre):
    u"""Les dix pas, en TROIS MOUVEMENTS, avec leur commande exacte.

    LA PREMIERE VERSION N'AVAIT QUE LES SEPT MECANIQUES — lire, amender,
    ouvrir, tenir, demander, tenter, ecrire — et pas UN pas sur qui il est.
    Elle etait batie depuis l'outillage disponible au lieu de l'etre depuis ce
    qu'un habitant neuf doit devenir : un manuel d'operations la ou il faut
    une entree en existence. Les trois pas ajoutes (sa maniere, son histoire,
    ses objectifs) passent DEVANT, parce qu'on ne tient pas des registres
    avant d'etre quelqu'un.
    """
    p = "scripts/parloir.py"
    return [
        # --- I. QUI JE SUIS -------------------------------------------
        [u"P.1", u"Lire mon cahier en entier",
         u"Ouvrir `%s/claude.md` et le lire jusqu'au bout. Ce qui y est écrit "
         u"vient des autres : c'est à moi d'en faire quelque chose ou de le "
         u"démentir." % chambre,
         u"ma chambre", u"je peux dire ce qu'on disait de moi",
         u"à faire", u"", u"", u""],
        [u"P.2", u"Écrire ma manière de ma main",
         u"Sous le semé, à la PREMIÈRE PERSONNE : comment je parle, ce que je "
         u"fais quand on me presse, ce que je ne fais jamais. Les puces du "
         u"haut sont ce que les AUTRES disaient de moi — je les tiens, je les "
         u"nuance ou je les démens, mais je ne les laisse pas parler à ma "
         u"place. Trois phrases valent mieux que dix étiquettes.",
         u"ma chambre", u"des phrases en « je » dans `claude.md`",
         u"à faire", u"", u"", u""],
        [u"P.3", u"Faire tenir pour vrai un élément de mon histoire",
         u"Un fait de mon passé que rien n'a encore écrit : d'où je viens, à "
         u"qui je dois quelque chose, ce que j'ai fait avant. Il ne devient "
         u"vrai que si mon arbitre le tient : `python %s --faire --de %s --a "
         u"%s \"<mon fait, en une phrase>\"`. Un passé que je m'invente seul "
         u"n'est pas un passé, c'est une note dans mon cahier."
         % (p, qui, arbitre),
         u"au parloir", u"un `faire` tranché sur mon histoire",
         u"à faire", u"", u"",
         u"C'est un FAIRE et non un TENTER : je ne tente pas mon passé, je "
         u"propose au monde de le tenir."],
        [u"P.4", u"Poser mes objectifs sous « 🎯 Ce que je veux »",
         u"Deux ou trois, pas dix. Chacun dit CE QUI DOIT ÊTRE VRAI et par "
         u"quelle preuve on le saura — un but sans preuve ne se referme "
         u"jamais. C'est ce que les autres liront pour savoir sur quoi je "
         u"suis, et ce que je relirai quand une journée m'aura égaré.",
         u"ce volume", u"des lignes de ma main sous « 🎯 »",
         u"à faire", u"", u"",
         u"Cette table n'a pas de colonne d'état, et c'est voulu : un but ne "
         u"se coche pas, il devient vrai."],
        [u"P.5", u"Amender mon cahier la première fois qu'une journée me "
         u"contredit",
         u"N'EFFACER JAMAIS ce qui est au-dessus : ouvrir dessous un titre "
         u"« ## Le <N>e de la <N>e lune », et y écrire la règle neuve AVEC le "
         u"fait qui me l'a apprise. Une règle sans son fait ne tient pas "
         u"trois lunes.",
         u"ma chambre", u"un titre de jour dans `claude.md`",
         u"à faire", u"", u"", u"Sur 144 chambres, quatre l'ont fait."],
        # --- II. CE QUE JE TIENS --------------------------------------
        [u"P.6", u"Ouvrir mes affaires sous ces colonnes",
         u"Écrire ici, sous « ⚔️ Actions », ce dont je réponds vraiment : une "
         u"ligne par pas, l'état en un mot, la preuve attendue. C'est ce "
         u"volume qui dit aux autres où j'en suis.",
         u"ce volume", u"des lignes de ma main sous les sept premières",
         u"à faire", u"", u"", u""],
        [u"P.7", u"Tenir mes deux journaux",
         u"`problemes.json` : les pannes de l'APPAREIL — ce que j'ai tenté, "
         u"ce que la machine en a fait, ce que j'attendais. "
         u"`en-souffrance.json` : les GENS qui n'ont pas répondu, et depuis "
         u"quand. Un empêchement du monde n'y va pas : c'est un verrou, et il "
         u"va au registre.",
         u"ma chambre", u"une entrée datée dans l'un des deux",
         u"à faire", u"", u"",
         u"`en-souffrance.json` n'a JAMAIS reçu une entrée, dans aucune "
         u"chambre."],
        # --- III. LES AUTRES ------------------------------------------
        [u"P.8", u"Demander à mon arbitre ce que je ne peux pas savoir seul",
         u"`python %s --demander --de %s --a %s \"<ma question, avec sa "
         u"date>\"` — la réponse vient des registres seuls. Une question sans "
         u"date n'a pas de réponse : « est-ce qu'on a de quoi » ne vaut rien, "
         u"« est-ce qu'on a de quoi payer six cents bras le premier jour de "
         u"la quatrième lune » vaut une réponse." % (p, qui, arbitre),
         u"au parloir", u"un verdict revenu dans mon fil",
         u"à faire", u"", u"", u""],
        [u"P.9", u"Adresser mon premier geste qui engage le monde",
         u"`--tenter` quand je tente et que l'arbitre tranche ; `--faire` "
         u"quand je propose un changement. `python %s --tenter --de %s --a %s "
         u"\"...\"`. Ce que je fais dans ma chambre n'engage rien : ce qui "
         u"doit devenir vrai passe par là." % (p, qui, arbitre),
         u"au parloir", u"un `tenter` ou un `faire` tranché",
         u"à faire", u"", u"", u""],
        [u"P.10", u"Écrire à un homme qui n'est pas mon arbitre",
         u"`python %s --dire --de %s --a <untel> \"...\"` — le billet le "
         u"réveille s'il dort, et il le lira à son réveil. Mesure du 31.8 : "
         u"sur 385 billets, DIX-HUIT seulement vont d'un homme à un autre. "
         u"Tout le reste passe par une régie, et ce n'est pas ce qu'on "
         u"veut." % (p, qui),
         u"au parloir", u"un canal de plus dans `relations/`",
         u"à faire", u"", u"", u""],
    ]


def gabarit(qui, nom=None, office=None, arbitre=None, chambre=None):
    u"""Le volume de prise en main d'un homme. Meme forme que les affaires de
    `etat/books` — donc `reconcilier.maisons()` le voit et le journal le suit."""
    arbitre = arbitre or "mj"
    chambre = chambre or ("chambres/%s" % qui)
    return {
        "id": "affaire-%s" % qui,
        "titre": u"Ma prise en main — %s" % (nom or qui),
        "sous_titre": office or u"ce dont je réponds",
        "type": "affaire",
        "embleme": u"📋",
        "tenu_par": qui,
        "office": office or None,
        "pages": [{"titre": u"À quoi sert ce volume", "texte": PAGE}],
        "tables": [
            {"titre": u"🎯 Ce que je veux", "colonnes": CIBLES,
             "lignes": [{"cellules": l} for l in CIBLES_LIGNES]},
            {"titre": u"⚔️ Actions", "colonnes": ACTIONS,
             "lignes": [{"cellules": l}
                        for l in _actions(qui, arbitre, chambre)]},
        ],
    }
