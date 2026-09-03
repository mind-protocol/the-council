/**
 * 🌍 Monde / Terrain
 * Les choses immobiles posées sur le plan : maisons (rectangles alignés aux
 * axes) et masques de villes cuites (terrain-masque.js). Le plan est INFINI —
 * pas de bords, pas de « taille de map » (voir CLAUDE.md). Toute modification
 * doit invalider la navgrid (fait par l'expose).
 */

/**
 * @typedef {{x: number, y: number}} Vec2
 *
 * @typedef {Object} Obstacle
 * @property {number} x        — coin min, mètres
 * @property {number} y        — coin min, mètres
 * @property {number} largeur  — mètres
 * @property {number} hauteur  — mètres
 */

/** Carré de la distance d'un point au rectangle (0 si dedans). */
export function distanceCarreeAuRect(p, o) {
  const dx = Math.max(o.x - p.x, 0, p.x - (o.x + o.largeur));
  const dy = Math.max(o.y - p.y, 0, p.y - (o.y + o.hauteur));
  return dx * dx + dy * dy;
}

export function creerTerrain() {
  /** @type {Obstacle[]} */
  const liste = [];
  /** Masques posés (villes cuites) — même contrat de requête, voir terrain-masque.js. */
  const masques = [];

  return {
    /** Pose un obstacle sur le plan. @param {Obstacle} rect */
    ajouterObstacle(rect) {
      liste.push({ ...rect });
    },

    /** Pose un masque (déjà construit). @param {ReturnType<import('./terrain-masque.js').creerTerrainMasque>} m */
    ajouterMasque(m) {
      masques.push(m);
    },

    /**
     * Les rectangles POSÉS seulement — un masque ne s'énumère jamais en
     * entier (des millions de cases), il se lit par requêtes bornées.
     * @returns {Iterable<Obstacle>}
     */
    obstacles() {
      return liste;
    },

    /**
     * Les obstacles à distance ≤ rayon du point (rectangles posés + cases
     * bloquées des masques). Pour ⚙️ Physique (répulsion des murs, collision).
     * @param {Vec2} pos @param {number} rayon @returns {Obstacle[]}
     */
    obstaclesPres(pos, rayon) {
      const r2 = rayon * rayon;
      const res = liste.filter((o) => distanceCarreeAuRect(pos, o) <= r2);
      for (const m of masques) res.push(...m.obstaclesPres(pos, rayon));
      return res;
    },

    /**
     * Un cercle chevauche-t-il un obstacle ? (valider un spawn, une case nav)
     * @param {Vec2} centre @param {number} rayon @returns {boolean}
     */
    chevaucheObstacle(centre, rayon) {
      const r2 = rayon * rayon;
      return (
        liste.some((o) => distanceCarreeAuRect(centre, o) < r2) ||
        masques.some((m) => m.chevaucheObstacle(centre, rayon))
      );
    },

    /**
     * VUE debug : les cases bloquées des masques dans un rectangle monde —
     * la vérité du masque, à confronter au dessin du plan cuit (🖥️).
     * @param {Obstacle} rect @returns {Obstacle[]}
     */
    casesBloqueesDans(rect) {
      return masques.flatMap((m) => m.casesBloqueesDans(rect));
    },
  };
}
