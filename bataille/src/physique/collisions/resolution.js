/**
 * ⚙️ Physique / Collisions / Résolution — la résolution DURE : personne ne
 * se traverse. Cercle/cercle (hommes) et cercle/rectangle (maisons), par
 * relaxation itérative. Fonctions PURES : positions corrigées en sortie,
 * aucune écriture (la seule écriture passe par appliquerIntegration, 🌍).
 */

const clamp = (v, min, max) => Math.min(Math.max(v, min), max);

/**
 * Sépare les interpénétrations après le pas d'intégration provisoire.
 * La correction se répartit en INVERSE des masses : le lourd tient, le
 * léger cède — une ligne d'hommes ne bloque pas un demi-tonne lancé.
 * @param {{id: number, pos: {x,y}, rayon: number, masse?: number}[]} corpsProvisoires
 * @param {(pos, rayon) => Object[]} obstaclesPres — vue 🌍 (terrain)
 * @param {{iterations?: number}} [params]
 * @returns {Map<number, {x: number, y: number}>} position corrigée par id
 */
export function resoudreCollisions(corpsProvisoires, obstaclesPres, { iterations = 2 } = {}, pairesIds = null) {
  // copies de travail — l'entrée n'est pas modifiée
  const corps = corpsProvisoires.map((c) => ({ id: c.id, rayon: c.rayon, masse: c.masse ?? 80, pos: { x: c.pos.x, y: c.pos.y } }));
  // paires candidates : celles de la grille du tick (ids), ou toutes (fallback)
  const parId = pairesIds ? new Map(corps.map((c) => [c.id, c])) : null;
  const candidates = pairesIds
    ? pairesIds.map(([a, b]) => [parId.get(a), parId.get(b)]).filter(([a, b]) => a && b)
    : null;

  const separer = (ca, cb) => {
    const dx = cb.pos.x - ca.pos.x, dy = cb.pos.y - ca.pos.y;
    const d = Math.hypot(dx, dy);
    const minD = ca.rayon + cb.rayon;
    if (d >= minD) return;
    const ux = d > 1e-9 ? dx / d : 1, uy = d > 1e-9 ? dy / d : 0; // départage déterministe
    // répartition en inverse des masses (le lourd tient sa ligne)
    const total = minD - d;
    const partA = cb.masse / (ca.masse + cb.masse);
    ca.pos.x -= ux * total * partA;
    ca.pos.y -= uy * total * partA;
    cb.pos.x += ux * total * (1 - partA);
    cb.pos.y += uy * total * (1 - partA);
  };

  for (let iter = 0; iter < iterations; iter++) {
    // cercle ↔ cercle : chacun recule de la moitié du chevauchement
    if (candidates) {
      for (const [ca, cb] of candidates) separer(ca, cb);
    } else {
      for (let a = 0; a < corps.length; a++) {
        for (let b = a + 1; b < corps.length; b++) separer(corps[a], corps[b]);
      }
    }

    // cercle ↔ rectangle : expulsé du côté le plus proche
    for (const c of corps) {
      for (const o of obstaclesPres(c.pos, c.rayon + 0.1)) {
        const px = clamp(c.pos.x, o.x, o.x + o.largeur);
        const py = clamp(c.pos.y, o.y, o.y + o.hauteur);
        const dx = c.pos.x - px, dy = c.pos.y - py;
        const d = Math.hypot(dx, dy);
        if (d >= c.rayon) continue;
        if (d > 1e-9) {
          // centre dehors : pousse le long de la normale au point le plus proche
          const pousse = c.rayon - d;
          c.pos.x += (dx / d) * pousse;
          c.pos.y += (dy / d) * pousse;
        } else {
          // centre DANS le rectangle : sortie par la face la plus proche
          const sorties = [
            { x: o.x - c.rayon - c.pos.x, y: 0, cout: c.pos.x - o.x },
            { x: o.x + o.largeur + c.rayon - c.pos.x, y: 0, cout: o.x + o.largeur - c.pos.x },
            { x: 0, y: o.y - c.rayon - c.pos.y, cout: c.pos.y - o.y },
            { x: 0, y: o.y + o.hauteur + c.rayon - c.pos.y, cout: o.y + o.hauteur - c.pos.y },
          ];
          sorties.sort((s1, s2) => s1.cout - s2.cout);
          c.pos.x += sorties[0].x;
          c.pos.y += sorties[0].y;
        }
      }
    }
  }

  return new Map(corps.map((c) => [c.id, c.pos]));
}
