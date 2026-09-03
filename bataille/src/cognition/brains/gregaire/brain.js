/**
 * 🧠 Brains / Grégaire — brain autonome pour les hommes SANS unité (drag &
 * drop) : rejoint le tas cru de ses escouade s'il en a, sinon flâne. La logique
 * vit dans la machine déclarative (machine.js) ; le brain ne fait que la
 * cadencer et l'introspecter. Interface commune : decide() + introspect().
 */

import { creerCadence } from '../cadence.js';
import { creerMachine } from '../machine.js';
import { decrireTas } from '../../langage/decrire.js';
import { creerChercher, PRIORITES_TROUPIER } from '../../competences/chercher.js';
import { creerParoles } from '../../paroles.js';
import { MACHINE_GREGAIRE, gardesCercle, actionsCercle } from './machine.js';

// le grégaire n'a ni corps suivi (souffle) ni peur outillée : jauges neutres
const JAUGES_NEUTRES = { peur: 0, souffle: 1, aArc: false, fleches: 0 };

/**
 * @param {Object} deps
 * @param {ReturnType<import('../../../infra/rng.js').creerRng>} deps.rng
 * @param {ReturnType<import('../../representation.js').creerRepresentation>} deps.representation
 * @param {{x, y, largeur, hauteur}} deps.zone
 * @param {{cadence, discussion}} deps.params
 * @param {(texte: string, dureeS: number) => void} [deps.dire] — le puits de parole (flavor)
 */
export function creerGregaire({ rng, representation, zone, params, dire }) {
  const cadence = creerCadence({ rng, ...params.cadence });
  const machine = creerMachine({
    definition: MACHINE_GREGAIRE,
    gardes: gardesCercle,
    actions: actionsCercle,
  });
  const ctx = {
    representation,
    rng,
    zone,
    params,
    lireTas: (r) => r.tasCru('escouade'),
    chercheur: creerChercher({ representation, rng, zone, params, priorites: PRIORITES_TROUPIER }),
  };
  const paroles = creerParoles({ graine: representation.monId, dire, params });
  let dernier = { objectifHumain: 'flâner', cible: null };

  return {

    // ── SE RELIRE (docs/sauvegarde.md) : la FEUILLE de la machine avant tout.
    etat() {
      return { role: 'gregaire', machine: machine.etat(), dernier };
    },

    restaurer(d = {}) {
      machine.restaurer(d.machine);
      if (d.dernier) dernier = { ...d.dernier };
    },
    decide(dt) {
      machine.vieillir(dt);
      let r = null;
      if (cadence.echue(dt)) {
        const avant = machine.etat();
        r = machine.decider(ctx);
        if (machine.etat() !== avant) paroles.evenement(avant, machine.etat());
        if (r) dernier = r;
      }
      paroles.tick(dt, { etat: machine.etat(), jauges: () => JAUGES_NEUTRES });
      return r?.intention ?? null;
    },

    /** Condition fine pour l'orientation (🧠) : la feuille courante. */
    etatCourant() {
      return machine.etat().split('.').pop();
    },

    introspect() {
      const escouade = representation.tasCru('escouade');
      return {
        brain: 'gregaire',
        etat: machine.etat(),
        objectifHumain: dernier.objectifHumain,
        machine: machine.description(),
        details: {
          escouadeCrue: escouade ? decrireTas(escouade) : 'nulle part',
          cible: dernier.cible,
          dernieresParoles: paroles.introspect(),
          prochaineDecisionDansS: cadence.restant(),
        },
      };
    },
  };
}
