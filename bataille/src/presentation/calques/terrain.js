/**
 * 🖥️ Calque terrain — ce qui est posé sur le plan.
 * 1) Les obstacles rectangulaires (maisons des scénarios) — vus du dessus.
 * 2) Le PLAN CUIT d'une ville (vues.plan, le plan2d de le-conseil2) : eau,
 *    voies, bâti, rempart — dessiné en RASTER caché à deux niveaux : la ville
 *    entière au loin, et une fenêtre fine sous la caméra dont la RÉSOLUTION
 *    SUIT LE ZOOM (bornée par un budget de pixels) — re-cuite quand la caméra
 *    en sort ou que l'échelle change vraiment, jamais re-tracée par frame.
 *    Les Path2D sont cuits UNE fois par plan (5,9 Mo de chemins à parser).
 * 3) La VÉRITÉ du masque (vues.terrain.casesBloqueesDans) au zoom de contact :
 *    le dessin est joli, le masque est VRAI — les deux doivent se recouvrir,
 *    et l'écart se voit ici.
 * Le plan cuit a l'Y vers le NORD ; le monde a le sud en bas — le raster
 * fait la bascule (y_monde = H − y_plan), la même que le masque (inverserY).
 * 2bis) Le SOL d'une ville de l'état (`<id>.plan.json`, sorti de
 *    cuire_ville.py au même passage que le masque) : des aires et des bandes
 *    par genre — eau, grève, colline, village, champ, route, quai, mur — déjà
 *    en mètres du monde, sans bascule. Les murs sont peints à l'épaisseur
 *    RÉELLE du masque et percés aux mêmes portes : le dessin et la vérité
 *    sortent du même trait, ils se recouvrent par construction.
 * 4) LES NOMS DE LIEUX : chaque pièce de sol porte son `etiq` (en mètres) et
 *    son nom — « Le port intérieur », « La barbacane ». Ils se lisent au loin,
 *    quand la carte est une carte, et s'effacent au zoom de contact, où l'on
 *    est dans la rue et non sur un plan. De la géographie, pas du brouillard.
 * 2ter) L'OMBRAGE DU RELIEF (`<id>.ombrage.png`, cuit par 07_ombrage.py au
 *    repère exact du plan) : posé entre les aires et les bandes, il donne son
 *    volume à la carte sans toucher à sa palette, et s'efface au zoom de
 *    contact où une pente mesurée au pas de 15 m n'est plus qu'un flou.
 * @viz terrain-obstacles, terrain-ville, terrain-sol, terrain-masque, terrain-ombrage, noms-de-lieux
 */

import { cheminToits } from './toits.js';

// La palette de la nuit — celle des planches de le-conseil2 (fond #14161c ici).
const COULEURS = {
  sol: '#1b1712',
  eau: '#1d2c33',
  voie: '#6d5c42',
  mur: '#6a6459',
  tour: '#847d70',
  bati: '#2e2820',
  batiTrait: 'rgba(220,190,140,.22)',
  niveau: 'rgba(220,190,140,.12)',
};
// Largeur des voies en mètres (mêmes proportions que la feuille du jeu source).
const LARGEURS_VOIES = { artere: 11, quai: 8, rue: 6, abord: 4, ruelle: 3, escalier: 2 };

// Le sol d'une ville de l'état, genre par genre, dans l'ordre où on le peint
// (du dessous vers le dessus). Une aire se remplit ; une bande se trace à sa
// largeur en mètres (le mur prend celle du masque, décidée à la cuisson).
const SOL = {
  champ: { aire: true, fond: '#1f1a12', trait: 'rgba(220,190,140,.10)' },
  greve: { aire: true, fond: '#2b2519', trait: 'rgba(220,190,140,.14)' },
  colline: { aire: true, fond: '#221d15', trait: 'rgba(220,190,140,.22)', niveaux: 2 },
  bois: { aire: true, fond: '#1c2216', trait: 'rgba(160,190,120,.18)' },
  marais: { aire: true, fond: '#1c2622', trait: 'rgba(120,170,160,.16)' },
  // un village n'est pas une aire : ses points sont les toits, un par maison
  village: { aire: true, toits: true, fond: '#2e2820', trait: 'rgba(220,190,140,.22)' },
  eau: { aire: true, fond: '#1d2c33', trait: '#33555f', traitLargeur: 1.2 },
  route: { bande: true, largeur: 6, trait: '#6d5c42' },
  riviere: { bande: true, largeur: 5, trait: '#1d2c33' },
  quai: { bande: true, largeur: 8, trait: '#4f5c5e' },
  mur: { bande: true, largeur: null, trait: '#6a6459', bord: 'rgba(220,190,140,.30)' },
};
const ORDRE_SOL = Object.keys(SOL);

// La fenêtre fine : budget de pixels fixe, résolution asservie au zoom —
// c'est ce qui évite le flou (une fenêtre 3 px/m étirée ×8 à l'écran).
const PRES_BUDGET_PX = 3072; // côté max du canvas fin
const PRES_PXM_MIN = 3;
const PRES_PXM_MAX = 48; // au-delà, on assume le lissage (zoom d'inspection extrême)
const LOIN_PXM = 0.25; // px/m — la ville entière d'un coup

// Rasters cachés, recalculés seulement quand le plan change, que la caméra
// sort de la fenêtre fine, ou que le zoom change d'échelle. Module-état
// assumé : un seul canvas, un seul plan.
let cachePlan = null; // le plan pour lequel dessins et rasters sont valides
let dessins = null; // les Path2D cuits une fois
let rasterLoin = null; // { canvas, x0, y0, largeur, hauteur, pxm } en mètres monde
let rasterPres = null;

/**
 * Le sol d'une ville de l'état : un Path2D par pièce, groupés par genre,
 * en mètres du monde. Une aire est fermée ; une bande reste ouverte.
 */
function cuireSol(plan) {
  const parGenre = {};
  for (const s of plan.sol ?? []) {
    const pts = s.points ?? [];
    if (pts.length < 2) continue;
    const g = SOL[s.genre];
    if (!g) continue; // un genre qu'on ne sait pas peindre reste du sol nu
    const path = new Path2D();
    if (g.toits) cheminToits(path, pts);   // un village : ses points SONT les maisons
    else {
      pts.forEach(([x, y], i) => (i ? path.lineTo(x, y) : path.moveTo(x, y)));
      if (g.aire) path.closePath();
    }
    (parGenre[s.genre] ??= []).push({ path, pts, nom: s.nom });
  }
  return {
    format: 'sol',
    parGenre,
    etiquettes: (plan.sol ?? [])
      .filter((s) => s.etiq && s.nom)
      .map((s) => ({ nom: s.nom, genre: s.genre, x: s.etiq[0], y: s.etiq[1] })),
    perces: plan.perces ?? [],
    epaisseurMur: plan.epaisseur_mur_m ?? 4,
    largeur: plan.largeur_m,
    hauteur: plan.hauteur_m,
    ombrage: plan.ombrage ?? null,
  };
}

/** Une courbe de niveau : le polygone rentré vers son centre d'un facteur t. */
function rentrer(pts, t) {
  const cx = pts.reduce((a, p) => a + p[0], 0) / pts.length;
  const cy = pts.reduce((a, p) => a + p[1], 0) / pts.length;
  const path = new Path2D();
  pts.forEach(([x, y], i) => {
    const px = cx + (x - cx) * t;
    const py = cy + (y - cy) * t;
    i ? path.lineTo(px, py) : path.moveTo(px, py);
  });
  path.closePath();
  return path;
}

/**
 * L'OMBRAGE DU RELIEF — le volume de la carte, cuit une fois en PNG par
 * `bataille/outils/osm/07_ombrage.py` et posé ici d'un `drawImage`.
 *
 * L'image est du NOIR à opacité variable, au repère exact du plan (mètre pour
 * mètre, y vers le sud) : la peindre ne change aucune couleur du sol, elle
 * creuse les pentes qui tournent le dos à la lumière. La carte garde sa
 * palette et gagne son relief.
 *
 * Elle S'EFFACE AU ZOOM DE CONTACT, comme les noms de lieux : le relief est
 * mesuré au pas de 15 m, et à trois pas d'un homme ce n'est plus une pente,
 * c'est une tache floue. On la fait fondre entre 2 et 8 px/m.
 */
function poserOmbrage(ctx, d, pxParM) {
  const img = d.ombrage;
  if (!img || !d.largeur || !d.hauteur) return;
  const a = 1 - Math.min(1, Math.max(0, (pxParM - 2) / 6));
  if (a <= 0.01) return;
  ctx.save();
  ctx.globalAlpha = a;
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(img, 0, 0, d.largeur, d.hauteur);
  ctx.restore();
}

/**
 * Peint le sol dans un contexte déjà transformé (mètres du monde, sans
 * bascule). Les murs vont sur une toile à part, percés aux portes, puis
 * posés : une porte est un trou dans le mur, pas une tache sur le sol.
 */
function tracerSol(ctx, d, pxParM) {
  let ombreFaite = false;
  for (const genre of ORDRE_SOL) {
    const g = SOL[genre];
    // L'OMBRAGE se pose entre les AIRES et les BANDES : après les aplats,
    // qui le couvriraient, et avant les routes, les quais et les murs, qui
    // sont des ouvrages d'homme et ne se creusent pas d'une ombre de colline.
    if (!g.aire && !ombreFaite) {
      ombreFaite = true;
      poserOmbrage(ctx, d, pxParM);
    }
    const pieces = d.parGenre[genre];
    if (!pieces || genre === 'mur') continue;
    if (g.aire) {
      ctx.fillStyle = g.fond;
      for (const p of pieces) ctx.fill(p.path);
      ctx.strokeStyle = g.trait;
      ctx.lineWidth = g.traitLargeur ?? 0.8;
      ctx.lineJoin = 'round';
      for (const p of pieces) ctx.stroke(p.path);
      if (g.niveaux) {
        ctx.lineWidth = 0.6;
        for (const p of pieces)
          for (let n = 1; n <= g.niveaux; n++) ctx.stroke(rentrer(p.pts, 1 - n / (g.niveaux + 1)));
      }
    } else {
      ctx.strokeStyle = g.trait;
      ctx.lineWidth = g.largeur;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      for (const p of pieces) ctx.stroke(p.path);
    }
  }
  if (!ombreFaite) poserOmbrage(ctx, d, pxParM);
  const murs = d.parGenre.mur;
  if (!murs) return;
  const toile = document.createElement('canvas');
  toile.width = ctx.canvas.width;
  toile.height = ctx.canvas.height;
  const c = toile.getContext('2d');
  c.setTransform(ctx.getTransform());
  const g = SOL.mur;
  c.lineCap = 'butt';
  c.lineJoin = 'miter';
  c.strokeStyle = g.bord;
  c.lineWidth = d.epaisseurMur + 1.2;
  for (const p of murs) c.stroke(p.path);
  c.strokeStyle = g.trait;
  c.lineWidth = d.epaisseurMur;
  for (const p of murs) c.stroke(p.path);
  c.globalCompositeOperation = 'destination-out';
  for (const t of d.perces) {
    c.beginPath();
    c.arc(t.ou[0], t.ou[1], t.rayon_m, 0, Math.PI * 2);
    c.fill();
  }
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(toile, 0, 0);
  ctx.restore();
}

/** Parse les chemins SVG du plan UNE fois (repère PLAN). */
function cuireDessins(plan) {
  if (plan.sol) return cuireSol(plan);
  return {
    format: 'plan2d',
    eau: plan.region?.eau ? new Path2D(plan.region.eau) : null,
    niveaux: (plan.niveaux ?? []).map((n) => new Path2D(n.d)),
    // les voies, du plus gros au plus fin (l'ordre d'itération de l'objet)
    voies: Object.entries(plan.voies ?? {}).map(([rang, d]) => ({
      largeur: LARGEURS_VOIES[rang] ?? 4,
      path: new Path2D(d),
    })),
    bati: Object.values(plan.bati ?? {}).map((d) => new Path2D(d)),
    courtine: plan.rempart?.courtine ? new Path2D(plan.rempart.courtine) : null,
    epaisseurMur: plan.rempart?.epaisseur_m ?? 6,
    tours: plan.rempart?.tours ? new Path2D(plan.rempart.tours) : null,
    hauteurPlan: (plan.bornes_coeur ?? [0, 0, 5280, 3600])[3],
  };
}

/** Dessine toutes les couches dans un contexte déjà transformé (repère PLAN). */
function tracerPlan(ctx, d) {
  if (d.eau) {
    ctx.fillStyle = COULEURS.eau;
    ctx.fill(d.eau);
  }
  ctx.strokeStyle = COULEURS.niveau;
  ctx.lineWidth = 1.5;
  for (const n of d.niveaux) ctx.stroke(n);
  ctx.strokeStyle = COULEURS.voie;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  for (const v of d.voies) {
    ctx.lineWidth = v.largeur;
    ctx.stroke(v.path);
  }
  ctx.fillStyle = COULEURS.bati;
  ctx.strokeStyle = COULEURS.batiTrait;
  ctx.lineWidth = 0.4;
  for (const b of d.bati) {
    ctx.fill(b);
    ctx.stroke(b);
  }
  if (d.courtine) {
    ctx.strokeStyle = COULEURS.mur;
    ctx.lineWidth = d.epaisseurMur;
    ctx.stroke(d.courtine);
  }
  if (d.tours) {
    ctx.fillStyle = COULEURS.tour;
    ctx.fill(d.tours);
  }
}

/**
 * Fabrique un raster couvrant le rectangle MONDE donné.
 * Transformation : x_px = (x_plan − x0)·s, y_px = (H − y_plan − y0)·s —
 * la bascule nord/sud est ici.
 */
function fabriquerRaster(d, x0, y0, largeur, hauteur, pxParM) {
  const canvas = document.createElement('canvas');
  canvas.width = Math.ceil(largeur * pxParM);
  canvas.height = Math.ceil(hauteur * pxParM);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = COULEURS.sol;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  if (d.format === 'sol') {
    // déjà en mètres du monde, l'Y dans le bon sens : pas de bascule
    ctx.setTransform(pxParM, 0, 0, pxParM, -x0 * pxParM, -y0 * pxParM);
    tracerSol(ctx, d, pxParM);
  } else {
    ctx.setTransform(pxParM, 0, 0, -pxParM, -x0 * pxParM, (d.hauteurPlan - y0) * pxParM);
    tracerPlan(ctx, d);
  }
  return { canvas, x0, y0, largeur, hauteur, pxm: pxParM };
}

/** Le raster couvre-t-il confortablement ce point ? (marge : le quart) */
function couvre(r, p) {
  const marge = r.largeur / 4;
  return (
    p.x > r.x0 + marge && p.x < r.x0 + r.largeur - marge &&
    p.y > r.y0 + marge && p.y < r.y0 + r.hauteur - marge
  );
}

/**
 * Dessine l'INTERSECTION visible du raster (jamais le raster entier : à
 * 24 px/m, la ville entière ferait une destination de ~126 000 px — au-delà
 * de ce qu'un canvas accepte, l'appel échoue en silence).
 */
function dessinerRaster(ctx, camera, r) {
  const ppm = camera.echelle();
  const hg = camera.versMonde({ x: 0, y: 0 });
  const bd = camera.versMonde({ x: ctx.canvas.clientWidth, y: ctx.canvas.clientHeight });
  const x0 = Math.max(r.x0, hg.x);
  const y0 = Math.max(r.y0, hg.y);
  const x1 = Math.min(r.x0 + r.largeur, bd.x);
  const y1 = Math.min(r.y0 + r.hauteur, bd.y);
  if (x1 <= x0 || y1 <= y0) return;
  const s = r.canvas.width / r.largeur; // px raster par mètre
  const e = camera.versEcran({ x: x0, y: y0 });
  ctx.drawImage(
    r.canvas,
    (x0 - r.x0) * s, (y0 - r.y0) * s, (x1 - x0) * s, (y1 - y0) * s,
    e.x, e.y, (x1 - x0) * ppm, (y1 - y0) * ppm
  );
}

// Les noms s'effacent entre ces deux échelles (px/m) : pleins en dessous,
// absents au-dessus. Au-delà, on est dans la rue.
const NOMS_PLEINS_PXM = 2;
const NOMS_EFFACES_PXM = 7;

/** Les noms de lieux, en toutes lettres, avec un halo pour tenir sur le sol. */
function dessinerNoms(ctx, camera, d) {
  const ppm = camera.echelle();
  const alpha = Math.min(1, Math.max(0, (NOMS_EFFACES_PXM - ppm) / (NOMS_EFFACES_PXM - NOMS_PLEINS_PXM)));
  if (alpha <= 0) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round';
  for (const n of d.etiquettes) {
    const e = camera.versEcran({ x: n.x, y: n.y });
    if (e.x < -200 || e.y < -40 || e.x > ctx.canvas.clientWidth + 200 || e.y > ctx.canvas.clientHeight + 40) continue;
    const eau = n.genre === 'eau';
    const mur = n.genre === 'mur';
    ctx.font = eau ? 'italic 13px Georgia, serif' : mur ? '11px Georgia, serif' : '12px Georgia, serif';
    const texte = eau ? n.nom.toUpperCase().split('').join('\u2009') : n.nom;
    ctx.lineWidth = 3;
    ctx.strokeStyle = 'rgba(20, 16, 12, 0.85)';
    ctx.strokeText(texte, e.x, e.y);
    ctx.fillStyle = eau ? 'rgba(150, 190, 205, 0.9)' : mur ? 'rgba(200, 190, 170, 0.8)' : 'rgba(225, 200, 150, 0.9)';
    ctx.fillText(texte, e.x, e.y);
  }
  ctx.restore();
}

export function dessinerTerrain(ctx, camera, vues) {
  const ppm = camera.echelle();

  // ── le plan cuit (raster deux niveaux) ──
  if (vues.plan) {
    if (cachePlan !== vues.plan) {
      cachePlan = vues.plan;
      dessins = cuireDessins(vues.plan);
      const B = dessins.format === 'sol'
        ? [0, 0, dessins.largeur, dessins.hauteur]
        : (vues.plan.bornes_coeur ?? [0, 0, 5280, 3600]);
      rasterLoin = fabriquerRaster(dessins, B[0], B[1], B[2] - B[0], B[3] - B[1], LOIN_PXM);
      rasterPres = null;
    }
    // le centre de l'écran en monde : la fenêtre fine le suit ; sa résolution
    // suit le zoom (re-cuite quand l'échelle change vraiment — facteur 1,5)
    const centre = camera.versMonde({ x: ctx.canvas.clientWidth / 2, y: ctx.canvas.clientHeight / 2 });
    const pxmCible = Math.min(PRES_PXM_MAX, Math.max(PRES_PXM_MIN, ppm));
    const echelleObsolete = rasterPres && (pxmCible > rasterPres.pxm * 1.5 || pxmCible < rasterPres.pxm / 1.5);
    if (!rasterPres || echelleObsolete || !couvre(rasterPres, centre)) {
      const cote = Math.min(640, PRES_BUDGET_PX / pxmCible);
      rasterPres = fabriquerRaster(dessins, centre.x - cote / 2, centre.y - cote / 2, cote, cote, pxmCible);
    }
    ctx.imageSmoothingEnabled = true;
    dessinerRaster(ctx, camera, rasterLoin);
    dessinerRaster(ctx, camera, rasterPres);
    if (dessins.format === 'sol') dessinerNoms(ctx, camera, dessins);
  }

  // ── la vérité du masque, au zoom de contact (l'écart dessin/masque se voit) ──
  // Un outil de debug : sur la carte seule (racine, sans habillage), on ne
  // montre pas la grille — le dessin y fait foi pour l'oeil.
  if (vues.habillage !== false && vues.terrain.casesBloqueesDans && ppm >= 8) {
    const hg = camera.versMonde({ x: 0, y: 0 });
    const bd = camera.versMonde({ x: ctx.canvas.clientWidth, y: ctx.canvas.clientHeight });
    ctx.strokeStyle = 'rgba(220,190,140,0.18)';
    ctx.lineWidth = 1;
    for (const o of vues.terrain.casesBloqueesDans({ x: hg.x, y: hg.y, largeur: bd.x - hg.x, hauteur: bd.y - hg.y })) {
      const e = camera.versEcran({ x: o.x, y: o.y });
      ctx.strokeRect(e.x, e.y, o.largeur * ppm, o.hauteur * ppm);
    }
  }

  // ── les obstacles rectangulaires posés (maisons des scénarios) ──
  for (const o of vues.terrain.obstacles()) {
    const e = camera.versEcran({ x: o.x, y: o.y });
    const l = o.largeur * ppm;
    const h = o.hauteur * ppm;
    ctx.fillStyle = '#463f33';
    ctx.fillRect(e.x, e.y, l, h);
    ctx.strokeStyle = '#6d6450';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(e.x, e.y, l, h);
  }
}
