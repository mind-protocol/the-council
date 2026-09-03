/**
 * 🖥️ Calque sélection — anneau autour de l'homme sélectionné.
 * Lit vues.idSelectionne et vues.corpsParId.
 * @viz selection
 */

export function dessinerSelection(ctx, camera, vues) {
  if (vues.idSelectionne == null) return;
  const c = vues.corpsParId(vues.idSelectionne);
  if (!c) return;
  const e = camera.versEcran(c.pos);
  // DISCRET : l'anneau dit lequel on tient, il ne le met pas en scene. Il etait
  // en jaune plein sur deux pixels a cinq de distance — le seul objet vif de la
  // carte, et l'oeil y revenait sans cesse. Serre, aminci et rendu translucide,
  // il se trouve quand on le cherche et s'oublie le reste du temps.
  ctx.beginPath();
  ctx.arc(e.x, e.y, c.rayon * camera.echelle() + 3, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(255, 216, 102, 0.42)';
  ctx.lineWidth = 1;
  ctx.stroke();
}
