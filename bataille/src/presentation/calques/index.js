/**
 * 🖥️ Calque index (debug) — le snapshot spatial : cases occupées (contour +
 * effectif, rien ailleurs — seules les cases occupées existent, plan infini).
 * Pour l'homme SÉLECTIONNÉ : les cases que voisinsDans() balaie pour sa
 * perception — la sur-approximation rectangulaire, que le cercle du calque
 * perception vient ensuite filtrer par distance.
 * Lit vues.indexDebug (vue debug 🌍), vues.idSelectionne, vues.corpsParId,
 * vues.perception (pour la portée de la requête).
 * @viz index-spatial-snapshot
 */

export function dessinerIndex(ctx, camera, vues) {
  const { tailleCase, cases } = vues.indexDebug();
  const ppm = camera.echelle();
  const cote = tailleCase * ppm;
  ctx.save();

  // Cases balayées par la requête du sélectionné — dessinées dessous.
  const id = vues.idSelectionne;
  const corps = id != null ? vues.corpsParId(id) : null;
  const info = id != null ? vues.perception(id) : null;
  if (corps && info) {
    const r = info.portee;
    const cx0 = Math.floor((corps.pos.x - r) / tailleCase);
    const cx1 = Math.floor((corps.pos.x + r) / tailleCase);
    const cy0 = Math.floor((corps.pos.y - r) / tailleCase);
    const cy1 = Math.floor((corps.pos.y + r) / tailleCase);
    const o = camera.versEcran({ x: cx0 * tailleCase, y: cy0 * tailleCase });
    const l = (cx1 - cx0 + 1) * cote;
    const h = (cy1 - cy0 + 1) * cote;
    ctx.fillStyle = 'rgba(240, 180, 41, 0.06)';
    ctx.fillRect(o.x, o.y, l, h);
    ctx.setLineDash([5, 4]);
    ctx.strokeStyle = 'rgba(240, 180, 41, 0.55)';
    ctx.lineWidth = 1;
    ctx.strokeRect(o.x, o.y, l, h);
    ctx.setLineDash([]);
  }

  ctx.strokeStyle = 'rgba(87, 201, 184, 0.55)';
  ctx.lineWidth = 1;
  ctx.fillStyle = 'rgba(87, 201, 184, 0.9)';
  ctx.font = '10px system-ui, sans-serif';
  ctx.textAlign = 'right';
  for (const c of cases) {
    const p = camera.versEcran({ x: c.cx * tailleCase, y: c.cy * tailleCase });
    ctx.strokeRect(p.x, p.y, cote, cote);
    if (cote >= 22) ctx.fillText(String(c.n), p.x + cote - 3, p.y + 11);
  }

  ctx.restore();
}
