// bataille2d.js — trois cents hommes devant une porte, et ce qui s'ensuit.
//
// CE QUE C'EST, ET CE QUE CE N'EST PAS. C'est une LUNETTE, exactement comme
// `foule2d` : un bac à sable posé sur le plan, qui ne touche à rien. Aucune
// écriture dans `etat/`, aucune minute de partie consommée, aucun fait de jeu.
// On peut la lancer, la voir tourner, la remettre à zéro : la partie n'en sait
// rien. Le jour où une bataille comptera vraiment, ce sera le MJ qui l'écrira,
// pas ce module.
//
// LES PV SONT EN MÉMOIRE ET N'EN SORTENT JAMAIS. C'est une contrainte assumée
// et pas une paresse : une simulation qui persiste est une simulation qu'il
// faut réconcilier, migrer, et déboguer à travers un fichier. Celle-ci se
// rejoue d'un bouton.
//
// L'ÉCHELLE EST 1:1, EN NOMBRE ET EN TAILLE. Trois cents corps, pas trois cents
// jetons valant dix hommes ; un homme fait 0,55 m d'épaules, marche à 1,3 m/s,
// frappe à 1,6 m. C'est ce qui rend la chose intéressante, parce que la
// géométrie décide alors toute seule : une porte de six mètres ne laisse
// passer que sept hommes de front, et les deux cent quatre-vingt-treize autres
// attendent dehors. Personne n'a écrit ce bouchon — il tombe des mètres.
//
// QUATRE MACHINES À ÉTATS, ET RIEN D'AUTRE.
//
//   le SOLDAT      colonne → forme → assaut → mêlée → (déroute) → blessé → mort
//   le VERROU      fermé → cède → ouvert            (la porte est un objectif,
//                                                    pas un décor)
//   la SURVIE      une morale par homme, qui tombe des morts qu'il VOIT tomber
//                  autour de lui — c'est elle qui décide de la déroute
//   le BOURGEOIS   saisi → fuite → rentre → terre → reprend sa journée
//                  (et le guet, lui, va DANS L'AUTRE SENS)
//
// LES ANNALES — CE QU'UN COMPORTEMENT DOIT LAISSER DERRIÈRE LUI. Une bataille
// qu'on regarde ne sert qu'à celui qui la regarde. Ce module tient donc, en
// plus des corps, une liste de FAITS datés, situés et attribués : la porte qui
// cède, un chef qui tombe, une escouade qui rompt, un blessé dans une rue, la
// peur qui gagne un quartier. C'est la seule sortie qu'un MJ puisse lire, et
// c'est elle qui rend la bataille traversable — on ne raconte pas des points
// qui bougent, on raconte ce qui est arrivé à qui, où, et à quelle heure.
//
// La règle qui les tient : UN COMPORTEMENT QUI N'ÉMET RIEN N'EXISTE PAS. Tout
// ce qu'on ajoutera ici — la chaîne de commandement, le roi, les pillards —
// doit produire sa ligne, faute de quoi on aura enrichi une simulation que
// personne ne peut lire.
//
// Elles sont BORNÉES PAR CONSTRUCTION, et il le faut : quinze chefs, quinze
// escouades, une ligne par quartier gagné par la peur. Le seul poste qui suive
// l'effectif est le blessé — et c'est voulu, parce qu'un blessé est justement
// la scène qu'on est venu chercher.
//
// LA DISRUPTION EST LE VRAI SUJET. `journee.js` est une fonction PURE : elle
// dit où est n'importe qui à n'importe quelle minute, sans état, et c'est ce
// qui permet à quatre cent mille personnes de vivre pour rien. On ne va donc
// PAS la salir. On se glisse par-dessus : `derange(cel, k, P)` est un droit de
// veto que `foule2d` demande pour chaque habitant qu'il s'apprête à dessiner.
// Tant que personne ne panique, il rend faux et ne coûte qu'un test ; ceux qui
// paniquent sortent de leur journée écrite et n'y rentrent qu'une fois calmés.
// La ville reste pure, la peur est une couche.
"use strict";
window.Bataille2d = (() => {

  // ---- les mesures, toutes en mètres et en secondes -------------------------
  // Rien ici n'est un réglage de jeu : ce sont des mesures d'homme. Quand un
  // chiffre paraît faux, c'est qu'il l'est — on le corrige contre la réalité,
  // pas contre l'envie que la bataille dure plus longtemps.
  const EPAULE      = 0.55;   // largeur d'un homme en armes
  const MARCHE      = 1.3;    // en colonne, sans se presser
  const CHARGE      = 3.0;    // les trente derniers mètres
  const FUITE       = 3.6;    // on court mieux quand on a peur
  const ALLONGE     = 1.6;    // épée, hache, pique courte
  const CADENCE     = 0.9;    // secondes entre deux coups
  const PV          = 100;
  const DEGAT       = [14, 30];
  const TOUCHE      = 0.45;   // un coup sur deux porte, à peu près
  const VERROU_PV   = 3000;   // ce que tient une porte bardée de fer
  const HACHE       = 11;     // pv de porte par homme au contact et par seconde
  const FRONT_PORTE = 7;      // combien tiennent de front dans six mètres

  // TOMBER N'EST PAS MOURIR, et c'était le plus gros gâchis du module : un
  // homme à zéro passait `mort`, c'est-à-dire qu'il sortait du monde. Or celui
  // qui tombe et respire encore est le personnage le plus utile de toute la
  // bataille — il ne bouge plus, il est devant une porte qu'on peut nommer, il
  // parle, et il sait des choses : quel ordre il avait reçu, qui était son
  // chef, où allait son aile. On peut le secourir, le dépouiller, l'interroger.
  // Deux hommes sur cinq, donc, et une plaie qui met du temps à décider.
  const PART_BLESSE = 0.38;
  const SAIGNE      = [40, 260];  // secondes avant que la plaie tranche
  const PART_MEURT  = 0.45;       // ce qu'elle décide, quand elle tranche

  // La morale ne se règle pas non plus : elle dit qu'un homme rompt quand ceux
  // qu'il touche du coude tombent, pas quand un compteur global baisse.
  const VUE_MORT    = 18;     // on voit tomber jusque-là
  const CHOC        = 0.085;  // ce que coûte un mort proche
  const SANG        = 0.35;   // ce que coûte d'être soi-même à demi saigné
  const REPRISE     = 0.012;  // la morale remonte quand rien ne se passe
  const ROMPT       = 0.30;

  // --- le commandement -------------------------------------------------------
  // L'ORDRE DESCEND, ET RIEN NE REMONTE. C'est la règle de tout le reste du
  // jeu — la musique d'Ostor traverse un plancher dans un seul sens — et elle
  // vaut ici en fer. La tête ordonne à l'aveugle : elle ne saura jamais si son
  // ordre est arrivé, ni ce qu'il a déclenché.
  //
  // DEUX CANAUX, ET ILS NE VALENT PAS LA MÊME CHOSE.
  //
  //   la BANNIÈRE   on la voit de loin, elle arrive vite, elle ne dit qu'un
  //                 mot — et elle tombe avec celui qui la porte
  //   le COUREUR    il porte ce qu'on veut, il met le temps de courir, et il
  //                 peut ne jamais arriver
  //
  // Le second n'existe que parce que le premier peut manquer, et c'est là que
  // se joue le drame : une aile sans bannière est une aile qu'on ne commande
  // plus qu'à la vitesse d'un homme qui court dans une presse.
  const PAR_ESC      = 20;    // hommes par escouade — l'unité qui pense
  const ESC_PAR_AILE = 5;     // escouades par aile — l'unité qu'on commande
  const VUE_BANNIERE = 110;   // jusqu'où l'on distingue laquelle est levée
  const DELAI_BANN   = 3.5;   // le temps de la voir, d'y croire, et de s'y mettre
  const COURSE       = 3.2;   // un homme qui porte un ordre ne flâne pas
  const DELIBERE     = [6, 14]; // ce que la tête met à changer d'avis
  const RELEVE       = 25;    // le temps qu'on met à relever une bannière
  const CHOC_BANN    = 0.20;  // ce que coûte la voir tomber — à TOUTE l'aile
  const TIENT_BANN   = 2.6;   // la morale remonte mieux sous une bannière debout
  const RALLIE_M     = 15;    // jusqu'où un chef rattrape un homme qui part
  const RALLIE_TAUX  = 0.10;  // et à quelle vitesse il le ramène
  // Le seuil de RETOUR au combat, plus haut que celui de rupture (0,30). C'est
  // la même hystérésis que la peur des habitants, et pour la même raison : sans
  // elle, un homme rallié rompt au pas suivant et l'armée clignote.
  const RALLIE_SEUIL = 0.48;
  // Être « au donjon », c'est être dans sa cour — pas dans la même ville. Le
  // rayon est celui de l'anneau des quatre-vingts, plus la portée d'une arme :
  // au-delà, on marche encore vers lui.
  const AU_DONJON = 45;

  // --- LES DEUX FINS QUI NE PASSENT PAS PAR LE VERROU ------------------------
  //
  // Tout ce qui précède fait tomber une porte à coups de hache. Il y a deux
  // façons pour que la nuit se décide autrement, et elles ne se ressemblent
  // pas : l'une arrête l'assaut, l'autre l'ouvre pour rien.
  //
  //   LE ROI VERSE. Trystane n'est pas à la porte : il est à deux cent trente
  //     mètres en arrière, sur une charrette, dans l'axe même par lequel une
  //     armée qui rompt s'en retourne. On ne le tue donc pas d'un coup d'épée
  //     — personne ne peut l'atteindre — il est ÉCRASÉ PAR LES SIENS. Ce n'est
  //     pas un jet de dés : c'est la conséquence arithmétique d'une déroute qui
  //     lui passe dessus, et elle n'arrive que si l'assaut s'effondre.
  //   BOISDUR EMPORTE LA SALLE. Une porte ouverte de l'intérieur ne coûte pas
  //     un point de verrou. Mais il faut d'abord que le Donjon SACHE, et c'est
  //     là que se trouve le fait le plus cher de la nuit : un homme court, et
  //     pendant qu'il court la ville sait ce que le pouvoir ignore.
  //
  // Les deux clefs sont des HORLOGES, pas des chances. Elles se tirent une
  // fois, à la graine, et la nuit se joue sur laquelle tombe la première —
  // exactement comme les six têtes qui ne délibèrent pas ensemble.
  const ROI_RECUL   = 230;    // où on l'a posé, en arrière de la porte
  const ROI_ESCORTE = 40;     // les hommes autour de la charrette
  const ROI_PRESSE  = 7;      // le rayon dans lequel on le bouscule
  // En hommes-secondes de reflux, et à l'échelle : quinze fuyards pendant six
  // secondes versent la charrette, trois qui passent ne la versent pas.
  const ROI_VERSE   = 90;
  const DETOUR_RUE  = 1.4;    // ce qu'une rue ajoute à la ligne droite
  const DELIBERE_ROSEVAL = [600, 2400];   // il a survécu à deux rois sans choisir
  const DELIBERE_BOISDUR = [900, 3600];   // et l'autre a des chiffres justes

  // --- ce qui distingue un corps d'un autre ---------------------------------
  // Trois réglages, et pas un de plus. Ils ne sont pas des bonus : ce sont les
  // trois façons dont une troupe peut ne pas se comporter comme la moyenne, et
  // chacune se paie. Le ferme meurt sur place au lieu de reculer ; le sourd ne
  // reçoit jamais l'ordre qui l'aurait sauvé ; le versatile n'est jamais là où
  // on l'attend.
  const PLANCHER_FERME   = ROMPT + 0.04;  // il ne passera pas sous le seuil
  const ROMPT_VERSATILE  = 0.44;          // il part bien avant les autres
  const REPRISE_VERSATILE = 3.2;          // et il revient bien plus vite
  const REPRISE_HUMEUR = (h) =>
    h.humeur === "versatile" ? REPRISE_VERSATILE : 1;

  // --- la peur ---------------------------------------------------------------
  // Elle a sa propre physique, et elle ne ressemble pas à celle des soldats.
  // On ne fuit pas un homme : on fuit UNE MASSE — et l'on ne fuit pas en
  // ligne droite, on fuit par la rue, parce qu'il y a des murs.
  const ALERTE      = 90;     // à partir d'où l'on voit et l'on part
  const FOYER_M     = 40;     // la maille qui agrège les soldats en masses
  const FOYER_MIN   = 3;      // sous trois hommes, ce n'est pas une armée
  const SAISI       = [0.4, 2.2];   // le temps de comprendre, avant de courir
  const FUITE_MIN   = 12;     // on court au moins ça avant de songer à rentrer
  const RENTRE_MAX  = 300;    // au-delà, on renonce et l'on se terre où l'on est
  const CALME       = 90;     // le temps qu'il faut pour ressortir
  const RUMEUR      = 30;     // la panique se prend aussi des autres
  const RUMEUR_MIN  = 2;      // il en faut deux qui courent pour y croire
  const PANIQUE_MAX = 4000;   // au-delà, on ne prend plus personne en charge
  // Les manteaux d'or ne fuient pas : ils vont voir. C'est leur métier, et
  // c'est la plus belle chose que cette couche sache produire — une rue qui se
  // vide dans un sens et se remplit d'or dans l'autre.
  const CONTRE = /^(guet|sergent|capitaine-guet)$/;
  const APPROCHE = 25;        // jusqu'où le guet s'avance, et pas plus loin

  // --- CEUX QUI PRENNENT LES ARMES -------------------------------------------
  // LE SEUL COMPORTEMENT QUI FASSE GROSSIR L'ASSAUT, et il manquait. La couche
  // de peur savait faire deux choses : fuir, et — pour le guet — aller voir.
  // Il n'y avait aucun moyen de REJOINDRE, ce qui est absurde pour cette
  // bataille-ci : l'armée de Perkin EST le peuple, et un soulèvement qui ne
  // recrute pas en traversant ses propres rues n'est pas un soulèvement.
  //
  // ON NE TIRE PAS AU SORT, ON LIT L'HOMME. Le métier, l'âge, et un déphasage
  // qui vient de son identité — exactement comme ses heures de sortie. Le même
  // homme prendra toujours les armes, et son voisin ne le fera jamais.
  //
  //   LE MÉTIER — ceux qui ont des bras et un outil qui coupe. Un portefaix,
  //     un tanneur, un écarnisseur. Pas une septa, pas un clerc, pas un
  //     changeur : ils ont autant de raisons d'en vouloir au Donjon, et pas
  //     les mains pour ça.
  //   L'ÂGE — de seize à quarante-cinq ans, et c'est la cellule qui le dit.
  //   LE GUET NE REJOINT JAMAIS. Il va voir, c'est son métier, et c'est déjà
  //     l'autre moitié de cette couche.
  //
  // Il faut aussi qu'il ait VU la masse : on ne rejoint pas une rumeur. C'est
  // la seule condition qui ne tienne pas à l'homme, et c'est la bonne — elle
  // fait que le recrutement suit le chemin de l'armée, rue par rue, au lieu de
  // lever la ville d'un coup.
  //
  // ET IL Y A DEUX CAMPS, ce qui est le vrai sujet. Une ville qui se soulève
  // ne se soulève jamais entière : le même cri, dans la même rue, à la même
  // minute, envoie le portefaix chercher une hache et l'aubergiste barrer sa
  // porte. Ce n'est pas une opinion tirée au sort — c'est ce qu'on a à perdre.
  //
  //   AVEC — ceux qui n'ont rien qu'un outil qui coupe. Portefaix, tanneurs,
  //     brassiers, écarnisseurs, vidangeurs. Ils travaillent chez un autre.
  //   CONTRE — ceux qui ont une porte à eux et du stock derrière. Aubergiste,
  //     marchand, changeur, logeur, meunier, grenetier. Ils ne défendent pas
  //     le roi : ils défendent leur rue, et ça les met du même côté que lui
  //     pour la nuit. C'est plus vrai, et c'est plus cruel.
  //
  // Le reste de la ville ne prend pas les armes du tout — et c'est la majorité.
  const AVEC = /^(portefaix|tanneur|apprenti-tanneur|teinturier|apprenti-teinturier|brassier|fendeur|charbonnier|ecarnisseur|saigneur|cordier|videur|compagnon|marmiton|balayeur|frotteur|vidangeur|aide-vidangeur|valet-fosse|souffleur|palefrenier|aide-meunier|mitron|enfourneur)$/;
  const CONTRE_EUX = /^(aubergiste|tavernier|marchand|marchand-bois|changeur|logeur|loueur|meunier|grenetier|brasseur|boucher|forgeron|potier|voilier|etalier|clerc|clerc-halle|clerc-port|maitre-maison|intendant|gardien|garde-maison|garde-coffre|etuviste)$/;
  const PART_ARMES = 0.22;    // ce qu'une rue donne quand l'armée y passe
  const PART_BARRE = 0.30;    // ceux qui ont pignon se défendent plus volontiers
  // Les paliers auxquels un quartier qui se lève mérite une ligne. Bornés par
  // construction : quatre lignes par quartier, jamais une par homme. C'est la
  // même leçon que ce fichier a déjà apprise trois fois — un fait émis depuis
  // une couche qui tourne PAR PERSONNE doit être verrouillé PAR LIEU, sinon il
  // sort au rythme de la population et enterre la guerre sous sa propre rumeur.
  const PALIERS_ARMES = [1, 10, 40, 120];

  // Ce que chaque quartier a levé, des deux côtés. C'est le seul compteur de
  // cette couche, et il sert à deux choses : franchir les paliers, et dire à
  // la fin combien de gens cette nuit a mis dans la rue qui n'y étaient pas.
  let enArmes = new Map();     // zone -> { assaut, garde }

  function armer(p) {
    const z = situer(p.x, p.y).zone;
    let c = enArmes.get(z);
    if (!c) enArmes.set(z, c = { assaut: 0, garde: 0 });
    const n = ++c[p.prend];
    if (PALIERS_ARMES.indexOf(n) < 0) return;
    noter("prend-les-armes", p.x, p.y,
          { clef: "armes:" + p.prend + ":" + z + ":" + n,
            dit: { camp: p.prend, zone: z, combien: n,
                   role: p.role, age: p.an, femme: p.femme } });
  }

  const PAS = 1 / 20;         // le pas de simulation, fixe
  // La maille de voisinage suit L'ÉPAULE, pas le terrain : devant une porte,
  // trois cents hommes tiennent dans vingt mètres, et une maille de six mètres
  // y met cent personnes par case — c'est-à-dire qu'on refait du n² là où l'on
  // croyait l'avoir évité. Trois mètres coûtent quatre fois plus de cases
  // vides, qui ne coûtent rien, et divisent par trois le vrai travail.
  const MAILLE = 3;

  // ---- l'état ---------------------------------------------------------------
  let toile = null, ctx = null, hote = null, vueDe = null, source = "/monde";
  let plan = null, J = null, voirie = null;
  let boucle = 0, marche = false, dernier = 0, reste = 0;
  let temps = 0;              // secondes écoulées de bataille

  let hommes = [];            // les deux camps, dans le même tableau
  let escouades = [];
  let ailes = [];             // cinq escouades chacune — l'unité qu'on COMMANDE
  let tetes = [];             // ceux qui décident, et qui ne se battent pas —
                              // un par corps, et ils ne se parlent pas entre eux
  let verrou = null;
  let objectif = null;        // le Donjon Rouge, en mètres
  let entree = null;          // la porte visée, en mètres
  // (la grille de voisinage vit plus bas, avec `semer` — elle n'est plus une
  // `Map` mais deux tableaux d'entiers, pour la raison qu'on va lire ici même.)
  // LA PEUR SE RANGE DANS LA CELLULE, PAS DANS UNE MAP À CLEFS DE TEXTE.
  // C'était une `Map` indexée par « 11-3:4127 » : le veto est demandé pour
  // CHACUN des quatre cent mille habitants à chaque calcul de la foule, et
  // fabriquer cette clef quatre cent mille fois coûtait NEUF SECONDES par
  // image — pour un simple accès tableau. C'est mot pour mot la leçon que
  // `journee.js` porte déjà en commentaire ; il a fallu la réapprendre.
  //
  // Donc : un tableau creux posé sur la cellule (`cel._peur[k]`), indexé comme
  // le binaire, et une liste plate pour ce que la simulation doit parcourir.
  let paniques = [];          // les enregistrements, à plat, pour la boucle
  let compte = { a: 0, d: 0, morts: 0, blesses: 0, fuyards: 0, rallies: 0 };

  // --- les annales -----------------------------------------------------------
  // Une liste plate de faits, et un jeu de verrous pour que chacun ne s'écrive
  // qu'une fois. `dejaDit` est le seul mécanisme : on lui donne une clef, il
  // rend vrai la première fois et faux ensuite. Tout ce qui doit être unique —
  // le premier sang, un chef, une escouade, un quartier — passe par lui.
  let annales = [];
  let dits = new Set();
  const dejaDit = (clef) => (dits.has(clef) ? true : (dits.add(clef), false));

  // REJOUABLE — et il a fallu le rendre vrai. La graine était posée à la
  // construction du module et n'était jamais remise : deux `rejouer()` dans la
  // même session donnaient deux batailles différentes, alors que le
  // commentaire promettait le contraire. Tant qu'on regardait, ça ne se voyait
  // pas ; le jour où l'on CUIT une bataille dans un fichier, un déroulé qui ne
  // se reproduit pas est un fichier qu'on ne peut ni vérifier ni corriger.
  const GRAINE = 20161219;
  let _s = GRAINE;
  const R = () => (_s = (_s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  const entre = (a, b) => a + R() * (b - a);

  // ---- la mise en place -----------------------------------------------------
  // On ne pose rien à la main : la porte et le donjon sont des repères du plan
  // cuit, avec leurs mètres. Si demain le plan bouge, la bataille bouge avec.
  function repereDuPlan(nom, genre) {
    const l = (plan && plan.reperes) || [];
    return l.find((r) => r.nom === nom) || l.find((r) => r.genre === genre) || null;
  }

  function portes() {
    return ((plan && plan.reperes) || []).filter((r) => r.genre === "porte");
  }

  // ---- SITUER UN FAIT -------------------------------------------------------
  // Un événement sans lieu ne se joue pas : « la porte cède » est une donnée,
  // « la porte cède, au bourg de la Gadoue, à quarante pas de la Vieille Porte »
  // est une scène. On situe donc par ce que le plan cuit connaît déjà — trente-
  // quatre repères nommés et douze quartiers — et jamais par des coordonnées.
  //
  // EN PAS, PAS EN MÈTRES. C'est la règle du jeu et ce n'est pas une coquetterie :
  // personne, dans cette ville, ne mesure une rue en mètres. Un pas fait 0,75 m.
  const PAS_M = 0.75;
  const enPas = (m) => Math.round(m / PAS_M / 5) * 5;

  // « à 135 pas de Le quai d'amont » — les noms du plan portent leur article,
  // et la préposition doit se contracter comme en français. Ça a l'air d'un
  // détail ; c'est la première chose que l'œil accroche dans un document qu'on
  // lit à voix haute, et ça suffit à le faire passer pour une sortie de machine.
  function duNom(nom) {
    if (/^Le /.test(nom))  return "du " + nom.slice(3);
    if (/^Les /.test(nom)) return "des " + nom.slice(4);
    if (/^La /.test(nom))  return "de la " + nom.slice(3);
    if (/^L'/.test(nom))   return "de l'" + nom.slice(2);
    return "de " + nom;
  }

  function situer(x, y) {
    let rep = null, dr = Infinity;
    for (const r of (plan && plan.reperes) || []) {
      const d = (r.x - x) ** 2 + (r.y - y) ** 2;
      if (d < dr) { dr = d; rep = r; }
    }
    let q = null, dq = Infinity;
    for (const c of (plan && plan.quartiers) || []) {
      const d = (c.x - x) ** 2 + (c.y - y) ** 2;
      if (d < dq) { dq = d; q = c; }
    }
    dr = Math.sqrt(dr);
    // Au-delà de trois cents mètres, un repère ne repère plus rien : on ne dit
    // pas « à mille pas du Donjon Rouge », qui ne situe personne.
    const bout = rep && dr < 300
      ? (dr < 12 ? "devant " + rep.nom : "à " + enPas(dr) + " pas " + duNom(rep.nom))
      : null;
    // LE REPÈRE L'EMPORTE, ET IL EST SEUL QUAND IL EST LÀ. Le plan ne donne
    // d'un quartier que son centre et son nombre de maisons — pas son emprise.
    // Le plus proche centre est donc une devinette, et cousue à un repère
    // précis elle produisait pire qu'une erreur : une INCOHÉRENCE. Deux blessés
    // à quarante pas l'un de l'autre, devant la même porte, l'un « au port » et
    // l'autre nulle part — parce que le seuil du quartier passait entre eux.
    // Dans un document qu'on lit d'affilée, ça se voit à la deuxième ligne et
    // ça décrédibilise tout le reste.
    //
    // Donc : un repère proche EST le lieu, et le quartier n'est que le recours
    // de ceux qui n'en ont aucun.
    const cq = q && Math.sqrt(dq) < 900 ? q.nom : null;
    return {
      quartier: bout ? null : cq,
      repere: bout ? rep.nom : null,
      ou: bout || cq || "hors la ville",
      // `zone` est le quartier le plus proche SANS condition — il ne s'affiche
      // jamais, il sert à regrouper. C'est la clef par laquelle on évite
      // d'écrire quatre-vingt-dix fois que la peur gagne un endroit.
      zone: q ? q.nom : "hors la ville",
    };
  }

  // ===========================================================================
  // LES TÉMOINS — ce qui rend un fait AMPLIFIABLE
  //
  // Un fait daté et situé est déjà utile. Un fait daté, situé, ET dont on sait
  // QUI l'a vu est autre chose : ce n'est plus une ligne à lire, c'est une
  // piste à remonter. La troupe ne lit pas les annales — elle va trouver la
  // teinturière du Culpucier qui était dans la rue à cette heure-là, et elle
  // lui demande. Et la teinturière peut mentir, se tromper, ou vouloir qu'on
  // la paie : c'est exactement la grammaire du jeu.
  //
  // ON NE PREND QUE LES PANIQUÉS, et ce n'est pas une limite mais la bonne
  // définition. Les quatre cent mille autres sont chez eux, porte fermée, et
  // n'ont rien vu ; ceux que la couche de peur a pris en charge sont
  // précisément les gens qui étaient DEHORS quand c'est arrivé.
  //
  // Le coût est nul à l'échelle du sac : quelques dizaines de faits, un
  // balayage de la liste des paniqués pour chacun.
  const VUE_TEMOIN = 50;      // au-delà, dans une rue, on ne voit plus qui tombe
  const TEMOINS_MAX = 6;      // on n'a pas besoin de la foule, on a besoin de noms

  function temoinsDe(x, y) {
    const l = [];
    for (const p of paniques) {
      // Celui qui s'est terré n'a plus rien vu : il est derrière sa porte.
      if (p.etat === "terre") continue;
      const d = Math.hypot(p.x - x, p.y - y);
      if (d > VUE_TEMOIN) continue;
      l.push({ d, p });
    }
    l.sort((a, b) => a.d - b.d);
    return l.slice(0, TEMOINS_MAX).map(({ d, p }) => ({
      id: p.id, age: p.an, role: p.role || null, femme: p.femme,
      // SON ADRESSE, et c'est le champ qui compte. Le reste décrit ; celui-ci
      // permet d'aller frapper à sa porte.
      chez: [+p.chez[0].toFixed(1), +p.chez[1].toFixed(1)],
      // LE QUARTIER, PAS LE REPÈRE LE PLUS PROCHE. `situer().ou` vise le repère
      // et donne « à 40 pas de la Salle de l'entrepôt » — ce qui, pour dire OÙ
      // HABITE quelqu'un, ne veut rien dire et produisait des monstres comme
      // « portefaix de aire de bris ». Ce dont on a besoin ici est le nom sous
      // lequel un quartier se demande dans la rue.
      ou: situer(p.chez[0], p.chez[1]).zone,
      pas: enPas(d),
      // Le guet ne témoigne pas comme un teinturier : il fait un rapport, il
      // est cru, et ce qu'il dit finit dans un registre.
      guet: !!p.contre,
    }));
  }

  /**
   * Porter un fait aux annales. `clef` le rend unique quand elle est donnée —
   * un chef ne tombe qu'une fois, un quartier n'est gagné qu'une fois.
   * Rend faux quand le fait avait déjà été dit, ce qui permet d'enchaîner.
   */
  function noter(quoi, x, y, o) {
    if (o && o.clef && dejaDit(o.clef)) return false;
    const l = situer(x, y);
    annales.push(Object.assign({
      t: +temps.toFixed(2), quoi,
      x: +x.toFixed(1), y: +y.toFixed(1),
      quartier: l.quartier, repere: l.repere, ou: l.ou, zone: l.zone,
      temoins: temoinsDe(x, y),
    }, o && o.dit));
    return true;
  }

  // Le dehors, c'est le côté opposé au cœur de la ville. On ne le devine pas
  // au jugé : les bornes du plan donnent le centre, et une porte regarde
  // toujours vers l'extérieur de ce centre-là.
  function dehors(p) {
    const [x0, y0, x1, y1] = plan.bornes;
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    const dx = p.x - cx, dy = p.y - cy, d = Math.hypot(dx, dy) || 1;
    return [dx / d, dy / d];
  }

  // ===========================================================================
  // L'ORDRE DE BATAILLE
  // ===========================================================================
  // Les effectifs, les noms et les humeurs sont ceux de `docs/bataille.md`.
  // Ici on ne fait que les POSER : ce bloc dit combien, où, et dans quelle
  // forme — jamais pourquoi.
  //
  // L'ÉCHELLE EST UN OUTIL DE REPÉRAGE, PAS UN RÉGLAGE. À neuf mille cinq cents
  // hommes on ne voit plus une formation, on voit une tache — et l'on ne va pas
  // attendre dix minutes de cuisson pour s'apercevoir qu'un corps part du
  // mauvais côté. Un vingtième rend quatre cent soixante-quinze corps, c'est-à-
  // dire le coût de la bataille d'avant, et la MÊME géométrie : mêmes
  // distances, mêmes rues, mêmes largeurs de front. On règle la mise en place à
  // l'œil, puis on cuit à 1.
  //
  // Elle ne touche QUE L'ASSAUT. Les cent vingt-cinq de la garde sont des
  // postes tenus un par un, pas une masse : les diviser par vingt donnerait six
  // hommes et une image fausse.
  let ECHELLE = 1 / 20;
  const combien = (n) => Math.max(PAR_ESC, Math.round(n * ECHELLE));

  // Les six corps. `recul` compte en mètres vers le DEHORS de la porte, `cote`
  // le long du rempart (positif vers le quai d'aval). Les deux se prennent sur
  // le repère du plan cuit : si la porte bouge un jour, l'armée bouge avec.
  //
  // LA FORME EST L'ARGUMENT, et c'est pour ça qu'il y en a quatre. Une colonne
  // arrive par la tête et s'engorge ; une ligne arrive à plat ; des paquets
  // arrivent de trois côtés et jamais ensemble ; une nuée n'arrive pas, elle
  // se répand. Personne n'écrit ces différences ensuite — elles tombent d'ici.
  const CORPS = [
    { id: "perkin", nom: "Ser Perkin la Puce", hommes: 2400, humeur: null,
      forme: "colonne", parRang: 8, recul: 110, cote: 0, rangTete: 2,
      dit: "le centre — il frappe la porte, et il est au troisième rang" },
    { id: "crochet", nom: "Ser Wat Crochet", hommes: 1800, humeur: null,
      porte: "La porte de Fer",
      forme: "colonne", parRang: 6, recul: 300, cote: 450, rangTete: 0,
      dit: "le port — il arrive en flanc, donc en retard, et il a les outils" },
    { id: "ronnel", nom: "Ser Ronnel Sans-Maison", hommes: 900, humeur: "ferme",
      porte: "La porte du Roi",
      forme: "ligne", parRang: 30, recul: 170, cote: -130, rangTete: 0,
      dit: "l'aile ferme — le seul corps qui ne rompt pas" },
    { id: "marda", nom: "Marda la Boiteuse", hommes: 1200, humeur: null,
      forme: "paquets", paquets: [[70, -60], [100, -150], [55, -25]],
      recul: 80, cote: -80, rangTete: 0,
      dit: "la Gadoue — par les ruelles, à trois endroits, et pas pour la porte" },
    { id: "vaugrain", nom: "Frère Vaugrain", hommes: 2000, humeur: "sourd",
      porte: "La Vieille Porte",
      forme: "colonne", parRang: 14, recul: 270, cote: -330, rangTete: 1,
      dit: "les cendres — au cantique, et ils n'entendent rien d'autre" },
    { id: "tam", nom: "Petit Tam", hommes: 1200, humeur: "versatile",
      forme: "nuee", largeur: 170, fond: 130, recul: 130, cote: 230, rangTete: 0,
      dit: "les enfants de la Gadoue — sans formation, et ils paniquent" },
  ];

  // QUATRE PORTES, ET CHAQUE VERROU TOMBE À SON HEURE.
  //
  // Les six corps entraient tous par la Gadoue : six chaînes de commandement
  // qui se disputaient un seul seuil de six mètres, où sept hommes cognent à la
  // fois. Neuf mille cinq cents hommes derrière une porte, c'est une file, pas
  // un sac — et surtout ça n'a jamais eu lieu ainsi : une ville se prend par
  // plusieurs portes, et ce qui décide de tout est que l'une cède avant les
  // autres.
  //
  // Un corps sans `porte` prend celle qu'on donne au four (la Gadoue par
  // défaut) : Perkin la frappe de face, Marda passe par ses ruelles, Petit Tam
  // suit. Les trois autres ont la leur. Le Donjon reste commun — c'est ce qui
  // fait converger les colonnes au lieu de les disperser.
  let verrous = [];           // un par porte engagée
  const porteDuCorps = (c, defaut) => c.porte || defaut;

  // COMBIEN D'AILES UN CORPS A, À EFFECTIF PLEIN — et c'est ce nombre-là qui
  // fait foi à toutes les échelles. Un corps de deux mille quatre cents hommes
  // se commande en vingt-quatre ailes ; à un vingtième il a moins de monde
  // dedans, mais il se commande toujours en vingt-quatre. La structure est de
  // la fiction, l'effectif est du réglage.
  const ailesDe = (c) =>
    Math.max(1, Math.round(c.hommes / (PAR_ESC * ESC_PAR_AILE)));

  /** Le repère d'un corps : le dehors de la porte, et le long du rempart. */
  function axeDe(porte) {
    const [nx, ny] = dehors(porte);
    return { nx, ny, tx: -ny, ty: nx };
  }

  /** Les places d'un corps, dans sa forme à lui. */
  function poserCorps(c, porte) {
    const { nx, ny, tx, ty } = axeDe(porte);
    const en = (recul, cote) => ({
      x: porte.x + nx * recul + tx * cote + entre(-.25, .25),
      y: porte.y + ny * recul + ty * cote + entre(-.25, .25),
    });
    const n = combien(c.hommes), l = [];

    if (c.forme === "nuee") {
      // Aucune formation, et c'est le propos. La BOÎTE est l'information : sa
      // largeur dit qu'ils tiennent trois rues et qu'aucun ordre ne les
      // traversera jamais d'un bout à l'autre.
      for (let i = 0; i < n; i++)
        l.push(en(c.recul + entre(-c.fond / 2, c.fond / 2),
                  c.cote + entre(-c.largeur / 2, c.largeur / 2)));
      return l;
    }
    if (c.forme === "paquets") {
      // Trois grappes qui n'ont pas le même chemin à faire. Elles n'arriveront
      // donc pas ensemble, et personne n'a eu à écrire qu'elles arrivent en
      // désordre : il suffisait de ne pas les poser au même endroit.
      const p = c.paquets, par = Math.ceil(n / p.length);
      for (let i = 0; i < n; i++) {
        const [r0, c0] = p[Math.min(p.length - 1, Math.floor(i / par))];
        const k = i % par;
        l.push(en(r0 + Math.floor(k / 7) * 1.3, c0 + (k % 7 - 3) * 1.2));
      }
      return l;
    }
    // Colonne et ligne sont la MÊME chose, et c'est tout l'intérêt de les avoir
    // écrites pareil : six de front font un serpent, trente font un mur, et
    // personne n'a eu à décider de la profondeur.
    const par = c.parRang;
    for (let i = 0; i < n; i++)
      l.push(en(c.recul + Math.floor(i / par) * 1.4,
                c.cote + (i % par - (par - 1) / 2) * 1.1));
    return l;
  }

  // LES NOMMÉS QUI NE SE BATTENT PAS. Ils ne sont PAS dans `hommes`, et c'est
  // une décision : un corps qui entre dans la boucle a une morale, une case de
  // grille et un coût par pas, et aucun de ceux-là n'a de raison d'en avoir.
  // Ce sont des repères humains — on les voit, on les nomme, et le jour où un
  // fait tombe à côté d'eux, la relecture saura devant QUI il est tombé.
  let figures = [];

  function homme(camp, x, y, opts) {
    return {
      camp, x, y, vx: 0, vy: 0,
      pv: PV, morale: 1, etat: "colonne", cible: null,
      prochain: entre(0, CADENCE),              // les coups ne tombent pas en chœur
      escouade: (opts && opts.escouade) || 0,
      aile: (opts && opts.aile) || 0,
      poste: (opts && opts.poste) || null,      // où l'on tient — les deux camps
      chef: !!(opts && opts.chef),
      capitaine: !!(opts && opts.capitaine),    // il porte la bannière de l'aile
      tete: !!(opts && opts.tete),              // il décide, et il ne se bat pas
      // LE NOM NE CHANGE RIEN À CE QU'IL ENCAISSE, et il faut que ça reste
      // vrai : le jour où un nommé a des pv à lui, on a ouvert la porte des
      // champions et de tous les cas particuliers qui suivent. Un nom ne
      // change que ce qu'on ÉCRIT quand il tombe.
      nom: (opts && opts.nom) || null,
      corps: (opts && opts.corps) || null,
      humeur: (opts && opts.humeur) || null,
      porte: null,                              // l'ordre qu'un coureur emporte
      chez: null,                               // à quelle escouade il court
      but: null, trace: null, avance: 0, cote: R() < .5 ? -1 : 1,
    };
  }

  /** L'ordre de bataille. Trois cents contre une garnison, et un verrou. */
  function dresser(nomPorte, n) {
    _s = GRAINE;                 // la même bataille, à chaque fois qu'on la dresse
    const porte = nomPorte ? repereDuPlan(nomPorte, "porte") : portes()[3];
    const donjon = repereDuPlan("Le Donjon Rouge", "donjon");
    if (!porte || !donjon) throw new Error("ni porte ni donjon dans ce plan");
    entree = porte; objectif = donjon;

    hommes = []; escouades = []; ailes = []; tetes = []; figures = [];
    temps = 0; reste = 0;
    // LES ANNALES REPARTENT ICI, ET AVANT LES CORPS. Sinon une seconde cuisson
    // n'écrit plus rien — et surtout, tout ce que la mise en place a à dire
    // (l'humeur des six corps) serait effacé juste après avoir été écrit.
    annales = []; dits.clear();

    // SIX CORPS, ET PLUS UN SEUL BLOC. C'était trois cents hommes en colonne
    // par six ; ce sont maintenant six foules qui vont dans la même direction
    // pour six raisons différentes, et deux d'entre elles n'obéissent à
    // personne. Tout ce que la bataille produira d'intéressant vient de là.
    //
    // Des escouades de vingt : l'unité qui PENSE (un chemin par escouade, pas
    // par homme). Des ailes de cinq escouades : l'unité qu'on COMMANDE. Et
    // désormais une chaîne par corps — parce que l'intérêt n'est pas d'avoir
    // une chaîne qui marche, c'est d'en avoir six qui ne s'accordent pas.
    const PAR = PAR_ESC;
    const TOTAL = CORPS.reduce((s, c) => s + c.hommes, 0);
    // Un effectif d'essai vaut une échelle : `pas(90)` et les vieux appels à
    // trois cents hommes continuent de marcher, et ils disent maintenant
    // quelque chose de juste — trois cents hommes, c'est un trente-deuxième
    // de cette armée-là.
    if (n) ECHELLE = n / TOTAL;

    // UN VERROU PAR PORTE ENGAGÉE, ET UN SEUL. Deux corps qui entrent par la
    // même porte frappent le MÊME battant : sans cette mise en commun, chacun
    // aurait le sien, la porte tomberait deux fois, et le compte des sept
    // hommes de front n'aurait plus de sens.
    // Le repère de la porte PRINCIPALE, pour tout ce qui se place par rapport
    // à elle sans appartenir à un corps : les figures, le roi sur sa charrette,
    // les habitants qui ont une adresse. Chaque corps aura le sien, qui masque
    // celui-ci dans sa boucle.
    const axeP = axeDe(porte);
    const en = (recul, cote) => [porte.x + axeP.nx * recul + axeP.tx * cote,
                                 porte.y + axeP.ny * recul + axeP.ty * cote];

    // LA VILLE SE REBÂTIT ENTRE DEUX BATAILLES. Le bâti est chargé une fois et
    // gardé — mais son ÉTAT appartient à la bataille, pas au décor. Sans cette
    // remise à zéro, la seconde cuisson trouvait quarante-cinq mille maisons
    // déjà forcées : plus rien à piller, donc plus personne qui s'arrête, donc
    // un déroulé entièrement différent. La vérification l'a dit tout de suite
    // — mille trente-huit mètres d'écart et deux millions d'états faux — et
    // c'est précisément ce qu'elle est là pour dire : un fichier cuit qui ne se
    // rejoue pas ne se vérifie pas, et ne se corrige donc jamais.
    if (bati) {
      bati.etat.fill(0);
      bati.forcees = 0; bati.brulees = 0; bati.butin = 0;
    }

    verrous = [];
    const verrouDe = (rep) => {
      let v = verrous.find((w) => w.nom === rep.nom);
      if (!v) verrous.push(v = { nom: rep.nom, porte: rep,
                                 pv: VERROU_PV, max: VERROU_PV, etat: "ferme",
                                 x: rep.x, y: rep.y, frappeurs: 0 });
      return v;
    };

    for (const c of CORPS) {
      // La porte de CE corps — la sienne s'il en a une, celle du four sinon.
      const rep = c.porte ? repereDuPlan(c.porte, "porte") : porte;
      c._entree = rep || porte;
      c._verrou = verrouDe(c._entree);
      const { nx, ny, tx, ty } = axeDe(c._entree);
      const en = (recul, cote) => [c._entree.x + nx * recul + tx * cote,
                                   c._entree.y + ny * recul + ty * cote];
      const places = poserCorps(c, c._entree);
      const e0 = escouades.length, a0 = ailes.length;
      const nEsc = Math.ceil(places.length / PAR);
      // LE NOMBRE D'AILES SE PREND SUR L'EFFECTIF PLEIN, JAMAIS SUR L'ÉCHELLE.
      // C'est le piège de la maquette, et il est silencieux : à un trente-
      // deuxième, un corps ne fait plus que quatre escouades, donc UNE aile —
      // et comme la réserve n'est ordonnée qu'aux ailes autres que la première,
      // plus aucune tête n'ordonnait quoi que ce soit. Quatre cents secondes de
      // bataille, six têtes, zéro ordre : le mécanisme entier était mort, et
      // rien ne le disait puisque la géométrie, elle, restait juste.
      //
      // L'échelle doit donc préserver la STRUCTURE autant que les distances :
      // même nombre d'ailes qu'à effectif plein, avec moins de monde dedans.
      const nAile = Math.min(nEsc, ailesDe(c));

      // L'ORDRE DE DÉPART EST CELUI QUE LA DOCTRINE DONNERAIT, et ce n'est pas
      // un détail de confort : les ailes commençaient toutes en « avancer », si
      // bien que la première délibération de chaque tête ordonnait la réserve —
      // vingt lignes de « tenir » à la seconde zéro, toutes identiques, en tête
      // du document. Or une réserve, au déploiement, EST déjà la réserve.
      // Personne ne le lui ordonne ; c'est là qu'on l'a mise.
      //
      // Un ordre ne vaut une ligne que lorsqu'il CHANGE quelque chose.
      for (let a = 0; a < nAile; a++)
        ailes.push({ id: a0 + a, corps: c.id, rang: a,
                     ordre: a === 0 ? "avancer" : "tenir",
                     capitaine: null, releve: 0,
                     banniere: { debout: false, x: porte.x, y: porte.y } });
      // LE PARTAGE DES ESCOUADES SUIT LE NOMBRE D'AILES RÉEL, pas la division
      // à effectif plein. `e / ESC_PAR_AILE` ne marche qu'à l'échelle 1 : à un
      // vingtième, six escouades ne rempliraient que les deux premières ailes
      // sur six, et les quatre autres — vides — auraient une force nulle, donc
      // un ordre de repli perpétuel. Une aile sans homme n'est pas une réserve,
      // c'est un trou dans la chaîne.
      const aileDeLEsc = (e) => a0 + Math.min(nAile - 1,
                                              Math.floor(e * nAile / nEsc));
      for (let e = 0; e < nEsc; e++)
        escouades.push({ id: e0 + e, corps: c.id, entree: c._entree,
                         aile: aileDeLEsc(e),
                         trace: null, phase: "porte",
                         // Elle part avec l'ordre de son aile, sinon la
                         // transmission croirait avoir un retard à rattraper
                         // avant même que la bataille ait commencé.
                         ordre: ailes[aileDeLEsc(e)].ordre,
                         attend: null, coureur: null,
                         // Le sourd l'est dès le départ, et pour toujours.
                         sourde: c.humeur === "sourd",
                         sourd_ne: c.humeur === "sourd" });

      for (let i = 0; i < places.length; i++) {
        const e = Math.floor(i / PAR);
        const h = homme("assaut", places[i].x, places[i].y,
                        { escouade: e0 + e, aile: aileDeLEsc(e),
                          corps: c.id, humeur: c.humeur,
                          chef: i % PAR === 0 });
        // CHACUN PORTE SA PORTE. On pourrait la retrouver par son corps à
        // chaque pas ; on la lui accroche une fois, parce que c'est lu vingt
        // fois par seconde et par homme, et qu'une indirection de plus à ce
        // rythme-là se paie en secondes de cuisson.
        h.entree = c._entree; h.verrou = c._verrou;
        // Un assaillant a un poste, lui aussi : celui d'où il est parti. C'est
        // là qu'il revient quand on lui ordonne de tenir — sans ça, « tenir »
        // ne voudrait rien dire pour quelqu'un qui n'a jamais rien gardé.
        h.poste = [h.x, h.y];
        hommes.push(h);
      }

      // LA TÊTE NE SE BAT PAS, et c'est ce qui la rend intéressante : son seul
      // acte est de décider. Elle est quand même un CORPS — donc elle est dans
      // le sac, donc elle est quelque part, donc le jour où la ligne cède elle
      // est joignable. Elle se tient au rang que son caractère lui donne :
      // Perkin au troisième, dans sa propre masse, ce qui ne l'empêche pas de
      // n'avoir jamais frappé un coup.
      const [hx, hy] = en(c.recul + (c.rangTete || 0) * 1.4, c.cote);
      const t = homme("assaut", hx, hy,
                      { tete: true, corps: c.id, nom: c.nom, humeur: c.humeur });
      t.entree = c._entree; t.verrou = c._verrou;
      t.etat = "commande";
      t.poste = [t.x, t.y];
      t.decide = entre(2, 5);
      hommes.push(t);
      tetes.push(t);

      // UN COMPORTEMENT QUI N'ÉMET RIEN N'EXISTE PAS — c'est la règle du
      // module, et l'humeur d'un corps la casse en silence. Un corps sourd ne
      // produit AUCUN `escouade-sourde` : ses escouades sortent de la
      // transmission avant d'y entrer, donc rien ne signale que deux mille
      // hommes n'écouteront jamais un ordre. À la relecture on verrait une tête
      // qui commande et des hommes qui n'obéissent pas, sans jamais savoir
      // pourquoi. On le dit une fois, au départ, et c'est assez.
      if (c.humeur)
        noter("corps-" + c.humeur, t.x, t.y,
              { clef: "humeur:" + c.id,
                dit: { corps: c.id, chef: c.nom, hommes: places.length,
                       humeur: c.humeur } });
    }

    // LE CAPITAINE SE NOMME APRÈS COUP, ET UN PAR AILE. Il était désigné par
    // un modulo sur l'indice — ce qui ne vaut que si chaque aile a exactement
    // cinq escouades pleines. Dès que l'échelle amincit les escouades, le
    // modulo tombe à côté et des ailes entières se retrouvent sans bannière,
    // c'est-à-dire hors de la chaîne, sans que rien ne le dise. On prend donc
    // le premier homme de l'aile qui n'est pas déjà chef d'escouade : un
    // soldat qu'on a monté en grade, pas un être à part. Il porte la bannière,
    // ce qui veut dire qu'il la fait tomber en tombant.
    for (const h of hommes) {
      if (h.camp !== "assaut" || h.tete || h.chef) continue;
      const a = ailes[h.aile];
      if (!a || a.capitaine) continue;
      h.capitaine = true;
      a.capitaine = h;
      a.banniere = { debout: true, x: h.x, y: h.y };
    }

    // La garnison. Elle ne sort pas : elle tient la porte, puis la cour du
    // donjon. Un défenseur qui charge en rase campagne n'aurait aucune raison
    // de le faire, et c'est le genre de bêtise qu'on n'écrit pas.
    //
    // ET IL Y EN A UNE PAR PORTE, forcément — mais elles ne sont pas égales, et
    // c'est là que se joue le sort de la ville. La ville a une garnison, pas
    // quatre : ce qu'on met à une porte, on ne l'a plus à l'autre. Quarante-
    // cinq hommes à celle qu'on croit menacée, quinze aux autres. Celle qui
    // cède la première n'est pas celle qu'on frappe le plus fort, c'est celle
    // qu'on a le moins gardée — et personne ne l'a décidé, c'est tombé du
    // compte.
    for (const v of verrous) {
      const premiere = v.porte.nom === porte.nom;
      const n = premiere ? 45 : 15;
      const { nx, ny, tx, ty } = axeDe(v.porte);
      for (let i = 0; i < n; i++) {
        const c = (i % 9 - 4) * 1.0, r = Math.floor(i / 9) * 1.3;
        const px = v.porte.x - nx * (8 + r) + tx * c;
        const py = v.porte.y - ny * (8 + r) + ty * c;
        const h = homme("garde", px, py,
                        { poste: [px, py],
                          // Le capitaine du poste est au milieu du premier
                          // rang. Il meurt dans la première minute et c'est
                          // tout le personnage : ses trois demandes de renfort
                          // sont datées, écrites, et personne ne les a lues.
                          nom: (premiere && i === 4) ? "Ser Damon Beurrepré" : null });
        h.entree = v.porte; h.verrou = v;
        hommes.push(h);
      }
    }
    for (let i = 0; i < 80; i++) {
      const a = (i / 80) * Math.PI * 2, r = 26 + (i % 3) * 2.2;
      const px = donjon.x + Math.cos(a) * r, py = donjon.y + Math.sin(a) * r;
      hommes.push(homme("garde", px, py, { poste: [px, py] }));
    }
    for (const h of hommes) if (h.camp === "garde") h.etat = "tient";

    // ---- CEUX QUI NE SE BATTENT PAS ---------------------------------------
    // Un roi porté sur une charrette, quatre personnes enfermées dans un
    // château, et huit habitants qui ont une adresse. Aucun n'est simulé : ce
    // sont des repères humains, posés pour que les faits aient quelqu'un sur
    // qui tomber. « La bannière de l'aile ouest tombe » est une donnée ;
    // « elle tombe à trente pas de chez Nonne la lavandière » est une scène.
    const fig = (camp, p, nom, dit) =>
      figures.push({ camp, x: p[0], y: p[1], nom, dit });
    const dans = (r, c) => en(-r, c);          // vers l'intérieur des murs

    fig("assaut", en(230, 20), "Trystane Feufidèle",
        "seize ans, sur une charrette, quarante hommes autour — s'il tombe, tout s'arrête");
    fig("garde", [donjon.x - 14, donjon.y - 10], "Lord Ardrian Roseval",
        "châtelain — il veut rendre le Donjon intact, et il ne décide jamais à temps");
    fig("garde", [donjon.x + 12, donjon.y - 16], "Dame Elyanne de Rosby",
        "soixante et onze ans, sa litière est prête depuis six jours et elle n'y monte pas");
    fig("garde", [donjon.x + 16, donjon.y + 8], "Lord Ronard Boisdur",
        "il est pour qu'on ouvre — la seule porte qui puisse s'ouvrir sans se casser");
    fig("garde", [donjon.x - 10, donjon.y + 14], "le septon Marris",
        "il veut que la Foi ne soit pas nommée dans ce qui va arriver");

    const mp = repereDuPlan("Le marché aux poissons", "marche-poissons");
    fig("ville", dans(20, 12), "Rob l'écailler",
        "il sauve son étal avant sa femme, et il le sait déjà");
    fig("ville", dans(48, -18), "les deux Nayle",
        "quatorze ans et onze ans — ils suivent l'armée, ils trouvent ça magnifique");
    fig("ville", dans(62, 26), "le vieux Wex",
        "sourd, sur le pas de sa porte — il ne bougera pas");
    fig("ville", dans(120, -40), "mestre Ottyn",
        "apothicaire — il ne ferme pas, il sait ce qu'il aura dans son échoppe dans une heure");
    fig("ville", mp ? [mp.x + 18, mp.y - 10] : dans(290, 0), "Nonne la lavandière",
        "trois enfants, elle en compte deux, et elle REMONTE vers le bruit");
    fig("ville", dans(150, 62), "sœur Jenn",
        "elle ouvre le septuaire et hurle qu'on y entre — deux cents y entrent");
    fig("ville", dans(205, -85), "Cateline la sage-femme",
        "elle va vers la bataille depuis le début, et elle est en train d'accoucher quelqu'un");
    fig("ville", dans(265, -120), "la Veuve",
        "receleuse, rue des Sœurs — elle ne sort pas, et elle achète dès ce soir");

    // `entree` et `verrou` restent, mais ne désignent plus QUE la porte
    // principale — celle qu'on a demandée au four. Ils ne servent qu'à ce qui
    // parle de la bataille en général : le bandeau, le relevé, le cercle du
    // plan. Tout ce qui concerne un homme passe par le sien.
    entree = porte;
    verrou = verrous.find((v) => v.nom === porte.nom) || verrous[0] || null;
    majCompte();
  }

  // ---- le voisinage ---------------------------------------------------------
  // Trois cent quatre-vingts corps, c'est peu — mais « peu » au carré fait
  // cent quarante mille comparaisons vingt fois par seconde, et c'est ainsi
  // qu'une simulation simple devient lente sans qu'on comprenne pourquoi. Une
  // grille de six mètres ramène ça à ce qu'on touche du coude.
  //
  // LA CASE SE DÉSIGNE PAR UN ENTIER, JAMAIS PAR UNE CLEF DE TEXTE. C'est la
  // même leçon que la peur des habitants porte trente lignes plus haut, et il
  // a fallu la réapprendre ici aussi. `autour` fabriquait un `ci + ":" + cj`
  // par case consultée : chaque homme en consulte dix-huit par pas, deux fois
  // (une fois pour chercher l'ennemi, une fois pour jouer des coudes). À deux
  // mille hommes et vingt pas par seconde, cela faisait SEPT CENT VINGT MILLE
  // concaténations de chaînes par seconde de bataille — un coût fixe par
  // homme, que la mêlée n'expliquait pas et que le profil désignait seul.
  //
  // À la place, un tri par comptage : `debut[]` dit où commence chaque case
  // dans `corps[]`, et `corps[]` tient les indices des hommes rangés case par
  // case. Deux passes, aucune allocation — les deux tampons sont réutilisés
  // d'un pas à l'autre et ne grandissent que quand il le faut.
  //
  // La grille ne couvre PAS le plan entier : cinq kilomètres sur trois en
  // mailles de trois mètres feraient trois millions et demi de cases à remettre
  // à zéro vingt fois par seconde, pour une bataille qui tient dans un carré de
  // six cents mètres. On la taille donc sur les hommes eux-mêmes, à chaque pas.
  //
  // Mais on la CALE SUR LA MÊME TRAME que les clefs de texte d'avant : l'origine
  // tombe sur un multiple de MAILLE, donc les cases découpent le terrain
  // exactement là où elles le découpaient. Sans quoi le voisinage change au
  // ras des bords de case, et une optimisation qui promettait de ne rien
  // changer change la bataille.
  let gI0 = 0, gJ0 = 0;         // le coin de la grille, en cases de la trame
  let gCol = 0, gLig = 0;       // sa taille, en cases
  let gDebut = new Int32Array(0);   // ncases + 1 bornes, en style CSR
  let gCorps = new Int32Array(0);   // les indices dans `hommes`, rangés par case
  // Les hommes bougent APRÈS le semis (`soldat` puis `pousser`), donc leur
  // case peut déborder de la boîte d'un pas de marche. Huit cases de marge
  // valent vingt-quatre mètres : personne ne franchit ça en un vingtième de
  // seconde, et une case vide ne coûte rien.
  const MARGE_C = 8;

  function caseDe(x, y) {
    let i = Math.floor(x / MAILLE) - gI0, j = Math.floor(y / MAILLE) - gJ0;
    // Un déroutant court à quatre cents mètres hors la porte, et rien
    // n'interdit qu'un jour il aille plus loin : on borne au lieu de sortir du
    // tableau. La boîte étant taillée sur les vivants, ce garde-fou ne sert
    // qu'aux positions absurdes.
    if (i < 0) i = 0; else if (i >= gCol) i = gCol - 1;
    if (j < 0) j = 0; else if (j >= gLig) j = gLig - 1;
    return j * gCol + i;
  }

  function semer() {
    let i0 = Infinity, j0 = Infinity, i1 = -Infinity, j1 = -Infinity;
    for (const h of hommes) {
      if (h.etat === "mort") continue;
      const i = Math.floor(h.x / MAILLE), j = Math.floor(h.y / MAILLE);
      if (i < i0) i0 = i; if (i > i1) i1 = i;
      if (j < j0) j0 = j; if (j > j1) j1 = j;
    }
    if (i0 === Infinity) { gCol = gLig = 0; return; }   // plus personne debout

    gI0 = i0 - MARGE_C; gJ0 = j0 - MARGE_C;
    gCol = (i1 - i0) + 1 + MARGE_C * 2;
    gLig = (j1 - j0) + 1 + MARGE_C * 2;
    const nc = gCol * gLig;

    // On ne rend jamais les tampons : ils prennent la taille du pire pas et la
    // gardent. C'est la moitié du gain — une allocation par pas rendrait le
    // ramasse-miettes visible à l'œil nu sur une bataille de dix mille hommes.
    if (gDebut.length < nc + 1) gDebut = new Int32Array(nc + 1);
    if (gCorps.length < hommes.length) gCorps = new Int32Array(hommes.length);
    gDebut.fill(0, 0, nc + 1);

    // Première passe : combien d'hommes par case.
    for (let k = 0; k < hommes.length; k++) {
      const h = hommes[k];
      if (h.etat === "mort") continue;
      gDebut[caseDe(h.x, h.y)]++;
    }
    // Somme courante : `debut[c]` porte pour l'instant la FIN de la case c.
    let s = 0;
    for (let c = 0; c < nc; c++) { s += gDebut[c]; gDebut[c] = s; }
    gDebut[nc] = s;
    // Seconde passe, à REBOURS, en décrémentant : chaque case se remplit par la
    // fin, donc les hommes s'y retrouvent dans l'ordre du tableau `hommes` —
    // le même ordre que les listes d'avant. C'est ce qui rend la bataille
    // identique au pas près, et c'est la seule preuve qu'on n'a rien cassé.
    // Au passage, `debut[c]` redevient le DÉBUT de la case c, et `debut[c+1]`
    // en marque la fin.
    for (let k = hommes.length - 1; k >= 0; k--) {
      const h = hommes[k];
      if (h.etat === "mort") continue;
      gCorps[--gDebut[caseDe(h.x, h.y)]] = k;
    }
  }

  function autour(x, y, rayon, fn) {
    if (!gCol) return;
    const r = Math.ceil(rayon / MAILLE);
    const ci = Math.floor(x / MAILLE) - gI0, cj = Math.floor(y / MAILLE) - gJ0;
    // On rogne la fenêtre au lieu de ramener le centre dans la grille : une
    // case hors boîte est vide par construction, donc la sauter revient
    // exactement au `grille.get` qui rendait `undefined`.
    let i0 = ci - r, i1 = ci + r, j0 = cj - r, j1 = cj + r;
    if (i0 < 0) i0 = 0; if (i1 >= gCol) i1 = gCol - 1;
    if (j0 < 0) j0 = 0; if (j1 >= gLig) j1 = gLig - 1;
    for (let i = i0; i <= i1; i++) for (let j = j0; j <= j1; j++) {
      const c = j * gCol + i;
      for (let k = gDebut[c], f = gDebut[c + 1]; k < f; k++) fn(hommes[gCorps[k]]);
    }
  }

  // ---- le chemin ------------------------------------------------------------
  // Tant que la porte tient, il n'y a pas de chemin à calculer : on est DEHORS,
  // en rase campagne, et l'on marche droit. Le graphe de voirie ne commence
  // qu'une fois le seuil franchi — c'est d'ailleurs la vérité du terrain, il
  // n'y a pas de rue avant la porte.
  function tracerVersDonjon(e) {
    if (e.trace || !voirie) return;
    // LE CHEMIN PART DE SA PORTE À LUI, et la clef de cache porte son nom :
    // avec une clef unique, la première escouade qui traçait imposait son
    // itinéraire à toutes les autres — quatre portes, un seul chemin, et trois
    // colonnes qui traversaient la ville pour aller prendre le départ d'une
    // quatrième.
    const dep = e.entree || entree;
    const depart = [dep.x, dep.y], arrivee = [objectif.x, objectif.y];
    // Une clef par escouade : elles partagent le même A* si le cache l'a déjà,
    // et sinon quinze calculs pour toute la bataille.
    e.trace = J.chemin(voirie, depart, arrivee, "bataille:donjon:" + (dep.nom || "?"));
    e.phase = "donjon";
  }

  // ---- la machine du soldat -------------------------------------------------
  function pousser(h, dt) {
    // La séparation, et c'est tout ce qu'il y a de « physique » ici. Sans elle,
    // trois cents hommes tiennent dans un mètre carré devant la porte et le
    // bouchon — qui est le sujet — n'existe pas.
    let sx = 0, sy = 0;
    autour(h.x, h.y, EPAULE * 2.4, (o) => {
      if (o === h) return;
      const dx = h.x - o.x, dy = h.y - o.y;
      const d2 = dx * dx + dy * dy;
      const min = EPAULE * 1.8;
      if (d2 > min * min || d2 === 0) return;
      const d = Math.sqrt(d2);
      sx += (dx / d) * (min - d); sy += (dy / d) * (min - d);
    });
    // SUR UNE VOIE, ON NE SE POUSSE QUE LE LONG DE LA VOIE. La séparation ne
    // connaît que les épaules des voisins et n'a jamais entendu parler d'un
    // mur : elle poussait donc dans les maisons tout ce qu'elle venait de
    // remettre dans la rue. On projette sa poussée sur la tangente — ce qui
    // n'ôte rien à ce qu'on lui demande, puisque ce qu'on veut d'elle dans une
    // rue est justement que les hommes se TASSENT les uns derrière les autres
    // au lieu de s'interpénétrer.
    if (h.surVoie) {
      const le = sx * h.tx + sy * h.ty;
      h.avance += le * 6 * dt;
      h.x += h.tx * le * 6 * dt; h.y += h.ty * le * 6 * dt;
      return;
    }
    h.x += sx * 6 * dt; h.y += sy * 6 * dt;
  }

  function versLe(h, bx, by, v, dt) {
    const dx = bx - h.x, dy = by - h.y, d = Math.hypot(dx, dy);
    if (d < .05) return 0;
    const pas = Math.min(v * dt, d);
    h.x += (dx / d) * pas; h.y += (dy / d) * pas;
    return d - pas;
  }

  function ennemiProche(h, rayon) {
    let m = null, dmin = rayon * rayon;
    autour(h.x, h.y, rayon, (o) => {
      // On n'achève pas un homme à terre, et l'on ne poursuit pas un fuyard :
      // dans les deux cas il a cessé d'être dans la bataille, et c'est ce qui
      // fait qu'il en reste quelqu'un à trouver après.
      if (o.camp === h.camp || o.etat === "mort" || o.etat === "blesse" ||
          o.etat === "deroute") return;
      const d = (o.x - h.x) ** 2 + (o.y - h.y) ** 2;
      if (d < dmin) { dmin = d; m = o; }
    });
    return m;
  }

  function frapper(h, o, dt) {
    h.prochain -= dt;
    if (h.prochain > 0) return;
    h.prochain += CADENCE;
    if (R() > TOUCHE) return;
    o.pv -= entre(DEGAT[0], DEGAT[1]);
    if (o.pv <= 0) tomber(o);
  }

  function tomber(o) {
    o.pv = 0;
    // Deux hommes sur cinq restent en vie par terre. Le tirage se fait ICI et
    // une seule fois : un blessé n'est jamais re-visé (il sort des cibles), et
    // c'est la plaie, plus tard, qui dira s'il se relève ou non.
    if (R() < PART_BLESSE) {
      o.etat = "blesse";
      o.saigne = entre(SAIGNE[0], SAIGNE[1]);
      compte.blesses++;
      // LE BLESSÉ EST LE SEUL FAIT QU'ON ÉCRIVE UN PAR UN, et c'est assumé :
      // c'est la scène qu'on vient chercher. Il ne bouge plus, il est à une
      // adresse, il parle, et il a un chef dont il peut donner le nom.
      noter("blesse", o.x, o.y, { dit: {
        camp: o.camp, escouade: o.camp === "assaut" ? o.escouade : null,
        chef: !!o.chef,
      } });
    } else {
      achever(o);
    }
    // LE CHOC EST LOCAL, et c'est toute la différence entre une morale qui
    // veut dire quelque chose et une jauge d'armée. Un homme ne sait pas
    // combien des siens sont tombés à l'autre bout de la ville ; il sait que
    // celui qui était à sa gauche n'y est plus.
    // ET LE CHOC S'ÉTEINT AVEC LA DISTANCE. Sans dégressivité, un mort au
    // milieu d'une presse touche cent hommes au même prix qu'il touche son
    // voisin de coude : dix-huit morts suffisaient à faire rompre cinquante
    // hommes en vingt secondes, ce qui n'est pas une armée mais une rumeur.
    // Un homme qui hurle par terre ne rassure personne : le choc est le même
    // qu'il soit mort ou blessé, et c'est la seule chose que le voisin voit.
    autour(o.x, o.y, VUE_MORT, (h) => {
      if (h.etat === "mort" || h.etat === "blesse" || h.camp !== o.camp) return;
      const d = Math.hypot(h.x - o.x, h.y - o.y);
      h.morale = Math.max(0, h.morale -
        CHOC * (1 - d / VUE_MORT) * (h.chef ? .5 : 1));
    });
    // Le premier sang de la journée, et la tête d'une escouade : deux faits
    // qu'on ne peut pas reconstituer après coup, et qui datent la bataille.
    noter("premier-sang", o.x, o.y, { clef: "premier-sang", dit: { camp: o.camp } });
    // QUI TOMBE MÉRITE UNE LIGNE, MAIS PAS N'IMPORTE QUI. À quatre cent
    // soixante-quinze escouades, un fait par chef d'escouade ferait quatre cent
    // soixante-quinze lignes que personne ne lira jamais — et l'on aurait
    // enrichi un journal de débogage en croyant écrire un document. On n'écrit
    // donc que ce qui CASSE LA CHAÎNE : un capitaine, qui emporte sa bannière ;
    // une tête, dont le corps n'aura plus jamais d'ordre neuf ; ou quelqu'un
    // qui a un nom, parce qu'un nom est ce qui rend une mort lisible.
    if (o.nom || o.capitaine || o.tete)
      noter(o.tete ? "tete-tombe" : "chef-tombe", o.x, o.y,
        { clef: (o.tete ? "tete:" : "chef:") + o.camp + ":" + (o.nom || o.aile),
          dit: { camp: o.camp, nom: o.nom, corps: o.corps, aile: o.aile,
                 escouade: o.escouade, mort: o.etat === "mort" } });
  }

  /** La plaie a tranché, ou le coup était franc. */
  function achever(o) {
    if (o.etat === "blesse") compte.blesses--;
    o.etat = "mort"; o.pv = 0;
    compte.morts++;
  }

  // UN BLESSÉ NE MEURT PAS FORCÉMENT, et il ne faut pas qu'il meure tous. Une
  // plaie qui s'arrête, c'est un homme qu'on retrouve au matin — c'est-à-dire
  // quelqu'un à qui la troupe peut parler trois jours plus tard. Les faire tous
  // mourir au bout de leur compte reviendrait à avoir écrit un délai de mort,
  // ce qui n'apporte rien à personne.
  function saigner(h, dt) {
    if (h.saigne === Infinity) return;
    h.saigne -= dt;
    if (h.saigne > 0) return;
    if (R() < PART_MEURT) {
      achever(h);
      noter("blesse-succombe", h.x, h.y, { dit: { camp: h.camp } });
    } else {
      h.saigne = Infinity;          // il tiendra jusqu'au matin
      noter("blesse-tient", h.x, h.y, { dit: { camp: h.camp } });
    }
  }

  function survie(h, dt) {
    // La morale reste entre zéro et un, et pas seulement pour la propreté : un
    // homme à −0,4 met une minute à repasser au-dessus du seuil quand le calme
    // revient, et l'on voit une armée qui ne se reprend jamais sans comprendre
    // pourquoi.
    // LA MORALE AVAIT UN BAS ET PAS DE HAUT. Elle ne tombait que des morts
    // qu'on voit — c'est-à-dire par en dessous, et rien ne la tenait par au-
    // dessus. Un homme qui a sa bannière debout dans son champ se reprend deux
    // fois et demie plus vite : ce n'est pas un bonus, c'est le seul mécanisme
    // par lequel un commandement PROTÈGE ses hommes au lieu de les déplacer.
    if (h.pv < PV * .5) h.morale = Math.max(0, h.morale - SANG * dt);
    else h.morale = Math.min(1, h.morale +
      REPRISE * dt * (sousLaBanniere(h) ? TIENT_BANN : 1) * REPRISE_HUMEUR(h));
    // L'HUMEUR DU CORPS, ET C'EST ICI QU'ELLE MORD. Elle était posée sur chaque
    // homme, portée par les six corps, exportée dans l'ordre de bataille — et
    // lue nulle part : les six corps étaient géométriquement distincts et
    // comportementalement identiques. Une mise en place qui ne veut rien dire.
    //
    //   ferme  — un PLANCHER de morale, jamais sous le seuil. Ronnel ne rompt
    //            pas, et c'est le seul point fixe qu'un lecteur ait dans toute
    //            la nuit. Ses hommes meurent ; ils ne partent pas.
    //   sourd  — ne rompt pas davantage, mais pour la raison inverse : il
    //            n'écoute rien, ni un ordre ni un mort. Vaugrain avance au
    //            cantique et il avancera jusqu'au bout.
    //   versatile — rompt TÔT et se reprend VITE. Tam reflue de cinquante pas
    //            et revient, trois fois. C'est lui qui alimente la peur des
    //            habitants, et c'est pour ça qu'il est collé à la ville.
    const seuil = h.humeur === "versatile" ? ROMPT_VERSATILE : ROMPT;
    if (h.humeur === "ferme" || h.humeur === "sourd")
      h.morale = Math.max(h.morale, PLANCHER_FERME);
    if (h.morale < seuil && h.etat !== "deroute") {
      h.etat = "deroute";
      compte.fuyards++;
    }
  }

  function soldat(h, dt) {
    if (h.etat === "mort") return;
    // Il reste dans la grille de voisinage, et c'est voulu : les vivants se
    // séparent de lui comme de n'importe quel corps, donc la presse s'ouvre
    // autour de celui qui est tombé. Personne n'a écrit ce vide-là.
    if (h.etat === "blesse") { saigner(h, dt); return; }
    // La tête ne se bat pas, ne marche pas, ne rompt pas. Elle décide, et son
    // pas de simulation se résume à ça.
    if (h.tete) return;
    survie(h, dt);
    // On repart libre à chaque pas : seul celui qui est effectivement sur sa
    // trace, plus bas, se redéclarera sur voie. Sans cette remise à zéro, un
    // homme qui quitte la colonne pour la mêlée garde une tangente périmée et
    // se fait pousser le long d'une rue qu'il a quittée.
    h.surVoie = false;

    if (h.etat === "deroute") {
      // Un chef à portée de bras le retient — mais il court plus vite que lui,
      // donc cette fenêtre-là se referme en quelques secondes.
      if (rallier(h, dt) && h.etat !== "deroute") return;
      // On fuit par où l'on est venu — un homme rompu ne cherche pas une
      // sortie, il refait le chemin qu'il connaît. ET IL LE REFAIT PAR LES
      // RUES : c'est la marche des fuyards civils, la même primitive, qui
      // descend le graphe de voirie de carrefour en carrefour. En ligne
      // droite, une déroute traversait le quartier de part en part.
      const [nx, ny] = dehors(h.entree);
      const bx = h.entree.x + nx * 400, by = h.entree.y + ny * 400;
      if (h.noeud === undefined) {
        h.v = FUITE; h.surRue = false; h.arc = null; h.venu = null; h.s = 0;
        h.noeud = noeudProche(h.x, h.y);
      }
      // Hors les murs il n'y a plus de rue, et c'est vrai : `marcher` rend
      // faux, on finit en rase campagne comme il se doit.
      if (!marcher(h, dt, bx, by, false)) versLe(h, bx, by, FUITE, dt);
      return;
    }

    // LE COUREUR NE SE BAT PAS TANT QU'IL PORTE. Il traverse la presse, et
    // c'est ce qui le rend fragile : il est visible, il est seul, et il ne
    // rend pas les coups. S'il tombe, l'ordre tombe avec lui — personne ne le
    // saura jamais, ni celui qui l'a envoyé, ni celle qui l'attendait.
    if (h.etat === "coureur") { courir(h, dt); return; }

    const proche = ennemiProche(h, ALLONGE + .6);
    if (proche) {
      noter("contact", h.x, h.y, { clef: "contact" });
      h.etat = "melee"; h.cible = proche;
      frapper(h, proche, dt);
      return;
    }
    if (h.etat === "melee") h.etat = h.camp === "garde" ? "tient" : "colonne";

    if (h.camp === "garde") {
      // Il tient son poste, et il y revient s'il en a été poussé. C'est tout
      // ce qu'un défenseur a le droit de faire ici, et c'est assez.
      if (h.poste) versLe(h, h.poste[0], h.poste[1], MARCHE, dt);
      return;
    }

    // --- l'assaillant ---------------------------------------------------
    const e = escouades[h.escouade];
    // L'ORDRE SE LIT SUR L'ESCOUADE, PAS SUR L'AILE. C'est toute la mécanique :
    // l'aile a reçu la décision de la tête, mais l'escouade n'en sait que ce
    // qui lui est PARVENU. Les deux peuvent différer pendant longtemps, et
    // c'est exactement là que la chaîne de commandement devient une histoire.
    const ordre = e ? e.ordre : "avancer";

    if (ordre === "repli") {
      // Un décrochement n'est pas une déroute : on s'en va en ordre, moins
      // vite, et l'on peut encore recevoir un ordre. C'est la différence entre
      // une armée qui recule et une armée qui n'existe plus.
      h.etat = "repli";
      const [nx, ny] = dehors(h.entree);
      versLe(h, h.entree.x + nx * 220, h.entree.y + ny * 220, MARCHE, dt);
      return;
    }
    if (ordre === "tenir") {
      h.etat = "forme";
      if (h.poste) versLe(h, h.poste[0], h.poste[1], MARCHE, dt);
      return;
    }

    const verrouDeLHomme = h.verrou;
    if (verrouDeLHomme && verrouDeLHomme.etat !== "ouvert") {
      const verrou = verrouDeLHomme;
      const d = Math.hypot(verrou.x - h.x, verrou.y - h.y);
      // SEPT HOMMES DE FRONT, ET PAS UN DE PLUS. C'est la largeur de la porte,
      // et c'est la seule chose qui compte dans tout l'assaut : les trois cents
      // ne valent pas trois cents, ils valent sept à la fois. Sans ce compte,
      // un cercle de deux mètres autour du seuil tient trente hommes, la porte
      // tombe en quarante secondes, et l'on a fabriqué une bataille où le
      // nombre décide — c'est-à-dire l'inverse d'un siège.
      if (h.front) {
        if (d < ALLONGE + 1.2) { h.etat = "assaut"; verrou.pv -= HACHE * dt; }
        else { h.etat = "colonne"; versLe(h, verrou.x, verrou.y,
                                          d > 40 ? MARCHE : CHARGE, dt); }
      } else if (d > 14) {
        h.etat = "colonne";
        versLe(h, verrou.x, verrou.y, d > 40 ? MARCHE : CHARGE, dt);
      } else {
        // Ceux qui attendent leur tour ne piétinent pas sur le seuil : ils se
        // rangent en arc devant, et c'est de là qu'ils voient tomber les leurs.
        h.etat = "forme";
        const a = (h.escouade / Math.max(1, escouades.length)) * Math.PI - Math.PI / 2;
        const [nx, ny] = dehors(h.entree);
        versLe(h, verrou.x + (nx * Math.cos(a) - ny * Math.sin(a)) * 9,
                  verrou.y + (ny * Math.cos(a) + nx * Math.sin(a)) * 9, MARCHE, dt);
      }
      return;
    }

    // --- LE PILLAGE ------------------------------------------------------
    //
    // Ici se décide ce qu'une armée devient une fois entrée. Ce n'est pas un
    // ordre : aucune tête ne dit « pillez », et aucune ne pourrait l'empêcher.
    // C'est un homme qui passe devant une porte et qui s'arrête, ou non.
    //
    // L'APPÉTIT VIENT DE L'HUMEUR DU CORPS, et c'est tout le personnage de
    // chacun. Ronnel le ferme ne s'arrête pas — c'est ce qui fait qu'il arrive.
    // Petit Tam le versatile s'arrête devant tout, et son corps se dissout dans
    // les trois cents premiers mètres. Vaugrain le sourd ne pille pas : il
    // brûle, ce qui prend moins de temps et ne rapporte rien.
    if (h.etat === "pille") { piller(h, dt); return; }
    if (bati && APPETIT[h.humeur || "-"] > 0 && !h.chef && !h.front) {
      // On ne quitte pas la colonne à chaque pas : un jet par seconde, tiré de
      // l'appétit. Sans ça, tout le monde s'arrête au premier pas et l'armée
      // n'avance jamais d'un mètre.
      h.tente = (h.tente || 0) - dt;
      if (h.tente <= 0) {
        h.tente = 1;
        if (R() < APPETIT[h.humeur || "-"]) {
          const b = maisonLibre(h.x, h.y, PORTEE_MAISON);
          if (b >= 0) {
            bati.etat[b] = 1; bati.forcees++;      // on la réserve en y allant
            h.maison = b; h.etat = "pille";
            h.reste_pille = entre(PILLE_S[0], PILLE_S[1]);
            return;
          }
        }
      }
    }

    // --- la porte est tombée : on remonte vers le donjon -----------------
    tracerVersDonjon(e);
    h.etat = "colonne";
    if (!e.trace) { versLe(h, objectif.x, objectif.y, MARCHE, dt); return; }
    const tr = e.trace;
    // ON GAGNE LE RAIL AVANT DE MONTER DESSUS.
    //
    // Poser un homme sur la trace, c'est l'y poser À `avance` — et `avance`
    // vaut zéro tant qu'il n'a pas marché. Le jour où la porte cède, tout ce
    // qui attendait derrière se retrouvait donc au seuil dans le même pas :
    // mesuré, cinq cent quarante-cinq mètres franchis en quatre secondes, à
    // travers tout ce qu'il y avait entre. Ce n'était pas une marche dans les
    // maisons, c'était un saut par-dessus — et c'est le prix que j'avais payé
    // sans le voir en remplaçant la visée par le placement.
    //
    // Donc deux temps : on marche jusqu'au seuil (dehors, en terrain libre,
    // où la ligne droite est honnête), et l'on n'entre sur le rail qu'une fois
    // arrivé. La colonne s'engouffre par la porte au lieu d'y apparaître.
    if (!h.surRail) {
      const q0 = surTrace(tr, 0);
      if (Math.hypot(q0[0] - h.x, q0[1] - h.y) > 2.5) {
        h.etat = "colonne";
        versLe(h, q0[0], q0[1], MARCHE, dt);
        return;
      }
      h.surRail = true;
      // Il entre AU SEUIL : son recul de rang le place derrière ceux qui sont
      // déjà passés, sans le renvoyer avant la porte.
      h.avance = (h.escouade * 20 + (h.chef ? 0 : 6)) * .45;
    }
    h.avance = Math.min(tr.long, h.avance + MARCHE * dt);
    // La colonne s'étire : chaque homme suit à son rang, décalé d'un côté de
    // la rue. C'est la même règle que les passants de `journee.js` — on tient
    // sa droite, et une ruelle de deux mètres se voit trop étroite pour deux
    // hommes de front.
    const recul = (h.escouade * 20 + (h.chef ? 0 : 6)) * .45;
    const q = surTrace(tr, Math.max(0, h.avance - recul));
    // ON EST POSÉ SUR LA TRACE, ON NE VISE PLUS UN POINT DESSUS.
    //
    // C'était un `versLe` vers ce point-ci, et c'était faux de deux façons à
    // la fois. D'abord l'homme avançait à MARCHE vers une cible qui reculait
    // elle-même à MARCHE : jamais rattrapée, l'écart ne faisait que croître.
    // Ensuite et surtout, viser un point c'est aller EN LIGNE DROITE vers lui
    // — donc couper tous les virages, et sur mille trois cents mètres de rues
    // tordues, marcher à travers les maisons. Mesuré sur une cuisson : 46 %
    // des vivants à plus de huit mètres de toute rue.
    //
    // L'A* était pourtant juste depuis le début. Il ne manquait que ceci :
    // s'en servir comme d'un RAIL et non comme d'une direction.
    h.x = q[0] + q[2] * h.cote * 1.4;
    h.y = q[1] + q[3] * h.cote * 1.4;
    // La tangente sert à la séparation : sur une voie, on ne se pousse que
    // vers l'avant ou vers l'arrière (voir `pousser`).
    h.surVoie = true; h.tx = q[3]; h.ty = -q[2];
    // ON ARRIVE QUAND ON EST ARRIVÉ, PAS QUAND LA TRACE S'ÉPUISE. Le test
    // portait sur la seule longueur parcourue : une escouade dont l'A* rendait
    // une trace dégénérée — vide, ou d'un mètre — avait `avance >= long - 1`
    // dès le premier pas, et l'on écrivait « le premier assaillant atteint le
    // Donjon Rouge » À LA PORTE, une seconde après l'avoir enfoncée. La
    // première cuisson à neuf mille cinq cents hommes le porte noir sur blanc :
    // t = 91,0 s, x = 3383, y = 613, soit six cent treize mètres trop tôt.
    //
    // C'est le pire genre de faute dans un document : elle ne casse rien, elle
    // se lit très bien, et elle est fausse. On demande donc la seule chose qui
    // soit vraie — être près du donjon.
    if (h.avance >= tr.long - 1 &&
        (objectif.x - h.x) ** 2 + (objectif.y - h.y) ** 2 < AU_DONJON ** 2) {
      h.etat = "arrive";
      noter("assaut-au-donjon", h.x, h.y, { clef: "au-donjon" });
    }
  }

  /** Un point sur une polyligne cumulée, plus sa normale. */
  function surTrace(tr, s) {
    const pts = tr.pts, cum = tr.cum;
    let a = 0, b = cum.length - 1;
    while (a < b - 1) { const m = (a + b) >> 1; if (cum[m] <= s) a = m; else b = m; }
    const p = pts[a], q = pts[Math.min(a + 1, pts.length - 1)];
    const l = Math.max(1e-6, cum[Math.min(a + 1, cum.length - 1)] - cum[a]);
    const t = Math.max(0, Math.min(1, (s - cum[a]) / l));
    const dx = (q[0] - p[0]) / l, dy = (q[1] - p[1]) / l;
    return [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, -dy, dx];
  }

  // ---- qui a le droit de cogner ---------------------------------------------
  // La place devant une porte se dispute, et elle se dispute par la DISTANCE :
  // les sept plus proches y sont, les autres attendent. On le décide une fois
  // par pas, pour toute l'armée — laisser chacun juger « reste-t-il une
  // place ? » revient à ce que trois cents hommes croient tous qu'il en reste
  // une, et l'on retrouve la grappe qu'on voulait éviter.
  //
  // LA RELÈVE EST GRATUITE : celui qui tombe cesse d'être le plus proche, et
  // le suivant prend sa place au pas d'après. Personne n'a écrit de rotation.
  function designerLeFront() {
    // UN FRONT PAR PORTE. Il n'y en avait qu'un, celui de la porte principale :
    // les trois autres verrous n'étaient donc frappés par personne, et leurs
    // colonnes attendaient devant un battant que rien n'entamait.
    // ON EFFACE UNE FOIS, PUIS CHAQUE PORTE DÉSIGNE LES SIENS. Chaque appel
    // remettait `front` à faux pour TOUTE l'armée avant de choisir : la
    // deuxième porte effaçait donc le front de la première, la troisième celui
    // de la deuxième, et il ne restait à la fin qu'un seul front pour quatre
    // battants. Symptôme : cinq cents hommes en « forme » et sept qui cognent,
    // pendant que trois portes ne recevaient pas un coup.
    for (const h of hommes) h.front = false;
    for (const v of verrous) frontDUnVerrou(v);
  }

  function frontDUnVerrou(verrou) {
    if (!verrou || verrou.etat === "ouvert") return;
    const cand = [];
    for (const h of hommes) {
      // Ni la tête, ni un coureur, ni une aile qu'on a fait décrocher. Sans
      // ça, un homme qui porte un ordre à travers la presse se retrouverait
      // désigné pour cogner la porte au passage — et l'ordre n'arriverait
      // jamais, pour une raison que personne n'aurait pu deviner.
      if (h.camp !== "assaut" || h.tete || h.etat === "mort" ||
          h.etat === "blesse" || h.etat === "deroute" ||
          h.etat === "coureur" || h.etat === "repli") continue;
      cand.push([(h.x - verrou.x) ** 2 + (h.y - verrou.y) ** 2, h]);
    }
    // Une sélection partielle, pas un tri : on ne classe pas trois cents hommes
    // vingt fois par seconde pour n'en garder que sept.
    for (let n = 0; n < FRONT_PORTE && n < cand.length; n++) {
      let m = n;
      for (let i = n + 1; i < cand.length; i++) if (cand[i][0] < cand[m][0]) m = i;
      const t = cand[n]; cand[n] = cand[m]; cand[m] = t;
      cand[n][1].front = true;
    }
  }

  // ---- la machine du verrou -------------------------------------------------
  function porteQuiCede() {
    for (const v of verrous) verrouQuiCede(v);
  }

  function verrouQuiCede(verrou) {
    if (!verrou || verrou.etat === "ouvert") return;
    const entree = verrou.porte;
    if (verrou.pv <= 0) {
      verrou.pv = 0;
      verrou.etat = "ouvert";
      noter("porte-enfoncee", verrou.x, verrou.y,
            { clef: "enfoncee:" + entree.nom, dit: { porte: entree.nom } });
      // Elle cède, et la garnison NE RECULE PAS. Elle avait d'abord reflué sur
      // le donjon — c'était propre, et c'était une bataille sans bataille :
      // quarante-cinq hommes traversaient la ville sans jamais croiser un fer,
      // et les trois cents entraient dans une ville vide. Un homme qui garde
      // une porte tient la brèche, parce que la brèche est plus étroite que
      // tout ce qu'il aura derrière. On resserre son poste sur le seuil : c'est
      // là que la vraie mêlée se donne, et sept contre sept.
      const [nx, ny] = dehors(entree);
      let i = 0;
      for (const h of hommes) {
        if (h.camp !== "garde" || !h.poste) continue;
        if (Math.hypot(h.poste[0] - entree.x, h.poste[1] - entree.y) > 60) continue;
        const c = (i % 7 - 3) * 0.9, r = Math.floor(i / 7) * 1.2;
        h.poste = [entree.x - nx * (3 + r) - ny * c, entree.y - ny * (3 + r) + nx * c];
        i++;
      }
    } else if (verrou.pv < verrou.max * .5) {
      verrou.etat = "cede";
      noter("porte-cede", verrou.x, verrou.y,
            { clef: "cede:" + entree.nom, dit: { porte: entree.nom } });
    }
  }

  // ===========================================================================
  // LA CHAÎNE DE COMMANDEMENT
  //
  // Trois verbes, et pas un de plus. On a tenu la liste courte exprès : un
  // vocabulaire d'ordres qui enfle est un vocabulaire dont chaque mot cesse
  // d'avoir des conséquences visibles, et l'on ne raconte plus rien.
  //
  //   avancer   marcher sur l'objectif — la porte, puis le donjon
  //   tenir     rester où l'on est. On se bat si l'on est joint, on n'avance pas
  //   repli     décrocher vers l'arrière, en ordre, sans avoir rompu
  //
  // « tenir » est le plus important des trois, et c'est le moins évident : une
  // aile en réserve ne meurt pas, ne voit pas mourir, et ne rompt donc pas.
  // Toute la différence entre trois cents hommes qui s'entassent sur un seuil
  // et une armée qui en engage cent.
  // ===========================================================================

  /** Le nom du chef d'un corps — ce qu'on écrit au lieu d'un numéro d'aile. */
  const nomDuCorps = (id) => {
    const c = CORPS.find((x) => x.id === id);
    return c ? c.nom : null;
  };

  /** L'aile d'un homme, ou null s'il n'en a pas (garde, tête). */
  const ailleDe = (h) => (h.camp === "assaut" && !h.tete ? ailes[h.aile] : null);

  /** Ce qu'une aile a encore debout, sur ce qu'elle avait. */
  function forceDe(a) {
    let vif = 0, tot = 0;
    for (const h of hommes) {
      if (h.camp !== "assaut" || h.tete || h.aile !== a.id) continue;
      tot++;
      if (h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute") vif++;
    }
    return tot ? vif / tot : 0;
  }

  // --- ce que la tête décide -------------------------------------------------
  // Sa doctrine tient en trois lignes, et c'est assez. On ne lui écrit pas une
  // intelligence : on lui écrit une DOCTRINE, c'est-à-dire quelques règles
  // simples qu'elle applique sans voir le détail — ce qui est exactement la
  // situation d'un homme à cent cinquante mètres de la porte.
  //
  // SIX TÊTES, ET AUCUNE NE COMMANDE LES AUTRES. Chacune ne voit que son
  // corps, ne délibère que pour lui, et ignore parfaitement ce que les cinq
  // autres viennent de décider. C'est de là que sortent les seules images
  // qu'on est venu chercher : deux corps qui pressent la même porte en même
  // temps, ou aucun. Personne n'a écrit ce désordre — il tombe de six horloges
  // qui ne battent pas ensemble.
  function decider(dt) {
    for (const tete of tetes) {
      if (tete.etat === "mort") continue;
      tete.decide -= dt;
      if (tete.decide > 0) continue;
      tete.decide = entre(DELIBERE[0], DELIBERE[1]);
      // Les ailes de SON corps, et pas une de plus.
      const sien = ailes.filter((a) => a.corps === tete.corps);
      for (const a of sien) {
        let veut;
        if (forceDe(a) < 0.4) veut = "repli";
        // SA porte, pas celle du voisin. Avec le verrou global, les quatre
        // têtes ordonnaient d'avancer dès que la première porte cédait — trois
        // corps se jetaient donc sur des battants encore debout parce qu'un
        // autre était tombé à l'autre bout de la ville, et sans qu'aucun
        // coureur ait porté la nouvelle.
        else if (tete.verrou && tete.verrou.etat === "ouvert") veut = "avancer";
        // TANT QUE LA PORTE TIENT, UNE SEULE AILE LA PRESSE — la première du
        // corps. Les autres sont en réserve, non par prudence mais par
        // arithmétique : sept hommes cognent, et ceux qui attendent derrière
        // ne font qu'y perdre leur morale en regardant tomber les leurs.
        else veut = a === sien[0] ? "avancer" : "tenir";
        if (veut === a.ordre) continue;
        a.ordre = veut;
        noter("ordre", tete.x, tete.y,
              { dit: { corps: tete.corps, chef: tete.nom, aile: a.id,
                       // Le rang DANS SON CORPS, parce que « l'aile n° 17 » ne
                       // veut rien dire pour personne : c'est un indice de
                       // tableau, et il ne dit ni à qui elle est ni où elle est.
                       rang: a.rang,
                       ordre: veut, force: +forceDe(a).toFixed(2) } });
      }
    }
  }

  // --- comment il descend ----------------------------------------------------
  function transmettre(dt) {
    for (const e of escouades) {
      const a = ailes[e.aile];
      if (!a) continue;
      // SOURD DE NAISSANCE. Une escouade peut devenir sourde en route — plus
      // de bannière, plus personne à envoyer — et celle-là peut réentendre le
      // jour où un chef se relève. Celle de Vaugrain, non : ses deux mille
      // marchent au cantique et aucun ordre ne les a jamais concernés. On sort
      // avant tout le reste, sans quoi on lui chercherait un coureur à chaque
      // pas pour lui porter un ordre qu'elle n'écoutera pas.
      if (e.sourd_ne) continue;

      // L'ordre est déjà arrivé, ou il est en route.
      if (e.ordre === a.ordre) { e.attend = null; continue; }
      if (e.attend !== null) {
        // Par la bannière : il suffit d'attendre.
        e.attend -= dt;
        if (e.attend <= 0) { e.ordre = a.ordre; e.attend = null; }
        continue;
      }
      // UN COUREUR QUI TOMBE BLOQUAIT SON ESCOUADE POUR TOUJOURS. On se
      // contentait de `if (e.coureur) continue` : le jour où l'homme meurt en
      // chemin, la référence reste, l'escouade attend un ordre que plus
      // personne ne porte, et elle n'est même pas déclarée sourde — elle est
      // simplement oubliée, en silence, jusqu'à la fin du sac.
      //
      // C'est le pire genre de faute dans un fichier qu'on cuit : elle ne
      // casse rien, elle ne se voit pas, et elle enlève juste une escouade de
      // l'histoire. On constate donc la chute, on l'écrit — parce qu'un ordre
      // perdu est exactement le genre de fait qu'on est venu chercher — et
      // l'on rouvre la porte à un second messager.
      if (e.coureur) {
        const c = e.coureur;
        if (c.etat === "coureur") continue;   // il court encore
        if (c.etat === "mort" || c.etat === "blesse" || c.etat === "deroute")
          noter("coureur-tombe", c.x, c.y,
                { dit: { vers: e.id, ordre: c.porte } });
        e.coureur = null;
      }

      const chef = chefDe(e.id);
      const b = a.banniere;
      // LA BANNIÈRE NE PARLE QU'À QUI LA VOIT, ET QU'À UN CHEF. Un homme
      // regarde le dos de celui de devant ; c'est le chef qui lève la tête.
      if (b.debout && chef &&
          (chef.x - b.x) ** 2 + (chef.y - b.y) ** 2 < VUE_BANNIERE ** 2) {
        e.attend = DELAI_BANN;
        continue;
      }
      // Sinon, il faut y aller. Et s'il n'y a personne à envoyer, l'escouade
      // est SOURDE : elle exécutera son dernier ordre jusqu'au bout.
      if (!envoyerCoureur(a, e)) {
        if (!e.sourde) {
          e.sourde = true;
          const p = centreDe(e.id);
          if (p) noter("escouade-sourde", p[0], p[1],
                       { clef: "sourde:" + e.id,
                         dit: { escouade: e.id, aile: a.id, ordre: e.ordre } });
        }
      }
    }
  }

  function chefDe(id) {
    for (const h of hommes)
      if (h.camp === "assaut" && h.escouade === id && h.chef &&
          h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute") return h;
    return null;
  }

  function centreDe(id) {
    let x = 0, y = 0, n = 0;
    for (const h of hommes) {
      if (h.camp === "assaut" && h.escouade === id &&
          h.etat !== "mort" && h.etat !== "blesse") { x += h.x; y += h.y; n++; }
    }
    return n ? [x / n, y / n] : null;
  }

  // UN COUREUR EST UN HOMME EN MOINS, et c'est le prix. On le prend dans
  // l'escouade du capitaine — pas dans celle qu'on veut joindre, qui par
  // définition n'entend rien.
  function envoyerCoureur(a, e) {
    // QUI ENVOIE. C'était le capitaine, et lui seul — ce qui rendait cette
    // fonction rigoureusement inatteignable : on n'envoie un coureur que
    // lorsque la bannière est tombée, et la bannière tombe exactement quand le
    // capitaine tombe. La branche entière était morte par construction, et
    // l'aile passait droit à « sourde » sans que personne ait couru.
    //
    // Un ordre ne dépend pas d'un seul homme : à défaut du capitaine, c'est le
    // premier chef encore debout de l'aile qui dépêche quelqu'un. L'aile n'est
    // muette que lorsqu'il ne lui reste plus un seul gradé.
    const chef = (a.capitaine && a.capitaine.etat !== "mort" &&
                  a.capitaine.etat !== "blesse" && a.capitaine.etat !== "deroute")
                 ? a.capitaine : premierChefDe(a.id);
    if (!chef) return false;
    const but = centreDe(e.id);
    if (!but) return false;
    const src = chef.escouade;
    for (const h of hommes) {
      if (h.camp !== "assaut" || h.escouade !== src) continue;
      if (h.chef || h.capitaine || h.tete) continue;
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute" ||
          h.etat === "coureur") continue;
      h.etat = "coureur";
      h.porte = a.ordre;
      h.chez = e.id;
      e.coureur = h;
      noter("coureur-part", h.x, h.y,
            { dit: { aile: a.id, rang: a.rang, corps: a.corps,
                     chef: nomDuCorps(a.corps), vers: e.id, ordre: a.ordre } });
      return true;
    }
    return false;
  }

  function courir(h, dt) {
    const e = escouades[h.chez];
    const but = centreDe(h.chez);
    if (!e || !but) { rendreCoureur(h); return; }
    const d = versLe(h, but[0], but[1], COURSE, dt);
    if (d > 4) return;
    // Il est arrivé. L'ordre entre — et s'il n'y avait plus de chef, il en
    // fait un : c'est la seule façon dont une escouade sourde redevient
    // commandable, et ça vaut d'être vu passer.
    e.ordre = h.porte;
    e.attend = null;
    if (e.sourde) {
      e.sourde = false;
      noter("escouade-reprise", h.x, h.y,
            { dit: { escouade: e.id, ordre: e.ordre } });
    }
    if (!chefDe(e.id)) {
      h.chef = true;
      noter("nouveau-chef", h.x, h.y, { dit: { escouade: e.id } });
    }
    noter("coureur-arrive", h.x, h.y, { dit: { vers: e.id, ordre: e.ordre } });
    rendreCoureur(h, e.id);
  }

  function rendreCoureur(h, chez) {
    const e = escouades[h.chez];
    if (e && e.coureur === h) e.coureur = null;
    // Il reste où il est arrivé : on ne renvoie personne en arrière dans une
    // bataille. Son escouade devient celle qu'il vient de joindre.
    if (chez !== undefined) h.escouade = chez;
    h.porte = null; h.chez = null;
    h.etat = "colonne";
  }

  // --- la bannière -----------------------------------------------------------
  // Elle suit son porteur tant qu'il est debout, elle reste où il est tombé
  // ensuite. Sa chute est le seul choc de morale du module qui ne décroisse
  // pas avec la distance — et c'est voulu : on ne voit pas tomber un homme à
  // cent mètres, on voit tomber une bannière.
  function bannieres(dt) {
    for (const a of ailes) {
      const c = a.capitaine;
      const bas = !c || c.etat === "mort" || c.etat === "blesse" ||
                  c.etat === "deroute";
      if (a.banniere.debout && bas) {
        a.banniere.debout = false;
        a.releve = RELEVE;
        for (const h of hommes)
          if (h.camp === "assaut" && !h.tete && h.aile === a.id &&
              h.etat !== "mort" && h.etat !== "blesse")
            h.morale = Math.max(0, h.morale - CHOC_BANN);
        // Le corps et le rang, comme pour les ordres : une bannière appartient
        // à quelqu'un, et « l'aile n° 13 » n'appartient à personne.
        noter("banniere-tombe", a.banniere.x, a.banniere.y,
              { dit: { aile: a.id, corps: a.corps, rang: a.rang,
                       chef: nomDuCorps(a.corps) } });
        continue;
      }
      if (a.banniere.debout) { a.banniere.x = c.x; a.banniere.y = c.y; continue; }
      // La relever prend du temps, et il faut quelqu'un pour la lever.
      a.releve -= dt;
      if (a.releve > 0) continue;
      const n = premierChefDe(a.id);
      if (!n) { a.releve = RELEVE; continue; }
      n.capitaine = true;
      a.capitaine = n;
      a.banniere = { debout: true, x: n.x, y: n.y };
      noter("banniere-relevee", n.x, n.y,
            { dit: { aile: a.id, corps: a.corps, rang: a.rang,
                     chef: nomDuCorps(a.corps) } });
    }
  }

  function premierChefDe(id) {
    for (const h of hommes)
      if (h.camp === "assaut" && !h.tete && h.aile === id && h.chef &&
          h.etat !== "mort" && h.etat !== "blesse" && h.etat !== "deroute") return h;
    return null;
  }

  /** Voit-il sa bannière ? C'est ce qui le fait tenir. */
  function sousLaBanniere(h) {
    const a = ailleDe(h);
    if (!a || !a.banniere.debout) return false;
    return (h.x - a.banniere.x) ** 2 + (h.y - a.banniere.y) ** 2 < VUE_BANNIERE ** 2;
  }

  // --- le ralliement ---------------------------------------------------------
  // UN HOMME QUI ROMPT N'EST PLUS PERDU. C'était le cas jusqu'ici : `deroute`
  // était un état absorbant, et l'armée ne faisait que se vider. Un chef vivant
  // qui l'a encore sous la main le ramène — et comme un fuyard court plus vite
  // qu'un chef, ça ne marche que dans les premiers instants. C'est bien : le
  // ralliement doit être une chose qu'on rate le plus souvent.
  function rallier(h, dt) {
    let chef = null;
    autour(h.x, h.y, RALLIE_M, (o) => {
      if (chef || o.camp !== h.camp) return;
      if (!o.chef && !o.capitaine) return;
      if (o.etat === "mort" || o.etat === "blesse" || o.etat === "deroute") return;
      chef = o;
    });
    if (!chef) return false;
    h.morale = Math.min(1, h.morale + RALLIE_TAUX * dt);
    if (h.morale < RALLIE_SEUIL) return true;
    h.etat = "forme";
    compte.fuyards--;
    compte.rallies++;
    noter("ralliement", h.x, h.y, { dit: { escouade: h.escouade } });
    return true;
  }

  // ---- les foyers : on fuit une MASSE, pas un homme -------------------------
  // La menace se cherchait sur les quatre cent vingt-cinq corps, pour chaque
  // habitant qui panique et à chaque pas : deux mille fois quatre cent
  // vingt-cinq, vingt fois par seconde. C'était le seul endroit de la couche
  // qui ne passait pas à l'échelle — et c'était en plus le mauvais modèle.
  //
  // On agrège donc les soldats vivants par carrés de quarante mètres, et l'on
  // ne garde que les carrés qui portent au moins trois hommes. Trois douzaines
  // de foyers au lieu de quatre cents corps, et surtout : UN HOMME SEUL N'EST
  // PAS UNE ARMÉE. Un fuyard qui traverse une rue ne vide plus le quartier,
  // ce qui est exactement ce qu'on observe — on s'écarte d'un soldat, on fuit
  // une troupe.
  let foyers = [];
  function fondreLesFoyers() {
    const cases = new Map();
    for (const h of hommes) {
      // Un blessé n'est pas une armée : on ne fuit pas un homme à terre, on
      // s'en approche ou l'on passe au large. C'est la même règle que le
      // fuyard isolé, et pour la même raison.
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      const c = Math.floor(h.x / FOYER_M) + ":" + Math.floor(h.y / FOYER_M);
      let f = cases.get(c);
      if (!f) cases.set(c, f = { x: 0, y: 0, n: 0 });
      f.x += h.x; f.y += h.y; f.n++;
    }
    foyers = [];
    for (const f of cases.values())
      if (f.n >= FOYER_MIN) foyers.push({ x: f.x / f.n, y: f.y / f.n, n: f.n });
  }

  /** Le foyer le plus proche, et sa distance. Rend null s'il n'y a rien. */
  function foyerProche(x, y) {
    let m = null, dmin = Infinity;
    for (const f of foyers) {
      const d = (f.x - x) ** 2 + (f.y - y) ** 2;
      if (d < dmin) { dmin = d; m = f; }
    }
    return m ? { f: m, d: Math.sqrt(dmin) } : null;
  }

  // ---- le réseau : fuir PAR LES RUES ----------------------------------------
  // La panique était un pilotage libre : on s'éloignait du fer en ligne droite,
  // donc à travers les maisons. C'était le défaut le plus visible de la couche
  // — une ville dont les murs arrêtent une armée mais pas ses habitants.
  //
  // ON NE CALCULE POURTANT AUCUN CHEMIN. Un A* par fuyard, c'est deux mille A*
  // par seconde, et il n'en est pas question. On marche le graphe de proche en
  // proche : arrivé à un carrefour, on prend la branche qui éloigne le plus (ou
  // qui rapproche le plus, quand on rentre), et l'on ne fait pas demi-tour. Un
  // homme qui fuit ne connaît pas le plan de la ville : il prend la rue qui
  // s'éloigne. C'est le bon modèle ET le modèle bon marché, ce qui n'arrive pas
  // souvent.
  const SEAU = 100;
  let reseau = null;
  function tisserReseau() {
    if (reseau || !voirie) return;
    const seau = new Map();
    for (const [id, n] of voirie.noeuds) {
      const c = Math.floor(n.xyz[0] / SEAU) + ":" + Math.floor(n.xyz[1] / SEAU);
      let l = seau.get(c);
      if (!l) seau.set(c, l = []);
      l.push(id);
    }
    reseau = { seau, noeuds: voirie.noeuds };
  }

  function noeudProche(x, y) {
    if (!reseau) return null;
    const ci = Math.floor(x / SEAU), cj = Math.floor(y / SEAU);
    let meil = null, dmin = Infinity;
    for (let r = 1; r < 12 && meil === null; r++) {
      for (let di = -r; di <= r; di++) for (let dj = -r; dj <= r; dj++) {
        if (r > 1 && Math.abs(di) < r && Math.abs(dj) < r) continue;
        for (const id of reseau.seau.get((ci + di) + ":" + (cj + dj)) || []) {
          const p = reseau.noeuds.get(id).xyz;
          const d = (p[0] - x) ** 2 + (p[1] - y) ** 2;
          if (d < dmin) { dmin = d; meil = id; }
        }
      }
    }
    return meil;
  }

  // Une rue n'est pas un segment : c'est une polyligne, et la suivre est ce qui
  // fait la différence entre longer un mur et le traverser en diagonale. On
  // oriente et l'on cumule UNE FOIS par lien — les liens sont partagés par tous
  // ceux qui fuient dans la même rue, ce qui est le cas général.
  const _arcs = new WeakMap();
  function arcDe(lien) {
    let a = _arcs.get(lien);
    if (a) return a;
    const t = lien.arete.trace;
    const pts = lien.sens > 0 ? t : t.slice().reverse();
    const cum = new Float64Array(pts.length);
    for (let i = 1; i < pts.length; i++)
      cum[i] = cum[i - 1] + Math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1]);
    a = { pts, cum, long: cum[cum.length - 1] || 0, vers: lien.vers };
    _arcs.set(lien, a);
    return a;
  }

  function choisirLien(noeudId, bx, by, fuir, venu) {
    const n = reseau && reseau.noeuds.get(noeudId);
    if (!n || !n.liens.length) return null;
    let meil = null, best = -Infinity;
    for (const l of n.liens) {
      const p = reseau.noeuds.get(l.vers);
      if (!p) continue;
      const d = Math.hypot(p.xyz[0] - bx, p.xyz[1] - by);
      // ON NE FAIT PAS DEMI-TOUR — sauf en cul-de-sac, où la pénalité se laisse
      // battre parce qu'il n'y a rien d'autre. Sans ça, un fuyard oscille entre
      // deux carrefours dès que la menace le dépasse.
      let s = (fuir ? d : -d) - (l.vers === venu ? 1e4 : 0);
      if (s > best) { best = s; meil = l; }
    }
    return meil;
  }

  /** Un pas de marche sur le réseau. Rend faux quand la rue manque. */
  function marcher(p, dt, bx, by, fuir) {
    if (!reseau) return false;
    // D'abord GAGNER LA RUE. On panique où l'on est — sur un seuil, au milieu
    // d'une cour —, pas sur un carrefour : sans ce premier bout en ligne
    // droite, le fuyard se téléporte de trente mètres à son premier pas.
    if (!p.surRue) {
      const n = reseau.noeuds.get(p.noeud);
      if (!n) return false;
      const dx = n.xyz[0] - p.x, dy = n.xyz[1] - p.y, d = Math.hypot(dx, dy);
      const pas = p.v * dt;
      if (d > pas) { p.x += (dx / d) * pas; p.y += (dy / d) * pas; return true; }
      p.x = n.xyz[0]; p.y = n.xyz[1]; p.surRue = true;
      return true;
    }
    let reste = p.v * dt, garde = 0;
    while (reste > 0 && garde++ < 8) {
      if (!p.arc) {
        const l = choisirLien(p.noeud, bx, by, fuir, p.venu);
        if (!l) return false;
        p.arc = arcDe(l); p.venu = p.noeud; p.noeud = l.vers; p.s = 0;
        if (p.arc.long <= 0) { p.arc = null; continue; }
      }
      const dispo = p.arc.long - p.s;
      if (reste < dispo) { p.s += reste; reste = 0; }
      else { reste -= dispo; p.arc = null; }
    }
    if (p.arc) { const q = surTrace(p.arc, p.s); p.x = q[0]; p.y = q[1]; }
    else { const n = reseau.noeuds.get(p.noeud);
           if (n) { p.x = n.xyz[0]; p.y = n.xyz[1]; } }
    return true;
  }

  // ---- la machine du bourgeois ----------------------------------------------
  // Cinq états, et ils ne tournent QUE sur ceux que `derange` a pris en charge :
  // les quatre cent mille autres n'existent pas ici, et c'est ce qui rend la
  // chose gratuite.
  //
  //   saisi    on ne part pas en courant : on se retourne, et l'on comprend
  //   fuite    par les rues, en s'éloignant de la masse
  //   rentre   la peur passée, on regagne son seuil — par les rues aussi
  //   terre    chez soi, porte fermée, et l'on ne ressort pas tout de suite
  //   contre   le guet, qui va dans l'autre sens
  /** Rendre quelqu'un à sa journée écrite. */
  // Chaque enregistrement CONNAÎT SA PLACE (`p.i`), et le dernier la reprend
  // quand on retire au milieu. Sans ça, reprendre la place de quelqu'un
  // demandait de balayer les quatre mille — pour chacun des dix-huit mille
  // habitants dehors, à chaque image. La page s'est arrêtée net, et c'était
  // mérité : une éviction doit coûter un échange, pas une recherche.
  function oublier(i) {
    const p = paniques[i];
    if (!p) return;
    if (p.cel._peur) p.cel._peur[p.k] = null;
    const dernier = paniques.pop();
    if (i < paniques.length) { paniques[i] = dernier; dernier.i = i; }
  }

  // Ceux qui sont déjà rentrés : leur place est la première qu'on reprend.
  // La liste se refait à chaque pas, en même temps qu'on les parcourt de toute
  // façon — elle ne coûte donc rien de plus qu'un `push`.
  let abris = [];

  function bourgeois(dt) {
    abris.length = 0;
    // À l'envers, parce qu'on retire en cours de route.
    for (let i = paniques.length - 1; i >= 0; i--) {
      const p = paniques[i];
      if (p.etat === "terre") abris.push(p);
      const m = foyerProche(p.x, p.y);
      p.age_t += dt;

      if (p.etat === "saisi") {
        p.attente -= dt;
        if (p.attente <= 0) {
          p.etat = p.contre ? "contre"
                 : p.prend === "assaut" ? "arme"
                 : p.prend === "garde" ? "barre" : "fuite";
          p.age_t = 0;
          if (p.prend) armer(p);
        }
        continue;
      }

      // IL A PRIS QUELQUE CHOSE ET IL Y VA. Il ne s'arrête pas au bord comme le
      // guet : il entre dedans. On ne le fait pas SE BATTRE — il n'est pas un
      // corps de la bataille, et le sac n'attend pas de fil pour lui — mais il
      // a quitté sa journée écrite pour de bon, il est dans la rue avec un
      // outil qui coupe, et c'est tout ce qu'il faut pour qu'on le retrouve au
      // matin et qu'on lui demande où il était.
      if (p.etat === "arme") {
        if (m) marcher(p, dt, m.f.x, m.f.y, false);
        continue;
      }

      // IL BARRE SA PORTE. Il ne bouge plus, il ne fuit plus, et il est chez
      // lui — donc à une adresse. C'est le seul de cette couche qui redevienne
      // un habitant sans avoir cessé d'être un acteur : demain il dira ce
      // qu'il a vu passer devant son seuil, et il aura une raison de mentir.
      if (p.etat === "barre") continue;

      if (p.etat === "contre") {
        // Il s'avance jusqu'à voir, et il s'arrête là. Un homme du guet n'est
        // pas suicidaire : il regarde, et il ira le dire.
        if (!m) { p.etat = "rentre"; continue; }
        if (m.d > APPROCHE) marcher(p, dt, m.f.x, m.f.y, false);
        // Il est arrivé au bord et il a vu. C'est le seul fait de la couche de
        // peur qui produise un TÉMOIN au sens plein : un homme du guet, qui a
        // un nom dans la ville, et qui ira le raconter au poste.
        //
        // UNE FOIS PAR HOMME, et le verrou est sur l'enregistrement, pas dans
        // le jeu de clefs : il s'arrête au bord et il y reste, donc la
        // condition reste vraie vingt fois par seconde jusqu'à la fin du sac.
        // PAR QUARTIER, PAS PAR HOMME — et c'est la troisième fois qu'on
        // apprend la même chose dans ce fichier. Tout fait émis depuis une
        // couche qui tourne PAR PERSONNE (la peur, la rumeur, le guet) doit
        // être verrouillé PAR LIEU, sinon il sort au rythme de la population
        // et il enterre la guerre sous sa propre rumeur. Vingt-huit hommes du
        // guet disaient vingt-huit fois la même phrase depuis deux endroits.
        //
        // Ce qu'on veut savoir tient en une ligne par quartier : le guet a vu,
        // à telle heure, et voilà combien d'hommes en armes il a comptés.
        else if (!p.vu) {
          p.vu = true;
          noter("guet-a-vu", p.x, p.y,
                { clef: "guet:" + situer(p.x, p.y).zone,
                  dit: { hommes: m.f.n } });
        }
        continue;
      }

      if (p.etat === "fuite") {
        if (!m) { p.etat = "rentre"; p.age_t = 0; continue; }
        // ON NE RENTRE PAS TANT QU'ON ENTEND. Le seuil de retour est plus haut
        // que celui de départ : sans cette hystérésis, un habitant posé juste à
        // la limite bascule entre fuir et rentrer à chaque pas, et l'on voit
        // une rue de gens qui tremblent sur place.
        if (m.d > ALERTE * 1.5 && p.age_t > FUITE_MIN) { p.etat = "rentre"; p.age_t = 0; }
        else marcher(p, dt, m.f.x, m.f.y, true);
        continue;
      }

      if (p.etat === "rentre") {
        if (m && m.d < ALERTE) { p.etat = "fuite"; p.age_t = 0; p.venu = null; continue; }
        const d = Math.hypot(p.chez[0] - p.x, p.chez[1] - p.y);
        // Le dernier bout se fait en ligne droite : le carrefour n'est pas la
        // porte, et l'on finit toujours par traverser sa rue.
        if (d < 12) { p.x = p.chez[0]; p.y = p.chez[1];
                      p.etat = "terre"; p.attente = CALME; continue; }
        if (p.age_t > RENTRE_MAX || !marcher(p, dt, p.chez[0], p.chez[1], false)) {
          // On a renoncé : la marche gloutonne peut tourner dans un quartier
          // sans jamais retomber sur sa rue. Alors on se terre où l'on est,
          // dans le premier renfoncement — ce qui vaut mieux qu'un habitant qui
          // fait des ronds jusqu'à la fin de la partie.
          p.etat = "terre"; p.attente = CALME;
        }
        continue;
      }

      // terre
      p.attente -= dt;
      if (p.attente <= 0 && (!m || m.d > ALERTE * 1.5)) oublier(i);
    }
  }

  // La rumeur court plus vite que la colonne : on ne panique pas seulement de
  // ce qu'on voit, mais de ce qu'on voit COURIR. C'est ce qui vide une rue
  // avant que le premier soldat n'y soit entré, et il n'y a rien de plus vrai
  // dans tout ce module. Une grille de vingt mètres sur les seuls paniqués —
  // deux mille au plus, donc rien.
  let semis = new Map();
  function semerLaRumeur() {
    semis.clear();
    for (const p of paniques) {
      if (p.etat === "terre" || p.contre) continue;   // on court après ceux qui courent
      const c = Math.floor(p.x / RUMEUR) + ":" + Math.floor(p.y / RUMEUR);
      let l = semis.get(c);
      if (!l) semis.set(c, l = []);
      l.push(p);
    }
  }

  function rumeur(x, y) {
    let n = 0;
    const ci = Math.floor(x / RUMEUR), cj = Math.floor(y / RUMEUR);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) {
      const l = semis.get((ci + i) + ":" + (cj + j));
      if (!l) continue;
      for (const p of l)
        if ((p.x - x) ** 2 + (p.y - y) ** 2 < RUMEUR * RUMEUR && ++n >= RUMEUR_MIN)
          return true;
    }
    return false;
  }

  /**
   * LE VETO. `foule2d` appelle ceci pour chaque habitant qu'il va dessiner,
   * juste après avoir lu sa journée écrite. On rend vrai quand on a pris cet
   * habitant en charge — et alors c'est nous qui disons où il est.
   *
   * Il faut que ce soit BON MARCHÉ, parce que c'est appelé des dizaines de
   * milliers de fois par calcul : tant que la bataille dort, c'est un test.
   */
  function derange(cel, k, P) {
    // LE VETO NE TIENT PAS À L'HORLOGE, IL TIENT À LA BATAILLE. Il était gardé
    // par `marche` : suspendre l'assaut renvoyait d'un coup tous les fuyards à
    // la place que leur journée écrite leur donnait — c'est-à-dire qu'on les
    // voyait se téléporter à leur puits pendant qu'une armée leur passait
    // dessus. Une pause arrête le temps, elle n'efface pas la peur.
    // Trois tests avant toute chose, dans l'ordre du moins cher : pas de
    // bataille, pas de masse à fuir, et l'on rend la main sans avoir rien
    // alloué. C'est le chemin que prennent quatre cent mille personnes.
    if (!hommes.length || temps <= 0) return false;
    const p = cel._peur ? cel._peur[k] : null;
    if (p) {
      P.x = p.x; P.y = p.y;
      // CELUI QUI A BARRÉ SA PORTE EST CHEZ LUI, ET IL Y RESTE. Le confondre
      // avec un fuyard le remettrait en mouvement dans la rue, alors que tout
      // son propos est de ne plus en bouger.
      P.quoi = (p.etat === "terre" || p.etat === "saisi" || p.etat === "barre")
               ? "sur-place" : "route";
      // Chacun garde sa couleur : on doit voir l'or du guet remonter la rue que
      // tout le monde descend, et le fer de ceux qui viennent de la prendre y
      // remonter avec lui — pour l'autre camp.
      P.vers = p.contre ? "ronde"
             : p.prend === "assaut" ? "armes"
             : p.prend === "garde" ? "barre" : "fuite";
      return true;
    }
    // On ne prend en charge que ceux qui sont DEHORS. Celui qui est chez lui y
    // reste : il a fermé sa porte, ce qui est exactement ce qu'on ferait.
    if (P.quoi === "chez") return false;
    if (!foyers.length) return false;
    const m = foyerProche(P.x, P.y);
    const vu = m && m.d < ALERTE;
    if (!vu && !rumeur(P.x, P.y)) return false;

    // LE PLAFOND N'EST PAS PREMIER ARRIVÉ, PREMIER SERVI. Il l'était, et l'on
    // atteignait les quatre mille places en six minutes — tenues pour l'essentiel
    // par des gens qui avaient paniqué par ouï-dire à huit cents mètres de là.
    // Résultat : un homme sur le point d'être piétiné se voyait refuser la
    // peur, parce qu'un autre s'était affolé le premier à l'autre bout de la
    // ville. Celui qui VOIT passe donc devant, en prenant la place de quelqu'un
    // qui est déjà rentré chez lui — la lui reprendre ne coûte rien : il est
    // sous son toit, et sa journée écrite l'y met aussi.
    if (paniques.length >= PANIQUE_MAX) {
      if (!vu) return false;
      let libre = false;
      while (abris.length && !libre) {
        const a = abris.pop();
        if (a.etat === "terre" && paniques[a.i] === a) { oublier(a.i); libre = true; }
      }
      if (!libre) return false;
    }

    // CHACUN SA PEUR, ET ELLE NE SE TIRE PAS AU SORT. Le déphasage vient de
    // l'identité du corps, comme ses heures de sortie : deux voisins ne partent
    // pas à la même seconde et ne courent pas à la même allure, et pourtant
    // rien n'est stocké. Un enfant et un vieillard courent moins vite qu'un
    // portefaix — c'est l'âge qui est dans la cellule qui le dit, pas un dé.
    const id = J.ident(cel, k);
    const h1 = ((id * 374761393) >>> 13 & 1023) / 1023;
    const h2 = ((id * 668265263) >>> 11 & 1023) / 1023;
    const an = cel.age_sexe ? (cel.age_sexe[k] & 0x7f) : 30;
    const role = (cel.roles_index && cel.role) ? cel.roles_index[cel.role[k]] : "";
    const contre = CONTRE.test(role || "");
    const vieux = an < 12 || an > 55;
    // TROISIÈME TIRAGE, ET C'EST CELUI DU CAMP. Il vient de l'identité comme
    // les deux autres, donc le même homme fera toujours le même choix — ce qui
    // est le minimum qu'on doive à quelqu'un qu'on peut aller retrouver le
    // lendemain et faire parler de sa nuit.
    const h3 = ((id * 2246822519) >>> 9 & 1023) / 1023;
    const jeune = an >= 16 && an <= 45;
    // On ne rejoint pas une rumeur : il faut avoir vu la masse de ses yeux.
    let prend = null;
    if (!contre && jeune && vu) {
      if (AVEC.test(role || "") && h3 < PART_ARMES) prend = "assaut";
      else if (CONTRE_EUX.test(role || "") && h3 < PART_BARRE) prend = "garde";
    }
    if (!cel._peur) cel._peur = new Array(cel.n).fill(null);
    const rec = {
      cel, k,
      x: P.x, y: P.y,
      chez: [cel.x0 + cel.x[k] / 100, cel.y0 + cel.y[k] / 100],
      etat: "saisi",
      // Celui qui va chercher une arme ne traîne pas non plus : il a décidé
      // avant d'avoir eu peur, et c'est précisément ce qui le distingue.
      attente: (contre || prend) ? 0.2 + h1 * 0.8
                                 : SAISI[0] + h1 * (SAISI[1] - SAISI[0]),
      v: contre ? MARCHE * 1.4
         : prend === "assaut" ? MARCHE * 1.3
         : (vieux ? 2.3 : FUITE) * (0.85 + h2 * 0.3),
      contre, prend, age_t: 0,
      // CE QUI FAIT D'UN PANIQUÉ UN TÉMOIN. Trois champs qu'on avait déjà
      // calculés et qu'on jetait : son identité, son âge, son métier. Avec
      // `chez` — qui est une ADRESSE — ça suffit à faire de lui quelqu'un que
      // la troupe peut aller trouver trois jours plus tard et faire parler.
      // C'est toute la différence entre une simulation et un gisement.
      id, an, role,
      // Le sexe est le bit 7 de l'octet d'âge, et il sert à une seule chose
      // ici : écrire « une épouse » au lieu de « un épouse ». Deviner le genre
      // d'après le nom du métier serait faux une fois sur trois, alors que la
      // cellule le sait pour de bon.
      femme: !!(cel.age_sexe && (cel.age_sexe[k] & 0x80)),
      noeud: noeudProche(P.x, P.y), arc: null, venu: null, s: 0, surRue: false,
    };
    rec.i = paniques.length;
    cel._peur[k] = rec;
    paniques.push(rec);
    // LA PEUR SE NOTE PAR QUARTIER, ET UNE SEULE FOIS PAR QUARTIER. Quatre
    // mille paniqués feraient quatre mille lignes que personne ne lira ; ce
    // qu'on veut savoir est plus simple — à quelle heure tel quartier a
    // compris, et s'il l'a vu ou entendu dire.
    //
    // C'ÉTAIT UNE MAILLE DE CENT VINGT MÈTRES, et c'était trop fin : quatre-
    // vingt-dix lignes sur cent quatre-vingt-douze, dont quatorze à la même
    // seconde et toutes rigoureusement identiques. Un document qui s'ouvre sur
    // quatorze fois la même phrase, on ne le lit pas — et la guerre, qui est le
    // sujet, se retrouvait noyée par sa propre rumeur. Douze quartiers : douze
    // lignes au plus, et chacune dit quelque chose.
    noter(vu ? "peur-gagne" : "rumeur-gagne", P.x, P.y, {
      clef: "peur:" + situer(P.x, P.y).zone,
      dit: { par: vu ? "on les a vus" : "on l'a entendu dire" },
    });
    P.vers = contre ? "ronde" : "fuite";
    P.quoi = "sur-place";      // le premier instant, on ne bouge pas
    return true;
  }

  // ---- la boucle ------------------------------------------------------------
  // PAS FIXE, et pas le temps de l'image. Une machine à états qu'on avance
  // d'un `dt` variable ne se rejoue pas deux fois pareil, et l'on passe la
  // soirée à chercher pourquoi la même bataille finit autrement. Vingt pas par
  // seconde, et l'on rattrape ce qu'il faut — sans jamais rattraper plus de
  // quatre pas d'un coup, sinon un onglet laissé en fond simule dix minutes en
  // une image et fige la page.
  function avancer(dtReel) {
    reste += Math.min(dtReel, 0.5);
    let n = 0;
    while (reste >= PAS && n++ < 4) {
      reste -= PAS;
      temps += PAS;
      semer();
      // LE COMMANDEMENT AVANT LES CORPS, et dans cet ordre-là : la tête décide,
      // les bannières montent ou tombent, les ordres descendent — et seulement
      // ensuite les hommes exécutent ce qu'ils ont reçu. L'inverse ferait agir
      // tout le monde sur l'ordre du pas précédent, ce qui ajouterait un
      // vingtième de seconde de retard partout, invisible et faux.
      decider(PAS);
      bannieres(PAS);
      transmettre(PAS);
      designerLeFront();
      porteQuiCede();
      for (const h of hommes) soldat(h, PAS);
      for (const h of hommes) if (h.etat !== "mort") pousser(h, PAS);
      // Les masses AVANT les habitants, et la rumeur après eux : ce qui court
      // à ce pas-ci est ce qui fera paniquer le voisin au pas suivant.
      escouadesQuiRompent();
      fondreLesFoyers();
      bourgeois(PAS);
      semerLaRumeur();
    }
    majCompte();
  }

  function majCompte() {
    let a = 0, d = 0;
    for (const h of hommes) {
      if (h.tete) continue;         // il commande, il ne fait pas nombre
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      if (h.camp === "assaut") a++; else d++;
    }
    compte.a = a; compte.d = d;
  }

  // ---- ce qu'une escouade laisse quand elle cesse d'en être une -------------
  // Une escouade ne « meurt » pas : elle se vide, et à un moment elle n'est
  // plus une unité. La moitié suffit — au-delà, les survivants n'exécutent
  // plus rien de ce qu'on leur avait dit. C'est le fait qui manque le plus au
  // récit d'une bataille, parce qu'il est le seul à parler d'un GROUPE.
  function escouadesQuiRompent() {
    if (!escouades.length) return;
    const vif = new Array(escouades.length).fill(0);
    const tot = new Array(escouades.length).fill(0);
    const cx = new Array(escouades.length).fill(0);
    const cy = new Array(escouades.length).fill(0);
    for (const h of hommes) {
      // La tête est du camp de l'assaut et porte une escouade nulle par
      // défaut : sans ce test, elle gonflerait à jamais l'effectif de la
      // première, qui ne romprait donc plus jamais.
      if (h.camp !== "assaut" || h.tete) continue;
      const e = h.escouade;
      tot[e]++;
      if (h.etat === "mort" || h.etat === "blesse" || h.etat === "deroute") continue;
      vif[e]++; cx[e] += h.x; cy[e] += h.y;
    }
    for (let e = 0; e < escouades.length; e++) {
      if (!tot[e] || vif[e] > tot[e] / 2) continue;
      // Le lieu du fait est celui des SURVIVANTS, pas celui des morts : c'est
      // là qu'il y a encore quelqu'un à voir.
      const x = vif[e] ? cx[e] / vif[e] : verrou.x, y = vif[e] ? cy[e] / vif[e] : verrou.y;
      noter("escouade-rompt", x, y,
            { clef: "rompt:" + e, dit: { escouade: e, restent: vif[e], sur: tot[e] } });
    }
  }

  // ---- le dessin ------------------------------------------------------------
  function repere() {
    const vue = vueDe && vueDe();
    if (!vue || !toile || !toile.width) return null;
    const k = Math.min(toile.width / vue[2], toile.height / vue[3]);
    return { k, ox: (toile.width - vue[2] * k) / 2 - vue[0] * k,
             oy: (toile.height - vue[3] * k) / 2 - vue[1] * k };
  }

  function ajuster() {
    if (!toile || !hote) return;
    const r = hote.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const l = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
    if (toile.width !== l || toile.height !== h) { toile.width = l; toile.height = h; }
  }

  const TEINTE = {
    assaut: "#8c2f22",        // le fer qui monte
    garde:  "#24506b",        // le fer qui tient
    mort:   "#5a5348",
    deroute:"#a8763a",
    blesse: "#8a4a52",
    // Le coureur porte l'ordre : il doit se voir traverser la presse, sinon
    // toute la chaîne de commandement reste une abstraction de fichier.
    coureur:"#d8c37a",
    repli:  "#6b6f7d",
    commande:"#c9a227",
  };

  function peindre() {
    if (!ctx || !toile.width) return;
    ctx.clearRect(0, 0, toile.width, toile.height);
    const rep = repere();
    if (!rep || !hommes.length) return;
    const dpr = window.devicePixelRatio || 1;
    // À 1:1, un homme fait un demi-mètre : au cadrage de la ville entière il
    // vaut un huitième de pixel. On ne triche pas sur sa POSITION — seulement
    // sur sa taille à l'écran, faute de quoi une armée de trois cents hommes
    // est rigoureusement invisible, ce qui est fidèle et inutile.
    const r = Math.max(1.5 * dpr, Math.min(4 * dpr, rep.k * EPAULE));
    const L = toile.width + 8, H = toile.height + 8;

    // Les verrous d'abord, sous les corps : ce sont les objectifs, ils doivent
    // se lire même quand sept hommes sont dessus. Il y en a un par porte, et
    // les voir tourner à des vitesses différentes est précisément ce qu'on
    // vient regarder.
    for (const v of verrous) {
      const x = rep.ox + v.x * rep.k, y = rep.oy + v.y * rep.k;
      const part = v.pv / v.max;
      ctx.strokeStyle = v.etat === "ouvert" ? "#7a8b5a" : "#b03a24";
      ctx.lineWidth = Math.max(2, 3 * dpr);
      ctx.beginPath();
      ctx.arc(x, y, Math.max(7, rep.k * 4), -Math.PI / 2,
              -Math.PI / 2 + 6.2832 * Math.max(0, part));
      ctx.stroke();
    }

    for (const h of hommes) {
      const x = rep.ox + h.x * rep.k, y = rep.oy + h.y * rep.k;
      if (x < -8 || y < -8 || x > L || y > H) continue;
      if (h.etat === "mort") {
        ctx.globalAlpha = .55; ctx.fillStyle = TEINTE.mort;
        ctx.fillRect(x - r * .7, y - r * .7, r * 1.4, r * 1.4);
        ctx.globalAlpha = 1;
        continue;
      }
      // Le blessé se lit comme un mort — couché, à plat — mais il garde sa
      // couleur de sang : sur le plan, on doit voir d'un coup d'œil combien
      // sont par terre et combien de ceux-là respirent encore.
      if (h.etat === "blesse") {
        ctx.globalAlpha = .8; ctx.fillStyle = TEINTE.blesse;
        ctx.fillRect(x - r, y - r * .55, r * 2, r * 1.1);
        ctx.globalAlpha = 1;
        continue;
      }
      ctx.fillStyle = TEINTE[h.etat] || TEINTE[h.camp];
      if (r <= 2.4) ctx.fillRect(x - r, y - r, r * 2, r * 2);
      else { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill(); }
      // Le chef porte un liseré : à trois cents hommes, c'est la seule façon
      // de voir qu'une escouade a perdu sa tête.
      if (h.chef) {
        ctx.strokeStyle = "#e8d9a8"; ctx.lineWidth = Math.max(1, dpr);
        ctx.beginPath(); ctx.arc(x, y, r + 1.5 * dpr, 0, 6.2832); ctx.stroke();
      }
    }

    peindreLesNommes(rep, dpr);
  }

  // ---- LES NOMMÉS -----------------------------------------------------------
  // Un anneau, et un nom quand on est assez près pour le lire. C'est la seule
  // entorse au principe « aucun corps n'a de traitement spécial », et elle est
  // d'AFFICHAGE et non de simulation : le nommé encaisse exactement ce que les
  // autres encaissent, il est seulement le seul qu'on retrouve à l'œil.
  //
  // L'anneau se lit à toutes les échelles ; le nom ne s'écrit qu'à partir du
  // moment où deux noms ne se marchent plus dessus. Sans ce seuil, la vue de
  // la ville entière devient un tas d'étiquettes empilées sur quatre-vingts
  // pixels, ce qui est moins lisible que rien.
  const NOM_LISIBLE = 0.34;     // pixels par mètre — en dessous, l'anneau seul
  const ANNEAU = {
    assaut: "#d98a5a", garde: "#6fb0d8", ville: "#cfc0a0",
  };

  function peindreLesNommes(rep, dpr) {
    const L = toile.width + 8, H = toile.height + 8;
    const lisible = rep.k > NOM_LISIBLE;
    ctx.lineWidth = Math.max(1.4, 1.6 * dpr);
    ctx.font = Math.round(11 * dpr) + "px ui-sans-serif, system-ui, sans-serif";
    ctx.textBaseline = "middle";

    const trace = (p, tombe) => {
      const x = rep.ox + p.x * rep.k, y = rep.oy + p.y * rep.k;
      if (x < -60 || y < -30 || x > L + 60 || y > H + 30) return;
      const R0 = Math.max(6.5 * dpr, rep.k * 5);
      ctx.globalAlpha = tombe ? .45 : 1;
      ctx.strokeStyle = ANNEAU[p.camp] || ANNEAU.ville;
      ctx.beginPath(); ctx.arc(x, y, R0, 0, 6.2832); ctx.stroke();
      // Un second anneau, plus mince, sur ceux qui décident : la tête d'un
      // corps n'est pas un habitant, et l'œil doit pouvoir trier sans lire.
      if (p.rang === "tete") {
        ctx.beginPath(); ctx.arc(x, y, R0 + 3 * dpr, 0, 6.2832); ctx.stroke();
      }
      if (!lisible) { ctx.globalAlpha = 1; return; }
      const t = p.nom, l = ctx.measureText(t).width;
      ctx.globalAlpha = tombe ? .4 : .82;
      ctx.fillStyle = "rgba(18,16,13,.72)";
      ctx.fillRect(x + R0 + 4 * dpr, y - 8 * dpr, l + 8 * dpr, 16 * dpr);
      ctx.globalAlpha = tombe ? .55 : 1;
      ctx.fillStyle = ANNEAU[p.camp] || ANNEAU.ville;
      ctx.fillText(t, x + R0 + 8 * dpr, y);
      ctx.globalAlpha = 1;
    };

    // Les vivants d'abord — un nommé qui se bat compte plus qu'un témoin.
    for (const h of hommes) {
      if (!h.nom) continue;
      trace({ x: h.x, y: h.y, nom: h.nom, camp: h.camp,
              rang: h.tete ? "tete" : null },
            h.etat === "mort" || h.etat === "blesse");
    }
    for (const f of figures) trace(f, false);
  }

  function image() {
    const t = performance.now();
    const dt = dernier ? (t - dernier) / 1000 : 0;
    dernier = t;
    if (marche) avancer(dt);
    peindre();
    montre();
    boucle = requestAnimationFrame(image);
  }

  // ---- la barre -------------------------------------------------------------
  let barre = null, lecture = null;
  function batirBarre() {
    barre = document.createElement("div");
    barre.className = "cv-bat-barre";
    barre.innerHTML =
      '<button class="cv-b-jouer" title="Lancer ou suspendre l\'assaut">▶</button>' +
      '<span class="cv-b-etat">—</span>' +
      '<button class="cv-b-rejouer" title="Remettre l\'armée devant la porte">↺</button>';
    lecture = barre.querySelector(".cv-b-etat");
    barre.querySelector(".cv-b-jouer").addEventListener("click", (e) => {
      e.stopPropagation(); basculer();
    });
    barre.querySelector(".cv-b-rejouer").addEventListener("click", (e) => {
      e.stopPropagation(); rejouer();
    });
    ["pointerdown", "wheel", "dblclick"].forEach((t) =>
      barre.addEventListener(t, (e) => e.stopPropagation()));
    hote.appendChild(barre);
  }

  function montre() {
    if (!lecture) return;
    if (!hommes.length) { lecture.textContent = "—"; return; }
    const mm = Math.floor(temps / 60), ss = Math.floor(temps % 60);
    // COMBIEN DE PORTES SONT TOMBÉES, plutôt que l'état d'une seule. C'est le
    // seul chiffre qui dise où en est un sac : une ville tient tant qu'il lui
    // reste un battant.
    const ouvertes = verrous.filter((v) => v.etat === "ouvert").length;
    const porte = verrous.length <= 1
      ? (verrou && verrou.etat === "ouvert" ? "porte enfoncée"
         : Math.round((verrou ? verrou.pv / verrou.max : 1) * 100) + " % de porte")
      : ouvertes + "/" + verrous.length + " portes enfoncées";
    lecture.textContent = mm + "′" + (ss < 10 ? "0" : "") + ss +
      " · " + compte.a + " contre " + compte.d + " · " + porte +
      (compte.blesses ? " · " + compte.blesses + " à terre" : "") +
      (compte.fuyards ? " · " + compte.fuyards + " en fuite" : "");
  }

  function basculer() {
    if (!hommes.length) rejouer();
    marche = !marche;
    dernier = performance.now();
    if (barre) {
      barre.querySelector(".cv-b-jouer").textContent = marche ? "⏸" : "▶";
      barre.classList.toggle("marche", marche);
    }
    if (window.Foule2d) Foule2d.salir();
  }

  function rejouer(nomPorte, n) {
    // Sans effectif, c'est l'ÉCHELLE qui commande, et non plus trois cents
    // hommes en dur : la seule question qu'on se pose désormais est « à quelle
    // fraction de l'armée regarde-t-on ? ».
    dresser(nomPorte || "La porte de la Gadoue", n);
    // On rend d'abord tout le monde à sa journée : les tableaux de peur vivent
    // sur les cellules, qui, elles, survivent à la bataille.
    for (const p of paniques) if (p.cel._peur) p.cel._peur[p.k] = null;
    paniques.length = 0; abris.length = 0; semis.clear(); foyers = [];
    enArmes = new Map();
    tisserReseau();
    compte.morts = 0; compte.blesses = 0; compte.fuyards = 0; compte.rallies = 0;
    // (Les annales sont remises à zéro par `dresser`, AVANT qu'il ne pose les
    // corps. Elles l'étaient ici, après lui — donc tout ce que la mise en place
    // écrivait était effacé dans la foulée. C'est resté invisible tant que
    // `dresser` n'écrivait rien ; le jour où il a annoncé les humeurs des six
    // corps, ces six lignes-là ne sont jamais arrivées jusqu'au fichier.)
    dernier = performance.now();
    if (window.Foule2d) Foule2d.salir();
  }

  // ---- l'attelage -----------------------------------------------------------
  let pret = null, rate = null;
  function poser(h, donneVue, opts) {
    if (rate) return Promise.resolve(false);
    hote = h; vueDe = donneVue;
    source = (opts && opts.source) || source;
    if (!toile) {
      toile = document.createElement("canvas");
      toile.className = "cv-bataille";
      ctx = toile.getContext("2d");
    }
    if (toile.parentNode !== hote) hote.appendChild(toile);
    if (!barre) batirBarre();
    else if (barre.parentNode !== hote) hote.appendChild(barre);
    ajuster();
    if (!pret) pret = amorcer();
    return pret;
  }

  // LES DONNÉES D'ABORD, L'ÉCRAN ENSUITE — et les deux se séparent, parce que
  // le four n'a pas d'écran. `preparer` ne touche pas au document : c'est par
  // là qu'entre `scripts/monde/sac.js`, qui fait tourner cette même bataille
  // sans navigateur pour la cuire. Le jour où les deux divergent, on a deux
  // simulations, et c'est la fin de la confiance qu'on peut leur accorder.
  //
  // Le chemin du module se prend dans une variable : au navigateur il est
  // absolu (`/modules/…`), sous Node c'est une URL de fichier. Une ligne, et
  // le module devient exécutable des deux côtés.
  async function preparer(ou) {
    if (ou) source = ou;
    J = await import(window.CHEMIN_JOURNEE || "/modules/monde/journee.js");
    const r = await fetch(source + "/plan2d");
    if (!r.ok) throw new Error("plan2d : " + r.status);
    plan = await r.json();
    if (!repereDuPlan("Le Donjon Rouge", "donjon")) throw new Error("pas de donjon ici");
    // La voirie n'est demandée QUE parce qu'on en aura besoin après la porte.
    // Un demi-mégaoctet qu'on ne paie pas si l'on n'ouvre jamais l'échelle.
    voirie = await J.voirie(source);
    await enterrer(source);
    tisserReseau();
    await chargerBati(source);
    return true;
  }

  // ---- LES RUES QUI N'EN SONT PLUS -----------------------------------------
  //
  // Le graphe et le plan ne sont pas cuits par le même passage, ni forcément
  // dans le bon ordre : `bati.json` peut être plus vieux que `rues.json`, et
  // alors des rues ont été tracées là où des maisons étaient déjà posées.
  // Mesuré sur Port-Réal : 1,4 % du réseau court sous le bâti, et trente-cinq
  // arêtes y sont enfouies aux trois quarts.
  //
  // Ce n'est pas beaucoup, et ça se voit ÉNORMÉMENT : il suffit d'une venelle
  // de quarante mètres à travers un pâté pour qu'une colonne entière la prenne
  // — c'est le plus court chemin, l'A* ne connaît que ça — et l'on regarde
  // trois cents hommes traverser six maisons en file indienne.
  //
  // ON NE COURT PAS APRÈS LES DATES DES FICHIERS. On mesure chaque arête
  // contre le masque du bâti, et l'on rend celles qui sont enterrées TRÈS
  // chères. L'A* les évitera tant qu'il existe autre chose, et les prendra
  // quand même s'il n'y a rien d'autre — ce qui est le bon comportement : une
  // impasse vaut mieux qu'un chemin qui n'existe pas.
  const ENTERRE = 0.55;       // au-delà de ça sous les toits, ce n'est plus une rue
  const PENITENCE = 25;       // ce qu'on la fait payer
  async function enterrer(src) {
    if (!voirie || voirie._enterre) return;
    let masque = null;
    try {
      const m = plan && plan.masque;
      if (!m) return;
      const r = await fetch(src + "/masque");
      if (!r.ok) return;
      const bits = new Uint8Array(await r.arrayBuffer());
      masque = { bits, pas: m.pas, nx: m.nx, ny: m.ny };
    } catch (e) { return; }
    const dedans = (x, y) => {
      const i = (x / masque.pas) | 0, j = (y / masque.pas) | 0;
      if (i < 0 || j < 0 || i >= masque.nx || j >= masque.ny) return false;
      const k = j * masque.nx + i;
      return (masque.bits[k >> 3] >> (k & 7)) & 1;
    };
    let n = 0;
    for (const [, nd] of voirie.noeuds) {
      for (const l of nd.liens) {
        const a = l.arete;
        if (a._sous === undefined) {
          let d = 0, t = 0;
          for (let i = 1; i < a.trace.length; i++) {
            const p = a.trace[i - 1], q = a.trace[i];
            const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
            const N = Math.max(1, Math.ceil(L / 2));
            for (let s = 0; s < N; s++) {
              t++;
              if (dedans(p[0] + (q[0] - p[0]) * s / N,
                         p[1] + (q[1] - p[1]) * s / N)) d++;
            }
          }
          a._sous = t ? d / t : 0;
          if (a._sous > ENTERRE) n++;
        }
        if (a._sous > ENTERRE) l.cout *= PENITENCE;
      }
    }
    voirie._enterre = n;
  }

  // ---- LE BÂTI, POUR LE PILLER ---------------------------------------------
  //
  // Une armée qui traverse une ville sans s'y arrêter n'est pas un sac, c'est
  // un défilé. Ce qui fait le sac, c'est que chaque maison est un objectif —
  // cinquante-trois mille objectifs, et une escouade qui doit choisir entre
  // avancer et s'arrêter. Personne n'écrit ce choix : il tombe de la
  // discipline du corps, et c'est de là que sort tout le reste. Un corps
  // discipliné arrive au Donjon à moitié de ses forces ; un corps qui se
  // dissout n'y arrive jamais.
  //
  // ON NE GARDE QUE CE QU'IL FAUT. Le fichier du bâti fait cinq mégaoctets et
  // porte seize colonnes ; on en retient quatre — où est la porte, ce qu'on y
  // fait, combien d'étages, et où en est le pillage. Le reste ne sert pas à
  // enfoncer un huis.
  let bati = null;
  const PILLE_S    = [25, 70];   // ce que coûte une maison, du seuil au butin
  const PORTEE_MAISON = 26;      // on ne quitte pas sa colonne pour plus loin
  const FEU        = 0.06;       // et parfois on met le feu en sortant

  // Ce qu'on trouve derrière une porte, par métier. Ce ne sont pas des points :
  // c'est ce qu'un homme peut emporter sur lui, et c'est pour ça qu'une manse
  // vaut trente taudis et qu'un puits ne vaut rien.
  const BUTIN = {
    manse: 40, change: 60, guilde: 30, septuaire: 25, "septuaire-quartier": 12,
    echoppe: 10, taverne: 8, auberge: 9, brasserie: 6, boulangerie: 4,
    forge: 7, poterie: 3, teinturerie: 5, tannerie: 3, corderie: 3,
    entrepot: 14, grenier: 10, moulin: 5, marche: 6, "marche-quartier": 6,
    "bureau-port": 20, caserne: 8, bordel: 9, etuve: 6, ecurie: 5,
    maison: 3, cabane: 1, taudis: 1,
  };

  async function chargerBati(src) {
    if (bati && bati.source === src) return;
    const r = await fetch(src + "/bati");
    if (!r.ok) { bati = null; return; }
    const d = await r.json();
    const col = {}; d._colonnes.forEach((c, i) => (col[c] = i));
    const l = d.bati, n = l.length;
    const x = new Float32Array(n), y = new Float32Array(n);
    const val = new Uint8Array(n), etat = new Uint8Array(n);
    const usage = new Array(n);
    for (let i = 0; i < n; i++) {
      const b = l[i];
      // LA PORTE, PAS LE CENTRE. On force un huis, on ne se matérialise pas
      // au milieu du salon — et c'est la porte qui donne sur la rue, donc le
      // seul point de la maison qu'un homme en colonne puisse atteindre.
      x[i] = b[col.porte_x] != null ? b[col.porte_x] : b[col.x];
      y[i] = b[col.porte_y] != null ? b[col.porte_y] : b[col.y];
      usage[i] = b[col.usage];
      const et = Math.max(1, b[col.etages] || 1);
      val[i] = Math.min(255, Math.round((BUTIN[usage[i]] ?? 2) * (1 + (et - 1) * .4)));
      etat[i] = 0;              // 0 intacte · 1 forcée · 2 pillée · 3 en feu
    }
    // Une grille plate sur les portes, du même bois que celle des corps : on
    // cherche « une maison à moins de vingt-six mètres » vingt fois par
    // seconde et par escouade, et une Map à clefs de texte se paierait ici
    // comme elle s'est payée partout ailleurs.
    const M = 40;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (let i = 0; i < n; i++) {
      if (x[i] < x0) x0 = x[i]; if (x[i] > x1) x1 = x[i];
      if (y[i] < y0) y0 = y[i]; if (y[i] > y1) y1 = y[i];
    }
    const nx = Math.max(1, Math.ceil((x1 - x0) / M) + 1);
    const ny = Math.max(1, Math.ceil((y1 - y0) / M) + 1);
    const cnt = new Int32Array(nx * ny + 1);
    const casier = (i) => Math.min(ny - 1, Math.max(0, ((y[i] - y0) / M) | 0)) * nx +
                          Math.min(nx - 1, Math.max(0, ((x[i] - x0) / M) | 0));
    for (let i = 0; i < n; i++) cnt[casier(i) + 1]++;
    for (let k = 0; k < nx * ny; k++) cnt[k + 1] += cnt[k];
    const rang = new Int32Array(n), curseur = cnt.slice();
    for (let i = 0; i < n; i++) rang[curseur[casier(i)]++] = i;
    bati = { source: src, n, x, y, val, etat, usage,
             M, x0, y0, nx, ny, debut: cnt, ordre: rang,
             forcees: 0, brulees: 0, butin: 0 };
  }

  // COMBIEN CHACUN S'ARRÊTE, par humeur de corps. Une chance par seconde de
  // marche, pour un homme qui passe devant une porte encore fermée.
  //
  // Ce sont les seuls chiffres de tout le module qui décident d'une PERSONNE
  // plutôt que d'une physique, et ils sont assumés comme tels : ce sont des
  // caractères, pas des mesures. Ronnel ne s'arrête jamais parce que c'est
  // Ronnel ; Petit Tam s'arrête devant tout parce que ce sont des enfants qui
  // n'ont jamais rien eu.
  const APPETIT = {
    "-": 0.030,            // les corps sans humeur — la troupe ordinaire
    ferme: 0,              // Ronnel : il arrive, et c'est tout ce qu'il fait
    sourd: 0.012,          // Vaugrain : il ne pille pas, il brûle
    versatile: 0.075,      // Petit Tam : le corps se dissout en chemin
  };
  // Vaugrain brûle au lieu d'emporter — plus vite, et il ne reste rien.
  const BRULE = { sourd: 0.75, "-": FEU, ferme: 0, versatile: 0.10 };

  /** Forcer une maison : y aller, y rester, en ressortir. */
  function piller(h, dt) {
    const b = h.maison;
    if (b == null || !bati) { h.etat = "colonne"; return; }
    const d = Math.hypot(bati.x[b] - h.x, bati.y[b] - h.y);
    // On y va — en ligne droite, et c'est honnête : la porte donne sur la rue
    // où l'on marchait déjà, il y a vingt-six mètres au plus.
    if (d > 1.5) { h.surVoie = false; versLe(h, bati.x[b], bati.y[b], MARCHE, dt); return; }
    h.reste_pille -= dt;
    if (h.reste_pille > 0) return;
    // ON RESSORT. Le butin est celui de la maison, pas du temps passé — un
    // taudis fouillé une minute reste un taudis.
    bati.butin += bati.val[b];
    const brule = R() < (BRULE[h.humeur || "-"] ?? FEU);
    bati.etat[b] = brule ? 3 : 2;
    if (brule) {
      bati.brulees++;
      // Le feu se voit de loin, et c'est le seul acte de cette bataille qui
      // change la ville pour de bon. On ne le note que de loin en loin, sinon
      // les annales ne parlent plus que de fumée.
      noter("maison-brulee", h.x, h.y,
            { clef: "feu:" + (h.corps || "?"), dit: { corps: h.corps } });
    }
    h.maison = null;
    h.etat = "colonne";
    // Il a perdu sa place dans la colonne : il la reprend où il en était, ce
    // qui le met derrière ceux qui n'ont pas ralenti. Personne ne l'attend.
    h.surRail = false;
  }

  /** La maison intacte la plus proche, dans la portée. Rend -1 s'il n'y en a pas. */
  function maisonLibre(px, py, portee) {
    if (!bati) return -1;
    const M = bati.M;
    const i0 = Math.max(0, Math.min(bati.nx - 1, ((px - bati.x0) / M) | 0));
    const j0 = Math.max(0, Math.min(bati.ny - 1, ((py - bati.y0) / M) | 0));
    const r = Math.ceil(portee / M);
    let meil = -1, dmin = portee * portee;
    for (let j = Math.max(0, j0 - r); j <= Math.min(bati.ny - 1, j0 + r); j++) {
      for (let i = Math.max(0, i0 - r); i <= Math.min(bati.nx - 1, i0 + r); i++) {
        const c = j * bati.nx + i;
        for (let k = bati.debut[c]; k < bati.debut[c + 1]; k++) {
          const b = bati.ordre[k];
          if (bati.etat[b]) continue;               // déjà forcée
          const d = (bati.x[b] - px) ** 2 + (bati.y[b] - py) ** 2;
          if (d < dmin) { dmin = d; meil = b; }
        }
      }
    }
    return meil;
  }

  async function amorcer() {
    try {
      await preparer();
      // ON NE DRESSE RIEN TANT QUE PERSONNE N'A RIEN DEMANDÉ. L'armée était
      // rangée dès l'ouverture de l'échelle : trois cents points rouges devant
      // la porte de la Gadoue à tout moment, sur un plan qu'on avait ouvert
      // pour chercher une rue. Une bataille se convoque — c'est le bouton qui
      // la fait exister, pas le fait de regarder la ville.
      if (!boucle) boucle = requestAnimationFrame(image);
      if (window.ResizeObserver) new ResizeObserver(ajuster).observe(hote);
      return true;
    } catch (e) {
      console.warn("bataille2d : pas de bataille ici —", e);
      rate = e;
      if (barre) { barre.remove(); barre = null; }
      if (toile) { toile.remove(); toile = null; }
      return false;
    }
  }

  function recadrer() { ajuster(); peindre(); }
  function arreter() {
    if (boucle) cancelAnimationFrame(boucle);
    boucle = 0; marche = false;
  }

  /** De quoi lire la bataille depuis la console, sans la regarder. */
  function etat() {
    if (!hommes.length) return { dressee: false, temps: 0, marche: false };
    const par = {};
    for (const h of hommes) par[h.etat] = (par[h.etat] || 0) + 1;
    return {
      temps: +temps.toFixed(1), marche,
      porte: entree && entree.nom, objectif: objectif && objectif.nom,
      verrou: verrou && { etat: verrou.etat, pv: Math.round(verrou.pv) },
      // Les quatre portes, chacune avec son compte : c'est le relevé qui dit
      // laquelle a cédé la première, et c'est de là que part tout le reste.
      portes: verrous.map((v) => ({ nom: v.nom, etat: v.etat,
                                    pv: Math.round(v.pv) })),
      assaut: compte.a, garde: compte.d, morts: compte.morts,
      blesses: compte.blesses, fuyards: compte.fuyards, etats: par,
      faits: annales.length,
      // LE SAC, EN QUATRE CHIFFRES. C'est par eux qu'on le retiendra : combien
      // de portes forcées, combien de toits en feu, et ce que l'armée emporte.
      sac: bati ? { maisons: bati.n, forcees: bati.forcees,
                    brulees: bati.brulees, butin: Math.round(bati.butin) } : null,
      // La ville : combien ont peur, et dans quel état. C'est le seul relevé
      // qui dise si la couche de peur fait quelque chose — on ne la voit
      // autrement qu'en regardant une rue se vider.
      ville: (() => {
        const v = { paniques: paniques.length, foyers: foyers.length };
        for (const p of paniques) v[p.etat] = (v[p.etat] || 0) + 1;
        return v;
      })(),
      moraleMoyenne: +(hommes.filter((h) => h.camp === "assaut" && h.etat !== "mort")
        .reduce((s, h, _, l) => s + h.morale / l.length, 0)).toFixed(2),
    };
  }

  // AVANCER SANS REGARDER. `requestAnimationFrame` ne bat pas dans un onglet
  // caché — ce qui est la bonne politique pour une lunette, et une impasse
  // pour l'éprouver : on ne va pas vérifier une machine à états à l'œil, en
  // temps réel, quatre minutes durant. `pas(90)` joue quatre-vingt-dix
  // secondes de bataille d'un trait et rend l'état. C'est aussi ce qui permet
  // de rejouer deux fois la même et de comparer.
  function pas(secondes) {
    if (!hommes.length) rejouer();
    const n = Math.round((secondes || 1) / PAS);
    // `avancer` consomme exactement un pas quand on lui en donne un : le
    // reliquat repart à zéro à chaque tour, et l'on ne dépend pas de l'horloge
    // réelle.
    for (let i = 0; i < n; i++) avancer(PAS);
    return etat();
  }

  // Les habitants qu'on a pris en charge, à plat. C'est le seul moyen de
  // VÉRIFIER que la peur passe par les rues au lieu de traverser les murs :
  // sans ce relevé, on ne peut que regarder des points et se persuader.
  const peur = () => paniques.map((p) => ({ x: p.x, y: p.y, etat: p.etat,
                                            surRue: p.surRue, contre: p.contre }));

  // Les corps eux-mêmes, tels quels — c'est ce que le four échantillonne à
  // chaque pas. On rend le tableau VIVANT et non une copie : le four le
  // parcourt cent mille fois, et recopier trois cents objets à chaque pas
  // coûterait plus cher que la simulation.
  const troupe = () => hommes;

  // LES RAILS QUE SUIVENT LES ESCOUADES. Un quart du chemin passe par des
  // ruelles, que le plan n'imprime pas au-delà de deux mètres par pixel : sans
  // ce relevé, on voit une colonne marcher sur du vide et l'on croit à un
  // décalage entre la carte et le calcul. Les escouades partagent leur A*, il
  // n'y a donc qu'une poignée de tracés distincts.
  const chemins = () => {
    const vus = new Set(), l = [];
    for (const e of escouades) {
      if (!e.trace || vus.has(e.trace)) continue;
      vus.add(e.trace);
      l.push(e.trace.pts.map((p) => [Math.round(p[0] * 10) / 10,
                                     Math.round(p[1] * 10) / 10]));
    }
    return l;
  };

  // CE QUE LE MJ LIRA. On rend le tableau tel quel, dans l'ordre où les faits
  // sont arrivés — c'est un document, pas une vue : on ne le trie pas, on ne
  // le filtre pas, et surtout on ne le résume pas ici. Résumer est le travail
  // de celui qui raconte.
  const faits = () => annales;

  // ---- L'ALENTOUR — CE QUE LA RUE TENAIT À CETTE MINUTE-LÀ ------------------
  // À NE PAS CONFONDRE AVEC `temoins`, qui est au-dessus et qui répond à une
  // autre question. Les deux sont utiles et aucun ne remplace l'autre :
  //
  //   `temoins`  — DES NOMS. Ceux que la couche de peur a pris en charge à
  //                moins de cinquante mètres : des gens qui étaient dehors,
  //                qui ont vu, et qu'on peut aller trouver. Résolu au moment du
  //                fait, pour rien, en balayant la liste des paniqués.
  //   `alentour` — UN ÉTAT DE RUE. Tout ce que le quartier contenait à cette
  //                minute, panique ou pas : combien dans la rue, de quels
  //                métiers, combien derrière une porte et LAQUELLE. C'est ce
  //                qui manque au premier — il ne voit que les affolés, donc il
  //                ne voit rien du tout d'un fait qui tombe hors de la peur, et
  //                il ne dit jamais par quelle porte aller frapper.
  //
  // ON NE LE RÉSOUT PAS AU MOMENT DU FAIT, et c'est le point de conception : un
  // `noter()` qui appellerait la foule coûterait un balayage de cellules par
  // blessé — des milliers, à neuf mille cinq cents hommes, en plein pas de
  // simulation. Les faits portent déjà leurs mètres et leur seconde ; la
  // question se repose donc APRÈS, une fois, sur le fichier fini. Même partage
  // que partout ici : on ne stocke pas des positions, on garde de quoi les
  // recalculer.
  //
  // LA MINUTE DU FAIT, PAS L'HEURE COURANTE. `minute` est l'heure à laquelle la
  // bataille commence ; on y ajoute la seconde du fait. Sans elle on
  // demanderait qui est là MAINTENANT pour un événement d'il y a trois heures,
  // et l'on attribuerait la porte enfoncée à des gens qui dormaient encore.
  const ALENTOUR_R = 50;         // mètres — ce qu'on voit dans une rue

  function temoigner(o) {
    const opt = o || {};
    const F = window.Foule2d;
    if (!F || !F.presents) return { faits: 0, sans: annales.length };
    const R = opt.rayon || ALENTOUR_R;
    const quoi = opt.quoi ? new Set([].concat(opt.quoi)) : null;
    const min0 = typeof opt.minute === "number" ? opt.minute : null;
    let vus = 0, sans = 0;
    for (const f of annales) {
      if (f.alentour !== undefined) continue;       // déjà fait
      if (quoi && !quoi.has(f.quoi)) { sans++; continue; }
      const g = F.presents(f.x, f.y, R,
                           min0 === null ? undefined : min0 + f.t / 60);
      // Pas de cellules chargées autour de ce point : on ne SAIT pas, et l'on
      // ne prétend pas que personne n'a vu. Un « zéro » et un « on ignore » ne
      // se jouent pas pareil, et confondre les deux ferait mentir le fichier.
      if (!g) { sans++; continue; }
      f.alentour = {
        rayon: R,
        // Ceux qui étaient DEHORS : la rue et la place. Les seuls qui aient pu
        // voir quelque chose de leurs yeux.
        rue: g.croises,
        dont: g.metiers.slice(0, 3).map(([m, n]) => (n > 1 ? n + " " + m : m))
                       .join(", ") || null,
        // Derrière une porte, à cinquante mètres : ils n'ont rien vu, mais ils
        // ont ENTENDU — et l'on sait par quelle porte aller leur demander.
        derriere: g.toit,
        portes: g.portes.slice(0, 2).map(([s, n]) => n + " " + s).join(", ") || null,
      };
      vus++;
    }
    return { faits: vus, sans };
  }

  // TOUT CE QUI PORTE UN NOM, à plat. C'est le seul relevé qui permette de
  // vérifier une mise en place sans la regarder : six têtes, un capitaine du
  // poste, un roi et douze témoins, avec leurs mètres. Une distribution qui se
  // lit dans la console est une distribution qu'on peut corriger.
  const nommes = () => [
    ...hommes.filter((h) => h.nom).map((h) => ({
      nom: h.nom, camp: h.camp, corps: h.corps,
      rang: h.tete ? "tete" : h.capitaine ? "capitaine" : "homme",
      etat: h.etat, x: +h.x.toFixed(1), y: +h.y.toFixed(1),
      ou: situer(h.x, h.y).ou })),
    ...figures.map((f) => ({
      nom: f.nom, camp: f.camp, rang: "figure", dit: f.dit,
      x: +f.x.toFixed(1), y: +f.y.toFixed(1), ou: situer(f.x, f.y).ou })),
  ];

  /** L'ordre de bataille tel qu'il est posé — combien, où, sous quel nom. */
  const ordreDeBataille = () => ({
    echelle: ECHELLE,
    assaut: CORPS.map((c) => ({
      corps: c.id, chef: c.nom, forme: c.forme, humeur: c.humeur,
      hommes: hommes.filter((h) => h.corps === c.id && !h.tete).length,
      sur: c.hommes,
      ailes: ailes.filter((a) => a.corps === c.id).length,
      escouades: escouades.filter((e) => e.corps === c.id).length,
      dit: c.dit,
    })),
    garde: hommes.filter((h) => h.camp === "garde").length,
    figures: figures.length,
  });

  return { poser, preparer, recadrer, arreter, basculer, rejouer, derange,
           etat, pas, peur, troupe, chemins, faits, nommes, ordreDeBataille,
           temoigner,
           echelle: (e) => { if (e) { ECHELLE = e; rejouer(); } return ECHELLE; },
           portes: () => portes().map((p) => p.nom),
           rafraichir: () => { peindre(); montre(); } };
})();
