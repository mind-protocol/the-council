/**
 * 🖥️ Calque navgrid (debug) — la recherche A* RÉCENTE : les dernières cases
 * évaluées (journal circulaire côté 🌍), fondu par récence — la plus fraîche
 * est la plus opaque. Rouge = bloquée (l'obstacle GONFLÉ du rayon agent — la
 * maison paraît plus grosse que son dessin, c'est voulu), bleu = libre.
 * Plus les contours des régions en cache. L'accumulation depuis le début
 * n'est PAS montrée : elle deviendrait du bruit.
 * Lit vues.navgridDebug (vue debug 🌍).
 * @viz navgrid
 */

export function dessinerNavgrid(ctx, camera, vues) {
  const { regions, evaluations } = vues.navgridDebug();
  const ppm = camera.echelle();
  ctx.save();

  // contours des régions en cache
  ctx.setLineDash([6, 4]);
  ctx.strokeStyle = 'rgba(136, 145, 165, 0.5)';
  ctx.lineWidth = 1;
  for (const r of regions) {
    const o = camera.versEcran({ x: r.i0 * r.tailleCase, y: r.j0 * r.tailleCase });
    ctx.strokeRect(o.x, o.y, r.colonnes * r.tailleCase * ppm, r.lignes * r.tailleCase * ppm);
  }
  ctx.setLineDash([]);

  // les dernières évaluations, de la plus ancienne (pâle) à la plus récente
  const { tailleCase, cases } = evaluations;
  const cote = tailleCase * ppm;
  const n = cases.length;
  for (let k = 0; k < n; k++) {
    const c = cases[k];
    const recence = (k + 1) / n;
    const p = camera.versEcran({ x: c.x, y: c.y });
    ctx.fillStyle = c.bloquee
      ? `rgba(224, 82, 82, ${0.08 + 0.35 * recence})`
      : `rgba(126, 201, 255, ${0.03 + 0.14 * recence})`;
    ctx.fillRect(p.x, p.y, cote, cote);
  }

  ctx.restore();
}
