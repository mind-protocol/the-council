/**
 * ⏱️ Orchestration / Pipeline — la liste ordonnée des phases d'un tick.
 * L'ordre est une décision d'archi, pas un accident.
 * Ordre actuel : perception (🧠) → decision (🧠) → action (🏃) →
 * physique (⚙️) → index (🌍, snapshot spatial de fin de tick).
 */

/** @typedef {{nom: string, executer: (dt: number) => void}} Phase */

/** @param {Phase[]} phases — injectées au bootstrap */
export function creerPipeline(phases) {
  return {
    /** Exécute toutes les phases dans l'ordre, pour UN pas de dt fixe. */
    executerTick(dt) {
      for (const phase of phases) phase.executer(dt);
    },
  };
}
