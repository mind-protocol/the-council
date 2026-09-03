/**
 * 🧠 Brains / Cadence — l'échéancier commun à tous les brains : chaque tête
 * a son rythme, période retirée ~N(moyenneHz, ecartTypeHz) à chaque décision,
 * phase initiale échelonnée (levier de scale : les décisions s'étalent).
 */

/**
 * @param {Object} deps
 * @param {ReturnType<import('../../infra/rng.js').creerRng>} deps.rng
 * @param {number} deps.moyenneHz
 * @param {number} deps.ecartTypeHz
 * @param {number} [deps.hzPlancher] — borne basse (jamais de période infinie)
 */
export function creerCadence({ rng, moyenneHz, ecartTypeHz, hzPlancher = 0.05 }) {
  const tirerPeriode = () => 1 / Math.max(hzPlancher, rng.normale(moyenneHz, ecartTypeHz));
  let tempsRestant = rng.uniforme() * tirerPeriode(); // échelonnage initial

  return {
    /** L'échéance est-elle atteinte ? (réarme si oui) @param {number} dt */
    echue(dt) {
      tempsRestant -= dt;
      if (tempsRestant > 0) return false;
      tempsRestant = tirerPeriode();
      return true;
    },

    /** @returns {number} secondes avant la prochaine échéance */
    restant() {
      return Math.max(0, tempsRestant);
    },
  };
}
