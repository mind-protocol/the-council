/**
 * 🖥️ Calque forces (debug) — la Physique rendue visible, gradients plutôt
 * que flèches : HALOS = champs de répulsion (la géométrie — portée — est
 * vraie ; le dégradé interne est illustratif, le profil réel vit dans
 * forces/repulsions.js), TRAÎNÉES estompées = l'inertie en global (l'arc du
 * demi-tour se voit), FLASH ambre = correction de collision (fantôme à la
 * position voulue par l'intégration). Pour l'homme SÉLECTIONNÉ seulement :
 * les deux vecteurs — vitesse désirée vs réelle, l'angle entre eux EST
 * l'inertie.
 * Lit vues.forces (vue debug ⚙️), vues.corps, vues.corpsParId,
 * vues.terrain, vues.idSelectionne.
 * Sur le sélectionné aussi : le vecteur COUDE-À-COUDE (vert doux) — la
 * ligne qui se soude épaule contre épaule.
 * L'anneau de GARDE (teinté à la livrée, pointillé) : la mesure d'escrime —
 * le rayon auquel ce corps tient les livrées adverses à distance.
 * @viz repulsion-douce, collision-dure, inertie, coude-a-coude, garde-de-lance, armes-differenciees, repousse-gisants
 */

const LONGUEUR_TRAINEE = 36; // positions gardées (~0.6 s à 60 fps)
const PAS_TRAINEE = 3;       // on dessine un point sur trois

// État local au calque (debug) : les traînées ne s'accumulent que quand le
// calque est actif — c'est un instrument, pas une donnée de sim.
const trainees = new Map();

function majTrainees(tous) {
  const vivants = new Set();
  for (const c of tous) {
    vivants.add(c.id);
    let t = trainees.get(c.id);
    if (!t) trainees.set(c.id, (t = []));
    t.push({ x: c.pos.x, y: c.pos.y });
    if (t.length > LONGUEUR_TRAINEE) t.shift();
  }
  for (const id of trainees.keys()) if (!vivants.has(id)) trainees.delete(id);
}

function fleche(ctx, de, vers) {
  const dx = vers.x - de.x;
  const dy = vers.y - de.y;
  const d = Math.hypot(dx, dy);
  if (d < 4) return;
  ctx.beginPath();
  ctx.moveTo(de.x, de.y);
  ctx.lineTo(vers.x, vers.y);
  ctx.stroke();
  const ux = dx / d, uy = dy / d;
  ctx.beginPath();
  ctx.moveTo(vers.x, vers.y);
  ctx.lineTo(vers.x - 8 * ux + 4 * uy, vers.y - 8 * uy - 4 * ux);
  ctx.lineTo(vers.x - 8 * ux - 4 * uy, vers.y - 8 * uy + 4 * ux);
  ctx.closePath();
  ctx.fill();
}

export function dessinerForces(ctx, camera, vues) {
  const { portees, parCorps } = vues.forces();
  const ppm = camera.echelle();
  const tous = [...vues.corps()];
  majTrainees(tous);
  ctx.save();

  // ── halos des murs : anneaux dégressifs sur la portée ──
  const ANNEAUX = 4;
  for (const o of vues.terrain.obstacles()) {
    const e = camera.versEcran({ x: o.x, y: o.y });
    for (let k = 1; k <= ANNEAUX; k++) {
      const marge = (portees.murs * k) / ANNEAUX;
      ctx.strokeStyle = `rgba(224, 82, 82, ${0.16 * (1 - (k - 1) / ANNEAUX)})`;
      ctx.lineWidth = (portees.murs / ANNEAUX) * ppm;
      ctx.strokeRect(
        e.x - (marge - portees.murs / (2 * ANNEAUX)) * ppm,
        e.y - (marge - portees.murs / (2 * ANNEAUX)) * ppm,
        (o.largeur + 2 * marge - portees.murs / ANNEAUX) * ppm,
        (o.hauteur + 2 * marge - portees.murs / ANNEAUX) * ppm
      );
    }
  }

  // ── halos des hommes : gradient radial, plein à la surface, nul à la portée ──
  // (les gisants : halo GRIS — on essaie de ne pas trébucher dessus)
  for (const c of tous) {
    const e = camera.versEcran(c.pos);
    const r0 = c.rayon * ppm;
    const r1 = (c.rayon + portees.hommes) * ppm;
    const gisant = c.posture === 'gisant';
    const teinte = gisant ? '150, 150, 150' : '224, 82, 82';
    const rayonChamp = gisant ? (c.rayon + (portees.gisants ?? 0.5)) * ppm : r1;
    const g = ctx.createRadialGradient(e.x, e.y, r0, e.x, e.y, rayonChamp);
    g.addColorStop(0, `rgba(${teinte}, 0.22)`);
    g.addColorStop(1, `rgba(${teinte}, 0)`);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(e.x, e.y, gisant ? rayonChamp : r1, 0, Math.PI * 2);
    ctx.fill();
  }

  // ── anneaux de GARDE : la mesure d'escrime, teintée à la livrée ──
  const TEINTES = { bleu: '74, 158, 255', rouge: '255, 95, 86' };
  if (portees.gardeDe) {
    ctx.setLineDash([5, 5]);
    ctx.lineWidth = 1;
    for (const c of tous) {
      const e = camera.versEcran(c.pos);
      ctx.strokeStyle = `rgba(${TEINTES[c.livree] ?? '154, 160, 174'}, 0.28)`;
      ctx.beginPath();
      ctx.arc(e.x, e.y, portees.gardeDe(c.id) * ppm, 0, Math.PI * 2); // par ARME
      ctx.stroke();
    }
    ctx.setLineDash([]);
  }

  // ── traînées : l'inertie en global — l'arc du demi-tour se voit ──
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  for (const c of tous) {
    const t = trainees.get(c.id);
    if (!t || t.length < PAS_TRAINEE * 2) continue;
    for (let k = PAS_TRAINEE; k < t.length; k += PAS_TRAINEE) {
      const a = camera.versEcran(t[k - PAS_TRAINEE]);
      const b = camera.versEcran(t[k]);
      ctx.strokeStyle = `rgba(126, 201, 255, ${0.35 * (k / t.length)})`;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }
  }

  // ── les CHOCS du tick : éclat blanc au point d'impact, rayon ∝ impulsion —
  // la poussée de masse SE VOIT (un renversement est un gros éclat) ──
  for (const choc of vues.forces().chocs ?? []) {
    const p = camera.versEcran(choc.pos);
    const r = Math.min(18, 3 + choc.impulsion / 60);
    ctx.beginPath();
    ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 246, 220, 0.9)';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // ── flashs de collision : fantôme (position voulue) + anneau (1 tick) ──
  for (const c of tous) {
    const d = parCorps.get(c.id);
    if (!d || !d.correction) continue;
    const e = camera.versEcran(c.pos);
    const voulu = camera.versEcran({ x: c.pos.x - d.correction.x, y: c.pos.y - d.correction.y });
    ctx.setLineDash([3, 2]);
    ctx.strokeStyle = 'rgba(240, 180, 41, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(voulu.x, voulu.y, c.rayon * ppm, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.strokeStyle = 'rgba(240, 180, 41, 0.9)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(e.x, e.y, c.rayon * ppm + 3, 0, Math.PI * 2);
    ctx.stroke();
  }

  // ── sélectionné : désirée vs réelle — l'angle entre les deux = l'inertie ──
  const id = vues.idSelectionne;
  const corps = id != null ? vues.corpsParId(id) : null;
  const d = id != null ? parCorps.get(id) : null;
  if (corps && d) {
    const e = camera.versEcran(corps.pos);
    const ECHELLE_S = 1.2; // 1 s de déplacement, en pixels via ppm
    if (d.vitesseDesiree) {
      ctx.strokeStyle = ctx.fillStyle = 'rgba(87, 201, 184, 0.9)';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 4]);
      fleche(ctx, e, {
        x: e.x + d.vitesseDesiree.x * ECHELLE_S * ppm,
        y: e.y + d.vitesseDesiree.y * ECHELLE_S * ppm,
      });
      ctx.setLineDash([]);
    }
    ctx.strokeStyle = ctx.fillStyle = 'rgba(126, 201, 255, 0.95)';
    ctx.lineWidth = 2.5;
    fleche(ctx, e, {
      x: e.x + corps.vel.x * ECHELLE_S * ppm,
      y: e.y + corps.vel.y * ECHELLE_S * ppm,
    });
    if (d.coude) {
      ctx.strokeStyle = ctx.fillStyle = 'rgba(120, 220, 160, 0.9)';
      ctx.lineWidth = 2;
      fleche(ctx, e, {
        x: e.x + d.coude.x * 2.5 * ECHELLE_S * ppm,
        y: e.y + d.coude.y * 2.5 * ECHELLE_S * ppm,
      });
    }
  }

  ctx.restore();
}
