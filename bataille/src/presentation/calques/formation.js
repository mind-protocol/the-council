/**
 * 🖥️ Calque formation — pour l'homme SÉLECTIONNÉ en formation : le REPÈRE
 * RÉSOLU par le langage (origine : trait de première ligne + flèche du cap +
 * source de la résolution), le lien orange vers son ANCRE (position crue),
 * la croix sur sa cible de slot. L'objectif complet est dans l'inspecteur.
 * Lit vues.formationDebug(id) (vue debug 🧠) et vues.corpsParId.
 * @viz ancrage-relationnel, objectif-humain, unite-drill, forme-ouverte, langage-resolution, ratissage-bonds
 */

const SOURCES = {
  surLocuteur: 'repère : sur le chef',
  premiereLigne: 'repère : la première ligne (auto-référent)',
  devantLocuteur: 'repère : amorçage devant le chef',
};

export function dessinerFormation(ctx, camera, vues) {
  const id = vues.idSelectionne;
  if (id == null) return;
  const info = vues.formationDebug(id);
  const corps = vues.corpsParId(id);
  if (!info || !corps) return;

  const ppm = camera.echelle();
  ctx.save();
  ctx.font = '11px system-ui, sans-serif';

  // le repère résolu : première ligne (trait) + cap (flèche) + source
  if (info.origine) {
    const o = camera.versEcran(info.origine.pos);
    const cap = info.origine.cap;
    const dx = -Math.sin(cap), dy = Math.cos(cap); // perpendiculaire
    const demi = 1.6 * ppm;
    ctx.beginPath();
    ctx.moveTo(o.x - dx * demi, o.y - dy * demi);
    ctx.lineTo(o.x + dx * demi, o.y + dy * demi);
    ctx.strokeStyle = 'rgba(240, 150, 90, 0.85)';
    ctx.lineWidth = 2.5;
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(o.x, o.y);
    ctx.lineTo(o.x + Math.cos(cap) * 1.0 * ppm, o.y + Math.sin(cap) * 1.0 * ppm);
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = 'rgba(245, 200, 160, 0.85)';
    ctx.fillText(SOURCES[info.source] ?? info.source ?? '', o.x + 8, o.y - 8);
  }

  // le lien vers l'ancre crue + la croix du slot (si j'ai un ancrage)
  if (info.ancrePosCrue && info.cible) {
    const moi = camera.versEcran(corps.pos);
    const ancre = camera.versEcran(info.ancrePosCrue);
    const cible = camera.versEcran(info.cible);
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(moi.x, moi.y);
    ctx.lineTo(ancre.x, ancre.y);
    ctx.strokeStyle = 'rgba(240, 150, 90, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.setLineDash([]);
    const b = 5;
    ctx.beginPath();
    ctx.moveTo(cible.x - b, cible.y - b);
    ctx.lineTo(cible.x + b, cible.y + b);
    ctx.moveTo(cible.x - b, cible.y + b);
    ctx.lineTo(cible.x + b, cible.y - b);
    ctx.strokeStyle = 'rgba(240, 150, 90, 0.9)';
    ctx.lineWidth = 2;
    ctx.stroke();
    if (info.nomAncre) {
      ctx.fillStyle = 'rgba(245, 200, 160, 0.9)';
      ctx.fillText(info.nomAncre, cible.x + 8, cible.y - 8);
    }
  }

  ctx.restore();
}
