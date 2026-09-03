/**
 * 🖥️ Bulles — paroles éphémères au-dessus d'un corps : LA VIZ DU MODULE DE
 * COMMUNICATION À VENIR (📯 Transmission + ⚙️ acoustique/portee-voix). Chaque
 * parole physique (ordre crié, relais, rumeur) appellera dire() ; demain la
 * bulle pourra montrer sa portée (cercle acoustique). Vieillies au TEMPS
 * SIMULÉ : la pause les fige, x5 les accélère.
 */

/**
 * @param {{tempsSim: () => number}} deps — horloge sim (via transport ⏱️)
 */
export function creerBulles({ tempsSim }) {
  /** @type {{idCorps: number, texte: string, naissance: number, duree: number}[]} */
  let liste = [];

  return {
    /**
     * Fait parler un corps. @param {number} idCorps @param {string} texte
     * @param {number} [dureeS] — durée d'affichage en secondes sim
     */
    dire(idCorps, texte, dureeS = 3) {
      liste.push({ idCorps, texte, naissance: tempsSim(), duree: dureeS });
    },

    /**
     * Les bulles vivantes, avec leur progression [0..1] (pour le fondu).
     * Purge les expirées au passage.
     * @returns {{idCorps, texte, progression: number}[]}
     */
    actives() {
      const t = tempsSim();
      liste = liste.filter((b) => t - b.naissance < b.duree);
      return liste.map((b) => ({
        idCorps: b.idCorps,
        texte: b.texte,
        progression: (t - b.naissance) / b.duree,
      }));
    },
  };
}
