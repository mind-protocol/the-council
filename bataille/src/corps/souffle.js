/**
 * ❤️ Corps / Souffle — la RÉSERVE se dépense linéairement avec l'effort
 * (l'engagement au fer la vide en ~45 s, la marche coûte peu, le repos
 * récupère) ; mais le RESSENTI — ce que lisent la Décision et demain la
 * vitesse effective — est une SIGMOÏDE de la réserve : long plateau frais
 * où rien ne paraît, bascule brutale, plateau épuisé. Pas une barre.
 * Les coûts arrivent des Actes (🏃) en unités d'effort-seconde : 1.0 = une
 * seconde d'engagement à pleine intensité.
 */

export function creerSouffle({ dureeEpuisementS, dureeRecuperationS, sigmoide }) {
  /** @type {Map<number, {reserve: number, effortTick: number}>} */
  const hommes = new Map();

  return {
    /** Au spawn : frais. @param {number} idCorps */
    enregistrer(idCorps) {
      hommes.set(idCorps, { reserve: 1, effortTick: 0 });
    },

    /**
     * Un effort ce tick (poussé par 🏃) : s'accumule jusqu'à la phase.
     * @param {number} idCorps @param {number} effortS — effort-secondes
     */
    depenser(idCorps, effortS) {
      const h = hommes.get(idCorps);
      if (h) h.effortTick += effortS;
    },

    /**
     * PHASE physiologie : consomme l'effort du tick, récupère au repos.
     * @param {number} dt
     */
    phase(dt) {
      for (const h of hommes.values()) {
        if (h.effortTick > 0) {
          h.reserve = Math.max(0, h.reserve - h.effortTick / dureeEpuisementS);
        } else {
          h.reserve = Math.min(1, h.reserve + dt / dureeRecuperationS);
        }
        h.effortTick = 0;
      }
    },

    /**
     * Le RESSENTI : sigmoïde de la réserve, dans [0, 1].
     * @param {number} idCorps @returns {number}
     */
    ressentiDe(idCorps) {
      const h = hommes.get(idCorps);
      if (!h) return 1;
      return 1 / (1 + Math.exp(-sigmoide.raideur * (h.reserve - sigmoide.centre)));
    },

    /** SE RELIRE — la reserve et l'effort du tick en cours. */
    etat() {
      return [...hommes.entries()].map(([id, h]) => [id, { ...h }]);
    },

    restaurer(liste = []) {
      hommes.clear();
      for (const [id, h] of liste) hommes.set(Number(id), { ...h });
    },

    /** La réserve brute (viz/debug). @param {number} idCorps */
    reserveDe(idCorps) {
      return hommes.get(idCorps)?.reserve ?? 1;
    },
  };
}
