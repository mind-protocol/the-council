/**
 * 🌍 Monde — EXPOSE, seule porte d'entrée du container (règles : CLAUDE.md).
 * VUES (lecture) et COMMANDES (écriture : DEUX écrivains, pas un de plus —
 * la règle est mécanique, aucun autre moyen d'écrire n'existe).
 * Aucun import d'un autre container : câblage par injection au bootstrap.
 */

import { creerRegistre } from './registre.js';
import { creerTerrain } from './terrain.js';
import { creerTerrainMasque } from './terrain-masque.js';
import { creerNavgrid } from './navgrid.js';
import { creerIndexSpatial } from './index-spatial.js';

/** Changement de scénario : pas de reset — on jette et on refabrique. */
export function creerMonde({ tailleCaseIndex } = {}) {
  const registre = creerRegistre();
  const terrain = creerTerrain();
  const navgrid = creerNavgrid(terrain);
  const index = creerIndexSpatial({ tailleCase: tailleCaseIndex });
  /** L'ATTELAGE — un fait physique : QUI est en selle sur QUOI.
   * @type {Map<number, number>} cavalierId → montureId */
  const attelages = new Map();

  return {
    // ── VUES (lecture seule) ──

    /** Corps, ordre stable. Pour 🖥️ Rendu, ⚙️ Physique (voisinages). */
    corps() {
      return registre.tous();
    },

    /** @param {number} id */
    corpsParId(id) {
      return registre.obtenir(id);
    },

    /** La monture de ce corps (id), ou null. Pour ⚙️ (asservissement) et 🏃. */
    montureDe(id) {
      return attelages.get(id) ?? null;
    },

    /** Met en selle. Appelé au chargement (🖥️/bootstrap). */
    atteler(cavalierId, montureId) {
      attelages.set(cavalierId, montureId);
    },

    /** Vide la selle (monture morte, démonte). Appelé par ⚙️. */
    desatteler(cavalierId) {
      attelages.delete(cavalierId);
    },

    /**
     * Snapshot spatial du tick (voir index-spatial.js). Pour 🧠 Perception,
     * demain 📯 Transmission. @param {{x,y}} pos @param {number} rayon
     */
    voisinsDans(pos, rayon) {
      return index.voisinsDans(pos, rayon);
    },

    /** Le snapshot entier, à plat — pour l'horizon de masse partagé (🧠). */
    corpsVus() {
      return index.tous();
    },

    /** Requêtes obstacles. Pour ⚙️ Physique (murs), 🖥️ Rendu. */
    terrain: {
      obstacles: () => terrain.obstacles(),
      obstaclesPres: (pos, rayon) => terrain.obstaclesPres(pos, rayon),
      chevaucheObstacle: (c, r) => terrain.chevaucheObstacle(c, r),
      // VUE debug (calque terrain) : la vérité du masque dans un rectangle
      casesBloqueesDans: (rect) => terrain.casesBloqueesDans(rect),
    },

    /** Traversabilité et régions A*. Pour 🏃 Action (Pathfinding). */
    navgrid: {
      estLibre: (pos) => navgrid.estLibre(pos),
      regionPour: (a, b) => navgrid.regionPour(a, b),
    },

    /**
     * VUE debug pour le calque navgrid (🖥️) : contours des régions du cache
     * (lecture PASSIVE — la viz ne perturbe pas ce qu'elle observe) et les
     * dernières évaluations (journal circulaire, la recherche récente).
     */
    navgridDebug() {
      return {
        regions: navgrid.regionsDebug(),
        evaluations: navgrid.evaluationsRecentes(),
      };
    },

    /** VUE debug pour le calque index (🖥️) : cases occupées du snapshot. */
    indexDebug() {
      return index.casesDebug();
    },

    // ── COMMANDES (les deux seuls écrivains) ──

    /** ÉCRIVAIN 1/2 — ⚙️ Physique (Intégration), une fois par tick.
     *  `vol` (optionnel) : l'état de vol du corps volant, écrit tel quel. */
    appliquerIntegration(id, pos, vel, cap, posture, vol) {
      const c = registre.obtenir(id);
      if (!c) return;
      c.pos.x = pos.x;
      c.pos.y = pos.y;
      c.vel.x = vel.x;
      c.vel.y = vel.y;
      if (cap !== undefined) c.cap = cap;
      if (posture !== undefined) c.posture = posture;
      if (vol !== undefined && c.vol) Object.assign(c.vol, vol);
    },

    /**
     * ÉCRIVAIN 2/2 — 🖥️ Présentation (drag & drop) + chargement scénario.
     * Refuse un spawn qui chevauche un obstacle. @returns {number | null} id
     */
    spawn(desc) {
      if (terrain.chevaucheObstacle(desc.pos, desc.rayon)) return null;
      return registre.ajouter(desc);
    },

    // ── CONSTRUCTION / DÉRIVÉS (bootstrap, pipeline) ──

    /** Pose un obstacle du scénario ; invalide la navgrid. */
    poserObstacle(rect) {
      terrain.ajouterObstacle(rect);
      navgrid.invalider();
    },

    /**
     * Pose le masque d'une ville cuite (chargé au bootstrap — le fichier
     * reste dans son dépôt d'origine, décision actée) ; invalide la navgrid.
     * @param {{nx, ny, pas, bits, inverserY}} desc — voir terrain-masque.js
     */
    poserMasque(desc) {
      terrain.ajouterMasque(creerTerrainMasque(desc));
      navgrid.invalider();
    },




    /**
     * Reprend le snapshot spatial. Appelée par la phase « index » du
     * pipeline (fin de tick) et une fois au chargement. Donnée dérivée —
     * la règle des deux écrivains n'est pas concernée.
     */
    // ── SE RELIRE (docs/sauvegarde.md) ────────────────────────────────────
    //
    // Ne sort QUE ce qui ne se recalcule pas. Le terrain n'est pas la : les
    // obstacles et le masque viennent du scenario/de la partie et sont
    // immuables — on garde leur NOM ailleurs, pas leurs bits. La navgrid et
    // l'index sont derives ; ils se rebatissent en une frame.

    /** @returns {{registre, attelages: Array<[number, number]>}} */
    etat() {
      return {
        registre: registre.etat(),
        attelages: [...attelages.entries()],
      };
    },

    /**
     * Reprend un monde sauve. Le terrain doit DEJA etre pose (obstacles,
     * masque) : on restaure des corps dans un sol, pas un sol.
     */
    restaurer({ registre: r, attelages: att = [] } = {}) {
      registre.restaurer(r);
      attelages.clear();
      for (const [cavalier, monture] of att) attelages.set(cavalier, monture);
      navgrid.invalider();       // le sol n'a pas bouge, mais le cache si
      index.reconstruire(registre.tous());
    },

    reconstruireIndex() {
      // TOUS les corps, le ciel compris — un seul canal canonique : ce sont
      // les distances VRAIES (3D, le snapshot porte z) qui font qu'un corps
      // en vol n'est jamais « à côté » de personne
      index.reconstruire(registre.tous());
    },
  };
}
