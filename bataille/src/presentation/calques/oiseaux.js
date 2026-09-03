/**
 * 🖥️ Calque oiseaux — ce que le sol ne porte pas : la silhouette battante
 * (plumage du profil ❤️ — des couleurs et des longueurs, pas des types),
 * l'OMBRE PORTÉE décalée par z (+ pointillé silhouette↔ombre : l'altitude se
 * lit d'un coup d'œil) et la trace du vol, colorée par la hauteur.
 *
 * Un oiseau est PETIT : à l'échelle d'un champ de bataille, il ferait deux
 * pixels. On le dessine donc à une taille LISIBLE (le rendu grossit, la
 * simulation ne bouge pas) — c'est un choix de lecture, dit ici et nulle part
 * ailleurs. L'ombre, elle, garde sa vraie place au sol : c'est elle qui dit
 * où il est réellement.
 *
 * Lit vues.corps (🌍, corps à `vol`) et vues.oiseauDe (❤️, le plumage).
 * @viz vol-banque, calque-oiseaux
 */

const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const paths = new Map(); // id → Array<{x, y, z}>

// Le grossissement de lecture : une envergure d'un mètre vingt se perdrait
// sur un champ de trois cents pas. On la rend comme si elle en faisait trois
// et demi — assez pour qu'un oiseau soit un oiseau, pas assez pour qu'il pèse
// plus qu'un homme à l'œil.
const GROSSISSEMENT = 3;

/** Le corvidé : ailes larges, plumes des bouts écartées, queue en coin. */
function corvide(ctx, s, demi, plumage) {
  ctx.fillStyle = plumage.corps;
  ctx.strokeStyle = plumage.trait;
  ctx.lineWidth = Math.max(0.6, s * 0.5);
  ctx.beginPath();
  ctx.moveTo(s * 5, 0);
  ctx.quadraticCurveTo(s * 2.4, -s * 2.6, -s * 1.2, -demi * 0.86);
  ctx.quadraticCurveTo(-s * 3.4, -demi, -s * 5.2, -demi * 0.82); // les rémiges écartées
  ctx.quadraticCurveTo(-s * 5, -s * 4, -s * 4.6, -s * 1.8);
  ctx.lineTo(-s * 10, -s * 1.5); // la queue en coin
  ctx.lineTo(-s * 11.5, 0);
  ctx.lineTo(-s * 10, s * 1.5);
  ctx.lineTo(-s * 4.6, s * 1.8);
  ctx.quadraticCurveTo(-s * 5, s * 4, -s * 5.2, demi * 0.82);
  ctx.quadraticCurveTo(-s * 3.4, demi, -s * 1.2, demi * 0.86);
  ctx.quadraticCurveTo(s * 2.4, s * 2.6, s * 5, 0);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

/** Le rapace : ailes en faux, pointues, queue étroite. */
function rapace(ctx, s, demi, plumage) {
  ctx.fillStyle = plumage.corps;
  ctx.strokeStyle = plumage.trait;
  ctx.lineWidth = Math.max(0.6, s * 0.5);
  ctx.beginPath();
  ctx.moveTo(s * 5.5, 0);
  ctx.quadraticCurveTo(s * 3, -s * 2.2, -s * 0.5, -demi * 0.55);
  ctx.quadraticCurveTo(-s * 3.6, -demi, -s * 6.4, -demi * 0.92); // la pointe de l'aile
  ctx.quadraticCurveTo(-s * 4.2, -s * 3.4, -s * 3.4, -s * 1.5);
  ctx.lineTo(-s * 9.5, -s * 1.1); // la queue étroite
  ctx.lineTo(-s * 10.2, 0);
  ctx.lineTo(-s * 9.5, s * 1.1);
  ctx.lineTo(-s * 3.4, s * 1.5);
  ctx.quadraticCurveTo(-s * 4.2, s * 3.4, -s * 6.4, demi * 0.92);
  ctx.quadraticCurveTo(-s * 3.6, demi, -s * 0.5, demi * 0.55);
  ctx.quadraticCurveTo(s * 3, s * 2.2, s * 5.5, 0);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

export function dessinerOiseaux(ctx, camera, vues) {
  const ppm = camera.echelle();

  for (const c of vues.corps()) {
    if (!c.vol) continue;
    const profil = vues.oiseauDe?.(c.id);
    if (!profil) continue;
    const vol = c.vol;

    // LA TRACE — d'où il vient, teintée par la hauteur qu'il tenait
    let path = paths.get(c.id);
    if (!path) {
      path = [];
      paths.set(c.id, path);
    }
    const dernier = path[path.length - 1];
    if (!dernier || Math.hypot(c.pos.x - dernier.x, c.pos.y - dernier.y) > 1.5) {
      path.push({ x: c.pos.x, y: c.pos.y, z: vol.z });
      if (path.length > 600) path.shift();
    }
    ctx.save();
    ctx.lineCap = 'round';
    for (let i = 1; i < path.length; i++) {
      const a = camera.versEcran(path[i - 1]);
      const b = camera.versEcran(path[i]);
      const h = clamp(path[i].z / 200, 0, 1);
      ctx.strokeStyle = `hsla(${38 + h * 150}, 45%, ${44 + h * 18}%, 0.35)`;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
    ctx.restore();

    // L'OMBRE, à sa vraie place au sol, décalée par la hauteur : c'est elle
    // qui dit où il est ; plus il monte, plus elle s'éloigne et pâlit
    const e = camera.versEcran(c.pos);
    const o = camera.versEcran({ x: c.pos.x + vol.z * 0.075, y: c.pos.y + vol.z * 0.045 });
    const batt = 0.72 + 0.28 * Math.cos(vol.phaseAile);
    const s = (profil.longueur * GROSSISSEMENT / 11) * ppm; // l'unité de dessin
    const demi = (profil.envergure * GROSSISSEMENT * batt) / 2 * ppm;

    ctx.save();
    ctx.translate(o.x, o.y);
    ctx.rotate(c.cap);
    ctx.fillStyle = `rgba(0, 0, 0, ${clamp(0.4 - vol.z / 340, 0.08, 0.34)})`;
    ctx.beginPath();
    ctx.ellipse(0, 0, s * 7, demi * 0.42, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.strokeStyle = 'rgba(215, 203, 169, 0.18)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 4]);
    ctx.beginPath();
    ctx.moveTo(e.x, e.y);
    ctx.lineTo(o.x, o.y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // LA BÊTE, cap vers la droite dans son repère, tournée par son cap. Les
    // ailes battent : leur envergure se resserre et s'ouvre avec la phase.
    ctx.save();
    ctx.translate(e.x, e.y);
    ctx.rotate(c.cap);
    if (profil.silhouette === 'rapace') rapace(ctx, s, demi, profil.plumage);
    else corvide(ctx, s, demi, profil.plumage);
    ctx.fillStyle = profil.plumage.ventre;
    ctx.beginPath();
    ctx.ellipse(-s * 1.2, 0, s * 4.6, s * 1.15, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}
