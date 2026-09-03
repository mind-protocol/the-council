/**
 * ⚙️ Physique / Forces / Répulsions — champs DOUX : les murs repoussent
 * légèrement, les hommes se repoussent entre eux. Influence, n'interdit pas
 * (l'interdiction, c'est collisions/). Profil linéaire : pleine intensité au
 * contact, nulle à la portée. Les intensités s'expriment en m/s (biais de
 * vitesse appliqué par l'intégration). Les PAIRES viennent de la grille du
 * tick (forces/paires.js) — le O(n²) est un fallback quand on n'en donne pas.
 */

const clamp = (v, min, max) => Math.min(Math.max(v, min), max);

/**
 * @param {Iterable<Object>} tousCorps — vue 🌍 (Corps)
 * @param {(pos, rayon) => Object[]} obstaclesPres — vue 🌍 (terrain)
 * @param {{repulsionHommes: {portee, intensite}, repulsionMurs: {portee, intensite}}} params
 * @returns {Map<number, {x: number, y: number}>} force par id
 */
export function calculerRepulsions(tousCorps, obstaclesPres, params, paires = null) {
  const corps = [...tousCorps];
  /** @type {Map<number, {x: number, y: number}>} */
  const forces = new Map();
  const ajouter = (id, fx, fy) => {
    const f = forces.get(id) ?? { x: 0, y: 0 };
    f.x += fx;
    f.y += fy;
    forces.set(id, f);
  };

  // Hommes ↔ hommes (paires, symétrique) — grille du tick, ou fallback n²
  const { portee: pH, intensite: iH } = params.repulsionHommes;
  // AUTOUR D'UN CHEVAL, le champ est plus fort et porte plus loin : une monture
  // pousse ce qui l'approche au lieu de le laisser se coller à son flanc. Un
  // homme ne marche pas dans un cheval. Reglable par params.repulsionCheval ;
  // defaut ici pour que le fichier reste autonome.
  const rc = params.repulsionCheval || { facteurIntensite: 2.5, porteeSup: 0.6 };
  const surPaire = (ca, cb) => {
    const dx = cb.pos.x - ca.pos.x, dy = cb.pos.y - ca.pos.y;
    const d = Math.hypot(dx, dy);
    const surface = d - ca.rayon - cb.rayon; // distance entre surfaces
    const cheval = ca.gabarit === 'cheval' || cb.gabarit === 'cheval';
    const portee = cheval ? pH + rc.porteeSup : pH;
    const inten = cheval ? iH * rc.facteurIntensite : iH;
    if (surface >= portee) return;
    const t = 1 - clamp(surface, 0, portee) / portee; // 1 au contact → 0 à la portée
    // d ≈ 0 : direction dégénérée — départage déterministe par l'axe x
    const ux = d > 1e-9 ? dx / d : 1, uy = d > 1e-9 ? dy / d : 0;
    ajouter(ca.id, -ux * inten * t, -uy * inten * t);
    ajouter(cb.id, ux * inten * t, uy * inten * t);
  };
  if (paires) {
    for (const [ca, cb] of paires) surPaire(ca, cb);
  } else {
    for (let a = 0; a < corps.length; a++) {
      for (let b = a + 1; b < corps.length; b++) surPaire(corps[a], corps[b]);
    }
  }

  // Murs → hommes
  const { portee: pM, intensite: iM } = params.repulsionMurs;
  for (const c of corps) {
    for (const o of obstaclesPres(c.pos, pM + c.rayon)) {
      const px = clamp(c.pos.x, o.x, o.x + o.largeur);
      const py = clamp(c.pos.y, o.y, o.y + o.hauteur);
      const dx = c.pos.x - px, dy = c.pos.y - py;
      const d = Math.hypot(dx, dy);
      if (d < 1e-9) continue; // centre dans le mur : collisions/ s'en charge
      const surface = d - c.rayon;
      if (surface >= pM) continue;
      const t = 1 - clamp(surface, 0, pM) / pM;
      ajouter(c.id, (dx / d) * iM * t, (dy / d) * iM * t);
    }
  }

  return forces;
}

/**
 * Les GISANTS repoussent doucement les vivants — on essaie de ne pas
 * trébucher sur les morts. Unidirectionnel : le cadavre ne bouge pas.
 * @param {Array} vivants @param {Array} gisants
 * @param {Map<number, {x, y}>} forces — accumulateur partagé
 * @param {{portee, intensite}} params
 */
export function ajouterRepulsionGisants(vivants, gisants, forces, { portee, intensite }, pairesMixtes = null) {
  const ajouter = (id, fx, fy) => {
    const f = forces.get(id) ?? { x: 0, y: 0 };
    f.x += fx;
    f.y += fy;
    forces.set(id, f);
  };
  const surPaire = (v, g) => {
    const dx = v.pos.x - g.pos.x;
    const dy = v.pos.y - g.pos.y;
    const d = Math.hypot(dx, dy);
    const surface = d - v.rayon - g.rayon;
    if (surface >= portee || d < 1e-9) return;
    const t = 1 - clamp(surface, 0, portee) / portee;
    ajouter(v.id, (dx / d) * intensite * t, (dy / d) * intensite * t);
  };
  if (pairesMixtes) {
    for (const [a, b] of pairesMixtes) {
      if (a.posture === 'gisant') surPaire(b, a);
      else surPaire(a, b);
    }
  } else {
    for (const v of vivants) for (const g of gisants) surPaire(v, g);
  }
}
