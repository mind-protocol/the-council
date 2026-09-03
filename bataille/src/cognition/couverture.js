/**
 * 🧠 Cognition / Couverture — la carte cognitive du « OÙ J'AI REGARDÉ » :
 * une croyance SPATIALE (grille grossière ~8 m), tamponnée par MA perception
 * (le disque de visibilité — pas celle des camarades : le partage viendra
 * avec la Transmission 📯), vieillie comme toute croyance (une case
 * redevient vierge après péremption). Fait partie de la Représentation.
 * Deux consommateurs : ratisser (délibéré, commandant) et chercher
 * (fallback individuel).
 */

/** @param {{tailleCase?: number, peremptionS?: number}} [options] */
export function creerCouverture({ tailleCase = 8, peremptionS = 120 } = {}) {
  /** @type {Map<string, {cx: number, cy: number, vuA: number}>} — vuA : l'heure du dernier regard */
  const cases = new Map();
  const cle = (cx, cy) => `${cx}|${cy}`;

  let tempsS = 0; // l'horloge interne (pour les caches de croyance)
  // L'ÂGE SE CALCULE, IL NE SE COMPTE PAS : chaque case porte l'heure où on
  // l'a vue, et son âge est une soustraction à la lecture. Vieillir toutes
  // les cases de tous les hommes à chaque tick coûtait 15 % de la colonne de
  // Gallipoli (427 corps, mesuré au profil) ; la purge des périmées se fait
  // par rondes, une toutes les dix secondes.
  const ageDe = (c) => tempsS - c.vuA;
  const fraiche = (c) => c !== undefined && ageDe(c) < peremptionS;
  let prochainePurge = 10;
  /** @type {{zoneCle: string, tempsS: number, valeur: number}|null} */
  let cachePart = null;

  const bornesDeZone = (zone) => ({
    cx0: Math.floor(zone.x / tailleCase),
    cx1: Math.floor((zone.x + zone.largeur - 1e-9) / tailleCase),
    cy0: Math.floor(zone.y / tailleCase),
    cy1: Math.floor((zone.y + zone.hauteur - 1e-9) / tailleCase),
  });

  return {
    /** Ma perception vient de balayer ce disque. */
    tamponner(pos, rayon) {
      const cx0 = Math.floor((pos.x - rayon) / tailleCase);
      const cx1 = Math.floor((pos.x + rayon) / tailleCase);
      const cy0 = Math.floor((pos.y - rayon) / tailleCase);
      const cy1 = Math.floor((pos.y + rayon) / tailleCase);
      for (let cx = cx0; cx <= cx1; cx++) {
        for (let cy = cy0; cy <= cy1; cy++) {
          // le centre de la case doit être dans le disque (pas juste l'effleurer)
          const dx = (cx + 0.5) * tailleCase - pos.x;
          const dy = (cy + 0.5) * tailleCase - pos.y;
          if (dx * dx + dy * dy <= rayon * rayon) cases.set(cle(cx, cy), { cx, cy, vuA: tempsS });
        }
      }
    },

    /** Le temps passe ; les cases périmées redeviennent vierges. */
    vieillir(dt) {
      tempsS += dt;
      if (tempsS < prochainePurge) return;
      prochainePurge = tempsS + 10;
      for (const [k, c] of cases) if (ageDe(c) >= peremptionS) cases.delete(k);
    },

    /** Ce point a-t-il été vu récemment ? */
    estCouverte(pos) {
      return fraiche(cases.get(cle(Math.floor(pos.x / tailleCase), Math.floor(pos.y / tailleCase))));
    },

    /**
     * Part de la zone jamais/anciennement vue, 0..1. CACHÉE ~1 s (une
     * croyance, pas un capteur — 27 états-majors sur un théâtre de 10 km²
     * balayaient 159 000 cases à chaque estimation), sans allocation.
     */
    partInconnue(zone) {
      const zoneCle = `${zone.x}|${zone.y}|${zone.largeur}|${zone.hauteur}`;
      if (cachePart && cachePart.zoneCle === zoneCle && tempsS - cachePart.tempsS < 2.5) {
        return cachePart.valeur;
      }
      const { cx0, cx1, cy0, cy1 } = bornesDeZone(zone);
      let total = 0;
      let vierges = 0;
      for (let cx = cx0; cx <= cx1; cx++) {
        for (let cy = cy0; cy <= cy1; cy++) {
          total++;
          if (!fraiche(cases.get(cle(cx, cy)))) vierges++;
        }
      }
      const valeur = total > 0 ? vierges / total : 0;
      cachePart = { zoneCle, tempsS, valeur };
      return valeur;
    },

    /**
     * Le centre du secteur vierge le plus proche, ou null si tout est couvert.
     * @param {{cap: number, poids: number}|null} [biais] — une PRÉFÉRENCE de
     *   direction (rumeur « ils sont à l'est ») : score = distance − poids ×
     *   projection dans le cap — continue, jamais un interdit.
     */
    prochainSecteurVierge(depuis, zone, biais = null) {
      const u = biais ? { x: Math.cos(biais.cap), y: Math.sin(biais.cap) } : null;
      const { cx0, cx1, cy0, cy1 } = bornesDeZone(zone);
      let choix = null;
      let scoreMin = Infinity;
      for (let cx = cx0; cx <= cx1; cx++) {
        for (let cy = cy0; cy <= cy1; cy++) {
          if (fraiche(cases.get(cle(cx, cy)))) continue;
          const x = (cx + 0.5) * tailleCase;
          const y = (cy + 0.5) * tailleCase;
          const d = Math.hypot(x - depuis.x, y - depuis.y);
          const proj = u ? (x - depuis.x) * u.x + (y - depuis.y) * u.y : 0;
          const score = d - (biais?.poids ?? 0) * proj;
          if (score < scoreMin) {
            scoreMin = score;
            choix = { x, y };
          }
        }
      }
      return choix;
    },

    /** Pour le calque couverture (🖥️) : les cases vues et leur fraîcheur. */
    casesDebug() {
      return { tailleCase, peremptionS, cases: [...cases.values()].map((c) => ({ cx: c.cx, cy: c.cy, ageS: ageDe(c) })) };
    },

    /**
     * SE RELIRE — ou j'ai regarde, et depuis quand. `cachePart` est derive.
     * @param {{depuis?: number}} [opts] — ne rendre que les cases plus
     *   fraiches que `depuis` secondes. C'est la DECIMATION : un homme du
     *   rang ne se sert de cette carte que pour ne pas re-scruter l'angle
     *   qu'il vient de faire (le fallback « chercher »), et cette memoire-la
     *   se refait toute seule en quelques secondes de regard. Le commandant,
     *   lui, RATISSE : sa carte longue est son outil de travail, elle sort
     *   entiere. Voir docs/sauvegarde.md.
     */
    etat({ depuis = Infinity } = {}) {
      const gardees = [...cases.values()].filter((c) => ageDe(c) < depuis);
      return { tempsS, cases: gardees.map((c) => ({ cx: c.cx, cy: c.cy, ageS: ageDe(c) })) }; // le format relu reste en âges
    },

    restaurer({ tempsS: t = 0, cases: liste = [] } = {}) {
      cases.clear();
      tempsS = t;
      for (const c of liste) cases.set(cle(c.cx, c.cy), { cx: c.cx, cy: c.cy, vuA: c.vuA ?? tempsS - (c.ageS ?? 0) });
      prochainePurge = tempsS + 10;
      cachePart = null;
    },
  };
}
