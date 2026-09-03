/**
 * 🧠 Compétences / Charger — sus à l'ennemi. La cible se résout contre MES
 * croyances : le tas ennemi cru d'abord (chacun court sur ce QU'IL croit,
 * pas sur un point d'état-major), la direction criée sinon (l'élan), et
 * faute de tout : on se tient prêt — on ne charge pas le brouillard.
 * L'allure est pleine ; le sprint viendra du ❤️ Corps. Le contact n'est pas
 * l'affaire de cette compétence : la machine bascule en tuer avant.
 */

import { allerA, attendre } from '../intentions.js';
import { capDeDirection } from '../langage/resoudre-lieu.js';

/** Contrat commun : (ctx) → {intention, objectifHumain, cible}. */
export function charger(ctx) {
  const r = ctx.representation;
  const ennemis = r.tasCru('ennemis');
  // une croyance PÉRIMÉE ne se charge pas : au-delà de la fraîcheur, on
  // retombe sur la direction criée (sinon on fonce sur un souvenir — ou un
  // charnier : ceux qu'on a vus là sont peut-être morts depuis)
  if (ennemis?.barycentre && ennemis.ageS < ctx.params.commandement.fraicheurEnnemi) {
    const cible = { ...ennemis.barycentre };
    // monté, la charge se donne AU GALOP — à pied le mot est ignoré
    return { intention: allerA(cible, 1, 'galop'), objectifHumain: "charger l'ennemi", cible };
  }
  const recu = r.ordre();
  const cap = recu?.ordre.vers?.nom != null ? capDeDirection(recu.ordre.vers.nom) : null;
  if (cap !== null && r.moi.pos) {
    const elan = ctx.params.charge.elan;
    const cible = { x: r.moi.pos.x + Math.cos(cap) * elan, y: r.moi.pos.y + Math.sin(cap) * elan };
    return { intention: allerA(cible, 1, 'galop'), objectifHumain: `charger vers le ${recu.ordre.vers.nom}`, cible };
  }
  return { intention: attendre(), objectifHumain: 'prêt à charger — je ne vois pas l’ennemi', cible: null };
}
