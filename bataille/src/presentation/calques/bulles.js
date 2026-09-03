/**
 * 🖥️ Calque bulles — les paroles au-dessus des corps : cartouche arrondi
 * avec queue, fondu sur la fin de vie. Lit vues.bulles() et vues.corpsParId.
 * @viz bulles-paroles, paroles-flavor, acoustique
 */

export function dessinerBulles(ctx, camera, vues) {
  const ppm = camera.echelle();
  ctx.save();
  ctx.font = '12px system-ui, sans-serif';

  for (const b of vues.bulles()) {
    const corps = vues.corpsParId(b.idCorps);
    if (!corps) continue;
    const e = camera.versEcran(corps.pos);
    // fondu : pleine opacité 70 % du temps, puis extinction
    const alpha = b.progression < 0.7 ? 1 : 1 - (b.progression - 0.7) / 0.3;

    const largeurTexte = ctx.measureText(b.texte).width;
    const l = largeurTexte + 16;
    const h = 22;
    const x = e.x - l / 2;
    const y = e.y - corps.rayon * ppm - h - 12;

    ctx.globalAlpha = alpha;
    ctx.beginPath();
    ctx.roundRect(x, y, l, h, 6);
    // la queue, vers le locuteur
    ctx.moveTo(e.x - 4, y + h);
    ctx.lineTo(e.x, y + h + 7);
    ctx.lineTo(e.x + 4, y + h);
    ctx.fillStyle = 'rgba(238, 240, 245, 0.95)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.35)';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = '#1a1d24';
    ctx.fillText(b.texte, x + 8, y + 15);
    ctx.globalAlpha = 1;
  }

  ctx.restore();
}
