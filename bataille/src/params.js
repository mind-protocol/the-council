/**
 * Params — constantes transverses, nommées et commentées. Unités SI :
 * mètres, secondes, m/s. Les valeurs propres à un scénario (zone, spawns)
 * vivent dans le scénario, pas ici.
 */

export const PARAMS = {
  // Corps d'un homme
  rayonHomme: 0.35,        // m — encombrement épaules
  // la masse est une DISTRIBUTION (comme les cadences) : tirée au spawn,
  // portée par le registre 🌍 — un fait du corps, comme le rayon
  masseHomme: { moyenneKg: 80, ecartTypeKg: 10, minKg: 55 },

  // Corps d'un cheval — l'attelage : le cheval porte, le cavalier veut.
  // V1 : l'allure de route est le TROT ; le galop viendra avec l'etat de
  // charge monte (l'allure par etat). Souffle de cheval : differe.
  cheval: {
    rayon: 0.6,     // m — l'encombrement d'un cheval vu du dessus
    masse: { moyenneKg: 480, ecartTypeKg: 60, minKg: 350 },
    allures: { pas: 1.7, trot: 3.5, galop: 8 }, // m/s
    accelMax: 3.5, // m/s2 — un cheval s'arrete et s'elance mieux qu'un homme charge
    // LE REFUS : un cheval ne s'enfonce pas dans une masse herissee — reflexe
    // d'ACTUATION (juge sur le reel devant lui, comme l'acte de frapper),
    // CONTINU : freinage proportionnel au herissement, derobade vers le
    // cote le moins pique. C'est ce qui fait TENIR les murs de piques.
    refus: {
      regardBaseM: 3,        // m — on regarde devant soi...
      regardParVitesseS: 1.2, // ...d'autant plus loin qu'on va vite (v x ce temps)
      rayonRegard: 3,        // m — la fenetre regardee autour du point devant
      allongePique: 2,       // m — au-dela, une pointe LEVEE compte plein
      poidsPique: 1,
      poidsAutre: 0.25,      // une epee levee inquiete peu un cheval
      pointesPourStopper: 4, // ~4 piques levees dans la fenetre = refus total
      deriveMax: 1.5,        // m/s — la derobade laterale a refus plein
    },
    // LA PASSE : un cavalier ne se tient pas au contact — il traverse,
    // reprend du champ, se reforme et revient. La reprise : le champ minimal
    // devant la masse crue pour (re)donner une charge.
    passe: { repriseM: 22 },
  },
  vitesseMax: 1.4,         // m/s — marche ; viendra du ❤️ Corps plus tard
  vitesseRecul: 0.5,       // m/s — a reculons (le corps, pas la volonte) : on ne fuit vite qu en tournant le dos
  accelMax: 1.5,           // m/s² — inertie : borne les changements d'allure ET de direction

  // Cadence de décision (brains)
  cadence: { moyenneHz: 0.5, ecartTypeHz: 0.1 },

  // Dragon (🧠 brain) : le vol se pilote plus vite que la marche — a 50 m/s,
  // une decision toutes les 2 s laisserait passer 100 m
  oiseau: { cadence: { moyenneHz: 2, ecartTypeHz: 0.3 } },

  // Perception (🧠) : cercle 360°, budget d'attention, cadence propre
  perception: {
    portee: 20,                                  // m
    budgetAttention: 7,                          // OBJETS max (individus + tas)
    chainageTas: 2.5,                            // m — deux hommes plus proches = même tas
    cadence: { moyenneHz: 2, ecartTypeHz: 0.3 }, // re-scans du monde
    rayonContact: 6,                             // m — en deca, on voit des HOMMES, plus une masse
    facteurAlerte: 0.35,                         // un adverse au contact -> je re-scanne ~3x plus vite
    facteurCalme: 2,                             // ni contact ni ennemi cru -> je scrute deux fois moins (l'horizon de masse veille)
    // la forme d'un tas (cap par les lances visibles, première ligne)
    forme: { netteteMin: 0.55, trancheAvant: 0.8 }, // cohérence min, épaisseur du 1er rang (m)
    // l'horizon de MASSE : au-dela du detail, un groupe de N hommes se voit
    // jusqu'a N x porteeParHomme (continu : un homme seul = la portee de
    // detail, une bande de 20 se voit partout). De loin on voit MOINS :
    // effectif a la poignee, ni postures ni forme — des champs ABSENTS
    masse: {
      porteeParHomme: 20,  // m — la visibilite d'une masse croit avec sa taille
      porteeMax: 400,      // m — plafond (l'echelle du theatre — 400 depuis le Dracarys)
      chainage: 5,         // m — de loin, les grappes fusionnent (une ligne = UNE masse)
      arrondiEffectif: 5,  // on estime a la poignee, jamais a l'homme pres
      cadence: { moyenneHz: 0.25, ecartTypeHz: 0.05 }, // on jette un oeil a l'horizon, on ne le scrute pas
    },
  },

  // Mise en formation (brain soldat)
  formation: {
    seuilArrive: 0.45,      // m
    seuilRecalcul: 0.3,     // m
    fraicheurRepere: 6,     // s — au-delà, ma première ligne crue est trop vieille pour servir de repère
    distanceImplicite: 4,   // m — « en formation » nu : l'amorçage se fait devant le locuteur
  },

  // Orientation (🧠) — l'arbitrage d'attention : où pointe mon corps
  orientation: {
    poidsMouvement: 1.0,   // « où vais-je » — multiplié par v/vitesseMax
    poidsVersGens: 0.6,    // « vers les gens intéressants »
    poidsCommeGens: 0.3,   // « comme les gens » — conformité des regards
    poidsFace: 3.0,        // flag facer : celui qu'on FACE domine l'arbitrage
    seuilResultante: 0.15, // en dessous : conserver le cap courant
    dureeEchoOrdre: 4,     // s — après un ordre entendu, son émetteur est facé
    // chaque tour de tête a SA durée ~N (pas robotique) ; un degré d'urgence
    // la divisera un jour. rotationMax reste le plafond PHYSIQUE (⚙️).
    dureeRotation: { moyenneS: 0.5, ecartTypeS: 0.12 },
    rotationMax: 6.0,      // rad/s (⚙️) — plafond corporel, l'urgence ne le bat pas
  },

  // Regroupement (brain gregaire) : on se tient EN CERCLE autour du
  // barycentre, jamais dessus (anti-hug)
  // rayon = plancher ; le rayon effectif se dérive de l'effectif CRU du tas
  // visé (espacement sur la circonférence) — un cercle de 20 s'étale
  discussion: { rayon: 1.2, espacement: 0.9, tolerance: 0.4, flottementAngulaire: 0.6, probaReplacement: 0.15 }, // m, m, m, rad, proba par décision

  // Acoustique (⚙️, stub) — portées de voix pour la future Transmission 📯
  acoustique: {
    porteeVoix: { murmure: 2, parole: 8, cri: 25 }, // m
  },

  // Paroles (🧠) — la surcouche de flavor : repliques contextuelles emises
  // par les brains (bascules de machine, seuils de jauges, bavardage, defis).
  // Flux rng DEDIE (seede par id) : ajouter une vanne ne change JAMAIS le
  // deroule d'une bataille — c'est le sens de « surcouche » (mesure : sur le
  // rng partage, le refus vecu de La Conroi passait de 57 ticks a 0).
  // Personne n'ecoute encore — la voix qui porte viendra (📯).
  paroles: {
    dureeBulleS: 3.5,   // s sim d'affichage d'une bulle
    silenceMinS: 4,     // s — deux repliques d'un meme homme, jamais a moins (anti-spam)
    verifJaugesS: 1,    // s — cadence de la verif des seuils (peur, souffle, carquois)
    probaSeuil: 0.1,    // un franchissement sur ~10 se dit — les autres le gardent pour eux
    bavardage: { moyennePeriodeS: 180, ecartTypeS: 60 }, // s — entre deux vannes desoeuvrees
    defi: { moyennePeriodeS: 90, ecartTypeS: 30 },       // s — les insultes du face-a-face
  },

  // Chercher (competences) : distance sous laquelle une piste est consideree verifiee
  chercher: { rayonVisite: 2.5 }, // m

  // Souffle (coeur) : reserve lineaire, RESSENTI sigmoide (pas une barre) —
  // long plateau frais, bascule vers 35 % de reserve, plateau epuise
  souffle: {
    dureeEpuisementS: 45,    // s d'engagement plein pour vider la reserve
    dureeRecuperationS: 90,  // s de repos pour la remplir
    facteurMarche: 0.35,     // la marche a pleine vitesse = 35 % d'un engagement
    sigmoide: { centre: 0.35, raideur: 8 },
  },

  // Combat : l engagement au contact — on n attaque JAMAIS seul.
  // Allonge, arc, rearmement, cout de garde : PAR ARME (❤️ corps/armes.js)
  combat: {
    graviteCuree: 3,      // un coup dans un dos en fuite compte TRIPLE — la curee tue
    rayonEngagement: 5.5,    // m — l ennemi cru a moins : la machine passe en tuer
    rayonDesengagement: 8,   // m — on ne SORT du combat qu au-dela (hysteresis anti-clignotement)
    margeFrappe: 0.2,     // m — portee de frappe = allonge de MON arme + marge
    souffleEngage: 0.6,   // ressenti mini pour se dire PRET (hysteresis haute)
    souffleBas: 0.3,      // ressenti sous lequel on rompt (hysteresis basse)
    allurePoussee: 0.3,   // fraction de vitesse : pousser doucement
    allureRecul: 0.35,    // fraction de vitesse : reculer sans tourner le dos
    allureFente: 0.8,     // la fente : fraction de vitesse max, le temps du geste
    dureeFenteS: 0.4,     // s — la fente est un GESTE bref (la fenetre avant le coup), pas une poussee continue
  },

  // Moral (🧠, une croyance) : la peur monte par PICS (un mort des miens vu),
  // decroit avec le temps ; s ajoutent le rapport percu et la CONTAGION (les
  // miens vus en fuite). Au seuil : la rupture — presque d un coup, l arriere
  // d abord (depuis engage, pas le temps d y penser : pas de transition)
  moral: {
    picParMort: 0.35,   // un mort des miens vu, la premiere fois
    tauPeurS: 12,       // demi-vie ~8 s : les pics de recence
    poidsRapport: 0.3,  // etre surclasse en face pese
    poidsFuyards: 3.5,  // la contagion : x la PROPORTION des miens en fuite (une grande unite est plus solide), PONDERE par la menace locale
    oubliMenaceS: 8,    // s — un tas adverse cru plus vieux ne donne plus prise a la contagion
    // la menace se mesure en SECONDES (tau = distance 3D / allure crue) :
    // 14 s = portee/vitesseMax — le comportement a pied est conserve ; un
    // galop (8 m/s) menace a ~110 m, un vol sur tout le theatre
    horizonMenaceS: 14,
    seuilRompt: 0.8,    // au-dela : je romps
    seuilRassure: 0.3,  // en-deca (et hors de danger) : je reprends mes esprits
  },

  // Sante (coeur) : les coups reduisent la vitesse ; au seuil, la mort —
  // un CONSTAT de la physiologie, manifeste par la posture 'gisant'
  sante: {
    coupsMortels: 4,          // au N-ieme coup, l homme tombe
    malusVitesseParCoup: 0.18,
    plancherVitesse: 0.35,    // un blesse boite, il ne s arrete pas
  },

  // Choc (⚙️) : le transfert de quantite de mouvement a l'impact — la
  // POUSSEE DE MASSE. L'a-coup subi (delta-v) bouscule toujours ; au-dela
  // d'un cran, il RENVERSE (a terre, on se releve) — duree qui croit avec
  // l'exces (continu). Presque mou : on encaisse, on ne rebondit pas.
  choc: {
    restitution: 0.2,      // 0 = mou, 1 = billard
    vRelMin: 1.0,          // m/s d'approche : en deca, c'est une bousculade, pas un choc
    deltaVRenverse: 2.5,   // m/s d'a-coup subi : au-dela, jete a terre
    dureeMinS: 1.2,        // a terre au moins ca
    dureeParDeltaV: 0.6,   // s de plus par m/s d'exces
    dureeMaxS: 5,
    demiVieGlissadeS: 0.3, // le sol freine un corps renverse (glissade breve)
    // le choc BLESSE au-dela d'un cran (continu) : etre percute par un
    // demi-tonne au galop n'est pas une bousculade — c'est le trauma qui
    // fait tuer la charge, pas seulement renverser
    blessure: { deltaVMin: 3, coupsParDeltaV: 0.35 },
  },

  // Tir (🏃) : la fleche qui tombe
  tir: {
    rayonImpact: 0.9, // m — une fleche touche qui se trouve LA ou elle tombe
  },

  // Garde (⚙️) : chacun se tient hors de portee de la pointe ADVERSE —
  // asymetrique par arme (❤️ armes.js) : l epeiste craint la pique a 4,7 m,
  // le piquier ne craint l epee qu a 1,3 m
  garde: {
    margeAllonge: 0.2, // m — la portee de garde = allonge de l arme ADVERSE + marge
    intensite: 1.0,    // m/s — ferme : la mesure d escrime tient les lignes
  },

  // Coude-a-coude (⚙️) : les rangs se soudent — faits geometriques purs
  coudeACoude: {
    capParallele: 0.6,     // rad — au-dela, les regards divergent : pas une ligne
    porteeLaterale: 2.2,   // m — au-dela, pas voisins d epaule
    longitudinalMax: 0.7,  // m — decalage avant/arriere tolere (cote a cote)
    espacement: 1.2,       // m — l epaulement cible (= le drill)
    intensite: 0.5,        // m/s — doux : influence, jamais aspiration
  },

  // Menace : un tas de livree adverse, cru frais et proche -> on se regroupe
  menace: { rayon: 12, fraicheurS: 3 }, // m, s

  // Couverture (🧠) — la carte cognitive du « où j'ai regardé »
  couverture: { tailleCase: 8, peremptionS: 600 }, // m, s — la péremption doit dépasser la durée d'un ratissage (sinon Sisyphe)

  // Commandement (🧠 commandant) — l'état-major
  commandement: {
    cadence: { moyenneHz: 0.1, ecartTypeHz: 0.02 }, // tempo de délibération
    fraicheurEnnemi: 30,       // s — au-delà, l'ennemi n'est plus « localisé »
    hysteresis: 1.3,           // une candidate doit dépasser l'engagée de +30 %
    malusEchecS: 45,           // s — une manœuvre qui vient d'échouer est boudée
    personnaliteEcart: 0.05,   // offsets de poids tirés par commandant
    seuilInconnue: 0.1,        // part de zone sous laquelle « tout est ratissé »
    plancherEngagement: 0,     // une utilite negative ne s engage pas — on tient les rangs
    porteeExposition: 25,      // m — a ce point devant la bande amie, l exposition sature (-1)
    // le DEBORDEMENT (charger par un flanc) : contourner le bout de la ligne
    // ennemie crue — le gain annonce (gainDePosition) et son prix (desordre)
    margeDebord: 6,            // m — le crochet passe au-dela du bout de leur ligne
    qualiteDebord: 0.5,        // frapper un bout de ligne, la ou les pointes ne regardent pas
    desordreDebord: 0.3,       // la marche qui tourne desordonne les rangs
    // poids des axes (posture agression) — se règlent devant la viz état-major
    poids: { temps: 0.3, exposition: 0.5, gainDePosition: 0.8, coutFatigue: 0.2, risqueDesordre: 0.3, gainInformation: 0.9 },
  },

  // Ratissage — chaque cri RATISSER = un BOND de secteur (l'unité se reforme
  // au ralliement en contournant les obstacles ; le serpentin = les cris)
  // biaisDirection : poids de la rumeur directionnelle dans le choix des
  // secteurs (score = distance − poids × projection) — préférence, pas interdit
  ratissage: { sautSecteur: 12, biaisDirection: 0.6 }, // m, sans unité

  // Barrage (🧠 commandant) — la recherche de la meilleure ligne : segments
  // ⊥ a l'axe de menace, la carte connue bouche, les trous se comptent
  barrage: {
    pasAvant: 3,        // m — l'echantillonnage le long de l'axe de menace
    porteeScan: 24,     // m — jusqu'ou on considere des lignes devant soi
    demiLargeur: 25,    // m — l'envergure scannee de part et d'autre de l'axe
    pasLateral: 1,      // m — l'echantillonnage du segment
    declinDistance: 20, // m — une bonne ligne LOINTAINE vaut moins (continu)
  },

  // Recul (bond arriere) et harcelement (la fenetre de tir des archers)
  recul: { saut: 8 }, // m — le bond de decrochage, front au danger
  harcelement: {
    standoff: 35, // m — la distance de volee que l unite qui tire veut tenir
    pres: 22,     // m — l ennemi cru a moins : un bond de recul (relance)
  },

  // Charge — l'élan : la distance visée quand on charge une DIRECTION
  // (l'ennemi cru prime toujours) ; le sprint viendra du ❤️ Corps
  charge: { elan: 15 }, // m

  // Index spatial (🌍)
  tailleCaseIndex: 2,                             // m

  // Répulsions douces (⚙️)
  repulsionHommes: { portee: 0.5, intensite: 2.0 }, // portee < espacement du cercle de discussion, sinon oscillation physique/brain
  repulsionCheval: { facteurIntensite: 2.5, porteeSup: 0.6 }, // autour d'un cheval : champ plus fort (x) et plus long (+m) — un homme ne se colle pas a la monture
  repulsionMurs: { portee: 0.8, intensite: 3.0 },
  repulsionGisants: { portee: 0.4, intensite: 0.8 }, // on enjambe les morts, on ne les pietine pas — doucement : un cadavre n ecarte pas une melee

  // Navigation
  tailleCaseNav: 0.5,      // m — un homme doit passer dans une case libre
  seuilWaypoint: 0.3,      // m — waypoint considéré atteint

  // Temps
  dtFixe: 1 / 60,          // s sim par pas
};
