/**
 * 🧠 Cognition / Brain « random walk » — brain de bibliothèque (plus le
 * défaut) : choisit un point aléatoire dans la zone à sa cadence propre.
 * Interface commune à tout brain : decide() + introspect() (obligatoire).
 */

import { allerA } from '../intentions.js';
import { creerCadence } from './cadence.js';

/**
 * @param {Object} deps
 * @param {ReturnType<import('../../infra/rng.js').creerRng>} deps.rng
 * @param {{x: number, y: number, largeur: number, hauteur: number}} deps.zone
 * @param {{moyenneHz?: number, ecartTypeHz?: number}} [deps.cadence]
 */
export function creerRandomWalk({ rng, zone, cadence = {} }) {
  const { moyenneHz = 0.5, ecartTypeHz = 0.1 } = cadence;
  const echeancier = creerCadence({ rng, moyenneHz, ecartTypeHz });
  let cible = null;

  return {
    /** @param {number} dt @returns {import('../intentions.js').Intention | null} */
    decide(dt) {
      if (!echeancier.echue(dt)) return null;
      cible = {
        x: rng.entre(zone.x, zone.x + zone.largeur),
        y: rng.entre(zone.y, zone.y + zone.hauteur),
      };
      return allerA(cible);
    },

    introspect() {
      return {
        brain: 'random-walk',
        etat: cible ? 'en route' : 'pas encore décidé',
        details: {
          cible,
          prochaineDecisionDansS: echeancier.restant(),
          cadenceMoyenneHz: moyenneHz,
        },
      };
    },
  };
}
