/**
 * ⏱️ Orchestration / Horloge — le temps simulé. dt FIXE ; pause ;
 * multiplicateur x1/x2/x5 = nombre de pas par frame, JAMAIS la taille du pas
 * (physique identique à toutes les vitesses).
 */

/** @param {{dtFixe?: number}} [options] — dt en secondes sim, défaut 1/60 */
export function creerHorloge({ dtFixe = 1 / 60 } = {}) {
  let accumMs = 0;
  let enPause = false;
  let vitesse = 1;
  let tempsSim = 0;
  const PLAFOND_ACCUM_MS = 500; // borne anti-spirale (onglet endormi)

  return {
    /**
     * Convertit du temps réel écoulé en nombre de pas fixes à exécuter.
     * 0 si en pause. @param {number} msReelles @returns {number}
     */
    pasAExecuter(msReelles) {
      if (enPause) return 0;
      accumMs = Math.min(accumMs + msReelles * vitesse, PLAFOND_ACCUM_MS);
      const pasMs = dtFixe * 1000;
      const n = Math.floor(accumMs / pasMs);
      accumMs -= n * pasMs;
      tempsSim += n * dtFixe;
      return n;
    },

    basculerPause() {
      enPause = !enPause;
      if (!enPause) accumMs = 0; // repartir propre, pas rattraper la pause
    },

    /** @param {1|2|5} mult */
    reglerVitesse(mult) {
      vitesse = mult;
    },

    /** @returns {{enPause: boolean, vitesse: number, dtFixe: number, tempsSim: number, accumMs: number}} */
    etat() {
      return { enPause, vitesse, dtFixe, tempsSim, accumMs };
    },

    /**
     * SE RELIRE. `accumMs` est le poste qui compte, et c'est le moins evident :
     * c'est le reste de temps reel pas encore converti en pas fixes. Un monde
     * repris avec accumMs a 0 n'execute PAS le meme nombre de pas a la
     * premiere frame que celui qu'on a quitte — et tout diverge des la, avant
     * meme que le hasard s'en mele. `dtFixe` ne se restaure pas : il est une
     * propriete de la sim, pas de la partie.
     */
    restaurer(d) {
      if (!d) return;
      if (typeof d.tempsSim === 'number') tempsSim = d.tempsSim;
      if (typeof d.accumMs === 'number') accumMs = d.accumMs;
      if (typeof d.vitesse === 'number') vitesse = d.vitesse;
      if (typeof d.enPause === 'boolean') enPause = d.enPause;
    },
  };
}
