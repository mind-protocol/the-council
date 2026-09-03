/**
 * 📯 Social / Unités — la vérité sociale : une unité formelle, son chef,
 * son ordre de drill et sa forme cible.
 * - `ordreDrill` : liste ordonnée des membres (chef en tête) — les HABITUDES
 *   rendues mécaniques : les habitués de l'avant en tête, le fond en queue.
 * - `forme` : donnée à vocabulaire OUVERT ({type: 'rangs', ...} aujourd'hui ;
 *   colonne, cercle, coin, tortue… demain). La doctrine (🧠) sait la lire.
 * La largeur adaptative à l'espace sera une décision du CHEF (future FSM
 * commandant), jamais des soldats.
 */

/**
 * @typedef {Object} Unite
 * @property {number} id
 * @property {string} nom
 * @property {number} chef — id du corps
 * @property {number[]} ordreDrill — ids, chef en tête
 * @property {Object} forme — ex. {type:'rangs', largeur, espacementLateral, espacementRang}
 */

export function creerUnites() {
  /** @type {Map<number, Unite>} */
  const parId = new Map();
  /** @type {Map<number, number>} — idCorps → idUnite */
  const parMembre = new Map();
  let prochainId = 1;

  return {
    /** @param {{nom, chef, ordreDrill, forme}} desc @returns {number} id */
    creer({ nom, chef, ordreDrill, forme }) {
      const id = prochainId++;
      parId.set(id, { id, nom, chef, ordreDrill: [...ordreDrill], forme: { ...forme } });
      for (const m of ordreDrill) parMembre.set(m, id);
      return id;
    },

    /** @param {number} id @returns {Unite | undefined} */
    obtenir(id) {
      return parId.get(id);
    },

    /** @param {number} idCorps @returns {Unite | undefined} */
    duMembre(idCorps) {
      const uid = parMembre.get(idCorps);
      return uid === undefined ? undefined : parId.get(uid);
    },
  };
}
