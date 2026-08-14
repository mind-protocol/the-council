// 1-corps.js — couche 1 : « qu'a appris mon corps pour survivre ? »
//
// ELLE NE DÉCIDE RIEN, ELLE A APPRIS. C'est toute la différence avec une couche
// de « survie » qui arbitrerait entre fuir et se battre : ici personne
// n'arbitre. Le corps a un répertoire de gestes acquis — par le dressage, par
// les batailles précédentes — et sous la menace il sort celui qui est le mieux
// appris. C'est pour ça que deux hommes avec exactement la même peur ne font pas
// le même geste, et c'est la seule chose que cette couche ait à dire.
//
// ─────────────────────────────────────────────────────────────────────────────
// COMMENT ELLE EST FAITE, EN UNE PAGE
//
//   un ÉVÉNEMENT arrive  →  il met un temps à être perçu       (canal, latence)
//                        →  il est atténué par ce qui bouche   (nuit, vacarme…)
//                        →  il est atténué par l'accoutumance  (habituation)
//                        →  il en reste une SAILLANCE
//   la saillance nourrit le REFLEXE — de combien la couche est aux commandes
//   le réflexe × le dressage donnent l'EMPRISE du corps sur la tête
//   les APPELS (ce que la situation réclame) × les ACQUIS (ce que CE corps sait)
//     élisent un geste des JAMBES et un geste des BRAS, séparément
//   le GRAPHE dit ce que cette élection a le droit de produire
//
// DEUX PISTES PARALLÈLES, ET C'EST LA DÉCISION D'ARCHITECTURE. Un homme recule
// en gardant son fer devant lui. Avec des états exclusifs on perd ça — et c'est
// exactement le défaut qu'on a dû corriger à la main dans `bataille2d.js`, où la
// branche « cède le pas » ne contenait aucun moyen de frapper.
//
// SON EMPRISE N'EST PAS UNE PRIORITÉ. Elle ne passe pas en premier parce qu'elle
// porte le numéro 1 : elle passe en premier quand le réflexe est haut, parce que
// la peur suspend la délibération pour de vrai. C'est une FONCTION, pas un rang.
// ─────────────────────────────────────────────────────────────────────────────
//
// Tout est normalisé sur [−1, 1], tout est fonction, et les seules constantes
// sont des mesures du monde. Voir README.md.
// ─────────────────────────────────────────────────────────────────────────────
// CE QUE LA MESURE A DIT — 3 contre 2, de nuit  (scenario-3-contre-2.js)
//
// CE QUI TIENT :
//   · Au repos, apres 30 s sans rien : plante, garde, emprise 0,00. La couche se
//     tait completement quand il ne se passe rien — c'est le test le plus
//     important de tous, et il passe.
//   · L'réflexe monte en 3,0 s et retombe en 45,0 s : rapport de QUINZE. On
//     s'alarme quinze fois plus vite qu'on ne se calme, et l'hysteresis qu'on
//     ecrivait a la main ailleurs sort d'ici toute seule.
//   · integrite(30 pv, coup de 22) et integrite(300 pv, coup de 220) rendent le
//     MEME nombre. Le seuil qui a coute une journee ne peut plus se reproduire.
//   · Dos au mur, l'appel de fuite tombe a -1,00 : ANNULE, pas reduit. Le
//     produit tient, la moyenne aurait laisse un homme courir a moitie.
//   · Aucune arete interdite dans les quatre ecoles.
//
// ─────────────────────────────────────────────────────────────────────────────
// LA PASSE SUIVANTE — ET ELLE A INVALIDE LA PRECEDENTE
//
// Le banc ne tournait plus (`C.appui` avait disparu avec la v2 du gregarisme) :
// tous les chiffres ci-dessus dataient de la v1. En le reparant, on a trouve la
// faute qui les expliquait TOUS.
//
//   LA LATENCE ETAIT UN FILTRE ET DEVAIT ETRE UNE LIGNE A RETARD. Un stimulus
//   emis a `t` etait teste contre `t + latence`, donc toujours rejete, et
//   l'appelant ne le representait jamais. **Aucun stimulus n'a jamais atteint
//   le reflexe depuis l'ecriture du fichier.** Le detail est a l'etape 1 de
//   `pas()`.
//
// Ce qui tombe avec elle — trois conclusions de conception tirees d'une
// tuyauterie percee, et il faut le dire parce qu'on a failli refaire le modele
// de degats pour rien :
//
//   · « Un homme au contact meurt avant d'avoir peur » : faux. On a fait durer
//     un duel jusqu'a 32,7 s, l'alarme ne bougeait pas d'un centieme. Ce
//     n'etait pas une question de duree.
//   · « Le conscrit deroute a 0,0 s a cause d'un stimulus » : faux, il n'en
//     recevait aucun — c'est `couverture` seule.
//   · « Le modele de degats et la couche 1 se contredisent » : ils ne se
//     contredisaient pas, ils ne se parlaient pas.
//
// DEUX AUTRES CORRECTIONS, chacune justifiee a son endroit :
//
//   LE DECOURS (voir `M.DECOURS`). Un coup durait un battement — 6 % du cycle —
//   pour charger une glande de 3 s. L'equilibre du reflexe est la moyenne du
//   rapport cyclique : il valait −0,35 QUELLE QUE SOIT la duree du combat. Il
//   faut 17 % du cycle pour franchir zero.
//
//   LA PRE-HABITUATION (voir `prehabituer`). `hab = vecu` par l'identite mettait
//   le veteran a 0,90 d'habituation : saillance d'un coup recu 0,076, soit une
//   surdite. B1 ne mesurait pas le dressage.
//
// CE QUE LA MESURE DIT MAINTENANT :
//
//   B1 — LE DRESSAGE ORDONNE ENFIN. conscrit 0,0 s · guet 5,7 s · soldat et
//     veteran ne rompent pas. C1 passe pour les deux premiers. C'etait « sans
//     verdict » depuis l'origine.
//   A3 — le zero juste tient toujours : reflexe −1,00, emprise 0,00 apres 30 s
//     de calme. Le decours n'a donc pas ramene de plancher par la porte de
//     derriere, ce qui etait le risque.
//   Aucune arete interdite, dans les quatre ecoles.
//   L'ordre des ecoles sort juste sur le plateau de reflexe, a duel egal :
//     conscrit −0,02 · soldat −0,19 · veteran −0,32.
//
// PUIS LA DYSREGULATION (voir `SOUS_EMPRISE`), qui a regle le defaut principal :
// `emprise` sortait vers les couches 2, 3 et 4 et n'agissait JAMAIS sur les
// gestes de la couche elle-meme. Un conscrit rompait donc a 0,0 s, sans un
// stimulus, avec `emprise 0,00` — un geste de corps elu pendant que le corps ne
// tenait rien du volant.
//
//   Mesure apres : il rompt a 5,7 s, et le releve montre enfin un ARC — coup
//   recu a 1 s, derobade, il tient, la glande monte de −1,00 a −0,16, l'emprise
//   atteint 0,78, ET ALORS il s'en va. Une rupture CAUSEE, au lieu d'une
//   rupture instantanee.
//   A3 tient toujours (−1,00 / 0,00 au repos) : la porte (c) n'a pas ramene de
//   plancher elle non plus.
//   PRIX A PAYER, ET IL EST REEL : le guet ne rompt plus du tout, donc B1 a
//   perdu un cran de resolution. Deux ecoles sur quatre ordonnent, contre une
//   seule avant la passe — c'est un gain, mais pas celui qu'on esperait.
//
// CE QUI RESTE OUVERT :
//
//   1. LE PLATEAU RESTE SOUS ZERO en duel de nuit (−0,02 pour le conscrit).
//      Reste a trancher si c'est juste — un homme frappe une fois toutes les
//      six secondes, la nuit, avec la vue a un tiers — ou s'il manque un
//      stimulus de presence au contact. Ne pas regler : chercher ce qu'on a
//      oublie de modeliser (regle 1).
//   2. C2 NE MESURE PAS CE QU'IL CROIT. Il compare A1 SEUL, qui fait face a
//      DEUX frappeurs, a A2 ACCOMPAGNE, qui n'en a qu'UN : deux hommes
//      differents dans deux situations differentes. Le chiffre qui en sort ne
//      dit rien de la contagion, ni dans un sens ni dans l'autre. C'est le banc
//      qu'il faut refaire, pas le modele.
// ─────────────────────────────────────────────────────────────────────────────
"use strict";
(() => {

  // ===========================================================================
  // LES MESURES DU MONDE — la seule exception à « jamais de constantes »
  // ===========================================================================
  const M = {
    // --- les latences des trois canaux, en secondes ---
    // ELLES ARBITRENT, elles ne décorent pas. Quand deux stimuli arrivent au
    // même instant, celui qui touche est traité le premier — et l'on n'a pas eu
    // à écrire de règle de priorité. C'est aussi ce qui fait qu'on pare un coup
    // qu'on a vu et qu'on encaisse celui qu'on n'a que senti.
    LAT_TACT: 0.030, LAT_OUIE: 0.120, LAT_VUE: 0.180,

    // --- l'adrénaline ---
    // L'ASYMÉTRIE EST LE FAIT, pas les valeurs : on s'réflexe en quelques
    // secondes et l'on se calme en une minute. Elle donne l'hystérésis, et elle
    // remplace à elle seule les marges et les délais de décision qu'on écrivait
    // à la main dans `bataille2d.js`.
    MONTEE_S: 3, DESCENTE_S: 45,

    // --- LE DÉCOURS — combien de temps un stimulus RÉSONNE ---------------------
    // LA SECONDE MOITIÉ DE `LATENCE`, ET ELLE MANQUAIT. La latence dit à quel
    // moment un stimulus commence à compter ; rien ne disait quand il cesse. Un
    // coup reçu durait donc UN BATTEMENT — cinquante millisecondes — pour
    // alimenter une glande dont la montée vaut trois secondes.
    //
    // ⚠ CE N'ÉTAIT PAS UN RÉGLAGE TROP BAS, C'ÉTAIT UN ÉQUILIBRE IMPOSSIBLE.
    // Mesuré : l'équilibre du réflexe est la moyenne du rapport cyclique — 6 %
    // du temps à +0,52, 94 % à −1 — et il vaut **−0,35 quelle que soit la durée
    // du combat**. On a fait durer un duel jusqu'à 32,7 s : l'alarme n'a pas
    // passé zéro une seule fois, dans aucune des quatre écoles. Il faut 17 % du
    // cycle pour franchir zéro, 6 % n'y arriveront jamais.
    //
    // C'est ce qui a fait croire pendant une journée que « la couche 1 n'a pas
    // le temps » et que le modèle de dégâts était en cause. Il ne l'était pas :
    // quadrupler la vie ne change rien à un rapport cyclique.
    //
    // IL EST PAR STIMULUS, ET C'EST CE QUI EN FAIT UNE MESURE ET NON UN RÉGLAGE.
    // Un nombre global serait un bouton. Ce qui se défend, c'est l'ORDRE : un
    // coup encaissé résonne parce qu'il fait mal ; un coup frôlé sursaute sans
    // la douleur ; un fer qu'on voit venir cesse de compter à l'instant où il
    // est passé — il ne résonne pas, il a déjà servi à armer la parade.
    DECOURS: {
      "coup reçu": 2.5, "coup frôlé": 1.5, "voisin à terre": 3,
      "les siens s'en vont": 2, "quelqu'un derrière": 1, "fer qui vient": 0.15,
      "le signe tombe": 4,
    },
    DECOURS_DEFAUT: 1,

    // --- CE QU'UN VÉTÉRAN N'ENTEND PLUS, ET JUSQU'OÙ -------------------------
    // `vecu` est une habituation pré-chargée : c'est la thèse du fichier et elle
    // tient. Mais elle était appliquée par l'IDENTITÉ — `hab = vecu` —, et une
    // identité est une constante déguisée : elle affirme qu'une unité de vécu
    // vaut une unité d'habituation sans dire de quoi c'est le rapport.
    //
    // Mesuré : à `vecu 0,9`, l'habituation initiale valait 0,90, donc la
    // saillance d'un coup reçu tombait de 0,762 à **0,076** — sous le seuil, du
    // côté négatif. Un vétéran ne POUVAIT PAS être alarmé d'être frappé. Le
    // banc B1 ne mesurait donc pas le dressage, il mesurait une surdité.
    //
    // L'habituation atténue ; elle n'abolit jamais. Le plafond est le fait.
    SOURD_MAX: 0.55,

    // --- CE QUI FAIT REDESCENDRE PLUS VITE, ET QUI N'EST PAS DE SOI ----------
    // Les deux chiffres viennent de `bataille2d`, dont ils sont la traduction
    // exacte — c'est le poste 3 de la depose, et le seul honnete : on ne
    // reinvente pas un nombre quand celui qu'on remplace en a deja un.
    //
    //   `TIENT_BANN = 2,6` — « la morale remonte mieux sous une banniere
    //     debout ». Il MULTIPLIAIT LA REPRISE, jamais le niveau : il se
    //     transpose donc tel quel sur la constante de descente.
    //   Pour le chef, `RALLIE_TAUX / REPRISE` vaut 8,3 — mais ce huit-la mesure
    //     une MAIN TENDUE a un homme qui part deja, pas une presence. On garde
    //     son ORDRE (un chef a quinze metres pese plus qu'un drapeau a cent
    //     dix) sans recopier son chiffre, qui dirait autre chose.
    APAISE_BANN: 2.6,
    APAISE_CHEF: 4,
    APAISE_MAX: 5,        // l'asymptote : au mieux six fois plus vite, jamais plus

    // --- les distances du corps ---
    EPAULE_M: 0.55,    // largeur d'un homme en armes
    COUDE_M: 2.2,      // jusqu'où l'on sait, sans regarder, que le voisin est là
    IMMEDIAT_M: 3.4,   // de quoi être touché avant d'avoir fini son geste

    // --- les temps de séjour, en secondes ---
    // Un geste DURE, donc il ne bégaie pas. Ce ne sont pas des anti-rebonds :
    // ce sont des durées d'homme, et chacune se défend séparément.
    SEJOUR: {
      "planté":     [0, 0],       // le seul état de repos : aucun minimum
      "serrer":     [0.4, 2],     // deux pas de côté, le temps de refermer
      "recul":      [0.6, 6],     // log-uniforme, médiane 1,9 s
      "dérobade":   [0.2, 0.5],   // une esquive, non interruptible
      "fuite":      [3, 3],       // au moins le temps de prendre sa course
      "ruée":       [1, 3],
      "sidération": [1, 10],
    },
    SEJOUR_BRAS: { "parer": [0.15, 0.35], "ballants": [1, 1] },

    // --- la nuit, le bruit, la presse ---
    // CETTE BATAILLE SE JOUE À QUATRE HEURES ET DEMIE. Ce n'est pas un cas
    // d'école, c'est le cas nominal : le canal de la vue tombe à un tiers, donc
    // le stimulus « je vois le fer partir » disparaît presque, donc on ne pare
    // plus par anticipation. Tout le reste en découle.
    GAIN_NUIT: 0.32,
    OREILLES: 4,           // hommes au contact qui suffisent à couvrir une oreille
    // De combien de temps un homme met a trouver normal que ses voisins
    // soient tendus. Court : une ligne s'habitue a sa propre nervosite en
    // quelques secondes, et c'est ce qui l'empeche de s'emballer sur
    // elle-meme.
    AMBIANT_S: 6,
    // Et de combien la lecture doit sauter au-dessus de l'ambiant pour
    // valoir un sursaut. Un cran de la table `LISIBLE` — soit a peu pres
    // le pas entre « il cede le pas » et « il court ».
    SURSAUT_SOCIAL: 0.6,
    COUDES_BLOQUANTS: 4,   // voisins pressants qui interdisent un pas de côté
  };

  // ===========================================================================
  // LA BOÎTE À OUTILS — borner sans écrêter
  // ===========================================================================

  // `tanh` plutôt qu'un `min/max` : douce partout, nulle en zéro, impaire —
  // donc ni bosse aux bornes ni asymétrie qu'on n'aurait pas voulue.
  const sature = (x, k) => Math.tanh(x / k);

  // Ramener une part de [0, max] sur [−1, +1].
  const part = (x, max) => (max > 0 ? Math.max(-1, Math.min(1, 2 * (x / max) - 1)) : -1);

  // Moyenne pondérée de signaux DÉJÀ normalisés : elle reste dans [−1, 1] par
  // construction, sans borne à poser. C'est toute la raison de normaliser en
  // amont.
  const melange = (paires) => {
    let s = 0, p = 0;
    for (const [v, w] of paires) { if (v == null) continue; s += v * w; p += w; }
    return p > 0 ? s / p : 0;
  };

  // Décroissance en 1/(1+x²) : le voisin de coude compte énormément, celui à six
  // mètres presque rien, et il n'y a AUCUN rayon au-delà duquel ça s'arrête net.
  const pres = (d, echelle) => 1 / (1 + (d / echelle) * (d / echelle));

  // Tirage log-uniforme — densité en 1/x. Beaucoup de courts, quelques longs,
  // rien d'arbitraire au milieu. C'est la loi des durées de geste.
  const logUnif = (a, b, u) => (a === b ? a : a * Math.pow(b / a, u));

  // ===========================================================================
  // LES SIGNAUX — l'état continu, chacun sur [−1, 1]
  // ===========================================================================

  // ---- L'INTÉGRITÉ ---------------------------------------------------------
  // PAS UNE PART DE POINTS DE VIE, et c'est le sujet même de la règle des
  // constantes. « La moitié de ses points » ne veut rien dire tant qu'on ne sait
  // pas ce qu'un coup retire : à trois cents points c'est sept coups, à trente
  // c'est moins d'un. La grandeur qui a un sens pour un homme est LE NOMBRE DE
  // COUPS QU'IL PEUT ENCORE ENCAISSER — et elle survit à n'importe quel
  // changement d'échelle, ce que le seuil qu'elle remplace n'a pas su faire.
  const integrite = (vie, coupTypique) => {
    if (!(coupTypique > 0)) return 1;
    return 2 * sature(vie / coupTypique, 3) - 1;
  };

  // ---- LE SOUFFLE ----------------------------------------------------------
  // Déjà une part de quelque chose de borné : simple changement d'échelle. On ne
  // le sature pas — être à bout est un état physique franc, pas une asymptote.
  const souffle = (s) => part(s, 1);

  // ===========================================================================
  // LE GREGARISME — v2
  // ===========================================================================
  // CE QUE LA v1 AVAIT DE FAUX, ET IL FAUT L'ECRIRE PARCE QUE C'ETAIT UNE FAUTE
  // DE PRINCIPE, pas de reglage :
  //
  //   ELLE LISAIT `voisin.réflexe`. C'est-a-dire la VARIABLE INTERIEURE de
  //   l'autre — sa peur, directement, sans passer par le monde. De la
  //   telepathie, dans la couche dont toute la discipline tient en une phrase :
  //   le corps ne percoit que des SIGNES. On ne voit pas la peur d'un homme, on
  //   voit qu'il recule, qu'il a lache son bouclier, qu'il ne bouge plus.
  //
  //   ELLE SAUTAIT LES CANAUX. Tout le reste du fichier passe par `gain()` — la
  //   nuit, le vacarme, la surdite de stress. La contagion, non : un homme
  //   « sentait » ses voisins a travers l'obscurite et le bruit. Or c'est
  //   justement de nuit qu'on ne voit plus son rang, et c'est ce qui fait la
  //   difference entre une ligne de jour et une ligne de nuit.
  //
  //   ELLE ETAIT SYMETRIQUE. Un homme qui hurle en contamine quatre ; quatre
  //   hommes calmes n'en calment pas un qui hurle. La peur monte plus vite
  //   qu'elle ne descend chez les autres comme chez soi.
  //
  //   SES SECTEURS FAISAIENT DES MARCHES. Huit cases et un `max` : un voisin qui
  //   passait d'un secteur au suivant basculait quarante-cinq degres de pourtour
  //   d'un coup. C'etait un artefact de discretisation, et `SECTEURS = 8` etait
  //   une constante de plus dont personne ne pouvait dire d'ou elle sortait.
  //
  //   ET ELLE IGNORAIT LES ENNEMIS. Un secteur tenu par un ennemi comptait comme
  //   un secteur VIDE. Or avoir quelqu'un derriere soi n'est pas la meme chose
  //   que n'avoir personne : c'est le pire des etats, et le pourtour doit le
  //   dire.

  // ---- LA COUVERTURE — un pourtour continu, ami en plus, ennemi en moins ----
  // Plus de cases : chaque voisin couvre un ARC autour de sa direction, avec une
  // cloche angulaire. La largeur de l'arc n'est pas un reglage — c'est ce qu'un
  // homme d'une demi-largeur d'epaules occupe, vu de la ou l'on est : de pres il
  // bouche beaucoup, de loin presque rien. La geometrie donne l'angle, on ne le
  // choisit pas.
  //
  // ET TOUS LES SECTEURS NE SE VALENT PAS. On ne demande pas qu'on nous couvre
  // DEVANT — on y fait face soi-meme. Le besoin va de 0 droit devant a 1 droit
  // derriere, et la couverture est la moyenne PONDEREE PAR CE BESOIN. Quatre
  // camarades tous masses devant soi laissent un homme seul, et c'est ce qu'un
  // compte de tetes ne pouvait pas dire.
  //
  // `voisins` : [{ angle, distance, ami, jambes, bras }] — l'angle EN RELATIF de
  // son cap. Aucun nom, aucun compte, aucune variable interieure : des formes
  // autour de lui, et ce qu'elles ont l'air de faire.
  const ARCS = 24;                     // la finesse du releve, pas un reglage
  const couverture = (voisins) => {
    if (!voisins || !voisins.length) return -1;
    const pas = 2 * Math.PI / ARCS;
    let somme = 0, total = 0;
    for (let k = 0; k < ARCS; k++) {
      const a = k * pas;
      const besoin = (1 - Math.cos(a)) / 2;          // 0 devant, 1 derriere
      let tenu = 0;
      for (const v of voisins) {
        // Ce qu'il bouche, vu d'ici : deux demi-epaules a sa distance.
        const large = Math.atan2(M.EPAULE_M, Math.max(0.3, v.distance));
        let ecart = Math.abs(((a - v.angle + Math.PI) % (2 * Math.PI)) - Math.PI);
        const part = Math.exp(-(ecart * ecart) / (2 * large * large));
        // UN AMI COUVRE, UN ENNEMI DECOUVRE. C'est le terme qui manquait : avoir
        // quelqu'un derriere soi n'est pas avoir personne, c'est pire.
        tenu += part * (v.ami ? 1 : -1.4) * pres(v.distance, M.COUDE_M * 1.6);
      }
      somme += Math.max(-1, Math.min(1, tenu)) * besoin;
      total += besoin;
    }
    // ⚠ L'ECHELLE, ET ELLE A FAILLI ANNULER TOUTE LA MESURE. Un arc sans
    // personne rend `tenu = 0` ; si l'on moyenne tel quel, un homme SEUL rend
    // zero — c'est-a-dire « l'ordinaire » — au lieu de −1. La v2 l'a fait
    // pendant une passe, et « deux camarades masses devant lui » est passe de
    // −0,81 a +0,05 : la mesure s'annulait elle-meme, en silence, et rien dans
    // le code ne le disait. On ramene donc la part TENUE sur [−1, 1], comme la
    // v1 le faisait — les ennemis, eux, poussent en dessous de zero.
    return Math.max(-1, Math.min(1, 2 * (somme / (total || 1)) - 1));
  };

  // ---- L'OUVERTURE — PAR OU le trou est, et non pas seulement s'il y en a ----
  // La v1 rendait un scalaire, donc `serrer` savait qu'il fallait se refermer et
  // pas de quel cote. Un geste qu'on ne peut pas executer n'est pas un geste.
  // Rend l'angle relatif du plus grand vide pondere par le besoin — c'est la
  // direction dans laquelle le corps se deporte.
  const ouverture = (voisins) => {
    const pas = 2 * Math.PI / ARCS;
    let pire = -Infinity, ou = Math.PI;
    for (let k = 0; k < ARCS; k++) {
      const a = k * pas, besoin = (1 - Math.cos(a)) / 2;
      let tenu = 0;
      for (const v of (voisins || [])) {
        if (!v.ami) continue;
        const large = Math.atan2(M.EPAULE_M, Math.max(0.3, v.distance));
        let ecart = Math.abs(((a - v.angle + Math.PI) % (2 * Math.PI)) - Math.PI);
        tenu += Math.exp(-(ecart * ecart) / (2 * large * large)) *
                pres(v.distance, M.COUDE_M * 1.6);
      }
      const manque = besoin * (1 - Math.min(1, tenu));
      if (manque > pire) { pire = manque; ou = a; }
    }
    return ou;
  };

  // ---- L'ALIGNEMENT — OU LES AUTRES FONT FACE -------------------------------
  // Quatrieme famille, et la derniere qui manquait : une ligne se forme sans que
  // personne l'ordonne. Chacun se tourne un peu vers la ou les autres se
  // tournent, et de proche en proche cent hommes regardent le meme cote.
  //
  // ⚠ L'ALIGNEMENT ET LE REGARD SONT LA MEME MESURE, ET ON LES FUSIONNE — en le
  // disant. On voulait deux choses : l'orientation du CORPS (la formation) et
  // l'orientation de l'ATTENTION (ce qu'on remarque). Elles sont distinctes chez
  // un homme reel. Mais le modele ne tient qu'un cap par homme : rien, dans
  // l'etat, ne permet de savoir s'il regarde ailleurs que ou il fait face. Deux
  // concepts qui partagent leur unique mesure sont UN concept tant que le modele
  // ne sait pas les separer — les distinguer ici ne produirait que deux noms
  // pour un nombre, et l'illusion d'avoir modelise le second.
  //
  // Moyenne CIRCULAIRE, et pas arithmetique : un voisin a +170° et un a −170°
  // regardent tous deux derriere, et leur moyenne plate serait DEVANT. C'est la
  // faute classique des angles, et elle donne une ligne qui fait face au vide.
  //
  // Rend l'angle relatif vers lequel le corps veut se tourner, ou `null` s'il ne
  // voit personne — auquel cas il garde son cap, ce qui est le bon defaut.
  const alignement = (voisins, ctx) => {
    if (!voisins || !voisins.length) return null;
    let x = 0, y = 0;
    for (const v of voisins) {
      if (!v.ami || v.cap == null) continue;
      const peri = Math.max(0, (Math.cos(v.angle) + 0.35) / 1.35);
      const per = (ctx && ctx.nuit ? M.GAIN_NUIT : 1) * peri *
                  pres(v.distance, M.COUDE_M);
      if (per <= 0.001) continue;
      x += Math.cos(v.cap) * per; y += Math.sin(v.cap) * per;
    }
    if (Math.hypot(x, y) < 1e-6) return null;
    return Math.atan2(y, x);
  };

  // ---- LE COUDE — est-ce qu'il TOUCHE quelqu'un ? ---------------------------
  // Le pourtour dit s'il est entoure ; celui-ci dit s'il est en CONTACT. Ce sont
  // deux choses, et la seconde declenche le geste : on ne cherche pas l'epaule
  // parce qu'on est peu nombreux, on la cherche parce qu'on ne la sent plus.
  const coude = (voisins) => {
    if (!voisins || !voisins.length) return -1;
    let mieux = 0;
    for (const v of voisins)
      if (v.ami) mieux = Math.max(mieux, pres(v.distance, M.EPAULE_M * 2));
    return 2 * mieux - 1;
  };

  // ---- CE QU'UN VOISIN MONTRE ------------------------------------------------
  // LA TABLE EST LE SYSTEME, et elle ne dit pas ce qu'il ressent : elle dit ce
  // qu'on VOIT de lui. Positif = signe d'alarme. C'est la seule chose que le
  // corps ait le droit de lire chez un autre, et ca suffit — c'est meme
  // exactement ce qu'un homme lit vraiment d'un voisin dans le noir : sa
  // silhouette qui recule, ses bras qui tombent, son immobilite.
  //
  // ⚠ LE POLE CALME DOIT VALOIR −1, ET IL A ETE GRADUE PAR ERREUR. Les valeurs
  // rassurantes etaient etalees (`planté` −0,6, `garde` −0,4) et l'on prend le
  // MAX des deux — donc un voisin parfaitement tranquille lisait −0,4, et la
  // contagion ne pouvait jamais descendre plus bas. Elle EPINGLAIT le reflexe :
  // mesure faite, un homme intact avec rien autour se stabilisait a −0,40 et
  // gardait 38 % d'emprise au repos. Le corps tenait un tiers du volant sans
  // qu'il se passe quoi que ce soit.
  //
  // Toute l'information utile est du cote ALARMANT — un homme calme est calme,
  // il n'y a pas de degres de tranquillite a lire de loin dans le noir. Les
  // graduations du bas etaient une precision inventee, et elle coutait le
  // repos de la couche.
  const LISIBLE = {
    "planté": -1, "serrer": -1, "recul": 0.4, "dérobade": 0.2,
    "fuite": 1.0, "ruée": 0.5, "sidération": 0.8,
    "garde": -1, "frapper": -1, "parer": -0.6, "ballants": 0.9,
  };

  // LES DEUX CANAUX NE LISENT PAS LES MEMES SIGNES, et c'est ce qui manquait
  // pour que la nuit veuille dire quelque chose. On ENTEND un homme qui rompt
  // et qui court, on entend un cri de charge ; on n'entend pas un homme baisser
  // sa garde, ni un homme se figer — la sideration est silencieuse, et c'est
  // meme ce qui la rend terrible dans le noir.
  //
  // Sans cette table, l'ouie couvrait tout ce que la nuit retirait a la vue, et
  // une ligne de nuit se comportait exactement comme une ligne de jour. Mesure :
  // la contagion ne bougeait pas d'un centieme entre les deux.
  // ---- CE QU'UNE FORME PORTE, en plus de ce qu'elle fait ------------------
  // UNE BANNIÈRE EST UNE FORME COMME UNE AUTRE, simplement plus grande et
  // plus loin — et c'est ce qui permet de la faire entrer sans lui écrire
  // une mécanique à elle. Le corps ne sait pas ce qu'est une bannière : il
  // voit une chose haute et immobile au-dessus des têtes, et il a appris que
  // tant qu'elle est là, les siens sont là.
  //
  // C'EST LE SEUL MOYEN QUE LE COMMANDEMENT AIT DE **PROTÉGER**. Tout le
  // reste de ce qu'un chef fait — ordonner, placer, envoyer — DÉPLACE des
  // hommes ; la bannière et sa présence sont les deux seules choses qui les
  // TIENNENT. Déposer la morale sans elles retirerait au commandement sa
  // moitié la plus utile, et personne ne s'en apercevrait avant trois
  // cuissons.
  //
  // ET ELLES PASSENT PAR LES CANAUX COMME LE RESTE : la nuit mange la
  // bannière, le vacarme mange le chef. Une troupe de nuit dans le bruit est
  // une troupe sans commandement, et l'on n'a pas eu à l'écrire.
  const PORTE = {
    "bannière":         -1,     // debout : rien ne rassure autant
    "chef":             -0.85,  // il est là, et il n'a rien à dire pour ça
    "bannière à terre":  0.95,  // et rien n'alarme autant qu'elle qui tombe
  };
  // Une épaule se sent au coude ; une hampe se voit d'un bout du rang à
  // l'autre. Deux échelles, deux portées.
  // ⚠ QUARANTE METRES COUVRAIENT UNE AILE ENTIERE, et c'etait le defaut.
  // Mesure : zero fuyard sur une cuisson complete, et la porte meme plus
  // enfoncee — chaque escouade ayant son porte-banniere, personne n'etait
  // jamais loin d'une, donc plus rien ne passait des voisins nulle part.
  //
  // LA VALEUR DIT CE QUE CA VAUT, LA PORTEE DIT COMBIEN D'HOMMES Y ONT
  // DROIT — et c'est la seconde qui etait trop genereuse. Une hampe rassure
  // ceux qui l'ont AU-DESSUS d'eux, pas une aile de deux cents hommes ; on
  // la ramene a ce qu'un rang serre couvre. Sa chute, elle, se voit de loin
  // et garde sa portee : on ne voit pas la banniere qu'on a, on voit celle
  // qui tombe.
  const PORTEE_SIGNE = { "bannière": 15, "bannière à terre": 40, "chef": 8 };
  // Le chef s'entend ; la hampe, non.
  const SIGNE_AUDIBLE = { "chef": 0.8, "bannière": 0, "bannière à terre": 0.3 };

  const AUDIBLE = {
    "fuite": 1, "ruée": 0.9, "ballants": 0.3, "recul": 0.2,
    "planté": 0, "serrer": 0.15, "dérobade": 0, "sidération": 0,
    "garde": 0, "frapper": 0.4, "parer": 0.2,
  };

  // LA PEUR PESE PLUS QUE LE CALME, et ce n'est pas une opinion : un homme qui
  // rompt en entraine quatre, quatre hommes fermes n'en retiennent pas un qui
  // rompt. Le poids d'un voisin est donc multiplie par ce qu'il montre d'alarme.
  const PANIQUE = 2.5;

  /**
   * Ce que le troupeau lui fait, tout compris — et ca passe par les CANAUX,
   * comme le reste. De nuit on ne voit plus son rang : c'est le fait qui separe
   * une ligne de jour d'une ligne de nuit, et la v1 le sautait entierement.
   *
   * Rend { contagion, imitation } :
   *   contagion — l'alarme qu'on prend des autres, sur [-1, 1]
   *   imitation — pour chaque geste, la part des voisins qui le font. Le corps
   *     copie sans decider, et c'est LA MEME MESURE qui sert aux deux : on lit
   *     une fois ce qu'ils font, on s'en sert pour trembler et pour suivre.
   */
  // ---- L'INITIATEUR — celui qui bouge le PREMIER pese plus ------------------
  // C'est la troisieme famille, et la seule qui soit temporelle. Un voisin qui
  // vient de changer de geste ne compte pas comme un voisin qui fait la meme
  // chose depuis vingt secondes : le mouvement SOUDAIN capte, l'immobile est du
  // decor. C'est la meme asymetrie que la soudainete d'un stimulus, appliquee au
  // troupeau — et c'est elle qui fait qu'une ligne se defait EN VAGUE, de proche
  // en proche, au lieu de fondre uniformement.
  //
  // Sans elle, l'imitation est un vote : tout le monde pese pareil, donc rien
  // ne part jamais de quelque part. Avec elle, il y a un PREMIER, et l'on peut
  // remonter la vague jusqu'a lui.
  const INITIATEUR = 2.0;
  const NEUF_S = 1.5;            // ce qu'un geste garde de sa nouveaute

  const signes = (voisins, ctx) => {
    const imitation = {};
    // ⚠ `apaise` SUR LES DEUX SORTIES, ET IL MANQUAIT SUR CELLE-CI. Un homme
    // sans un voisin sortait par cette ligne, donc sans le champ ; l'appelant
    // multipliait alors par `undefined`, la contagion passait a NaN, et le
    // reflexe avec elle — DEFINITIVEMENT, puisqu'un NaN ne redescend jamais.
    //
    // Mesure : 116 hommes sur 604 avaient un reflexe qui n'etait pas un
    // nombre ; leur election retombait sur `courant`, c'est-a-dire `plante`,
    // pour toute la nuit. Une bataille de six cents secondes rendait ZERO mort
    // et un verrou intact — et l'on a d'abord accuse la depose de `morale`,
    // puis l'election de `sideration`.
    //
    // Un champ absent sur UNE branche de retour est la panne la plus chere de
    // toute la seance, et la moins visible : rien n'a jete, rien n'a prevenu.
    if (!voisins || !voisins.length)
      return { contagion: -1, imitation, apaise: 1 };
    let somme = 0, poids = 0;
    // Ce que les signes autour de lui apaisent, de 1 (rien) à 0 (une hampe
    // debout à trois pas). Le PLUS FORT gagne : on ne cumule pas deux
    // bannières, on se rassure de la meilleure.
    let apaise = 1;
    for (const v of voisins) {
      if (!v.ami) continue;
      // On le voit (ou pas). Le cap relatif sert de `deFace` : ce qui est
      // derriere soi ne se voit pas, et le vacarme couvre ce qui s'entend.
      // ⚠ ON NE LIT PAS SES VOISINS AVEC LE CONE DE LA MENACE. `gain("vue")`
      // passe par `tunnel`, qui rend ZERO des quatre-vingt-dix degres : on ne
      // voyait donc AUCUN voisin de rang, et la contagion saturait a -1 pour
      // tout le monde. C'etait une confusion de deux champs visuels differents —
      // celui qui suit un fer qui arrive est etroit, celui qui sait que l'epaule
      // d'a cote est encore la est LARGE. La vision peripherique est justement
      // ce qui sert a tenir un rang.
      //
      // Cent dix degres de part et d'autre, degrade jusqu'a rien dans le dos —
      // ce sont les bornes du champ humain, pas un reglage. Le retrecissement
      // sous réflexe s'y applique quand meme : c'est LUI, le tunnel, et il mord
      // d'abord sur ce qu'on voit du coin de l'oeil. La peur coupe un homme de
      // son rang avant de le couper de son ennemi.
      const serre = Math.max(0, Math.min(0.85, (ctx.reflexe + 1) / 2 * 0.7));
      const peri = Math.max(0, (Math.cos(v.angle) + 0.35) / 1.35) * (1 - serre);
      const vu = (ctx.nuit ? M.GAIN_NUIT : 1) * peri;
      const entendu = gain("ouie", ctx, 1);
      // Ce qui se voit passe par l'oeil ; ce qui fait du bruit passe AUSSI par
      // l'oreille, et seulement pour la part qui en fait. De nuit il ne reste
      // que le bruit — donc on sait qu'un homme court, on ne sait pas qu'un
      // autre a baissé les bras.
      // CE QU'IL PORTE PRIME SUR CE QU'IL FAIT, et se lit de plus loin. Une
      // hampe debout n'est pas un geste : c'est un FAIT, et il rassure même
      // quand celui qui la tient recule.
      const porte = v.porte || null;
      const bruit = porte ? (SIGNE_AUDIBLE[porte] || 0)
                          : Math.max(AUDIBLE[v.jambes] || 0, AUDIBLE[v.bras] || 0);
      // ⚠ CE QUE « SOURD » VEUT DIRE, ET CE N'EST PAS UN DRESSAGE. Le corps
      // des faux gueux « n'écoute rien, ni un ordre ni un mort : il avance au
      // cantique et il avancera jusqu'au bout ». Ce n'est ni du courage ni de
      // l'entraînement — c'est une FERMETURE DU CANAL SOCIAL. Il voit tomber
      // son voisin comme n'importe qui ; ça ne lui fait rien.
      //
      // Elle vit donc sur la perception et pas dans les acquis : un homme
      // sourd n'a pas appris à tenir, il n'entend pas ce qui fait partir les
      // autres. C'est la différence entre un vétéran et un fanatique, et le
      // modèle ne savait pas la dire tant que tout passait par le dressage.
      const echelle = porte ? (PORTEE_SIGNE[porte] || M.COUDE_M) : M.COUDE_M;
      const per = Math.max(vu, entendu * bruit) * pres(v.distance, echelle);
      if (per <= 0.001) continue;
      const lu = porte ? PORTE[porte]
                       : Math.max(LISIBLE[v.jambes] == null ? 0 : LISIBLE[v.jambes],
                                  LISIBLE[v.bras] == null ? -1 : LISIBLE[v.bras]);
      // Ce qu'il montre, ce qu'il montre DEPUIS COMBIEN DE TEMPS, et de combien
      // sa peur pese plus que son calme. Les trois se multiplient.
      const neuf = 1 + INITIATEUR * Math.exp(-(v.depuis == null ? 9 : v.depuis) / NEUF_S);
      // ⚠ UN SIGNE N'EST PAS UN VOISIN, ET IL NE VOTE PAS. Première version :
      // la bannière entrait dans la moyenne pondérée comme un homme, avec sa
      // lecture de −1 et sa portée de quarante mètres. Tout homme de la
      // formation en avait donc une dans sa liste, en permanence, et elle
      // DILUAIT le pic de n'importe quel fuyard : mesure faite, 95 morts et
      // ZÉRO fuyard sur une cuisson entière. Plus personne ne rompait, jamais.
      //
      // C'est la même faute que `LISIBLE` épinglant la contagion à −0,4, mais
      // par le haut : une source constante, maximale et omniprésente écrase
      // toute variation — et la contagion est une DÉRIVÉE, donc elle meurt.
      //
      // Un signe est un CONTEXTE, pas un pair. Il ne dit pas « voilà ce qui se
      // passe », il dit « voilà ce sur quoi tu peux compter ». Il module donc
      // ce que les hommes transmettent, au lieu de s'y ajouter — et il garde
      // son percept : il passe par les canaux, la nuit le mange, le vacarme
      // mange le chef.
      if (porte) { apaise = Math.min(apaise, 1 + lu * per); continue; }
      const w = per * neuf * (1 + PANIQUE * Math.max(0, lu));
      somme += lu * w; poids += w;
      // UN SIGNE NE S'IMITE PAS : on ne « fait » pas une bannière. Il rassure
      // ou il alarme, il n'entraîne aucun geste.
      if (!porte) for (const g of [v.jambes, v.bras])
        if (g) imitation[g] = (imitation[g] || 0) + per * neuf;
    }
    let tot = 0;
    for (const g in imitation) tot = Math.max(tot, imitation[g]);
    for (const g in imitation) imitation[g] /= (tot || 1);
    // ⚠ LA SURDITÉ S'APPLIQUE AU RÉSULTAT, PAS AUX POIDS — et la première
    // version l'avait mise sur `per`, donc au numérateur ET au dénominateur
    // d'une moyenne pondérée. Un gain uniforme s'y SIMPLIFIE : mesure faite,
    // la contagion valait +0,97 pour un homme ouvert comme pour un sourd à
    // 0,85. La fermeture ne changeait rien du tout, et rien à la lecture ne
    // le disait.
    //
    // ET ELLE NE TOUCHE QUE LA CONTAGION, PAS L'IMITATION. C'est une
    // distinction plus fine que ce qu'on avait en tête, et elle est plus
    // vraie : le fanatique IMITE SANS S'ÉMOUVOIR. Il marche avec les autres,
    // il se resserre avec eux, il fait ce qu'ils font — il n'est simplement
    // pas remué par leur peur. Un corps qui avance au cantique n'est pas un
    // corps isolé, c'est un corps que rien n'atteint.
    const sourd = Math.max(0, Math.min(1, (ctx && ctx.sourd) || 0));
    const brut = poids > 0 ? somme / poids : -1;
    return { contagion: -1 + (1 - sourd) * (brut + 1), imitation,
             apaise: Math.max(0, Math.min(1, apaise)) };
  };

  // ---- LA MENACE -----------------------------------------------------------
  // Combien, à quelle distance, et de quel côté. La proximité au carré parce que
  // la menace explose sur les deux derniers mètres — c'est là qu'on n'a plus le
  // temps de rien.
  const menace = (proches) => {
    if (!proches || !proches.length) return -1;
    let somme = 0;
    for (const p of proches) {
      const pr = Math.max(0, 1 - p.distance / M.IMMEDIAT_M);
      // ⚠ CE TERME A ÉTÉ ÉCRIT `1 − deFace` ET C'ÉTAIT FAUX — la première
      // version du fichier. Un ennemi PILE EN FACE donnait alors zéro : un
      // homme en train de se faire frapper de front percevait un péril nul,
      // ses bras tombaient au premier battement, et tous les ordres du
      // scénario s'inversaient. La mesure l'a sorti en une passe ; à la
      // lecture, rien ne se voyait.
      //
      // De face il compte pour moitié, de flanc pour un, de dos pour un et
      // demi. Le rapport de trois entre le dos et la face est à peu près ce
      // que dit la physiologie de la surprise — et surtout, aucun angle ne
      // vaut zéro : un homme qu'on voit venir reste un homme qui vous tue.
      const angle = 1 - 0.5 * (p.deFace == null ? 0 : p.deFace);
      somme += pr * pr * angle * (p.frappe ? 1.6 : 1);
    }
    return 2 * sature(somme, 1.4) - 1;
  };

  // ---- L'ISSUE -------------------------------------------------------------
  // ACCULÉ N'EST PAS UN ÉTAT D'ÂME, C'EST UNE GÉOMÉTRIE, et c'est le signal qui
  // manque le plus souvent. Un homme qui a une rue derrière lui et un homme
  // adossé à un mur n'ont pas la même peur pour la même menace — et le second se
  // bat mieux, ce qui est le contraire de ce qu'on attend naïvement.
  const issue = (degagement) => part(degagement == null ? 1 : degagement, 1);

  // ===========================================================================
  // LES CANAUX — ce qui atténue AVANT que le corps ait rien à en faire
  // ===========================================================================
  // PORTE (a) : la perception. Un stimulus qu'on ne reçoit pas ne déclenche
  // rien, et ce n'est PAS la même chose qu'un stimulus qu'on reçoit et qu'on
  // ignore. Confondre les deux est la faute la plus commune du genre.
  const LATENCE = { tact: M.LAT_TACT, ouie: M.LAT_OUIE, vue: M.LAT_VUE };

  // Le vacarme se dérive de ce qui existe déjà — les hommes au contact autour de
  // soi — donc ce n'est pas une constante de plus.
  const vacarme = (pressants, ennemisProches) =>
    sature(((pressants || 0) + (ennemisProches || 0)) / M.OREILLES, 1);

  // LA SURDITÉ DE STRESS — l'exclusion auditive, qui est documentée. Elle tue le
  // SEUL canal qui informe sur le dos, et elle le tue exactement quand il
  // servirait : réflexe haute → on n'entend plus derrière → on est pris à
  // revers → réflexe plus haute.
  const surdite = (reflexe) => Math.pow(Math.max(0, (reflexe + 1) / 2), 2);

  // LE TUNNEL — le champ visuel se rétrécit sous le réflexe. La boucle la plus
  // vicieuse et la plus vraie : peur → on ne voit plus partir les coups → on est
  // surpris → peur. Un homme qui commence à avoir peur devient OBJECTIVEMENT
  // plus facile à tuer, ce qui justifie sa peur.
  const tunnel = (reflexe, deFace) => {
    const serre = Math.max(0, Math.min(0.95, (reflexe + 1) / 2 * 0.8));
    const f = deFace == null ? 1 : deFace;
    return Math.max(0, (f - serre) / (1 - serre));
  };

  /** Ce qui reste d'un stimulus après ce qui bouche. Porte (a), et elle seule. */
  const gain = (canal, ctx, deFace) => {
    if (canal === "tact") return 1;                    // rien ne bouche le toucher
    if (canal === "ouie")
      return (1 - (ctx.vacarme || 0)) * (1 - surdite(ctx.reflexe));
    return (ctx.nuit ? M.GAIN_NUIT : 1) * tunnel(ctx.reflexe, deFace);
  };

  // ===========================================================================
  // LES SIX STIMULI — leur formule de détection
  // ===========================================================================
  // LA RÈGLE QUI LES GARDE HONNÊTES : le corps ne compte pas. « Je suis en
  // infériorité » n'est pas un stimulus, c'est une conclusion — couche 2. Si un
  // stimulus ne se rattache pas à un sens, il n'est pas d'ici.

  // 1. LE COUP QUI TOUCHE — tact. Contre le dégât TYPIQUE, jamais contre les
  // points de vie : ce qui compte pour un corps n'est pas la fraction de sa
  // jauge, c'est « ce coup-là sortait-il de l'ordinaire ».
  const coupRecu = (degat, degatTypique, deFace, ecu) => ({
    quoi: "coup reçu", canal: "tact", deFace,
    // L'écu atténue ce qu'on PERÇOIT, pas ce qu'on encaisse : un coup pris sur
    // le bouclier surprend moins, même s'il fait mal.
    force: sature(degat / (degatTypique || 1), 1) * (ecu == null ? 1 : ecu),
    soudainete: 1,
  });

  // 2. LE COUP QUI FRÔLE — tact. LE MODÈLE N'A PAS DE TRAJECTOIRE DE LAME, donc
  // pas d'écart en mètres — mais il a mieux : DE COMBIEN LE JET A MANQUÉ SON
  // SEUIL. Un raté de peu EST un frôlement, et la substitution porte la même
  // information psychologique.
  //
  // Il est souvent plus violent que le coup reçu, et c'est le fait qu'il faut
  // respecter : le coup reçu est fini, le coup manqué annonce le suivant.
  const coupFrole = (tire, seuil, deFace) => ({
    quoi: "coup frôlé", canal: "tact", deFace,
    force: Math.max(0, 1 - (tire - seuil) / (seuil || 1)),
    soudainete: 1,
  });

  // 3. LE FER QUI PART VERS MOI — vue. La seule formule qui soit une vraie loi
  // perceptive : l'imminence se perçoit en 1/τ (le « looming »), qui n'est pas
  // linéaire en distance. Et `prochain` — les secondes avant que son coup
  // parte — est un meilleur τ qu'une cinématique de lame, puisque les coups de
  // ce modèle sont instantanés.
  const ferQuiVient = (tau, deFace) => ({
    quoi: "fer qui vient", canal: "vue", deFace,
    force: sature(1 / Math.max(tau, 0.05), 8) * Math.max(0, deFace || 0),
    // SA SOUDAINETÉ EST FAIBLE, et c'est sa définition : ce qu'on voit venir ne
    // fait pas sursauter. Ça inquiète, et ça arme une parade. C'est le seul
    // stimulus dont la soudaineté ne vaille pas 1.
    soudainete: sature(1 / Math.max(tau, 0.05), 20),
  });

  // 4. LE VOISIN QUI TOMBE — vue, et ouïe par le cri. Le cri double la portée
  // sans changer la forme, et c'est le seul canal qui traverse un dos tourné.
  const voisinTombe = (d, deFace, cri) => ({
    quoi: "voisin à terre", canal: cri ? "ouie" : "vue", deFace,
    force: pres(d, M.COUDE_M) * (cri ? 1 : 0.8), soudainete: 1,
  });

  // 5. LE VOISIN QUI PART — vue. LE SEUL DONT LA FORMULE SOIT INTRINSÈQUEMENT
  // UNE DÉRIVÉE, et le plus puissant déclencheur de fuite qui existe. Ce n'est
  // pas « combien sont partis », c'est QUELLE PROPORTION VIENT DE PARTIR : trois
  // hommes qui s'en vont d'un groupe de quatre est une catastrophe, les mêmes
  // trois d'un groupe de trente n'est rien.
  //
  // C'est aussi ce qui fait la contagion : la fenêtre se rouvre à chaque départ,
  // donc une ligne se défait par propagation et non par un seuil global.
  const voisinPart = (partis, amisAvant) => {
    const f = Math.min(1, Math.max(0, partis) / Math.max(1, amisAvant));
    return { quoi: "les siens s'en vont", canal: "vue", deFace: 1,
             force: f, soudainete: f };
  };

  // 6. QUELQU'UN DANS MON DOS — ouïe. Deux substitutions honnêtes faute de
  // vitesse par homme dans le modèle : son CAP VOULU pointé sur moi vaut mieux
  // qu'une vitesse — il dit son intention —, et le vacarme se dérive de la
  // presse.
  const dansLeDos = (d, deFace, vient) => ({
    quoi: "quelqu'un derrière", canal: "ouie", deFace,
    force: Math.max(0, -deFace) * pres(d, M.IMMEDIAT_M) * Math.max(0, vient),
    soudainete: Math.max(0, vient),
  });

  // 7. LE SIGNE QUI TOMBE — vue. LE SEUL STIMULUS QUI PORTE LOIN, et il fallait
  // qu'il existe : une banniere abattue se voit d'un bout a l'autre d'une aile,
  // la ou tout le reste du repertoire tient dans les six metres du coude.
  //
  // Il vient de `CHOC_BANN` — « ce que coute la voir tomber, a TOUTE l'aile » —
  // et c'est la seule piece du modele de morale qui n'avait aucun equivalent
  // ici. La deposer sans l'ecrire aurait retire au commandement sa
  // VULNERABILITE : un etat-major qu'on ne peut plus frapper.
  //
  // Sa portee est passee en argument et non ecrite ici : ce n'est pas une
  // mesure du corps, c'est une propriete de la CHOSE qu'on regarde — une
  // banniere se voit a cent dix metres, un homme a six.
  const signeTombe = (d, portee) => ({
    quoi: "le signe tombe", canal: "vue", deFace: 1,
    // Lineaire et non en 1/(1+x²) : une banniere ne se voit pas « un peu
    // moins » de loin, elle se voit ou elle ne se voit pas, et entre les deux
    // c'est la certitude qui s'effrite, pas la taille.
    force: Math.max(0, 1 - d / (portee || 110)),
    soudainete: 1,
  });

  // ===========================================================================
  // L'HABITUATION — double processus, et c'est ce qui fait le vétéran
  // ===========================================================================
  // UN STIMULUS MODÉRÉ RÉPÉTÉ HABITUE ; UN STIMULUS VIOLENT SENSIBILISE. C'est
  // le double processus mesuré, et il donne les deux hommes qu'on veut : celui
  // qui s'endurcit au fil de la mêlée, et celui qui craque de plus en plus vite
  // après avoir failli mourir une fois.
  //
  // ET C'EST ICI QUE `vecu` ENTRE, au lieu d'être un coefficient posé à la
  // main : l'expérience EST une habituation pré-chargée. Un vétéran n'est pas
  // brave — son corps a déjà entendu tout ça.
  const SEUIL_SENSIBILISE = 0.75;
  const habituer = (h, sal, dt) => {
    const a = h == null ? 0 : h;
    if (sal <= 0) return Math.max(0, a - a * 0.02 * dt);      // ça s'oublie, lentement
    return sal < SEUIL_SENSIBILISE
      ? Math.min(1, a + (1 - a) * 1.4 * sal * dt)
      : Math.max(0, a - a * 1.4 * sal * dt);
  };

  // CE QUE LE VÉCU CHARGE D'AVANCE — et qui n'est PAS l'identité.
  //
  // Elle remplace `hab = max(0, vecu)`. Deux choses changent, et la seconde est
  // la vraie : la forme sature au lieu d'être linéaire, et surtout elle est
  // PLAFONNÉE. Un homme qui a tout vu entend encore un coup ; il l'entend moins.
  //
  // Ça ne rajoute aucun axe personnel, et c'est la condition pour que ce soit
  // cohérent : `vecu` garde ses deux emplois déjà déclarés — l'habituation ici,
  // le répertoire dans `acquis` — et l'on n'introduit surtout pas un
  // coefficient de « bravoure », qui serait la barre de morale que toute cette
  // couche est bâtie pour éviter. Le dressage agit sur `emprise`, le vécu sur la
  // saillance : deux axes, deux endroits de l'APPAREIL, aucun dans les appels.
  const prehabituer = (vecu) => M.SOURD_MAX * sature(Math.max(0, vecu || 0), 0.6);

  /** Ce qui reste d'un stimulus, tout compris. C'est elle qui arme le réflexe. */
  const saillance = (st, ctx, hab) =>
    Math.max(0, st.force) * Math.max(0, st.soudainete)
    * gain(st.canal, ctx, st.deFace) * (1 - Math.min(1, hab || 0));

  // ⚠ L'ARMEMENT N'EST PAS LA SAILLANCE — DEUX QUESTIONS, DEUX MESURES.
  //
  //   la saillance répond à « EST-CE QUE ÇA FAIT SURSAUTER ? » — c'est une
  //     question de glande, et la soudaineté y a toute sa place ;
  //   l'armement répond à « EST-CE QUE ÇA ARME UNE PARADE ? » — et ce n'en est
  //     pas une.
  //
  // Les confondre a rendu `parer` inélisible, et le fichier se contredisait
  // déjà tout seul : le commentaire de `ferQuiVient` dit à la fois que sa
  // soudaineté est faible PAR DÉFINITION (« ce qu'on voit venir ne fait pas
  // sursauter ») et que « ça arme une parade ». Les deux ne tiennent ensemble
  // que si l'armement ne passe pas par la soudaineté.
  //
  // Mesure, de jour, un fer qui part à 0,15 s : force 0,682 × soudaineté 0,322
  // = saillance 0,164, donc un appel de parade à −0,67 — battu par la garde
  // (0,126 contre 0,274). Sans la soudaineté, le même fer arme à 0,509.
  //
  // Un homme voit très bien venir le coup qu'il pare : c'est même la seule
  // façon de parer. Ce qu'il ne fait pas, c'est sursauter.
  const armement = (st, ctx, hab) =>
    Math.max(0, st.force) * gain(st.canal, ctx, st.deFace)
    * (1 - Math.min(1, hab || 0));

  // CE QU'IL RESTE D'UN STIMULUS APRÈS COUP — la décroissance du sursaut.
  // Pure : elle ne lit que deux dates et une durée, exactement comme le test de
  // latence. Un stimulus n'a donc PAS besoin d'être maintenu en vie par
  // l'appelant, et c'est délibéré : laisser `bataille2d.js` décider combien de
  // temps dure un sursaut ferait fuir un fait du modèle vers le harnais — la
  // faute même que la v2 du grégarisme a corrigée en rapatriant le calcul des
  // voisins DANS la couche, pour qu'il passe par les canaux.
  const resonne = (sal, age, quoi) =>
    sal * Math.exp(-age / (M.DECOURS[quoi] || M.DECOURS_DEFAUT));

  // ===========================================================================
  // LE REFLEXE — L'ACTIVATION DE LA COUCHE, ET RIEN D'AUTRE
  // ===========================================================================
  // IL S'EST APPELE « RÉFLEXE » PENDANT UNE JOURNEE, ET LE NOM ETAIT UN PIEGE.
  // « Réflexe » dit une emotion, donc quelque chose qui aurait un avis sur ce
  // qu'il faut faire — et de fil en aiguille on se retrouve avec une BARRE DE
  // MORALE : un seul nombre qui resume tout et qui decide tout. C'est
  // exactement ce que cette couche est batie pour eviter, puisque le geste s'y
  // elit par une competition DISTRIBUEE, un `appel x acquis` par geste.
  //
  // CE QU'IL EST VRAIMENT : de combien la couche 1 est AUX COMMANDES. Rien de
  // plus. Il ne choisit aucun geste, il n'entre dans aucun appel, et il ne doit
  // jamais y entrer. Il fait deux choses, et les deux sont des modulations de
  // l'APPAREIL, pas des entrees du choix :
  //
  //   il ferme les canaux — le tunnel visuel, la surdite de stress ;
  //   il donne la main au corps — `emprise`, sur les couches 2, 3 et 4.
  //
  // LE TEST QUI LE GARDE HONNETE : si on le retirait, qu'est-ce qui casserait ?
  // Reponse admissible : le tunnel, la surdite, l'emprise. Le jour ou la reponse
  // devient « les gestes », il a derape et il faut le remettre a sa place.
  //
  // ─────────────────────────────────────────────────────────────────────────
  // ET IL NE SE NOURRIT QUE DE CE QUI ARRIVE
  //
  // Il a eu un « plancher » calcule des signaux continus — l'integrite, l'appui,
  // le souffle, l'issue. C'etait une DUPLICATION : les appels lisent deja ces
  // memes signaux, directement et sans retard. Le plancher en refaisait une
  // copie lissee, agregee, et c'est par la que le scalaire redevenait une jauge
  // globale.
  //
  // Ce que ca produisait se mesurait : un homme intact, calme, sans rien autour,
  // portait un plancher de −0,21 — uniquement parce qu'a vingt-cinq points de
  // vie il est a 1,14 coup de la mort. Une information que les appels avaient
  // deja. Sans plancher, il est a −1 tant qu'il ne lui arrive rien, et c'est ce
  // qu'on veut dire par « calme ».
  //
  // Restent DEUX sources, et elles ont en commun de dire « il se passe quelque
  // chose », jamais « ou j'en suis » :
  //
  //   LES PICS — la saillance du stimulus le plus fort de ce battement ;
  //   LA CONTAGION — l'alarme que les autres MONTRENT. C'est le seul signal
  //     continu qui parle d'eveil et non de situation, et il a sa place ici :
  //     la panique se prend au niveau de l'activation, pas seulement du choix.
  const activer = (reflexe, cible, dt, fond, apaise) => {
    const a = reflexe == null ? -1 : reflexe;
    // ET LA DESCENTE EST PERSONNELLE. C'est ce que `humeur: "versatile"` disait
    // dans la bataille — « il rompt TÔT et se reprend VITE ; Tam reflue de
    // cinquante pas et revient, trois fois ». La reprise n'est pas du courage :
    // c'est la vitesse à laquelle une décharge retombe, et elle suit le FOND,
    // comme le souffle. Celui qui en a se vide moins vite et se refait plus
    // vite — un seul chiffre, deux effets opposés, comme dans un corps.
    //
    // La MONTÉE, elle, ne se négocie pas : une glande est une glande, et
    // personne n'a d'adrénaline lente.
    // Deux constantes de temps : on s'alarme en quelques secondes, on se calme
    // en une minute. L'asymetrie est le fait, pas les valeurs.
    const f = fond == null ? 1 : Math.max(0.4, Math.min(1.8, fond));
    // ET IL Y A UNE SECONDE MOITIE, QUI NE VIENT PAS DE LUI. `fond` est ce
    // qu'un homme a DANS le ventre ; `apaise` est ce qu'il a SOUS LES YEUX —
    // sa banniere encore debout, son chef a portee de voix. Meme effet, deux
    // sources, et il fallait les deux : sans la seconde, la depose de `morale`
    // retirerait au commandement le seul moyen qu'il ait de PROTEGER ses
    // hommes au lieu de les deplacer.
    //
    // ⚠ CE N'EST PAS UN PLANCHER, et c'est la seule chose a verifier ici. Ca
    // ne touche PAS la cible : un homme sous sa banniere a exactement aussi
    // peur qu'un autre du meme coup. Il s'en remet plus vite, c'est tout —
    // c'est une constante de temps, donc l'appareil, et non un terme ajoute a
    // ce qu'il ressent. `TIENT_BANN` disait deja exactement cela : il
    // multipliait la REPRISE de la morale, jamais son niveau.
    // ⚠ ON SATURE, ON N'ECRETE PAS — et la premiere version de cette ligne
    // etait un `Math.min(4, …)`, c'est-a-dire precisement la faute que le
    // README nomme. Mesure : sous sa banniere ET avec son chef a quinze
    // metres, un homme se calmait exactement aussi vite qu'avec le chef seul.
    // La banniere ne servait a rien des qu'un chef etait la, non pas parce que
    // le modele le dit, mais parce que la borne avait mange le produit.
    //
    // L'asymptote est le fait a defendre, pas le plafond : quoi qu'un homme
    // ait sous les yeux, une glande ne se vide pas instantanement. Six fois
    // plus vite au maximum — quarante-cinq secondes qui deviennent sept ou
    // huit — et l'on s'en approche sans jamais y toucher.
    const ap = 1 + M.APAISE_MAX * sature((Math.max(1, apaise || 1) - 1) / M.APAISE_MAX, 1);
    const tau = cible > a ? M.MONTEE_S : M.DESCENTE_S / (f * ap);
    return a + (cible - a) * (1 - Math.exp(-dt / tau));
  };

  // ===========================================================================
  // L'EMPRISE — de combien cette couche couvre les trois autres
  // ===========================================================================
  // LA PIÈCE MAÎTRESSE DE TOUTE LA PILE, et elle tient en une ligne. Ce n'est
  // pas une règle de priorité : c'est la désinhibition du réflexe sous stress.
  // À réflexe basse, le corps propose et la réflexion dispose ; à réflexe haute,
  // le corps agit et la réflexion regarde.
  //
  // ET LE DRESSAGE LA REPOUSSE — c'est à cela qu'il sert vraiment. Un vétéran
  // garde sa tête plus longtemps sous la même peur, non parce qu'il a moins peur
  // (il en a autant), mais parce qu'il lui en faut davantage pour que la main
  // lui échappe.
  const emprise = (reflexe, c) => {
    const a = reflexe == null ? -1 : reflexe;
    const d = c && c.dressage != null ? c.dressage : 0;
    return Math.min(1, Math.max(0, sature(((a + 1) / 2) * (1 - 0.45 * d), 0.55)));
  };

  // ===========================================================================
  // LES ACQUIS — ce que le dressage enseigne, ET CE QU'IL DÉSAPPREND
  // ===========================================================================
  // Ce qu'on apprend à l'exercice, ce sont exactement les gestes qui vont CONTRE
  // le corps : rester serré quand tout pousse à s'ouvrir, frapper ce qui vient
  // au lieu de reculer d'un pas. Un corps non dressé n'est pas vide : c'est un
  // corps qui a très bien appris autre chose — se dérober et courir sont
  // d'excellents réflexes, appris pour une autre situation que celle-ci.
  const JAMBES = ["planté", "serrer", "recul", "dérobade", "fuite", "ruée", "sidération"];
  const BRAS   = ["garde", "frapper", "parer", "ballants"];

  const acquis = (c) => {
    const d = c.dressage == null ? 0 : c.dressage;
    // Le sang versé enseigne ce que l'exercice ne peut pas. On le compte à part
    // parce qu'un vétéran mal dressé existe, et un conscrit bien dressé aussi.
    const v = c.vecu == null ? 0 : c.vecu;
    return {
      // ⚠ RESTER PLANTE NE S'APPREND PAS, et lui donner le meilleur acquis
      // du tableau (0,67 pour un garde) etait la faute. Il gagnait alors par
      // la porte de derriere : mesure sur la bataille, 93 % des hommes AU
      // CONTACT etaient plantes. Or un homme a portee de bras frappe, se
      // resserre, cede le pas ou s'efface — tenir sans rien faire est
      // l'EXCEPTION, pas le repos.
      //
      // Ce que le dressage enseigne, c'est tout le reste. Son acquis est
      // donc PLAT, comme celui de la sideration : ni l'un ni l'autre ne se
      // drille, et les deux ne sont que ce qui reste quand rien d'appris ne
      // sort. Un peu de vecu quand meme — un vieux sait attendre, et c'est
      // la seule chose vraie qu'on puisse dire de l'immobilite.
      "planté":     sature(0.15 + 0.25 * v, 1),
      "recul":      sature(0.5 * d + 0.6 * v + 0.3, 1),
      // LE GESTE LE PLUS DRILLE QUI SOIT, et le plus contre-nature : refermer le
      // trou, c'est marcher vers l'endroit ou l'on vient de voir tomber
      // quelqu'un. Un homme de rang le fait sans y penser ; un gueux ne l'a
      // jamais appris et s'ecarte au contraire. D'ou le poids du dressage, le
      // plus fort du tableau, et un vecu qui compte peu : ca s'apprend a
      // l'exercice, pas au sang.
      "serrer":     sature(1.1 * d + 0.3 * v, 1),
      "dérobade":   sature(-0.2 * d + 0.7 * v + 0.5, 1),
      "fuite":      sature(-0.9 * d - 0.3 * v + 0.4, 1),
      "ruée":       sature(-0.3 * d - 0.4 * v + 0.1, 1),
      // ON N'APPREND JAMAIS À SE FIGER. Seul acquis qui ne dépende pas du
      // dressage : l'exercice ne protège pas de la sidération, seule la bataille
      // le fait. C'est pourquoi elle frappe les recrues dès le premier jour et
      // épargne les vieux — et pourquoi un conscrit très bien dressé mais qui
      // n'a jamais vu de sang s'y expose autant qu'un gueux.
      "sidération": sature(-0.9 * v + 0.2, 1),
      "garde":      sature(0.8 * d + 0.5 * v + 0.3, 1),
      "frapper":    sature(0.6 * d + 0.8 * v + 0.1, 1),
      "parer":      sature(0.7 * d + 0.6 * v, 1),
      // ET LAISSER TOMBER LES BRAS NE S'APPREND PAS NON PLUS. Ce n'est pas
      // un geste, c'est la DEFAILLANCE de la garde — donc un acquis
      // toujours negatif, que le dressage et le sang ne font qu'enfoncer.
      // Personne ne le fait « bien » ; certains le font seulement plus tard.
      "ballants":   sature(-0.5 - 0.7 * d - 0.5 * v, 1),
    };
  };

  // ===========================================================================
  // LES APPELS — ce que la situation réclame, pour tous les corps pareil
  // ===========================================================================
  // L'IMITATION — le corps copie le voisin sans l'avoir decide, et c'est la
  // troisieme famille du gregarisme apres la couverture et la contagion. Elle
  // ne remplace aucun appel : elle les DEPLACE, d'un tiers au plus. Un geste que
  // personne ne fait garde son appel propre ; un geste que tout le rang fait
  // gagne assez pour emporter un homme qui hesitait — ce qui est exactement ce
  // qu'on voulait : la ligne qui avance ensemble, qui se fige ensemble, et qui
  // rompt ensemble sans qu'aucune ligne de code ne l'organise.
  const IMITE = 0.33;

  const appels = (s, top) => {
    const im = (g, v) => v + IMITE * (1 - Math.abs(v)) *
                         (((s.imitation && s.imitation[g]) || 0) * 2 - 1);
    // ⚠ UN GESTE BREF S'ARME SUR SON PROPRE STIMULUS, PAS SUR LE PLUS FORT.
    //
    // Ces trois appels lisaient `top.quoi` — c'est-à-dire « mon stimulus
    // était-il le plus bruyant du battement ? ». La faute était invisible tant
    // que `ferQuiVient` n'était pas émis ; elle est sortie à la minute où on
    // l'a branché sur la vraie bataille.
    //
    // Mesure : de nuit, un fer qui part à deux dixièmes rend une saillance de
    // 0,04 — la vue tombe à un tiers, et sa SOUDAINETÉ vaut 0,25 par
    // définition (ce qu'on voit venir ne fait pas sursauter). N'importe quel
    // contact le couvre. `parer` ne pouvait donc JAMAIS être élu : son appel
    // valait −1 en permanence, et l'on aurait pu retirer le geste du fichier
    // sans que rien ne change.
    //
    // C'est la même erreur de forme que la latence-filtre : un `max` posé là où
    // il fallait une adresse. On garde donc les saillances PAR STIMULUS, et
    // chaque geste bref va chercher la sienne. Le `top` reste ce qu'il est —
    // ce qui tient l'homme —, mais il ne sert plus qu'à la glande.
    const de = (quoi) => (top && top.par && top.par[quoi]) || 0;
    return {
      // Appelé par l'ABSENCE de menace — c'est le seul geste dont l'appel soit
      // une négation, et c'est ce qui en fait le repos.
      "planté":     im("planté", -Math.max(-1, s.menace)),
      "recul":      im("recul", melange([[s.menace, 1], [-s.appui, 0.8], [-s.integrite, 0.6]])),
      // Appele par le TROU et non par le nombre : c'est le coude qu'on ne sent
      // plus qui declenche, et le pourtour ouvert qui l'entretient. Sans menace
      // du tout on ne se resserre pas — on se resserre CONTRE quelque chose.
      "serrer":     im("serrer", melange([[-s.coude, 1.2], [-s.appui, 1], [s.menace, 0.8]])),
      // Le seul geste armé par un ÉVÉNEMENT et par lui seul : il répond à un
      // coup, pas à une situation.
      "dérobade":   Math.max(de("coup frôlé"), de("coup reçu")) * 2 - 1,
      // Appelée par la contagion d'abord, la menace ensuite — et IMPOSSIBLE sans
      // issue. On multiplie au lieu de moyenner : être acculé ne rend pas la
      // fuite moins souhaitable, il la rend irréalisable. Une moyenne aurait
      // laissé un homme au pied d'un mur courir à moitié.
      "fuite":      ((melange([[de("les siens s'en vont") * 2 - 1, 1.2],
                               [s.menace, 1], [-s.appui, 0.8]]) + 1)
                     * (s.issue + 1) / 2) - 1,
      "ruée":       im("ruée", melange([[s.menace, 1], [-s.issue, 1], [s.souffle, 0.8]])),
      // SE FIGER N'EST APPELÉ PAR RIEN DE PROPRE : il n'a pas de déclencheur. Il
      // gagne quand les cinq autres sont faibles, ce qui EST sa définition.
      //
      // ⚠ ET LA LIGNE DISAIT L'INVERSE DE CE COMMENTAIRE. Elle lisait `menace`,
      // c'est-à-dire LE SIGNAL LE PLUS FORT DU MODÈLE : un homme au contact
      // maximal portait donc un appel de sidération à +1,00 en permanence. Ce
      // n'était pas « ce qui reste quand rien ne sort », c'était le favori.
      //
      // Mesure, au fer, débordé, entamé, dos dégagé — le pire cas ordinaire :
      // sidération 0,754 contre fuite 0,486 et recul 0,415. Les hommes ne
      // fuyaient pas parce qu'ils se figeaient, et la dépose de `morale` l'a
      // rendu visible d'un coup : zéro fuyard sur six cents secondes et
      // quatre-vingt-quinze morts.
      //
      // ZÉRO N'EST PAS UNE CONSTANTE RÉGLÉE, c'est le point neutre de
      // l'échelle : ni appelé, ni repoussé. C'est la seule écriture qui dise
      // « pas de déclencheur » sans en inventer un.
      //
      // ET LE MÉCANISME QU'ON VOULAIT EST INTACT, c'est même le test : un
      // conscrit acculé, dont la fuite est annulée par `issue` et le recul
      // interdit par la presse, se fige toujours — parce que les autres sont à
      // zéro, pas parce qu'on l'a poussé. C'est l'écrasement de foule, et il
      // sort du modèle au lieu d'une branche.
      //
      // L'imitation reste : on se fige aussi parce que le rang se fige.
      "sidération": im("sidération", 0),
      // ⚠ LA GARDE EST LE REPOS DES BRAS, comme `planté` est celui des jambes,
      // et elle etait appelee par la seule menace — donc a −1 des qu'aucun
      // ennemi n'etait proche. Un homme EN MARCHE, loin de tout, avait donc un
      // appel de garde negatif et un appel de `ballants` legerement positif :
      // il laissait tomber les bras. Mesure sur la bataille : six cents hommes
      // en `ballants`, y compris ceux qui n'avaient encore vu personne.
      //
      // Un homme en armes TIENT SON ARME. C'est l'etat par defaut d'un corps
      // qui en porte une, menace ou pas, et la menace ne fait que le renforcer.
      "garde":      im("garde", melange([[0.5, 1], [s.menace, 1]])),
      "frapper":    s.aPortee ? im("frapper", s.menace) : -1,
      "parer":      de("fer qui vient") * 2 - 1,
      // ET `ballants` DEMANDE QUE TOUT AILLE MAL A LA FOIS. En moyenne, il
      // suffisait qu'un seul des trois termes soit defavorable pour qu'il
      // passe devant une garde a −1. En PRODUIT, un homme qui a encore du
      // souffle OU de la carcasse garde son arme — c'est la meme lecon que
      // l'issue et la fuite : ce qui doit etre conjoint ne se moyenne pas.
      "ballants":   2 * Math.max(0, (-s.souffle + 1) / 2)
                      * Math.max(0, (-s.integrite + 1) / 2) - 1,
    };
  };

  // ===========================================================================
  // LE GRAPHE — ce que l'élection a le droit de produire
  // ===========================================================================
  // LES ARÊTES INTERDITES SONT LES VRAIES AFFIRMATIONS DU MODÈLE, et les moins
  // chères à vérifier : aucune n'est une question de calibration. Si l'une
  // apparaît dans les logs, c'est le modèle qui est faux — pas le réglage.
  const INTERDIT_JAMBES = {
    // On ne décroche pas depuis une fuite : il faut repasser par planté. Une
    // fois le dos tourné, on ne se ravise que si tout retombe.
    "fuite":      new Set(["recul", "ruée", "dérobade", "serrer"]),
    // Un homme sidéré ne se dérobe pas — c'est la définition de la sidération.
    "sidération": new Set(["dérobade", "ruée", "serrer"]),
    // On ne freine pas une charge : on la finit ou on fuit.
    "ruée":       new Set(["recul"]),
  };
  const INTERDIT_BRAS = {
    // On ne repasse jamais du bras mort au coup porté sans repasser par la garde.
    "ballants": new Set(["frapper", "parer"]),
  };

  // ===========================================================================
  // LA PORTE (c) : LA DYSRÉGULATION — quels gestes exigent que le corps AIT LA MAIN
  // ===========================================================================
  // LE FICHIER SE CONTREDISAIT ICI, ET IL FAUT DIRE COMMENT ON TRANCHE.
  //
  //   Le réflexe déclare : « il n'entre dans aucun appel, et il ne doit jamais y
  //   entrer » — sinon il redevient la barre de morale, un scalaire qui résume
  //   tout et décide tout.
  //   Le relevé du banc déclare l'inverse : « les appels court-circuitent la
  //   glande », puisqu'ils lisent `menace`, instantané, au lieu de ce que le
  //   corps RESSENT.
  //
  // La mesure départage, et elle dit quelque chose de plus precis que les deux :
  // le conscrit rompt a 0,0 s, sans un stimulus, **avec `emprise` a 0,00**. Un
  // geste de corps elu pendant que le corps ne tient rien du volant.
  //
  // Le fautif n'etait donc pas que les appels ignorent la glande. C'est
  // qu'`emprise` SORT de la couche vers les trois autres et n'agit JAMAIS a
  // l'interieur d'elle-meme. On l'applique ou elle manquait, et l'on n'ajoute
  // aucun terme aux appels : le reflexe ne choisit toujours rien, il decide
  // seulement de combien le repertoire du corps a le droit de s'exprimer.
  //
  // CE QUI JUSTIFIE LA LISTE, ET ELLE EST COURTE. Fuir, se figer, se ruer sont
  // les trois gestes dont le NOM MEME est « le corps a pris la main ». Un homme
  // calme, meme mal dresse, ne part pas en courant : il reste plante, mal a
  // l'aise. Les autres ne sont pas ici — tenir, se resserrer, garder, frapper,
  // parer, rompre d'un pas sont des gestes qu'on fait tres bien de sang-froid,
  // et la derobade est une adresse avant d'etre une panique.
  //
  // `ballants` n'y est pas non plus, et c'est le cas limite qui montre la
  // regle : il a un moteur qui n'est PAS la peur — l'epuisement. Un homme a
  // bout laisse tomber les bras en toute lucidite, et le lui interdire serait
  // faire dire a l'emprise autre chose que ce qu'elle dit.
  //
  // La ruee est a 0,7 et non a 1 : on charge aussi sur ordre, et de sang-froid.
  const SOUS_EMPRISE = { "fuite": 1, "sidération": 1, "ruée": 0.7 };
  const dysregule = (geste, empr) => {
    const b = SOUS_EMPRISE[geste];
    return b == null ? 1 : (1 - b) + b * Math.max(0, Math.min(1, empr));
  };

  // PORTE (b) : L'EXÉCUTION. Il reçoit le stimulus et ne peut pas répondre —
  // ce qui n'est pas la même chose que ne pas vouloir.
  //
  // C'EST ICI QUE LA PRESSE FABRIQUE LA SIDÉRATION, et c'est physiquement vrai :
  // ni dérobade ni recul possibles, les deux issues du corps fermées, il ne
  // reste que se figer. C'est le mécanisme des écrasements de foule, et il
  // explique une chose qu'on voit sur tous les champs sans savoir la modéliser.
  const possible = (geste, s, ctx) => {
    const serre = (ctx.presse || 0) >= M.COUDES_BLOQUANTS;
    if (geste === "dérobade") return !serre;
    if (geste === "recul")    return !serre && s.issue > -0.9;
    if (geste === "fuite")    return s.issue > -0.9 && s.souffle > -0.9;
    if (geste === "ruée")     return s.souffle > -0.5 && ctx.bras !== "ballants";
    return true;
  };

  // LES COUPLAGES ENTRE PISTES — ce qu'une machine unique ne peut pas donner.
  const coupler = (jambes, bras) => {
    // On ne frappe pas en courant le dos tourné.
    if (jambes === "fuite" && (bras === "frapper" || bras === "parer")) return "garde";
    // La ruée force le bras : c'est même tout ce qu'elle est.
    if (jambes === "ruée") return "frapper";
    return bras;
  };

  // ===========================================================================
  // UN BATTEMENT
  // ===========================================================================
  /**
   * @param c  le corps — { dressage, vecu } + l'état de la couche, muté ici
   * @param p  ce qu'il perçoit — { t, dt, stimuli[], signaux, nuit, presse }
   * @param u  un tirage dans [0,1[ — injecté, pour rester reproductible
   */
  function pas(c, p, u) {
    const dt = p.dt, s = p.signaux;
    if (c.reflexe == null) {
      c.reflexe = -1;
      // L'expérience est une habituation pré-chargée : c'est tout ce que `vecu`
      // veut dire, et il n'a pas besoin d'un coefficient de plus. Elle passe par
      // `prehabituer` et non plus par l'identité — voir là-bas pourquoi.
      const v = prehabituer(c.vecu);
      c.hab = { tact: v, ouie: v, vue: v };
      // Ce qui résonne encore, par canal. C'est de l'état, et le README l'admet
      // nommément : ce qui se souvient est un état explicite, pas un champ posé
      // au passage.
      c.echo = { tact: null, ouie: null, vue: null };
      // Ce qui est parti et n'est pas encore arrivé. La ligne à retard.
      c.attente = [];
      c.jambes = "planté"; c.bras = "garde";
      c.jusqua = 0; c.jusquaBras = 0; c.retour = null;
    }
    const ctx = {
      reflexe: c.reflexe, nuit: p.nuit, presse: p.presse, bras: c.bras,
      sourd: c.sourd || 0,
      vacarme: vacarme(p.presse, s.ennemisProches),
    };

    // --- 0. le troupeau, et il se calcule ICI ------------------------------
    // Il lui faut le CONTEXTE — la nuit, le vacarme, la surdité —, et le
    // contexte n'existe qu'ici. La v1 le calculait chez l'appelant, donc hors
    // des canaux : un homme sentait ses voisins à travers l'obscurité. Ce qui
    // vient du dehors doit entrer par une oreille ou par un œil, sans exception.
    if (p.voisins) {
      const sg = signes(p.voisins, ctx);
      s.imitation = sg.imitation;
      // ---- LA CONTAGION EST UNE DERIVEE, ET IL A FALLU SIX CENTS HOMMES
      // POUR LE VOIR. En boucle fermee sur une vraie bataille, elle
      // s'auto-alimentait : chacun lit ses voisins, `ballants` vaut +0,9, donc
      // un homme qui baisse les bras fait baisser les bras a ses voisins, qui
      // le lui renvoient. Mesure : reflexe moyen de −0,98 a +0,51 en dix
      // secondes, emprise calee a 0,81, et six cents hommes en `ballants`.
      // Rien n'amortissait — la descente en 45 s ne pouvait rien contre six
      // cents sources mutuelles qui montent en 3 s.
      //
      // CE QUI MANQUAIT N'ETAIT PAS UN REGLAGE, C'ETAIT UN MECANISME : on
      // s'habitue a la peur des autres. Une ligne uniformement tendue ne
      // transmet plus rien, parce qu'un etat STEADY ne porte aucune
      // information — exactement comme « les siens s'en vont », qui n'a jamais
      // ete un compte mais une PROPORTION QUI VIENT DE PARTIR.
      //
      // On garde donc un niveau ambiant qui s'adapte en quelques secondes, et
      // l'on ne prend que ce qui le DEPASSE. Tout le monde tendu depuis une
      // minute : rien ne passe. Un seul homme qui craque a l'instant : tout
      // passe. C'est le meme double processus que l'habituation des canaux,
      // applique au troupeau — et c'est ce qui borne la boucle sans la
      // couper.
      const brut = sg.contagion;
      c.social = c.social == null ? brut
        : c.social + (brut - c.social) * (1 - Math.exp(-dt / M.AMBIANT_S));
      // L'APAISEMENT MULTIPLIE LE SURSAUT, il ne le décale pas : sous une
      // bannière debout, ce qui passe des autres passe moins fort — et ce
      // n'est pas la même chose que d'avoir moins peur soi-même.
      s.contagion = Math.max(-1, Math.min(1,
        2 * Math.max(0, (brut - c.social) / M.SURSAUT_SOCIAL) * sg.apaise - 1));
      s.appui = couverture(p.voisins);
      s.coude = coude(p.voisins);
      // LES DEUX SORTIES POSTURALES. Elles ne participent a AUCUNE election :
      // ce ne sont pas des gestes, ce sont des DIRECTIONS que le corps donne au
      // geste elu. `ouverture` dit par ou refermer quand on se resserre ;
      // `alignement` dit vers ou se tourner quand on ne fait rien d'autre.
      // Les melanger aux appels serait la faute de composition la plus facile :
      // « ou aller » n'est pas « quoi faire ».
      s.ouverture = ouverture(p.voisins);
      s.alignement = alignement(p.voisins, ctx);
    }

    // --- 1. les stimuli perçus, latence comprise ---------------------------
    // Un stimulus émis à `t` n'est perçu qu'à `t + latence(canal)`. C'est ce qui
    // fait que le toucher gagne toujours contre la vue, sans règle de priorité.
    //
    // ⚠ DEUX SORTIES, ET LA SÉPARATION EST TOUTE LA CORRECTION DU DÉCOURS.
    //
    //   `frais` — le stimulus de CE battement. Il arme les gestes brefs, et eux
    //     seuls : la dérobade et la parade répondent au coup qui arrive, jamais
    //     à celui d'il y a deux secondes. Leur donner l'écho ferait un homme qui
    //     se dérobe pendant toute la durée du décours — un `SEJOUR` de 0,2 s
    //     rejoué en boucle, c'est-à-dire l'inverse d'une impulsion.
    //   `echo` — ce qui RÉSONNE, et qui ne nourrit que la glande.
    //
    // C'est la ligne de partage que le fichier tient déjà partout ailleurs :
    // le réflexe est l'APPAREIL, les appels sont le CHOIX. Le décours appartient
    // au premier et n'a rien à faire dans le second.
    //
    // ⚠⚠ LA LATENCE ÉTAIT UN FILTRE, ET ELLE DEVAIT ÊTRE UNE LIGNE À RETARD.
    // C'EST LA PLUS GROSSE FAUTE QU'AIT PORTÉE CE FICHIER, et elle était muette.
    //
    // Le test comparait l'instant d'émission à ce même instant plus la latence.
    // Un stimulus émis à `t` était donc TOUJOURS rejeté à `t` — et comme
    // l'appelant le pousse une fois puis vide sa boîte, il n'était jamais
    // représenté. Conséquence : **aucun stimulus n'a jamais atteint le réflexe**,
    // dans aucune mesure de ce banc, depuis l'écriture du fichier.
    //
    // Tout ce qu'on croyait mesurer en découlait. Le réflexe collé à −1 quoi
    // qu'il arrive ; « un homme au contact meurt avant d'avoir peur », qu'on a
    // mis sur le compte du modèle de dégâts ; le conscrit qui déroute à 0,0 s,
    // qui ne venait pas d'un stimulus mais de `couverture` seule. Trois
    // conclusions de conception tirées d'une tuyauterie percée.
    //
    // La correction est de faire ce que le commentaire disait déjà : un
    // stimulus ATTEND. Il entre dans une file et n'en sort qu'à l'heure de sa
    // perception. Et ça tient dans la couche, pas chez l'appelant — pour la même
    // raison que l'écho et que les voisins de la v2 : le harnais n'a pas à
    // savoir combien de temps un son met à monter jusqu'à une oreille.
    //
    // La latence et le décours sont désormais les deux bouts d'un seul objet :
    // quand le stimulus commence à compter, quand il cesse.
    for (const st of (p.stimuli || [])) c.attente.push(st);

    let frais = null;
    const touches = new Set();
    const restants = [];
    for (const st of c.attente) {
      if (p.t + 1e-9 < (st.t || 0) + LATENCE[st.canal]) { restants.push(st); continue; }
      // L'accoutumance D'AVANT ce stimulus : les deux mesures doivent lire la
      // meme, sinon l'armement paie une habituation que le stimulus vient de
      // creer lui-meme.
      const habAvant = c.hab[st.canal];
      const sal = saillance(st, ctx, habAvant);
      c.hab[st.canal] = habituer(habAvant, sal, dt);
      touches.add(st.canal);
      // `par` : la saillance de CHAQUE stimulus de ce battement, a son nom. Le
      // `max` reste pour la glande ; les gestes brefs, eux, vont chercher le
      // leur. Voir la note dans `appels`.
      if (!frais) frais = { quoi: st.quoi, saillance: sal, canal: st.canal, par: {} };
      // `par` porte l'ARMEMENT, pas la saillance : ce qui arme un geste bref
      // n'est pas ce qui fait sursauter. Voir `armement`.
      frais.par[st.quoi] = Math.max(frais.par[st.quoi] || 0,
                                    armement(st, ctx, habAvant));
      if (sal > frais.saillance)
        { frais.quoi = st.quoi; frais.saillance = sal; frais.canal = st.canal; }
      // L'écho ne garde qu'un stimulus par canal : le plus fort de ceux qui
      // sonnent encore. On ne les somme pas — deux coups ne font pas deux fois
      // peur, c'est le plus violent qui tient l'homme.
      const e = c.echo[st.canal];
      const vif = e ? resonne(e.saillance, p.t - e.t, e.quoi) : 0;
      if (sal >= vif) c.echo[st.canal] = { quoi: st.quoi, saillance: sal, t: p.t };
    }
    c.attente = restants;
    // L'HABITUATION NE SE NOURRIT PAS DE L'ÉCHO, et c'est délibéré : on
    // s'habitue à ce qui ARRIVE, pas à ce qui traîne. Un canal dont l'écho
    // sonne encore mais où rien de neuf n'est arrivé se désaccoutume comme les
    // autres — sinon un seul coup suffirait à rendre un homme sourd pour trois
    // secondes, ce qui est exactement le défaut qu'on vient de corriger.
    for (const canal of ["tact", "ouie", "vue"])
      if (!touches.has(canal)) c.hab[canal] = habituer(c.hab[canal], 0, dt);

    let top = null;
    for (const canal of ["tact", "ouie", "vue"]) {
      const e = c.echo[canal];
      if (!e) continue;
      const sal = resonne(e.saillance, p.t - e.t, e.quoi);
      if (sal < 1e-3) { c.echo[canal] = null; continue; }
      if (!top || sal > top.saillance) top = { quoi: e.quoi, saillance: sal, canal };
    }

    // --- 2. le réflexe : de combien le corps prend la main ------------------
    // Les pics et la contagion, et rien d'autre. Pas de plancher : ce que les
    // appels savent déjà lire n'a pas à être recopié ici.
    //
    // LE DÉCOURS N'EST PAS UN PLANCHER DÉGUISÉ, et c'est le contrôle qui le
    // garde honnête : il ne lit AUCUN signal continu — ni l'intégrité, ni
    // l'appui, ni le souffle, ni l'issue — donc il ne peut pas refaire le
    // plancher retiré plus haut. Sans stimulus, l'écho est vide et la cible
    // retombe à −1. Le test A3 (« au repos, rien ne se déclenche ») est la
    // garde : s'il casse, c'est qu'un plancher est revenu par cette porte.
    const cible = Math.max(top ? top.saillance * 2 - 1 : -1,
                           s.contagion == null ? -1 : s.contagion);
    c.reflexe = activer(c.reflexe, cible, dt, c.fond, p.apaise);

    // --- 3. l'élection, piste par piste ------------------------------------
    // `frais`, PAS `top` : les gestes brefs répondent au coup de ce battement.
    // Voir la note des deux sorties à l'étape 1 — c'est la moitié de la
    // correction du décours, et c'est celle qui se voit le moins.
    const ap = appels(s, frais), ac = acquis(c);
    // DE COMBIEN LE CORPS TIENT LE VOLANT — et il le tient d'abord sur SES
    // PROPRES gestes. C'est le même nombre qu'on rend aux couches 2, 3 et 4 ;
    // il n'y a pas deux emprises, il y en avait une qui ne s'appliquait qu'au
    // dehors. Voir `SOUS_EMPRISE`.
    const empr = emprise(c.reflexe, c);
    const elire = (liste, courant, interdits) => {
      // LES DEUX MOITIÉS REVIENNENT SUR [0, 1] AVANT DE SE MULTIPLIER, et ce
      // n'est pas un détail d'échelle : sur [−1, 1], deux négatifs donneraient
      // un fort positif, donc un geste ni appelé ni appris sortirait vainqueur.
      // On aurait vu des hommes courir parce qu'ils ne savent pas courir.
      let quoi = courant, fort = -1;
      const table = {};
      for (const g of liste) {
        const v = ((ap[g] + 1) / 2) * ((ac[g] + 1) / 2) * dysregule(g, empr);
        table[g] = v;
        if (interdits[courant] && interdits[courant].has(g)) continue;
        if (liste === JAMBES && !possible(g, s, ctx)) continue;
        if (v > fort) { fort = v; quoi = g; }
      }
      return { quoi, fort, table };
    };

    // --- 4. le séjour : un geste dure, donc il ne bégaie pas ---------------
    if (p.t >= c.jusqua) {
      const e = elire(JAMBES, c.jambes, INTERDIT_JAMBES);
      if (e.quoi !== c.jambes) {
        // LA DÉROBADE N'EST PAS UN ÉTAT, C'EST UNE IMPULSION : elle interrompt,
        // elle dure trois dixièmes, et l'on revient d'où l'on venait.
        c.retour = e.quoi === "dérobade" ? c.jambes : null;
        c.jambes = e.quoi;
        const sj = M.SEJOUR[c.jambes];
        c.jusqua = p.t + logUnif(sj[0], sj[1], u);
      } else if (c.retour) {
        c.jambes = c.retour; c.retour = null; c.jusqua = p.t;
      }
      c.table = e.table;
    }
    if (p.t >= c.jusquaBras) {
      const eb = elire(BRAS, c.bras, INTERDIT_BRAS);
      if (eb.quoi !== c.bras) {
        c.bras = eb.quoi;
        const sj = M.SEJOUR_BRAS[c.bras];
        c.jusquaBras = p.t + (sj ? logUnif(sj[0], sj[1], u) : 0);
      }
      c.tableBras = eb.table;
    }
    c.bras = coupler(c.jambes, c.bras);

    return {
      jambes: c.jambes, bras: c.bras, reflexe: c.reflexe,
      emprise: empr,
      // Ou le corps veut se porter, et ou il veut faire face. Le premier ne
      // sert que pendant `serrer`, le second tout le temps.
      ouverture: s.ouverture, alignement: s.alignement,
      // On rend l'ÉCHO et non le frais : c'est lui qui explique le réflexe
      // qu'on rend juste au-dessus, et un relevé doit dire ce qui tient l'homme,
      // pas seulement ce qui vient de le toucher.
      saillant: top ? top.quoi : null, saillance: top ? top.saillance : 0,
      frais: frais ? frais.quoi : null,
      phrase: phrase(c.jambes, c.bras),
    };
  }

  // ===========================================================================
  // LA TRADUCTION — c'est elle qui part dans les logs
  // ===========================================================================
  // Ce que cette couche produit se pousse en `geste` et en `recit`, JAMAIS en
  // `replique` : ce n'est pas de la parole, c'est un corps qui agit, et la Règle
  // Zéro ne s'y applique pas.
  //
  // ET C'EST AUSSI UN TEST DE CONCEPTION : un comportement qui ne se raconte pas
  // distinctement d'un autre ne mérite pas d'exister. Deux cases qui porteraient
  // la même phrase sont deux états à fusionner.
  const PHRASES = {
    "planté|garde":        "Il tient. Le poids sur les deux pieds, la pointe basse, il regarde venir.",
    "planté|frapper":      "Il travaille — il frappe à intervalles réguliers, comme on fend du bois.",
    "planté|parer":        "Il ne cède pas d'un pouce et prend le coup sur le fer.",
    "planté|ballants":     "Il est planté là, les bras tombés, et il ne se défend plus.",
    "serrer|garde":        "Il se referme d'un pas sur son voisin, l'épaule cherchant l'épaule.",
    "serrer|frapper":      "Il rentre dans le rang sans cesser de frapper devant lui.",
    "serrer|parer":        "Il se resserre en tenant le fer en travers.",
    "serrer|ballants":     "Il se rapproche des siens sans plus rien tenir devant lui.",
    "recul|frapper":       "Il cède le terrain sans cesser de se battre — un pas, un coup, un pas.",
    "recul|garde":         "Il décroche proprement, le fer en travers, sans leur donner le dos.",
    "recul|parer":         "Il rompt d'un pas en opposant le fer.",
    "recul|ballants":      "Il recule, et ses bras sont retombés. Il tient encore son épée ; il ne s'en sert plus.",
    "dérobade|parer":      "Le fer passe où il était. Il n'a pas décidé de bouger.",
    "dérobade|garde":      "Il se dérobe d'un quart de tour, l'arme haute.",
    "dérobade|frapper":    "Il s'efface et frappe dans le même geste.",
    "dérobade|ballants":   "Il s'écarte du coup sans rien lui opposer.",
    "fuite|garde":         "Il s'en va vite, et il s'en va en ordre — de trois quarts, l'arme du bon côté.",
    "fuite|ballants":      "La déroute. Il court, il a lâché son bouclier, il ne regarde plus derrière.",
    "ruée|frapper":        "Il part en avant, seul. Personne ne l'a suivi et il ne s'en est pas aperçu.",
    "sidération|garde":    "Il est planté, l'arme levée, et il ne fait rien. On lui parle, il n'entend pas.",
    "sidération|frapper":  "Il frappe dans le vide, au même rythme, sans viser personne.",
    "sidération|parer":    "Il tient le fer en travers et ne bouge plus du tout.",
    "sidération|ballants": "Il ne bouge plus du tout. Il est encore debout et c'est tout ce qu'on peut en dire.",
  };
  const phrase = (j, b) => PHRASES[j + "|" + b] || (j + " · " + b);

  // ===========================================================================
  const API = { M, sature, part, melange, pres, logUnif,
                integrite, souffle, couverture, ouverture, alignement, coude,
                signes, LISIBLE, AUDIBLE, PORTE, PORTEE_SIGNE,
                menace, issue,
                LATENCE, vacarme, surdite, tunnel, gain,
                coupRecu, coupFrole, ferQuiVient, voisinTombe, voisinPart, dansLeDos, signeTombe,
                habituer, prehabituer, saillance, armement, resonne, activer, emprise,
                JAMBES, BRAS, acquis, appels, INTERDIT_JAMBES, INTERDIT_BRAS,
                possible, SOUS_EMPRISE, dysregule, coupler, pas, phrase, PHRASES };

  // Il doit tourner dans node SEUL, sans faux navigateur : c'est la condition
  // pour qu'on puisse le mesurer au lieu de le regarder.
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  if (typeof window !== "undefined") window.Corps = API;
})();
