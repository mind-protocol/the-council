/**
 * ❤️ Corps / Carquois — LES FLÈCHES SE COMPTENT : le tir est une ressource
 * qu'on dépense, jamais un régime (docs/recherche/le-tir.md). LE FREESTYLE
 * N'EXISTE PAS — c'est le SCÉNARIO qui décide de l'abondance (une botte fait
 * 24 flèches ; un stock à demeure sur un rempart, des charrettes en campagne,
 * rien du tout en rase campagne). Le carquois vide est un ÉVÉNEMENT : l'acte
 * refuse, la machine bascule — « plus une flèche, au couteau ! ».
 */

export function creerCarquois() {
  /** @type {Map<number, number>} — id → flèches restantes */
  const fleches = new Map();

  return {
    /** Au spawn : la dotation du scénario. @param {number} idCorps @param {number} n */
    enregistrer(idCorps, n) {
      fleches.set(idCorps, n);
    },

    /** Puise une flèche. @returns {boolean} — false : carquois vide, l'acte refuse */
    puiser(idCorps) {
      const n = fleches.get(idCorps) ?? 0;
      if (n <= 0) return false;
      fleches.set(idCorps, n - 1);
      return true;
    },

    /** SE RELIRE — ce qui reste au carquois. */
    etat() {
      return [...fleches.entries()];
    },

    restaurer(liste = []) {
      fleches.clear();
      for (const [id, n] of liste) fleches.set(Number(id), n);
    },

    /** @param {number} idCorps @returns {number} */
    de(idCorps) {
      return fleches.get(idCorps) ?? 0;
    },
  };
}
