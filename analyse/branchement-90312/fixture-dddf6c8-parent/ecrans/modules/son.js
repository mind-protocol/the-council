// son.js — l'oreille de la bataille.
//
// POURQUOI CE MODULE EXISTE. La bataille se joue à quatre heures et demie du
// matin. Le canal de la vue est au tiers de sa valeur, le stimulus « fer qui
// part vers moi » est presque mort, et un homme se fait tuer par ce qu'il n'a
// pas vu venir. Si le rendu ne bascule pas sur l'oreille, le joueur SUBIT la
// cécité du modèle sans en recevoir la matière : il regarde un champ obscur où
// des choses arrivent sans cause. La nuit, le son n'est pas une ambiance, c'est
// le canal d'information.
//
// ─────────────────────────────────────────────────────────────────────────────
// LES CINQ DÉCISIONS, ET AUCUNE N'EST TECHNIQUE
//
// 1. TOUT EST SYNTHÉTISÉ, SAUF LA GORGE HUMAINE. Un échantillon est une
//    constante ; un synthé est une fonction. Une banque de sons est une banque
//    de constantes qui mentiront le jour où l'échelle du modèle bougera — c'est
//    `SEUIL_RECUL = 0.5`, mais dans l'oreille. Cinq clangs enregistrés donnent
//    cinq clangs ; la synthèse modale donne un CONTINUUM piloté par la sortie
//    de la machine à états — un coup qui touche, un coup paré, un fer qui
//    glisse ne sont plus quatre fichiers mais quatre points d'un paramétrage.
//    Le cri d'homme, lui, s'entend synthétique au premier essai : ceux-là sont
//    des fichiers, une quinzaine, dans `sons/cris/`.
//
// 2. LE PLAFOND DE VOIX N'EST PAS UNE LIMITE DE MACHINE, C'EST L'OREILLE.
//    Au-delà d'une vingtaine d'attaques par seconde, l'audition cesse de
//    résoudre les onsets : elle fusionne en rugosité, puis en texture. Le
//    budget de voix a donc le droit d'exister au même titre que la largeur
//    d'épaules d'un homme — c'est une mesure perceptive, pas un réglage de
//    performance. Cent `AudioBufferSourceNode` simultanés ne coûtent rien ;
//    c'est l'oreille qui plafonne, pas le processeur.
//
// 3. CE QUI N'EST PAS JOUÉ N'EST PAS PERDU : ÇA PASSE DANS LE FOND. C'est le
//    point de conception, et il rend le problème trivial. Les événements non
//    élus incrémentent une DENSITÉ au lieu de disparaître. L'énergie se
//    conserve : sous le seuil de résolution, un son devient de la texture —
//    ce qui est littéralement ce qu'est une foule. Pas de troncature, pas de
//    « on a laissé tomber les autres » : une seule grandeur qui bascule d'un
//    canal à l'autre.
//
//    CE QUE CETTE DENSITÉ ALLUME A CHANGÉ, et c'est le seul revirement de ce
//    fichier. Elle pilotait trois bandes de bruit filtré ; ça sonnait comme
//    une ventilation, on a corrigé deux fois, et le défaut n'était pas dans le
//    réglage mais dans le matériau — une foule n'est pas du bruit qu'on filtre.
//    Elle pilote désormais un DÉBIT DE GRAINS de vraies gorges (`grainer`).
//    La règle est intacte, le canal a changé.
//
// 4. L'OREILLE EST AU PERSONNAGE, PAS À LA CAMÉRA. Le zoom est un œil, pas un
//    corps. Si le mix se resserrait quand la vue approche, on fabriquerait une
//    oreille omnisciente qui entend le fer à trois cents mètres du siège, et le
//    brouillard tomberait par la bande. Conséquence assumée : quand le joueur
//    zoome loin de son personnage, il regarde un endroit qu'il n'entend pas.
//    C'est juste, et c'est déroutant — au rendu de le dire, pas à nous de le
//    corriger.
//
// 5. LA SURDITÉ DE STRESS SE JOUE, ELLE NE SE DÉCRIT PAS. Sous alarme haute,
//    l'exclusion auditive rétrécit le champ perçu — et elle tue le canal du dos
//    exactement quand il servirait. Ici, l'alarme de l'oreille resserre le
//    rayon audible et ferme les aigus. Le joueur devient sourd de son dos au
//    moment où ça le tue : c'est le modèle joué, pas un effet.
//
// INTERDIT, symétrique de la Règle Zéro du manuel : AUCUN SON DÉCLENCHÉ POUR
// LE DRAME. Un son sort d'un événement du modèle, ou il n'existe pas.
//
// SCRIPT CLASSIQUE, PAS MODULE ES — même raison que `hasard.js` : la chaîne de
// la bataille se lit en synchrone.
"use strict";
window.Son = (() => {

  // ───────────────────────────────────────────────────────────────────────────
  // LES MESURES — du monde physique, jamais des réglages.
  //
  // Chacune se corrige quand on apprend qu'on s'était trompé sur le monde, et
  // jamais pour obtenir un comportement. Elles portent leur source.
  // ───────────────────────────────────────────────────────────────────────────
  const M = {
    // Le son parcourt 343 m/s dans l'air à 20 °C. À deux cents mètres, c'est
    // six dixièmes de seconde de retard — parfaitement audible, et gratuit à
    // rendre puisqu'on ordonnance déjà avec de l'anticipation. C'est ce décalage
    // qui donne la profondeur d'un champ de nuit : on voit l'éclair du fer,
    // on l'entend après.
    CELERITE: 343,

    // Jusqu'où porte chaque chose, de nuit, dans une ville. Un cri d'homme
    // porte loin et bas (les basses fréquences contournent le bâti) ; un choc
    // de fer est aigu, directionnel, et meurt vite dans les rues.
    PORTEE: { fer: 120, chair: 60, pas: 90, cri: 300, houle: 500 },

    // Le seuil de fusion auditive : au-delà, les attaques ne se distinguent
    // plus les unes des autres. C'est LUI qui fixe le budget de voix.
    ONSETS_PAR_SECONDE: 20,

    // L'intervalle minimal entre deux attaques d'une même famille. En deçà,
    // deux sons voisins filtrent en peigne et l'on entend une mitraillette.
    GARDE_MS: { fer: 40, chair: 60, cri: 200, effort: 120 },

    // Le temps de montée et de descente de l'adrénaline, en secondes. La nappe
    // suit les mêmes constantes que l'alarme du modèle : on ne change pas
    // d'ambiance deux fois par seconde, et ce n'est pas un lissage d'affichage,
    // c'est une glande.
    MONTEE: 1.2, DESCENTE: 8,

    // L'anticipation d'ordonnancement. Le rythme se cale sur l'horloge du
    // moteur audio, jamais sur `requestAnimationFrame` : un tremblement de
    // quelques millisecondes s'entend beaucoup plus qu'il ne se voit.
    LOOKAHEAD: 0.08,
  };

  // Combien de voix discrètes au plus. Ce n'est pas une constante posée : c'est
  // le seuil de fusion multiplié par la durée d'une tranche d'ordonnancement —
  // au-delà, la voix suivante ne serait pas entendue COMME une voix.
  const budgetVoix = () => Math.max(4, Math.round(M.ONSETS_PAR_SECONDE * M.LOOKAHEAD * 6));

  // Ce que la scène perd si l'on n'entend pas cette chose-là. Même geste que
  // `criticite.py` : on classe par ce qui manquerait, pas par ce qui est fort.
  // Un cri de panique porte une information que rien d'autre ne porte — il
  // annonce la contagion ; une parade de routine n'annonce rien.
  const CRITICITE = {
    "cri-panique": 1.0, "cri-mort": 0.8, "cri-assaut": 0.7,
    "cri-blesse": 0.5, chair: 0.45, effort: 0.3, fer: 0.25, pas: 0.05, houle: 0.05,
  };

  // À quelle bande de la nappe verse un événement qu'on n'a pas élu. C'est la
  // conservation de l'énergie du point 3 : il ne disparaît pas, il s'épaissit.
  const BANDE = {
    fer: "aigu", chair: "grave", pas: "grave", effort: "medium",
    "cri-assaut": "medium", "cri-blesse": "medium", "cri-mort": "medium",
    "cri-panique": "medium", houle: "medium",
  };

  const famillePortee = (f) => M.PORTEE[f] || (f.startsWith("cri") ? M.PORTEE.cri : 120);
  const familleGarde = (f) => M.GARDE_MS[f] || (f.startsWith("cri") ? M.GARDE_MS.cri : 60);
  const borne = (v, a, b) => (v < a ? a : v > b ? b : v);

  // ───────────────────────────────────────────────────────────────────────────
  // LA SURDITÉ DE STRESS — définie UNE FOIS, dans `survival-stack/1-corps.js`
  //
  // Elle y existe déjà : `surdite(alarme) = ((alarme + 1) / 2)²`. En la
  // réécrivant ici, on aurait deux définitions de la même chose, et le jour où
  // l'une bouge l'autre ment — c'est le même défaut qu'une constante recopiée.
  // On emprunte donc celle du corps quand il est chargé, et le repli est la
  // formule identique pour que le banc d'essai tourne module seul.
  //
  // CONSÉQUENCE D'INTERFACE, et elle a failli passer inaperçue : dans la pile,
  // TOUT est normalisé sur [−1, 1] — l'alarme comprise. Ce module la prenait
  // sur [0, 1]. Branché tel quel, un homme au calme (−1) aurait été lu comme
  // « à mi-alarme », et un homme paniqué (+1) aurait sonné comme un homme
  // ordinaire. L'oreille parle donc la même langue que le reste : [−1, 1].
  const surdite = (a) => (window.Corps && window.Corps.surdite)
    ? window.Corps.surdite(a)
    : Math.pow(Math.max(0, (a + 1) / 2), 2);

  // ───────────────────────────────────────────────────────────────────────────
  // L'ÉTAT DU MODULE
  // ───────────────────────────────────────────────────────────────────────────
  let ctx = null;                       // le contexte audio, créé au premier éveil
  let bus = null, stress = null, limiteur = null, maitre = null;
  let bruitBuffer = null;               // une seconde de bruit blanc, réutilisée partout
  let horloge = null;                   // le battement d'ordonnancement
  let eveille = false;

  let oreille = { x: 0, y: 0, alarme: -1 };  // où écoute-t-on, et dans quel état ([−1, 1])
  let suivi = undefined;                     // d'où l'on reprend la position, à chaque battement
  let attente = [];                          // les événements de la tranche en cours
  let curseur = {};                          // famille → prochaine attaque permise, en temps audio
  let densite = { grave: 0, medium: 0, aigu: 0 };  // ce qui est versé à la nappe
  let vivants = 0;                           // voix en cours, pour la somme en 1/√n
  let volume = 0.8;
  const cris = {};                           // famille → [AudioBuffer]

  // CE QUI SE COMPTE, ET POURQUOI PAS PAR TRANCHE. Un compte remis à zéro tous
  // les quatre-vingts millisecondes ne se lit pas : on tombe une fois sur deux
  // sur une tranche vide et l'on croit que rien ne joue. On tient donc un
  // CUMUL — qui sert à vérifier, parce qu'il ne ment pas — et un DÉBIT sur la
  // dernière seconde — qui sert à regarder.
  let compte = { voix: 0, nappe: 0, hors: 0 };          // la tranche en cours
  let cumul = { voix: 0, nappe: 0, hors: 0 };           // depuis l'éveil
  let debit = { voix: 0, nappe: 0, hors: 0 };           // la dernière seconde pleine
  let fenetre = { voix: 0, nappe: 0, hors: 0, t: 0 };

  // ───────────────────────────────────────────────────────────────────────────
  // LA CHAÎNE — construite une fois
  //
  // Des sources incohérentes s'additionnent en PUISSANCE : cinquante voix
  // identiques font +17 dB. Sans le gain en 1/√n et le limiteur en bout,
  // il suffit de dézoomer pour saturer.
  // ───────────────────────────────────────────────────────────────────────────
  function batir() {
    const A = window.AudioContext || window.webkitAudioContext;
    if (!A) return false;
    ctx = new A();

    maitre = ctx.createGain();
    maitre.gain.value = volume;

    // Le limiteur : un compresseur à ratio haut, seuil bas, attaque très courte.
    // Il ne remplace pas le 1/√n — il rattrape ce que le 1/√n ne prévoit pas,
    // c'est-à-dire la coïncidence.
    limiteur = ctx.createDynamicsCompressor();
    limiteur.threshold.value = -12;
    limiteur.knee.value = 6;
    limiteur.ratio.value = 12;
    limiteur.attack.value = 0.003;
    limiteur.release.value = 0.15;

    // La surdité de stress : un passe-bas qui se ferme avec l'alarme.
    stress = ctx.createBiquadFilter();
    stress.type = "lowpass";
    stress.frequency.value = 16000;
    stress.Q.value = 0.7;

    bus = ctx.createGain();
    bus.gain.value = 1;

    bus.connect(stress); stress.connect(limiteur);
    limiteur.connect(maitre); maitre.connect(ctx.destination);

    // Une seconde de bruit blanc : la matière première du fer, du pied et de la
    // nappe. Un seul buffer pour tout le module — on le relit à des vitesses et
    // des points de départ différents, ce qui suffit à ce qu'on ne reconnaisse
    // jamais deux fois la même chose.
    bruitBuffer = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const d = bruitBuffer.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;

    return true;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // IL N'Y A PLUS DE NAPPE — retirée le 14 août, à l'oreille.
  //
  // Elle a existé, elle était défendable sur le papier, et elle sonnait mal.
  // Trois bandes de bruit filtré, même respirantes, même à Q bas : ça reste du
  // bruit à large bande, et l'oreille appelle ça une ventilation. On a corrigé
  // deux fois — Q, modulation lente — et le défaut n'était pas là : il était
  // dans le matériau. Une foule n'est pas du bruit qu'on filtre, c'est mille
  // gorges et mille pieds. La seule façon d'en faire une est d'en semer les
  // morceaux, et c'est `grainer()` qui le fait.
  //
  // CE QU'ON PERD, ET IL FAUT LE DIRE : la décision 3 du haut de ce fichier —
  // « ce qui n'est pas joué passe dans la nappe » — n'est plus tenue par une
  // bande continue. Elle l'est par le GRAIN, dont le débit sort de la même
  // densité. C'est la même conservation ; le canal a changé, pas la règle.
  // `densite` continue donc d'être tenue à jour : elle ne pilote plus un gain,
  // elle pilote un débit de grains.
  //
  // Ce qui reste franchement muet : le grave (les pieds, la masse) et l'aigu
  // (le fer au loin). Le jour où l'on voudra les rendre, ce sera par des
  // grains eux aussi — des pas enregistrés, des chocs lointains —, jamais en
  // rallumant une bande.

  // ---- LE GRAIN — la foule est faite de gorges, pas de bruit ----------------
  // Un morceau de murmure, pris au hasard dans un des fichiers de `houle`, à
  // une hauteur et une position de départ tirées. Trois de ces grains qui se
  // chevauchent font une foule ; du bruit filtré n'en fera jamais une.
  //
  // Ça ne passe PAS par l'élection et ça n'a pas de position : le grain est la
  // texture elle-même. Son débit sort de la densité — c'est la version
  // audible de « ce qui n'est pas joué s'épaissit ».
  let grainDu = 0, grains = 0, avecGrain = true;
  function grainer(maintenant) {
    const banque = cris.houle;
    if (!avecGrain || !banque || !banque.length) return;
    const d = densite.medium;
    if (d < 0.4) return;
    // De un à huit grains par seconde selon l'épaisseur. Au-delà, ils se
    // recouvrent complètement et l'on n'ajoute plus que du volume.
    const parSeconde = Math.min(8, 0.8 + d * 0.9);
    if (maintenant - grainDu < 1 / parSeconde) return;
    grainDu = maintenant; grains++;

    const buf = banque[(Math.random() * banque.length) | 0];
    const src = ctx.createBufferSource();
    src.buffer = buf;
    // Large dispersion de hauteur : c'est ce qui empêche de reconnaître les
    // deux seuls fichiers dont on dispose.
    src.playbackRate.value = 0.72 + Math.random() * 0.55;
    const duree = 0.25 + Math.random() * 0.5;
    const debut = Math.random() * Math.max(0.01, buf.duration - duree);

    // Une enveloppe douce aux deux bouts : un grain coupé net fait un clic, et
    // huit clics par seconde, c'est un moteur.
    const g = ctx.createGain();
    const pic = 0.5 * Math.min(1, d / 8);
    g.gain.setValueAtTime(0.0001, maintenant);
    g.gain.exponentialRampToValueAtTime(Math.max(0.0002, pic), maintenant + duree * 0.35);
    g.gain.exponentialRampToValueAtTime(0.0001, maintenant + duree);

    const pan = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
    if (pan) pan.pan.value = Math.random() * 1.6 - 0.8;
    src.connect(g);
    if (pan) { g.connect(pan); pan.connect(bus); } else g.connect(bus);
    src.start(maintenant, debut, duree + 0.05);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // LA DISTANCE — ce qui reste d'un son quand il a traversé la nuit
  //
  // Trois effets, et les trois sont physiques : la pression décroît en 1/d,
  // l'air et le bâti mangent les aigus les premiers, et le son arrive en
  // retard. Le troisième est celui qu'on oublie, et c'est celui qui donne la
  // profondeur.
  // ───────────────────────────────────────────────────────────────────────────
  function chaine(x, y, famille, quand) {
    const dx = x - oreille.x, dy = y - oreille.y;
    const d = Math.sqrt(dx * dx + dy * dy);
    const portee = famillePortee(famille) * (1 - 0.45 * surdite(oreille.alarme));
    if (d > portee) return null;

    // 1/d, borné à un mètre — sinon un événement sur l'oreille sature seul.
    const attenuation = 1 / Math.max(1, d / 3);

    const sortie = ctx.createGain();
    sortie.gain.value = attenuation / Math.sqrt(Math.max(1, vivants));

    // Les aigus meurent avec la distance : un fer à cent mètres est un bruit
    // sourd, pas un tintement lointain.
    const air = ctx.createBiquadFilter();
    air.type = "lowpass";
    air.frequency.value = borne(18000 * Math.exp(-d / 45), 400, 18000);

    // LE PANORAMIQUE EST DANS LE REPÈRE DU MONDE, ET C'EST BIEN CE QU'ON VEUT —
    // vérifié, pas supposé. On craignait qu'un plan qui pivote ne mette à
    // droite ce qui sonne à gauche ; `carte-ville.js` ne pivote jamais (seuls
    // les HOMMES pivotent, dans `bataille2d.js`), donc l'axe x du monde EST
    // l'axe x de l'écran. Le jour où une vue tournante apparaîtra, c'est ici
    // qu'il faudra projeter dans la base de l'écran — et nulle part ailleurs.
    //
    // On ne modélise pas l'orientation de la tête : un homme au combat tourne
    // trop pour qu'une tête fixe ne soit pas un mensonge plus gros que
    // l'approximation.
    const pan = ctx.createStereoPanner
      ? ctx.createStereoPanner() : null;
    if (pan) pan.pan.value = borne(dx / Math.max(20, portee * 0.5), -1, 1);

    air.connect(pan || sortie);
    if (pan) pan.connect(sortie);
    sortie.connect(bus);

    return { entree: air, t: quand + d / M.CELERITE, d, attenuation };
  }

  // ───────────────────────────────────────────────────────────────────────────
  // LE FER — synthèse modale, et c'est ici que le continuum se gagne
  //
  // Un choc métallique, c'est une salve très courte qui excite des modes
  // inharmoniques amortis. Deux paramètres suffisent à couvrir tout ce que la
  // machine à états produit :
  //   `metal` 1 = fer contre fer (brillant, long) … 0 = fer dans la chair
  //                              (sourd, mat, court)
  //   `force` 0…1 = ce que le coup portait
  // Un coup paré et un coup qui touche ne sont pas deux fichiers : ce sont deux
  // points de ce plan, et tout ce qu'il y a entre les deux existe aussi.
  // ───────────────────────────────────────────────────────────────────────────
  // ⚠ POURQUOI ÇA SONNAIT COMME DU VERRE. Cinq SINUS purs à des rapports
  // inharmoniques, avec une décroissance d'un demi-seconde : c'est la recette
  // exacte d'un verre, d'un carillon, d'un glockenspiel. Trois erreurs
  // empilées, et aucune n'était un réglage :
  //
  //   · UN SINUS PUR N'EST PAS DU MÉTAL. Un mode d'acier réel est un
  //     RÉSONATEUR — une bande étroite excitée par du bruit —, pas une raie.
  //     C'est la largeur de bande qui fait entendre « acier » plutôt que
  //     « cloche ». On excite donc des bandpass à Q élevé, jamais des sinus.
  //   · TROP LONG. Une lame qui en heurte une autre sonne 80 à 200 ms, pas une
  //     demi-seconde. Un demi-seconde, c'est un verre à pied.
  //   · TROP HAUT. On montait à 3 000 Hz de fondamental ; une lame ou une
  //     plaque d'armure vit entre 600 et 1 800 Hz. Le suraigu est du cristal.
  //
  // Et un ajout qui fait beaucoup : les modes d'un objet frappé GLISSENT vers
  // le bas en s'éteignant (la raideur chute avec l'amplitude). Sans ce glissé,
  // même juste par ailleurs, un choc reste synthétique.
  const MODES = [1, 1.71, 2.46, 3.62];         // rapports inharmoniques d'une plaque

  function fer(quand, ev) {
    const c = chaine(ev.x, ev.y, ev.metal > 0.5 ? "fer" : "chair", quand);
    if (!c) return false;
    const force = borne(ev.force === undefined ? 0.6 : ev.force, 0, 1);
    const metal = borne(ev.metal === undefined ? 1 : ev.metal, 0, 1);
    const t = c.t;

    // Le fondamental monte avec la brillance et se disperse d'un coup à
    // l'autre : deux lames ne sonnent jamais pareil, et c'est ce qui empêche
    // le filtre en peigne sans qu'on ait à le corriger après coup.
    const f0 = (330 + 1150 * metal) * (0.78 + Math.random() * 0.44);
    const duree = (0.03 + 0.17 * metal * metal) * (0.7 + 0.6 * force);

    // Le transitoire : six millisecondes de bruit, c'est l'attaque. Sans lui on
    // entend une cloche ; avec lui on entend un choc.
    const bruit = ctx.createBufferSource();
    bruit.buffer = bruitBuffer;
    bruit.playbackRate.value = 0.8 + Math.random() * 0.5;
    // ET IL PORTE PLUS QUE LES MODES. Un choc d'acier, c'est aux deux tiers du
    // transitoire large bande ; la résonance n'est que la queue. Tant que le
    // rapport était inverse, on entendait la queue — c'est-à-dire la cloche.
    const gb = ctx.createGain();
    gb.gain.setValueAtTime(0.8 * force, t);
    gb.gain.exponentialRampToValueAtTime(0.0001, t + 0.011 + 0.03 * (1 - metal));
    const passe = ctx.createBiquadFilter();
    passe.type = metal > 0.5 ? "highpass" : "lowpass";
    passe.frequency.value = metal > 0.5 ? 1200 : 700;
    bruit.connect(passe); passe.connect(gb); gb.connect(c.entree);
    bruit.start(t, Math.random() * 0.5); bruit.stop(t + 0.08);

    // Les modes, en RÉSONATEURS et non en sinus. Une seule source de bruit,
    // large et brève, excite trois ou quatre bandes étroites : c'est la
    // définition physique d'un objet métallique frappé, et c'est ce qui fait
    // entendre « acier » là où des sinus faisaient entendre « verre ».
    // Le nombre de bandes tenues décroît avec la chair : un coup dans un corps
    // n'a pas de résonance, il a un thud.
    const combien = 1 + Math.round(3 * metal);
    const corde = ctx.createBufferSource();
    corde.buffer = bruitBuffer;
    corde.playbackRate.value = 0.9 + Math.random() * 0.35;
    corde.start(t, Math.random() * 0.5);
    corde.stop(t + duree + 0.05);
    for (let i = 0; i < combien; i++) {
      const bande = ctx.createBiquadFilter();
      bande.type = "bandpass";
      const f = f0 * MODES[i] * (0.98 + Math.random() * 0.04);
      bande.frequency.setValueAtTime(f, t);
      // LE GLISSÉ. La raideur d'une plaque chute avec l'amplitude : ses modes
      // descendent de quelques pour cent pendant qu'ils s'éteignent. C'est
      // inaudible en soi et c'est ce qui distingue un choc d'un bip.
      bande.frequency.exponentialRampToValueAtTime(f * 0.93, t + duree);
      // Q élevé pour tenir la note, mais pas au point d'en faire une raie :
      // au-delà de 60 on retombe sur le sinus qu'on vient de retirer.
      bande.Q.value = 14 + 22 * metal;
      const g = ctx.createGain();
      const amp = (0.5 * force) / (1 + i * 1.2);
      // Les partiels aigus s'éteignent les premiers — c'est ce qui fait qu'un
      // choc « s'assombrit » en mourant au lieu de baisser de volume.
      const dm = duree / (1 + i * 0.55);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(Math.max(0.0002, amp), t + 0.002);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dm);
      corde.connect(bande); bande.connect(g); g.connect(c.entree);
    }
    return true;
  }

  // LE PIED, LE CORPS QUI TOMBE — du bruit grave enveloppé, rien de plus. Ces
  // sons-là n'ont pas de hauteur ; leur seule information est « quelque chose
  // de lourd, là ».
  function sourd(quand, ev) {
    const c = chaine(ev.x, ev.y, ev.famille === "pas" ? "pas" : "chair", quand);
    if (!c) return false;
    const force = borne(ev.force === undefined ? 0.5 : ev.force, 0, 1);
    const t = c.t;
    const src = ctx.createBufferSource();
    src.buffer = bruitBuffer;
    src.playbackRate.value = 0.25 + Math.random() * 0.25;
    const f = ctx.createBiquadFilter();
    f.type = "lowpass"; f.frequency.value = 200 + 260 * force; f.Q.value = 1.2;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.5 * force, t + 0.008);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.12 + 0.2 * force);
    src.connect(f); f.connect(g); g.connect(c.entree);
    src.start(t, Math.random() * 0.5); src.stop(t + 0.4);
    return true;
  }

  // LES CRIS — les seuls fichiers du module. Détunés et décalés à chaque
  // lecture : dix cris bien choisis en donnent une centaine à l'oreille.
  function cri(quand, ev) {
    const banque = cris[ev.famille];
    if (!banque || !banque.length) return false;
    const c = chaine(ev.x, ev.y, "cri", quand);
    if (!c) return false;
    const buf = banque[(Math.random() * banque.length) | 0];
    const src = ctx.createBufferSource();
    src.buffer = buf;
    // ±6 % : assez pour que la même gorge ne se reconnaisse pas d'un homme à
    // l'autre, pas assez pour qu'on entende le pitch shift.
    src.playbackRate.value = 0.94 + Math.random() * 0.12;
    const g = ctx.createGain();
    g.gain.value = 0.9 * borne(ev.force === undefined ? 0.8 : ev.force, 0.15, 1);
    src.connect(g); g.connect(c.entree);
    src.start(c.t);
    return true;
  }

  function jouer(quand, ev) {
    vivants++;
    // Une voix vit au plus deux secondes ; on décompte à plat plutôt que de
    // guetter `onended`, qui arrive trop tard pour servir au 1/√n suivant.
    setTimeout(() => { vivants = Math.max(0, vivants - 1); }, 1400);
    if (ev.famille === "fer" || ev.famille === "chair") return fer(quand, ev);
    if (ev.famille === "pas") return sourd(quand, ev);
    if (ev.famille.startsWith("cri") || ev.famille === "effort") return cri(quand, ev);
    return false;
  }

  // ───────────────────────────────────────────────────────────────────────────
  // LE BATTEMENT — l'élection, et le versement du reste à la nappe
  //
  // La même élection que partout ailleurs dans ce jeu : on ne prend pas le plus
  // proche ni le plus fort, on prend celui dont l'absence coûterait le plus.
  // ───────────────────────────────────────────────────────────────────────────
  function battre() {
    if (!eveille || !ctx) return;
    // L'oreille suit le personnage, jamais la caméra — décision 4. On la reprend
    // à chaque battement plutôt qu'une fois pour toutes : un homme marche, et
    // douze fois par seconde suffit très largement à une oreille qui se déplace
    // à un mètre par seconde.
    if (suivi) { const p = suivi(); if (p && p.x !== undefined) { oreille.x = p.x; oreille.y = p.y; } }
    const maintenant = ctx.currentTime;
    const quand = maintenant + M.LOOKAHEAD;
    const evs = attente; attente = [];
    // ⚠ ON NE REMET PAS `compte` À ZÉRO ICI. Il l'était, et tout ce que `fond()`
    // versait ENTRE deux battements était effacé avant d'avoir été cumulé :
    // trois cents hommes qui marchaient épaississaient bien la nappe, mais le
    // compte rendu disait « 0 ». Un compteur qui ment sur ce qu'on vient de
    // brancher est pire que pas de compteur. La remise à zéro est donc à la
    // FIN, juste après le versement au cumul.

    // Le score : criticité × proximité. La rareté entre par la garde de
    // famille ci-dessous — un fer qui vient de sonner ne peut pas resonner
    // avant quarante millisecondes, ce qui écrête la répétition tout seul.
    for (const ev of evs) {
      const dx = ev.x - oreille.x, dy = ev.y - oreille.y;
      ev._d = Math.sqrt(dx * dx + dy * dy);
      const portee = famillePortee(ev.famille) * (1 - 0.45 * surdite(oreille.alarme));
      ev._dedans = ev._d <= portee;
      ev._score = (CRITICITE[ev.famille] || 0.2) * (1 - ev._d / Math.max(1, portee));
    }
    evs.sort((a, b) => b._score - a._score);

    const budget = budgetVoix();
    // Jusqu'où l'on a le droit de repousser une attaque pour la faire tenir
    // dans sa garde de famille. Au-delà, ce n'est plus cette tranche-ci : le
    // son arriverait après ce qu'il annonce, et il vaut mieux le verser à la
    // nappe que de le jouer en retard sur l'image.
    const limite = quand + 4 * M.LOOKAHEAD;

    for (const ev of evs) {
      // Hors de portée : on ne l'entend pas du tout. Il ne va même pas à la
      // nappe — le brouillard vaut pour l'oreille comme pour le reste.
      if (!ev._dedans) { compte.hors++; continue; }

      // LA GARDE ESPACE, ELLE N'ÉLIMINE PAS. Premier jet, elle interdisait
      // l'élection : trente coups de fer dans la même tranche n'en donnaient
      // qu'UN SEUL, parce qu'ils portaient tous le même horodatage et que le
      // deuxième arrivait déjà trop tôt. Une mêlée entière sonnait comme un
      // homme qui tape sur une enclume. Ce qu'il fallait, c'est décaler la
      // deuxième attaque de quarante millisecondes — ce qui évite le filtre en
      // peigne ET rend le crépitement. Ce qui ne tient plus dans la tranche
      // tombe alors de lui-même dans la nappe : l'écrêtage est une conséquence,
      // pas une règle.
      const f = ev.famille;
      const t = Math.max(quand, curseur[f] || 0);
      if (compte.voix < budget && t <= limite && jouer(t, ev)) {
        curseur[f] = t + familleGarde(f) / 1000;
        compte.voix++;
      } else {
        // Non élu ≠ perdu : il s'épaissit dans sa bande.
        densite[BANDE[f] || "medium"] += 1;
        compte.nappe++;
      }
    }

    cumul.voix += compte.voix; cumul.nappe += compte.nappe; cumul.hors += compte.hors;
    fenetre.voix += compte.voix; fenetre.nappe += compte.nappe; fenetre.hors += compte.hors;
    if (maintenant - fenetre.t >= 1) {
      debit = { voix: fenetre.voix, nappe: fenetre.nappe, hors: fenetre.hors };
      fenetre = { voix: 0, nappe: 0, hors: 0, t: maintenant };
    }
    compte = { voix: 0, nappe: 0, hors: 0 };
    reglerFond(maintenant);
    grainer(maintenant);
  }

  // Ce qui reste de l'ancien `reglerNappe` : la densité, qui n'allume plus une
  // bande mais nourrit le débit des grains, et la surdité de stress, qui est
  // la seule chose du module à agir sur TOUT ce qui sort.
  //
  // L'inertie est celle de l'adrénaline, pas celle de l'affichage : ce qui
  // s'épaissit vite met huit secondes à retomber. C'est ce qui fait qu'une
  // ville qui vient de se taire continue de bruire — et c'est vrai.
  function reglerFond(maintenant) {
    for (const nom of Object.keys(densite)) densite[nom] *= 0.55;
    // Seize kilohertz au calme, deux à la panique : le dos cesse d'exister,
    // ce qui est exactement le point.
    stress.frequency.setTargetAtTime(
      16000 * Math.pow(0.14, surdite(oreille.alarme)), maintenant, 0.8);
  }

  // ───────────────────────────────────────────────────────────────────────────
  // LES CRIS — chargés une fois, à l'éveil
  // ───────────────────────────────────────────────────────────────────────────
  async function chargerCris() {
    let fiches = [];
    try {
      const r = await fetch("/sons/cris/cris.json");
      fiches = await r.json();
    } catch (e) { return; }
    await Promise.all(fiches.map(async (f) => {
      try {
        const r = await fetch("/sons/cris/" + f.fichier);
        const buf = await ctx.decodeAudioData(await r.arrayBuffer());
        (cris[f.famille] = cris[f.famille] || []).push(buf);
      } catch (e) { /* un fichier manquant n'empêche pas les autres */ }
    }));
  }

  // ───────────────────────────────────────────────────────────────────────────
  // CE QUE LE RESTE DU JEU APPELLE
  // ───────────────────────────────────────────────────────────────────────────

  /**
   * Ouvrir l'oreille. DOIT être appelé depuis un geste de l'utilisateur —
   * aucun navigateur ne laisse une page faire du bruit sans qu'on l'ait
   * touchée, et c'est très bien ainsi.
   */
  async function eveiller() {
    if (eveille) return true;
    if (!ctx && !batir()) return false;
    if (ctx.state === "suspended") await ctx.resume();
    eveille = true;
    // Au premier éveil, l'oreille se met d'elle-même au personnage. Sans ça
    // elle resterait à l'origine du monde, c'est-à-dire au coin nord-ouest de
    // la carte — et tout serait hors de portée sans qu'on comprenne pourquoi.
    if (suivi === undefined) suivre();
    if (!horloge) horloge = setInterval(battre, Math.round(M.LOOKAHEAD * 1000));
    chargerCris();
    return true;
  }

  function dormir() {
    eveille = false;
    if (horloge) { clearInterval(horloge); horloge = null; }
    if (ctx && ctx.state === "running") ctx.suspend();
  }

  /**
   * Où l'on écoute, et dans quel état. `alarme` sur [−1, 1], comme toute la
   * pile. Poser une position à la main COUPE le suivi : c'est ce qui permet au
   * banc d'essai d'écouter depuis un point fixe.
   */
  function poserOreille(o) {
    if (o.x !== undefined) { oreille.x = o.x; suivi = null; }
    if (o.y !== undefined) oreille.y = o.y;
    if (o.alarme !== undefined) oreille.alarme = borne(o.alarme, -1, 1);
  }

  /**
   * D'où l'oreille reprend sa position à chaque battement.
   *   `suivre(fn)`   — une fonction qui rend `{x, y}` en mètres, ou `null`
   *   `suivre(null)` — on s'arrête au dernier point connu
   *   `suivre()`     — le défaut : le marqueur du joueur sur le plan de la
   *                    ville, qui est le seul endroit du jeu où l'on sache où
   *                    le personnage se tient AU MÈTRE.
   * On ne va pas le chercher dans le DOM : `CarteVille.ou()` le rend déjà, et
   * passer par `.cv-ici-point` ferait dépendre le son de la forme d'un dessin.
   */
  function suivre(f) {
    if (f === null) { suivi = null; return null; }
    if (typeof f === "function") { suivi = f; return suivi; }
    suivi = () => (window.CarteVille && window.CarteVille.ou) ? window.CarteVille.ou() : null;
    return suivi;
  }

  /**
   * Un événement du modèle. Il n'est pas joué tout de suite : il attend le
   * prochain battement, où il sera élu ou versé à la nappe.
   *   { famille, x, y, force?, metal? }
   */
  function dire(ev) {
    if (!eveille || !ev || !ev.famille) return;
    // Un garde-fou et un seul : une tranche qui déborde n'est pas un problème
    // de son, c'est une simulation qui a divergé. On plafonne pour ne pas
    // faire tomber la page, et le compte le dit.
    if (attente.length < 4000) attente.push(ev);
  }

  /**
   * Verser DIRECTEMENT à la nappe, sans passer par l'élection.
   *   `fond("pas", 240, x, y)` — « il y a deux cent quarante hommes qui
   *   marchent, par là ».
   *
   * POURQUOI CE SECOND GUICHET, ET POURQUOI IL N'EST PAS UNE COMMODITÉ. Le pas
   * d'un homme est un événement comme un autre — mais il y a dix-sept cents
   * hommes, et deux pas par seconde chacun font trois mille cinq cents objets
   * par seconde à fabriquer, trier et jeter pour que TOUS finissent en nappe.
   * On paierait l'élection au prix fort pour un résultat connu d'avance.
   *
   * Ce guichet dit la même chose en un appel : c'est le seul cas où l'on SAIT
   * qu'une chose est de la texture et jamais une voix. Une règle, donc, et une
   * seule : n'y verse que ce qui n'a AUCUNE chance d'être élu — la masse, la
   * houle, le fer d'une mêlée qu'on n'a pas sous les yeux. Un cri n'y va
   * jamais : un cri qui n'est pas élu doit avoir été jugé, pas escamoté.
   */
  function fond(famille, combien, x, y) {
    if (!eveille || !combien) return;
    const dx = x - oreille.x, dy = y - oreille.y;
    const d = Math.sqrt(dx * dx + dy * dy);
    const portee = famillePortee(famille) * (1 - 0.45 * surdite(oreille.alarme));
    if (d > portee) { compte.hors += combien; return; }
    // Même décroissance que pour une voix : ce qui est loin épaissit moins.
    densite[BANDE[famille] || "medium"] += combien * (1 - d / portee);
    compte.nappe += combien;
  }

  const reglerVolume = (v) => { volume = borne(v, 0, 1); if (maitre) maitre.gain.value = volume; };

  /** Pour le banc d'essai et pour l'œil du MJ : ce que l'oreille fait. */
  const etat = () => ({
    eveille,
    voix: debit.voix, nappe: debit.nappe, hors: debit.hors,   // par seconde, pour l'œil
    cumul: { ...cumul },                                       // depuis l'éveil, pour la preuve
    vivants, grains, budget: budgetVoix(),
    densite: { ...densite },
    alarme: oreille.alarme,
    // Ce que l'alarme FAIT, et non ce qu'elle vaut : le banc d'essai doit
    // dessiner les anneaux de portée avec la même formule que celle qui les
    // calcule, sinon on règle contre un dessin qui ment.
    sourdine: surdite(oreille.alarme),
    ou: { x: Math.round(oreille.x), y: Math.round(oreille.y), suit: !!suivi },
    cris: Object.fromEntries(Object.entries(cris).map(([k, v]) => [k, v.length])),
  });

  /**
   * Le grain de foule — le seul fond qui reste. `grain(false)` laisse le champ
   * entièrement muet entre les coups : plus une seule source continue, rien
   * que les événements élus. C'est l'état le plus sec du module, et il est
   * parfaitement jouable — une nuit de ville n'est pas bruyante.
   */
  const reglerGrain = (v) => { avecGrain = v !== false; return avecGrain; };

  return { eveiller, dormir, oreille: poserOreille, suivre, dire, fond,
           grain: reglerGrain, volume: reglerVolume, etat, M };
})();
