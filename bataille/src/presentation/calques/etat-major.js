/**
 * 🖥️ Calque état-major — L'ESPACE DES CHOIX du commandant SÉLECTIONNÉ, sur
 * la carte : chaque option de l'arbitre (chemin → destination, score),
 * l'ENGAGÉE en doré, les autres graduées ; la LIGNE DE BARRAGE crue (trait
 * blanc), le POSTE retenu (cercle), l'AXE DE MENACE (flèche pointillée).
 * Au-dessus de CHAQUE chef : la manœuvre engagée + phase (étiquette dorée) —
 * les tactiques des deux camps se lisent d'un coup d'œil.
 * Tout vient des CROYANCES du chef (son debug d'état-major) — pas du monde :
 * une option posée au mauvais endroit est une information, pas un bug.
 * Lit vues.corps et vues.etatMajor(id) (vue 🧠 dédiée).
 * @viz etat-major
 */

function fleche(ctx, de, vers, tetePx = 7) {
  const dx = vers.x - de.x;
  const dy = vers.y - de.y;
  const d = Math.hypot(dx, dy);
  if (d < 2) return;
  ctx.beginPath();
  ctx.moveTo(de.x, de.y);
  ctx.lineTo(vers.x, vers.y);
  ctx.stroke();
  const ux = dx / d, uy = dy / d;
  ctx.beginPath();
  ctx.moveTo(vers.x, vers.y);
  ctx.lineTo(vers.x - tetePx * ux + tetePx * 0.55 * uy, vers.y - tetePx * uy - tetePx * 0.55 * ux);
  ctx.lineTo(vers.x - tetePx * ux - tetePx * 0.55 * uy, vers.y - tetePx * uy + tetePx * 0.55 * ux);
  ctx.closePath();
  ctx.fill();
}

function etiquette(ctx, camera, pos, texte, couleur) {
  const e = camera.versEcran(pos);
  ctx.font = '11px system-ui, sans-serif';
  ctx.fillStyle = 'rgba(12, 14, 19, 0.8)';
  const l = ctx.measureText(texte).width;
  ctx.fillRect(e.x - l / 2 - 4, e.y - 18, l + 8, 15);
  ctx.fillStyle = couleur;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(texte, e.x, e.y - 10.5);
}

export function dessinerEtatMajor(ctx, camera, vues) {
  const ppm = camera.echelle();
  ctx.save();

  // l'étiquette ⚔ sur chaque chef : la manœuvre engagée, lisible de loin
  ctx.font = '11px system-ui, sans-serif';
  ctx.textAlign = 'center';
  for (const c of vues.corps()) {
    const em = vues.etatMajor?.(c.id);
    if (!em?.engagee) continue;
    const e = camera.versEcran(c.pos);
    ctx.fillStyle = '#f0c674';
    ctx.fillText(`⚔ ${em.engagee.nom} ${em.engagee.phase + 1}/${em.engagee.phases}`, e.x, e.y - 0.9 * ppm - 8);
  }

  const id = vues.idSelectionne;
  const carte = id != null ? vues.etatMajor?.(id)?.carte : null;
  if (!carte) {
    ctx.restore();
    return;
  }

  // l'AXE DE MENACE : d'où le chef croit que ça vient
  if (carte.capMenace !== null && carte.positionUnite) {
    const de = camera.versEcran(carte.positionUnite);
    const vers = camera.versEcran({
      x: carte.positionUnite.x + Math.cos(carte.capMenace) * 12,
      y: carte.positionUnite.y + Math.sin(carte.capMenace) * 12,
    });
    ctx.setLineDash([4, 5]);
    ctx.strokeStyle = ctx.fillStyle = 'rgba(255, 140, 120, 0.7)';
    ctx.lineWidth = 1.5;
    fleche(ctx, de, vers);
    ctx.setLineDash([]);
  }

  // la LIGNE DE BARRAGE crue : le segment que le chef voudrait boucher
  if (carte.ligne?.centre && carte.capMenace !== null) {
    const lat = { x: -Math.sin(carte.capMenace), y: Math.cos(carte.capMenace) };
    const demi = Math.max(2, (carte.ligne.trous ?? 4) / 2);
    const a = camera.versEcran({ x: carte.ligne.centre.x - lat.x * demi, y: carte.ligne.centre.y - lat.y * demi });
    const b = camera.versEcran({ x: carte.ligne.centre.x + lat.x * demi, y: carte.ligne.centre.y + lat.y * demi });
    ctx.strokeStyle = 'rgba(214, 218, 227, 0.85)';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
    etiquette(ctx, camera, carte.ligne.centre, `ligne — ${(carte.ligne.qualite ?? 0).toFixed(2)}`, '#d6dae3');
  }

  // le POSTE retenu : où le chef a décidé de se tenir
  if (carte.poste) {
    const e = camera.versEcran(carte.poste);
    ctx.strokeStyle = '#ffd866';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(e.x, e.y, Math.max(4, 0.5 * ppm), 0, Math.PI * 2);
    ctx.stroke();
  }

  // les OPTIONS : chemins → destinations, l'engagée en doré, le reste gradué
  for (const o of carte.options ?? []) {
    const fini = Number.isFinite(o.score);
    const couleur = o.engagee
      ? 'rgba(255, 216, 102, 0.95)'
      : fini
        ? `rgba(126, 201, 255, ${0.35 + 0.4 * Math.min(1, Math.max(0, o.score))})`
        : 'rgba(150, 155, 170, 0.25)';
    ctx.strokeStyle = ctx.fillStyle = couleur;
    ctx.lineWidth = o.engagee ? 2.5 : 1.5;
    if (o.chemin?.length >= 2) {
      const de = camera.versEcran(o.chemin[0]);
      const vers = camera.versEcran(o.chemin[o.chemin.length - 1]);
      fleche(ctx, de, vers);
    }
    if (o.destination) {
      etiquette(
        ctx,
        camera,
        o.destination,
        `${o.nom}${fini ? ` ${o.score.toFixed(2)}` : ''}`,
        o.engagee ? '#ffd866' : '#a9c9e8'
      );
    }
  }

  ctx.restore();
}
