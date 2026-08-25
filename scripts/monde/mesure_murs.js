// -*- coding: utf-8 -*-
/**
 * MESURE DES MURS — combien d'hommes marchent dans les maisons, et lesquels.
 *
 *     node scripts/monde/mesure_murs.js
 *     node scripts/monde/mesure_murs.js --hommes 400 --duree 300
 *     node scripts/monde/mesure_murs.js --porte "La porte du Roi" --tous 2
 *     node scripts/monde/mesure_murs.js --deroute 80 --deroute-a 300
 *
 * POURQUOI CE FICHIER EXISTE. Le défaut est connu et n'a jamais été chiffré :
 * `bataille2d.js` charge un masque du bâti juste (`sousToit`), tient la fonction
 * qui dirait « ce point est-il libre ? » (`libreEn`) — et ne l'appelle QUE pour
 * alimenter un signal d'observation. La locomotion, `versLe()`, finit sur
 * `h.x += (dx/d)*pas` sans un seul test : vingt et un sites d'appel, aucune
 * collision. Un seul état a été réparé, la marche au donjon, qui roule sur un
 * rail d'A* ; ses commentaires citent une mesure d'avant le rail — « 46 % des
 * vivants à plus de huit mètres de toute rue » — et c'est le seul chiffre que
 * la maison possède sur le sujet.
 *
 * CE FICHIER NE RÉPARE RIEN, ET C'EST VOULU. Il ne touche pas une ligne du
 * module. Il ne dit pas ce qu'il faut faire : il dit COMBIEN, OÙ et PAR QUEL
 * ÉTAT. Sans cette ventilation, on ne sait pas s'il faut réparer un état (la
 * déroute) ou poser un test dans `versLe` (vingt et un appelants) — et l'on
 * tranche alors par préférence d'architecture, ce qui est la façon la plus sûre
 * de payer cher une réparation qui ne mord sur rien.
 *
 * SIX MESURES, ET LES QUATRE DERNIÈRES SONT CELLES QU'ON OUBLIE.
 *
 *   1. LA PART DES HOMMES DANS LE BÂTI, au fil de la nuit et en fin de nuit,
 *      ventilée par état et par camp. C'est le compte brut ; il ne suffit pas.
 *   2. LA PROFONDEUR DE L'INFRACTION. Un homme à un mètre dans un mur frôle un
 *      angle ; un homme à quinze mètres est au milieu d'un pâté de maisons, et
 *      ce ne sont pas les mêmes réparations. D'où une DISTRIBUTION et jamais
 *      une moyenne — la moyenne d'un frôlement et d'une traversée ne décrit ni
 *      l'un ni l'autre.
 *   3. LES ÉPISODES, relevés à chaque pas et non à chaque seconde. Un homme
 *      qui traverse une maison en quatre secondes et un homme qui campe dedans
 *      trois minutes pèsent le même poids dans un compte d'instants, et ce ne
 *      sont pas du tout les mêmes fautes. On compte donc les ENTRÉES, leur
 *      durée, et le plus loin qu'on ait été poussé pendant le séjour.
 *   4. LA DISTANCE À LA RUE LA PLUS PROCHE, pour être comparable aux 46 %.
 *      Ce n'est pas la profondeur : une cour, un jardin, une grève sont libres
 *      de bâti ET loin de toute rue. Marcher là n'est pas traverser un mur,
 *      mais c'est marcher où aucune colonne ne passerait.
 *   5. PAR QUELLE BRANCHE DE CODE IL EST ENTRÉ. `h.branche` est la phrase que
 *      le module s'écrit à lui-même pour dire quelle branche de `soldat()`
 *      vient de le conduire : la relever à l'instant de l'entrée NOMME le
 *      chemin fautif au lieu de le déduire. Avec `h.vit` et `h.presse`, elle
 *      tranche la seule question qui décide de la réparation — un homme entré
 *      À L'ARRÊT n'a pas marché dans le mur, il y a été poussé par `pousser()`
 *      (l. 2068, 2083, 2086), qui déplace les corps sans passer par `versLe`.
 *   6. CE QUI N'A PAS EU LIEU. Un état jamais atteint n'est pas un état sain :
 *      c'est un état non mesuré, et le tableau les affiche pareil. On recense
 *      donc à pleine cadence qui est passé par quoi, on le DIT, et l'on se
 *      donne de quoi provoquer ce qui manque (`--deroute`). S'y ajoute le
 *      relevé de la couche 1, à qui la déroute appartient désormais tout
 *      entière : si ses jambes ne disent jamais « fuite », le zéro fuyard des
 *      cuissons récentes n'est pas une bataille sereine, c'est une panne.
 *
 * DEUX MASQUES, PARCE QUE LE MASQUE EN CONTIENT DEUX. `plan_ville.py` grave le
 * bâti PUIS la courtine (`graver_courtine`, les sept portes laissées en trous).
 * Un homme « sous toit » peut donc être dans une maison ou dans les six mètres
 * d'épaisseur du rempart — et devant une porte qu'on enfonce, la moitié de la
 * troupe est sur la muraille. Confondre les deux ferait passer sept casseurs de
 * porte pour sept hommes égarés dans un quartier. On rasterise donc la
 * courtine à part, depuis `plan.rempart`, et l'on compte les deux séparément.
 *
 * COMMENT ON MESURE, ET POURQUOI C'EST EXACT. Le masque est un bit par mètre
 * carré (5280 × 3600). On en tire DEUX cartes de distance exactes, par la
 * transformée séparable de Felzenszwalb–Huttenlocher : la distance de chaque
 * point au vide le plus proche (c'est la profondeur), et la distance de chaque
 * point à la rue la plus proche (les axes de `voirie` rasterisés). Deux passes
 * en O(n) sur dix-neuf millions de cellules, et l'on répond ensuite à chaque
 * relevé par un accès tableau. Une recherche en anneau par homme et par relevé
 * aurait coûté le même prix pour un résultat approché.
 *
 * IL EMPRUNTE SON AMORÇAGE AU FOUR, IL NE LE RECOPIE PAS. `planter()`, la liste
 * `CHAINE` et `chargerBataille()` sont lus dans `scripts/monde/sac.js` et
 * évalués tels quels — c'est le patron de `ecrans/modules/bataille/
 * banc-moteur.js`, et la seule façon qu'un morceau découpé demain entre dans la
 * mesure le jour où il entre dans le four.
 *
 * NI PEUPLE NI TOURNÉE, et ce n'est pas une économie. `sac.js` lit le jour et
 * la minute EN DIRECT dans `etat/monde.json` pour promener ses habitants : une
 * cuisson avec la ville ne se reproduit pas d'une heure de partie à l'autre.
 * On monte la chaîne seule, à graine tenue, et deux lancements rendent les
 * mêmes chiffres.
 *
 * IL N'ÉCRIT RIEN. Ni dans `etat/`, ni dans `monde/`, ni de sac, ni de planche.
 * Une mesure qui laisse des fichiers derrière elle ne mesure plus ce qu'on
 * croit — c'est la règle que `sac.js` s'est déjà donnée pour ses planches.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { pathToFileURL } = require("url");

const ICI = path.dirname(path.dirname(__dirname));      // la racine du dépôt
const MODULES = path.join(ICI, "ecrans", "modules");
const SAC = path.join(ICI, "scripts", "monde", "sac.js");

// ---------------------------------------------------------------------------
// LA CONDITION
//
// Trois cents hommes et vingt minutes. Ce n'est pas une belle bataille, c'est
// une bataille SUFFISANTE : il faut que la colonne se forme dehors, que la
// porte tombe (elle tombe vers la centième seconde), que le rail se prenne,
// que le fer se touche, que le repli parte et que des coureurs courent —
// c'est-à-dire que les états voyageurs EXISTENT, puisque c'est eux qu'on vient
// ventiler. Cinq cents secondes ne suffisaient pas : le repli n'y apparaissait
// pas du tout, et l'on aurait lu son zéro comme une innocence.
//
// LES DÉFAUTS SONT CEUX DU RAPPORT, et c'est exprès : `node scripts/monde/
// mesure_murs.js` sans un argument doit rendre les chiffres qu'on a cités,
// sinon un chiffre cité n'est plus vérifiable par personne.
// ---------------------------------------------------------------------------
const DEFAUTS = { hommes: 300, duree: 1200, porte: "La porte de la Gadoue",
                  serveur: "http://localhost:3129", source: "/monde", tous: 4,
                  // ---- PROVOQUER CE QUI NE SE PRODUIT PLUS -----------------
                  // UN ÉTAT QU'ON NE VOIT PAS N'EST PAS UN ÉTAT SAIN : c'est un
                  // état non mesuré, et confondre les deux est la seule façon
                  // sûre de conclure de travers. Les sacs du disque le disent —
                  // `essai.reference` rend 435 fuyards, toutes les cuissons
                  // récentes en rendent ZÉRO. Or `deroute` est précisément le
                  // chemin qui va tout droit (l. 3214), donc celui qu'on vient
                  // ventiler. On se donne de quoi le faire exister à la main :
                  // `--deroute N` fait rompre N hommes à `--deroute-a` secondes,
                  // c'est-à-dire une fois la porte tombée et la colonne engagée
                  // dans la ville, là où une déroute a des maisons à traverser.
                  //
                  // C'EST DE LA MESURE, PAS UNE RÉPARATION. On pose un état
                  // depuis le dehors, sur des hommes du module, et l'on regarde
                  // où ils vont. Aucun fichier n'est touché. À zéro par défaut :
                  // la cuisson de référence doit rester celle du moteur nu.
                  deroute: 0, "deroute-a": 150 };
const PAS = 1 / 20;               // le pas du module, et il ne se règle pas ici

// ON NE COMPTE PAS COMME UNE FAUTE CE QUI EST VOULU. Deux états entrent dans un
// bâtiment exprès, et le module le dit lui-même : `piller` (l. 6559 : « il
// quitte la colonne pour une maison ») et `rentre` (l. 4060 : l'anneau de la
// garde se retire À L'INTÉRIEUR du Donjon quand il s'ouvre). Ils restent
// mesurés et affichés — on veut voir qu'ils sont bien dedans, c'est la preuve
// que le masque dit vrai — mais ils sortent des totaux de l'infraction.
const LEGITIMES = new Set(["pille", "rentre"]);

// Celui qui est tombé ne marche plus, et sa position est celle où on l'a
// laissé. Le compter, c'est faire enfler le chiffre au fil de la nuit pour une
// raison qui n'a rien à voir avec la locomotion — un mort dans un mur y est
// entré vivant, et il y a déjà été compté à ce moment-là.
const COUCHES = new Set(["mort", "blesse", "terre"]);

function args() {
  const a = process.argv.slice(2), o = Object.assign({}, DEFAUTS);
  for (let i = 0; i < a.length; i++) {
    const c = a[i].replace(/^--/, "");
    if (c in DEFAUTS) o[c] = a[++i];
  }
  o.hommes = +o.hommes; o.duree = +o.duree; o.tous = +o.tous;
  o.deroute = +o.deroute; o["deroute-a"] = +o["deroute-a"];
  return o;
}

// ---------------------------------------------------------------------------
// L'EMPRUNT AU FOUR — mot pour mot le geste de `banc-moteur.js`
// ---------------------------------------------------------------------------
const sacSrc = fs.readFileSync(SAC, "utf8");
function morceau(quoi, re) {
  const m = sacSrc.match(re);
  if (!m) throw new Error(
    "sac.js a changé de forme : « " + quoi + " » ne s'y retrouve plus.\n" +
    "  La mesure emprunte l'amorçage du four au lieu de le recopier ; elle ne\n" +
    "  devine pas. Rendez-lui son morceau, ou changez l'emprunt ici.");
  return m[0];
}
/* eslint-disable no-eval */
const CHAINE = eval(morceau("const CHAINE", /const CHAINE = \[[\s\S]*?\];/) + "\nCHAINE;");
const planter = eval("(" + morceau("function planter",
  /function planter\(base\) \{[\s\S]*?\n\}/) + ")");
const chargerBataille = eval("(" + morceau("function chargerBataille",
  /function chargerBataille\(\) \{[\s\S]*?\n\}/) + ")");
/* eslint-enable no-eval */

const empreinte = (f) => crypto.createHash("sha256")
  .update(fs.readFileSync(path.join(MODULES, f))).digest("hex").slice(0, 12);

// ===========================================================================
// LES CARTES DE DISTANCE
// ===========================================================================
//
// LE PLAFOND EST UNE QUESTION DE PRÉCISION, PAS DE PRUDENCE. On range les
// distances au carré dans un `Float32Array` de dix-neuf millions de cases : un
// entier y est EXACT jusqu'à 16,7 millions, et pas au-delà. Mille mètres au
// carré font un million — on reste donc dans l'exact partout, à condition de
// borner. Un point à plus de mille mètres de toute rue n'existe pas dans cette
// ville, et un homme à plus de mille mètres du vide n'existe nulle part.
const PLAFOND = 1e6;

/**
 * La transformée de distance à une dimension (Felzenszwalb–Huttenlocher).
 * `f` porte les valeurs de départ, `d` reçoit les distances au carré. Les
 * tampons `v` et `z` viennent de l'appelant pour ne rien allouer dans la
 * boucle — neuf mille appels par carte, c'est le genre d'allocation qui coûte
 * plus cher que le calcul.
 *
 * Tout y est en doubles : les valeurs intermédiaires (`f[q] + q*q`) montent à
 * vingt-huit millions, où le `Float32Array` de rangement ne serait plus exact.
 * On ne range en float32 qu'après avoir borné.
 */
function dt1d(f, n, d, v, z) {
  let k = 0;
  v[0] = 0; z[0] = -Infinity; z[1] = Infinity;
  for (let q = 1; q < n; q++) {
    let s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]);
    while (s <= z[k]) {
      k--;
      s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k]);
    }
    k++; v[k] = q; z[k] = s; z[k + 1] = Infinity;
  }
  k = 0;
  for (let q = 0; q < n; q++) {
    while (z[k + 1] < q) k++;
    d[q] = (q - v[k]) * (q - v[k]) + f[v[k]];
  }
}

/**
 * La carte des distances, en mètres, à l'ensemble des cellules-graines. La
 * grille fait un mètre par case — c'est celle du masque —, donc une distance
 * en cases EST une distance en mètres : aucun facteur d'échelle à traîner,
 * conformément au « true 1:1 » de la maison.
 */
function carteDistance(nx, ny, estGraine) {
  const g = new Float32Array(nx * ny);
  for (let k = 0; k < g.length; k++) g[k] = estGraine(k) ? 0 : PLAFOND;
  const nMax = Math.max(nx, ny);
  const f = new Float64Array(nMax), d = new Float64Array(nMax);
  const v = new Int32Array(nMax), z = new Float64Array(nMax + 1);
  // Les colonnes d'abord (le long de y), puis les lignes (le long de x). La
  // séparabilité de la distance euclidienne au carré est ce qui rend le calcul
  // linéaire ; c'est aussi ce qui oblige à garder l'exact entre les deux
  // passes, d'où un plafond haut plutôt qu'un plafond commode.
  for (let i = 0; i < nx; i++) {
    for (let j = 0; j < ny; j++) f[j] = g[j * nx + i];
    dt1d(f, ny, d, v, z);
    for (let j = 0; j < ny; j++) g[j * nx + i] = Math.min(PLAFOND, d[j]);
  }
  for (let j = 0; j < ny; j++) {
    const base = j * nx;
    for (let i = 0; i < nx; i++) f[i] = g[base + i];
    dt1d(f, nx, d, v, z);
    for (let i = 0; i < nx; i++) g[base + i] = Math.min(PLAFOND, d[i]);
  }
  // On range la RACINE une fois pour toutes : la lecture se fait des dizaines
  // de milliers de fois, la racine une seule.
  for (let k = 0; k < g.length; k++) g[k] = Math.sqrt(g[k]);
  return g;
}

// ---------------------------------------------------------------------------
// LES STATISTIQUES — des quantiles, jamais une moyenne
//
// La moyenne d'un frôlement d'angle et d'une traversée de pâté ne décrit ni
// l'un ni l'autre, et c'est très exactement la question qu'on nous pose. On
// range donc les valeurs et l'on lit dedans.
// ---------------------------------------------------------------------------
function quantile(tri, p) {
  if (!tri.length) return 0;
  const i = Math.min(tri.length - 1, Math.max(0, Math.round((tri.length - 1) * p)));
  return tri[i];
}
const m1 = (x) => x.toFixed(1).padStart(5) + " m";
const pc = (a, b) => (b ? (100 * a / b).toFixed(1) : "0.0").padStart(5) + " %";
const nb = (n) => n.toLocaleString("fr-FR");

// ===========================================================================
async function main() {
  const o = args();
  planter(o.serveur);
  const B = chargerBataille();

  const chaine = CHAINE.map((f) => ({ f, sha: empreinte(f) }));
  const ensemble = crypto.createHash("sha256")
    .update(chaine.map((c) => c.f + ":" + c.sha).join("|")).digest("hex").slice(0, 12);

  console.log("\nMESURE DES MURS — " + o.hommes + " hommes à « " + o.porte +
              " », " + o.duree + " s de bataille");
  console.log("  chaîne  : " + CHAINE.length + " fichiers, empreinte d'ensemble " +
              ensemble + "   (empruntée à scripts/monde/sac.js)");
  console.log("  graine  : " + (globalThis.window.BatailleHasard || {}).GRAINE +
              " · ni peuple ni tournée : la ville n'entre pas dans la condition");

  let t0 = Date.now();
  await B.preparer(o.source);
  console.log("  module  : prêt en " + ((Date.now() - t0) / 1000).toFixed(1) + " s");

  // ---- LE MASQUE DU BÂTI --------------------------------------------------
  // On le recharge pour nous : `sousToit` est interne au module et ne sort
  // jamais. La lecture des bits est celle d'`enterrer()` (l. 6405-6429),
  // recopiée volontairement — elle tient en quatre lignes, et la seule autre
  // voie serait de percer le module pour une mesure.
  t0 = Date.now();
  const plan = await (await fetch(o.source + "/plan2d")).json();
  const M = plan.masque;
  const bits = new Uint8Array(await (await fetch(o.source + "/masque")).arrayBuffer());
  const nx = M.nx, ny = M.ny, maille = M.pas, N = nx * ny;
  const cellule = (x, y) => {
    const i = (x / maille) | 0, j = (y / maille) | 0;
    if (i < 0 || j < 0 || i >= nx || j >= ny) return -1;
    return j * nx + i;
  };
  const bati = (k) => k >= 0 && ((bits[k >> 3] >> (k & 7)) & 1) === 1;
  let nBati = 0;
  for (let k = 0; k < N; k++) if (bati(k)) nBati++;

  // ---- LA COURTINE, À PART ------------------------------------------------
  // `plan.rempart.courtine` est le tracé SVG du mur, avec un `M` à chaque
  // interruption : ce sont les sept portes, que `graver_courtine` saute
  // exactement de la même façon. On rasterise à la même demi-épaisseur, et
  // l'on obtient de quoi distinguer « il est dans une maison » de « il est sur
  // le rempart » — sans quoi sept casseurs de porte passent pour sept hommes
  // égarés dans un quartier.
  const courtine = new Uint8Array(N);
  let nCourtine = 0;
  {
    const demi = (plan.rempart && plan.rempart.epaisseur_m || 6) / 2;
    const d = (plan.rempart && plan.rempart.courtine) || "";
    for (const sous of d.split("M").slice(1)) {
      const pts = sous.split("L").map((s) => s.trim().split(/[\s,]+/).map(Number))
                      .filter((p) => p.length >= 2 && isFinite(p[0]) && isFinite(p[1]));
      for (let i = 1; i < pts.length; i++) {
        const [ax, ay] = pts[i - 1], [bx, by] = pts[i];
        const L = Math.hypot(bx - ax, by - ay);
        if (L < 1e-6) continue;
        const ux = (bx - ax) / L, uy = (by - ay) / L;
        // La boîte du segment, élargie de la demi-épaisseur, puis le test de
        // projection : c'est `graver_courtine` transposé, au mètre près.
        const i0 = Math.max(0, Math.floor(Math.min(ax, bx) - demi));
        const i1 = Math.min(nx - 1, Math.ceil(Math.max(ax, bx) + demi));
        const j0 = Math.max(0, Math.floor(Math.min(ay, by) - demi));
        const j1 = Math.min(ny - 1, Math.ceil(Math.max(ay, by) + demi));
        for (let j = j0; j <= j1; j++) {
          const cy = j + .5 - ay;
          for (let i2 = i0; i2 <= i1; i2++) {
            const cx = i2 + .5 - ax;
            const t = cx * ux + cy * uy;
            if (t < 0 || t > L) continue;
            if (Math.abs(-cx * uy + cy * ux) > demi) continue;
            const k = j * nx + i2;
            if (!courtine[k]) { courtine[k] = 1; nCourtine++; }
          }
        }
      }
    }
  }
  // ---- DEDANS OU DEHORS LES MURS ------------------------------------------
  // SANS CETTE LIGNE-LÀ, LA MESURE DE LA RUE NE VEUT RIEN DIRE. L'assaut se
  // forme HORS les murs, où il n'y a par construction aucune rue de la voirie
  // de surface : compter ces hommes-là dans « à plus de huit mètres de toute
  // rue » ferait monter le chiffre de moitié sans qu'un seul homme ait traversé
  // quoi que ce soit. On sépare donc, et l'on ne compare que ce qui se compare.
  //
  // Comment : on regrave la courtine ÉPAISSE — huit mètres de demi-largeur au
  // lieu de trois —, ce qui referme les sept portes (des trous de six mètres),
  // puis l'on inonde depuis le bord du plan. Ce que l'eau n'atteint pas est
  // intra muros. C'est une fermeture morphologique, et c'est la seule façon
  // d'obtenir un dedans quand la seule chose qu'on ait est un mur troué.
  const intra = new Uint8Array(N);
  {
    const gros = new Uint8Array(N);
    const demi = 8;
    const d = (plan.rempart && plan.rempart.courtine) || "";
    for (const sous of d.split("M").slice(1)) {
      const pts = sous.split("L").map((s) => s.trim().split(/[\s,]+/).map(Number))
                      .filter((p) => p.length >= 2 && isFinite(p[0]) && isFinite(p[1]));
      for (let i = 1; i < pts.length; i++) {
        const [ax, ay] = pts[i - 1], [bx, by] = pts[i];
        const L = Math.hypot(bx - ax, by - ay);
        if (L < 1e-6) continue;
        const ux = (bx - ax) / L, uy = (by - ay) / L;
        const i0 = Math.max(0, Math.floor(Math.min(ax, bx) - demi));
        const i1 = Math.min(nx - 1, Math.ceil(Math.max(ax, bx) + demi));
        const j0 = Math.max(0, Math.floor(Math.min(ay, by) - demi));
        const j1 = Math.min(ny - 1, Math.ceil(Math.max(ay, by) + demi));
        for (let j = j0; j <= j1; j++) {
          const cy = j + .5 - ay;
          for (let i2 = i0; i2 <= i1; i2++) {
            const cx = i2 + .5 - ax;
            const tt = cx * ux + cy * uy;
            // Les bouts sont ARRONDIS (`tt` borné puis distance au point le
            // plus proche du segment) et non coupés net : deux tronçons qui se
            // touchent en angle laisseraient sinon un coin ouvert, et l'eau
            // passerait par là — une fuite d'un pixel suffit à noyer la ville.
            const s = Math.max(0, Math.min(L, tt));
            if (Math.hypot(cx - ux * s, cy - uy * s) > demi) continue;
            gros[j * nx + i2] = 1;
          }
        }
      }
    }
    const vu = new Uint8Array(N);
    const pile = new Int32Array(N);
    let n = 0;
    const pousser = (k) => { if (!vu[k] && !gros[k]) { vu[k] = 1; pile[n++] = k; } };
    for (let i = 0; i < nx; i++) { pousser(i); pousser((ny - 1) * nx + i); }
    for (let j = 0; j < ny; j++) { pousser(j * nx); pousser(j * nx + nx - 1); }
    while (n) {
      const k = pile[--n], i = k % nx, j = (k / nx) | 0;
      if (i > 0) pousser(k - 1);
      if (i < nx - 1) pousser(k + 1);
      if (j > 0) pousser(k - nx);
      if (j < ny - 1) pousser(k + nx);
    }
    let nIntra = 0;
    for (let k = 0; k < N; k++) if (!vu[k]) { intra[k] = 1; nIntra++; }
    console.log("  masque  : " + nx + " × " + ny + " à " + maille + " m — " +
                pc(nBati, N).trim() + " de la place est bâtie, dont " +
                nb(nCourtine) + " m² de courtine ; " + nb(nIntra) +
                " m² intra muros   (" + ((Date.now() - t0) / 1000).toFixed(1) + " s)");
  }

  // ---- LA VOIRIE ----------------------------------------------------------
  // La même que celle sur laquelle le module trace ses A* : on la demande à
  // `journee.js`, qui la tient en cache depuis que `preparer()` l'a chargée.
  // Pas un octet de réseau de plus, et surtout pas un second graphe.
  t0 = Date.now();
  const J = await import(pathToFileURL(path.join(MODULES, "monde", "journee.js")).href);
  const voirie = await J.voirie(o.source);
  const aretes = new Set();
  for (const [, nd] of voirie.noeuds) for (const l of nd.liens) aretes.add(l.arete);
  // On rasterise les AXES, et c'est délibéré : la mesure historique dit « à
  // plus de huit mètres de toute rue », pas « hors chaussée ». Comparer à autre
  // chose que ce qui a été mesuré alors, ce serait ne rien comparer du tout.
  const estRue = new Uint8Array(N);
  let nRue = 0;
  for (const a of aretes) {
    const t = a.trace;
    for (let i = 1; i < t.length; i++) {
      const p = t[i - 1], q = t[i];
      const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
      const n = Math.max(1, Math.ceil(L / 0.5));   // un point tous les 50 cm
      for (let s = 0; s <= n; s++) {
        const u = s / n;
        const k = cellule(p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u);
        if (k >= 0 && !estRue[k]) { estRue[k] = 1; nRue++; }
      }
    }
  }
  console.log("  voirie  : " + nb(aretes.size) + " arêtes, " + nb(nRue) +
              " cellules d'axe   (" + ((Date.now() - t0) / 1000).toFixed(1) + " s)");

  // ---- LES DEUX CARTES ----------------------------------------------------
  t0 = Date.now();
  const profondeur = carteDistance(nx, ny, (k) => !bati(k));      // vers le vide
  const distRue = carteDistance(nx, ny, (k) => estRue[k] === 1);  // vers l'axe
  console.log("  cartes  : deux transformées exactes en " +
              ((Date.now() - t0) / 1000).toFixed(1) + " s\n");

  // =========================================================================
  // LA CUISSON
  // =========================================================================
  t0 = Date.now();
  B.rejouer(o.porte, o.hommes);
  const corps = B.troupe();
  const nPas = Math.round(o.duree / PAS);
  const parReleve = Math.max(1, Math.round(o.tous / PAS));

  // Ce qu'on accumule. On garde les VALEURS et non des sommes : on veut des
  // quantiles, et un quantile ne se calcule pas sur une moyenne courante.
  const neuf = () => ({ vus: 0, intra: 0, maison: 0, courtine: 0, surRail: 0,
                        maisonSurRail: 0, prof: [], rue: [], qui: new Set() });
  const seaux = new Map();
  const seau = (clef) => {
    let e = seaux.get(clef);
    if (!e) seaux.set(clef, e = neuf());
    return e;
  };
  const parCamp = new Map();
  const seauCamp = (clef) => {
    let e = parCamp.get(clef);
    if (!e) parCamp.set(clef, e = neuf());
    return e;
  };

  const toutesProf = [], toutesRue = [];
  const courbe = [];
  const dedansJamais = new Set();
  let vusTotal = 0, maisonTotal = 0, courtineTotal = 0, horsPlan = 0;

  // ---- LA MISE EN PLACE, AVANT LE PREMIER PAS ------------------------------
  // LA QUESTION QUI CHANGE LA RÉPARATION. Un homme dans une maison peut y être
  // ENTRÉ EN MARCHANT — c'est la locomotion qui est en cause — ou y avoir été
  // POSÉ par `dresser`, et alors aucun test dans `versLe` n'y changera rien :
  // c'est le placement des postes qu'il faudrait corriger. On relève donc
  // l'instant zéro, avant que quiconque ait bougé d'un pouce.
  const poseDedans = new Uint8Array(corps.length);
  const posePar = new Map();
  for (let k = 0; k < corps.length; k++) {
    const h = corps[k], c = cellule(h.x, h.y);
    let e = posePar.get(h.etat + " · " + h.camp);
    if (!e) posePar.set(h.etat + " · " + h.camp, e = { n: 0, dedans: 0 });
    e.n++;
    if (c >= 0 && bati(c) && !courtine[c]) { poseDedans[k] = 1; e.dedans++; }
  }

  // ---- LES ÉPISODES, à chaque pas et non à chaque relevé -------------------
  // Un homme qui traverse une maison en quatre secondes et un homme qui campe
  // dedans trois minutes pèsent pareil dans un compte d'instants. On suit donc
  // chacun À PLEINE CADENCE — vingt fois par seconde, ce qui ne coûte qu'un
  // accès tableau — et l'on ferme un épisode quand il ressort : sa durée, le
  // plus loin où il a été poussé, et l'état qui l'a fait entrer.
  const dansDepuis = new Float64Array(corps.length).fill(-1);
  const profMax = new Float64Array(corps.length);
  const etatEntree = new Array(corps.length).fill(null);
  const surRailEntree = new Uint8Array(corps.length);
  // ---- PAR QUELLE PORTE IL EST ENTRÉ --------------------------------------
  // `h.branche` est la phrase que le module s'écrit à lui-même à chaque
  // battement pour dire quelle branche de `soldat()` vient de le conduire. La
  // relever à l'instant de l'entrée, c'est NOMMER le chemin de code fautif au
  // lieu de le déduire. Et `presse` avec `vit` tranchent la seule ambiguïté
  // qui reste : un homme entré à l'arrêt, coudes serrés, n'a pas marché dans
  // le mur — il y a été POUSSÉ par `pousser()`, qui déplace les corps
  // directement (l. 2068, 2083, 2086) sans jamais passer par `versLe`.
  const brancheEntree = new Array(corps.length).fill(null);
  const presseEntree = new Float64Array(corps.length);
  const vitEntree = new Float64Array(corps.length);
  const episodes = [];
  const fermer = (k, t) => {
    if (dansDepuis[k] < 0) return;
    episodes.push({ etat: etatEntree[k], camp: corps[k].camp,
                    debut: dansDepuis[k], duree: t - dansDepuis[k],
                    prof: profMax[k], rail: !!surRailEntree[k],
                    branche: brancheEntree[k], presse: presseEntree[k],
                    vit: vitEntree[k],
                    // Un séjour ouvert au tout premier pas n'est pas une
                    // entrée : c'est un homme qu'on a POSÉ là.
                    pose: !!poseDedans[k] && dansDepuis[k] <= PAS * 2 });
    dansDepuis[k] = -1;
  };

  // ---- LE RECENSEMENT DES ÉTATS, à pleine cadence -------------------------
  // « Cet état ne fait aucune infraction » et « cet état n'a jamais eu lieu »
  // se ressemblent comme deux gouttes d'eau dans un tableau, et ne veulent pas
  // du tout dire la même chose : le premier innocente un mécanisme, le second
  // dit qu'on ne l'a pas mesuré. On compte donc, vingt fois par seconde, qui
  // est passé par quoi — un état transitoire d'une demi-seconde (le coureur qui
  // part, l'homme qu'on rallie) est invisible à un relevé toutes les deux
  // secondes, et c'est justement celui-là qu'on cherche.
  //
  // On ne fait le compte des HOMMES qu'au changement d'état : `Set.add` vingt
  // fois par seconde et par homme coûtait plus cher que la bataille elle-même,
  // pour ajouter dix mille fois le même entier au même ensemble.
  const cens = new Map();
  const avant = new Array(corps.length).fill(null);
  const recenser = (etat, k) => {
    let c = cens.get(etat);
    if (!c) cens.set(etat, c = { pas: 0, qui: new Set() });
    c.pas++;
    if (avant[k] !== etat) { c.qui.add(k); avant[k] = etat; }
  };

  // ---- LA COUCHE 1, PARCE QUE LA DÉROUTE LUI APPARTIENT MAINTENANT --------
  //
  // POURQUOI ON MESURE ÇA DANS UN SCRIPT QUI PARLE DE MURS. Parce qu'un état
  // qui ne se produit jamais ne peut pas être ventilé, et que `deroute` est
  // l'état qu'on venait ventiler en premier. Or il n'existe plus que deux
  // chemins vers lui dans tout le module : la charrette du roi qui verse
  // (`survie()`, l. 2963) et `h.l1.jambes === "fuite"` (l. 3091). L'ancienne
  // morale — `morale`, `ROMPT`, `CHOC`, `SANG`, `REPRISE` — a été DÉPOSÉE au
  // profit de la couche (le commentaire l. 2939-2945 l'assume). Donc si les
  // jambes ne disent jamais « fuite », personne ne rompt de la nuit, et le
  // zéro fuyard des cuissons récentes n'est pas une bataille sereine : c'est
  // une branche morte.
  //
  // ON COMPTE PAR OBSERVATION, PAS PAR PAS. `h.l1` est un objet neuf à chaque
  // coup d'œil de l'homme (`oeil(h)`, quelques dixièmes de seconde), et il
  // demeure entre deux. Compter à 20 Hz compterait vingt fois le même
  // clignement. L'identité de l'objet dit exactement quand il y a du neuf.
  const L1 = { jambes: new Map(), bras: new Map(), obs: 0, sans: 0,
               empr: new Float64Array(21), sangFroid: new Float64Array(21),
               emprMax: 0, sangFroidMin: 1, emprHaut: 0, quiFuite: new Set(),
               quiSideration: new Set(), quiEmprHaut: new Set() };
  const l1Avant = new Array(corps.length).fill(null);
  const compter = (m, v, k) => {
    let e = m.get(v);
    if (!e) m.set(v, e = { n: 0, qui: new Set() });
    e.n++; e.qui.add(k);
  };

  let t = 0, forces = 0;
  for (let i = 0; i < nPas; i++) {
    B.pas(PAS);
    t += PAS;

    for (let k = 0; k < corps.length; k++) {
      const h = corps[k];
      if (h.tete || COUCHES.has(h.etat)) continue;
      if (!h.l1) { L1.sans++; continue; }
      if (h.l1 === l1Avant[k]) continue;      // pas de nouveau coup d'œil
      l1Avant[k] = h.l1;
      L1.obs++;
      compter(L1.jambes, String(h.l1.jambes), k);
      compter(L1.bras, String(h.l1.bras), k);
      if (h.l1.jambes === "fuite") L1.quiFuite.add(k);
      if (h.l1.jambes === "sidération") L1.quiSideration.add(k);
      const e = +h.l1.emprise || 0, r = +h.l1.sangFroid || 0;
      L1.empr[Math.max(0, Math.min(20, Math.round(e * 20)))]++;
      // `sangFroid` vit sur [−1, 1] : on le ramène sur [0, 1] pour le ranger,
      // et l'on redonne l'échelle vraie à l'affichage.
      L1.sangFroid[Math.max(0, Math.min(20, Math.round((r + 1) * 10)))]++;
      if (e > L1.emprMax) L1.emprMax = e;
      if (r < L1.sangFroidMin) L1.sangFroidMin = r;
      if (e > 0.6) { L1.emprHaut++; L1.quiEmprHaut.add(k); }
    }

    // ---- LA DÉROUTE PROVOQUÉE ----------------------------------------------
    // À l'heure dite, on fait rompre N hommes debout de l'assaut. On les prend
    // au hasard de l'ordre du tableau et non « les plus avancés » : on veut
    // mesurer le chemin d'un fuyard ordinaire, pas le pire cas choisi exprès.
    if (o.deroute > 0 && !forces && t >= o["deroute-a"]) {
      for (const h of corps) {
        if (forces >= o.deroute) break;
        if (h.camp !== "assaut" || COUCHES.has(h.etat) || h.tete || h.hors) continue;
        if (h.etat === "deroute" || LEGITIMES.has(h.etat)) continue;
        h.etat = "deroute"; h.noeud = undefined; forces++;
      }
      console.log("  (déroute provoquée : " + forces + " hommes rompent à " +
                  Math.round(t) + " s)");
    }

    for (let k = 0; k < corps.length; k++) recenser(corps[k].etat, k);

    // ---- à chaque pas : les épisodes ---------------------------------------
    for (let k = 0; k < corps.length; k++) {
      const h = corps[k];
      if (COUCHES.has(h.etat) || LEGITIMES.has(h.etat)) { fermer(k, t); continue; }
      const c = cellule(h.x, h.y);
      if (c < 0 || !bati(c)) { fermer(k, t); continue; }
      // ON NE COMPTE PAS LA COURTINE COMME UN ÉPISODE. Le rempart est un lieu
      // où l'on se bat pour de vrai — la porte est dedans — et un séjour de
      // trois minutes sur la muraille ne raconte pas la même faute qu'un
      // séjour de trois minutes dans une cuisine. Il est compté ailleurs,
      // séparément, où on peut le lire pour ce qu'il est.
      if (courtine[c]) { fermer(k, t); continue; }
      if (dansDepuis[k] < 0) {
        dansDepuis[k] = t; profMax[k] = 0;
        etatEntree[k] = h.etat; surRailEntree[k] = h.surVoie ? 1 : 0;
        brancheEntree[k] = h.branche || "—";
        presseEntree[k] = h.presse || 0;
        vitEntree[k] = h.vit || 0;
      }
      const p = profondeur[c];
      if (p > profMax[k]) profMax[k] = p;
    }

    // ---- au relevé : la ventilation ----------------------------------------
    // Toutes les `--tous` secondes, et non à chaque pas : ces tableaux gardent
    // chaque valeur pour en tirer des quantiles, et vingt relevés par seconde
    // en feraient des millions pour une précision qu'on n'utilise pas.
    if (i % parReleve !== 0) continue;
    let vus = 0, dansMaison = 0, dansCourtine = 0, leg = 0, dedansMurs = 0, rail = 0;
    const profIci = [], rueIci = [];
    for (let k = 0; k < corps.length; k++) {
      const h = corps[k];
      if (COUCHES.has(h.etat)) continue;
      const c = cellule(h.x, h.y);
      if (c < 0) { horsPlan++; continue; }       // hors du plan : on se tait
      const legitime = LEGITIMES.has(h.etat);
      const dedans = bati(c);
      const mur = dedans && courtine[c] === 1;
      const dansLaVille = intra[c] === 1;

      const e = seau(h.etat), ec = seauCamp(h.etat + " · " + h.camp);
      e.vus++; ec.vus++;
      if (h.surVoie) { e.surRail++; ec.surRail++; }
      // LA RUE NE SE MESURE QU'INTRA MUROS. Hors les murs il n'y a pas de rue,
      // et c'est vrai — le module le dit lui-même l. 3214. Compter la colonne
      // qui se forme dans les champs, c'est mesurer la campagne.
      const dr = distRue[c];
      if (dansLaVille) { e.intra++; ec.intra++; e.rue.push(dr); ec.rue.push(dr); }
      if (dedans) {
        const pr = profondeur[c];
        if (mur) { e.courtine++; ec.courtine++; }
        else {
          e.maison++; ec.maison++;
          e.prof.push(pr); ec.prof.push(pr);
          e.qui.add(k); ec.qui.add(k);
          if (h.surVoie) { e.maisonSurRail++; ec.maisonSurRail++; }
        }
      }
      if (legitime) { if (dedans) leg++; continue; }
      vus++; vusTotal++;
      if (h.surVoie) rail++;
      if (dansLaVille) { dedansMurs++; toutesRue.push(dr); rueIci.push(dr); }
      if (dedans && !mur) {
        maisonTotal++; dansMaison++; dedansJamais.add(k);
        toutesProf.push(profondeur[c]); profIci.push(profondeur[c]);
      } else if (mur) { courtineTotal++; dansCourtine++; }
    }
    profIci.sort((a, b) => a - b);
    rueIci.sort((a, b) => a - b);
    // L'ÉTAT DE LA PORTE, PARCE QU'IL DATE TOUT LE RESTE. Tant qu'elle tient,
    // l'assaut piétine dans le bourg extra muros et le rail n'existe pas
    // encore : lire « la colonne n'est presque jamais sur son rail » sans
    // savoir cela, c'est accuser le rail d'un retard qui est celui du bois.
    const E = B.etat();
    const laPorte = (E.portes || []).find((p) => p.nom === o.porte);
    courbe.push({ t: Math.round(t), vus, maison: dansMaison, mur: dansCourtine,
                  leg, intra: dedansMurs, rail,
                  porte: laPorte ? laPorte.etat : "?",
                  pv: laPorte && laPorte.pv != null ? laPorte.pv : 0,
                  med: quantile(profIci, .5), p90: quantile(profIci, .9),
                  rueMed: quantile(rueIci, .5),
                  rueLoin: rueIci.filter((d) => d > 8).length });
  }
  for (let k = 0; k < corps.length; k++) fermer(k, t);
  const fini = B.etat();
  console.log("  cuisson : " + ((Date.now() - t0) / 1000).toFixed(1) + " s pour " +
              o.duree + " s de bataille — " +
              nb(episodes.length) + " séjours dans une maison");
  console.log("  issue   : " + fini.morts + " morts, " + fini.blesses +
              " blessés, " + fini.fuyards + " fuyards · portes " +
              (fini.portes || []).map((p) => p.nom.replace(/^La /, "") + " " +
                                             p.etat).join(", ") + "\n");

  // ---- LE TÉMOIN, DANS L'EMPRISE DE LA BATAILLE ---------------------------
  // « 14 % des hommes à plus de huit mètres d'une rue » ne veut rien dire tant
  // qu'on ne sait pas ce que ça vaut pour un point pris au hasard là où ça se
  // passe. Et le témoin ne se prend PAS sur les dix-neuf millions de cellules
  // du plan : la moitié est de la mer et des champs, où il n'y a évidemment
  // aucune rue, et le chiffre monterait à 85 % sans rien dire de la ville.
  // On le prend donc sur l'emprise de la nuit, dilatée de cent mètres.
  const B0 = [Infinity, Infinity, -Infinity, -Infinity];
  for (const h of corps) {
    if (h.x < B0[0]) B0[0] = h.x; if (h.y < B0[1]) B0[1] = h.y;
    if (h.x > B0[2]) B0[2] = h.x; if (h.y > B0[3]) B0[3] = h.y;
  }
  const marge = 100;
  const bi0 = Math.max(0, Math.floor(B0[0] - marge)), bi1 = Math.min(nx - 1, Math.ceil(B0[2] + marge));
  const bj0 = Math.max(0, Math.floor(B0[1] - marge)), bj1 = Math.min(ny - 1, Math.ceil(B0[3] + marge));
  let libres = 0, libresLoin = 0;
  for (let j = bj0; j <= bj1; j++)
    for (let i = bi0; i <= bi1; i++) {
      const k = j * nx + i;
      if (bati(k) || !intra[k]) continue;
      libres++; if (distRue[k] > 8) libresLoin++;
    }

  // =========================================================================
  // LA COURBE
  // =========================================================================
  console.log("── LA PART DES VIVANTS DANS LE BÂTI, AU FIL DE LA NUIT ──");
  console.log("      t   porte  debout  intra muros  sur rail   dans une maison   prof.méd prof.p90" +
              "   courtine   dist.rue méd  > 8 m (intra)");
  const saut = Math.max(1, Math.round(courbe.length / 22));
  for (let i = 0; i < courbe.length; i++) {
    const c = courbe[i];
    if (i % saut !== 0 && i !== courbe.length - 1) continue;
    console.log("  " + String(c.t).padStart(5) + " s " +
                String(c.porte).padStart(6) + " " +
                String(c.vus).padStart(6) + " " +
                String(c.intra).padStart(6) + " " + pc(c.intra, c.vus) + " " +
                String(c.rail).padStart(6) + "   " +
                String(c.maison).padStart(5) + " " + pc(c.maison, c.vus) + "  " +
                m1(c.med) + " " + m1(c.p90) + "  " +
                String(c.mur).padStart(6) + "   " + m1(c.rueMed) + "     " +
                pc(c.rueLoin, c.intra));
  }

  const fin = courbe[courbe.length - 1];
  console.log("\n  EN FIN DE BATAILLE : " + fin.maison + " des " + fin.vus +
              " hommes debout sont dans une maison — " + pc(fin.maison, fin.vus).trim() +
              " (plus " + fin.mur + " sur la courtine)");
  console.log("  SUR TOUTE LA NUIT  : " + nb(maisonTotal) + " relevés dans une maison sur " +
              nb(vusTotal) + " — " + pc(maisonTotal, vusTotal).trim() +
              " du temps d'homme ; " + pc(courtineTotal, vusTotal).trim() + " sur la courtine");
  console.log("  " + dedansJamais.size + " des " + corps.length +
              " hommes sont entrés dans une maison au moins une fois — " +
              pc(dedansJamais.size, corps.length).trim());
  if (horsPlan) console.log("  (" + nb(horsPlan) + " relevés hors du plan, non comptés)");

  // =========================================================================
  // LA VENTILATION — c'est elle qui décide de la réparation
  // =========================================================================
  const tableau = (m, titre) => {
    console.log("\n── " + titre + " ──");
    console.log("  " + "état".padEnd(20) + "relevés  en maison    part   sur rail" +
                "  dont en maison   prof.méd prof.p90 prof.max  courtine" +
                "   intra muros  > 8 m de rue");
    const l = [...m.entries()].sort((a, b) => b[1].maison - a[1].maison ||
                                              b[1].vus - a[1].vus);
    for (const [clef, e] of l) {
      const p = e.prof.slice().sort((a, b) => a - b);
      const r = e.rue.slice().sort((a, b) => a - b);
      const loin = r.filter((d) => d > 8).length;
      const marque = LEGITIMES.has(clef.split(" · ")[0]) ? " ‡" : "";
      console.log("  " + (clef + marque).padEnd(20) +
                  String(e.vus).padStart(7) + "  " +
                  String(e.maison).padStart(7) + "  " + pc(e.maison, e.vus) + "  " +
                  String(e.surRail).padStart(7) + "  " +
                  String(e.maisonSurRail).padStart(12) + "   " +
                  m1(quantile(p, .5)) + " " + m1(quantile(p, .9)) + " " +
                  m1(p.length ? p[p.length - 1] : 0) + "  " +
                  String(e.courtine).padStart(7) + "  " +
                  String(e.intra).padStart(10) + "  " + pc(loin, r.length));
    }
  };
  // =========================================================================
  // LE RECENSEMENT — ce qu'on a mesuré, et ce qu'on n'a PAS pu mesurer
  //
  // Il vient AVANT la ventilation, et ce n'est pas de la politesse : sans lui,
  // un zéro dans le tableau qui suit se lit « cet état est sain » alors qu'il
  // veut dire « cet état n'a pas eu lieu ». La seule chose qui distingue les
  // deux est ici.
  // =========================================================================
  console.log("\n── CE QUI A EU LIEU (recensé à chaque pas) ──");
  console.log("  " + "état".padEnd(14) + "hommes distincts   pas d'homme   part du temps");
  const TOUS_ETATS = ["colonne", "forme", "assaut", "melee", "arrive", "deroute",
                      "tient", "fuite", "rentre", "contre", "coureur", "repli",
                      "commande", "pille", "saisi", "terre", "blesse", "mort"];
  const pasTotal = [...cens.values()].reduce((s, c) => s + c.pas, 0);
  const vus2 = new Set(cens.keys());
  for (const e of [...cens.entries()].sort((a, b) => b[1].pas - a[1].pas))
    console.log("  " + e[0].padEnd(14) + String(e[1].qui.size).padStart(10) +
                "         " + nb(e[1].pas).padStart(11) + "   " + pc(e[1].pas, pasTotal));
  const absents = TOUS_ETATS.filter((e) => !vus2.has(e));
  if (absents.length) {
    console.log("\n  ⚠ JAMAIS ATTEINTS DANS CETTE CUISSON, DONC NON MESURÉS : " +
                absents.join(", "));
    console.log("    Un zéro plus bas pour ces états-là ne les innocente de rien.");
  }

  // =========================================================================
  // LA COUCHE 1 — POURQUOI PERSONNE NE ROMPT
  //
  // Elle vient juste après le recensement, parce qu'elle en est l'explication.
  // `deroute` n'a plus que deux portes : la charrette du roi versée, et des
  // jambes qui disent « fuite ». Si la seconde ne s'ouvre jamais, le zéro
  // fuyard n'est pas une propriété de la bataille, c'est une panne — et la
  // ventilation de `deroute` par les murs ne mesurera jamais rien.
  // =========================================================================
  console.log("\n── LA COUCHE 1 (window.Corps) — CE QUE LES CORPS ONT VOULU FAIRE ──");
  console.log("  chargée : " + (globalThis.window.Corps ? "oui" : "NON") +
              " · pourvoyeur BatailleCorps : " +
              (globalThis.window.BatailleCorps ? "oui" : "NON") +
              " · pilote : " + (globalThis.window.BatailleCorps
                                ? globalThis.window.BatailleCorps.pilote : "—"));
  console.log("  " + nb(L1.obs) + " coups d'œil relevés sur " + corps.length +
              " hommes ; " + nb(L1.sans) + " pas d'homme sans `l1`" +
              (L1.sans ? "  ⚠ la couche n'a pas touché tout le monde" : ""));
  const ligneL1 = (m, titre) => {
    console.log("  " + titre);
    const tot = [...m.values()].reduce((s, e) => s + e.n, 0);
    for (const [v, e] of [...m.entries()].sort((a, b) => b[1].n - a[1].n))
      console.log("      " + v.padEnd(14) + nb(e.n).padStart(10) + " " +
                  pc(e.n, tot) + "   " + String(e.qui.size).padStart(4) +
                  " hommes distincts");
  };
  ligneL1(L1.jambes, "jambes —");
  ligneL1(L1.bras, "bras —");
  console.log("  emprise : max " + L1.emprMax.toFixed(2) + " · au-dessus de 0,60 : " +
              nb(L1.emprHaut) + " coups d'œil " + pc(L1.emprHaut, L1.obs).trim() +
              ", sur " + L1.quiEmprHaut.size + " hommes distincts");
  const barres = (arr, bas, haut) => {
    const tot = arr.reduce((s, v) => s + v, 0);
    for (let i = 0; i <= 20; i += 2) {
      const n = arr[i] + (i < 20 ? arr[i + 1] : 0);
      const v = bas + (haut - bas) * i / 20;
      console.log("      " + v.toFixed(2).padStart(6) + "   " + nb(n).padStart(9) +
                  " " + pc(n, tot) + "  " +
                  "█".repeat(Math.round(46 * n / Math.max(1, tot))));
    }
  };
  console.log("  distribution de l'emprise (0 = la tête tient le volant, 1 = le corps) :");
  barres(L1.empr, 0, 1);
  console.log("  distribution du sang-froid (+1 = froid, −1 = la glande à fond) — min " +
              L1.sangFroidMin.toFixed(2) + " :");
  barres(L1.sangFroid, -1, 1);
  const fuite = L1.jambes.get("fuite");
  console.log("  → « fuite » : " + (fuite ? nb(fuite.n) + " fois, " + fuite.qui.size +
              " hommes" : "JAMAIS ÉLUE — la seule porte ordinaire vers la déroute" +
              " est fermée") + " ; fuyards comptés par le module : " + fini.fuyards);

  tableau(seaux, "PAR ÉTAT (‡ = entre dans une maison exprès, hors des totaux)");
  tableau(parCamp, "PAR ÉTAT ET PAR CAMP");

  // =========================================================================
  // LES ÉPISODES — traverser ou camper, ce n'est pas la même faute
  // =========================================================================
  // ---- LA MISE EN PLACE, D'ABORD ------------------------------------------
  // On la lit AVANT les séjours, parce qu'elle change ce que les séjours
  // veulent dire : un homme posé dans une cuisine par `dresser` y restera toute
  // la nuit sans qu'aucune ligne de locomotion soit en cause.
  console.log("\n── AVANT LE PREMIER PAS — CE QUE LA MISE EN PLACE A POSÉ DANS UNE MAISON ──");
  console.log("  " + "état · camp".padEnd(22) + "hommes   dans une maison");
  let poseN = 0, poseD = 0;
  for (const [clef, e] of [...posePar.entries()].sort((a, b) => b[1].dedans - a[1].dedans)) {
    poseN += e.n; poseD += e.dedans;
    console.log("  " + clef.padEnd(22) + String(e.n).padStart(6) + "   " +
                String(e.dedans).padStart(6) + " " + pc(e.dedans, e.n));
  }
  console.log("  " + "TOTAL".padEnd(22) + String(poseN).padStart(6) + "   " +
              String(poseD).padStart(6) + " " + pc(poseD, poseN) +
              "   ← rien à voir avec versLe : c'est `dresser` qui les a mis là");

  console.log("\n── LES SÉJOURS DANS UNE MAISON (relevés à chaque pas) ──");
  console.log("  " + "état d'entrée".padEnd(20) + "séjours   dont posés là" +
              "   durée méd  durée max   prof.méd prof.max   entrés en marchant");
  const parEpisode = new Map();
  for (const e of episodes) {
    let s = parEpisode.get(e.etat);
    if (!s) parEpisode.set(e.etat, s = { n: 0, d: [], p: [], pose: 0, rail: 0 });
    s.n++; s.d.push(e.duree); s.p.push(e.prof);
    if (e.pose) s.pose++; if (e.rail) s.rail++;
  }
  for (const [clef, s] of [...parEpisode.entries()].sort((a, b) => b[1].n - a[1].n)) {
    const d = s.d.sort((a, b) => a - b), p = s.p.sort((a, b) => a - b);
    console.log("  " + String(clef).padEnd(20) + String(s.n).padStart(7) + "   " +
                String(s.pose).padStart(11) + "   " +
                quantile(d, .5).toFixed(1).padStart(7) + " s  " +
                d[d.length - 1].toFixed(1).padStart(7) + " s   " +
                m1(quantile(p, .5)) + " " + m1(p[p.length - 1]) + "  " +
                String(s.n - s.pose).padStart(12) + " " + pc(s.n - s.pose, s.n) +
                (s.rail ? "  (dont " + s.rail + " sur le rail)" : ""));
  }
  const marchants = episodes.filter((e) => !e.pose);
  console.log("  " + "TOTAL".padEnd(20) + String(episodes.length).padStart(7) + "   " +
              String(episodes.length - marchants.length).padStart(11) + "   " +
              " ".repeat(34) + String(marchants.length).padStart(12) + " " +
              pc(marchants.length, episodes.length));

  // ---- PAR QUELLE BRANCHE DE CODE ------------------------------------------
  // C'est la ligne qui désigne le fautif au lieu de le supposer : la phrase que
  // le module s'écrit à lui-même au battement où l'homme est entré.
  console.log("\n── PAR QUELLE BRANCHE IL EST ENTRÉ (h.branche à l'instant de l'entrée) ──");
  const parBranche = new Map();
  for (const e of marchants) {
    const clef = String(e.branche || "—").replace(/\d+/g, "N");
    let s = parBranche.get(clef);
    if (!s) parBranche.set(clef, s = { n: 0, arret: 0, presse: 0, p: [] });
    s.n++; s.p.push(e.prof);
    // À L'ARRÊT ET COUDES SERRÉS : ce n'est pas lui qui a marché. `versLe`
    // n'aurait rien à tester dans ce cas-là — c'est `pousser` qu'il faudrait
    // borner, et c'est la seule chose qui distingue les deux réparations.
    if (e.vit < 0.2) s.arret++;
    if (e.presse >= 2) s.presse++;
  }
  console.log("  " + "branche".padEnd(52) + "entrées   à l'arrêt   presse ≥ 2   prof.méd");
  for (const [clef, s] of [...parBranche.entries()].sort((a, b) => b[1].n - a[1].n)
                                                   .slice(0, 14)) {
    const p = s.p.sort((a, b) => a - b);
    console.log("  " + (clef.length > 50 ? clef.slice(0, 49) + "…" : clef).padEnd(52) +
                String(s.n).padStart(6) + "  " +
                String(s.arret).padStart(6) + " " + pc(s.arret, s.n) + " " +
                String(s.presse).padStart(6) + " " + pc(s.presse, s.n) + "  " +
                m1(quantile(p, .5)));
  }
  const arret = marchants.filter((e) => e.vit < 0.2).length;
  console.log("  → " + pc(arret, marchants.length).trim() + " des entrées se font" +
              " À L'ARRÊT (vit < 0,2 m/s) : ce sont des hommes POUSSÉS dans le mur,");
  console.log("    pas des hommes qui y marchent. `versLe` n'a rien à voir avec" +
              " celles-là — c'est `pousser()`.");

  // =========================================================================
  // LA PROFONDEUR — la distribution, jamais la moyenne
  // =========================================================================
  console.log("\n── LA PROFONDEUR DE L'INFRACTION ──");
  console.log("  Distance du point au vide le plus proche. Un mètre, c'est un angle");
  console.log("  frôlé ; dix, c'est le milieu d'un pâté de maisons.");
  const histo = (tri, bornes) => {
    for (let i = 0; i < bornes.length - 1; i++) {
      const a = bornes[i], b = bornes[i + 1];
      const n = tri.filter((d) => d > a && d <= b).length;
      console.log("  " + (b === Infinity ? "  > " + a + " m" :
                          String(a).padStart(3) + " – " + String(b).padStart(2) + " m")
                  .padEnd(12) + String(n).padStart(8) + " " + pc(n, tri.length) +
                  "  " + "█".repeat(Math.round(56 * n / Math.max(1, tri.length))));
    }
  };
  const triP = toutesProf.slice().sort((a, b) => a - b);
  console.log("\n  a) INSTANT PAR INSTANT — le temps passé à telle profondeur");
  histo(triP, [0, 1, 2, 3, 5, 8, 12, 20, Infinity]);
  if (triP.length)
    console.log("     médiane " + quantile(triP, .5).toFixed(1) + " m · p90 " +
                quantile(triP, .9).toFixed(1) + " m · p99 " +
                quantile(triP, .99).toFixed(1) + " m · pire " +
                triP[triP.length - 1].toFixed(1) + " m");
  const triE = episodes.map((e) => e.prof).sort((a, b) => a - b);
  console.log("\n  b) SÉJOUR PAR SÉJOUR — le plus loin où chaque entrée a mené");
  histo(triE, [0, 1, 2, 3, 5, 8, 12, 20, Infinity]);
  if (triE.length)
    console.log("     médiane " + quantile(triE, .5).toFixed(1) + " m · p90 " +
                quantile(triE, .9).toFixed(1) + " m · pire " +
                triE[triE.length - 1].toFixed(1) + " m");

  // =========================================================================
  // LA DISTANCE À LA RUE — la comparaison aux 46 %
  // =========================================================================
  console.log("\n── LA DISTANCE À LA RUE LA PLUS PROCHE ──");
  console.log("  Comparable à la mesure d'avant le rail — « 46 % des vivants à plus");
  console.log("  de huit mètres de toute rue » (bataille2d.js l. 3706).");
  const triR = toutesRue.slice().sort((a, b) => a - b);
  histo(triR, [0, 2, 4, 8, 15, 30, 60, Infinity]);
  const loin = triR.filter((d) => d > 8).length;
  console.log("  → " + pc(loin, triR.length).trim() + " des relevés de vivants " +
              "INTRA MUROS sont à plus de 8 m d'un axe de rue" +
              "   (n = " + nb(triR.length) + ")");
  console.log("    Témoin — le sol LIBRE et intra muros de l'emprise de la nuit (" +
              (bi1 - bi0) + " × " + (bj1 - bj0) + " m) : " +
              pc(libresLoin, libres).trim() + " y est à plus de 8 m.");
  console.log("    Un chiffre d'hommes SOUS le témoin veut dire qu'ils tiennent la");
  console.log("    rue mieux que le hasard ; au-dessus, qu'ils vont où l'on ne va pas.");
  console.log("");
}

main().catch((e) => { console.error("mesure_murs : " + (e && e.stack || e)); process.exit(1); });
