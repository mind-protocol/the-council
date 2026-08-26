(() => {
"use strict";

const URLS = {
  homme:"/bataille?volet=homme",
  c1:"/bataille?volet=scene&epreuve=ordre-unite&action=poser&menu=ferme&zoom=0.72",
  c2:"/bataille?volet=scene&epreuve=croisement-amis&action=poser&menu=ferme&zoom=0.76",
  c3:"/bataille?volet=scene&epreuve=succession&action=poser&menu=ferme&zoom=0.76",
  c4:"/bataille?volet=scene&epreuve=messagers&action=poser&menu=ferme&zoom=0.62",
  c5:"/bataille?volet=scene&epreuve=rassemblement-armee&action=poser&menu=ferme&zoom=0.48",
  c6:"/bataille?volet=scene&epreuve=bataille-rangee-naive&action=poser&menu=ferme&zoom=0.52",
  c7:"/bataille?volet=scene&epreuve=ratissage-ville&action=poser&menu=ferme&zoom=0.63",
  sol:"/bataille?volet=scene&epreuve=sol&action=poser&menu=ferme&masque=1&zoom=0.78",
  contact:"/bataille?volet=scene&epreuve=contact&action=poser&menu=ferme&zoom=0.80",
  letalite:"/bataille?volet=scene&epreuve=letalite&action=poser&menu=ferme&zoom=0.80",
  rythme:"/bataille?volet=scene&epreuve=rythme&action=poser&menu=ferme&zoom=0.80",
  recul:"/bataille?volet=scene&epreuve=recul&action=poser&menu=ferme&zoom=0.80",
  rupture:"/bataille?volet=scene&epreuve=rupture-unite&action=poser&menu=ferme&zoom=0.78",
  presse:"/bataille?volet=scene&epreuve=presse&action=poser&menu=ferme&zoom=0.82",
  dragon:"/bataille?volet=scene&epreuve=dragon-survol&action=poser&menu=ferme&zoom=0.58",
  dragonOuvert:"/bataille?volet=scene&epreuve=dragon-bataille-rangee-ouverte&action=poser&menu=ferme&zoom=0.58",
  feu:"/bataille?volet=scene&epreuve=incendie-ville&action=poser&menu=ferme&zoom=0.62",
  guet:"/bataille?volet=scene&epreuve=guet-retraite&action=poser&menu=ferme&zoom=0.18",
};

const CATEGORIES = {
  physique:{ nom:"Physique", emoji:"🔵", couleur:"var(--physique)" },
  individu:{ nom:"Individu", emoji:"🟢", couleur:"var(--individu)" },
  collectif:{ nom:"Collectif", emoji:"🟣", couleur:"var(--collectif)" },
  commandement:{ nom:"Commandement", emoji:"🟠", couleur:"var(--commandement)" },
  mission:{ nom:"Mission", emoji:"🔴", couleur:"var(--mission)" },
  observation:{ nom:"Observation", emoji:"🟡", couleur:"var(--observation)" },
};

const VIZ = {
  directe:{ nom:"✅ Viz directe", couleur:"var(--directe)" },
  indirecte:{ nom:"◐ Viz indirecte", couleur:"var(--indirecte)" },
  absente:{ nom:"✕ Viz absente", couleur:"var(--absente)" },
};

const F = (id, categorie, emoji, nom, existe, sources, viz, dependances, plus) =>
  Object.assign({ id, categorie, emoji, nom, existe, sources, viz,
    dependances:dependances || [] }, plus || {});

// INVENTAIRE DU CODE ACTUEL. Les directions de refactor ne sont jamais des
// nœuds : elles décrivent seulement pourquoi une feature existante est rayée.
const FEATURES = [
  F("PHY-SOL", "physique", "🗺️", "Sol franchissable et obstacles",
    "Le même masque répond à la pose, au déplacement, au pathfinding et à l’occlusion. Une épreuve peut substituer sa propre fonction de terrain.",
    ["bataille2d.js · libreEn(), obstacleEn(), reglerTerrainEpreuve()", "plan2d.json + masque.bin"],
    {status:"directe", url:URLS.sol, label:"Masque de collision", observe:"Le masque peut être superposé à la carte ; les corps et leurs routes doivent rester dans les zones libres."}),

  F("PHY-LOCOMOTION", "physique", "🏃", "Locomotion, accélération et freinage",
    "La vitesse réelle rattrape une allure demandée avec accélération, freinage, fatigue et souplesse. L’orientation de l’arme ne pivote pas instantanément avec les pieds.",
    ["bataille2d.js · versLe(), tourner(), vigueur()"],
    {status:"indirecte", url:URLS.c1, label:"Marche d’une vintaine", observe:"La trajectoire et les vitesses se voient ; les valeurs exactes demandent encore le survol ou une sonde."}, ["PHY-SOL"]),

  F("PHY-COLLISION", "physique", "🫸", "Encombrement, séparation et presse",
    "Les corps se repoussent localement, produisent une presse mesurée et projettent leur séparation sur la voie quand ils sont dans une rue.",
    ["bataille2d.js · eloigner(), h.presse"],
    {status:"directe", url:URLS.presse, label:"Épreuve de presse", observe:"Le bouchon, la densité et les hommes sans issue sont visibles et mesurés."}, ["PHY-SOL", "PHY-LOCOMOTION"]),

  F("PHY-PASSAGE", "physique", "↔️", "Cession locale de passage",
    "Un homme immobile se décale devant un allié qui avance. Le déplacement et l’identité de celui à qui il a cédé restent dans son diagnostic.",
    ["bataille2d.js · eloigner()", "h.cedePourChef, h.cedeDistance"],
    {status:"indirecte", url:URLS.c2, label:"Croisement de groupes alliés", observe:"Le mouvement est visible ; le bénéficiaire et la distance cédée apparaissent au survol."}, ["PHY-COLLISION"],
    {specifique:true, probleme:"Le coefficient devient plus fort sur le booléen « chef ». Une relation de commandement modifie donc directement la poussée corporelle.", direction:"Conserver une seule mécanique de cession fondée sur le mouvement, l’encombrement et une priorité sociale explicite ; le rang ne doit pas être une branche de collision."}),

  F("PHY-HUIS", "physique", "🚪", "Franchissement des huis et intérieurs",
    "Des hommes peuvent viser une porte, suivre une trace locale, franchir le seuil, occuper un intérieur et ressortir par le même huis.",
    ["bataille2d.js · cheminDePorte(), franchirHuis(), sortirParHuis()"],
    {status:"directe", url:URLS.c7, label:"Maisons du ratissage", observe:"Les files devant les portes, les entrées, les corps à l’intérieur et les sorties sont visibles."}, ["PHY-SOL", "PHY-COLLISION"],
    {specifique:true, probleme:"La topologie porte ↔ intérieur et son pathfinding local vivent dans le bloc du ratissage. Une autre mission ne peut pas entrer dans un bâtiment sans réutiliser cette mission.", direction:"Faire du huis un portail général du monde ; le ratissage ne devrait fournir que la destination et le nombre d’hommes."}),

  F("PHY-ARMES", "physique", "🗡️", "Allonge, garde et orientation des armes",
    "Chaque arme porte une allonge, une cadence, un dégât et une garde. Le fer a une orientation actuelle et une orientation désirée, reliées par une vitesse de pivot.",
    ["bataille/mesures.js", "bataille2d.js · tourner(), frapper()"],
    {status:"directe", url:URLS.contact, label:"Contact et fers dessinés", observe:"Les traits d’armes, l’orientation, l’entrée en mesure et les frappes sont visibles."}, ["PHY-LOCOMOTION"]),

  F("PHY-MONTURE", "physique", "🐎", "Monture de combat",
    "Une monture augmente l’encombrement visible, l’allure et l’accélération du mouvement déjà choisi ; elle n’invente aucune destination.",
    ["bataille2d.js · montureCombat, versLe()", "bataille/roster.js"],
    {status:"indirecte", url:URLS.c6, label:"Cavalerie de C6", observe:"L’ovale orienté et la vitesse sont visibles, mais il n’existe pas encore de cadran cinématique dédié."}, ["PHY-LOCOMOTION", "PHY-COLLISION"]),

  F("PHY-PIQUE", "physique", "🔱", "Pique et restitution de l’élan",
    "La pique est une arme longue et lente. Le surcroît contre un cavalier n’existe que si la pointe fait face, si le piquier est presque planté et si la monture arrive encore lancée.",
    ["bataille2d.js · frapper() / contreCharge"],
    {status:"indirecte", url:URLS.c6, label:"Piquiers contre cavaliers", observe:"Les hampes et les contacts se voient ; le compteur de contre-charges est dans les sondes."}, ["PHY-ARMES", "PHY-MONTURE"]),

  F("PHY-FEU", "physique", "🔥", "Propagation du feu urbain",
    "La chaleur déposée sur les bâtiments, leur dose, le vent, la fumée et les foyers secondaires évoluent indépendamment des missions militaires.",
    ["bataille/incendie-ville.js", "bataille2d.js · signalerIncendies()"],
    {status:"directe", url:URLS.feu, label:"Épreuve F1", observe:"Toits, chaleur, fumée, vent et sauts de feu possèdent leur couche visuelle."}, ["PHY-SOL"]),

  F("PHY-DRAGON", "physique", "🐉", "Vol, virage et empreinte du souffle",
    "Le dragon suit une trajectoire continue, avec profil de vol. Le cône 3D du souffle est intersecté avec le sol et dépose une dose thermique sur son empreinte réelle.",
    ["bataille/dragons.js · intersectionConeSol(), deposerChaleur()"],
    {status:"directe", url:URLS.dragon, label:"Épreuve D1", observe:"Path aérien, altitude, passage et empreinte conique restent dessinés."}, ["PHY-FEU"]),

  F("PHY-SON", "physique", "📣", "Propagation locale du bruit et des rumeurs",
    "La bataille entretient un maillage sonore et des foyers de rumeur qui propagent cris, panique et nouvelles dans l’espace.",
    ["bataille2d.js · MAILLE_SON, sillage(), rumeur()"],
    {status:"absente", url:URLS.guet, label:"Contexte urbain seulement", observe:"Les conséquences sont visibles dans la foule, mais aucun front d’onde ni chemin de transmission n’est actuellement dessiné."}, ["PHY-SOL"]),

  F("IND-CORPS", "individu", "🫀", "Couche 1 — corps",
    "Le corps accumule exposition, charge nerveuse, emprise, sang-froid et stimuli entre deux battements, puis propose jambes et bras.",
    ["survival-stack/1-corps.js", "bataille/corps-adapt.js"],
    {status:"directe", url:URLS.homme, label:"Banc d’un homme", observe:"Les cadrans et le journal montrent chaque stimulus et la réponse corporelle."}, ["PHY-COLLISION", "PHY-ARMES"]),

  F("IND-REFLEXION", "individu", "🧭", "Couche 2 — réflexion locale",
    "L’homme compte appuis et menaces, mesure son état et son dégagement réel derrière lui, puis propose tenir, attendre ou céder.",
    ["survival-stack/2-reflexion.js", "bataille/reflexion-adapt.js"],
    {status:"directe", url:URLS.recul, label:"Survol + épreuve de recul", observe:"La fiche montre idée, tenue, attente, appui et dégagement ; l’épreuve montre la sortie physique."}, ["IND-CORPS", "PHY-SOL"]),

  F("IND-INTERPRETATION", "individu", "🪞", "Couche 3 — manière d’agir",
    "La place, le goût de serrer, la hâte et le respect de la lettre composent la manière dont cet homme interprète une situation ou improvise.",
    ["survival-stack/3-interpretation.js", "bataille2d.js · h.l3"],
    {status:"indirecte", url:URLS.c1, label:"Fiche individuelle", observe:"Les quatre composantes et la manière sont visibles au survol, sans cadran dédié sur la carte."}, ["IND-CORPS"]),

  F("IND-ENVIE", "individu", "🧲", "Couche 4 — envie et patience",
    "L’envie intervient dans la convoitise et dans le temps pendant lequel un chef supporte le silence avant de prendre une initiative.",
    ["survival-stack/4-envie.js", "bataille2d.js · initiative()"],
    {status:"indirecte", url:URLS.c3, label:"Succession et initiative", observe:"La valeur d’envie est visible au survol ; son effet temporel n’a pas encore de chronologie dédiée."}, ["IND-INTERPRETATION"]),

  F("IND-ARBITRAGE", "individu", "⚖️", "Couche 5 — qui conduit",
    "L’arbitre choisit quelle proposition conduit les jambes et les bras. Une doctrine reste un candidat et ne remplace pas la pile.",
    ["survival-stack/5-qui-conduit.js", "bataille2d.js · executerReflexion()"],
    {status:"indirecte", url:URLS.c6, label:"Pensée et conducteur au survol", observe:"Le gagnant et sa phrase sont lisibles homme par homme ; la compétition entre candidats n’est pas dessinée."}, ["IND-CORPS", "IND-REFLEXION", "IND-INTERPRETATION", "IND-ENVIE"]),

  F("IND-PENSEE", "individu", "💭", "Trace de pensée",
    "Chaque homme conserve l’action qu’il essaie, sa cause immédiate, le système qui conduit et deux pensées précédentes.",
    ["bataille2d.js · penser(), memoriserPerception()"],
    {status:"directe", url:URLS.c1, label:"Bulle de pensée au survol", observe:"La phrase « j’essaie de X parce que Y » et son système sont affichés."}, ["IND-ARBITRAGE"]),

  F("IND-REPOS", "individu", "😮‍💨", "Souffle et repos social",
    "La fatigue réduit allure et accélération. Voir des voisins reprendre leur souffle augmente la probabilité de s’arrêter ; voir l’ennemi souffler pèse davantage.",
    ["bataille2d.js · souffle(), vigueur(), repos()"],
    {status:"directe", url:URLS.rythme, label:"Épreuve de rythme", observe:"Les respirations collectives, reprises et durées de bout sont visibles et mesurées."}, ["IND-CORPS", "PHY-LOCOMOTION"]),

  F("COL-APPARTENANCE", "collectif", "🫂", "Appartenance à sa propre unité",
    "Chaque homme garde sa formation, son escouade, son aile et son corps. Croiser des alliés ne change pas ceux qu’il considère comme les siens.",
    ["bataille2d.js · formation, escouade, aile, corps"],
    {status:"directe", url:URLS.c2, label:"Épreuve C2", observe:"Les liens au propre chef et les deux groupes qui se traversent sont visibles."}, ["IND-PENSEE"]),

  F("COL-GUIDE", "collectif", "🚩", "Guide vivant de la formation",
    "Le chef de formation conduit. S’il tombe, un successeur est élu dans l’unité sans effacer la destination commune.",
    ["bataille2d.js · guideDe(), successeur()"],
    {status:"directe", url:URLS.c3, label:"Épreuve C3", observe:"La chute, la reprise du guide et la conservation du but sont visibles et sondées."}, ["COL-APPARTENANCE"]),

  F("COL-ROUTE", "collectif", "🪢", "Route mutualisée par formation",
    "Une seule route est calculée par le guide ou l’échelon parent. Les membres suivent la trace et prennent leur recul sur elle au lieu de recalculer A*.",
    ["bataille2d.js · calculerRouteFormation(), suivreRouteRalliement()"],
    {status:"directe", url:URLS.c1, label:"Route C1", observe:"La trace est dessinée et la sonde compte exactement les calculs A*."}, ["PHY-SOL", "COL-GUIDE"]),

  F("COL-PLACEMENT", "collectif", "📐", "Places relatives dans la vintaine",
    "Les hommes cherchent une place relative au chef, actuellement dérivée de quatre files sur cinq rangs puis assouplie par la route, la cohésion et le terrain.",
    ["bataille2d.js · FILES_VINTAINE, placeDeFormation(), suivreGuideDirect()"],
    {status:"directe", url:URLS.c5, label:"Rassemblement C5", observe:"Les liens, les rangs et la déformation autour des obstacles sont visibles."}, ["COL-GUIDE", "COL-ROUTE", "PHY-COLLISION"],
    {specifique:true, probleme:"Le repère de base est encore un pochoir 4 × 5. Même s’il se déforme, l’ordre des cases préexiste à la situation et réapparaît comme un damier.", direction:"Conserver appartenance, voisinage, face, espacement et profondeur comme contraintes continues ; aucune case individuelle ne devrait exister avant le mouvement."}),

  F("COL-COHESION", "collectif", "🪢", "Cohésion et allure du guide",
    "L’étirement de la troupe ralentit dynamiquement le guide ; les suiveurs accélèrent ou attendent selon leur place et la distance des leurs.",
    ["bataille2d.js · allureDuGuide(), suivreGuideDirect()"],
    {status:"indirecte", url:URLS.c1, label:"Marche C1", observe:"Les variations d’allure se voient et la cohésion est mesurée, mais sa distribution n’a pas encore de surcouche."}, ["COL-PLACEMENT"]),

  F("COL-RUPTURE", "collectif", "🏳️", "Rupture et ralliement d’unité",
    "La rupture individuelle peut devenir collective selon la situation locale. Les survivants cherchent une protection ou leur bannière et peuvent se rallier.",
    ["bataille2d.js · jugerRuptureUnite(), appliquerRuptureUnite(), rallier()"],
    {status:"directe", url:URLS.rupture, label:"Épreuve de rupture", observe:"La propagation, les caps de fuite, les bannières et les ralliés sont visibles et comptés."}, ["IND-REFLEXION", "COL-APPARTENANCE"]),

  F("CMD-HIERARCHIE", "commandement", "👑", "Hiérarchie de commandement",
    "Le moteur connaît corps, ailes, escouades, chefs de corps, centeniers et chefs de formation. Un supérieur place ses chefs, pas directement tous leurs hommes.",
    ["bataille2d.js · ailes, escouades, echelons()", "bataille/commandement.js · formerEchelon()"],
    {status:"directe", url:URLS.c5, label:"Épreuve C5", observe:"Drapeaux, chefs nommés, liens de subordination et places d’échelon sont visibles."}, ["COL-APPARTENANCE", "COL-GUIDE"]),

  F("CMD-ORDRE", "commandement", "💬", "Ordre littéral reçu",
    "Une unité et une mémoire de commandant conservent la phrase reçue, sa version et son heure. Les hommes portent les mêmes mots jusqu’à un nouvel ordre.",
    ["bataille2d.js · ordonnerFormation(), marquerOrdreRecu()", "bataille/commandement.js · recevoirOrdre()"],
    {status:"directe", url:URLS.c1, label:"Ordre C1", observe:"La phrase prononcée apparaît au chef puis dans les fiches individuelles."}, ["CMD-HIERARCHIE"]),

  F("CMD-TRANSMISSION", "commandement", "🏃", "Bannières et coureurs",
    "Les signaux simples peuvent passer par bannière si elle est visible. Un ordre précis exige un coureur qui retrouve le destinataire actuel et peut tomber en route.",
    ["bataille2d.js · transmettre(), envoyerCoureur(), courir()"],
    {status:"directe", url:URLS.c4, label:"Épreuve C4", observe:"Les coureurs ont un halo, portent une phrase et visent la position vivante de leur destinataire."}, ["CMD-ORDRE", "PHY-LOCOMOTION", "PHY-SON"]),

  F("CMD-INITIATIVE", "commandement", "🧠", "Initiative après silence ou ordre périmé",
    "Un chef sans nouvelles attend selon sa patience, puis reprend une consigne, reconstruit depuis l’intention ou retombe sur sa manière propre. Le motif est écrit dans les annales.",
    ["bataille2d.js · initiative(), DE_LINTENTION"],
    {status:"absente", url:URLS.c3, label:"Contexte de succession", observe:"Le nouvel ordre peut apparaître en bulle, mais la durée du silence, les candidats et le déclenchement ne sont pas visualisés ensemble."}, ["CMD-ORDRE", "IND-ENVIE", "IND-INTERPRETATION"]),

  F("CMD-PERCEPTION", "commandement", "👁️", "Champ de vision du commandant",
    "Toutes les cinq secondes, quarante-huit rayons sont arrêtés par le premier obstacle. Seuls les ennemis réellement visibles nourrissent la mémoire.",
    ["bataille/commandement.js · champVision(), visibleDansChamp()", "bataille2d.js · observerCommandants()"],
    {status:"directe", url:URLS.c6, label:"Carte subjective C6", observe:"Sélectionner la carte d’un commandant affiche son polygone visible et les directions masquées."}, ["PHY-SOL"]),

  F("CMD-CROYANCES", "commandement", "🧠", "Faits, sources et croyances vieillissantes",
    "Les observations et rapports gardent auteur, source et date. Ils deviennent des croyances dont la confiance décroît ; une vieille rumeur ne remplace pas une vue directe plus récente.",
    ["bataille/commandement.js · assimiler(), confiance(), transmettre()"],
    {status:"directe", url:URLS.c6, label:"Carte subjective C6", observe:"Les zones d’incertitude, l’âge, la source et la confiance apparaissent dans la carte et les rapports."}, ["CMD-PERCEPTION", "CMD-TRANSMISSION"]),

  F("CMD-ESTIMATION", "commandement", "⚖️", "Estimation du rapport de force",
    "Chaque commandant somme ses seules croyances actives pour obtenir une fourchette ennemie, sa force propre, un rapport local et des signatures montées ou à longues hampes.",
    ["bataille/commandement.js · estimation()", "bataille2d.js · forcePropreCommandant()"],
    {status:"directe", url:URLS.c6, label:"Carte subjective C6", observe:"Les fourchettes et confiances sont inscrites près des contacts ; la fiche de rapport garde le total."}, ["CMD-CROYANCES"]),

  F("CMD-PAIRS", "commandement", "🤝", "Échange entre commandants de même rang",
    "Deux commandants de même rôle échangent uniquement s’ils se rencontrent à moins de onze mètres et si l’un détient un fait inconnu de l’autre.",
    ["bataille2d.js · observerCommandants() / VOIX_PAIRS", "bataille/commandement.js · inconnusPour(), transmettre()"],
    {status:"indirecte", url:URLS.c7, label:"Rencontres du ratissage", observe:"Les chefs et leurs bulles se voient ; le détail des faits échangés reste surtout dans le rapport de commandement."}, ["CMD-CROYANCES", "CMD-HIERARCHIE"]),

  F("CMD-CARTE", "commandement", "🕸️", "Carte et graphe tactiques subjectifs",
    "La carte est reconstruite depuis une mémoire : soi, objectif, alliés effectivement rencontrés, contacts estimés et relations observer, rapporter, pression, contester ou occuper l’axe.",
    ["bataille/commandement.js · grapheTactique()", "bataille2d.js · carteCommandant(), peindreCarteCommandant()"],
    {status:"directe", url:URLS.c6, label:"Surcouche sélectionnable", observe:"Au survol d’un commandant, le bouton de carte affiche polygone, croyances, icônes et flèches."}, ["CMD-CROYANCES", "CMD-ESTIMATION", "CMD-PAIRS", "CMD-ORDRE"]),

  F("MIS-RASSEMBLER", "mission", "🚩", "Rassembler une force",
    "Un seul appel planifie un repère supérieur, attribue les unités, place les échelons de chefs et diffuse l’ordre de retrouver les siens.",
    ["bataille2d.js · ordonnerRassemblement(), planifierRassemblement()"],
    {status:"directe", url:URLS.c5, label:"Épreuve C5", observe:"L’armée part mêlée puis les hommes, unités et chefs rejoignent leurs relations propres."}, ["CMD-HIERARCHIE", "COL-ROUTE", "COL-PLACEMENT"]),

  F("MIS-DEPLOYER", "mission", "📐", "Déployer ligne, soutien et réserve",
    "L’entrée publique de déploiement accepte actuellement une seule forme : ligne-soutien-réserve. Elle la transforme en secteurs et places d’échelons.",
    ["bataille2d.js · ordonnerDeploiement(), planifierRassemblement()"],
    {status:"directe", url:URLS.c6, label:"Déploiements de C6", observe:"Les deux forces et leurs trois profondeurs sont visibles sur le champ ouvert."}, ["MIS-RASSEMBLER"],
    {specifique:true, probleme:"La forme stratégique et le calcul spatial sont confondus dans un seul planificateur nommé. Ajouter une autre disposition oblige à ajouter une nouvelle branche de forme.", direction:"L’ordre peut demander frontage, profondeur, appuis et réserve ; le placement doit les résoudre contre l’espace libre et les voisins, sans imprimer un modèle nommé."}),

  F("MIS-ENGAGER", "mission", "⚔️", "Déplacer un dispositif pour engager",
    "Le repère supérieur est translaté vers un front. Les secteurs suivent et les unités reçoivent une phrase d’engagement ; les individus continuent à passer par leur pile complète.",
    ["bataille2d.js · deplacerDeploiement()"],
    {status:"directe", url:URLS.c6, label:"Bataille rangée C6", observe:"Les fronts avancent, les routes et les contacts physiques sont visibles."}, ["MIS-DEPLOYER", "CMD-ORDRE"]),

  F("MIS-RATISSER", "mission", "🏘️", "Ratisser un secteur urbain",
    "Les unités revendiquent des secteurs, choisissent une maison, forment une file, en font entrer quatre, fouillent, combattent un groupe éventuel, rapportent et reprennent la recherche.",
    ["bataille2d.js · ordonnerRatissage(), menerRatissage(), coordonnerRatissages()"],
    {status:"directe", url:URLS.c7, label:"Épreuve C7", observe:"Secteurs, maisons, files, entrées, combats, rapports et rendez-vous sont visibles."}, ["PHY-HUIS", "CMD-PAIRS", "CMD-CROYANCES", "COL-ROUTE"],
    {specifique:true, probleme:"La mission contient aussi des primitives générales : réservation d’une destination, file d’accès, portail, occupation d’un intérieur, rapport et fin de tâche.", direction:"Garder « fouiller les maisons de ce secteur » comme mission ; sortir accès, réservation, franchissement, occupation et compte rendu en facultés communes."}),

  F("MIS-ANTI-DRAGON", "mission", "🐉", "Ordre appris d’ouverture anti-dragon",
    "Un déploiement peut recevoir la phrase d’ouvrir les rangs, garder les chefs en vue et se rallier après le passage. L’ordre reste soumis à l’arbitrage individuel.",
    ["bataille2d.js · DOCTRINES, ordonnerDoctrineDeploiement(), executerDoctrine()"],
    {status:"directe", url:URLS.dragonOuvert, label:"Épreuve D4b", observe:"L’écartement, le passage du dragon, les hommes ayant exécuté et le ralliement sont visibles."}, ["CMD-ORDRE", "IND-ARBITRAGE", "PHY-DRAGON"],
    {specifique:true, probleme:"La phrase peut rester une doctrine historique, mais son exécution calcule directement une cible « ordre ouvert » et reconnaît le danger dragon.", direction:"La doctrine devrait demander moins de densité et moins d’exposition à un danger venant du ciel ; locomotion et placement devraient résoudre ces contraintes sans connaître le mot dragon."}),

  F("VIZ-ORDRES", "observation", "💬", "Bulles d’ordres prononcés",
    "La phrase littérale n’est dessinée que pendant qu’elle est dite ou juste après son changement, au-dessus du chef qui la porte.",
    ["bataille2d.js · ordreEnTrainDEtreDit(), peindreLesOrdres()"],
    {status:"directe", url:URLS.c1, label:"Ordre C1", observe:"La bulle apparaît au changement puis disparaît ; la fiche conserve ensuite la phrase."}, ["CMD-ORDRE"]),

  F("VIZ-PENSEES", "observation", "💭", "Inspection d’un combattant",
    "Le survol montre pensée, raisons, couches, traits, physique, ordre, appartenance, circulation et perceptions récentes.",
    ["bataille/inspection-page.js", "bataille2d.js · sousLeDoigt(), diagnostic()"],
    {status:"directe", url:URLS.c1, label:"Survol de C1", observe:"Pointer n’importe quel homme ouvre sa fiche ; le pointeur peut entrer dans la fiche sans la fermer."}, ["IND-PENSEE"]),

  F("VIZ-COMMANDEMENT", "observation", "🗺️", "Surcouche mentale du commandant",
    "Un bouton dans la fiche d’un commandant sélectionne sa carte subjective et la peint en transparence sur le monde réel.",
    ["bataille2d.js · selectionnerCarteCommandant(), peindreCarteCommandant()"],
    {status:"directe", url:URLS.c6, label:"Commandants de C6", observe:"Sélectionner un commandant puis sa carte ; recliquer la désactive."}, ["CMD-CARTE", "VIZ-PENSEES"]),

  F("VIZ-MARK", "observation", "📌", "Marque de bataille",
    "Depuis une fiche, un commentaire capture la zone, le diagnostic, la fin de l’historique perceptif et les rapports utiles dans un dossier autonome.",
    ["bataille/inspection-page.js", "serveur.js · POST /marque-bataille"],
    {status:"directe", url:URLS.c6, label:"Bouton Mark au survol", observe:"Ouvrir une fiche, cliquer Mark, commenter puis enregistrer ; le chemin sauvegardé est confirmé."}, ["VIZ-PENSEES", "VIZ-COMMANDEMENT"]),

  F("VIZ-EPREUVES", "observation", "🧪", "Épreuves et sondes reproductibles",
    "Chaque épreuve pose une scène déterministe, annonce ce qu’elle manipule, cadre la vue et compare les relevés à des conditions écrites.",
    ["bataille/scenarios.js", "bataille/page.js", "bataille/sondes-page.js"],
    {status:"directe", url:"/bataille?volet=scene", label:"Catalogue des épreuves", observe:"Chaque accordéon expose poser, mesurer, recadrer, attendu, mesure et verdict."}),

  F("VIZ-RAPPORTS", "observation", "📦", "Rapports structurés et bancs headless",
    "Le moteur exporte unités, commandements, croyances, ratissages, dynamique et diagnostics. Les bancs rejouent les mêmes scénarios sans écran.",
    ["bataille2d.js · etat(), unites(), rapportsCommandement(), diagnostic()", "bataille/banc-*.js"],
    {status:"indirecte", url:URLS.c6 + "&action=mesurer", label:"Sondes de C6", observe:"Les agrégats apparaissent dans les sondes ; le JSON complet reste aujourd’hui dans la console, les marks et les bancs."}, ["VIZ-EPREUVES", "CMD-CARTE"]),
];

const TARGET_STATUS = {
  existe:{ nom:"Déjà propriétaire", couleur:"var(--directe)" },
  melange:{ nom:"À extraire du four", couleur:"var(--indirecte)" },
  absent:{ nom:"Faculté générale absente", couleur:"var(--absente)" },
};

const T = (id, categorie, emoji, nom, niveaux, module, responsabilite,
  entrees, sorties, statut, etat, sources, position) => ({
    id, categorie, emoji, nom, niveaux, module, existe:responsabilite,
    entrees, sorties, statut, etat, sources, position,
  });

// TARGET LOGIQUE. Ces nœuds ne prétendent pas exister : ils indiquent quel
// module doit posséder chaque décision, et où la matière se trouve aujourd'hui.
const TARGETS = [
  T("TGT-STRATEGIE", "mission", "♛", "Stratégie", [15], "bataille/strategie.js",
    "Valoriser destruction, préservation, contrôle, temps et pertes acceptables, puis choisir ce que la bataille doit obtenir.",
    "situation politique, ressources, valeur des lieux et des personnes",
    "objectif stratégique pondéré et conditions d’abandon",
    "absent", "Les scénarios injectent un but ; aucun moteur ne le choisit ni ne le réévalue.",
    ["bataille/scenarios.js · objectifs injectés"], { col:2, row:1 }),

  T("TGT-CONDUITE", "commandement", "♜", "Conduite de la bataille", [14], "bataille/conduite.js",
    "Transformer l’objectif stratégique en axes, réserves, phases, échéances et responsabilités de commandement.",
    "objectif stratégique, forces disponibles, carte agrégée",
    "plan de bataille révisable et missions de commandants",
    "melange", "Rassemblement, déploiement et engagement existent, mais comme appels particuliers du four.",
    ["bataille2d.js · ordonnerRassemblement(), ordonnerDeploiement(), deplacerDeploiement()"], { col:2, row:2 }),

  T("TGT-COMMANDEMENT", "commandement", "🧠", "Carte mentale", [11], "bataille/commandement.js",
    "Conserver ce qu’un chef sait réellement : faits sourcés, croyances vieillissantes, estimation de force et graphe tactique subjectif.",
    "observations, rapports, ordre reçu et position du chef",
    "croyances, incertitudes, estimation et graphe tactique",
    "existe", "Ce module possède déjà clairement cette responsabilité et ne choisit volontairement aucune doctrine.",
    ["bataille/commandement.js · memoire(), assimiler(), estimation(), grapheTactique()"], { col:1, row:3 }),

  T("TGT-TACTIQUE", "commandement", "⚖️", "Décision tactique", [12], "bataille/tactique.js",
    "Construire plusieurs futurs plausibles, estimer leurs risques et récompenses, puis choisir un ordre sans reconnaître un scénario codé en dur.",
    "objectif local, carte mentale, capacités propres et options réalisables",
    "ordre choisi, raison, alternatives rejetées et prochain réexamen",
    "absent", "Quelques décisions particulières existent, mais aucun comparateur général de scénarios n’est propriétaire de ce niveau.",
    ["bataille2d.js · fragments dans deciderLesTetes(), donnerOrdreLocal()"], { col:2, row:3 }),

  T("TGT-COORDINATION", "commandement", "🤝", "Coordination entre pairs", [13], "bataille/coordination.js",
    "Échanger vécu, ordre courant et intention, proposer une répartition et résoudre les conflits entre commandants de même rang.",
    "mémoires des pairs, missions revendiquées et possibilité matérielle de parler",
    "engagements mutuels, zones revendiquées et faits transmis",
    "melange", "La faculté apparaît dans le ratissage, mais reste liée à cette mission et à ses secteurs.",
    ["bataille2d.js · echangerEntrePairs(), reglerConflits()", "bataille/commandement.js · transmettre()"], { col:3, row:3 }),

  T("TGT-ORDRES", "commandement", "📜", "Ordres", [8], "bataille/ordres.js",
    "Porter une phrase littérale, son auteur, ses destinataires, son objectif, ses contraintes, son urgence et ses conditions de péremption.",
    "décision d’un chef et contexte d’émission",
    "objet ordre stable, interprétable et traçable",
    "melange", "La phrase et son heure existent, mais leur contrat reste partagé entre le four et la mémoire de commandement.",
    ["bataille2d.js · ordonnerFormation(), marquerOrdreRecu()", "bataille/commandement.js · recevoirOrdre()"], { col:2, row:4 }),

  T("TGT-COMMUNICATION", "commandement", "🏃", "Communication", [9], "bataille/communication.js",
    "Déterminer si une information peut voyager, par quel support, avec quel délai, quelle déformation et quel accusé de réception.",
    "message, émetteur, destinataire, terrain, portée et porteurs disponibles",
    "livraison, échec, retard ou message déformé",
    "melange", "Coureurs, bannières et échanges de faits fonctionnent, mais n’ont pas encore de propriétaire commun.",
    ["bataille2d.js · transmettre(), envoyerCoureur(), courir()", "bataille/commandement.js · transmettre()"], { col:3, row:4 }),

  T("TGT-OBJECTIFS", "mission", "🎯", "Objectifs et missions", [10], "bataille/objectifs.js + bataille/missions/*",
    "Faire vivre détruire, contrôler et empêcher jusqu’à satisfaction, impossibilité ou péremption, puis produire la prochaine tâche utile.",
    "ordre reçu, état du monde, état de l’unité et faits nouveaux",
    "tâche courante, condition de succès et prochain comportement par défaut",
    "absent", "Les boucles rassembler, engager et ratisser existent séparément ; leur moteur commun n’existe pas.",
    ["bataille2d.js · ordonnerRassemblement(), menerFormation(), menerRatissage()"], { col:2, row:5 }),

  T("TGT-UNITES", "collectif", "🫂", "Unités", [5, 7], "bataille/unites.js",
    "Posséder l’appartenance, la hiérarchie, le guide vivant, l’effectif, la dispersion, la fatigue et la capacité collective courante.",
    "hommes, liens d’appartenance et conséquences des actions",
    "état d’unité, chef actuel, cohésion et capacité d’exécution",
    "melange", "Le roster décrit les échelons, mais l’état vivant des unités reste porté par les hommes et le four.",
    ["bataille/roster.js · ECHELONS", "bataille2d.js · formation, escouade, aile, corps, successions()"], { col:2, row:6 }),

  T("TGT-FORMATION", "collectif", "📐", "Formation", [6], "bataille/formation.js",
    "Résoudre orientation, largeur, profondeur, voisinage, espacement et obstacles comme contraintes continues, sans distribuer de cases préfabriquées.",
    "état de l’unité, direction, espace libre et contraintes de mission",
    "cibles relatives souples, allure du guide et mesure de cohésion",
    "melange", "La cohésion et l’allure existent, mais autour d’un pochoir 4 × 5 encore contenu dans le four.",
    ["bataille2d.js · placeDeFormation(), allureDuGuide(), suivreGuideDirect()"], { col:3, row:6 }),

  T("TGT-INDIVIDU", "individu", "🫀", "Réaction individuelle", [4], "survival-stack/1-corps.js → 5-qui-conduit.js",
    "Faire proposer au corps, à la réflexion, à la manière et à l’envie plusieurs conduites, puis élire celle qui commande les jambes et les bras.",
    "perceptions, état du corps, ordre interprété et mémoire récente",
    "action individuelle élue et explication « parce que »",
    "existe", "La pile est chargée entièrement et possède déjà ses cinq couches ; l’adaptation bataille reste un raccord.",
    ["survival-stack/1-corps.js … 5-qui-conduit.js", "bataille/corps-adapt.js", "bataille/reflexion-adapt.js"], { col:2, row:7 }),

  T("TGT-PERCEPTION", "individu", "👁️", "Perception", [3], "bataille/perception.js + bataille/faits.js",
    "Transformer seulement les conséquences accessibles aux sens en observations datées, situées et incertaines.",
    "monde physique, position, orientation, sens et attention de l’observateur",
    "faits vus, entendus ou déduits, avec source et confiance initiale",
    "melange", "Le vocabulaire des faits est séparé, mais les capteurs individuels et ceux des commandants sont encore distribués.",
    ["bataille/faits.js", "bataille/corps-adapt.js", "bataille/reflexion-adapt.js", "bataille2d.js · observerCommandants()"], { col:1, row:8 }),

  T("TGT-ACTIONS", "individu", "🦶", "Gestes", [1], "bataille/actions.js",
    "Définir les demandes corporelles génériques : marcher, tourner, ralentir, frapper, parer, pousser, franchir ou céder.",
    "action élue, cible, direction, intensité et état corporel",
    "tentative de geste normalisée remise à la physique",
    "melange", "Les gestes fonctionnent, mais leur vocabulaire et leur exécution sont des fonctions internes du four.",
    ["bataille2d.js · versLe(), tourner(), frapper(), franchirHuis()"], { col:2, row:8 }),

  T("TGT-PHYSIQUE", "physique", "⚙️", "Physique et monde", [2], "bataille/physique.js + bataille/monde.js",
    "Appliquer sol, topologie, accélération, collisions, encombrement, portée, inertie, armes, montures, huis, feu et autres conséquences matérielles.",
    "tentatives de gestes et état matériel du monde",
    "nouvel état physique, contacts, blessures, déplacements et événements",
    "melange", "Les mesures spécialisées existent, mais le noyau matériel demeure majoritairement dans bataille2d.js.",
    ["bataille2d.js · libreEn(), eloigner(), versLe(), frapper()", "bataille/mesures.js", "bataille/incendie-ville.js", "bataille/dragons.js"], { col:2, row:9 }),
];

const TARGET_LINKS = [
  { de:"TGT-STRATEGIE", vers:"TGT-CONDUITE", type:"commande" },
  { de:"TGT-CONDUITE", vers:"TGT-TACTIQUE", type:"commande" },
  { de:"TGT-COMMANDEMENT", vers:"TGT-TACTIQUE", type:"information" },
  { de:"TGT-COORDINATION", vers:"TGT-TACTIQUE", type:"coordination" },
  { de:"TGT-TACTIQUE", vers:"TGT-ORDRES", type:"commande" },
  { de:"TGT-ORDRES", vers:"TGT-COMMUNICATION", type:"commande" },
  { de:"TGT-COMMUNICATION", vers:"TGT-OBJECTIFS", type:"commande" },
  { de:"TGT-OBJECTIFS", vers:"TGT-UNITES", type:"commande" },
  { de:"TGT-UNITES", vers:"TGT-FORMATION", type:"commande" },
  { de:"TGT-FORMATION", vers:"TGT-INDIVIDU", type:"commande" },
  { de:"TGT-INDIVIDU", vers:"TGT-ACTIONS", type:"commande" },
  { de:"TGT-ACTIONS", vers:"TGT-PHYSIQUE", type:"commande" },
  { de:"TGT-PHYSIQUE", vers:"TGT-PERCEPTION", type:"retour" },
  { de:"TGT-PERCEPTION", vers:"TGT-INDIVIDU", type:"retour" },
  { de:"TGT-PERCEPTION", vers:"TGT-COMMANDEMENT", type:"retour" },
  { de:"TGT-UNITES", vers:"TGT-COMMANDEMENT", type:"retour" },
  { de:"TGT-COMMUNICATION", vers:"TGT-COMMANDEMENT", type:"retour" },
  { de:"TGT-COMMANDEMENT", vers:"TGT-COORDINATION", type:"coordination" },
];

const $ = (id) => document.getElementById(id);
const parId = new Map(FEATURES.concat(TARGETS).map((f) => [f.id, f]));
let vue = new URL(location.href).searchParams.get("vue") === "target" ? "target" : "existant";
let filtre = "tous";
let selection = null;
let commentaires = [];

function correspond(f) {
  if (filtre === "tous") return true;
  if (CATEGORIES[filtre]) return f.categorie === filtre;
  if (filtre === "specifique") return !!f.specifique;
  if (filtre === "viz-insuffisante") return f.viz.status !== "directe";
  return true;
}

function compteCommentaires(id) {
  return commentaires.filter((c) => c.feature === id).length;
}

function noeud(f) {
  const b = document.createElement("button");
  b.type = "button"; b.className = "noeud" + (f.specifique ? " specifique" : "") +
    (selection === f.id ? " selectionne" : "");
  b.dataset.feature = f.id;
  b.style.setProperty("--couleur", CATEGORIES[f.categorie].couleur);
  b.style.setProperty("--viz", VIZ[f.viz.status].couleur);
  b.setAttribute("aria-label", f.id + " — " + f.nom);

  const haut = document.createElement("span"); haut.className = "noeudHaut";
  const code = document.createElement("code"); code.textContent = f.id;
  const em = document.createElement("span"); em.textContent = f.emoji;
  haut.append(code, em);
  const nom = document.createElement("span"); nom.className = "noeudNom"; nom.textContent = f.nom;
  const bas = document.createElement("span"); bas.className = "noeudBas";
  const viz = document.createElement("span"); viz.className = "vizPoint";
  viz.textContent = VIZ[f.viz.status].nom;
  const n = document.createElement("span"); n.className = "commentairesCompte";
  const total = compteCommentaires(f.id);
  n.textContent = total ? "💬 " + total : f.specifique ? "⚠ spécifique" : "";
  bas.append(viz, n);
  b.append(haut, nom, bas);
  b.addEventListener("click", () => choisir(f.id, true));
  return b;
}

function noeudTarget(f) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "noeud targetNoeud" + (selection === f.id ? " selectionne" : "");
  b.dataset.feature = f.id;
  b.style.gridColumn = String(f.position.col);
  b.style.gridRow = String(f.position.row);
  b.style.setProperty("--couleur", CATEGORIES[f.categorie].couleur);
  b.style.setProperty("--statut", TARGET_STATUS[f.statut].couleur);
  b.setAttribute("aria-label", f.nom + " — " + f.module);

  const haut = document.createElement("span"); haut.className = "noeudHaut";
  const niveaux = document.createElement("code");
  niveaux.textContent = f.niveaux.map((n) => "N" + n).join(" + ");
  const em = document.createElement("span"); em.textContent = f.emoji;
  haut.append(niveaux, em);
  const nom = document.createElement("span"); nom.className = "noeudNom"; nom.textContent = f.nom;
  const module = document.createElement("span"); module.className = "targetModule"; module.textContent = f.module;
  const bas = document.createElement("span"); bas.className = "noeudBas";
  const statut = document.createElement("span"); statut.className = "targetStatut";
  statut.textContent = TARGET_STATUS[f.statut].nom;
  const total = document.createElement("span"); total.className = "commentairesCompte";
  const n = compteCommentaires(f.id); total.textContent = n ? "💬 " + n : "";
  bas.append(statut, total);
  b.append(haut, nom, module, bas);
  b.addEventListener("click", () => choisir(f.id, true));
  return b;
}

function rendreGraphe() {
  const colonnes = $("colonnes"); colonnes.replaceChildren();
  colonnes.className = vue === "target" ? "target" : "";
  if (vue === "target") {
    TARGETS.forEach((f) => colonnes.appendChild(noeudTarget(f)));
    requestAnimationFrame(dessinerLiens);
    return;
  }
  for (const [id, cat] of Object.entries(CATEGORIES)) {
    const fs = FEATURES.filter((f) => f.categorie === id && correspond(f));
    if (!fs.length) continue;
    const col = document.createElement("section"); col.className = "colonne";
    col.style.setProperty("--couleur", cat.couleur);
    const titre = document.createElement("h2"); titre.textContent = cat.emoji + " " + cat.nom;
    const ns = document.createElement("div"); ns.className = "noeuds";
    fs.forEach((f) => ns.appendChild(noeud(f)));
    col.append(titre, ns); colonnes.appendChild(col);
  }
  requestAnimationFrame(dessinerLiens);
}

function dessinerLiens() {
  const svg = $("liens"), colonnes = $("colonnes");
  const base = colonnes.getBoundingClientRect();
  const largeur = colonnes.scrollWidth, hauteur = colonnes.scrollHeight;
  svg.setAttribute("width", largeur); svg.setAttribute("height", hauteur);
  svg.setAttribute("viewBox", `0 0 ${largeur} ${hauteur}`);
  svg.replaceChildren();
  const ns = "http://www.w3.org/2000/svg";
  const defs = document.createElementNS(ns, "defs");
  const marker = document.createElementNS(ns, "marker");
  marker.setAttribute("id", "flecheArchitecture"); marker.setAttribute("viewBox", "0 0 8 8");
  marker.setAttribute("refX", "7"); marker.setAttribute("refY", "4");
  marker.setAttribute("markerWidth", "5"); marker.setAttribute("markerHeight", "5");
  marker.setAttribute("orient", "auto-start-reverse");
  const pointe = document.createElementNS(ns, "path"); pointe.setAttribute("d", "M0,0 L8,4 L0,8 z");
  pointe.setAttribute("fill", "#746b61"); marker.appendChild(pointe); defs.appendChild(marker); svg.appendChild(defs);

  const liens = vue === "target" ? TARGET_LINKS : FEATURES.filter(correspond)
    .flatMap((f) => f.dependances.map((dep) => ({ de:dep, vers:f.id, type:"dependance" })));
  for (const lien of liens) {
    const a = colonnes.querySelector(`[data-feature="${lien.de}"]`);
    const b = colonnes.querySelector(`[data-feature="${lien.vers}"]`);
    if (!a || !b) continue;
    const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    const acx = ra.left - base.left + ra.width / 2;
    const acy = ra.top - base.top + ra.height / 2;
    const bcx = rb.left - base.left + rb.width / 2;
    const bcy = rb.top - base.top + rb.height / 2;
    const vertical = vue === "target" && Math.abs(bcy - acy) > Math.abs(bcx - acx) * .7;
    let x1, y1, x2, y2, d;
    if (vertical) {
      const descend = bcy >= acy;
      x1 = acx; x2 = bcx;
      y1 = (descend ? ra.bottom : ra.top) - base.top;
      y2 = (descend ? rb.top : rb.bottom) - base.top;
      const courbe = Math.max(18, Math.abs(y2 - y1) * .42);
      d = `M${x1},${y1} C${x1},${y1 + (descend ? courbe : -courbe)} ${x2},${y2 - (descend ? courbe : -courbe)} ${x2},${y2}`;
    } else {
      x1 = ra.right - base.left; y1 = acy;
      x2 = rb.left - base.left; y2 = bcy;
      if (x2 < x1) { x1 = ra.left - base.left; x2 = rb.right - base.left; }
      const courbe = Math.max(22, Math.abs(x2 - x1) * .42);
      d = `M${x1},${y1} C${x1 + (x2 >= x1 ? courbe : -courbe)},${y1} ${x2 - (x2 >= x1 ? courbe : -courbe)},${y2} ${x2},${y2}`;
    }
    const p = document.createElementNS(ns, "path");
    const couleurs = { commande:"#a98343", retour:"#579ac0", coordination:"#9a80cb", dependance:"#5d5750" };
    const actif = selection === lien.de || selection === lien.vers;
    p.setAttribute("d", d); p.setAttribute("fill", "none");
    p.setAttribute("stroke", couleurs[lien.type] || couleurs.dependance);
    p.setAttribute("stroke-width", actif ? "3" : vue === "target" ? "2.2" : "1");
    p.setAttribute("opacity", actif ? ".98" : vue === "target" ? ".82" : ".32");
    if (lien.type === "retour") p.setAttribute("stroke-dasharray", "6 5");
    if (lien.type === "coordination") p.setAttribute("stroke-dasharray", "3 4");
    p.setAttribute("marker-end", "url(#flecheArchitecture)"); svg.appendChild(p);
  }
}

function etiquettes(f) {
  const zone = $("ficheEtiquettes"); zone.replaceChildren();
  const niveau = document.createElement("span"); niveau.className = "etiquette niveau";
  niveau.style.setProperty("--couleur", CATEGORIES[f.categorie].couleur);
  niveau.textContent = CATEGORIES[f.categorie].emoji + " " + CATEGORIES[f.categorie].nom;
  zone.append(niveau);
  if (vue === "target") {
    const ns = document.createElement("span"); ns.className = "etiquette";
    ns.textContent = f.niveaux.map((n) => "Niveau " + n).join(" · ");
    const statut = document.createElement("span"); statut.className = "etiquette viz";
    statut.style.setProperty("--viz", TARGET_STATUS[f.statut].couleur);
    statut.textContent = TARGET_STATUS[f.statut].nom;
    zone.append(ns, statut);
    return;
  }
  const viz = document.createElement("span"); viz.className = "etiquette viz";
  viz.style.setProperty("--viz", VIZ[f.viz.status].couleur); viz.textContent = VIZ[f.viz.status].nom;
  zone.append(viz);
  if (f.specifique) {
    const s = document.createElement("span"); s.className = "etiquette alerte";
    s.textContent = "⚠ système trop spécifique"; zone.appendChild(s);
  }
}

function afficherHistorique(id) {
  const zone = $("historiqueCommentaires"); zone.replaceChildren();
  const xs = commentaires.filter((c) => c.feature === id).slice(0, 5);
  if (!xs.length) return;
  const titre = document.createElement("h3"); titre.textContent = "Commentaires enregistrés"; zone.appendChild(titre);
  for (const c of xs) {
    const d = document.createElement("div"); d.className = "commentairePasse";
    const t = document.createElement("time");
    const date = new Date(c.cree_a); t.textContent = Number.isNaN(date.valueOf()) ? c.cree_a : date.toLocaleString("fr-FR");
    const p = document.createElement("p"); p.textContent = c.commentaire;
    d.append(t, p); zone.appendChild(d);
  }
}

function remplirFiche(f) {
  $("ficheVide").hidden = true; $("ficheContenu").hidden = false;
  $("ficheEmoji").textContent = f.emoji; $("ficheId").textContent = f.id;
  $("ficheNom").textContent = f.nom; $("ficheExiste").textContent = f.existe;
  etiquettes(f);
  const cible = vue === "target";
  $("ficheResponsabiliteTitre").textContent = cible ? "Responsabilité propriétaire" : "Ce qui existe";
  $("blocEtatCible").hidden = !cible;
  $("blocContrat").hidden = !cible;
  $("blocVisualisation").hidden = cible;
  $("blocGeneraliser").hidden = !f.specifique;
  $("ficheProbleme").textContent = f.probleme || "";
  $("ficheDirection").textContent = f.direction || "";
  const ouvrir = $("ficheOuvrir");
  if (cible) {
    $("ficheEtatCible").textContent = TARGET_STATUS[f.statut].nom + " — " + f.etat;
    $("ficheEntrees").textContent = f.entrees;
    $("ficheSorties").textContent = f.sorties;
    ouvrir.hidden = true;
  } else {
    $("ficheViz").textContent = VIZ[f.viz.status].nom + " — " + f.viz.label + ".";
    $("ficheObserver").textContent = f.viz.observe;
    ouvrir.hidden = !f.viz.url; ouvrir.href = f.viz.url || "#";
    ouvrir.textContent = f.viz.status === "absente"
      ? "Ouvrir le contexte actuel dans /bataille ↗"
      : "Ouvrir cette preuve dans /bataille ↗";
  }
  const sources = $("ficheSources"); sources.replaceChildren();
  f.sources.forEach((s) => { const li = document.createElement("li"); li.textContent = s; sources.appendChild(li); });
  $("commentaire").placeholder = cible
    ? `Ex. ${f.id} : ce module devrait aussi recevoir…`
    : `Ex. ${f.id} : ${f.specifique ? "ce système devrait plutôt…" : "dans cette situation…"}`;
  $("statutCommentaire").textContent = compteCommentaires(f.id)
    ? compteCommentaires(f.id) + " commentaire(s) déjà enregistré(s)." : "";
  afficherHistorique(f.id);
}

function choisir(id, pousser) {
  const f = parId.get(id); if (!f) return;
  if ((vue === "target") !== TARGETS.includes(f)) return;
  selection = id;
  if (pousser) {
    const u = new URL(location.href); u.searchParams.set("feature", id);
    history.pushState(null, "", u);
  }
  rendreGraphe(); remplirFiche(f);
}

function rendreResume() {
  if (vue === "target") {
    const existants = TARGETS.filter((f) => f.statut === "existe").length;
    const melanges = TARGETS.filter((f) => f.statut === "melange").length;
    const absents = TARGETS.filter((f) => f.statut === "absent").length;
    $("resume").innerHTML = `<span><strong>${TARGETS.length}</strong> propriétaires cibles pour 15 niveaux</span>` +
      `<span><strong>${existants}</strong> déjà propriétaires</span>` +
      `<span class="resumeAlerte"><strong>${melanges}</strong> responsabilités à extraire</span>` +
      `<span class="resumeAlerte"><strong>${absents}</strong> facultés générales absentes</span>` +
      `<span class="fluxLegende"><i class="fluxTrait" style="--flux:#a98343"></i> ordre descendant</span>` +
      `<span class="fluxLegende"><i class="fluxTrait retour" style="--flux:#579ac0"></i> retour perçu</span>`;
    return;
  }
  const directes = FEATURES.filter((f) => f.viz.status === "directe").length;
  const insuffisantes = FEATURES.length - directes;
  const specifiques = FEATURES.filter((f) => f.specifique).length;
  $("resume").innerHTML = `<span><strong>${FEATURES.length}</strong> features existantes</span>` +
    `<span><strong>${directes}</strong> avec viz directe</span>` +
    `<span class="resumeAlerte"><strong>${insuffisantes}</strong> viz indirectes ou absentes</span>` +
    `<span class="resumeAlerte"><strong>${specifiques}</strong> systèmes à généraliser</span>`;
}

function appliquerVue(nouvelle, pousser) {
  vue = nouvelle === "target" ? "target" : "existant";
  selection = null;
  $("vues").querySelectorAll("button[data-vue]").forEach((b) =>
    b.classList.toggle("actif", b.dataset.vue === vue));
  $("filtres").hidden = vue === "target";
  $("graphe").classList.toggle("targetVue", vue === "target");
  $("graphe").setAttribute("aria-label", vue === "target"
    ? "Graphe de la target logique"
    : "Graphe des features existantes");
  $("surtitrePage").textContent = vue === "target"
    ? "Architecture visée · responsabilités adressables"
    : "Moteur actuel · inventaire adressable";
  $("introPage").textContent = vue === "target"
    ? "Du geste à la stratégie : chaque nœud nomme le module qui doit posséder la décision. Les flèches pleines descendent les ordres ; les pointillés remontent les conséquences perçues."
    : "Chaque nœud est une feature qui existe dans le code. Sa couleur dit à quel niveau elle vit ; son œil dit comment elle se vérifie aujourd’hui.";
  $("ficheVide").hidden = false; $("ficheContenu").hidden = true;
  $("ficheVide").querySelector("p").textContent = vue === "target"
    ? "Sélectionnez un module cible pour voir sa responsabilité, son contrat et ce qui reste à extraire."
    : "Sélectionnez une feature. Son identifiant restera dans l’URL.";
  if (pousser) {
    const u = new URL(location.href);
    if (vue === "target") u.searchParams.set("vue", "target");
    else u.searchParams.delete("vue");
    u.searchParams.delete("feature");
    history.pushState(null, "", u);
  }
  rendreResume(); rendreGraphe();
}

async function chargerCommentaires() {
  try {
    const r = await fetch("/architecture-bataille/commentaires");
    const doc = await r.json(); commentaires = Array.isArray(doc.commentaires) ? doc.commentaires : [];
    rendreGraphe(); if (selection) remplirFiche(parId.get(selection));
  } catch (e) {}
}

$("filtres").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-filtre]"); if (!b) return;
  filtre = b.dataset.filtre;
  $("filtres").querySelectorAll("button").forEach((x) => x.classList.toggle("actif", x === b));
  rendreGraphe();
});

$("vues").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-vue]"); if (!b || b.dataset.vue === vue) return;
  appliquerVue(b.dataset.vue, true);
});

$("enregistrer").addEventListener("click", async () => {
  const f = parId.get(selection), texte = $("commentaire").value.trim();
  if (!f) return;
  if (!texte) { $("statutCommentaire").textContent = "Écrivez un commentaire d’abord."; return; }
  $("enregistrer").disabled = true; $("statutCommentaire").textContent = "Enregistrement…";
  try {
    const r = await fetch("/architecture-bataille/commentaires", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({ feature:f.id, titre:f.nom, commentaire:texte,
        url:location.href, classification:f.categorie,
        visualisation:vue === "target" ? f.statut : f.viz.status }),
    });
    const doc = await r.json(); if (!r.ok) throw new Error(doc.erreur || "échec");
    commentaires.unshift(doc.commentaire); $("commentaire").value = "";
    $("statutCommentaire").textContent = "Enregistré dans " + doc.ecrit + ".";
    rendreGraphe(); remplirFiche(f);
  } catch (e) {
    $("statutCommentaire").textContent = "Échec : " + e.message;
  } finally { $("enregistrer").disabled = false; }
});

$("copier").addEventListener("click", async () => {
  const f = parId.get(selection); if (!f) return;
  const texte = `${f.id} — ${f.nom}\n${location.href}`;
  try { await navigator.clipboard.writeText(texte); $("statutCommentaire").textContent = "Référence copiée."; }
  catch (e) { $("statutCommentaire").textContent = texte; }
});

window.addEventListener("resize", () => requestAnimationFrame(dessinerLiens));
window.addEventListener("popstate", () => {
  const u = new URL(location.href);
  const nouvelle = u.searchParams.get("vue") === "target" ? "target" : "existant";
  if (nouvelle !== vue) appliquerVue(nouvelle, false);
  const id = u.searchParams.get("feature");
  if (id && parId.has(id)) choisir(id, false);
});

appliquerVue(vue, false); chargerCommentaires();
const initiale = new URL(location.href).searchParams.get("feature");
if (initiale && parId.has(initiale)) choisir(initiale, false);
})();
