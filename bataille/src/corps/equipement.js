/**
 * ❤️ Corps / Équipement — le paquetage de chaque homme : UNE arme (du
 * catalogue armes.js) et parfois un bouclier. Seedé par le scénario au
 * spawn (par unité) ; la lance d'ordonnance par défaut (l'homme droppé).
 * La vue rendue (`de`) porte les chiffres de silhouette : le rendu 🖥️
 * dessine des longueurs, jamais des types.
 */

import { ARMES, BOUCLIER, ARC_DE_TIR } from './armes.js';

export function creerEquipement() {
  /** @type {Map<number, {arme: string, bouclier: boolean}>} */
  const parCorps = new Map();

  return {
    /**
     * Enregistre un homme avec son paquetage.
     * @param {number} idCorps @param {{arme?: string, bouclier?: boolean}} [paquetage]
     */
    enregistrer(idCorps, paquetage = {}) {
      const arme = paquetage.arme ?? 'lance';
      if (!ARMES[arme]) throw new Error(`equipement : arme inconnue '${arme}'`);
      parCorps.set(idCorps, { arme, bouclier: !!paquetage.bouclier, arc: !!paquetage.arc });
    },

    /** L'arme portée (l'entrée du catalogue). @param {number} idCorps */
    armeDe(idCorps) {
      return ARMES[parCorps.get(idCorps)?.arme ?? 'lance'];
    },

    /**
     * Le bouclier porté, avec son fait physique (l'arc paré), ou null.
     * @param {number} idCorps @returns {{arcCouverture: number}|null}
     */
    bouclierDe(idCorps) {
      return parCorps.get(idCorps)?.bouclier
        ? { arcCouverture: BOUCLIER.arcCouverture, coutParadeS: BOUCLIER.coutParadeS }
        : null;
    },

    /** L'arc de tir porté (le projecteur de zone), ou null. */
    arcTirDe(idCorps) {
      return parCorps.get(idCorps)?.arc ? ARC_DE_TIR : null;
    },

    /**
     * La vue RENDUE (🖥️) : le nom, la silhouette, le bouclier — des chiffres,
     * pas des types. @param {number} idCorps
     */
    /** SE RELIRE — les CLES du paquetage, jamais les profils d'armes (du parametre). */
    etat() {
      return [...parCorps.entries()].map(([id, p]) => [id, { ...p }]);
    },

    restaurer(liste = []) {
      parCorps.clear();
      for (const [id, p] of liste) parCorps.set(Number(id), { ...p });
    },

    /** @param {number} idCorps */
    de(idCorps) {
      const p = parCorps.get(idCorps);
      if (!p) return null;
      const arme = ARMES[p.arme];
      return {
        arme: p.arme,
        longueurRendue: arme.longueurRendue,
        bouclier: p.bouclier ? { rayonRendu: BOUCLIER.rayonRendu } : null,
        arc: !!p.arc, // l'arbalete se voit : un arc en travers de la main
      };
    },
  };
}
