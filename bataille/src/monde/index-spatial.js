/**
 * 🌍 Monde / Index spatial — « qui est où » : grille de hachage sur plan
 * infini (seules les cases occupées existent). SÉMANTIQUE DE SNAPSHOT :
 * reconstruit une fois par tick (phase index, après l'Intégration) avec des
 * COPIES des positions — pendant tout le tick suivant, toutes les requêtes
 * voient la même photo figée. Résultats en ordre stable (tri par id) :
 * le déterminisme en dépend.
 */

/** @param {{tailleCase?: number}} [options] */
export function creerIndexSpatial({ tailleCase = 2 } = {}) {
  /** @type {Map<string, {id, pos: {x,y}, livree}[]>} */
  let grille = new Map();
  /** le snapshot À PLAT (mêmes objets que la grille) : les requêtes à grand
   * rayon (horizon de masse, 200 m) coûtent moins en balayant les corps
   * qu'en visitant des dizaines de milliers de cellules */
  let plat = [];

  return {
    /** Reprend la photo : appelé une fois par tick. @param {Iterable} tousCorps */
    reconstruire(tousCorps) {
      grille = new Map();
      plat = [];
      for (const c of tousCorps) {
        const k = `${Math.floor(c.pos.x / tailleCase)}|${Math.floor(c.pos.y / tailleCase)}`;
        let case_ = grille.get(k);
        if (!case_) grille.set(k, (case_ = []));
        case_.push({
          id: c.id,
          pos: { x: c.pos.x, y: c.pos.y },
          cap: c.cap,
          posture: c.posture,
          livree: c.livree,
          // des FAITS qui se voient : le gabarit (un cheval est plus gros
          // qu'un homme, un oiseau leger), l'altitude (un corps en vol est
          // LÀ-HAUT), l'allure (le mouvement se voit, sa vitesse aussi)
          rayon: c.rayon,
          z: c.vol?.z ?? 0,
          vitesse: Math.hypot(c.vel.x, c.vel.y),
          // ça se VOIT, qu'un homme marche — la forme d'un groupe se lit
          // sur ceux qui sont plantés (🧠 forme-tas)
          enMouvement: Math.hypot(c.vel.x, c.vel.y) > 0.3,
        });
        plat.push(case_[case_.length - 1]);
      }
    },

    /**
     * TOUT le snapshot, à plat, dans l'ordre de reconstruction — les mêmes
     * fiches que voisinsDans (z, vitesse, enMouvement aplatis). Pour
     * l'horizon de masse partagé (🧠 percevoir.js), qui regroupe le monde
     * une fois pour tous.
     * @returns {{id, pos: {x,y}, livree, z, vitesse}[]}
     */
    tous() {
      return plat;
    },

    /**
     * Les corps (snapshot) à distance ≤ rayon, triés par id.
     * @param {{x,y}} pos @param {number} rayon
     * @returns {{id, pos: {x,y}, livree}[]}
     */
    voisinsDans(pos, rayon) {
      const r2 = rayon * rayon;
      const zRequete = pos.z ?? 0;
      const resultat = [];
      const cx0 = Math.floor((pos.x - rayon) / tailleCase);
      const cx1 = Math.floor((pos.x + rayon) / tailleCase);
      const cy0 = Math.floor((pos.y - rayon) / tailleCase);
      const cy1 = Math.floor((pos.y + rayon) / tailleCase);
      // grand rayon (horizon de masse ~200 m) : la fenêtre de cellules dépasse
      // l'effectif — le balayage à plat coûte moins, même résultat, même tri
      if ((cx1 - cx0 + 1) * (cy1 - cy0 + 1) > plat.length) {
        for (const s of plat) {
          const dx = s.pos.x - pos.x, dy = s.pos.y - pos.y, dz = s.z - zRequete;
          if (dx * dx + dy * dy + dz * dz <= r2) resultat.push(s);
        }
        resultat.sort((a, b) => a.id - b.id);
        return resultat;
      }
      for (let cx = cx0; cx <= cx1; cx++) {
        for (let cy = cy0; cy <= cy1; cy++) {
          const case_ = grille.get(`${cx}|${cy}`);
          if (!case_) continue;
          for (const s of case_) {
            // la distance est VRAIE (3D) : un corps à 175 m d'altitude n'est
            // pas « à côté » — au sol (z partout nul), rien ne change
            const dx = s.pos.x - pos.x, dy = s.pos.y - pos.y, dz = s.z - zRequete;
            if (dx * dx + dy * dy + dz * dz <= r2) resultat.push(s);
          }
        }
      }
      resultat.sort((a, b) => a.id - b.id);
      return resultat;
    },

    /**
     * VUE debug (calque index, 🖥️) : les cases occupées du snapshot et leur
     * effectif, en ordre stable (tri cx puis cy — déterminisme).
     * @returns {{tailleCase: number, cases: {cx: number, cy: number, n: number}[]}}
     */
    casesDebug() {
      const cases = [...grille.entries()].map(([k, corps]) => {
        const [cx, cy] = k.split('|').map(Number);
        return { cx, cy, n: corps.length };
      });
      cases.sort((a, b) => a.cx - b.cx || a.cy - b.cy);
      return { tailleCase, cases };
    },
  };
}
