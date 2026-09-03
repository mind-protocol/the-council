/**
 * 🖥️ Présentation / Caméra — monde (mètres) ↔ écran (pixels). SEUL endroit
 * du projet qui connaît les pixels. écran = monde × échelle + décalage.
 */

/** @param {{pixelsParMetre?: number}} [options] — zoom initial, défaut 20 */
export function creerCamera({ pixelsParMetre = 20 } = {}) {
  let ppm = pixelsParMetre;
  let ox = 0;
  let oy = 0;

  return {
    /** @param {{x,y}} posMonde (m) @returns {{x,y}} pixels canvas */
    versEcran(posMonde) {
      return { x: posMonde.x * ppm + ox, y: posMonde.y * ppm + oy };
    },

    /** @param {{x,y}} posEcran (px) @returns {{x,y}} mètres monde */
    versMonde(posEcran) {
      return { x: (posEcran.x - ox) / ppm, y: (posEcran.y - oy) / ppm };
    },

    /**
     * Zoom multiplicatif centré sur un point écran (le point sous le curseur
     * ne bouge pas). Échelle bornée [0.01, 400] px/m — le plancher n'est pas
     * une limite d'usage (1 px = 100 m : tout théâtre tient à l'écran), juste
     * la garde contre l'échelle nulle.
     * @param {number} facteur @param {{x,y}} pivotEcran
     */
    zoomer(facteur, pivotEcran) {
      // Plafond de zoom (le plus PRES) baisse : 400 ppm mettait un seul homme
      // plein ecran, inutile sur une grande carte. 150 laisse le detail sans
      // qu'on se perde dans un pixel. Plancher inchange (le plus LOIN).
      const nouveau = Math.min(Math.max(ppm * facteur, 0.01), 150);
      const reel = nouveau / ppm;
      ox = pivotEcran.x - (pivotEcran.x - ox) * reel;
      oy = pivotEcran.y - (pivotEcran.y - oy) * reel;
      ppm = nouveau;
    },

    /** Pan en pixels (drag). @param {{x,y}} deltaEcran */
    deplacer(deltaEcran) {
      ox += deltaEcran.x;
      oy += deltaEcran.y;
    },

    /** @returns {number} pixels par mètre courant */
    echelle() {
      return ppm;
    },
  };
}
