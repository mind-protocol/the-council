// faits.js — LA table des types de faits de la bataille.
//
// TROISIÈME FEUILLE DÉTACHÉE DE `bataille2d.js`, après `hasard.js` et
// `mesures.js`. Celle-ci ne sort aucun calcul du four : elle sort son
// VOCABULAIRE, c'est-à-dire la seule chose qu'il partage avec le reste du
// dépôt.
//
// ─────────────────────────────────────────────────────────────────────────────
// LE DÉFAUT QU'ELLE FERME, ET IL A ÉTÉ MESURÉ
//
// `bataille2d.js` émet des faits par `noter(quoi, x, y, o)`. Deux consommateurs
// les relisent, et chacun tenait SA liste des types :
//
//   `serveur/croiser.js`      décidait si l'on VOIT, si l'on ENTEND, ou si l'on
//                             trouve la TRACE — par une table `PORTEES`.
//   `scripts/monde/annales.js` rangeait par niveau et par aspect, pour la
//                             lecture — par des tables `NIVEAUX` et `ASPECTS`.
//
// Trois vocabulaires, trois fichiers, aucun lien : ils ont dérivé en silence.
// Au dépouillement, **douze types émis par le four étaient absents de
// `PORTEES`** — porte-abimee, porte-ouverte, donjon-ouvert, donjon-tranche,
// declencheur-tombe, initiative, habitant, ordre-deforme, ordre-sans-personne,
// roi-averti, roi-tombe, messager-tombe. Ils tombaient tous sur le défaut
// timide `{vu: 45, entendu: 0, trace: 0}`, ce qui donnait ceci :
//
//   • une porte à moitié défoncée ne s'entendait PAS, quand `porte-cede`
//     s'entend à cinq cents mètres ;
//   • le roi qui verse sous sa propre déroute — le plus gros fait de la nuit —
//     ne portait pas plus loin qu'un homme qui s'assoit ;
//   • un habitant nommé qui barricade sa porte ne laissait AUCUNE trace, alors
//     que c'est exactement la trace qu'on vient chercher le lendemain matin ;
//   • et `messager-tombe` n'était connu de personne, ni des portées ni des
//     aspects : il s'écrivait dans le sac et rien au monde ne pouvait le lire.
//
// Sur le sac cuit de Port-Réal, cela faisait **15 faits sur 206**.
//
// LA RÈGLE, DÉSORMAIS : un type de fait s'écrit ICI, une fois, et les deux
// découpes en sortent. Un comportement neuf du four ajoute SA LIGNE dans cette
// table — pas une ligne dans `croiser.js` plus une dans `annales.js`, dont on
// oubliera toujours la seconde.
// ─────────────────────────────────────────────────────────────────────────────
//
// DEUX DÉCOUPES DU MÊME VOCABULAIRE, ET ELLES NE SE CONFONDENT PAS.
//
//   `portee`  — de la PHYSIQUE. Jusqu'où un homme dans la rue perçoit la
//               chose, à l'œil et à l'oreille, et combien de temps elle reste
//               lisible au sol. Ce sont des mesures, pas des réglages :
//               l'en-tête de `serveur/croiser.js` l'explique en long, et les
//               chiffres ci-dessous s'y plient.
//   `aspects` — de la LECTURE. Sous quelles questions ce fait se range quand
//               on relit la nuit — la chaîne de commandement, la ville, le
//               fer, ce qui se sait, les ouvrages, l'issue. Un fait en sert
//               plusieurs, et c'est voulu.
//
// Le NIVEAU (ce qu'un rapport retient, par opposition au moindre râle) reste
// dans `annales.js` : il classe par profondeur de lecture et n'a pas de sens
// pour la perception. Voir la note en tête de sa constante `NIVEAUX`.
//
// CHARGEABLE DES DEUX CÔTÉS. Script nu pour le navigateur (`window.BatailleFaits`),
// `require` pour Node — `croiser.js` et `annales.js` sont du Node. Même patron
// que `mesures.js` et `hasard.js`.
"use strict";
(() => {

  // ===========================================================================
  // CE QUE PORTE TOUT FAIT, SANS EXCEPTION
  // ===========================================================================
  // `noter()` le pose lui-même sur chaque entrée : c'est le squelette, et les
  // `champs` déclarés plus bas s'y ajoutent. On le documente ici pour qu'un
  // lecteur des annales sache ce qu'il peut filtrer partout.
  //
  //   t          la seconde de bataille (le sac commence à 0)
  //   quoi       le type — une clef de cette table
  //   x, y       les mètres du plan, vrais et 1:1
  //   quartier   le quartier, ou null si un repère est plus proche
  //   repere     le repère du plan le plus proche, ou null
  //   ou         « devant La porte de la Gadoue » — la formule toute faite
  //   zone       la zone, toujours renseignée, et c'est elle qui sert au bruit
  //   pres       le nom de l'habitant devant chez qui ça s'est passé, ou null
  //   pres_pas   à combien de pas de lui
  //   temoins    combien d'hommes pouvaient le voir
  const COMMUNS = ["t", "quoi", "x", "y", "quartier", "repere", "ou", "zone",
                   "pres", "pres_pas", "temoins"];

  // ===========================================================================
  // LES ASPECTS — en travers, et ils se recouvrent exprès.
  // ===========================================================================
  // L'ORDRE DE CETTE TABLE EST UNE DÉCISION. Un fait sert plusieurs aspects
  // mais ne se range que sous UN quand on groupe (`annales.js --par aspect`),
  // sinon on relit deux fois la même ligne en croyant à deux faits : c'est le
  // PREMIER de cette liste qui le réclame qui l'emporte. Ne pas réordonner
  // sans savoir ce qu'on déplace.
  const ASPECTS = {
    commandement: { nom: "La chaîne de commandement",
                    dit: "qui ordonne, qui transmet, qui n'entend plus rien" },
    ville:        { nom: "La ville",
                    dit: "ce que la population fait pendant qu'on se bat dessus" },
    fer:          { nom: "Le fer",
                    dit: "le contact, les corps à terre, les escouades qui cessent d'en être" },
    nouvelles:    { nom: "Ce qui se sait",
                    dit: "l'information qui circule — ou qui tombe en chemin" },
    ouvrages:     { nom: "Les ouvrages",
                    dit: "les portes, et par où l'on entre" },
    issue:        { nom: "L'issue",
                    dit: "comment la nuit s'est décidée" },
    // Le filet de sécurité : un `quoi` qu'aucun type de cette table ne nomme
    // tombe ici, et `annales.js` le dit sur la sortie d'erreur. Sans ça,
    // ajouter un fait dans le four le ferait disparaître en silence de toutes
    // les vues — et l'on chercherait le défaut dans le four, qui n'y serait
    // pour rien.
    divers:       { nom: "Divers", dit: "ce qu'aucun aspect ne réclame encore" },
  };

  // ===========================================================================
  // LA TABLE
  // ===========================================================================
  // `portee.vu` et `portee.entendu` sont des MÈTRES. `portee.trace` est la
  // durée en SECONDES pendant laquelle la chose reste lisible au sol après
  // coup — `0` pour ce qui ne laisse rien, `Infinity` pour ce qu'on retrouvera
  // au matin. `portee.trace_vu` est la distance à laquelle on repère cette
  // trace-là ; sans lui, `croiser.js` prend `min(vu, 25)`, ce qui convient à un
  // corps par terre et pas à une maison brûlée.
  //
  // `arrete: true` coupe la marche du joueur quand le fait est VU. Le manuel
  // le dit : « ce qui se lève en chemin devient un fil, et alors on arrête de
  // marcher. » On ne le laisse pas au jugé.
  //
  // Les chiffres ne sont pas des réglages de difficulté : ce sont des mesures,
  // de nuit, dans une ville de pierre. Chacun se justifie en une ligne, et
  // celui qui n'en a pas n'a rien à faire ici.
  const FAITS = {

    // --- LES OUVRAGES --------------------------------------------------------
    // L'état d'une porte AVANT qu'on la frappe. Ce n'est pas un événement :
    // c'est une constatation du four à l'ordre de bataille. Mais contrairement
    // à `corps-ferme`, ÇA SE VOIT — un battant fendu se lit de la rue, il se
    // lit toute la nuit, et c'est la seule chose qu'un homme puisse aller
    // vérifier avant l'assaut. Aucun bruit : personne ne l'a frappée.
    "porte-abimee": {
      dit: "une porte déjà entamée avant qu'on l'ait touchée",
      champs: ["porte", "part"],
      portee: { vu: 60, entendu: 0, trace: Infinity, trace_vu: 60 },
      aspects: ["ouvrages"],
    },
    "porte-cede": {
      dit: "le verrou est sous la moitié de ses points — elle ne tiendra pas",
      champs: ["porte"],
      portee: { vu: 80, entendu: 500, trace: 0 },
      aspects: ["ouvrages"],
      arrete: true,
    },
    "porte-enfoncee": {
      dit: "elle est tombée, et la ville est ouverte de ce côté",
      champs: ["porte"],
      portee: { vu: 80, entendu: 700, trace: Infinity, trace_vu: 60 },
      aspects: ["ouvrages", "issue"],
      arrete: true,
    },
    // LE CONTRAIRE EXACT DE `porte-enfoncee` : zéro hache, zéro bélier. Le
    // sergent tire les barres de l'intérieur et le battant s'ouvre. Ça se VOIT
    // de loin — une porte de ville qui bâille et des hommes qui s'y engouffrent
    // —, ça ne s'entend presque pas, et ça reste ouvert pour la nuit.
    "porte-ouverte": {
      dit: "on l'a ouverte de dedans",
      champs: ["porte", "par", "hommes", "apres"],
      portee: { vu: 120, entendu: 120, trace: Infinity, trace_vu: 80 },
      aspects: ["ouvrages", "issue"],
      arrete: true,
    },
    // Un ouvrage majeur qui s'ouvre sur une esplanade : ça se voit du bout de
    // la place, et le peu de bruit qu'il fait est couvert par le reste. Il
    // reste ouvert : c'est la nuit qui bascule, on ne le referme pas.
    "donjon-ouvert": {
      dit: "le Donjon s'ouvre, et la garde y rentre",
      champs: ["par", "contre", "hommes", "apres"],
      portee: { vu: 200, entendu: 150, trace: Infinity, trace_vu: 150 },
      aspects: ["ouvrages", "issue"],
      arrete: true,
    },
    // HUIS CLOS, ET C'EST TOUT LE FAIT. Le conseil a tranché de TENIR : deux
    // hommes qui s'engueulent derrière des murs. Rien à voir, rien à entendre,
    // rien par terre — la seule chose perceptible est une porte qui NE s'ouvre
    // pas, c'est-à-dire une absence. Portée nulle, comme `corps-*`, et c'est la
    // mesure juste et non une omission.
    "donjon-tranche": {
      dit: "le conseil a tranché de tenir — la porte ne s'ouvrira pas",
      champs: ["par", "contre", "apres"],
      portee: { vu: 0, entendu: 0, trace: 0 },
      aspects: ["issue"],
    },

    // --- LE FER --------------------------------------------------------------
    "contact": {
      dit: "les deux lignes se touchent, pour la première fois",
      champs: [],
      portee: { vu: 60, entendu: 250, trace: 0 },
      aspects: ["fer", "issue"],
      arrete: true,
    },
    // Un corps qu'on relève, un pavé noirci : ça se voit du trottoir d'en face.
    "premier-sang": {
      dit: "le premier homme touché de la nuit",
      champs: ["camp"],
      portee: { vu: 50, entendu: 0, trace: 3600, trace_vu: 20 },
      aspects: ["fer", "issue"],
    },
    "blesse": {
      dit: "un homme à terre qui respire encore",
      champs: ["camp", "escouade", "chef"],
      portee: { vu: 40, entendu: 35, trace: Infinity },
      aspects: ["fer"],
      arrete: true,
    },
    "blesse-succombe": {
      dit: "la plaie a tranché",
      champs: ["camp"],
      portee: { vu: 30, entendu: 0, trace: Infinity },
      aspects: ["fer"],
    },
    "blesse-tient": {
      dit: "il ne saigne plus, et il est encore là au matin",
      champs: ["camp"],
      portee: { vu: 30, entendu: 25, trace: Infinity },
      aspects: ["fer"],
    },
    "chef-tombe": {
      dit: "un chef d'escouade ou un capitaine est à terre",
      champs: ["camp", "nom", "corps", "aile", "escouade", "mort"],
      portee: { vu: 50, entendu: 60, trace: 1800 },
      aspects: ["commandement"],
    },
    "tete-tombe": {
      dit: "la tête d'un corps est à terre — son aile n'a plus d'ordres",
      champs: ["camp", "nom", "corps", "aile", "escouade", "mort"],
      portee: { vu: 60, entendu: 90, trace: 3600 },
      aspects: ["commandement"],
      arrete: true,
    },
    "escouade-rompt": {
      dit: "une escouade cesse d'en être une",
      champs: ["escouade", "restent", "sur"],
      portee: { vu: 120, entendu: 150, trace: 0 },
      aspects: ["fer"],
      arrete: true,
    },
    "ralliement": {
      dit: "un fuyard revient dans le rang",
      champs: ["escouade"],
      portee: { vu: 90, entendu: 110, trace: 0 },
      aspects: ["fer"],
    },
    "assaut-au-donjon": {
      dit: "l'assaut est arrivé au pied du Donjon",
      champs: [],
      portee: { vu: 150, entendu: 400, trace: 0 },
      aspects: ["fer", "issue"],
      arrete: true,
    },

    // --- LA CHAÎNE DE COMMANDEMENT -------------------------------------------
    // Elle se voit de près et ne s'entend guère : un coureur qui part est un
    // homme qui court, rien de plus, et il faut être dans la même rue pour
    // comprendre que c'en est un.
    "ordre": {
      dit: "une tête ordonne à son aile",
      champs: ["corps", "chef", "aile", "rang", "ordre", "phrase"],
      portee: { vu: 40, entendu: 60, trace: 0 },
      aspects: ["commandement"],
    },
    "coureur-part": {
      dit: "un homme part porter l'ordre à une escouade",
      champs: ["aile", "rang", "corps", "chef", "vers", "ordre", "phrase"],
      portee: { vu: 40, entendu: 0, trace: 0 },
      aspects: ["commandement", "nouvelles"],
    },
    "coureur-arrive": {
      dit: "l'ordre est entré dans l'escouade",
      champs: ["vers", "ordre", "phrase"],
      portee: { vu: 40, entendu: 0, trace: 0 },
      aspects: ["commandement", "nouvelles"],
    },
    "coureur-tombe": {
      dit: "il n'arrivera pas, et personne à l'autre bout ne le saura",
      champs: ["vers", "ordre", "phrase"],
      portee: { vu: 45, entendu: 0, trace: 900 },
      aspects: ["commandement", "nouvelles"],
    },
    // Il arrive, et il n'y a plus d'escouade à qui parler. Un homme qui
    // s'arrête au milieu de la rue, qui cherche, et qui repart : ça se voit à
    // la distance d'un coureur — c'en est un — et ça ne fait aucun bruit. Il
    // repart, donc rien par terre.
    "ordre-sans-personne": {
      dit: "l'ordre arrive là où il n'y a plus personne pour le prendre",
      champs: ["vers", "ordre", "phrase"],
      portee: { vu: 40, entendu: 0, trace: 0 },
      aspects: ["commandement", "nouvelles"],
    },
    // DANS SA TÊTE, ET NULLE PART AILLEURS. Une phrase qui perd une subordonnée
    // en jouant des coudes ne se voit pas, ne s'entend pas, ne laisse rien : le
    // coureur lui-même ignore qu'il l'a perdue. Portée nulle, pour la même
    // raison que `corps-sourd` — c'est une note du fichier sur lui-même. Ce
    // qu'un marcheur peut percevoir de cette scène, c'est `coureur-part`, qui
    // porte déjà.
    "ordre-deforme": {
      dit: "il a perdu une clause en chemin, et il ne le sait pas",
      champs: ["vers", "perdu", "phrase"],
      portee: { vu: 0, entendu: 0, trace: 0 },
      aspects: ["commandement", "nouvelles"],
    },
    // ELLE PART SANS QUE PERSONNE SOIT VENU. Tout l'intérêt du déclencheur est
    // qu'il n'y a ni coureur, ni bannière, ni voix : une escouade qui regardait
    // la porte se met en marche d'elle-même. Ce qui se perçoit, c'est donc une
    // TROUPE qui s'ébranle — la distance d'un mouvement de formation, pas celle
    // d'un homme — et rigoureusement aucun bruit propre.
    "declencheur-tombe": {
      dit: "ce qu'elle attendait est arrivé : elle part sans qu'on l'appelle",
      champs: ["escouade", "aile", "phrase"],
      portee: { vu: 100, entendu: 0, trace: 0 },
      aspects: ["commandement"],
    },
    // UN CHEF D'ESCOUADE QUI S'INVENTE UN ORDRE FAUTE DE NOUVELLES. Même
    // physique qu'`ordre` — un homme qui donne de la voix, qu'on entend un peu
    // plus loin qu'on ne l'identifie — mais une voix de chef d'escouade et non
    // de tête de corps : plus courte des deux côtés.
    "initiative": {
      dit: "sans nouvelles, il tranche tout seul",
      champs: ["escouade", "aile", "corps", "chef", "phrase", "motif"],
      portee: { vu: 35, entendu: 45, trace: 0 },
      aspects: ["commandement"],
    },
    "escouade-sourde": {
      dit: "plus rien ne lui parvient — elle jouera son dernier ordre jusqu'au bout",
      champs: ["escouade", "aile", "ordre", "phrase"],
      portee: { vu: 0, entendu: 0, trace: 0 },
      aspects: ["commandement", "nouvelles"],
    },
    "escouade-reprise": {
      dit: "un coureur est passé : elle est de nouveau commandable",
      champs: ["escouade", "ordre"],
      portee: { vu: 60, entendu: 0, trace: 0 },
      aspects: ["commandement", "nouvelles"],
    },
    "nouveau-chef": {
      dit: "elle n'avait plus de chef ; le coureur en fait un",
      champs: ["escouade"],
      portee: { vu: 35, entendu: 0, trace: 0 },
      aspects: ["commandement"],
    },
    "banniere-tombe": {
      dit: "l'aile perd son signal",
      champs: ["aile", "corps", "rang", "chef"],
      portee: { vu: 130, entendu: 0, trace: 600 },
      aspects: ["commandement"],
    },
    "banniere-relevee": {
      dit: "un homme la ramasse, et l'aile réentend",
      champs: ["aile", "corps", "rang", "chef"],
      portee: { vu: 130, entendu: 0, trace: 0 },
      aspects: ["commandement"],
    },
    // Ce que chaque corps EST ne se perçoit pas : c'est une note du fichier sur
    // lui-même, pas un événement de la rue. Portée nulle, et c'est voulu.
    "corps-ferme": {
      dit: "ce corps tient — on le dit une fois, au départ",
      champs: ["corps", "chef", "hommes", "humeur"],
      portee: { vu: 0, entendu: 0, trace: 0 },
      aspects: ["commandement"],
    },
    "corps-sourd": {
      dit: "ce corps n'a pas de cors : ses escouades n'entendront jamais un ordre",
      champs: ["corps", "chef", "hommes", "humeur"],
      portee: { vu: 0, entendu: 0, trace: 0 },
      aspects: ["commandement"],
    },
    "corps-versatile": {
      dit: "ce corps décroche vite et se rallie vite",
      champs: ["corps", "chef", "hommes", "humeur"],
      portee: { vu: 0, entendu: 0, trace: 0 },
      aspects: ["commandement"],
    },

    // --- LE ROI, ET CE QU'ON EN SAIT AU DONJON --------------------------------
    // Un homme du guet franchit la porte du Donjon en courant et parle. Ce
    // qu'on perçoit d'ici, c'est exactement `coureur-arrive` : un homme, une
    // porte, aucun bruit. Ce qui suit — deux lords qui délibèrent — est
    // derrière les murs et ne se perçoit pas du tout.
    "roi-averti": {
      dit: "la nouvelle est entrée au Donjon, et l'heure commence à courir",
      champs: ["porte", "depuis", "pas"],
      portee: { vu: 45, entendu: 0, trace: 0 },
      aspects: ["nouvelles", "issue"],
    },
    // LE PENDANT EXACT DE `coureur-tombe`, ET IL N'ÉTAIT LU PAR PERSONNE : ni
    // portée, ni aspect, ni niveau. Même corps, même rue, même quart d'heure
    // avant qu'on le ramasse — donc les mêmes chiffres, et il faut que ce soit
    // les mêmes : deux hommes tombés côte à côte ne se perçoivent pas
    // différemment parce que l'un portait une nouvelle plus grosse.
    "messager-tombe": {
      dit: "le porteur de la nouvelle tombe en chemin — le Donjon ne saura rien",
      champs: ["porte", "depuis", "reste"],
      portee: { vu: 45, entendu: 0, trace: 900 },
      aspects: ["commandement", "nouvelles"],
    },
    // LA CHARRETTE VERSE. Aucun coup d'épée : neuf mille hommes qui refluent
    // par où ils sont venus, et il est posé au milieu. C'est haut, c'est au
    // milieu d'une place, et la clameur qui monte autour porte plus loin que
    // la chose elle-même — le seul fait de la nuit dont l'ouïe dise plus que
    // l'œil. Ce qui reste par terre est une charrette renversée : ça ne
    // s'enlève pas, et ça se voit du bout de la rue.
    "roi-tombe": {
      dit: "sa propre déroute lui passe dessus",
      champs: ["nom", "presse"],
      portee: { vu: 150, entendu: 200, trace: Infinity, trace_vu: 100 },
      aspects: ["issue"],
      arrete: true,
    },

    // --- LA VILLE ------------------------------------------------------------
    "guet-a-vu": {
      dit: "le guet les a vus venir",
      champs: ["hommes"],
      portee: { vu: 70, entendu: 0, trace: 0 },
      aspects: ["nouvelles"],
    },
    "peur-gagne": {
      dit: "une zone bascule parce qu'on les a vus",
      champs: ["par"],
      portee: { vu: 60, entendu: 80, trace: 0 },
      aspects: ["ville", "nouvelles"],
    },
    "rumeur-gagne": {
      dit: "une zone bascule parce qu'on l'a entendu dire",
      champs: ["par"],
      portee: { vu: 60, entendu: 0, trace: 0 },
      aspects: ["ville", "nouvelles"],
    },
    // UN VOISIN QUI SORT AVEC UNE HACHE — ou celui d'en face qui met une planche
    // en travers de sa porte. Ça se voit dans la rue, ça ne s'entend pas, et ça
    // reste toute la nuit : sa porte est ouverte et il n'est pas chez lui. C'est
    // la trace la plus jouable de toutes, parce qu'elle a une ADRESSE et qu'elle
    // attend qu'on vienne lui demander où il était.
    "prend-les-armes": {
      dit: "des gens de la ville se rangent d'un côté",
      champs: ["camp", "zone", "combien", "role", "age", "femme"],
      portee: { vu: 40, entendu: 0, trace: Infinity, trace_vu: 30 },
      aspects: ["ville"],
    },
    // MÊME CHOSE QUE `prend-les-armes`, AVEC UN NOM DESSUS. C'est un habitant
    // nommé, devant chez lui, en train de faire quelque chose de la nuit —
    // barricader, fuir, regarder. Il tombait sur le défaut et ne laissait donc
    // AUCUNE trace : c'est-à-dire que le seul fait du sac qui porte une adresse
    // et une bouche s'effaçait au bout de trente secondes. Il reste, comme son
    // voisin en armes, et pour la même raison.
    "habitant": {
      dit: "quelqu'un qui a un nom, devant chez lui, pendant que ça passe",
      champs: ["nom", "fait"],
      portee: { vu: 35, entendu: 0, trace: Infinity, trace_vu: 30 },
      aspects: ["ville"],
    },
    // LE FEU EST LE FAIT QUI PORTE LE PLUS LOIN DE TOUS, et de très loin. Une
    // maison qui brûle se voit d'un bout à l'autre d'un quartier, s'entend
    // moins qu'elle ne se voit, et laisse un trou noir dans la rue pour le
    // reste de la partie. C'est aussi le seul acte de cette nuit qui change la
    // ville pour de bon : sa trace ne s'éteint jamais.
    "maison-brulee": {
      dit: "une maison part au feu",
      champs: ["corps"],
      portee: { vu: 600, entendu: 200, trace: Infinity, trace_vu: 400 },
      aspects: ["ville"],
      arrete: true,
    },
  };

  // Ce qu'on ne connaît pas se voit de près et ne s'entend pas. Un fait neuf
  // arrive donc timidement plutôt que de crier à travers la ville — c'est le
  // bon défaut : on l'oublie dans la table sans que la partie devienne fausse.
  // Ce n'est PAS une excuse pour l'y oublier : `annales.js` dit tout haut ce
  // qu'il ne connaît pas, et c'est le seul garde-fou qui reste.
  const PORTEE_DEFAUT = { vu: 45, entendu: 0, trace: 0 };

  // ===========================================================================
  // LES DEUX DÉCOUPES, TIRÉES DE LA TABLE ET JAMAIS ÉCRITES À LA MAIN
  // ===========================================================================

  /** `{ <type>: {vu, entendu, trace, trace_vu?} }` — ce que lit `croiser.js`. */
  const PORTEES = {};
  for (const [q, f] of Object.entries(FAITS)) PORTEES[q] = f.portee;

  /** Les types dont la VUE coupe la marche du joueur. */
  const ARRETENT = new Set(
    Object.keys(FAITS).filter((q) => FAITS[q].arrete));

  /** `{ <aspect>: {nom, dit, quoi:[…]} }` — ce que lit `annales.js`. */
  const ASPECTS_PLEINS = {};
  for (const [k, a] of Object.entries(ASPECTS))
    ASPECTS_PLEINS[k] = { nom: a.nom, dit: a.dit, quoi: [] };
  for (const [q, f] of Object.entries(FAITS))
    for (const a of f.aspects || []) {
      if (!ASPECTS_PLEINS[a])
        throw new Error("faits.js : « " + q + " » réclame l'aspect inconnu « " +
                        a + " » — ajoutez-le à ASPECTS ou corrigez la ligne.");
      ASPECTS_PLEINS[a].quoi.push(q);
    }

  /** La portée d'un type, ou le défaut timide s'il n'est pas de la table. */
  const porteeDe = (quoi) => PORTEES[quoi] || PORTEE_DEFAUT;

  /** Tous les aspects d'un type ; `divers` s'il n'en a aucun. */
  const aspectsDe = (quoi) => {
    const f = FAITS[quoi];
    return f && f.aspects && f.aspects.length ? f.aspects.slice() : ["divers"];
  };

  /** Vrai si le type est de la table — ce qui n'est pas le cas rend le défaut. */
  const connu = (quoi) => Object.prototype.hasOwnProperty.call(FAITS, quoi);

  // ===========================================================================
  const API = { FAITS, COMMUNS, ASPECTS: ASPECTS_PLEINS,
                PORTEES, PORTEE_DEFAUT, ARRETENT,
                porteeDe, aspectsDe, connu };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.BatailleFaits = API;
})();
