/**
 * 🧠 Compétences / Chercher — UNE implémentation : retrouver quelqu'un sur
 * des CROYANCES périmées, la cible étant la plus IMPORTANTE selon une liste
 * de priorités (une donnée, par rôle) — la fraîcheur ne départage qu'à rang
 * égal. Un rang sans croyance passe au suivant ; les rangs futurs (autre
 * unité, autre commandant, n'importe quel allié) sont déclarés et
 * s'activeront quand la Représentation portera ces croyances.
 * Une piste vérifiée-et-vide est mémorisée (sinon on orbite un fantôme) et
 * redevient candidate si la croyance bouge. Sans aucune piste : exploration
 * — même geste que flâner, mais l'ÉTAT diffère : c'est ici que les pistes
 * futures (direction d'une voix entendue, lieux nommés) se brancheront.
 * Fabrique STATEFULE (pistes vérifiées) au contrat commun :
 * (ctx) → {intention, objectifHumain, cible}.
 */

import { allerA } from '../intentions.js';

/** Qui chercher, du plus au moins important — par RÔLE. Pure donnée. */
export const PRIORITES_TROUPIER = ['escouade', 'chef', 'unite', 'autreUnite', 'allie'];
export const PRIORITES_COMMANDANT = ['unite', 'hommes', 'chef', 'autreCommandant', 'allie'];

/** Y a-t-il quelqu'un À connaître ? (identités seedées, pas positions). PUR. */
export function connaitQuelquun(representation) {
  const ctx = representation.contextePerception();
  return ctx.suivis.length > 0 || ctx.amisIds.size > 0 || ctx.uniteIds.size > 0;
}

/** Les pistes d'un rang : chaque résolveur lit la Représentation, rien d'autre. */
const RESOLVEURS = {
  escouade(r) {
    const tas = r.tasCru('escouade');
    return tas?.barycentre ? [{ cle: 'tescouade', pos: tas.barycentre, ageS: tas.ageS, nom: 'mon escouade' }] : [];
  },
  chef(r) {
    if (r.chefId == null || r.chefId === r.monId) return [];
    const cru = r.individuCru(r.chefId);
    return cru?.pos ? [{ cle: `i${r.chefId}`, pos: cru.pos, ageS: cru.ageS, nom: r.nomDe(r.chefId) }] : [];
  },
  unite(r) {
    const tas = r.tasCru('unite');
    return tas?.barycentre ? [{ cle: 'tunite', pos: tas.barycentre, ageS: tas.ageS, nom: 'mon unité' }] : [];
  },
  hommes(r) {
    const { uniteIds } = r.contextePerception();
    const pistes = [];
    for (const id of uniteIds) {
      const cru = r.individuCru(id);
      if (cru?.pos) pistes.push({ cle: `i${id}`, pos: cru.pos, ageS: cru.ageS, nom: r.nomDe(id) });
    }
    return pistes;
  },
  // Croyances à venir (tas anonymes suivis, unités alliées repérées) : rangs
  // déclarés, résolveurs vides — ils s'activeront sans toucher à la cascade.
  autreUnite: () => [],
  autreCommandant: () => [],
  allie: () => [],
};

/**
 * @param {Object} deps
 * @param {ReturnType<import('../representation.js').creerRepresentation>} deps.representation
 * @param {Object} deps.rng
 * @param {{x, y, largeur, hauteur}} deps.zone
 * @param {Object} deps.params
 * @param {string[]} deps.priorites — PRIORITES_TROUPIER ou PRIORITES_COMMANDANT
 */
export function creerChercher({ representation, rng, zone, params, priorites }) {
  /** @type {Map<string, {x, y}>} — pistes vérifiées vides (cle → pos visitée) */
  const verifiees = new Map();

  const dejaVerifiee = (piste) => {
    const v = verifiees.get(piste.cle);
    return v && Math.hypot(v.x - piste.pos.x, v.y - piste.pos.y) < 0.5; // la croyance n'a pas bougé
  };

  /** La meilleure piste : premier RANG servi ; la fraîcheur départage dedans. */
  const meilleurePiste = () => {
    for (const rang of priorites) {
      let choix = null;
      for (const piste of RESOLVEURS[rang](representation)) {
        if (dejaVerifiee(piste)) continue;
        if (!choix || piste.ageS < choix.ageS) choix = piste;
      }
      if (choix) return choix;
    }
    return null;
  };

  return {
    /** @returns {{intention, objectifHumain, cible}} */
    chercher() {
      const moi = representation.moi;
      for (;;) {
        const piste = meilleurePiste();
        if (!piste) {
          const cible = {
            x: rng.entre(zone.x, zone.x + zone.largeur),
            y: rng.entre(zone.y, zone.y + zone.hauteur),
          };
          return { intention: allerA(cible), objectifHumain: 'chercher les miens (aucune piste)', cible };
        }
        // arrivé sur la piste et toujours rien : vérifiée, vide — la suivante
        if (moi.pos && Math.hypot(moi.pos.x - piste.pos.x, moi.pos.y - piste.pos.y) < params.chercher.rayonVisite) {
          verifiees.set(piste.cle, { x: piste.pos.x, y: piste.pos.y });
          continue;
        }
        const fraicheur = piste.ageS < 1 ? '' : ` (vu il y a ${Math.round(piste.ageS)} s)`;
        return {
          intention: allerA(piste.pos),
          objectifHumain: `chercher ${piste.nom}${fraicheur}`,
          cible: piste.pos,
        };
      }
    },
  };
}
