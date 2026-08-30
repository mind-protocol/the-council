// foule2d.js — la ville qui marche, en plan, à l'heure du jeu.
//
// CE MODULE NE CALCULE AUCUN DÉPLACEMENT. Tout est déjà écrit et servi :
// `monde/gens.js` charge les corps par cellules de 250 m, et `monde/journee.js`
// répond à `ou(corps, minute)` par une fonction PURE — rien à simuler, rien à
// sauvegarder, rien à rattraper. On peut demander où est n'importe qui à
// n'importe quelle minute, y compris trois jours plus tard, et obtenir la même
// réponse. Ici on ne fait que DESSINER ce que la 3D dessinait déjà en volume.
//
// POURQUOI UN CANVAS ET PAS DU SVG. Le plan est en SVG parce qu'il ne bouge
// pas : quarante mille silhouettes posées une fois, que le navigateur garde.
// La foule est l'inverse — quelques milliers de points qui changent tous à
// chaque image. En SVG, ce serait quelques milliers de nœuds à remuer soixante
// fois par seconde, et la page tombe à genoux. Un canvas posé par-dessus, calé
// sur le même cadrage, rend la même chose sans toucher au document.
//
// L'HORLOGE EST 1:1 : une minute réelle vaut une minute de Port-Réal. Elle
// part de l'heure du jeu (`etat/monde.json`) et n'y revient qu'à la demande —
// pendant qu'elle tourne, elle n'est PAS la montre de la partie, et rien de ce
// qu'on y voit n'est un fait de jeu. C'est une lunette braquée sur la ville,
// pas une avance du temps : le MJ seul fait avancer l'heure.
"use strict";
window.Foule2d = (() => {
  let G = null, J = null;              // les modules du monde, chargés à la demande
  let toile = null, ctx = null;
  let hote = null, vueDe = null, source = "/monde";
  let manif = null, rangs = null, pleinAir = null, voirie = null;
  let masque = null;                   // le filet : un bit par mètre carré
  let cellules = [], centre = null;
  let marche = false;                  // l'horloge tourne-t-elle
  let t0 = 0, min0 = 0, jour0 = 0;     // l'ancre : temps réel ↔ minute de jeu
  let minute = 0, jour = 0;
  let boucle = 0;
  const P = {};

  // Ce qu'on va chercher, et la couleur de chacun. Un point ne dit pas grand
  // chose ; un point QUI VA QUELQUE PART dit toute la ville — on voit l'eau du
  // matin, le pain, puis le marché, puis les tavernes du soir, chacun à son
  // heure et par sa couleur. Les services sont ceux de `besoins.json`.
  // NI NOIR NI CARRÉ. Un habitant n'est pas un pixel mort : c'est une tache de
  // laine sur un pavé, ronde parce que tout ce qui est vivant l'est, et
  // colorée parce que le noir sur du beige ne dit rien d'autre que « trou ».
  // Les teintes restent SOURDES — assez pour tenir sur un fond clair, jamais
  // assez pour crier — et chacune dit où va celui qui la porte.
  const TEINTES = {
    fuite: "#b03a24",            // celui qui court, et qui ne va nulle part
    puits: "#2f7f9e",            // l'eau
    boulangerie: "#a8701e",      // le pain
    echoppe: "#96591a",
    marche: "#b8811a",
    taverne: "#96324f",
    septuaire: "#545a8a",
    etuve: "#3c6f5a",
    travail: "#6b6252",
    chez: "#6b6252",             // ceux qui rentrent
    // LE GUET SE VOIT, et c'est le seul métier qui le mérite : c'est lui qu'on
    // regarde passer quand on prépare une sortie. L'or des manteaux — un or
    // qui tient sur du beige, pas un jaune de bannière.
    ronde: "#d8930a",
    poste: "#a97a1c",
  };
  const DEFAUT = "#6b6252";
  // Sous un toit : la même laine, vue à travers un mur. Un brun chaud, pas une
  // ombre — quarante personnes dans une taverne doivent faire un groupe qu'on
  // compte, pas une tache d'encre sur le plan.
  const DEDANS = "#8a7c66";

  // ---- LE FILET : personne ne marche dans un mur ---------------------------
  // `journee.js` pose les gens en mètres et ne sait rien du bâti : les
  // attroupements débordaient sur les toits, les piétons coupaient à travers
  // les maisons. Aucune règle géométrique ne couvre tous les cas — les
  // emprises se chevauchent, une arête de voirie traverse une cour, une porte
  // est SUR la façade et non devant. On cuit donc l'empreinte au sol de la
  // ville une fois pour toutes (`plan_ville.py`, un bit par mètre carré, 2,3
  // Mo pour Port-Réal) et l'on repousse ce qui tombe dessus.
  //
  // LA POUSSÉE EST UNE SPIRALE, pas une projection : on cherche la case libre
  // la plus proche, anneau par anneau. C'est ce qui fait sortir quelqu'un par
  // le côté le plus court — devant sa porte s'il est près de la rue, dans la
  // cour s'il en a une — au lieu de plaquer tout le monde dans la même
  // direction, ce qui alignerait la foule contre les façades.
  const POUSSEE = 9;                   // au-delà, on renonce et l'on laisse
  function bati(x, y) {
    if (!masque) return false;
    const i = (x / masque.pas) | 0, j = (y / masque.pas) | 0;
    if (i < 0 || j < 0 || i >= masque.nx || j >= masque.ny) return false;
    const k = j * masque.nx + i;
    return (masque.bits[k >> 3] >> (k & 7)) & 1;
  }
  // QUI EST SOUS LE CIEL, ET QUI EST SOUS UN TOIT. C'est la question que le
  // filet doit poser, et pendant longtemps il en posait une autre : « marche-
  // t-il ? ». Un homme arrêté était réputé arrivé, donc chez lui ou dans sa
  // taverne, donc en droit d'être dans la pierre. Le compte disait autre chose
  // — au marché, l'étendue est de CINQUANTE-CINQ MÈTRES, et le disque des
  // badauds mord de moitié sur les maisons d'en face : un tiers de la foule
  // d'un marché se tenait dans les cuisines du voisinage, et comme la flânerie
  // glisse d'une station à l'autre toutes les deux minutes, on la voyait
  // traverser les murs.
  //
  // Le puits et le marché sont à ciel ouvert — la table le dit elle-même
  // (`plein_air`) — et celui qui fuit ou qui monte la garde l'est aussi. Ces
  // quatre-là se dégagent comme les marcheurs. Le reste — la taverne, le four,
  // l'étuve — est DEDANS pour de bon, et l'en chasser ferait un anneau de
  // clients autour d'une salle vide.
  function aCiel(p) {
    if (p.quoi === "route") return true;
    if (p.quoi !== "sur-place") return false;
    return p.vers === "fuite" || p.vers === "ronde" ||
           !!(pleinAir && pleinAir.has(p.vers));
  }

  function degager(p) {
    if (!masque || !bati(p.x, p.y)) return;
    const pas = masque.pas;
    for (let d = 1; d <= POUSSEE; d++) {
      // les quatre côtés de l'anneau : à distance égale, sortir tout droit
      // vaut mieux que sortir en biais.
      for (let t = -d; t <= d; t++) {
        const essais = [[t, -d], [t, d], [-d, t], [d, t]];
        for (let e = 0; e < 4; e++) {
          const x = p.x + essais[e][0] * pas, y = p.y + essais[e][1] * pas;
          if (!bati(x, y)) { p.x = x; p.y = y; return; }
        }
      }
    }
  }

  // ---- l'horloge -----------------------------------------------------------
  const hhmm = (m) => {
    const h = Math.floor(m / 60) % 24;
    return (h < 10 ? "0" : "") + h + "h" + (m % 60 < 10 ? "0" : "") + (m % 60);
  };

  function horloge() {
    if (!marche) return;
    // 1:1 — une minute réelle, une minute de ville. Le pas se prend sur le
    // temps ÉCOULÉ et non sur un compteur qu'on incrémente : un onglet mis en
    // arrière-plan reprend à l'heure juste au lieu d'avoir pris du retard.
    const passe = (performance.now() - t0) / 60000;
    const total = min0 + passe;
    jour = jour0 + Math.floor(total / 1440);
    minute = total - Math.floor(total / 1440) * 1440;
  }

  function caler(d) {
    min0 = (d && typeof d.minute === "number") ? d.minute : 480;
    jour0 = (d && d.jour) || 1;
    minute = min0; jour = jour0;
    t0 = performance.now();
  }

  // ---- le cadrage ----------------------------------------------------------
  // La toile suit le SVG au pixel près. On ne l'écoute pas : c'est le plan qui
  // prévient quand il a bougé (`recadrer`), parce que lui seul sait quand.
  function ajuster() {
    if (!toile || !hote) return;
    const r = hote.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const l = Math.round(r.width * dpr), h = Math.round(r.height * dpr);
    if (toile.width !== l || toile.height !== h) {
      toile.width = l; toile.height = h;
    }
  }

  // Le SVG a `preserveAspectRatio="xMidYMid meet"` : son cadrage est CENTRÉ et
  // laisse des marges. Reproduire ça à la main est le seul endroit où une
  // erreur se voit tout de suite — la foule marcherait à côté de ses rues.
  function repere() {
    const vue = vueDe && vueDe();
    if (!vue || !toile || !toile.width) return null;
    return CarteProjection.repere(vue, toile.width, toile.height);
  }

  // ---- ce qu'on charge -----------------------------------------------------
  // On ne charge que ce qu'on regarde, et l'on ne recharge que si l'on a
  // vraiment bougé : `autour` rend toutes les cellules du rayon, y compris
  // celles déjà en cache, donc l'appeler à chaque image ne coûterait rien en
  // réseau — mais il rend une promesse, et attendre une promesse par image est
  // une allocation par image pour rien.
  let enCharge = false;
  function charger(vue) {
    if (enCharge || !G) return;
    const cx = vue[0] + vue[2] / 2, cy = vue[1] + vue[3] / 2;
    // ON CHARGE CE QU'ON REGARDE, ET LA VILLE ENTIÈRE TIENT. Le plafond était à
    // 1 400 m : au cadrage large, les trois quarts de Port-Réal n'étaient pas
    // chargés, et l'on prenait pour des rues désertes des cellules qu'on
    // n'avait jamais demandées. Les cent cinquante et une cellules font
    // quatre méga-octets et demi de binaire dense, une fois — moins que le
    // plan lui-même.
    const rayon = Math.max(300, Math.hypot(vue[2], vue[3]) / 2);
    if (centre && Math.hypot(cx - centre[0], cy - centre[1]) < 120 &&
        Math.abs(rayon - centre[2]) < 120) return;
    enCharge = true;
    G.autour(cx, cy, rayon, source).then((c) => {
      cellules = c; centre = [cx, cy, rayon];
      sale = true;                     // des corps neufs : il faut les placer
      // ET LA TRANCHE EN COURS N'A PLUS DE SOL. Elle indexe `cellules` par
      // rang ; la remplacer sous ses pieds lui fait sauter tout ce que le
      // nouveau tableau range avant son curseur, et l'on publiait ce
      // demi-comptage comme un nuage entier. On la reprend de zéro : le
      // dernier nuage complet reste à l'écran pendant ce temps.
      travail = null;
    }).catch(() => {}).then(() => { enCharge = false; });
  }

  // ---- QUI EST LÀ, ET DE QUEL MÉTIER ---------------------------------------
  // Une balade disait ce qu'on longe — des murs, des enseignes, un tissu — et
  // il y manquait le principal : LES GENS. Ce n'est pas du décor. C'est la
  // seule chose qui dise si la rue est vide à trois heures du matin ou pleine
  // à midi, donc la seule qui décide si l'on peut y faire quelque chose sans
  // être vu. Une ruelle déserte et une ruelle où trois portefaix déchargent
  // ne sont pas le même endroit, et jusqu'ici le MJ ne pouvait pas le savoir.
  //
  // ON NE COMPTE QUE CE QU'ON VOIT. Les quatre cent deux mille corps existent
  // à toute heure, mais la plupart sont derrière un mur — un marcheur ne les
  // rencontre pas. On sépare donc `dehors`, qui est de la RENCONTRE (en chemin,
  // ou arrêté à l'air libre : le puits, la halle, le marché), de `dedans`, qui
  // n'est que de l'ambiance. Confondre les deux ferait de Culpucier endormi
  // une foule, ce qui est faux et se retournerait contre le joueur.
  //
  // LE MÉTIER EST DÉJÀ DANS LE BINAIRE — un octet par corps, index dans le
  // `roles_index` du manifeste, quatre-vingt-huit rôles. On ne l'invente pas,
  // on ne le calcule pas, et il ne coûte rien.
  const PORTEE_GENS = 30;              // mètres : la rue, pas le quartier

  // QUATRE ÉTATS, PAS DEUX — et c'est la correction qui fait tout le prix de
  // cette fonction. « Dehors ou dedans » mettait dans le même sac celui qui
  // dort chez lui et celui qui boit à la taverne : neuf mille trois cents
  // personnes d'un côté, cent vingt-six de l'autre, c'est-à-dire un chiffre de
  // population et pas une rue. Or ce sont quatre situations que le jeu
  // distingue à chaque scène :
  //
  //   rue   — en chemin. On le croise, il vous voit, il vous a vu passer.
  //   place — arrêté à l'air libre : le puits, la halle. Un attroupement.
  //   toit  — sorti, mais derrière une porte : la taverne, le four, l'étuve.
  //           On ne le croise pas — on peut aller le chercher, et l'on sait
  //           par quelle porte. C'est le seul des quatre qui soit une ADRESSE.
  //   chez  — chez lui. Du chiffre d'ambiance, jamais une rencontre.
  //
  // `plein_air` (deux entrées : le puits et le marché) départage `place` de
  // `toit`. Tout le reste des services a un toit, et c'est pour ça qu'ils
  // valent une porte plutôt qu'une silhouette.
  // `quand` est une minute de jeu : sans elle on répond pour l'heure courante,
  // avec elle on répond pour une heure passée. C'est ce qui permet de demander
  // « qui était là » et pas seulement « qui est là » — sans quoi on ne pourrait
  // jamais attribuer de témoins à un fait daté, ce qui est tout l'usage.
  function presents(x, y, rayon, quand) {
    if (!G || !J || !voirie || !cellules.length) return null;
    // ON NE DIFFÈRE RIEN ICI. Le dessin peut se permettre d'attendre une passe ;
    // un compte de témoins, non — il doit être juste du premier coup, quel que
    // soit le plafond que la dernière tranche de dessin a laissé derrière elle.
    J.quotaChemins();
    const R = rayon || PORTEE_GENS, R2 = R * R;
    const min = (quand === undefined || quand === null) ? minute : quand;
    const maille = (manif && manif.cellule_m) || 250;
    const rue = new Map(), place = new Map(), toit = new Map(), chez = new Map();
    // Sous un toit, ce qui compte n'est pas le métier de l'homme : c'est la
    // PORTE derrière laquelle il est. « 12 à la taverne » se joue ; « 12
    // portefaix » ne dit pas où aller frapper.
    const portes = new Map();
    // CE QU'ILS FONT, et pas seulement ce qu'ils sont. Le verbe était calculé
    // à chaque corps — `p.quoi` dit où il est, `p.vers` où il va — puis jeté au
    // profit d'un compte par métier. Dix portefaix qui FUIENT se lisaient donc « 10
    // portefaix », mot pour mot comme dix portefaix qui vont au travail : le
    // MJ recevait une rue paisible au milieu d'un assaut.
    //
    // On le garde, rangé par verbe puis par métier — « fuient : 6 portefaix,
    // 2 servantes » se joue, « 8 personnes » ne se joue pas.
    const font = new Map();
    let nRue = 0, nPlace = 0, nToit = 0, nChez = 0;
    const p = {};
    for (const cel of cellules) {
      // ÉCARTER LA CELLULE ENTIÈRE AVANT DE L'OUVRIR. Une cellule porte deux
      // mille six cents corps et il y en a jusqu'à vingt-cinq chargées ; sans
      // ce test, un pas de balade paierait soixante-cinq mille journées, et
      // une balade fait un pas tous les vingt mètres. Avec, il en reste une ou
      // quatre, ce qui est exactement ce qu'un homme a autour de lui.
      if (cel.x0 - x > R || x - (cel.x0 + maille) > R ||
          cel.y0 - y > R || y - (cel.y0 + maille) > R) continue;
      for (let k = 0; k < cel.n; k++) {
        J.ou(cel, k, jour, min, voirie, rangs, p);
        const dx = p.x - x, dy = p.y - y;
        if (dx * dx + dy * dy > R2) continue;
        const m = (cel.roles_index && cel.roles_index[cel.role[k]]) || "inconnu";
        let t;
        if (p.quoi === "route") { t = rue; nRue++; }
        else if (p.quoi === "chez") { t = chez; nChez++; }
        // LA PEUR EST TOUJOURS DEHORS. Un homme jeté à terre ou saisi reste
        // « sur-place », avec `fuite` ou `ronde` pour destination — or ce ne
        // sont pas des services et il n'y a pas de toit
        // au-dessus. Sans ce test, un homme accroupi au milieu de la rue était
        // compté derrière une porte, et le fichier annonçait « 10 fuite,
        // 1 ronde » dans la colonne des portes où l'on va frapper.
        else if (p.vers === "fuite" || p.vers === "ronde") { t = place; nPlace++; }
        else if (pleinAir && pleinAir.has(p.vers)) { t = place; nPlace++; }
        else {
          t = toit; nToit++;
          const s = p.vers || "quelque part";
          portes.set(s, (portes.get(s) || 0) + 1);
        }
        t.set(m, (t.get(m) || 0) + 1);
        // Le verbe, tiré des deux mêmes champs qui viennent de décider la
        // colonne. `fuite` et `ronde` d'abord : ce sont les seuls qu'on ne
        // pardonnerait pas de perdre.
        const verbe = p.vers === "fuite" ? "fuient"
          : p.vers === "ronde" ? "en ronde"
          : p.quoi === "chez" ? "chez eux"
          : p.quoi === "route" ? "en chemin vers " + (p.vers || "quelque part")
          : "à " + (p.vers || "l'abri");
        let f = font.get(verbe);
        if (!f) font.set(verbe, f = new Map());
        f.set(m, (f.get(m) || 0) + 1);
      }
    }
    const trier = (t) => [...t.entries()].sort((a, b) => b[1] - a[1]);
    // Ceux qu'on croise sont ceux de la rue ET ceux de la place : c'est le
    // même geste — on passe devant eux et ils lèvent la tête.
    const croises = new Map(rue);
    for (const [m, n] of place) croises.set(m, (croises.get(m) || 0) + n);
    return {
      rayon: R, jour, minute: Math.round(min),
      // ce qu'on RENCONTRE
      rue: nRue, place: nPlace, croises: nRue + nPlace,
      metiers: trier(croises),
      // CE QU'ILS FONT — du plus nombreux au plus rare, chaque verbe avec le
      // détail des métiers qui s'y trouvent. C'est la seule ligne qui dise une
      // ACTION plutôt qu'un état, et donc la seule dont un récit puisse partir.
      font: [...font.entries()]
        .map(([v, m]) => [v, [...m.entries()].sort((a, b) => b[1] - a[1]),
                          [...m.values()].reduce((s, n) => s + n, 0)])
        .sort((a, b) => b[2] - a[2]),
      // ce qu'on peut aller CHERCHER, et par quelle porte
      toit: nToit, portes: trier(portes), metiers_toit: trier(toit),
      // l'ambiance, et rien de plus
      chez: nChez,
    };
  }

  // ---- le dessin -----------------------------------------------------------
  // UN SUR N, ET N SUIT L'APPROCHE. Au cadrage de la ville entière, un habitant
  // vaut un pixel : les dessiner tous donne du grain, pas une foule. On en
  // saute donc d'autant plus qu'on est loin — c'est la même règle qu'en
  // volume, et elle ne s'optimise pas, elle évite le calcul.
  // ON NE BAISSE PAS LE CHIFFRE, ON PLAFONNE CE QU'ON DESSINE.
  //
  // On a sauté un corps sur trois, puis on a essayé des secteurs : les deux
  // mentaient à leur façon. Le saut disait « il y a trois fois moins de
  // monde » ; les carrés donnaient une carte de chaleur qui n'est pas un plan
  // de ville — on ne repère pas une rue dans un dégradé.
  //
  // Il ne reste donc qu'une représentation, la bonne : UN POINT PAR PERSONNE,
  // tous, avec la couleur de là où ils vont. Le seul garde-fou est un plafond
  // en dur sur ce qui est À L'ÉCRAN — ce qui coûte, c'est le point qu'on trace,
  // pas l'habitant qui vit hors du cadre. Le hors-champ est donc écarté avant
  // d'être compté, ce qui plafonne le dessin et allège le calcul du même geste.
  // Soixante mille disques par image faisaient ramer le glissé : le plafond
  // descend à dix-huit mille, ce qui tient largement le soixantième de seconde
  // et reste très au-dessus de ce qu'un quartier porte à n'importe quelle
  // heure. Il n'est atteint qu'au cadrage de la ville entière, aux heures de
  // pointe — et quand il l'est, LE COMPTEUR LE DIT au lieu de faire passer un
  // chiffre tronqué pour le vrai.
  const MAX_ECRAN = 18000;

  // Le nuage, EN MÈTRES : ce que le calcul produit, ce que le dessin projette.
  // Les deux sont séparés parce qu'ils n'ont pas le même rythme — l'un suit la
  // ville, l'autre suit l'œil.
  let nuage = { tas: new Map(), dedans: [], total: 0 };

  // LE CALCUL SE FAIT PAR TRANCHES, ET LA PAGE NE GÈLE JAMAIS.
  //
  // Le premier passage est de loin le plus cher : les quatre cent mille
  // journées ne sont pas encore en cache, et chacune demande des chemins. Fait
  // d'un bloc, il fige l'onglet plusieurs secondes à l'ouverture — la carte est
  // là, le curseur ne répond plus, et l'on croit que la page est cassée.
  //
  // On se donne donc un BUDGET par image et l'on reprend où l'on s'était
  // arrêté. La foule apparaît par vagues au lieu de tomber d'un coup, ce qui
  // est plus honnête à regarder qu'un écran mort — et surtout le glissé, la
  // molette et les boutons répondent pendant tout ce temps.
  //
  // Le nuage PARTIEL est publié à chaque tranche : on dessine ce qu'on a. Un
  // compteur qui monte pendant deux secondes vaut mieux qu'un compteur juste
  // qui arrive après le gel.
  // LE BUDGET SUIT L'IMAGE, IL NE LA COMMANDE PAS.
  //
  // Neuf millisecondes fixes étaient neuf millisecondes prises À QUELQU'UN : le
  // plan, la chronique et le reste de la page se partagent les seize
  // millisecondes d'une image, et la foule en mangeait plus de la moitié. Coût
  // mesuré en régime chaud, cadrage ville entière : 12,5 ms de médiane par
  // image pour cette seule couche, avec des queues à 21 ms — c'est-à-dire une
  // image sur cinq perdue, et une foule qui avance par à-coups alors que son
  // calcul, lui, est parfaitement continu.
  //
  // On mesure donc l'image RÉELLE (l'écart entre deux passages de `image()`) et
  // l'on rend au dessin ce qu'il lui faut : quand l'image dépasse, la tranche
  // maigrit ; quand elle respire, elle regrossit. La foule met alors un peu plus
  // longtemps à se remplir, ce qui ne se voit pas — elle se remplit déjà par
  // vagues —, et elle cesse de faire sauter tout ce qui est autour.
  const BUDGET_MAX = 9, BUDGET_MIN = 2;
  let BUDGET = BUDGET_MAX;
  function doser(ecart) {
    if (!ecart || ecart > 400) return;   // un onglet revenu au premier plan
    if (ecart > 20) BUDGET = Math.max(BUDGET_MIN, BUDGET - 1);
    else if (ecart < 15) BUDGET = Math.min(BUDGET_MAX, BUDGET + 0.5);
  }
  let travail = null;                  // la tranche en cours, s'il y en a une

  function calculer(complet) {
    const rep = repere();
    if (!rep || !voirie || !cellules.length) return;
    // Un cadrage qui bouge invalide ce qu'on avait commencé : les positions
    // sont en mètres mais le tri à l'écran, lui, dépend de la vue.
    const vue = vueDe && vueDe();
    const sceau = vue ? vue.join(",") : "";
    // L'HEURE DE LA TRANCHE EST FIGÉE À SON OUVERTURE, ET ON NE LA JETTE PAS
    // PARCE QUE L'HORLOGE A AVANCÉ. `minute` se dérive de `performance.now()`
    // et change donc à CHAQUE image : comparer l'une à l'autre invalidait la
    // tranche en cours soixante fois par seconde, si bien qu'un calcul plus
    // long que le budget repartait de zéro sans jamais arriver au bout. On ne
    // repart que si le cadrage a bougé, ou si l'heure a SAUTÉ — ce qui, à 1:1,
    // ne peut venir que d'un recalage (↺) et jamais de l'écoulement du temps.
    if (travail && (travail.sceau !== sceau ||
                    Math.abs(travail.minute - minute) > 1))
      travail = null;
    if (!travail) {
      // `n` est tout ce qui est à l'écran (c'est lui qui bute sur le plafond),
      // `dh` seulement ce qui est sous le ciel — la barre distingue les deux.
      travail = { ic: 0, k: 0, n: 0, dh: 0, tas: new Map(), dedans: [],
                  sceau, minute, cout: 0 };
    }
    const t = travail;
    const L = toile.width, H = toile.height;
    const t0 = performance.now();
    let garde = 0;
    // ON NE COMMENCE PAS UN CHEMIN NEUF APRÈS L'ÉCHÉANCE DE LA TRANCHE. Voir la
    // note de `chemin()` dans journee.js : un seul A* à froid coûte jusqu'à
    // vingt-huit millisecondes, et ils arrivent en grappes — les voisins d'une
    // même cellule vont aux mêmes endroits. Sans cette borne, quatre d'affilée
    // tombent dans la même tranche et l'image passe à cent millisecondes :
    // mesuré à l'ouverture de l'échelle. Avec, le dépassement est borné à un
    // seul chemin. En régime chaud elle ne sert à rien — tout est en cache et
    // rien n'est différé. Le passage `complet` (rafraichir) la lève : là on veut
    // la vérité tout de suite, quitte à geler une fois.
    J.quotaChemins(complet ? null : BUDGET);
    // CEUX QUI SONT DEDANS COMPTENT AUSSI. La 3D les écartait, et elle avait
    // raison : un point posé au milieu d'un bâtiment y est noyé dans la pierre.
    // UN PLAN EST UNE COUPE — on voit très bien qui est dans quelle maison, et
    // c'est même ce qu'on vient y chercher. Les écarter ôtait treize mille
    // personnes sur seize mille à deux heures de l'après-midi.
    while (t.ic < cellules.length) {
      const cel = cellules[t.ic];
      while (t.k < cel.n) {
        const k = t.k++;
        // ON REGARDE L'HORLOGE SOUVENT, et c'est tout le sujet. Une personne
        // ne coûte rien la deuxième fois — mais la PREMIÈRE, sa journée se
        // calcule et ses chemins se cherchent sur le graphe.
        //
        // TOUTES LES TRENTE-DEUX, C'ÉTAIT TRENTE-DEUX DE TROP. Le raisonnement
        // tenait (la lecture de l'horloge est indolore, on l'espace) mais il
        // comptait sur des corps de coût comparable : au premier passage, trente-
        // deux journées froides d'affilée coûtent des dizaines de millisecondes,
        // et le budget ne veut plus rien dire. Mesuré à l'ouverture : des images
        // à 65 et 83 ms — quatre à cinq images perdues d'un coup, et c'est le
        // hoquet le plus visible du module.
        //
        // Toutes les quatre, le dépassement retombe à l'ordre d'UN chemin, et
        // les cent mille lectures d'horloge que coûte une passe complète se
        // comptent en trois millisecondes sur la passe entière.
        if (!complet && (++garde & 3) === 0 && performance.now() - t0 > BUDGET) {
          t.cout += performance.now() - t0;
          publier(t, false, false);
          rendreLesChemins();
          return;
        }
        // `t.minute` et non `minute` : un nuage doit être d'un SEUL instant.
        // Sur plusieurs images, la fin de la ville aurait été calculée à une
        // heure et son début à une autre — invisible sur un piéton, mais c'est
        // par là que les points se mettent à sauter.
        J.ou(cel, k, jour, t.minute, voirie, rangs, P);
        // Avant tout le reste : un corps différé n'a pas de position du tout.
        if (P.quoi === "differe") continue;
        // « chez » ne se dessine pas ; « differe » ne se dessine pas ENCORE —
        // son chemin n'est pas tracé, il entrera au nuage suivant.
        if (P.quoi === "chez" || P.quoi === "differe") continue;
        // ON DÉGAGE TOUT CE QUI EST SOUS LE CIEL — le piéton en chemin comme
        // le badaud du marché. Voir `aCiel` : c'est le toit qui décide, pas
        // le fait de marcher.
        const ciel = aCiel(P);
        if (ciel) degager(P);
        const x = rep.ox + P.x * rep.k, y = rep.oy + P.y * rep.ky;
        if (x < -8 || y < -8 || x > L + 8 || y > H + 8) continue;
        t.n++;
        if (t.n >= MAX_ECRAN) {
          t.cout += performance.now() - t0; espacer(t);
          publier(t, true, true); travail = null; rendreLesChemins(); return;
        }
        // Et l'on peint avec la même règle qu'on dégage : celui qui fuit était
        // compté sous un toit alors qu'il est accroupi au milieu de la rue —
        // `presents` le rangeait déjà dehors, le dessin non.
        // QUATRE NOMBRES, PAS DEUX : la position ET la vitesse. C'est ce qui
        // permet à la peinture de faire glisser cet homme entre deux calculs.
        if (!ciel) {
          t.dedans.push(P.x, P.y, P.vx || 0, P.vy || 0);
        } else {
          t.dh++;
          const c = TEINTES[P.vers] || DEFAUT;
          let tas = t.tas.get(c);
          if (!tas) t.tas.set(c, tas = []);
          tas.push(P.x, P.y, P.vx || 0, P.vy || 0);
        }
      }
      t.ic++; t.k = 0;
    }
    t.cout += performance.now() - t0; espacer(t);
    publier(t, t.n >= MAX_ECRAN, true);
    travail = null;
    rendreLesChemins();
  }

  // ON NE LAISSE JAMAIS UNE ÉCHÉANCE DERRIÈRE SOI. `journee.js` est un module,
  // donc UNE instance pour toute la page : la 3D (`monde/foule.js`) et les
  // témoins de `presents()` s'en servent aussi. Une échéance oubliée serait une
  // échéance PASSÉE pour eux, et tous leurs chemins neufs reviendraient `null`
  // sans qu'aucun d'eux ait rien demandé — une foule 3D qui se vide, et personne
  // pour faire le lien avec le plan 2D qu'on venait de fermer.
  function rendreLesChemins() { if (J) J.quotaChemins(); }

  // Ce que la tranche a coûté EN TOUT, images comprises. Mesuré depuis
  // `image()`, on ne voyait que le dernier morceau — neuf millisecondes — et
  // la période retombait à son plancher : la ville se recalculait donc en
  // permanence alors qu'un passage complet lui coûte dix fois ça.
  function espacer(t) {
    PERIODE = Math.max(250, Math.min(1000, t.cout * 4));
  }

  // ON NE REMPLACE JAMAIS UN NUAGE ENTIER PAR UN NUAGE PARTIEL.
  //
  // C'est la cause du scintillement, et elle est plus bête que le calcul :
  // quand une tranche dépassait son budget, on publiait les neuf
  // millisecondes qu'on venait de faire, et l'image suivante en publiait
  // neuf autres. Chaque image montrait donc un sous-ensemble DIFFÉRENT des
  // corps — les points s'allumaient et s'éteignaient d'une image à l'autre.
  // En pause, rien ne se recalculait et le défaut ne se voyait pas : d'où
  // l'impression qu'ils ne clignotent qu'en marchant.
  //
  // On garde donc à l'écran le dernier nuage COMPLET pendant que le suivant
  // se fabrique, et l'on n'échange qu'au bout. Le partiel ne sert plus qu'au
  // tout premier remplissage, là où il n'y a rien d'autre à montrer et où
  // voir la foule arriver par vagues vaut mieux qu'un écran vide.
  let entier = false;                  // le nuage affiché est-il achevé
  function publier(t, tronque, fini) {
    if (!fini && entier) return;
    entier = !!fini;
    nuage = { tas: t.tas, dedans: t.dedans, total: t.n, dh: t.dh, tronque,
              partiel: !fini, minute: t.minute };
    compter(t.dh, t.n - t.dh, tronque);
  }

  function peindre() {
    if (!ctx || !toile.width) return;
    ctx.clearRect(0, 0, toile.width, toile.height);
    const rep = repere();
    if (!rep) return;
    const dpr = window.devicePixelRatio || 1;
    // UN POINT DE DEUX PIXELS SUR UN FOND CLAIR N'EST PAS UN POINT, C'EST DU
    // BRUIT. Le plancher était à 1,1 pixel : à l'échelle de la ville, la foule
    // était bien dessinée et pourtant invisible — on cherchait la panne dans le
    // calcul alors qu'elle était dans la taille. Trois pixels de côté, c'est le
    // minimum pour qu'un habitant se voie sur du beige.
    const r = Math.max(1.6 * dpr, Math.min(3.2 * dpr, rep.k * .9));
    const L = toile.width + 8, H = toile.height + 8;
    // TOUT EST ROND, et tout se trace en UN SEUL CHEMIN par couleur : on
    // enchaîne les arcs dans le même `beginPath` et l'on remplit une fois.
    // C'est ce qui rend le disque abordable là où on le croyait trop cher —
    // le coût d'un canvas est dans le nombre d'appels de remplissage, pas dans
    // le nombre de courbes. Le `moveTo` avant chaque arc est obligatoire :
    // sans lui, le chemin relie les points entre eux et l'on peint une toile
    // d'araignée à la place d'une foule.
    // LA PEINTURE AVANCE LES GENS ELLE-MÊME, et c'est ce qui rend une foule
    // calculée quatre fois par seconde regardable à soixante images.
    //
    // Le calcul est cher, le dessin ne l'est pas : on ne peut pas replacer
    // quatre cent mille corps à chaque image, mais on peut les faire GLISSER.
    // Chaque point porte donc sa vitesse en mètres par minute, et l'on
    // extrapole du temps écoulé depuis l'instant du nuage. Un piéton avance de
    // sept centimètres entre deux images : personne ne voit une extrapolation
    // de cet ordre, tout le monde voit le bond d'un mètre qu'elle remplace.
    //
    // BORNÉ, parce qu'extrapoler est un mensonge qui se paie au coin de rue :
    // si la passe suivante tarde — un cadrage large, un onglet qui rame —, on
    // fige plutôt que d'envoyer tout le monde tout droit à travers la ville.
    // Un dixième de minute, c'est six secondes et sept mètres de marche.
    const dt = Math.max(0, Math.min(.1, minute - (nuage.minute || minute)));
    const ronds = (pts, ray) => {
      ctx.beginPath();
      for (let i = 0; i < pts.length; i += 4) {
        const x = rep.ox + (pts[i] + pts[i + 2] * dt) * rep.k,
              y = rep.oy + (pts[i + 1] + pts[i + 3] * dt) * rep.ky;
        if (x < -8 || y < -8 || x > L || y > H) continue;
        ctx.moveTo(x + ray, y);
        ctx.arc(x, y, ray, 0, 6.2832);
      }
      ctx.fill();
    };
    if (nuage.dedans.length) {
      // Assez marqués pour se voir sur un toit : à 45 % ils étaient là et ne se
      // distinguaient pas du bâti, ce qui revenait à ne pas les dessiner aux
      // heures où la ville est au travail.
      ctx.globalAlpha = .75;
      ctx.fillStyle = DEDANS;
      ronds(nuage.dedans, Math.max(1.4, r * .9));
      ctx.globalAlpha = 1;
    }
    for (const [couleur, pts] of nuage.tas) {
      ctx.fillStyle = couleur;
      ronds(pts, r);
    }
  }

  // ON NE RECALCULE PAS QUATRE CENT MILLE JOURNÉES SOIXANTE FOIS PAR SECONDE.
  // Un homme marche à soixante-dix mètres par minute : entre deux images il a
  // avancé d'un millimètre. Refaire le calcul à chaque image coûtait cent
  // soixante-cinq millisecondes pour un déplacement invisible — c'est-à-dire
  // six images par seconde pour rien.
  // On recalcule donc quatre fois par seconde, et l'on REDESSINE à chaque
  // image : redessiner ne coûte rien, et c'est ce qui garde le glissé fluide.
  // ET LA PÉRIODE SE RÈGLE TOUTE SEULE. Recalculer la ville entière coûte cent
  // quatre-vingts millisecondes ; un quartier en coûte cinq. Une période fixe
  // serait donc soit trop lente de près, soit ruineuse de loin. On mesure ce
  // que le dernier calcul a coûté et l'on espace le suivant d'autant — jamais
  // moins d'un quart de seconde, jamais plus d'une. Personne ne peut le voir :
  // à un mètre par seconde, un piéton avance d'un pas.
  let PERIODE = 250;
  let dernier = -1e9;
  // LA VILLE EST PEUPLÉE MÊME À L'ARRÊT. L'horloge démarre en pause — et l'on
  // ne calculait le nuage que lorsqu'elle tournait : tant que personne n'avait
  // appuyé sur ▶, la carte n'affichait RIEN, et l'on croyait la couche cassée.
  // Une ville en pause n'est pas une ville vide : c'est une ville arrêtée sur
  // une minute, et cette minute-là a ses habitants dans ses rues.
  let sale = true;
  let avantImage = 0;
  function image() {
    // Ce que la DERNIÈRE image a réellement coûté, tout compris — la foule, le
    // plan, la chronique, le navigateur. C'est le seul chiffre qui dise si l'on
    // a de la place pour calculer, et c'est lui qui règle la tranche.
    const t0i = performance.now();
    if (avantImage) doser(t0i - avantImage);
    avantImage = t0i;
    horloge();
    // L'HEURE S'AFFICHE MÊME QUAND ON NE PEINT RIEN. Une carte repliée n'a pas
    // de largeur, donc pas de dessin — mais l'horloge, elle, tourne quand même,
    // et une barre restée sur « — » se lit comme un bouton mort.
    montre();
    const vue = vueDe && vueDe();
    if (vue) charger(vue);
    const t = performance.now();
    // En pause, rien ne bouge dans la ville : on ne recalcule pas du tout, et
    // la boucle ne coûte plus que son dessin.
    // Une tranche entamée se poursuit à CHAQUE image, sans attendre la
    // période : c'est ce qui fait apparaître la foule en une seconde au lieu
    // de la faire attendre le prochain battement.
    if (travail || sale || (marche && t - dernier > PERIODE)) {
      if (!travail) { dernier = t; sale = false; }
      calculer();                      // la période se règle dans `espacer`
    }
    peindre();
    boucle = requestAnimationFrame(image);
  }

  // ---- la barre ------------------------------------------------------------
  let barre = null, lecture = null, compte = null;
  function batirBarre() {
    barre = document.createElement("div");
    barre.className = "cv-foule-barre";
    barre.innerHTML =
      '<button class="cv-f-jouer" title="Lancer ou arrêter l\'horloge">▶</button>' +
      '<span class="cv-f-heure">—</span>' +
      '<span class="cv-f-compte"></span>' +
      '<button class="cv-f-caler" title="Revenir à l\'heure de la partie">↺</button>';
    lecture = barre.querySelector(".cv-f-heure");
    compte = barre.querySelector(".cv-f-compte");
    barre.querySelector(".cv-f-jouer").addEventListener("click", (e) => {
      e.stopPropagation();
      basculer();
    });
    barre.querySelector(".cv-f-caler").addEventListener("click", (e) => {
      e.stopPropagation();
      reprendreHeure();
    });
    // Un clic sur la barre ne doit pas glisser la carte ni penser à un lieu.
    ["pointerdown", "wheel", "dblclick"].forEach((t) =>
      barre.addEventListener(t, (e) => e.stopPropagation()));
    hote.appendChild(barre);
  }

  function montre() {
    if (lecture) lecture.textContent = hhmm(Math.floor(minute));
  }

  // Le compte n'est pas le nombre de points : c'est ce qu'ils REPRÉSENTENT. Un
  // sur huit dessiné au cadrage large, c'est huit fois plus de monde dehors, et
  // c'est ce chiffre-là qui veut dire quelque chose. On ne le réécrit que
  // lorsqu'il a franchement bougé — un nombre qui change à chaque image ne se
  // lit pas, il clignote.
  // « DEHORS » NE VOULAIT PAS DIRE DEHORS. Le compteur affichait `t.n`, qui est
  // TOUT ce que le cadrage contient — et depuis qu'on dessine aussi les gens
  // sous leur toit (un plan est une coupe), c'était en grande partie des gens
  // chez eux. D'où cinq cent dix-huit annoncés « dehors » pour une vingtaine de
  // marcheurs visibles dans la rue : les cinq cents autres étaient là, pâles,
  // posés sur leurs maisons, et personne ne les compte comme des passants.
  //
  // Les deux nombres n'ont pas le même sens et ne servent pas à la même chose —
  // c'est écrit en tête de `presents()` : dehors est de la RENCONTRE, dedans
  // n'est que de l'ambiance. On les dit donc séparément.
  let dernierDh = -1, dernierDd = -1;
  function compter(dh, dd, tronque) {
    if (!compte) return;
    // Un nombre qui change à chaque image ne se lit pas, il clignote : on ne
    // réécrit que s'il a franchement bougé. LE PLANCHER ÉTAIT À QUARANTE, ce
    // qui convenait aux dix-huit mille de la pleine ville et gelait tout à
    // l'échelle de la rue — de vingt à cinquante passants, aucun changement
    // n'était jamais « franc ». Il suit maintenant l'ordre de grandeur.
    const fige = (a, b) => Math.abs(a - b) <= Math.max(2, b * .04);
    if (!tronque && fige(dh, dernierDh) && fige(dd, dernierDd)) return;
    dernierDh = dh; dernierDd = dd;
    // « et plus » : on a cessé de compter avant la fin. Mieux vaut le dire que
    // laisser croire que la ville tient en dix-huit mille personnes.
    const n = (v) => v.toLocaleString("fr-FR");
    compte.textContent = (dh || dd)
      ? n(dh) + " dehors" + (dd ? " · " + n(dd) + " sous un toit" : "") +
        (tronque ? " et plus" : "")
      : "";
  }

  function basculer() {
    marche = !marche;
    sale = true;
    if (marche) { min0 = minute; jour0 = jour; t0 = performance.now(); }
    if (barre) barre.querySelector(".cv-f-jouer").textContent = marche ? "⏸" : "▶";
    if (barre) barre.classList.toggle("marche", marche);
  }

  function reprendreHeure() {
    return fetch("/carte").then((r) => r.json()).then((d) => {
      caler(d.date);
      sale = true;
      if (marche) t0 = performance.now();
    }).catch(() => {});
  }

  // ---- l'attelage ----------------------------------------------------------
  // `poser` est appelé par carte-ville.js après chaque redessin du plan. Les
  // modules du monde sont chargés à la PREMIÈRE fois seulement : ce sont un
  // demi-mégaoctet de voirie et le manifeste des corps, qu'on ne paie pas tant
  // que personne n'a ouvert l'échelle de la ville.
  let pret = null, rate = null;
  function poser(h, donneVue, opts) {
    // Une fois qu'on sait qu'il n'y a pas de foule ici, on ne remonte pas une
    // barre morte à chaque redessin du plan.
    if (rate) return Promise.resolve(false);
    hote = h; vueDe = donneVue;
    source = (opts && opts.source) || source;
    if (!toile) {
      toile = document.createElement("canvas");
      toile.className = "cv-foule";
      ctx = toile.getContext("2d");
    }
    // Le plan se réécrit à chaque `dessiner()` : la toile et la barre en
    // sortent, il faut les remettre. Elles gardent leur état — l'horloge n'est
    // pas remise à zéro parce qu'on a changé de salle.
    if (toile.parentNode !== hote) hote.appendChild(toile);
    if (!barre) batirBarre();
    else if (barre.parentNode !== hote) hote.appendChild(barre);
    ajuster();
    if (!pret) pret = amorcer();
    return pret;
  }

  async function amorcer() {
    try {
      G = await import("/modules/monde/gens.js");
      J = await import("/modules/monde/journee.js");
      manif = await G.manifeste(source);
      rangs = J.rangs(manif);
      const table = await J.table(source);
      pleinAir = new Set(table.plein_air || table.services || []);
      await reprendreHeure();
      voirie = await J.voirie(source);
      // Le masque est un confort, pas une dépendance : s'il manque, la foule
      // marche comme avant plutôt que de ne pas marcher du tout.
      try {
        const m = (await (await fetch(source + "/plan2d")).json()).masque;
        if (m) {
          const buf = await (await fetch(source + "/masque")).arrayBuffer();
          masque = { nx: m.nx, ny: m.ny, pas: m.pas, bits: new Uint8Array(buf) };
        }
      } catch (e) { masque = null; }
      if (!boucle) boucle = requestAnimationFrame(image);
      if (window.ResizeObserver) new ResizeObserver(ajuster).observe(hote);
      return true;
    } catch (e) {
      // Un lieu sans corps n'a pas de foule : on retire la barre plutôt que de
      // laisser un bouton qui ne fait rien. MAIS ON LE DIT — une couche qui
      // disparaît sans un mot se cherche une heure, et c'est exactement ce qui
      // vient d'arriver en la branchant.
      console.warn("foule2d : pas de foule ici —", e);
      rate = e;
      if (barre) barre.remove();
      barre = null;
      if (toile) toile.remove();
      toile = null;
      return false;
    }
  }

  // Recadrer, c'est REPEINDRE, pas seulement retailler la toile. Sans ça, un
  // glissé de carte pendant que l'horloge est en pause laisse les gens là où
  // ils étaient à l'écran : le plan bouge sous une foule immobile, et l'on voit
  // des habitants traverser les murs. `requestAnimationFrame` ne rattrape rien
  // ici — en pause, il n'y a pas d'image suivante.
  // ET C'EST AUSSI RECOMPTER. Le nuage est trié À L'ÉCRAN (`calculer` écarte
  // tout ce qui tombe hors de la toile, et c'est ce tri qui donne le compte) ;
  // le dessin, lui, écarte au cadrage COURANT à chaque image. Tant que
  // recadrer ne salissait pas, les deux se séparaient dès qu'on approchait :
  // la barre annonçait les cinq cents personnes du cadrage d'avant pendant
  // qu'on en voyait vingt dans la rue où l'on venait de descendre. En marche
  // ça se rattrapait à la première période ; EN PAUSE, jamais — et l'horloge
  // démarre en pause. Un chiffre faux qui ne se corrige pas est pire que pas
  // de chiffre.
  // Le repeint attend l'image, le retaillage non :
  // `carte-ville` appelle ceci depuis `pointermove`, qui n'est
  // pas cadencé sur l'écran, et l'on repeignait donc la foule entière plusieurs
  // fois par image affichée pendant qu'on tire le plan. `sale` reste posé tout
  // de suite : c'est un drapeau que la prochaine image consomme une seule fois,
  // quel que soit le nombre de mouvements de souris qui l'ont levé.
  function recadrer() { ajuster(); sale = true; if (!boucle) peindre(); }

  // Reprendre l'heure, basculer, changer de salle : autant de raisons de
  // replacer tout le monde avant la prochaine image.
  function salir() { sale = true; }
  function arreter() {
    if (boucle) cancelAnimationFrame(boucle);
    boucle = 0; marche = false;
  }

  // L'heure se DÉRIVE du temps réel : la demander la met à jour au passage,
  // sinon elle ne vaut que ce que la dernière image en a fait — et l'appelant
  // qui la lit sans dessiner (une scène, un test) lirait une heure figée.
  // De quoi savoir, depuis la console, ce que la carte voit vraiment : combien
  // de cellules sont chargées, combien de corps elles portent, quelle heure il
  // est, et quelle taille font les points à l'écran. Une foule invisible a
  // toujours une de ces cinq causes, et sans ce relevé on les cherche à
  // l'aveugle.
  function etat() {
    const rep = repere();
    let corps = 0;
    for (const c of cellules) corps += c.n;
    return {
      cellules: cellules.length, corps,
      heure: hhmm(Math.floor(minute)), minute, jour, marche,
      dehors: nuage.dh || 0, aEcran: nuage.total,
      points: nuage.dedans.length / 4 +
        [...nuage.tas.values()].reduce((n, t) => n + t.length / 4, 0),
      toile: toile ? [toile.width, toile.height] : null,
      vue: vueDe && vueDe(),
      metresParPixel: rep ? +(1 / rep.k).toFixed(2) : null,
      periode: PERIODE, budget: +BUDGET.toFixed(1), pret: !!voirie, plafond: MAX_ECRAN,
      partiel: !!travail, tronque: !!nuage.tronque,
    };
  }

  return { poser, recadrer, salir, arreter, basculer, etat, presents,
           // UNE tranche de calcul, puis le dessin : ce que fait une image de
           // la boucle. C'est par là qu'on mesure si la page peut geler.
           tranche: () => { horloge(); montre();
                            const v = vueDe && vueDe(); if (v) charger(v);
                            calculer(); peindre(); },
           heure: () => { horloge(); return minute; },
           // une image tout de suite, sans attendre la boucle : le glissé en
           // pause s'en sert, et c'est aussi par là qu'on vérifie le module
           // dans un navigateur qui ne composite pas.
           rafraichir: () => { horloge(); montre(); const v = vueDe && vueDe();
                               if (v) charger(v);
                               dernier = performance.now(); travail = null; calculer(true);
                               peindre(); } };
})();
