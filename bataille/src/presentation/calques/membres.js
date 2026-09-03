/**
 * 🖥️ Calque hommes / membres — ce qui dépasse du corps et bouge avec le pas.
 * Les BRAS : deux courbes à coude qui partent des épaules, le droit vers
 * l'arme, le gauche vers l'écu, l'arbrier ou les RÊNES (en selle, elles
 * courent jusqu'à la tête du cheval). Les JAMBES du cheval : quatre traits
 * sous la bête, qui battent avec la foulée. Tout est dessiné par frame — deux
 * traits et une main, rien à mettre en vignette. Appelé par hommes.js.
 * @viz bras, renes, jambes-cheval
 */

import { COULEUR_PEAU, assombrir } from '../vignettes.js';

/**
 * LES JAMBES du cheval : quatre traits sous le corps, qui dépassent aux
 * flancs et battent avec la foulée — les diagonales ensemble, comme au trot.
 * Dessinées AVANT la vignette : on ne voit que ce qui sort du corps.
 */
export function dessinerJambes(ctx, e, c, ppm, pas, robe) {
  const cx = Math.cos(c.cap), cy = Math.sin(c.cap);
  const qx = -cy, qy = cx;
  const bat = Math.sin(pas.phase) * 0.3 * pas.allure; // m, le long du cap
  for (const [ax, ay, sens] of [[0.72, 0.62, 1], [0.72, -0.62, -1], [-0.72, 0.62, -1], [-0.72, -0.62, 1]]) {
    const ox = e.x + cx * ax * ppm + qx * ay * c.rayon * ppm;
    const oy = e.y + cy * ax * ppm + qy * ay * c.rayon * ppm;
    const hx = ox + cx * (sens * bat + (ax > 0 ? 0.18 : -0.18)) * ppm + qx * ay * 0.35 * ppm;
    const hy = oy + cy * (sens * bat + (ax > 0 ? 0.18 : -0.18)) * ppm + qy * ay * 0.35 * ppm;
    // un FUSEAU : large à la cuisse, fin au canon, et le sabot au bout
    const dx = hx - ox, dy = hy - oy;
    const d = Math.hypot(dx, dy) || 1;
    const nx = -dy / d, ny = dx / d;
    const haut = Math.max(1.4, 0.11 * ppm), bas = Math.max(0.7, 0.045 * ppm);
    ctx.beginPath();
    ctx.moveTo(ox + nx * haut, oy + ny * haut);
    ctx.quadraticCurveTo(ox + dx * 0.45 + nx * haut * 0.5, oy + dy * 0.45 + ny * haut * 0.5, hx + nx * bas, hy + ny * bas);
    ctx.lineTo(hx - nx * bas, hy - ny * bas);
    ctx.quadraticCurveTo(ox + dx * 0.45 - nx * haut * 0.5, oy + dy * 0.45 - ny * haut * 0.5, ox - nx * haut, oy - ny * haut);
    ctx.closePath();
    ctx.fillStyle = assombrir(robe, 0.25);
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.lineWidth = Math.max(1, 0.03 * ppm);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(hx, hy, Math.max(1, 0.05 * ppm), 0, Math.PI * 2);
    ctx.fillStyle = '#1e1814';
    ctx.fill();
  }
}

/**
 * LES BRAS. Vus du dessus, deux traits qui partent des épaules : le droit va
 * à la poignée de l'arme, le gauche à l'écu — ou, en selle, aux RÊNES, qui
 * courent jusqu'à la tête du cheval. C'est ce qui fait qu'un cavalier tient
 * sa bête au lieu d'être posé dessus. Par frame, deux traits et une main :
 * rien à mettre en vignette.
 */
export function dessinerBras(ctx, e, c, eq, ppm, fond, enSelle, pas) {
  const cx = Math.cos(c.cap), cy = Math.sin(c.cap);
  const balD = pas.balance * (c.posture === 'pret' ? 0.3 : 1); // bras droit : avec le pas
  const balG = -pas.balance * (eq?.bouclier ? 0.5 : 1); // bras gauche : en opposition
  const qx = -cy, qy = cx; // vers la droite de l'homme
  const manche = assombrir(fond, 0.25);
  const epaisseur = Math.max(1.6, 0.14 * ppm);
  // un bras a un COUDE : il sort de l'épaule vers le dehors, puis rentre vers
  // la main. Une courbe dont le contrôle est poussé sur le côté, dans un
  // contour sombre comme le reste du corps, et une main qui a une taille.
  const bras = (ex, ey, mx, my, dehors) => {
    const kx = (ex + mx) / 2 + dehors * qx * 0.14 * ppm;
    const ky = (ey + my) / 2 + dehors * qy * 0.14 * ppm;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.quadraticCurveTo(kx, ky, mx, my);
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.lineWidth = epaisseur + Math.max(1, 0.05 * ppm);
    ctx.stroke();
    ctx.strokeStyle = manche;
    ctx.lineWidth = epaisseur;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(mx, my, Math.max(1.3, 0.085 * ppm), 0, Math.PI * 2);
    ctx.fillStyle = COULEUR_PEAU;
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.55)';
    ctx.lineWidth = Math.max(0.8, 0.03 * ppm);
    ctx.stroke();
  };
  // l'épaule droite / gauche : au bord des épaules, un peu en arrière
  const edx = e.x + qx * c.rayon * 0.72 * ppm - cx * 0.05 * ppm;
  const edy = e.y + qy * c.rayon * 0.72 * ppm - cy * 0.05 * ppm;
  const egx = e.x - qx * c.rayon * 0.72 * ppm - cx * 0.05 * ppm;
  const egy = e.y - qy * c.rayon * 0.72 * ppm - cy * 0.05 * ppm;
  // la main droite : sur l'arme, devant l'épaule
  const avant = (c.posture === 'pret' ? 0.32 : 0.18) + balD;
  bras(edx, edy, edx + cx * avant * ppm + qx * 0.06 * ppm, edy + cy * avant * ppm + qy * 0.06 * ppm, 1);
  if (enSelle) {
    // la main gauche tient les rênes, devant le pommeau ; les rênes filent à la tête
    const rx = e.x + cx * 0.38 * ppm - qx * 0.1 * ppm, ry = e.y + cy * 0.38 * ppm - qy * 0.1 * ppm;
    bras(egx, egy, rx, ry, -1);
    const tx = e.x + cx * 1.42 * ppm, ty = e.y + cy * 1.42 * ppm; // la tête de la bête
    ctx.beginPath();
    ctx.moveTo(rx, ry);
    ctx.lineTo(tx - qx * 0.16 * ppm, ty - qy * 0.16 * ppm);
    ctx.moveTo(rx, ry);
    ctx.lineTo(tx + qx * 0.16 * ppm, ty + qy * 0.16 * ppm);
    ctx.strokeStyle = 'rgba(60, 40, 22, 0.9)';
    ctx.lineWidth = Math.max(1, 0.035 * ppm);
    ctx.stroke();
  } else if (eq?.bouclier) {
    // la main gauche dans les énarmes de l'écu
    bras(egx, egy, egx - qx * 0.16 * ppm + cx * (0.04 + balG) * ppm, egy - qy * 0.16 * ppm + cy * (0.04 + balG) * ppm, -1);
  } else if (eq?.arc) {
    // la main gauche sous l'arbrier : elle tient, elle ne balance pas
    bras(egx, egy, egx + cx * 0.3 * ppm + qx * 0.35 * ppm, egy + cy * 0.3 * ppm + qy * 0.35 * ppm, -1);
  } else {
    // le bras gauche ballant : il balance en plein
    bras(egx, egy, egx + cx * (-0.1 + balG) * ppm - qx * 0.08 * ppm, egy + cy * (-0.1 + balG) * ppm - qy * 0.08 * ppm, -1);
  }
}
