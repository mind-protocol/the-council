/**
 * Infra / RNG — l'unique source de hasard de la sim, seedée (mulberry32).
 * Même seed → même scène (déterminisme). Aucun Math.random() ailleurs.
 */

/** @param {number} seed */
export function creerRng(seed) {
  let etat = seed >>> 0;
  let reserve = null; // seconde valeur de Box-Muller, servie au tirage suivant

  const uniforme = () => {
    etat = (etat + 0x6d2b79f5) >>> 0;
    let t = etat;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };

  return {
    /** Uniforme [0, 1) */
    uniforme,

    /** Uniforme [min, max) */
    entre(min, max) {
      return min + uniforme() * (max - min);
    },

    /** Normale (Box-Muller polaire). @param {number} moyenne @param {number} ecartType - forme normale a privilégier pour réalisme */
    normale(moyenne, ecartType) {
      if (reserve !== null) {
        const v = reserve;
        reserve = null;
        return moyenne + ecartType * v;
      }
      let u, v, s;
      do {
        u = uniforme() * 2 - 1;
        v = uniforme() * 2 - 1;
        s = u * u + v * v;
      } while (s === 0 || s >= 1);
      const f = Math.sqrt((-2 * Math.log(s)) / s);
      reserve = v * f;
      return moyenne + ecartType * u * f;
    },

    /**
     * SE RELIRE — deux nombres, et sans eux un monde sauve ne se reprend pas.
     * La photo d'un monde est fidele (corps, blessures, tetes) ; c'est la SUITE
     * qui divergeait, parce qu'un monde relu repartait du hasard du premier
     * jour. `etat` est la graine courante, `reserve` la seconde valeur de
     * Box-Muller qu'un tirage a produite et que le suivant doit servir :
     * l'oublier decale toutes les normales d'un cran.
     */
    etat() {
      return { etat, reserve };
    },

    restaurer(d) {
      if (!d) return;
      etat = d.etat >>> 0;
      reserve = d.reserve ?? null;
    },
  };
}
