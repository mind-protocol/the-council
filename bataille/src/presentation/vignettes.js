/**
 * 🖥️ Présentation / Vignettes — les corps PRÉ-RENDUS, une fois pour toutes.
 *
 * Un homme était redessiné trait par trait à chaque frame : une ellipse, un
 * cercle, deux contours, et cela six cents fois par image. Le détail coûtait
 * donc le nombre d'hommes multiplié par le nombre de traits, et c'est ce qui
 * interdisait d'en mettre plus.
 *
 * Ici, chaque combinaison — livrée × panache × VARIANTE × palier de zoom —
 * est dessinée UNE fois dans un canvas hors écran, aussi finement qu'on veut,
 * puis blittée avec rotation. Le rendu cesse d'être payé par corps ; il est
 * payé par VARIÉTÉ, et la variété est bornée : huit variantes par livrée.
 *
 * LA VARIANTE, c'est ce qui fait qu'un rang n'est pas une rangée de jetons :
 * une teinte qui tire vers la boue ou vers le jour, des épaules plus ou moins
 * larges, un casque de fer, un chapel ou une coiffe, et de la CRASSE — la
 * cotte est salie, jamais neuve. Tirée de l'id du corps, stable d'une frame
 * à l'autre, et sans toucher au hasard de la sim.
 *
 * Ce que ça ne change pas, et qui est la règle : la silhouette reste franche
 * avant d'être jolie. Un homme richement dessiné se distingue moins bien d'un
 * autre quand ils sont trente serrés — le détail entre au zoom, pas avant.
 *
 * Le jour où de vrais assets arrivent, ils remplacent la fonction qui dessine
 * et rien d'autre : le calque blitte déjà une image orientée.
 */

const cache = new Map();

/** Les LIVRÉES : la couleur qu'on VOIT sur un homme. Franches, comme dans un jeu. Inconnue → gris. */
export const LIVREES = {
  bleu: '#3b7fe0',
  rouge: '#d2463a',
  jaune: '#e2a92e',
  vert: '#4fae66',
  noir: '#3a3b44',
  blanc: '#ddd4bd',
};
export const LIVREE_INCONNUE = '#8e939c';
export const couleurLivree = (livree) => LIVREES[livree] ?? LIVREE_INCONNUE;

/** La boue, la poussière, la suie : ce vers quoi toute couleur tire au champ. */
const BOUE = '#5a4a32';
const PEAU = '#d8b389';

/**
 * Les ROBES d'un cheval : une distribution, comme les masses — pas la
 * livrée de son cavalier. Tirée de l'id (viz seulement : aucun hasard de la
 * sim n'est consommé), le bai en tête comme dans toute écurie.
 */
const ROBES = [
  ['#6b4a2e', 4], // bai
  ['#9a5a2c', 3], // alezan
  ['#a8a49c', 2], // gris
  ['#2e2a28', 1], // noir
  ['#c9a56a', 1], // isabelle
];
const TOTAL_ROBES = ROBES.reduce((a, [, poids]) => a + poids, 0);

/** Un hachage stable d'un id — la seule source de « hasard » de ce module. */
function hacher(id, sel = 0) {
  let h = ((id + 1) * 2654435761 + sel * 40503) >>> 0;
  h = ((h >>> 13) ^ h) * 0x5bd1e995 >>> 0;
  h = ((h >>> 15) ^ h) >>> 0;
  return h;
}
/** Un réel dans [0,1[ stable pour (id, sel). */
const bruit = (id, sel) => (hacher(id, sel) >>> 8) / 16777216;

export function robeDe(id) {
  let t = hacher(id) % TOTAL_ROBES;
  for (const [robe, poids] of ROBES) {
    if (t < poids) return robe;
    t -= poids;
  }
  return ROBES[0][0];
}

/** Huit variantes de corps ; l'id en choisit une, pour toujours. */
export const VARIANTES = 8;
export const varianteDe = (id) => hacher(id, 3) % VARIANTES;

/**
 * Paliers de zoom en puissances de deux : on ne regénère pas à chaque cran de
 * molette, et l'agrandissement d'un palier au suivant ne se voit pas.
 */
function palier(ppm) {
  return Math.min(256, Math.max(16, 2 ** Math.ceil(Math.log2(Math.max(1, ppm)))));
}

/** '#rrggbb' ou 'rgb(r, g, b)' → [r, g, b]. */
function rgbDe(couleur) {
  if (couleur[0] === '#') {
    const n = parseInt(couleur.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  return (couleur.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
}
const rgb = ([r, g, b]) => `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;

/** Mélange vers le blanc — le jour tombe sur les épaules et le casque. */
export function eclaircir(couleur, part) {
  return rgb(rgbDe(couleur).map((v) => v + (255 - v) * part));
}

/** Vers le noir — le creux sous le bras, l'ombre de la cotte. */
export function assombrir(couleur, part) {
  return rgb(rgbDe(couleur).map((v) => v * (1 - part)));
}

/** Vers une autre couleur — la boue sur la livrée. */
export function melanger(a, b, t) {
  const x = rgbDe(a), y = rgbDe(b);
  return rgb(x.map((v, i) => v + (y[i] - v) * t));
}

/**
 * La variante d'un homme : proportions, casque, teinte et crasse. Tout sort
 * de l'index, rien du hasard de la sim.
 */
function varianteHomme(v, couleur) {
  const s = v * 17; // sel
  return {
    // les épaules : de l'étroit au carré ; la longueur : du ramassé à l'allongé
    epaules: 0.64 + 0.14 * bruit(s, 1),
    longueur: 0.94 + 0.12 * bruit(s, 2),
    tete: 0.38 + 0.08 * bruit(s, 3),
    // le casque : fer (calotte claire), chapel (bord large), coiffe (mailles, sombre)
    casque: ['fer', 'chapel', 'coiffe', 'fer', 'chapel', 'fer', 'coiffe', 'fer'][v % 8],
    // la livrée salie : chacun sa part de boue et sa part de jour
    teinte: melanger(
      melanger(couleur, BOUE, 0.08 + 0.22 * bruit(s, 4)),
      bruit(s, 5) < 0.5 ? '#000000' : '#ffffff',
      0.1 * bruit(s, 6)
    ),
    // la crasse : de deux à cinq taches, posées sur les épaules
    crasse: Array.from({ length: 2 + Math.floor(3 * bruit(s, 7)) }, (_, i) => ({
      a: bruit(s, 10 + i) * Math.PI * 2,
      d: 0.2 + 0.7 * bruit(s, 20 + i),
      r: 0.12 + 0.2 * bruit(s, 30 + i),
      alpha: 0.18 + 0.25 * bruit(s, 40 + i),
    })),
  };
}

/**
 * Dessine un homme vu du dessus, cap vers la DROITE (+x), centré en (0,0),
 * dans une unité : `r` = le rayon du corps en pixels.
 */
function dessinerCorps(ctx, r, couleur, panache, v) {
  const V = varianteHomme(v, couleur);
  const teinte = V.teinte;
  const ex = r * V.longueur * 0.72, ey = r * V.epaules; // demi-axes : axe du cap, travers
  // L'OMBRE au sol, décalée : elle donne l'épaisseur, et c'est elle qui fait
  // qu'un homme se pose sur le pave au lieu d'y être collé.
  ctx.beginPath();
  ctx.ellipse(r * 0.12, r * 0.14, ex * 1.08, ey * 1.06, 0, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
  ctx.fill();

  // LES ÉPAULES : plus larges en travers du cap que dans son axe. Un dégradé
  // du bord vers le centre — vu de haut, le dos prend le jour et les flancs
  // tombent dans l'ombre.
  const g = ctx.createLinearGradient(0, -ey, 0, ey);
  g.addColorStop(0, assombrir(teinte, 0.4));
  g.addColorStop(0.42, eclaircir(teinte, 0.14));
  g.addColorStop(1, assombrir(teinte, 0.4));
  ctx.beginPath();
  ctx.ellipse(0, 0, ex, ey, 0, 0, Math.PI * 2);
  ctx.fillStyle = g;
  ctx.fill();
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
  ctx.lineWidth = Math.max(1, r * 0.07);
  ctx.stroke();

  // LA CRASSE : des taches de boue et de suie, dans le contour des épaules
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(0, 0, ex, ey, 0, 0, Math.PI * 2);
  ctx.clip();
  for (const t of V.crasse) {
    ctx.beginPath();
    ctx.ellipse(Math.cos(t.a) * t.d * ex, Math.sin(t.a) * t.d * ey, t.r * r, t.r * r * 0.7, t.a, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(48, 34, 18, ${t.alpha})`;
    ctx.fill();
  }
  ctx.restore();

  // LA FENTE DE LA COTTE dans l'axe du corps : deux traits qui disent le sens
  // sans qu'on ait besoin de la tête — utile quand les rangs se touchent.
  ctx.beginPath();
  ctx.moveTo(-ex * 0.7, 0);
  ctx.lineTo(ex * 0.6, 0);
  ctx.strokeStyle = assombrir(teinte, 0.55);
  ctx.lineWidth = Math.max(0.5, r * 0.05);
  ctx.stroke();

  // LA TÊTE, posée vers l'avant : le casque dit la variante. Le NASAL, un
  // trait sombre, pointe où l'homme regarde.
  const tx = r * 0.3, tr = r * V.tete;
  if (V.casque === 'chapel') {
    // le chapel de fer : un bord large et mat autour de la calotte
    ctx.beginPath();
    ctx.arc(tx, 0, tr * 1.35, 0, Math.PI * 2);
    ctx.fillStyle = '#7d7668';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.lineWidth = Math.max(0.8, r * 0.05);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.arc(tx, 0, tr, 0, Math.PI * 2);
  const gt = ctx.createRadialGradient(tx + tr * 0.3, -tr * 0.3, tr * 0.1, tx, 0, tr);
  if (V.casque === 'coiffe') {
    gt.addColorStop(0, '#8d8a80');
    gt.addColorStop(1, '#4e4b44');
  } else {
    gt.addColorStop(0, '#d8d3c4');
    gt.addColorStop(1, V.casque === 'chapel' ? '#9d9686' : '#8f8a7c');
  }
  ctx.fillStyle = gt;
  ctx.fill();
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.55)';
  ctx.lineWidth = Math.max(0.8, r * 0.06);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(tx + tr * 0.15, 0);
  ctx.lineTo(tx + tr * 1.0, 0);
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
  ctx.lineWidth = Math.max(0.8, r * 0.08);
  ctx.stroke();

  // LE PANACHE du chef : anneau doré, fait physique qu'on reconnaît de loin.
  if (panache) {
    ctx.beginPath();
    ctx.ellipse(0, 0, ex + r * 0.16, ey + r * 0.16, 0, 0, Math.PI * 2);
    ctx.strokeStyle = '#f0c674';
    ctx.lineWidth = Math.max(1.5, r * 0.12);
    ctx.stroke();
  }
}

/**
 * La vignette d'un homme, cap vers la droite. Le calque la blitte en tournant
 * le contexte du cap : on ne stocke pas d'orientations, on tourne l'image.
 * @param {string} couleur #rrggbb de la livrée
 * @param {boolean} panache
 * @param {number} ppm pixels par mètre courant
 * @param {number} rayonM rayon du corps en mètres
 * @param {number} [variante] 0..VARIANTES-1 — voir varianteDe(id)
 * @returns {{toile: HTMLCanvasElement, r: number, demi: number}} — `r` = rayon en px DANS la vignette
 */
export function vignetteHomme(couleur, panache, ppm, rayonM, variante = 0) {
  const p = palier(ppm);
  const clef = `${couleur}|${panache ? 1 : 0}|${p}|${rayonM.toFixed(2)}|${variante}`;
  const prete = cache.get(clef);
  if (prete) return prete;

  const r = Math.max(3, rayonM * p);
  // marge : l'ombre déborde, et l'anneau de panache aussi
  const demi = Math.ceil(r * 1.5);
  const toile = document.createElement('canvas');
  toile.width = toile.height = demi * 2;
  const ctx = toile.getContext('2d');
  ctx.translate(demi, demi);
  dessinerCorps(ctx, r, couleur, panache, variante);

  const v = { toile, r, demi };
  cache.set(clef, v);
  return v;
}

/** La variante d'un cheval : gabarit, marques en tête, crasse. */
function varianteCheval(v, robe) {
  const s = 101 + v * 23;
  const sombre = rgbDe(robe).reduce((a, b) => a + b, 0) < 300;
  return {
    longueur: 0.94 + 0.12 * bruit(s, 1),
    largeur: 0.9 + 0.2 * bruit(s, 2),
    teteL: 0.9 + 0.2 * bruit(s, 3),
    // la liste ou l'étoile en tête : une marque blanche, une fois sur trois
    marque: bruit(s, 4) < 0.35 ? (bruit(s, 5) < 0.5 ? 'liste' : 'etoile') : null,
    // crins : noirs sur les robes claires et baies, clairs sur les gris
    crins: sombre ? eclaircir(robe, 0.25) : robe === '#a8a49c' ? '#e6e2d8' : '#1e1814',
    teinte: melanger(robe, BOUE, 0.05 + 0.2 * bruit(s, 6)),
    crasse: Array.from({ length: 2 + Math.floor(3 * bruit(s, 7)) }, (_, i) => ({
      x: -0.8 + 1.4 * bruit(s, 10 + i),
      y: -0.8 + 1.6 * bruit(s, 20 + i),
      r: 0.14 + 0.2 * bruit(s, 30 + i),
      alpha: 0.15 + 0.22 * bruit(s, 40 + i),
    })),
  };
}

/**
 * Dessine un cheval vu du dessus, cap vers la DROITE, centré en (0,0).
 * `p` = pixels par mètre du palier, `r` = demi-largeur du corps en px.
 * La housse porte la livrée : c'est elle qu'on reconnaît de loin, pas la robe.
 */
function dessinerCheval(ctx, p, r, robe, housse, v, chef) {
  const V = varianteCheval(v, robe);
  const teinte = V.teinte;
  const L = 1.05 * p * V.longueur; // demi-longueur du corps
  const W = r * V.largeur; // demi-largeur au plus large (la croupe)

  // l'ombre, décalée : le cheval se pose sur le sol
  ctx.beginPath();
  ctx.ellipse(0.12 * r, 0.16 * r, L * 1.1, W * 1.08, 0, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(0, 0, 0, 0.32)';
  ctx.fill();

  // la queue : des crins qui partent de la croupe, un peu de biais
  ctx.strokeStyle = V.crins;
  ctx.lineCap = 'round';
  ctx.lineWidth = Math.max(1, W * 0.26);
  ctx.beginPath();
  ctx.moveTo(-L * 0.9, 0);
  ctx.quadraticCurveTo(-L * 1.2, W * 0.28, -L * 1.42, W * 0.1);
  ctx.stroke();
  ctx.lineWidth = Math.max(1, W * 0.14);
  ctx.beginPath();
  ctx.moveTo(-L * 0.92, W * 0.05);
  ctx.quadraticCurveTo(-L * 1.18, W * 0.42, -L * 1.36, W * 0.34);
  ctx.stroke();

  // LE CORPS : vu du dessus, la croupe et les épaules font deux masses de
  // même largeur, et le FLANC SE CREUSE entre les deux — une courbe rentrée,
  // franche, qui donne la taille. Les deux bouts sont ronds.
  const corps = new Path2D();
  corps.moveTo(-L * 0.98, 0);
  corps.bezierCurveTo(-L * 0.98, -W * 0.75, -L * 0.78, -W, -L * 0.5, -W);
  corps.bezierCurveTo(-L * 0.3, -W, -L * 0.22, -W * 0.74, 0, -W * 0.74);
  corps.bezierCurveTo(L * 0.22, -W * 0.74, L * 0.32, -W * 0.96, L * 0.55, -W * 0.94);
  corps.bezierCurveTo(L * 0.72, -W * 0.92, L * 0.84, -W * 0.7, L * 0.84, -W * 0.3);
  corps.bezierCurveTo(L * 0.84, W * 0.3, L * 0.72, W * 0.92, L * 0.55, W * 0.94);
  corps.bezierCurveTo(L * 0.32, W * 0.96, L * 0.22, W * 0.74, 0, W * 0.74);
  corps.bezierCurveTo(-L * 0.22, W * 0.74, -L * 0.3, W, -L * 0.5, W);
  corps.bezierCurveTo(-L * 0.78, W, -L * 0.98, W * 0.75, -L * 0.98, 0);
  corps.closePath();
  const g = ctx.createLinearGradient(0, -W, 0, W);
  g.addColorStop(0, assombrir(teinte, 0.38));
  g.addColorStop(0.45, eclaircir(teinte, 0.16));
  g.addColorStop(1, assombrir(teinte, 0.38));
  ctx.fillStyle = g;
  ctx.fill(corps);
  // la ligne du dos, qui prend le jour
  ctx.beginPath();
  ctx.moveTo(-L * 0.85, 0);
  ctx.lineTo(L * 0.6, 0);
  ctx.strokeStyle = eclaircir(teinte, 0.22);
  ctx.lineWidth = Math.max(1, W * 0.1);
  ctx.stroke();
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.55)';
  ctx.lineWidth = Math.max(1, W * 0.07);
  ctx.stroke(corps);

  // la crasse : boue aux flancs et à la croupe
  ctx.save();
  ctx.clip(corps);
  for (const t of V.crasse) {
    ctx.beginPath();
    ctx.ellipse(t.x * L, t.y * W, t.r * W, t.r * W * 0.6, 0.3, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(48, 34, 18, ${t.alpha})`;
    ctx.fill();
  }
  ctx.restore();

  // L'ENCOLURE : elle part du garrot, s'affine vers la tête, et se courbe
  ctx.beginPath();
  ctx.moveTo(L * 0.66, -W * 0.62);
  ctx.bezierCurveTo(L * 0.95, -W * 0.52, L * 1.15, -W * 0.38, L * 1.28, -W * 0.28);
  ctx.lineTo(L * 1.28, W * 0.28);
  ctx.bezierCurveTo(L * 1.15, W * 0.38, L * 0.95, W * 0.52, L * 0.66, W * 0.62);
  ctx.closePath();
  ctx.fillStyle = eclaircir(teinte, 0.04);
  ctx.fill();
  ctx.stroke();
  // la crinière : des crins couchés d'un côté de l'encolure
  ctx.strokeStyle = V.crins;
  ctx.lineWidth = Math.max(1, W * 0.2);
  ctx.beginPath();
  ctx.moveTo(L * 0.66, -W * 0.08);
  ctx.quadraticCurveTo(L * 0.95, -W * 0.3, L * 1.24, -W * 0.06);
  ctx.stroke();

  // LA TÊTE : longue, plus étroite au bout du nez, les deux oreilles dressées
  const tl = L * 0.24 * V.teteL, tw = W * 0.3;
  const tete = new Path2D();
  tete.moveTo(L * 1.22, -tw);
  tete.bezierCurveTo(L * 1.22 + tl * 1.1, -tw * 1.05, L * 1.22 + tl * 2.1, -tw * 0.55, L * 1.22 + tl * 2.1, 0);
  tete.bezierCurveTo(L * 1.22 + tl * 2.1, tw * 0.55, L * 1.22 + tl * 1.1, tw * 1.05, L * 1.22, tw);
  tete.closePath();
  ctx.fillStyle = eclaircir(teinte, 0.1);
  ctx.fill(tete);
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.55)';
  ctx.lineWidth = Math.max(1, W * 0.07);
  ctx.stroke(tete);
  if (V.marque === 'liste') {
    ctx.beginPath();
    ctx.moveTo(L * 1.26, 0);
    ctx.lineTo(L * 1.22 + tl * 2.0, 0);
    ctx.strokeStyle = 'rgba(245, 240, 230, 0.85)';
    ctx.lineWidth = Math.max(1, tw * 0.45);
    ctx.stroke();
  } else if (V.marque === 'etoile') {
    ctx.beginPath();
    ctx.arc(L * 1.22 + tl * 0.7, 0, Math.max(1, tw * 0.3), 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(245, 240, 230, 0.85)';
    ctx.fill();
  }
  ctx.beginPath();
  ctx.moveTo(L * 1.2, -tw * 0.9);
  ctx.lineTo(L * 1.12, -tw * 1.7);
  ctx.moveTo(L * 1.2, tw * 0.9);
  ctx.lineTo(L * 1.12, tw * 1.7);
  ctx.strokeStyle = assombrir(teinte, 0.35);
  ctx.lineWidth = Math.max(1, W * 0.13);
  ctx.stroke();

  // LA SELLE et sa housse aux couleurs de la livrée : deux pans qui tombent
  // sur les flancs, la selle de cuir au milieu
  if (housse) {
    ctx.beginPath();
    ctx.moveTo(-L * 0.42, -W * 0.98);
    ctx.quadraticCurveTo(-L * 0.05, -W * 0.74, L * 0.28, -W * 0.88);
    ctx.lineTo(L * 0.28, W * 0.88);
    ctx.quadraticCurveTo(-L * 0.05, W * 0.74, -L * 0.42, W * 0.98);
    ctx.closePath();
    ctx.fillStyle = melanger(housse, BOUE, 0.3);
    ctx.fill();
    if (chef) {
      // LA HOUSSE DU CHEF : une bande claire en travers de chaque pan et un
      // liseré d'or — l'unité reconnaît la monture de son chef de loin,
      // même quand lui porte l'épée et n'a pas de hampe pour un pennon.
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(-L * 0.42, -W * 0.98);
      ctx.quadraticCurveTo(-L * 0.05, -W * 0.74, L * 0.28, -W * 0.88);
      ctx.lineTo(L * 0.28, W * 0.88);
      ctx.quadraticCurveTo(-L * 0.05, W * 0.74, -L * 0.42, W * 0.98);
      ctx.closePath();
      ctx.clip();
      ctx.strokeStyle = eclaircir(housse, 0.45);
      ctx.lineWidth = Math.max(1.5, W * 0.28);
      ctx.beginPath();
      ctx.moveTo(-L * 0.3, -W * 1.1);
      ctx.lineTo(L * 0.1, -W * 0.2);
      ctx.moveTo(-L * 0.3, W * 1.1);
      ctx.lineTo(L * 0.1, W * 0.2);
      ctx.stroke();
      ctx.restore();
      ctx.strokeStyle = '#f0c674';
      ctx.lineWidth = Math.max(1.2, W * 0.1);
      ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.55)';
    ctx.lineWidth = Math.max(1, W * 0.07);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.ellipse(-L * 0.04, 0, L * 0.24, W * 0.62, 0, 0, Math.PI * 2);
  ctx.fillStyle = '#4a3722';
  ctx.fill();
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
  ctx.lineWidth = Math.max(1, W * 0.07);
  ctx.stroke();
}

/**
 * La vignette d'un cheval, cap vers la droite. Le cavalier est un autre corps,
 * dessiné par-dessus par le calque : ici il n'y a que la bête et sa selle.
 * @param {string} robe #rrggbb @param {string|null} housse livrée du cavalier
 * @param {number} ppm @param {number} rayonM demi-largeur du corps en mètres
 * @param {number} [variante] 0..VARIANTES-1
 * @param {boolean} [chef] la monture d'un chef : housse marquée, liseré d'or
 */
export function vignetteCheval(robe, housse, ppm, rayonM, variante = 0, chef = false) {
  const p = palier(ppm);
  const clef = `cheval|${robe}|${housse ?? ''}|${p}|${rayonM.toFixed(2)}|${variante}|${chef ? 1 : 0}`;
  const prete = cache.get(clef);
  if (prete) return prete;

  const r = Math.max(2, rayonM * p);
  const demi = Math.ceil(Math.max(1.05 * p * 1.85, r * 1.5));
  const toile = document.createElement('canvas');
  toile.width = toile.height = demi * 2;
  const ctx = toile.getContext('2d');
  ctx.translate(demi, demi);
  dessinerCheval(ctx, p, r, robe, housse, variante, chef);

  const v = { toile, r, demi, p };
  cache.set(clef, v);
  return v;
}

/**
 * LE GISANT — un homme à terre, vu du dessus. Ce n'est PAS un homme debout
 * qu'on aurait pâli : un corps tombé s'étale. Le torse est à plat, plus long
 * et plus mince que des épaules vues d'en haut, la tête roule sur le côté,
 * un bras part en travers et les jambes ne sont plus parallèles. C'est cette
 * silhouette-là qui fait qu'un champ couvert de morts se lit d'un coup d'œil,
 * sans avoir à compter personne.
 *
 * La livrée y est SALIE plus qu'ailleurs (la terre, le sang, le piétinement)
 * et sans lumière du dessus : rien ne brille sur un mort.
 * @param {string} couleur livrée @param {number} ppm @param {number} rayonM
 * @param {number} [variante] 0..VARIANTES-1 — voir varianteDe(id)
 */
export function vignetteGisant(couleur, ppm, rayonM, variante = 0) {
  const pal = palier(ppm);
  const clef = 'gisant|' + couleur + '|' + pal + '|' + rayonM.toFixed(2) + '|' + variante;
  const prete = cache.get(clef);
  if (prete) return prete;

  const r = Math.max(3, rayonM * pal);
  const demi = Math.ceil(r * 2.6); // il s'étale : la marge est plus large que debout
  const toile = document.createElement('canvas');
  toile.width = toile.height = demi * 2;
  const ctx = toile.getContext('2d');
  ctx.translate(demi, demi);

  const s = variante * 31;
  const terni = melanger(couleur, BOUE, 0.42 + 0.16 * bruit(s, 1));
  const cote = bruit(s, 2) < 0.5 ? 1 : -1; // de quel côté il est tombé
  const peau = melanger(PEAU, BOUE, 0.25);
  const trait = 'rgba(0, 0, 0, 0.55)';
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';

  // LES JAMBES — deux traits épais, ouverts, l'une pliée
  const membre = (path, epaisseur, couleurMembre) => {
    ctx.strokeStyle = trait;
    ctx.lineWidth = Math.max(2, r * (epaisseur + 0.12));
    ctx.stroke(path);
    ctx.strokeStyle = couleurMembre;
    ctx.lineWidth = Math.max(1, r * epaisseur);
    ctx.stroke(path);
  };
  const ecart = (0.5 + 0.35 * bruit(s, 3)) * cote;
  for (const [ouvre, plie] of [[0.35, 0], [-0.2, 0.5 + 0.4 * bruit(s, 4)]]) {
    const j = new Path2D();
    const sens = ouvre > 0 ? 1 : -1;
    j.moveTo(-r * 0.45, r * 0.25 * sens);
    j.quadraticCurveTo(
      -r * (1.5 + plie * 0.4), r * (ouvre * 1.3 + ecart * plie),
      -r * (2.3 - plie * 0.7), r * (ouvre * 2.6 + ecart * plie * 1.9)
    );
    membre(j, 0.28, assombrir(terni, 0.25));
  }

  // LES BRAS — un jeté en travers, l'autre replié sous lui
  const jete = (0.9 + 0.5 * bruit(s, 5)) * cote;
  const brasA = new Path2D();
  brasA.moveTo(r * 0.15, r * 0.3 * cote);
  brasA.quadraticCurveTo(r * 0.2, r * jete * 0.8, -r * 0.25, r * jete * 1.35);
  membre(brasA, 0.25, assombrir(terni, 0.2));
  ctx.beginPath();
  ctx.arc(-r * 0.25, r * jete * 1.35, Math.max(1, r * 0.15), 0, Math.PI * 2);
  ctx.fillStyle = peau;
  ctx.fill();

  const brasB = new Path2D();
  brasB.moveTo(r * 0.1, -r * 0.3 * cote);
  brasB.quadraticCurveTo(-r * 0.5, -r * 0.75 * cote, -r * 0.75, -r * 0.35 * cote);
  membre(brasB, 0.23, assombrir(terni, 0.3));

  // LE TORSE — à plat : plus long dans l'axe, plus mince en travers
  ctx.beginPath();
  ctx.ellipse(-r * 0.1, 0, r * 0.95, r * 0.6, 0.06 * cote, 0, Math.PI * 2);
  ctx.fillStyle = terni;
  ctx.fill();
  ctx.strokeStyle = trait;
  ctx.lineWidth = Math.max(1, r * 0.09);
  ctx.stroke();
  // la cotte creusée par le corps qui s'affaisse
  ctx.beginPath();
  ctx.moveTo(-r * 0.8, r * 0.12 * cote);
  ctx.quadraticCurveTo(-r * 0.1, r * 0.3 * cote, r * 0.6, r * 0.1 * cote);
  ctx.strokeStyle = assombrir(terni, 0.42);
  ctx.lineWidth = Math.max(0.8, r * 0.12);
  ctx.stroke();

  // LA TÊTE — roulée sur le côté, la nuque cassée vers l'épaule
  const tx = r * 0.95, ty = r * 0.42 * cote, tr = r * 0.4;
  ctx.beginPath();
  ctx.moveTo(r * 0.5, r * 0.1 * cote);
  ctx.lineTo(tx - tr * 0.4, ty);
  ctx.strokeStyle = peau;
  ctx.lineWidth = Math.max(1.5, r * 0.24);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(tx, ty, tr, 0, Math.PI * 2);
  const casqueTombe = bruit(s, 6) > 0.5;
  ctx.fillStyle = casqueTombe ? melanger(peau, '#3a2a1c', 0.45) : '#7d7668';
  ctx.fill();
  ctx.strokeStyle = trait;
  ctx.lineWidth = Math.max(0.8, r * 0.07);
  ctx.stroke();
  if (casqueTombe) {
    // le casque a roulé un peu plus loin — il ne le tient plus
    ctx.beginPath();
    ctx.arc(tx + tr * (0.7 + 0.6 * bruit(s, 7)), ty + tr * 1.25 * cote, tr * 0.62, 0, Math.PI * 2);
    ctx.fillStyle = '#6e6a60';
    ctx.fill();
    ctx.strokeStyle = trait;
    ctx.lineWidth = Math.max(0.8, r * 0.07);
    ctx.stroke();
  }

  const v = { toile, r, demi };
  cache.set(clef, v);
  return v;
}

/**
 * LA BÊTE MORTE — un cheval couché sur le flanc : la masse au sol, l'encolure
 * jetée en avant, la tête posée à plat, et les quatre jambes raides du MÊME
 * côté. C'est ce dernier point qui dit « mort » et pas « couché » — un cheval
 * vivant ne tend pas ses quatre membres à l'horizontale.
 */
export function vignetteGisantCheval(robe, ppm, rayonM, variante = 0) {
  const pal = palier(ppm);
  const clef = 'gisant-cheval|' + robe + '|' + pal + '|' + rayonM.toFixed(2) + '|' + variante;
  const prete = cache.get(clef);
  if (prete) return prete;

  const p = pal;
  const r = Math.max(2, rayonM * p);
  const L = 1.05 * p;
  const demi = Math.ceil(Math.max(L * 2.1, r * 3.2));
  const toile = document.createElement('canvas');
  toile.width = toile.height = demi * 2;
  const ctx = toile.getContext('2d');
  ctx.translate(demi, demi);

  const s = 211 + variante * 13;
  const terni = melanger(robe, BOUE, 0.35);
  const cote = bruit(s, 1) < 0.5 ? 1 : -1;
  const trait = 'rgba(0, 0, 0, 0.55)';
  ctx.lineCap = 'round';

  // les quatre jambes, raides, toutes du même côté
  for (const [ax, ecart] of [[0.62, 1.0], [0.5, 1.35], [-0.55, 1.0], [-0.68, 1.35]]) {
    ctx.beginPath();
    ctx.moveTo(L * ax, r * 0.3 * cote);
    ctx.lineTo(L * (ax + 0.12 * (ax > 0 ? 1 : -1)), r * ecart * 2.1 * cote);
    ctx.strokeStyle = trait;
    ctx.lineWidth = Math.max(2, r * 0.4);
    ctx.stroke();
    ctx.strokeStyle = assombrir(terni, 0.3);
    ctx.lineWidth = Math.max(1, r * 0.28);
    ctx.stroke();
  }

  // la masse, affalée et un peu plus large que debout
  ctx.beginPath();
  ctx.ellipse(-L * 0.06, 0, L * 0.92, r * 1.05, 0, 0, Math.PI * 2);
  ctx.fillStyle = terni;
  ctx.fill();
  ctx.strokeStyle = trait;
  ctx.lineWidth = Math.max(1, r * 0.08);
  ctx.stroke();

  // l'encolure jetée en avant, la tête posée à plat
  ctx.beginPath();
  ctx.moveTo(L * 0.7, -r * 0.35 * cote);
  ctx.quadraticCurveTo(L * 1.25, -r * 0.2 * cote, L * 1.5, r * 0.45 * cote);
  ctx.strokeStyle = trait;
  ctx.lineWidth = Math.max(2, r * 0.75);
  ctx.stroke();
  ctx.strokeStyle = melanger(terni, '#000000', 0.1);
  ctx.lineWidth = Math.max(1.5, r * 0.6);
  ctx.stroke();
  ctx.beginPath();
  ctx.ellipse(L * 1.6, r * 0.6 * cote, L * 0.2, r * 0.3, 0.5 * cote, 0, Math.PI * 2);
  ctx.fillStyle = eclaircir(terni, 0.08);
  ctx.fill();
  ctx.strokeStyle = trait;
  ctx.lineWidth = Math.max(1, r * 0.08);
  ctx.stroke();

  const v = { toile, r, demi, p };
  cache.set(clef, v);
  return v;
}

/** La couleur de peau — pour les mains dessinées par le calque. */
export const COULEUR_PEAU = PEAU;

/** Combien de vignettes vivent en memoire (viz perf). */
export function compteVignettes() {
  return cache.size;
}
