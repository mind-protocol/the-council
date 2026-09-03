/**
 * 🧠 Compétences / Monter — le savoir-faire du couple monté. LA PASSE :
 * un cavalier ne se tient pas au contact — il traverse, reprend du champ
 * hors de portée, se reforme, et revient. `seDegager` est le COMMENT du
 * dégagement ; les prédicats (`enSelle`, `elanSuffisant`) sont purs et
 * partagés avec les gardes de la machine — l'infanterie n'est jamais
 * concernée (tout est gardé par la selle).
 */

import { allerA, attendre } from '../intentions.js';

/** Suis-je en selle ? PUR (ctx.monture : thunk 🌍 via le brain). */
export function enSelle(ctx) {
  return (ctx.monture?.() ?? null) !== null;
}

/** La masse adverse CRUE (fraîche, tolérance x3 comme la volée), ou null. */
function masseAdverse(representation, params) {
  const t = representation.tasCru('ennemis') ?? representation.tasCru('inconnu');
  if (!t || !t.livree || !representation.maLivree || t.livree === representation.maLivree) return null;
  if (t.ageS >= params.menace.fraicheurS * 3) return null;
  return t;
}

/**
 * L'ÉLAN : une charge a besoin de distance — monté, on ne la (re)donne
 * qu'avec assez de champ devant la masse crue. À pied : toujours vrai.
 * PUR — partagé par la garde `ordreCharger`.
 */
export function elanSuffisant(ctx) {
  if (!enSelle(ctx)) return true;
  const t = masseAdverse(ctx.representation, ctx.params);
  const moi = ctx.representation.moi;
  if (!t?.barycentre || !moi.pos) return true; // pas de masse crue : rien ne retient
  return Math.hypot(moi.pos.x - t.barycentre.x, moi.pos.y - t.barycentre.y) >= ctx.params.cheval.passe.repriseM;
}

/** Le verbe : traverser, sortir au trot, reprendre du champ pour repasser. */
export function seDegager(ctx) {
  const r = ctx.representation;
  const t = masseAdverse(r, ctx.params);
  if (!t?.barycentre || !r.moi.pos) {
    return { intention: attendre(), objectifHumain: 'du champ repris — je me reforme', cible: null };
  }
  // on prolonge SA course : loin de la masse, du côté où l'on est déjà
  const dx = r.moi.pos.x - t.barycentre.x;
  const dy = r.moi.pos.y - t.barycentre.y;
  const d = Math.hypot(dx, dy) || 1;
  const portee = ctx.params.cheval.passe.repriseM + 4; // sortir un peu au-delà de la reprise
  const cible = { x: t.barycentre.x + (dx / d) * portee, y: t.barycentre.y + (dy / d) * portee };
  return {
    intention: allerA(cible, 1, 'trot'),
    objectifHumain: 'traverser et reprendre du champ pour repasser',
    cible,
  };
}
