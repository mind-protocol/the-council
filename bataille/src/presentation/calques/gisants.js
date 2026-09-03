/**
 * 🖥️ Calque hommes / gisants — LES MORTS, et ce qu'ils laissent au sol.
 *
 * Ils étaient un cercle vidé et un trait en travers : de loin, un champ après
 * la bataille ressemblait à un champ avant. Ici un mort est un CORPS TOMBÉ —
 * torse à plat, tête roulée, un bras jeté, les jambes ouvertes (vignette ❤️
 * livrée × variante, comme les vivants) — sous une FLAQUE qui s'élargit, avec
 * son arme lâchée à côté et son écu à plat.
 *
 * LA FLAQUE EST LA VRAIE VIZ. Un corps se lit à trente pixels ; une tache
 * sombre se lit à trois. C'est elle qui dit, d'un coup d'œil sur toute la
 * carte, où l'on s'est battu et où l'on est mort — et elle reste quand les
 * vivants sont partis.
 *
 * Son âge est mesuré au TEMPS DE L'ÉCRAN, pas à celui de la simulation : le
 * calque n'a pas accès à l'heure du monde, et une flaque qui s'étale un peu
 * plus vite en accéléré ne ment sur rien. Mémoire locale, viz seulement.
 *
 * Dessiné AVANT tout le reste : on marche sur ses morts, on ne marche pas
 * dessous.
 * @viz mort-gisant, flaque-de-sang, arme-lachee
 */

import { couleurLivree, robeDe, varianteDe, vignetteGisant, vignetteGisantCheval, melanger } from '../vignettes.js';

// premier instant où on l'a vu à terre (ms écran) — la flaque s'étale depuis
const vusMorts = new Map();
const ETALEMENT_S = 18; // le temps qu'une flaque met à prendre sa taille

/** Un pseudo-hasard stable par corps (viz seulement) : la forme de la flaque. */
function bruit(id, i) {
  let h = ((id + 1) * 374761393 + i * 668265263) >>> 0;
  h = ((h ^ (h >>> 13)) * 1274126177) >>> 0;
  return (h >>> 8) / 16777216;
}

/**
 * LA FLAQUE — un contour irrégulier, jamais un rond : le sang suit le sol.
 * Deux couches, la seconde plus sombre et plus petite, décalée sous le torse.
 * @param {number} part 0..1 — où en est son étalement
 */
function dessinerFlaque(ctx, e, c, ppm, part) {
  const grand = c.gabarit === 'cheval' ? 2.6 : 1.15;
  const r = (0.2 + 0.8 * part) * grand * ppm;
  if (r < 1.2) return; // sous le pixel, on ne peint rien
  const cotes = 11;
  // LE CONTOUR EST COURBE, jamais anguleux : une flaque n'a pas d'arêtes.
  // On passe une courbe par les MILIEUX des rayons tirés — chaque sommet
  // devient un point de contrôle, et le bord ondule au lieu de casser.
  const forme = (echelle, decalX, decalY) => {
    const pts = [];
    for (let i = 0; i < cotes; i++) {
      const a = (i / cotes) * Math.PI * 2;
      const d = r * echelle * (0.62 + 0.55 * bruit(c.id, i));
      pts.push([e.x + decalX + Math.cos(a) * d, e.y + decalY + Math.sin(a) * d * 0.8]);
    }
    ctx.beginPath();
    const mil = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    let m = mil(pts[cotes - 1], pts[0]);
    ctx.moveTo(m[0], m[1]);
    for (let i = 0; i < cotes; i++) {
      const suivant = mil(pts[i], pts[(i + 1) % cotes]);
      ctx.quadraticCurveTo(pts[i][0], pts[i][1], suivant[0], suivant[1]);
    }
    ctx.closePath();
  };
  forme(1, 0, 0);
  ctx.fillStyle = 'rgba(46, 14, 10, 0.46)';
  ctx.fill();
  forme(0.55, -Math.cos(c.cap) * r * 0.18, -Math.sin(c.cap) * r * 0.18);
  ctx.fillStyle = 'rgba(26, 7, 6, 0.55)';
  ctx.fill();
}

/** L'arme lâchée et l'écu tombé : à CÔTÉ du corps, jamais dessus. */
function dessinerArmeLachee(ctx, e, c, eq, ppm, fond) {
  if (!eq) return;
  // elle est partie de la main, à un pas du corps : on l'écarte franchement,
  // sinon elle barre le mort et on croit qu'il la tient encore
  if (eq.longueurRendue >= 0.1) {
    const cote = bruit(c.id, 20) < 0.5 ? 1 : -1;
    const a = c.cap + (Math.PI / 2) * cote + (bruit(c.id, 21) - 0.5) * 0.9;
    const dx = Math.cos(a), dy = Math.sin(a);
    const ox = e.x + dx * 1.05 * ppm;
    const oy = e.y + dy * 1.05 * ppm;
    const l = eq.longueurRendue * ppm;
    const t = a + Math.PI / 2 + (bruit(c.id, 23) - 0.5) * 0.8; // couchée en travers
    ctx.beginPath();
    ctx.moveTo(ox - Math.cos(t) * l * 0.5, oy - Math.sin(t) * l * 0.5);
    ctx.lineTo(ox + Math.cos(t) * l * 0.5, oy + Math.sin(t) * l * 0.5);
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
    ctx.lineWidth = Math.max(1.5, 0.085 * ppm);
    ctx.lineCap = 'round';
    ctx.stroke();
    ctx.strokeStyle = '#8a8470';
    ctx.lineWidth = Math.max(1, 0.05 * ppm);
    ctx.stroke();
  }
  // l'écu à plat de l'autre côté, aux couleurs ternies de sa livrée
  if (eq.bouclier) {
    const b = c.cap - Math.PI / 2 + (bruit(c.id, 22) - 0.5) * 1.1;
    const bx = e.x + Math.cos(b) * 1.0 * ppm;
    const by = e.y + Math.sin(b) * 1.0 * ppm;
    const rb = eq.bouclier.rayonRendu * ppm;
    ctx.beginPath();
    ctx.ellipse(bx, by, rb, rb * 0.86, b, 0, Math.PI * 2);
    ctx.fillStyle = melanger(fond, '#3a2f1e', 0.5);
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.55)';
    ctx.lineWidth = Math.max(1, rb * 0.18);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(bx, by, Math.max(1, rb * 0.2), 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(150, 143, 125, 0.8)';
    ctx.fill();
  }
}

/**
 * TOUS LES MORTS, en une passe, sous les vivants.
 * @param {number} seuilVignette px/m — sous ce zoom, un mort est une tache
 */
export function dessinerGisants(ctx, camera, vues, corps, visible, seuilVignette) {
  const ppm = camera.echelle();
  const maintenant = performance.now();

  for (const c of corps) {
    if (c.posture !== 'gisant') continue;
    const e = camera.versEcran(c.pos);
    if (!visible(e)) continue;

    let depuis = vusMorts.get(c.id);
    if (depuis === undefined) vusMorts.set(c.id, (depuis = maintenant));
    const part = Math.min(1, (maintenant - depuis) / (ETALEMENT_S * 1000));

    dessinerFlaque(ctx, e, c, ppm, part);

    // DE LOIN : la tache suffit, et c'est elle qu'on veut voir. De près : le
    // corps, tourné par son cap — c'est dans cet axe qu'il est tombé.
    if (ppm < seuilVignette) {
      ctx.beginPath();
      ctx.ellipse(e.x, e.y, c.rayon * ppm * 1.2, c.rayon * ppm * 0.62, c.cap, 0, Math.PI * 2);
      ctx.fillStyle = c.gabarit === 'cheval' ? robeDe(c.id) : couleurLivree(c.livree);
      ctx.globalAlpha = 0.45;
      ctx.fill();
      ctx.globalAlpha = 1;
      continue;
    }

    const v = c.gabarit === 'cheval'
      ? vignetteGisantCheval(robeDe(c.id), ppm, c.rayon, varianteDe(c.id))
      : vignetteGisant(couleurLivree(c.livree), ppm, c.rayon, varianteDe(c.id));
    const k = c.gabarit === 'cheval' ? ppm / v.p : (c.rayon * ppm) / v.r;
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(c.cap);
    ctx.scale(k, k);
    ctx.drawImage(v.toile, -v.demi, -v.demi);
    ctx.restore();

    if (c.gabarit !== 'cheval') dessinerArmeLachee(ctx, e, c, vues.equipement?.(c.id), ppm, couleurLivree(c.livree));
  }
}
