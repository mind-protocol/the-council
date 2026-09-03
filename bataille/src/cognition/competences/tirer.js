/**
 * 🧠 Compétences / Tirer — la VOLÉE : faire pleuvoir sur la ZONE où l'on
 * croit l'ennemi (le barycentre cru du tas adverse — pas un homme, un
 * rectangle de sol). Les prédicats sont purs et partagés avec les gardes :
 * on tire si l'on a un arc, des flèches, une cible crue dans la fourchette
 * de portée, et PERSONNE au contact de soi — c'est le contact qui fait
 * lâcher l'arc, jamais une distance : on tire très bien sur un homme à 3 m.
 */

import { attendre, tirer as intentionTirer } from '../intentions.js';
import { ennemiAuContact } from './combattre.js';

/** Le tas adverse CRU et frais (livrée opposée), ou null. PUR. */
function tasAdverse(representation, params) {
  // le tas identifié 'ennemis' d'abord ; 'inconnu' en repli (pas encore interprété)
  const t = representation.tasCru('ennemis') ?? representation.tasCru('inconnu');
  if (!t || !t.livree || !representation.maLivree || t.livree === representation.maLivree) return null;
  if (t.ageS >= params.menace.fraicheurS * 3) return null; // la volée tolère une croyance un peu vieille
  return t;
}

/** Peut-on donner la volée ? PUR (ctx : arc(), fleches(), representation). */
export function voleePossible(ctx) {
  const arc = ctx.arc?.();
  if (!arc || (ctx.fleches?.() ?? 0) <= 0) return false;
  if (ennemiAuContact(ctx.representation, ctx.params)) return false;
  const tas = tasAdverse(ctx.representation, ctx.params);
  if (!tas || !ctx.representation.moi.pos) return false;
  const d = Math.hypot(
    ctx.representation.moi.pos.x - tas.barycentre.x,
    ctx.representation.moi.pos.y - tas.barycentre.y
  );
  return d <= arc.porteeMax;
}

/** Le verbe : nocker, viser la zone crue, lâcher. */
export function tirer(ctx) {
  const tas = tasAdverse(ctx.representation, ctx.params);
  const moi = ctx.representation.moi;
  if (!tas || !moi.pos) {
    return { intention: attendre(), objectifHumain: 'plus de cible sous la volée', cible: null };
  }
  const d = Math.hypot(moi.pos.x - tas.barycentre.x, moi.pos.y - tas.barycentre.y);
  return {
    intention: intentionTirer(tas.barycentre),
    objectifHumain: `faire pleuvoir sur une unité ${tas.livree} (à ${Math.round(d)} m)`,
    cible: tas.barycentre,
  };
}
