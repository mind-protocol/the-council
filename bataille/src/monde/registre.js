/**
 * 🌍 Monde / Registre des corps
 * L'annuaire des corps : qui existe, physiquement. Stocke et retrouve ;
 * ne décide rien, ne bouge rien. Voir CLAUDE.md : mutation en place,
 * ordre d'itération stable.
 */

/**
 * @typedef {{x: number, y: number}} Vec2 — mètres (monde), jamais des pixels
 *
 * @typedef {Object} Corps
 * @property {number} id      — unique, croissant, jamais réutilisé
 * @property {Vec2}   pos     — mètres
 * @property {Vec2}   vel     — m/s
 * @property {number} cap     — radians ; l'orientation, rendue VISIBLE par la
 *   lance (physicalisation) — écrite par l'Intégration (direction de la
 *   vitesse en mouvement, conservée à l'arrêt)
 * @property {number} rayon   — encombrement, mètres
 * @property {number} masse   — kg ; tirée en distribution au spawn — la
 *   poussée de masse (⚙️ choc) s'en dérive
 * @property {string} gabarit — 'homme' | 'cheval' | 'oiseau' : la silhouette
 *   SE VOIT (le rendu et la perception la lisent, jamais un type ailleurs)
 * @property {{z: number, vz: number, vitesseAir: number, banque: number,
 *   pente: number, phaseAile: number} | undefined} vol — OPTIONNEL : l'état
 *   de vol (absent = au sol). Une seule instance canonique par entité — pas
 *   d'entité parallèle. Écrit par l'Intégration (⚙️) comme pos/vel/cap.
 * @property {string} livree  — apparence observable : l'appartenance se VOIT
 * @property {string} nom     — on reconnaît les gens ; l'interprétation reste
 *   dans la 🧠 Cognition
 * @property {boolean} panache — ornement visible du chef (fait physique)
 * @property {string|null} personnage — OPTIONNEL : l'id de la fiche du jeu
 *   (`etat/personnages.json`) que ce corps incarne. C'est l'affectation d'un
 *   objet narratif à un objet physique, posée par le scénario ; le moteur ne
 *   la lit pas, il la porte — c'est par elle qu'un siège trouve son corps.
 */

export function creerRegistre() {
  /** @type {Map<number, Corps>} — Map préserve l'ordre d'insertion */
  const parId = new Map();
  let prochainId = 1;

  return {
    /**
     * Crée un corps. Appelé uniquement via l'expose (spawn).
     * @param {{pos: Vec2, rayon: number, livree: string, nom?: string, panache?: boolean}} desc
     * @returns {number} id du corps créé
     */
    ajouter({ pos, rayon, masse = 80, gabarit = 'homme', livree, nom = '', panache = false, cap = 0, posture = 'repos', vol, personnage = null }) {
      const id = prochainId++;
      parId.set(id, {
        id,
        pos: { x: pos.x, y: pos.y },
        vel: { x: 0, y: 0 },
        cap,
        posture,
        rayon,
        masse,
        gabarit,
        livree,
        nom,
        panache,
        personnage,
        // le vol : état complet dès le spawn (vitesseAir seedée par le scénario)
        ...(vol ? { vol: { z: vol.z, vz: 0, vitesseAir: vol.vitesseAir ?? 0, banque: 0, pente: 0, phaseAile: 0 } } : {}),
      });
      return id;
    },

    /** @param {number} id @returns {Corps | undefined} */
    obtenir(id) {
      return parId.get(id);
    },

    /** Tous les corps, ordre d'insertion (stable). @returns {Iterable<Corps>} */
    tous() {
      return parId.values();
    },

    // ── SE RELIRE (docs/sauvegarde.md) ────────────────────────────────────
    //
    // `prochainId` fait partie de l'état, et ce n'est pas un detail : un id
    // reattribue ferait qu'un ressuscite prendrait l'identite d'un mort, et
    // toutes les croyances qui le nomment (🧠 individus, mortsConnus,
    // attelages) designeraient quelqu'un d'autre.

    /** @returns {{prochainId: number, corps: Array<Corps>}} — donnee plate, copiee */
    etat() {
      return {
        prochainId,
        corps: [...parId.values()].map((c) => ({
          ...c,
          pos: { ...c.pos },
          vel: { ...c.vel },
          ...(c.vol ? { vol: { ...c.vol } } : {}),
        })),
      };
    },

    /** Remplace tout. Charger, c'est composer un monde neuf — jamais fusionner. */
    restaurer({ prochainId: pid, corps = [] } = {}) {
      parId.clear();
      for (const c of corps) {
        parId.set(c.id, {
          ...c,
          pos: { ...c.pos },
          vel: { ...c.vel },
          ...(c.vol ? { vol: { ...c.vol } } : {}),
        });
      }
      // Sans `prochainId` sauve (vieux fichier), on repart au-dessus du plus
      // grand id present : jamais en dessous, quoi qu'il arrive.
      const plancher = corps.reduce((m, c) => Math.max(m, c.id), 0) + 1;
      prochainId = Math.max(pid ?? 0, plancher);
    },
  };
}
