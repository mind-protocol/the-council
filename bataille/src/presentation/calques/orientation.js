/**
 * 🖥️ Calque orientation — pour l'homme SÉLECTIONNÉ : l'arbitrage d'attention
 * rendu visible — les trois composantes (mouvement bleu, vers-les-gens vert,
 * comme-les-gens violet), la résultante (blanc) et la condition (formation /
 * face / arbitrage). C'est avec ce calque qu'on règle les poids.
 * Lit vues.orientationDebug(id) (vue debug 🧠) et vues.corpsParId.
 * @viz orientation-arbitrage, orientation-facer
 */

const ECHELLE_M = 2.2; // mètres dessinés par unité de poids

function fleche(ctx, de, vecteur, couleur, ppm) {
  const l = Math.hypot(vecteur.x, vecteur.y);
  if (l < 0.03) return;
  const ax = de.x + vecteur.x * ECHELLE_M * ppm;
  const ay = de.y + vecteur.y * ECHELLE_M * ppm;
  ctx.beginPath();
  ctx.moveTo(de.x, de.y);
  ctx.lineTo(ax, ay);
  ctx.strokeStyle = couleur;
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(ax, ay, 3, 0, Math.PI * 2);
  ctx.fillStyle = couleur;
  ctx.fill();
}

export function dessinerOrientation(ctx, camera, vues) {
  const id = vues.idSelectionne;
  if (id == null) return;
  const info = vues.orientationDebug(id);
  const corps = vues.corpsParId(id);
  if (!info || !corps) return;

  const ppm = camera.echelle();
  const e = camera.versEcran(corps.pos);
  ctx.save();

  if (info.composantes) {
    fleche(ctx, e, info.composantes.mouvement, 'rgba(106, 176, 255, 0.9)', ppm);
    fleche(ctx, e, info.composantes.versGens, 'rgba(120, 220, 160, 0.9)', ppm);
    fleche(ctx, e, info.composantes.commeGens, 'rgba(199, 146, 234, 0.9)', ppm);
  }

  // la résultante : le cap désiré
  fleche(ctx, e, { x: Math.cos(info.cap) * 0.8, y: Math.sin(info.cap) * 0.8 }, 'rgba(240, 240, 245, 0.95)', ppm);

  ctx.font = '11px system-ui, sans-serif';
  ctx.fillStyle = 'rgba(220, 224, 232, 0.85)';
  ctx.fillText(info.condition, e.x + 10, e.y + corps.rayon * ppm + 14);
  ctx.restore();
}
