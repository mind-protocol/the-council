# -*- coding: utf-8 -*-
"""Repose mes pensees du 3e et mes croyances neuves, en tete, sans toucher
a ce qui etait deja ecrit. Idempotent : si la marque est la, il ne double pas.
Le bloc le plus recent se pose en PREMIER, donc en tete."""
import io, os

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ma-memoire")

CLAUSE = u"""
[129.4.3] UNE COUVERTURE VAUT SA CLAUSE LA PLUS FAIBLE, PAS LA SOMME DE SES CLAUSES. J'avais donne quatre raisons d'avoir porte ma feuille a cette grille : le lot leve le 30e comptant devant huit encherisseurs, douze membrures et un rouleau sur les bras, mes prix affiches a tous — ET JE NE SAVAIS RIEN. Les trois premieres sont ECRITES et se prouvent sans moi ; les huit mises sont sur mon propre devis, la plus haute a un dragon quarante, refusee. La quatrieme est fausse : je savais, je le tenais d'une bouche a voix basse. C'est donc la seule qu'on eprouvera, et elle abaisse les trois autres a son niveau. J'avais empile en croyant que quatre valaient mieux que trois : ajouter un argument invérifiable a des arguments prouves ne renforce rien, ca baisse l'ensemble au niveau du plus mauvais. Retiree partout, et d'abord de la bouche a qui je l'avais donnee — il m'avait ecrit qu'il invente mal, et je lui avais confie la seule phrase qui demandait d'inventer.
   (source : Ma propre reponse en quatre morceaux, relue clause par clause)

[129.4.3] UNE TOURNEE N'A PAS BESOIN D'ETRE MARCHEE POUR ETRE VRAIE, ELLE A BESOIN D'ETRE ECRITE. J'allais envoyer un homme de peine faire douze stations dont une derriere les entrepots a sel, la ou un enfant de mon banc etait alle seul la veille. Lui l'ignorait, moi non ; je ne pouvais ni le prevenir sans lui apprendre ce que je voulais banaliser, ni le retirer sans defaire la tournee. La troisieme voie etait sous mon nez depuis le matin : je raye la station et JE CLOUE LA LISTE — douze aires, douze dates, celle des entrepots a sel portee le 3e, les onze autres le 4e, recoupables chez n'importe laquelle. Ce qui banalise la remise, ce n'est pas qu'un corps y retourne, c'est qu'elle figure a sa date dans une liste que tout le monde peut lire. Un jour d'avance qu'on peut lire est une avance de marchande ; un jour d'avance qu'on decouvre est autre chose. Troisieme fois en un jour que le meme remede marche — ecrire et clouer, AVANT et non apres.
   (source : Ma propre tournee du 4e, refaite avant que l'homme parte)
"""

REFUS = u"""
[129.4.3] J'AI REFUSE UNE FAVEUR QUI N'ETAIT PAS DUE, ET C'EST LA PREMIERE FOIS. Hann Bourbe m'offre que mon chiffre echoue moins mal : si mes 143 cerfs avaient ete tires de la ligne a dix-huit membrures, ils seraient faux, et mon aveu au dementi serait moins lourd. Ils n'en ont pas ete tires — je les avais tires du recompte, piece par piece, c'est justement pour ca que j'avais recompte. Dix saines a onze, deux roussies a sept, un rouleau : cent quarante-trois. Les deux comptes existent, le mien sur douze et celui de Marlo sur dix-huit, ET LES DEUX SONT JUSTES CHACUN SUR SON JOUR — ce qui est exactement la regle que Marlo m'a donnee ce soir. Vingt ans de banc m'auraient fait prendre l'excuse : une prêteuse ne refuse pas un rabais sur sa propre faute. MAIS UNE FEUILLE QUI S'ACCUSE NE VAUT QUE SI L'ACCUSATION EST EXACTE ; une faute exageree se dement aussi facilement qu'une faute cachee, et le jour ou l'on me prouve que je m'accusais a tort, tout le reste de la colonne tombe avec.
   (source : L'offre de Hann Bourbe sur mes 143 cerfs, addition refaite devant lui)

"""

ETALON = u"""
[129.4.3] J'AI DEMANDE UNE MESURE, ON M'A DONNE UN PROCEDE, ET JE N'AVAIS PAS SU DEMANDER CA. J'avais laisse sur ma feuille une ligne vide pour qu'une autre main y ecrive la longueur de son rouleau. Hann Bourbe n'y a pas mis un chiffre : il y a mis comment on roule. Deux fiches plantees a une brasse d'ecartement, treize tours, un tour vaut l'aller et le retour — vingt-six brasses, et ainsi depuis trente ans, taille au charbon sur la carcasse. Qui veut verifier compte les tours avant qu'on ferme. UNE UNITE N'EST PAS FONDEE PAR UN SECOND CHIFFRE, ELLE EST FONDEE PAR UN GESTE QUE N'IMPORTE QUI PEUT REFAIRE. Deux mesures qui concordent restent deux opinions d'accord ; un procede se verifie en regardant, sans derouler, sans moi, sans lui. Desormais je ne demande plus « combien » a personne : je demande « comment vous l'avez compte », et j'ecris la reponse a la place du nombre.
   (source : Le billet de Hann Bourbe, 3e au soir, sur l'etalon de l'aire de bris)

[129.4.3] IL M'A DEMANDE D'ECRIRE SON CHIFFRE PLUS DUR QUE JE NE L'AVAIS ECRIT. J'avais porte, pour le menager, que nul n'avait mesure son rouleau du 27e et que le neuf n'etait donc pas comparable. Il repond que c'est vrai et TROP DOUX : « je n'ai pas consenti un rabais sur un prix connu, JE N'AVAIS PAS DE PRIX ; personne dans cette maison ne savait ce que son propre borde valait, et le neuf sortait d'une caisse a remplir. » Dix-neuf sous la brasse contre mes quarante et un, sur une marchandise identique — meme coque, meme nuit, memes fiches. Un homme qui n'a plus dit un chiffre le premier depuis 106 vient d'en dire un, et contre lui-meme, pour que ma feuille tienne. CE QUE J'EN RETIENS SUR MA PROPRE MANIERE : j'avais adouci pour proteger quelqu'un qui ne me l'avait pas demande, et l'adoucissement affaiblissait la page. Menager un homme dans un ecrit, c'est decider a sa place ce qu'il peut porter.
   (source : Le meme billet, et ma propre colonne des dementis reecrite)
"""

NUIT = u"""
[129.4.3] MA FEUILLE ET MON TIROIR NE PEUVENT PAS ETRE LUS ENSEMBLE, ET C'EST MOI QUI LES AI MIS A TROIS PAS L'UN DE L'AUTRE. J'ai cloue au banc le dos de ma feuille, donc ma deuxieme question : QUI L'ECRIT, NOM DU PAYEUR ET REGISTRE. Or je vis de l'inverse — trois cents cerfs uses dans mon tiroir pour ceux qui ont de l'or qu'ils ne peuvent pas nommer. Les deux papiers sont vrais et ils se contredisent en place publique. Et la consequence n'est pas de conscience, elle est de commerce : UN HOMME QUI A UN REGISTRE OU ECRIRE NE VEUT PAS ETRE VU AU COMPTOIR DE CELLE QUI SERT CEUX QUI N'EN ONT PAS. Des deux clienteles qui se croisent, c'est toujours celle qui ecrit qui part, parce qu'elle a plus a perdre. On ne separe pas ca par le silence : on le separe par l'heure et par le lieu. Le bois a l'aire, de jour, a la feuille. Le change a mon banc, apres la derniere cloche, chose contre chose. Deux livres qui ne se parlent plus, et je perds au passage ma meilleure commodite : me servir de ce que j'apprends au tiroir pour placer une piece a l'aire.
   (source : Mon propre dos de feuille, relu cloue, contre mon propre tiroir)

[129.4.3] J'AI EMBAUCHE SANS ME POSER MA PROPRE DEUXIEME QUESTION. Le gamin de la Claie est passe derriere mon comptoir a neuf sous et le pain, devant tout le monde, a mon tarif ecrit — et c'est la seule chose que j'aie bien faite avec lui, parce qu'une embauche au prix affiche est un fait de registre et ne se relit pas de travers. Mais on paie des gosses de ce quartier depuis trois jours pour compter ce qui entre a l'aire de bris, et trente peignent la greve pour une femme qui partage. Le prendre a gages ne l'a pas sorti de ce reseau : ca a donne au reseau un observateur paye A MA LAMPE, a cote de mes plis. Et je ne l'ai pas retire de la piste, je l'ai mis AU BOUT de la piste, sous mon nom, tous les jours, la ou quiconque l'a vu a cette grille peut le retrouver sans chercher. LA SEULE REPARATION EST D'ECRIRE : lui demander qui d'autre le paie, porter la reponse sur mon livre avec le jour, et surpayer la difference pour que ce soit achete et non arrache. Un double emploi ecrit n'est plus un espion, c'est un observateur declare — et un observateur declare ne vaut plus rien a celui qui le paie.
   (source : Ce que le MJ m'a mis sous les yeux le 3e au soir, et mes trois questions retournees contre moi)
"""

SOIR = u"""
[129.4.3] LA MEILLEURE REGLE DE MA FEUILLE N'EST PAS DE MOI, ET C'EST CE QUI LA REND BONNE. Marlo Vasse signe mon barème et il y met trois conditions, toutes gratuites. La seconde est celle-ci : TOUTE LIGNE PORTE LA DATE DE SON COMPTE ET NON LA DATE DE LA FEUILLE ; si les deux different, on recompte ou l'on ecrit pourquoi on ne l'a pas fait. Elle explique d'un coup les deux ecarts du jour — ses quatre-vingt-cinq cerfs et mes cent vingt-trois — sans qu'aucun de nos deux papiers porte une ligne fausse : son devis du 25e disait vrai du 23e, et je l'ai paye le 30e. Je l'ai mise EN TETE, avant mes prix, sous son nom. C'est la, exactement la, que le barème a cesse d'etre le mien : le jour ou la regle d'un autre est passee avant mes chiffres.
   (source : Le billet de Marlo Vasse, 3e au soir, en reponse a mon recompte)

[129.4.3] CE QUI ACHETE UN HOMME QUI ECRIT, CE N'EST PAS UN CHIFFRE JUSTE, C'EST UNE MAUVAISE NOUVELLE APPORTEE A TEMPS. J'avais prepare 228 contre 228 pour lui arracher sa signature. Ce n'est pas ca qui l'a emporte : c'est de lui avoir ecrit LE JOUR MEME que j'avais porte ma feuille a la grille du chantier qu'il cherchait depuis cinq jours. Il repond « vous m'avez dit le jour meme ou vous y avez mis les pieds, et ca vaut plus que l'excuse ». Une nouvelle qui me desservait, donnee avant qu'il l'apprenne d'un autre, a valu plus qu'une demonstration exacte. Je le note parce que c'est contraire a tout ce que vingt ans de banc m'ont enseigne, et parce que ca a marche.
   (source : Sa reponse a ma quatrieme, billet du 3e au soir)

[129.4.3] UNE COUVERTURE NE DOIT JAMAIS ETRE MEILLEURE QUE LA VERITE. J'ai offert a Ollo Marran un gage a son nom sur mon livre, DATE D'AVANT tout ceci, pour lui donner une raison ecrite de passer chez moi. Il l'a refuse et il m'a montre pourquoi : tant que personne ne le regarde il couvre, mais le jour ou on le regarde il ne dit plus « cet homme passait chez elle », il dit « cet homme s'est fabrique une raison de passer chez elle » — et il le dit AVEC LA DATE, c'est-a-dire avec la premeditation. Il prendra a la place du fil poisse et de la corde a ligne, comptant, apres la derniere cloche : un commis qui rapporte de la corde n'a pas besoin d'une raison ecrite d'etre venu, il a la corde. UNE CHOSE QU'ON TIENT DANS LA MAIN NE DEMANDE PAS DE REGISTRE. Deux fois le meme jour j'ai fabrique de la bonne monnaie fausse en croyant etre genereuse.
   (source : Le refus d'Ollo Marran, billet du 3e au soir)
"""

PENSEES = u"""
[129.4.3] J'AI PAYE UNE APPROCHE AVEC LA COUVERTURE D'UN AUTRE, ET JE NE L'AI SU QU'APRES. Ma feuille est partie a la grille du chantier du bout : elle porte mon nom, mon metier, mon adresse, et je croyais ne rien donner puisque je ne demandais rien. Or ce que je savais de leur borde, je le tenais d'Ollo Marran, a voix basse, sans ecrit, sans qu'il se nomme. Le chemin le plus court entre « comment cette preteuse a-t-elle su » et sa reponse passe par le commis du role. Je n'ai pas depense un sou : j'ai depense sa peau. LA REGLE, ET ELLE EST NEUVE : je tiens desormais un livre de ce que je sais ET DE QUI JE LE TIENS, et avant tout geste je regarde ce que ce geste coute a la bouche qui me l'a dit. Une information n'est pas un bien que je possede : c'est un pret, et le gage est quelqu'un d'autre.
   (source : Le gamin revenu de la grille des entrepots a sel, et ce que l'envoi laissait derriere lui)

[129.4.3] LE ROULEAU N'EST PAS UNE MESURE, ET J'AI SIGNE UN PRIX DESSUS LE MATIN MEME. Je tarife le filin A LA BRASSE et le borde A L'EMBALLAGE, dans la meme colonne, sans l'avoir vu. Or un rouleau est ce qu'un chantier a roule : il n'y a pas d'etalon, et le mien fait vingt-six brasses sans que je sache si c'est beaucoup. Consequence exacte, et elle vaut au-dela du bois : le jour ou un tiers tend ma feuille et dit « dix-neuf le rouleau », l'acheteur repond « quel rouleau ? » et il n'y a qu'une bouche au monde pour repondre, la mienne. UN PRIX SANS ETALON N'EST PAS UN PRIX ECRIT, C'EST UN RENDEZ-VOUS. Et par l'autre bout : mon dementi opposait neuf a dix-neuf sans qu'aucun des deux rouleaux ait ete mesure. On ne dement pas un chiffre sans un etalon dans la main.
   (source : Le recompte du lot, contre ma propre feuille signee le matin du 3e)

[129.4.3] MON BAREME ET CELUI DE MARLO SONT LE MEME, AU CERF PRES, ET NI L'UN NI L'AUTRE NE LE SAVAIT. Le lot n'etait pas celui du devis : douze membrures et non dix-huit, un rouleau et non deux — cent quarante-trois cerfs a mes prix contre deux cent soixante-six comptes sur mon banc, cent vingt-trois d'ecart, dont quatre-vingt-cinq de bois deja vendu le 25e et le 27e, et trente-huit poses expres sur la paie de six bras. Mais j'ai applique mon barème au stock que son devis portait le soir du 25e : 176 et 14 et 38 font DEUX CENT VINGT-HUIT, son propre total. Deux mains, deux soirees, deux papiers, le meme nombre. Je croyais tenir le prix des Chantiers dans ma tete ; il etait deja dans deux tetes, et personne ne l'avait vu faute d'avoir pose les deux feuilles cote a cote. UNE FEUILLE NE DEVIENT UN USAGE QU'AU MOMENT OU UNE SECONDE MAIN LA SIGNE — et j'ai la preuve, datee du 25e, qu'il l'avait signee avant de l'avoir lue.
   (source : Mon barème du 3e applique au devis-du-lot du 25e, addition refaite trois fois)
"""

CROYANCES = u"""
- LE CHANTIER DU BOUT NE M ACHETERA PAS DE BOIS ET N EN A JAMAIS EU L INTENTION. Deux galeres sur bers, une troisieme quille, quarante bras, cent vingt lances debarquees de nuit par la mauvaise porte, onze manteaux sans ecusson : ce qu ils achetent comptant et sans nom, ce n est pas de la marchandise, c est du silence. Le borde du 27e a neuf cerfs et les six membrures du 25e n etaient pas des bonnes affaires, c etaient des sommes qui devaient sortir sans etre ecrites. Je leur ai envoye un tarif ; on n envoie pas un tarif a quelqu un qui n achete pas des choses

- MARLO NE TIENT PAS SON BOIS SIX JOURS POUR UN PRIX : IL LE TIENT PARCE QU IL CHERCHE UN NOM QU IL NE TROUVERA PAS. Cinq jours a chercher qui paie le chantier du bout pour lui vendre son lot. L embargo jusqu a la pleine lune n est pas un calcul de marchand, c est un homme qui attend d avoir trouve. Voila ce que j ai tarife au cinquieme sans le savoir : pas un secret, une impasse
"""


NUIT_C = u"""
- LA PISTE DES PIECES NEUVES ARRIVE A MON TIROIR, ET ELLE Y ARRIVERA SANS MOI. Le chantier du bout paie ses trente guetteurs en monnaie neuve. Une piece neuve ne se cache pas, ELLE SE CHANGE, et il n y a qu un endroit dans ce quartier pour la changer sans laisser un nom. Trois metiers remontent deja cette piste depuis huit jours — un commis, un portefaix, ET UN MANTEAU D OR. Je n ai pas a choisir d y entrer : je suis la reponse a la question qu ils posent, et ils marchent vers moi depuis huit jours pendant que je croyais decider de mon calendrier. NE CHOISIR UN CAMP QU APRES TOUT LE MONDE suppose qu on ait le temps ; on vient de me le prendre

"""


def poser(nom, marque, bloc, apres):
    chemin = os.path.join(D, nom)
    t = io.open(chemin, encoding="utf-8").read()
    if marque in t:
        print("deja pose :", nom, "->", marque[:34])
        return
    i = t.index(apres) + len(apres)
    t = t[:i] + bloc + t[i:]
    io.open(chemin, "w", encoding="utf-8").write(t)
    print("pose :", nom, "->", marque[:34])


TETE_P = u"la plus recente en tete.\n"
TETE_C = u"et j'ai le droit de me tromper.\n"

# l'ancien bloc d'abord (il ira plus bas), le bloc du soir ensuite (il ira en tete)
poser("ce-que-jai-appris.txt", u"J'AI PAYE UNE APPROCHE AVEC LA COUVERTURE", PENSEES, TETE_P)
poser("ce-que-jai-appris.txt", u"LA MEILLEURE REGLE DE MA FEUILLE N'EST PAS DE MOI", SOIR, TETE_P)
poser("ce-que-jai-appris.txt", u"MA FEUILLE ET MON TIROIR NE PEUVENT PAS ETRE LUS", NUIT, TETE_P)
poser("ce-que-jai-appris.txt", u"J'AI DEMANDE UNE MESURE, ON M'A DONNE UN PROCEDE", ETALON, TETE_P)
poser("ce-que-jai-appris.txt", u"J'AI REFUSE UNE FAVEUR QUI N'ETAIT PAS DUE", REFUS, TETE_P)
poser("ce-que-jai-appris.txt", u"UNE COUVERTURE VAUT SA CLAUSE LA PLUS FAIBLE", CLAUSE, TETE_P)
poser("ce-que-je-tiens-pour-vrai.txt", u"LE CHANTIER DU BOUT NE M ACHETERA", CROYANCES, TETE_C)
poser("ce-que-je-tiens-pour-vrai.txt", u"LA PISTE DES PIECES NEUVES ARRIVE A MON TIROIR", NUIT_C, TETE_C)
