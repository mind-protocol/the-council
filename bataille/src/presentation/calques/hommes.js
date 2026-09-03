/**
 * 🖥️ Calque hommes — les corps : ronds vus du dessus, couleur = livrée,
 * LANCE orientée par le cap (l'orientation se voit parce que la lance se
 * voit — physicalisation), panache du chef.
 * La POSTURE se voit : lance LEVÉE (raccourcie, pointe brillante) = prêt à
 * engager — c'est le canal physique de la readiness. Les coups reçus
 * FLASHENT (anneau rouge bref, mémoire locale au calque) puis RESTENT : une
 * tache sombre sur la cotte par coup encaissé — le corps porte son histoire.
 * Le SOUFFLE se voit : à bout, la pointe de l'arme tombe hors de l'axe.
 * Lit vues.corps, vues.equipement (❤️), vues.blessuresDe (❤️), vues.souffleDe (❤️).
 * Les MORTS ont leur propre calque (gisants.js) : un corps tombé, sa flaque
 * qui s'élargit, son arme lâchée — dessinés SOUS les vivants.
 * Le FUYARD détale sans sa lance en garde — la déroute se lit de loin.
 * Le CHEVAL est une bête, pas une tache : robe tirée d'une distribution,
 * housse aux couleurs du cavalier ; dessiné AVANT les hommes, pour que le
 * cavalier se voie dessus.
 * Le CHEF porte un PENNON au bout de sa hampe, à la livrée : l'unité se
 * reconnaît à sa bannière, comme sur le champ.
 * Les BRAS se voient : le droit sur l'arme, le gauche à l'écu ou aux rênes.
 * @viz registre-corps, bras, renes, livree-physique, cap, cap-integre, nom-panache, equipement-lance, armes-differenciees, bouclier-parade, readiness-regard, blessures, acte-frapper, marche-arriere-lente, mort-gisant, etat-fuir, choc-renverse, dracarys, attelage, refus-monture, robe-cheval, pennon, usure-visible, arbalete
 */

import { vignetteHomme, vignetteCheval, couleurLivree, robeDe, varianteDe } from '../vignettes.js';
import { dessinerBras, dessinerJambes } from './membres.js';
import { dessinerGisants } from './gisants.js';

// mémoire locale au calque (viz seulement) : blessures vues → flash bref
const blessuresVues = new Map();
const flashs = new Map();
// longueur d'arme AFFICHÉE par corps : elle GLISSE vers la cible (lever /
// baisser / rengainer en fuite sont des gestes, pas des téléportations)
const armesAffichees = new Map();
// LE PAS. La phase de marche ne suit PAS le temps mais la DISTANCE parcourue :
// un homme arrete ne remue pas, et un homme qui court balance plus vite sans
// qu'on ait a le lui dire. On cumule donc le chemin fait, par corps.
const cheminParcouru = new Map();
const dernierePos = new Map();
const LONGUEUR_DE_PAS = 0.75; // m — un cycle complet (deux pas) tous les 1,5 m
const FOULEE_CHEVAL = 1.6; // m — la foulée d'un cheval, plus longue

// En dessous : un rond (il y a un homme là). Au-dessus : la vignette — des
// épaules, une tête, et tout ce qui se porte.
const SEUIL_VIGNETTE = 12; // px/m

/** Un pseudo-hasard stable par corps (viz seulement) : où tombent les taches. */
function bruit(id, i) {
  let h = ((id + 1) * 374761393 + i * 668265263) >>> 0;
  h = ((h ^ (h >>> 13)) * 1274126177) >>> 0;
  return (h >>> 8) / 16777216;
}

/**
 * LE PAS d'un corps, mesuré une fois par frame : la phase suit la DISTANCE
 * parcourue (un homme arrêté ne remue pas), l'allure suit la vitesse. Les
 * épaules roulent dessus, et les bras BALANCENT dessus — le droit devant
 * quand le gauche est derrière, comme on marche. En selle, on ne marche pas.
 */
function avancerPas(c, enSelle, foulee = LONGUEUR_DE_PAS) {
  const prec = dernierePos.get(c.id);
  let chemin = cheminParcouru.get(c.id) ?? 0;
  if (prec) chemin += Math.hypot(c.pos.x - prec.x, c.pos.y - prec.y);
  cheminParcouru.set(c.id, chemin);
  dernierePos.set(c.id, { x: c.pos.x, y: c.pos.y });
  const allure = enSelle ? 0 : Math.min(1, Math.hypot(c.vel.x, c.vel.y) / 2.5);
  const phase = (chemin / foulee) * Math.PI;
  // le balancement des bras, en mètres le long du cap : ± 0,16 m à pleine allure
  return { phase, allure, enSelle, balance: Math.sin(phase) * 0.16 * allure };
}

/** La bête : vignette au zoom, silhouette allongée de loin — jamais la livrée du cavalier sur la robe. */
function dessinerCheval(ctx, e, c, ppm, chef) {
  const robe = robeDe(c.id);
  if (ppm >= SEUIL_VIGNETTE) {
    dessinerJambes(ctx, e, c, ppm, avancerPas(c, false, FOULEE_CHEVAL), robe);
    const v = vignetteCheval(robe, couleurLivree(c.livree), ppm, c.rayon, varianteDe(c.id), chef);
    const k = ppm / v.p;
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(c.cap);
    ctx.scale(k, k);
    ctx.drawImage(v.toile, -v.demi, -v.demi);
    ctx.restore();
    return;
  }
  ctx.save();
  ctx.translate(e.x, e.y);
  ctx.rotate(c.cap);
  ctx.beginPath();
  ctx.ellipse(0, 0, 1.05 * ppm, c.rayon * ppm, 0, 0, Math.PI * 2);
  ctx.fillStyle = robe;
  ctx.fill();
  ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
  ctx.lineWidth = 1.2;
  ctx.stroke();
  // la housse, de loin : une barre à la livrée en travers du dos
  ctx.beginPath();
  ctx.moveTo(0, -c.rayon * 0.8 * ppm);
  ctx.lineTo(0, c.rayon * 0.8 * ppm);
  ctx.strokeStyle = couleurLivree(c.livree);
  ctx.lineWidth = Math.max(1.5, 0.3 * ppm);
  ctx.stroke();
  ctx.restore();
}

/** Le refus : le cheval se dérobe — chevron orangé vers la fenêtre regardée. */
function dessinerRefus(ctx, e, refus, camera) {
  const g = camera.versEcran(refus.regard);
  ctx.strokeStyle = `rgba(240, 160, 70, ${0.25 + 0.65 * refus.intensite})`;
  ctx.lineWidth = 2;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(e.x, e.y);
  ctx.lineTo(g.x, g.y);
  ctx.stroke();
  ctx.setLineDash([]);
  const dx = g.x - e.x, dy = g.y - e.y;
  const d = Math.hypot(dx, dy) || 1;
  const px = -dy / d, py = dx / d;
  ctx.beginPath();
  ctx.moveTo(g.x + px * 8 - (dx / d) * 6, g.y + py * 8 - (dy / d) * 6);
  ctx.lineTo(g.x, g.y);
  ctx.lineTo(g.x - px * 8 - (dx / d) * 6, g.y - py * 8 - (dy / d) * 6);
  ctx.stroke();
}

/**
 * L'ARME : dans la MAIN DROITE, longueur du paquetage (❤️), LEVÉE quand prêt
 * (raccourcie, pointe brillante). À bout de souffle la pointe TOMBE : le bras
 * s'ouvre vers l'extérieur, l'arme n'est plus dans l'axe. L'arbalète est un
 * arc en travers de la main. Le chef porte un pennon au bout de sa hampe.
 */
function dessinerArme(ctx, e, c, eq, ppm, souffle, fond, pas) {
  const levee = c.posture === 'pret';
  const avantCible =
    c.posture === 'fuit' ? 0 : levee ? Math.max(0.3, eq.longueurRendue * 0.35) : eq.longueurRendue;
  const avant = (armesAffichees.get(c.id) ?? avantCible) + (avantCible - (armesAffichees.get(c.id) ?? avantCible)) * 0.12;
  armesAffichees.set(c.id, avant);
  // l'épuisement : jusqu'à un demi-radian d'ouverture quand le souffle est parti
  const chute = souffle < 0.4 ? (0.4 - souffle) * 1.3 : 0;
  const cap = c.cap + chute;
  const dx = Math.cos(cap), dy = Math.sin(cap);
  // la main droite balance avec le pas — moins en garde, où le bras est tenu
  const bal = pas.balance * (levee ? 0.3 : 1);
  const mx = e.x - Math.sin(c.cap) * c.rayon * 0.7 * ppm + Math.cos(c.cap) * bal * ppm; // main droite
  const my = e.y + Math.cos(c.cap) * c.rayon * 0.7 * ppm + Math.sin(c.cap) * bal * ppm;
  if (avant >= 0.08) { // sous ce seuil : rengainée, rien à dessiner
    const bx = mx + dx * avant * ppm, by = my + dy * avant * ppm; // le bout
    ctx.beginPath();
    ctx.moveTo(mx - dx * (levee ? 0.1 : 0.3) * ppm, my - dy * (levee ? 0.1 : 0.3) * ppm);
    ctx.lineTo(bx, by);
    ctx.strokeStyle = levee ? '#e8dfc0' : '#c9c2a6';
    ctx.lineWidth = Math.max(1, 0.06 * ppm);
    ctx.stroke();
    if (levee) {
      ctx.beginPath();
      ctx.arc(bx, by, Math.max(1.5, 0.09 * ppm), 0, Math.PI * 2);
      ctx.fillStyle = '#f4ead0';
      ctx.fill();
    }
    // le pennon du chef, sous le fer d'une hampe assez longue pour le porter
    if (c.panache && avant >= 1.2 && ppm >= 8) {
      const fx = bx - dx * 0.12 * ppm, fy = by - dy * 0.12 * ppm;
      const ondule = Math.sin(performance.now() / 160 + c.id) * 0.12;
      const qx = -dy, qy = dx; // en travers
      ctx.beginPath();
      ctx.moveTo(fx, fy);
      ctx.lineTo(fx - dx * 0.55 * ppm + qx * (0.16 + ondule) * ppm, fy - dy * 0.55 * ppm + qy * (0.16 + ondule) * ppm);
      ctx.lineTo(fx - dx * 0.3 * ppm + qx * 0.04 * ppm, fy - dy * 0.3 * ppm + qy * 0.04 * ppm);
      ctx.closePath();
      ctx.fillStyle = fond;
      ctx.fill();
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }
  if (eq.arc && ppm >= 8) {
    // l'arbalète : l'arbrier dans l'axe, l'arc en travers, tenue devant
    const cx = Math.cos(c.cap), cy = Math.sin(c.cap);
    const ax = mx + cx * 0.25 * ppm, ay = my + cy * 0.25 * ppm;
    const qx = -cy, qy = cx;
    ctx.beginPath();
    ctx.moveTo(mx - cx * 0.15 * ppm, my - cy * 0.15 * ppm);
    ctx.lineTo(ax + cx * 0.2 * ppm, ay + cy * 0.2 * ppm);
    ctx.strokeStyle = '#6e5a3c';
    ctx.lineWidth = Math.max(1.5, 0.09 * ppm);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ax - qx * 0.32 * ppm, ay - qy * 0.32 * ppm);
    ctx.quadraticCurveTo(ax + cx * 0.1 * ppm, ay + cy * 0.1 * ppm, ax + qx * 0.32 * ppm, ay + qy * 0.32 * ppm);
    ctx.strokeStyle = '#d8cfae';
    ctx.lineWidth = Math.max(1, 0.05 * ppm);
    ctx.stroke();
  }
}

/** Le BOUCLIER au bras gauche : un écu à la livrée, bordé, l'umbo au centre. */
function dessinerBouclier(ctx, e, c, eq, ppm, fond, pas) {
  const bal = -pas.balance * 0.5; // en opposition du bras droit, tenu plus court
  const gx = e.x + Math.sin(c.cap) * c.rayon * 0.95 * ppm + Math.cos(c.cap) * bal * ppm; // bras gauche
  const gy = e.y - Math.cos(c.cap) * c.rayon * 0.95 * ppm + Math.sin(c.cap) * bal * ppm;
  const r = eq.bouclier.rayonRendu * ppm;
  ctx.beginPath();
  ctx.arc(gx, gy, r, 0, Math.PI * 2);
  if (ppm >= SEUIL_VIGNETTE) {
    const g = ctx.createRadialGradient(gx - r * 0.3, gy - r * 0.3, r * 0.1, gx, gy, r);
    g.addColorStop(0, fond);
    g.addColorStop(1, 'rgba(0, 0, 0, 0.55)');
    ctx.fillStyle = g;
    ctx.fill();
    ctx.fillStyle = fond;
    ctx.globalAlpha = 0.6;
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = 'rgba(20, 16, 10, 0.75)';
    ctx.lineWidth = Math.max(1, r * 0.16);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(gx, gy, Math.max(1, r * 0.22), 0, Math.PI * 2);
    ctx.fillStyle = '#d9d2bd';
    ctx.fill();
  } else {
    ctx.fillStyle = '#7a6f52';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.4)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}

/** Les coups encaissés restent : une tache sombre par coup, sur la cotte. */
function dessinerBlessures(ctx, e, c, b, ppm) {
  const n = Math.min(4, Math.floor(b));
  for (let i = 0; i < n; i++) {
    const a = bruit(c.id, i) * Math.PI * 2;
    const d = (0.25 + 0.5 * bruit(c.id, i + 7)) * c.rayon * ppm;
    ctx.beginPath();
    ctx.arc(e.x + Math.cos(a) * d, e.y + Math.sin(a) * d, Math.max(1.2, (0.07 + 0.04 * bruit(c.id, i + 13)) * ppm), 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(90, 16, 16, 0.85)';
    ctx.fill();
  }
}

/** Le corps d'un homme : rond de loin, vignette tournée et balancée au pas de près. */
function dessinerCorps(ctx, e, c, ppm, fond, pas) {
  if (ppm < SEUIL_VIGNETTE) {
    ctx.beginPath();
    ctx.arc(e.x, e.y, c.rayon * ppm, 0, Math.PI * 2);
    ctx.fillStyle = fond;
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.45)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    return;
  }
  // LES PIEDS, sous le corps : deux semelles qui dépassent devant et derrière
  // à chaque appui. À l'arrêt ils rentrent sous les épaules et ne se voient
  // plus — un homme immobile n'a pas de pieds vus du dessus.
  if (!pas.enSelle) {
    const cx = Math.cos(c.cap), cy = Math.sin(c.cap);
    const qx = -cy, qy = cx;
    const av = Math.sin(pas.phase) * 0.22 * pas.allure;
    for (const [lat, sens] of [[0.13, 1], [-0.13, -1]]) {
      const fx = e.x + cx * sens * av * ppm + qx * lat * ppm;
      const fy = e.y + cy * sens * av * ppm + qy * lat * ppm;
      ctx.save();
      ctx.translate(fx, fy);
      ctx.rotate(c.cap);
      ctx.beginPath();
      ctx.ellipse(0, 0, 0.13 * ppm, 0.065 * ppm, 0, 0, Math.PI * 2);
      ctx.fillStyle = '#3a2c1c';
      ctx.fill();
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.restore();
    }
  }
  // la vignette est dessinee cap vers la droite : on tourne le contexte,
  // on ne stocke pas d'orientations. Un drawImage au lieu de six traits.
  const v = vignetteHomme(fond, !!c.panache, ppm, c.rayon, varianteDe(c.id));
  const k = (c.rayon * ppm) / v.r; // du palier de la vignette au zoom reel

  // LE BALANCEMENT DU PAS — vu du dessus, marcher c'est rouler des
  // epaules et se deporter d'un rien a chaque appui. Deux fois rien, et
  // c'est ce qui separe un rang qui AVANCE d'un rang qui glisse. Ca ne
  // coute aucune vignette de plus : la meme image, tournee un peu plus.
  const { phase, allure } = pas;
  const roulis = Math.sin(phase) * 0.13 * allure;          // rad
  const appui = Math.sin(phase) * c.rayon * 0.16 * allure; // m, en travers

  ctx.save();
  ctx.translate(e.x, e.y);
  ctx.rotate(c.cap + roulis);
  ctx.scale(k, k);
  ctx.drawImage(v.toile, -v.demi, appui * ppm / k - v.demi);
  ctx.restore();
}

export function dessinerHommes(ctx, camera, vues) {
  const ppm = camera.echelle();
  const corps = [...vues.corps()].filter((c) => !c.vol); // le ciel appartient au calque oiseaux

  // ON NE DESSINE QUE CE QUI EST VISIBLE. Sur une grande carte, projeter est
  // gratuit mais dessiner un corps (arcs, bras, jambes, arme) ne l'est pas :
  // un corps hors du canvas coute pour rien. Marge large (bras, lance, panache
  // debordent le centre) pour ne jamais couper un corps au bord.
  const W = ctx.canvas.width, H = ctx.canvas.height;
  const marge = 4 * ppm; // m -> px : allonge d'arme + rayon, avec du jeu
  const visible = (e) => e.x >= -marge && e.x <= W + marge && e.y >= -marge && e.y <= H + marge;

  // Qui monte quoi : le registre dit cavalier → monture, on renverse pour
  // que la bête sache si elle porte un chef (sa housse le dit).
  const cavalierDe = new Map();
  for (const c of corps) {
    if (c.gabarit === 'cheval') continue;
    const m = vues.montureDe?.(c.id);
    if (m != null) cavalierDe.set(m, c);
  }

  // LES MORTS D'ABORD, tous ensemble : on marche SUR ses morts, jamais
  // dessous. Leur flaque reste quand les vivants sont partis.
  dessinerGisants(ctx, camera, vues, corps, visible, SEUIL_VIGNETTE);

  // LES BÊTES ENSUITE : le cavalier est un autre corps, il se dessine dessus.
  for (const c of corps) {
    if (c.gabarit !== 'cheval' || c.posture === 'gisant') continue;
    const e = camera.versEcran(c.pos);
    if (!visible(e)) continue;
    dessinerCheval(ctx, e, c, ppm, !!cavalierDe.get(c.id)?.panache);
  }

  for (const c of corps) {
    if (c.gabarit === 'cheval' || c.posture === 'gisant') continue;
    const e = camera.versEcran(c.pos);
    if (!visible(e)) continue;
    const fond = couleurLivree(c.livree);

    const refus = vues.refus?.()?.get(c.id);
    if (refus?.regard) dessinerRefus(ctx, e, refus, camera);

    // le RENVERSÉ : jeté à terre (plein pâle, arme lâchée) — il se relèvera
    if (c.posture === 'renverse') {
      ctx.beginPath();
      ctx.arc(e.x, e.y, c.rayon * ppm, 0, Math.PI * 2);
      ctx.fillStyle = fond;
      ctx.globalAlpha = 0.4;
      ctx.fill();
      ctx.globalAlpha = 0.8;
      ctx.strokeStyle = '#e8e2cf';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;
      continue;
    }

    const eq = vues.equipement?.(c.id);
    const souffle = vues.souffleDe?.(c.id) ?? 1;
    const enSelle = vues.montureDe?.(c.id) != null;
    const pas = avancerPas(c, enSelle);
    // l'écu SOUS le corps : il dépasse du bras gauche, il ne cache pas l'homme
    if (eq) {
      dessinerArme(ctx, e, c, eq, ppm, souffle, fond, pas);
      if (eq.bouclier) dessinerBouclier(ctx, e, c, eq, ppm, fond, pas);
    }

    // les coups reçus flashent (anneau rouge bref)
    const b = vues.blessuresDe?.(c.id) ?? 0;
    if (b > (blessuresVues.get(c.id) ?? 0)) flashs.set(c.id, 14);
    blessuresVues.set(c.id, b);
    const flash = flashs.get(c.id) ?? 0;
    if (flash > 0) {
      flashs.set(c.id, flash - 1);
      ctx.beginPath();
      ctx.arc(e.x, e.y, c.rayon * ppm + 3.5, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(255, 60, 60, ${flash / 14})`;
      ctx.lineWidth = 2.5;
      ctx.stroke();
    }

    dessinerCorps(ctx, e, c, ppm, fond, pas);
    if (ppm >= SEUIL_VIGNETTE) {
      dessinerBras(ctx, e, c, eq, ppm, fond, enSelle, pas);
      if (b > 0) dessinerBlessures(ctx, e, c, b, ppm);
    }

    // le panache du chef : anneau doré (fait physique, se reconnaît de loin).
    // Au zoom il est deja dans la vignette — on ne le dessine qu'au loin.
    if (c.panache && ppm < SEUIL_VIGNETTE) {
      ctx.beginPath();
      ctx.arc(e.x, e.y, c.rayon * ppm + 2.5, 0, Math.PI * 2);
      ctx.strokeStyle = '#f0c674';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }
}
