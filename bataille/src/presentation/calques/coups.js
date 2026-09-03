/**
 * 🖥️ Calque coups — les GESTES de frappe (🏃, ≤ 0,5 s) : un trait de pointe
 * du frappeur vers sa cible, blanc-chaud s'il a PORTÉ, gris s'il a fendu le
 * vide (la cible avait bougé — la croyance était périmée). Le coup PARÉ fait
 * CLANG : l'étincelle dorée à la pointe — le bouclier a mangé le fer.
 * S'efface vite : un coup est un instant.
 * Les FLÈCHES volent : un trait court qui FILE du tireur vers la chute
 * (interpolé sur volS), puis la croix d'impact à l'atterrissage — blanche
 * si elle a porté, grise si elle s'est fichée en terre.
 * Lit vues.coups (vue debug 🏃).
 * @viz acte-frapper, acte-tirer, bouclier-parade, etat-tire, etat-poursuite, arc-et-carquois
 */

export function dessinerCoups(ctx, camera, vues) {
  const coups = vues.coups?.() ?? [];
  if (!coups.length) return;
  ctx.save();
  ctx.lineCap = 'round';
  for (const c of coups) {
    const de = camera.versEcran(c.de);
    const vers = camera.versEcran(c.vers);
    const alpha = Math.max(0, 1 - c.ageS / 0.5);
    if (c.fleche) {
      const volS = c.volS ?? 0;
      if (c.ageS < volS) {
        // EN VOL : un trait court qui file le long de la trajectoire
        const t = c.ageS / volS;
        const px = de.x + (vers.x - de.x) * t;
        const py = de.y + (vers.y - de.y) * t;
        const d = Math.hypot(vers.x - de.x, vers.y - de.y) || 1;
        const lg = Math.min(10, d * 0.06);
        ctx.strokeStyle = 'rgba(230, 225, 205, 0.9)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(px - ((vers.x - de.x) / d) * lg, py - ((vers.y - de.y) / d) * lg);
        ctx.lineTo(px, py);
        ctx.stroke();
        continue;
      }
      // ATTERRIE : la croix d'impact, qui s'éteint
      const alphaChute = Math.max(0, 1 - (c.ageS - volS) / 0.9);
      ctx.strokeStyle = c.touche
        ? `rgba(255, 240, 210, ${0.95 * alphaChute})`
        : `rgba(150, 155, 170, ${0.6 * alphaChute})`;
      ctx.lineWidth = c.touche ? 2.5 : 1.5;
      const b = 4;
      ctx.beginPath();
      ctx.moveTo(vers.x - b, vers.y - b);
      ctx.lineTo(vers.x + b, vers.y + b);
      ctx.moveTo(vers.x - b, vers.y + b);
      ctx.lineTo(vers.x + b, vers.y - b);
      ctx.stroke();
      continue;
    }
    const curee = c.touche && (c.gravite ?? 1) > 1;
    ctx.strokeStyle = curee
      ? `rgba(220, 60, 50, ${alpha})`
      : c.touche
      ? `rgba(255, 235, 200, ${0.95 * alpha})`
      : c.pare
        ? `rgba(240, 198, 116, ${0.85 * alpha})`
        : `rgba(150, 155, 170, ${0.5 * alpha})`;
    ctx.lineWidth = curee ? 4.5 : c.touche ? 3 : c.pare ? 2.5 : 1.5;
    ctx.beginPath();
    ctx.moveTo(de.x, de.y);
    ctx.lineTo(vers.x, vers.y);
    ctx.stroke();
    // le CLANG : l'étincelle à la pointe parée
    if (c.pare) {
      ctx.beginPath();
      ctx.arc(vers.x, vers.y, 3 + 5 * (c.ageS / 0.5), 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(240, 198, 116, ${0.9 * alpha})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }
  ctx.restore();
}
