/**
 * 🏃 Action / Steering / Suivi de chemin — vitesse désirée vers le waypoint
 * courant, waypoint suivant quand assez proche, arrivé au dernier → immobile.
 * La vitesse max viendra du ❤️ Corps plus tard ; des params pour l'instant.
 * (Futurs voisins de dossier : evitement.js, arrivee.js.)
 */

/**
 * @param {{vitesseMax: number, seuilWaypoint?: number}} options
 *   — seuilWaypoint : distance (m) sous laquelle un waypoint est atteint
 */
export function creerSuivi({ vitesseMax, seuilWaypoint = 0.3 }) {
  return {
    /**
     * Un pas de suivi pour un corps.
     * @param {{x: number, y: number}[]} chemin
     * @param {number} index — waypoint courant
     * @param {{x: number, y: number}} pos — position actuelle du corps
     * @returns {{vel: {x: number, y: number}, index: number, arrive: boolean}}
     */
    avancer(chemin, index, pos) {
      // avale les waypoints déjà atteints (plusieurs si le pas est grand)
      while (index < chemin.length) {
        const w = chemin[index];
        const dx = w.x - pos.x, dy = w.y - pos.y;
        if (dx * dx + dy * dy > seuilWaypoint * seuilWaypoint) break;
        index++;
      }
      if (index >= chemin.length) {
        return { vel: { x: 0, y: 0 }, index, arrive: true };
      }
      const w = chemin[index];
      const dx = w.x - pos.x, dy = w.y - pos.y;
      const d = Math.hypot(dx, dy);
      return {
        vel: { x: (dx / d) * vitesseMax, y: (dy / d) * vitesseMax },
        index,
        arrive: false,
      };
    },
  };
}
