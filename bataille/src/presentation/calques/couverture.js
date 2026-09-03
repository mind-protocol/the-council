/**
 * 🖥️ Calque couverture — pour l'homme SÉLECTIONNÉ : son « où j'ai regardé »
 * (la carte cognitive) — les cases vues teintées, s'estompant avec l'âge du
 * regard. Le brouillard de guerre personnel, littéralement : ce qui n'est
 * pas teinté, il ne l'a jamais vu (ou plus depuis longtemps).
 * Lit vues.couverture(id) (vue debug 🧠).
 * @viz couverture
 */

export function dessinerCouverture(ctx, camera, vues) {
  const id = vues.idSelectionne;
  if (id == null) return;
  const info = vues.couverture(id);
  if (!info) return;

  const ppm = camera.echelle();
  const cote = info.tailleCase * ppm;
  ctx.save();
  for (const c of info.cases) {
    const p = camera.versEcran({ x: c.cx * info.tailleCase, y: c.cy * info.tailleCase });
    const alpha = 0.14 * Math.max(0.15, 1 - c.ageS / info.peremptionS);
    ctx.fillStyle = `rgba(120, 220, 160, ${alpha})`;
    ctx.fillRect(p.x, p.y, cote, cote);
  }
  ctx.restore();
}
