/**
 * 🖥️ Calque chemins (debug) — trajectoires A* restantes et cibles.
 * Lit vues.chemins (vue debug de 🏃 Action) et vues.corpsParId.
 * @viz pathfinding-astar, suivi-chemin, intentions
 */

export function dessinerChemins(ctx, camera, vues) {
  ctx.save();
  ctx.setLineDash([5, 5]);
  ctx.strokeStyle = 'rgba(122, 162, 247, 0.45)';
  ctx.lineWidth = 1.5;

  for (const { id, chemin, index } of vues.chemins()) {
    const corps = vues.corpsParId(id);
    if (!corps || index >= chemin.length) continue;

    // polyligne : position courante → waypoints restants
    ctx.beginPath();
    const d = camera.versEcran(corps.pos);
    ctx.moveTo(d.x, d.y);
    for (let k = index; k < chemin.length; k++) {
      const w = camera.versEcran(chemin[k]);
      ctx.lineTo(w.x, w.y);
    }
    ctx.stroke();

    // la cible : petit anneau
    const cible = camera.versEcran(chemin[chemin.length - 1]);
    ctx.beginPath();
    ctx.arc(cible.x, cible.y, 4, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();
}
