/**
 * 🧠 Brains / Oiseau / Brain — le corbeau et le rapace de chasse. UN brain
 * pour les deux : ce qui les sépare est dans le profil (❤️ oiseaux.js), pas
 * dans le graphe. Contrat commun : `decide()` + `introspect()`. Il pilote la
 * MACHINE_OISEAU (machine.js) sur ses croyances (la masse CRUE en bas) et sa
 * proprioception (cap/allure par velDe, altitude par moi.pos.z) — jamais une
 * position, jamais le registre. Le profil est un SAVOIR SUR SOI (❤️, injecté
 * au bootstrap), comme l'arme du soldat.
 *
 * Il ne connaît personne et ne veut rien de personne : il vole au-dessus de
 * la bataille et regarde. Aucune de ses intentions ne blesse.
 */

import { creerCadence } from '../cadence.js';
import { creerMachine } from '../machine.js';
import { MACHINE_OISEAU, gardes, actions } from './machine.js';

/**
 * @param {Object} deps
 * @param {ReturnType<import('../../../infra/rng.js').creerRng>} deps.rng
 * @param {Object} deps.representation — les croyances (dont moi.pos {x,y,z}, proprioception)
 * @param {() => {x: number, y: number}} deps.velDe — proprioception : ma vitesse (le cap s'en dérive)
 * @param {{x, y, largeur, hauteur}} deps.zone — le champ (le cercle s'y tient)
 * @param {Object} deps.profil — l'entrée ❤️ OISEAUX portée (un savoir sur soi)
 * @param {Object} deps.params
 */
export function creerOiseau({ rng, representation, velDe, zone, profil, params }) {
  const cadence = creerCadence({ rng, ...(params.oiseau?.cadence ?? params.cadence) });
  const machine = creerMachine({ definition: MACHINE_OISEAU, gardes, actions });
  const ctx = { representation, velDe, zone, profil, params, rng, vecu: { etatS: 0 }, passe: null, axe: null };
  let dernier = { objectifHumain: "prendre l'air", cible: null };

  return {
    etat() {
      return { role: 'oiseau', machine: machine.etat(), dernier };
    },

    restaurer(d = {}) {
      machine.restaurer(d.machine);
      if (d.dernier) dernier = { ...d.dernier };
    },

    decide(dt) {
      machine.vieillir(dt);
      ctx.vecu.etatS += dt;
      if (!cadence.echue(dt)) return null;
      const avant = machine.etat();
      const r = machine.decider(ctx);
      if (machine.etat() !== avant) ctx.vecu.etatS = 0; // le temps repart avec l'état
      if (r) dernier = r;
      return r?.intention ?? null;
    },

    /** Condition fine pour l'orientation (🧠) : la feuille courante. */
    etatCourant() {
      return machine.etat().split('.').pop();
    },

    introspect() {
      return {
        brain: 'oiseau',
        etat: machine.etat(),
        objectifHumain: dernier.objectifHumain,
        machine: machine.description(),
        details: {
          profil: profil.nom,
          cible: dernier.cible,
          capPasse: ctx.passe?.cap ?? null,
          tempsDansEtatS: ctx.vecu.etatS,
          prochaineDecisionDansS: cadence.restant(),
        },
      };
    },
  };
}
