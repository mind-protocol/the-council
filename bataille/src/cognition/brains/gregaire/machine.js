/**
 * 🧠 Brains / Grégaire / Machine — la FSM déclarative du désœuvrement.
 * Le QUOI : gardes PURES (jamais de rng) + transitions justifiées. Le
 * COMMENT vit dans competences/ (flaner, se-regrouper, chercher) — les
 * actions sont des appels de compétences, plus un if/else métier ici.
 * SEUL, le défaut est CHERCHER (remonter ses croyances périmées) ; flâner
 * est réservé à qui ne connaît personne (homme droppé sans attaches).
 * Partagé avec le soldat via ctx.lireTas (lui vise escouade ?? unite).
 */

import { flaner } from '../../competences/flaner.js';
import { geometrieCercle, rejoindre, ecarter, discuter } from '../../competences/se-regrouper.js';
import { connaitQuelquun } from '../../competences/chercher.js';

/** Menace : un tas inconnu de livree ADVERSE, cru frais, proche. PUR. */
export function menacePercue(ctx) {
  const r = ctx.representation;
  const t = r.tasCru('inconnu');
  if (!t || !t.livree || !r.maLivree || t.livree === r.maLivree) return false;
  if (t.ageS >= ctx.params.menace.fraicheurS) return false;
  const moi = r.moi;
  if (!moi.pos) return false;
  // la distance est vraie (3D) : une menace là-haut n'est pas « à côté »
  return Math.hypot(moi.pos.x - t.barycentre.x, moi.pos.y - t.barycentre.y, t.z ?? 0) < ctx.params.menace.rayon;
}

export const gardesCercle = {
  menaceEtEscouadeLoin: (ctx) => {
    if (!menacePercue(ctx)) return false;
    const g = geometrieCercle(ctx);
    return g !== null && g.d - g.rayon > g.tolerance;
  },
  menaceEtSeul: (ctx) => menacePercue(ctx) && geometrieCercle(ctx) === null,
  seulSansAttaches: (ctx) =>
    geometrieCercle(ctx) === null && !connaitQuelquun(ctx.representation),
  seulAvecAttaches: (ctx) =>
    geometrieCercle(ctx) === null && connaitQuelquun(ctx.representation),
  surLeCercle: (ctx) => {
    const g = geometrieCercle(ctx);
    return g !== null && Math.abs(g.d - g.rayon) <= g.tolerance;
  },
  /** Le tas que je vois est un FRAGMENT : bien moins que ce que je sais exister. */
  groupeReduit: (ctx) => {
    const r = ctx.representation;
    const t = ctx.lireTas(r);
    if (!t) return false;
    const etiquette = t === r.tasCru('escouade') ? 'escouade' : 'unite';
    const attendu = r.attendu(etiquette);
    return attendu > 0 && t.effectif < attendu / 2;
  },
  escouadeLoin: (ctx) => {
    const g = geometrieCercle(ctx);
    return g !== null && g.d - g.rayon > g.tolerance;
  },
  escouadeTropPres: (ctx) => {
    const g = geometrieCercle(ctx);
    return g !== null && g.rayon - g.d > g.tolerance;
  },
};

export const actionsCercle = {
  flaner,
  rejoindre,
  ecarter,
  discuter,
  chercher: (ctx) => ctx.chercheur.chercher(),
};

export const MACHINE_GREGAIRE = {
  brain: 'gregaire',
  initial: 'cherche',
  etats: {
    cherche: { agir: 'chercher' },
    flane: { agir: 'flaner' },
    rejoint: { agir: 'rejoindre' },
    secarte: { agir: 'ecarter' },
    discute: { agir: 'discuter' },
  },
  transitions: [
    // la menace d'abord : se regrouper n'est PAS fuir (fuir = la deroute, reservee)
    { de: '*', vers: 'rejoint', quand: 'menaceEtEscouadeLoin', libelle: 'une unité ennemie approche — je me regroupe' },
    { de: '*', vers: 'cherche', quand: 'menaceEtSeul', libelle: 'une unité ennemie approche, seul — je rallie les miens' },
    { de: '*', vers: 'cherche', quand: 'groupeReduit', libelle: "nous ne sommes qu'une poignée — je pars retrouver le gros" },
    { de: '*', vers: 'discute', quand: 'surLeCercle', libelle: 'me voilà sur le cercle de discussion' },
    { de: '*', vers: 'rejoint', quand: 'escouadeLoin', libelle: 'mon escouade est loin — je la rejoins' },
    { de: '*', vers: 'secarte', quand: 'escouadeTropPres', libelle: "trop au centre du groupe — je m'écarte" },
    { de: '*', vers: 'cherche', quand: 'seulAvecAttaches', libelle: 'je suis seul — je pars chercher les miens' },
    { de: '*', vers: 'flane', quand: 'seulSansAttaches', libelle: 'personne à retrouver — je flâne' },
  ],
};
