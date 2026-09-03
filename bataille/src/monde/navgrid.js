/**
 * 🌍 Monde / NavGrid
 * « Par où peut-on passer » — projection navigable du terrain, support de
 * l'A* (🏃 Action). Plan infini ⇒ rien de précalculé : cache local à la
 * demande, matérialisé sur la zone englobant départ/arrivée + marge.
 * Une case est libre si un agent (cercle) centré dessus ne chevauche rien.
 */

/**
 * @typedef {{x: number, y: number}} Vec2
 *
 * @typedef {Object} RegionNav
 * @property {number} colonnes
 * @property {number} lignes
 * @property {(i: number, j: number) => boolean} estLibre
 * @property {(pos: Vec2) => {i: number, j: number}} versCase
 * @property {(i: number, j: number) => Vec2} versMonde — centre de la case
 */

/**
 * @param {ReturnType<import('./terrain.js').creerTerrain>} terrain
 * @param {{tailleCase?: number, rayonAgent?: number, marge?: number, tailleJournal?: number}} [options]
 *   — tailleJournal : nombre d'évaluations gardées pour la viz (journal circulaire)
 */
export function creerNavgrid(terrain, { tailleCase = 0.5, rayonAgent = 0.35, marge = 10, tailleJournal = 400 } = {}) {
  /** @type {Map<string, RegionNav>} */
  const cache = new Map();

  // Journal circulaire des dernières évaluations (viz) : la recherche RÉCENTE,
  // pas le sédiment depuis le début — l'accumulation deviendrait du bruit.
  const journal = new Array(tailleJournal);
  let posJournal = 0;

  const caseEstLibre = (cx, cy) => !terrain.chevaucheObstacle({ x: cx, y: cy }, rayonAgent);

  function construireRegion(i0, j0, colonnes, lignes) {
    // mémo par case : 0 inconnu, 1 libre, 2 bloquée (calcul paresseux)
    const memo = new Uint8Array(colonnes * lignes);
    const versMonde = (i, j) => ({ x: (i0 + i + 0.5) * tailleCase, y: (j0 + j + 0.5) * tailleCase });
    return {
      i0,
      j0,
      colonnes,
      lignes,
      estLibre(i, j) {
        const k = j * colonnes + i;
        if (memo[k] === 0) {
          const c = versMonde(i, j);
          memo[k] = caseEstLibre(c.x, c.y) ? 1 : 2;
          journal[posJournal % tailleJournal] = {
            x: (i0 + i) * tailleCase,
            y: (j0 + j) * tailleCase,
            bloquee: memo[k] === 2,
          };
          posJournal++;
        }
        return memo[k] === 1;
      },
      versCase: (pos) => ({ i: Math.floor(pos.x / tailleCase) - i0, j: Math.floor(pos.y / tailleCase) - j0 }),
      versMonde,
      /**
       * Lecture PASSIVE du mémo (viz) : ne calcule jamais une case — le mémo
       * reste l'empreinte exacte de ce que l'A* a réellement évalué.
       * @returns {0 | 1 | 2} 0 inconnue, 1 libre, 2 bloquée
       */
      etatBrut(i, j) {
        return memo[j * colonnes + i];
      },
    };
  }

  return {
    /** Ce point est-il traversable ? @param {Vec2} pos @returns {boolean} */
    estLibre(pos) {
      return caseEstLibre(pos.x, pos.y);
    },

    /**
     * Matérialise (ou ressert du cache) la région couvrant départ et arrivée,
     * marge comprise. @param {Vec2} depart @param {Vec2} arrivee @returns {RegionNav}
     */
    regionPour(depart, arrivee) {
      // bornes QUANTIFIÉES (tuiles de 64 cases) : deux recherches voisines
      // tombent sur la MÊME région et partagent son mémo — sans quantum,
      // chaque paire départ/arrivée créait une région au mémo vierge et
      // tout re-interrogeait le terrain (dominait le profil à 630 hommes)
      const Q = 64;
      const q = (v, haut) => (haut ? Math.ceil(v / Q) * Q : Math.floor(v / Q) * Q);
      const i0 = q(Math.floor((Math.min(depart.x, arrivee.x) - marge) / tailleCase), false);
      const j0 = q(Math.floor((Math.min(depart.y, arrivee.y) - marge) / tailleCase), false);
      const i1 = q(Math.ceil((Math.max(depart.x, arrivee.x) + marge) / tailleCase), true);
      const j1 = q(Math.ceil((Math.max(depart.y, arrivee.y) + marge) / tailleCase), true);
      const cle = `${i0}|${j0}|${i1}|${j1}`;
      let region = cache.get(cle);
      if (!region) {
        region = construireRegion(i0, j0, i1 - i0, j1 - j0);
        cache.set(cle, region);
      }
      return region;
    },

    /**
     * VUE debug (calque navgrid, 🖥️) : les régions en cache, avec la taille
     * de case et l'état brut de chaque case — lecture passive uniquement.
     * @returns {Iterable<{i0, j0, colonnes, lignes, tailleCase, etat: (i, j) => 0|1|2}>}
     */
    regionsDebug() {
      return [...cache.values()].map((r) => ({
        i0: r.i0,
        j0: r.j0,
        colonnes: r.colonnes,
        lignes: r.lignes,
        tailleCase,
        etat: r.etatBrut,
      }));
    },

    /**
     * VUE debug (calque navgrid, 🖥️) : les N dernières cases évaluées,
     * de la plus ancienne à la plus récente (le calque fond par récence).
     * @returns {{tailleCase: number, cases: {x, y, bloquee: boolean}[]}}
     */
    evaluationsRecentes() {
      const n = Math.min(posJournal, tailleJournal);
      const cases = [];
      for (let k = posJournal - n; k < posJournal; k++) cases.push(journal[k % tailleJournal]);
      return { tailleCase, cases };
    },

    /** Le terrain a changé : jette le cache (appelée par l'expose). */
    invalider() {
      cache.clear();
      posJournal = 0;
    },
  };
}
