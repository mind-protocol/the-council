/**
 * 🖥️ Calque lignes — les FRONTS, en vérité terrain (debug) : pour chaque
 * camp (livrée), le contour de sa ligne — l'homme le plus AVANCÉ vers
 * l'ennemi par tranche latérale (~espacement du drill), donc une ligne
 * COURBE — avec son envergure (m) et son % DE TROUS (tranches vides).
 * Entre les deux : la PERPENDICULAIRE CENTRALE (l'axe de menace), avec la
 * distance entre les fronts. C'est la viz du concept « ligne de barrage »
 * (le % de trous que la manœuvre tenir voudra minimiser) — la version CRUE
 * du commandant viendra à côté quand l'estimation la calculera.
 * Analyse VIZ-SEULEMENT : rien ici ne nourrit la sim.
 * @viz lignes-de-front
 */

const COULEURS_LIVREE = {
  bleu: '#4a9eff',
  rouge: '#ff5f56',
};
const TRANCHE = 1.2; // m — l'espacement du drill : un trou = une place vide
const COURBURE_MAX = 0.45; // rad — virage max entre deux segments du tracé
const PASSES_MOYENNE = 3; // lissages par moyenne glissante

/**
 * Lisse le contour : moyenne glissante (le tracé suit la TENDANCE du front,
 * pas chaque épaule), puis COURBURE BORNÉE — un virage trop sec est relaxé
 * vers la corde jusqu'à repasser sous COURBURE_MAX.
 */
function lisserContour(points) {
  if (points.length < 3) return points;
  let p = points.map((q) => ({ ...q }));
  for (let passe = 0; passe < PASSES_MOYENNE; passe++) {
    const lisse = p.map((q, i) => {
      if (i === 0 || i === p.length - 1) return q;
      return {
        x: (p[i - 1].x + 2 * q.x + p[i + 1].x) / 4,
        y: (p[i - 1].y + 2 * q.y + p[i + 1].y) / 4,
      };
    });
    p = lisse;
  }
  for (let iter = 0; iter < 4; iter++) {
    let corrige = false;
    for (let i = 1; i < p.length - 1; i++) {
      const a1 = Math.atan2(p[i].y - p[i - 1].y, p[i].x - p[i - 1].x);
      const a2 = Math.atan2(p[i + 1].y - p[i].y, p[i + 1].x - p[i].x);
      const virage = Math.atan2(Math.sin(a2 - a1), Math.cos(a2 - a1));
      if (Math.abs(virage) <= COURBURE_MAX) continue;
      // trop sec : le point du milieu glisse vers la corde
      const corde = { x: (p[i - 1].x + p[i + 1].x) / 2, y: (p[i - 1].y + p[i + 1].y) / 2 };
      p[i] = { x: (p[i].x + corde.x) / 2, y: (p[i].y + corde.y) / 2 };
      corrige = true;
    }
    if (!corrige) break;
  }
  return p;
}

/** Le contour du front d'un camp, vers `u` (unitaire, vers l'ennemi). */
function analyserFront(corps, barycentre, u) {
  const lat = { x: -u.y, y: u.x };
  const projs = corps.map((c) => ({
    c,
    l: (c.pos.x - barycentre.x) * lat.x + (c.pos.y - barycentre.y) * lat.y,
    a: (c.pos.x - barycentre.x) * u.x + (c.pos.y - barycentre.y) * u.y,
  }));
  let minL = Infinity, maxL = -Infinity;
  for (const p of projs) {
    minL = Math.min(minL, p.l);
    maxL = Math.max(maxL, p.l);
  }
  const nBins = Math.max(1, Math.ceil((maxL - minL) / TRANCHE));
  const bins = new Array(nBins).fill(null);
  for (const p of projs) {
    const i = Math.min(nBins - 1, Math.floor((p.l - minL) / TRANCHE));
    if (!bins[i] || p.a > bins[i].a) bins[i] = p;
  }
  const tenus = bins.filter(Boolean);
  return {
    contour: tenus.map((p) => p.c.pos), // trié par construction (bins ordonnés)
    envergure: maxL - minL + 0.7, // + le diamètre d'épaules
    partTrous: 1 - tenus.length / nBins,
    centre: (() => {
      const t = tenus;
      return {
        x: t.reduce((s, p) => s + p.c.pos.x, 0) / t.length,
        y: t.reduce((s, p) => s + p.c.pos.y, 0) / t.length,
      };
    })(),
  };
}

function etiqueter(ctx, camera, pos, texte, couleur) {
  const e = camera.versEcran(pos);
  ctx.font = '11px system-ui, sans-serif';
  ctx.fillStyle = 'rgba(12, 14, 19, 0.75)';
  const l = ctx.measureText(texte).width;
  ctx.fillRect(e.x - l / 2 - 4, e.y - 8, l + 8, 16);
  ctx.fillStyle = couleur;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(texte, e.x, e.y);
}

export function dessinerLignes(ctx, camera, vues) {
  // les camps : les vivants, par livrée (les gisants ne tiennent plus de ligne)
  const parLivree = new Map();
  for (const c of vues.corps()) {
    if (c.posture === 'gisant') continue;
    if (!parLivree.has(c.livree)) parLivree.set(c.livree, []);
    parLivree.get(c.livree).push(c);
  }
  const camps = [...parLivree.entries()].filter(([, l]) => l.length >= 2);
  if (camps.length < 2) return;
  camps.sort((a, b) => b[1].length - a[1].length);
  const [[livA, corpsA], [livB, corpsB]] = camps;

  const bary = (l) => ({
    x: l.reduce((s, c) => s + c.pos.x, 0) / l.length,
    y: l.reduce((s, c) => s + c.pos.y, 0) / l.length,
  });
  const bA = bary(corpsA);
  const bB = bary(corpsB);
  const d = Math.hypot(bB.x - bA.x, bB.y - bA.y);
  if (d < 1e-6) return;
  const u = { x: (bB.x - bA.x) / d, y: (bB.y - bA.y) / d };

  const fronts = [
    { livree: livA, front: analyserFront(corpsA, bA, u) },
    { livree: livB, front: analyserFront(corpsB, bB, { x: -u.x, y: -u.y }) },
  ];

  ctx.save();
  // les deux contours de front (courbes), teintés à la livrée
  for (const { livree, front } of fronts) {
    const couleur = COULEURS_LIVREE[livree] ?? '#9aa0ae';
    const trace = lisserContour(front.contour);
    if (trace.length >= 2) {
      ctx.beginPath();
      const p0 = camera.versEcran(trace[0]);
      ctx.moveTo(p0.x, p0.y);
      // courbe : quadratiques par points-milieux (aucun angle au tracé)
      for (let i = 1; i < trace.length - 1; i++) {
        const e = camera.versEcran(trace[i]);
        const s = camera.versEcran({ x: (trace[i].x + trace[i + 1].x) / 2, y: (trace[i].y + trace[i + 1].y) / 2 });
        ctx.quadraticCurveTo(e.x, e.y, s.x, s.y);
      }
      const fin = camera.versEcran(trace[trace.length - 1]);
      ctx.lineTo(fin.x, fin.y);
      ctx.strokeStyle = couleur;
      ctx.globalAlpha = 0.5;
      ctx.lineWidth = 7;
      ctx.lineCap = 'round';
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
  }

  // la perpendiculaire centrale : l'axe de menace entre les deux fronts
  const cA = fronts[0].front.centre;
  const cB = fronts[1].front.centre;
  const eA = camera.versEcran(cA);
  const eB = camera.versEcran(cB);
  ctx.setLineDash([6, 6]);
  ctx.strokeStyle = 'rgba(214, 218, 227, 0.55)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(eA.x, eA.y);
  ctx.lineTo(eB.x, eB.y);
  ctx.stroke();
  ctx.setLineDash([]);

  // les étiquettes : envergure + % de trous par front, distance au milieu
  for (const { livree, front } of fronts) {
    const couleur = COULEURS_LIVREE[livree] ?? '#9aa0ae';
    const recul = livree === fronts[0].livree ? { x: -u.x, y: -u.y } : u;
    const posEtiquette = { x: front.centre.x + recul.x * 2.2, y: front.centre.y + recul.y * 2.2 };
    etiqueter(ctx, camera, posEtiquette, `${front.envergure.toFixed(1)} m — ${Math.round(front.partTrous * 100)} % de trous`, couleur);
  }
  const dFronts = Math.hypot(cB.x - cA.x, cB.y - cA.y);
  etiqueter(
    ctx,
    camera,
    { x: (cA.x + cB.x) / 2, y: (cA.y + cB.y) / 2 },
    `${dFronts.toFixed(1)} m`,
    'rgba(214, 218, 227, 0.9)'
  );
  ctx.restore();
}
