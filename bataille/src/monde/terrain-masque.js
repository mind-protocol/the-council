/**
 * 🌍 Monde / Terrain-masque
 * Le « pathmap » d'une ville cuite (le-conseil2) : une grille de cases de
 * `pas` mètres, 1 bit par case, bit à 1 = bâti (courtines comprises, les
 * portes restent percées). Cuit ailleurs (plan_ville.py) — ici on ne fait
 * que LIRE. Hors de la grille : libre (le plan reste infini).
 *
 * Repères : le plan cuit a l'Y vers le NORD (haut) ; le monde bataille a le
 * sud en bas (y croissant vers le sud) — `inverserY` fait la conversion à
 * la lecture, déclaré par le scénario (une propriété de la source, pas un
 * défaut deviné). Adressage du bit : k = j*nx + i, poids faible d'abord.
 */

import { distanceCarreeAuRect } from './terrain.js';

/**
 * @param {Object} desc
 * @param {number} desc.nx      — colonnes
 * @param {number} desc.ny      — lignes
 * @param {number} desc.pas     — mètres par case
 * @param {Uint8Array} desc.bits — le fichier .masque.bin, brut
 * @param {boolean} [desc.inverserY] — la source a l'Y vers le nord
 */
export function creerTerrainMasque({ nx, ny, pas, bits, inverserY = false }) {
  // LE DESCRIPTEUR DOIT ÊTRE CELUI DU FICHIER : un masque recuit à un autre pas
  // lu avec l'ancien nx brouille terre et mer en silence (mesuré le 2 septembre :
  // la péninsule recuite au mètre, lue avec 3 557 cases par ligne — spawns refusés)
  const attendus = Math.ceil((nx * ny) / 8);
  if (!bits || bits.length !== attendus) {
    throw new Error(`masque : ${bits ? bits.length : 0} octets pour ${nx} x ${ny} cases (${attendus} attendus) — le descripteur (nx, ny, pas) n'est pas celui de ce fichier, recomposer`);
  }
  const bloquee = (i, j) => {
    if (i < 0 || j < 0 || i >= nx || j >= ny) return false;
    const js = inverserY ? ny - 1 - j : j;
    const k = js * nx + i;
    return ((bits[k >> 3] >> (k & 7)) & 1) === 1;
  };
  /** Le rectangle monde d'une case (même forme que les obstacles posés). */
  const rectDe = (i, j) => ({ x: i * pas, y: j * pas, largeur: pas, hauteur: pas });

  /**
   * Itère les cases bloquées dans la fenêtre [x0..x1]×[y0..y1] (mètres),
   * en ordre stable (j puis i — le déterminisme en dépend).
   */
  function* casesBloquees(x0, y0, x1, y1) {
    const i0 = Math.floor(x0 / pas);
    const j0 = Math.floor(y0 / pas);
    const i1 = Math.floor(x1 / pas);
    const j1 = Math.floor(y1 / pas);
    for (let j = j0; j <= j1; j++)
      for (let i = i0; i <= i1; i++) if (bloquee(i, j)) yield rectDe(i, j);
  }

  return {
    /** Un cercle chevauche-t-il du bâti ? (navgrid, spawn) */
    chevaucheObstacle(centre, rayon) {
      const r2 = rayon * rayon;
      for (const o of casesBloquees(centre.x - rayon, centre.y - rayon, centre.x + rayon, centre.y + rayon))
        if (distanceCarreeAuRect(centre, o) < r2) return true;
      return false;
    },

    /**
     * Les cases bloquées à distance ≤ rayon, comme rectangles — le même
     * contrat que les obstacles posés (⚙️ répulsion des murs, collision).
     * @param {{x, y}} pos @param {number} rayon @returns {Array}
     */
    obstaclesPres(pos, rayon) {
      const r2 = rayon * rayon;
      const res = [];
      for (const o of casesBloquees(pos.x - rayon, pos.y - rayon, pos.x + rayon, pos.y + rayon))
        if (distanceCarreeAuRect(pos, o) <= r2) res.push(o);
      return res;
    },

    /**
     * VUE debug (calque terrain, 🖥️) : les cases bloquées dans un rectangle
     * monde — la VÉRITÉ du masque, à confronter au dessin du plan cuit.
     * @param {{x, y, largeur, hauteur}} rect
     */
    casesBloqueesDans(rect) {
      return [...casesBloquees(rect.x, rect.y, rect.x + rect.largeur, rect.y + rect.hauteur)];
    },
  };
}
