/**
 * ❤️ Corps / Blessures — les coups reçus, COMPTÉS, et leurs conséquences
 * physiologiques : la vitesse diminue coup après coup (malus linéaire,
 * plancher), et au seuil, LA MORT — un CONSTAT de la physiologie, jamais
 * une écriture du Monde. Le cadavre reste sur le champ : sa manifestation
 * physique (posture 'gisant') part par la chaîne normale (🧠 émet le geste,
 * ⚙️ l'écrit) — la mort SE VOIT, elle ne se sait pas.
 * Un mort ne prend plus de coups (on ne compte pas l'acharnement).
 */

export function creerBlessures({ coupsMortels, malusVitesseParCoup, plancherVitesse }) {
  /** @type {Map<number, number>} — id → coups reçus */
  const coups = new Map();
  /** @type {Set<number>} */
  const morts = new Set();

  return {
    /** Un coup porté (par l'Acte 🏃) — la gravité compte (curée : x3). */
    subir(idCible, gravite = 1) {
      if (morts.has(idCible)) return;
      const n = (coups.get(idCible) ?? 0) + gravite;
      coups.set(idCible, n);
      if (n >= coupsMortels) morts.add(idCible);
    },

    /** SE RELIRE — les morts se sauvent A PART : un seuil de mortalite peut
     *  changer entre deux versions, un mort ne doit pas se relever pour autant. */
    etat() {
      return { coups: [...coups.entries()], morts: [...morts] };
    },

    restaurer({ coups: c = [], morts: m = [] } = {}) {
      coups.clear(); morts.clear();
      for (const [id, n] of c) coups.set(Number(id), n);
      for (const id of m) morts.add(Number(id));
    },

    /** @param {number} idCorps @returns {number} */
    de(idCorps) {
      return coups.get(idCorps) ?? 0;
    },

    /** @param {number} idCorps @returns {boolean} */
    estVivant(idCorps) {
      return !morts.has(idCorps);
    },

    /**
     * Le facteur de vitesse : 1 frais, réduit par coup, plancher — un blessé
     * boite, il ne s'arrête pas. Un mort ne va nulle part (0).
     * @param {number} idCorps @returns {number}
     */
    facteurVitesse(idCorps) {
      if (morts.has(idCorps)) return 0;
      return Math.max(plancherVitesse, 1 - malusVitesseParCoup * (coups.get(idCorps) ?? 0));
    },
  };
}
