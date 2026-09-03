/**
 * 🧠 Brains / Commandant — l'HOMME + LE RÔLE, en parallèle :
 * - l'homme : la machine soldat complète (corps, peur, tempo ~0,5 Hz),
 *   monopole des intentions motrices ;
 * - le rôle : l'état-major (estimation → projection → arbitre), au tempo du
 *   commandement (~0,1 Hz) + SAILLANCE (un fait qui bascule force la
 *   délibération, vérifiée à ~1 Hz), qui ne produit QUE des paroles
 *   (via le puits emettreOrdre — échafaudage, puis Transmission 📯).
 * introspect() étend celui du soldat avec l'état-major (viz 🖥️).
 */

import { creerSoldat } from '../soldat/brain.js';
import { creerCadence } from '../cadence.js';
import { creerArbitre } from './arbitre.js';

/**
 * @param {Object} deps — celles de creerSoldat, plus :
 * @param {Object[]} deps.manoeuvres — le livre (doctrine/manoeuvres/)
 * @param {(ordre: Object) => void} deps.emettreOrdre — le puits de paroles
 */
export function creerCommandant({ manoeuvres, emettreOrdre, carte, ...depsSoldat }) {
  const soldat = creerSoldat(depsSoldat);
  const { representation, rng, zone, drill, params } = depsSoldat;
  const arbitre = creerArbitre({ manoeuvres, representation, rng, params, zone, drill, carte, tire: () => !!depsSoldat.arcTirDe?.(representation.monId) && (depsSoldat.flechesDe?.(representation.monId) ?? 0) > 0 });
  const cadenceRole = creerCadence({ rng, ...params.commandement.cadence, hzPlancher: 0.02 });
  let accumSaillance = 0;

  return {

    // ── SE RELIRE : celle de l'homme, plus l'accumulateur du role.
    etat() {
      return { role: 'commandant', soldat: soldat.etat(), accumSaillance };
    },

    restaurer(d = {}) {
      soldat.restaurer(d.soldat);
      accumSaillance = d.accumSaillance ?? 0;
    },
    decide(dt) {
      const intention = soldat.decide(dt); // l'homme d'abord

      // le rôle, à son tempo
      arbitre.vieillir(dt);
      accumSaillance += dt;
      let delibere = cadenceRole.echue(dt);
      if (!delibere && accumSaillance >= 1) {
        accumSaillance = 0;
        delibere = arbitre.saillance();
      }
      if (delibere) {
        const { aEmettre } = arbitre.deliberer();
        if (aEmettre) emettreOrdre(aEmettre);
      }

      return intention;
    },

    introspect() {
      return { ...soldat.introspect(), brain: 'commandant', etatMajor: arbitre.etatMajorDebug() };
    },

    /** Calque état-major (🖥️) : la dernière délibération, carte comprise. */
    etatMajorDebug() {
      return arbitre.etatMajorDebug();
    },

    formationDebug() {
      return soldat.formationDebug();
    },

    etatCourant() {
      return soldat.etatCourant();
    },
  };
}
