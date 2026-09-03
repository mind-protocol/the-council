/**
 * 🧠 Doctrine / Formes / Rangs — l'interprète de la forme 'rangs' : forme +
 * ordreDrill + monId → MON ancrage relationnel (« derrière X », « à droite
 * de Y »). Fonction PURE sur savoir partagé statique : tout le monde applique
 * le même drill, tout le monde est d'accord SANS calcul central.
 * Remplissage centre-vers-l'extérieur en alternance (centre, droite, gauche,
 * droite+2, gauche+2…). Un fichier par forme — le vocabulaire est ouvert.
 */

/**
 * @param {{largeur: number, espacementLateral: number, espacementRang: number}} forme
 * @param {number[]} ordreDrill — ids, chef en tête
 * @param {number} monId
 * @returns {{type: 'tenir'}
 *   | {type: 'flanc'|'derriere', ancreId: number, cote?: 1|-1,
 *      offset: {droite, avant}, offsetChef: {droite, avant}}}
 *   — offset : relatif à l'ANCRE ; offsetChef : mon slot complet relatif au
 *     CHEF (le « dressage » : on se règle sur son ancre ET sur l'alignement
 *     général, sinon l'erreur s'accumule le long de la chaîne).
 *   Les deux dans le repère de la formation (droite/avant du chef).
 */
export function ancrageRangs(forme, ordreDrill, monId) {
  const k = ordreDrill.indexOf(monId);
  if (k <= 0) return { type: 'tenir' }; // le chef EST l'origine

  const { largeur, espacementLateral, espacementRang } = forme;
  const rang = Math.floor(k / largeur);
  const p = k % largeur;
  const colonne = p === 0 ? 0 : p % 2 === 1 ? (p + 1) / 2 : -(p / 2);
  const offsetChef = { droite: colonne * espacementLateral, avant: -rang * espacementRang };

  if (rang === 0) {
    // premier rang : ancré latéralement — p=1,2 sur le chef, ensuite sur
    // le voisin du même côté (k-2)
    const cote = p % 2 === 1 ? 1 : -1;
    return {
      type: 'flanc',
      ancreId: ordreDrill[p <= 2 ? 0 : k - 2],
      cote,
      offset: { droite: cote * espacementLateral, avant: 0 },
      offsetChef,
    };
  }

  // rangs suivants : derrière l'homme devant moi (même colonne)
  return {
    type: 'derriere',
    ancreId: ordreDrill[k - largeur],
    offset: { droite: 0, avant: -espacementRang },
    offsetChef,
  };
}
