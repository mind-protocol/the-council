/**
 * ⏱️ Orchestration — EXPOSE, seule porte d'entrée (règles : CLAUDE.md).
 * Possède le temps. Seul le bootstrap lui donne du temps réel (sa boucle de
 * frame) ; les containers ne voient que le dt de leurs phases.
 */

import { creerHorloge } from './horloge.js';
import { creerPipeline } from './pipeline.js';

/**
 * @param {{phases: import('./pipeline.js').Phase[], dtFixe?: number}} deps
 */
export function creerOrchestration({ phases, dtFixe }) {
  const horloge = creerHorloge({ dtFixe });
  const pipeline = creerPipeline(phases);

  return {
    /**
     * Avance la sim du temps réel écoulé : N pas fixes via le pipeline.
     * Appelé uniquement par la boucle de frame du bootstrap.
     * @param {number} msReelles
     */
    avancer(msReelles) {
      const n = horloge.pasAExecuter(msReelles);
      const dt = horloge.etat().dtFixe;
      for (let i = 0; i < n; i++) pipeline.executerTick(dt);
    },

    /** COMMANDES pour 🖥️ Présentation (transport). */
    transport: {
      basculerPause: () => horloge.basculerPause(),
      reglerVitesse: (m) => horloge.reglerVitesse(m),
      etat: () => horloge.etat(),
      // reprendre le temps ou on l'a laisse (voir horloge.restaurer)
      restaurer: (d) => horloge.restaurer(d),
    },
  };
}
