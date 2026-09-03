/**
 * 🧠 Compétences / Flâner — sans amis connus (mémoire vide, homme seul) :
 * un point aléatoire dans la zone du scénario.
 * Contrat commun : (ctx) → {intention, objectifHumain, cible}.
 */

import { allerA } from '../intentions.js';

/** @param {{rng, zone}} ctx */
export function flaner(ctx) {
  const cible = {
    x: ctx.rng.entre(ctx.zone.x, ctx.zone.x + ctx.zone.largeur),
    y: ctx.rng.entre(ctx.zone.y, ctx.zone.y + ctx.zone.hauteur),
  };
  return { intention: allerA(cible), objectifHumain: 'flâner', cible };
}
