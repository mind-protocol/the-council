/**
 * 🧠 Compétences / Se regrouper — le cercle de discussion autour du
 * barycentre CRU du tas (croyances, pas vérité). Anti-hug : on vise le
 * CERCLE, jamais le centre. Le rayon SE DÉRIVE DE L'EFFECTIF CRU : chacun
 * le calcule de ses propres croyances (aucune coordination) — une escouade
 * de 4 tient sur le petit cercle, un rassemblement de 20 s'étale en anneau
 * (la circonférence doit loger tout le monde à l'espacement près).
 * Trois verbes au contrat commun (ctx) → {intention, objectifHumain, cible}
 * + la géométrie pure que les gardes des machines consultent (le QUOI reste
 * dans les machines).
 */

import { allerA, attendre } from '../intentions.js';

/** Le rayon qui loge l'effectif cru sur la circonférence. PUR. */
function rayonPourEffectif(effectif, { rayon, espacement }) {
  return Math.max(rayon, ((effectif + 1) * espacement) / (2 * Math.PI));
}

/** Géométrie pure moi ↔ cercle, ou null si rien à viser. Pour les GARDES. */
export function geometrieCercle(ctx) {
  const moi = ctx.representation.moi;
  const tas = ctx.lireTas(ctx.representation);
  if (!moi.pos || !tas) return null;
  const { tolerance } = ctx.params.discussion;
  const rayon = rayonPourEffectif(tas.effectif, ctx.params.discussion);
  const d = Math.hypot(moi.pos.x - tas.barycentre.x, moi.pos.y - tas.barycentre.y);
  return { d, rayon, tolerance };
}

/** Mon angle sur le cercle + le point visé (au centre exact : angle tiré). */
function analyser(ctx) {
  const moi = ctx.representation.moi;
  const tas = ctx.lireTas(ctx.representation);
  const barycentre = tas.barycentre;
  const rayon = rayonPourEffectif(tas.effectif, ctx.params.discussion);
  const dx = moi.pos.x - barycentre.x;
  const dy = moi.pos.y - barycentre.y;
  const d = Math.hypot(dx, dy);
  const angle = d > 1e-6 ? Math.atan2(dy, dx) : ctx.rng.entre(0, Math.PI * 2);
  return {
    angle,
    surCercle: (a) => ({
      x: barycentre.x + Math.cos(a) * rayon,
      y: barycentre.y + Math.sin(a) * rayon,
    }),
  };
}

/** Trop loin : je rejoins ma place sur le cercle, dans mon propre axe. */
export function rejoindre(ctx) {
  const a = analyser(ctx);
  const cible = a.surCercle(a.angle);
  return { intention: allerA(cible), objectifHumain: 'rejoindre mon escouade', cible };
}

/** Trop au centre : je recule vers le cercle (anti-hug). */
export function ecarter(ctx) {
  const a = analyser(ctx);
  const cible = a.surCercle(a.angle);
  return { intention: allerA(cible), objectifHumain: "m'écarter un peu", cible };
}

/** Sur le cercle : planté (l'inertie arrête le corps) ; replacement occasionnel. */
export function discuter(ctx) {
  const { flottementAngulaire, probaReplacement } = ctx.params.discussion;
  const a = analyser(ctx);
  if (ctx.rng.uniforme() < probaReplacement) {
    const cible = a.surCercle(a.angle + ctx.rng.entre(-flottementAngulaire, flottementAngulaire));
    return { intention: allerA(cible), objectifHumain: 'discuter avec mon escouade', cible };
  }
  return { intention: attendre(), objectifHumain: 'discuter avec mon escouade', cible: null };
}
