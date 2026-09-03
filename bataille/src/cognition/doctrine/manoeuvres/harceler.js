/**
 * 🧠 Doctrine / Manœuvres / Harceler — la doctrine de l'unité QUI TIRE :
 * se former, puis TENIR LA DISTANCE — chaque fois que l'ennemi approche
 * trop (`ennemiTropPres`), un bond de RECUL (relance) rouvre l'écart, front
 * au danger. Le tir n'est pas ordonné ici : la volée est l'affaire de chaque
 * homme (garde voleePossible) dès qu'une cible crue est à portée — la
 * manœuvre ne fait que garder l'unité DANS la fenêtre de tir, hors de
 * portée des lames. L'échec est le contact subi malgré tout.
 */

export const HARCELER = {
  nom: 'harceler',
  applicabilite: ['uniteTire', 'ennemiLocalise', 'uniteAvecMoi'],

  /** Où cette manœuvre voudrait l'unité : à distance de volée de l'ennemi. */
  geometrie(situation) {
    const depart = situation.positionUnite;
    const ennemi = situation.positionEnnemie;
    if (!depart || !ennemi) return null;
    const d = Math.hypot(ennemi.x - depart.x, ennemi.y - depart.y) || 1;
    const u = { x: (ennemi.x - depart.x) / d, y: (ennemi.y - depart.y) / d };
    const standoff = situation.distanceStandoff;
    const destination = { x: ennemi.x - u.x * standoff, y: ennemi.y - u.y * standoff };
    return { chemin: [depart, destination], destination };
  },

  // le harcèlement sert les deux postures — c'est l'ARME qui le désigne
  poids: { agression: 0.4, defense: 0.4 },

  phases: [
    { ordre: { verbe: 'EN_FORMATION', sur: { type: 'locuteur' } }, succes: 'uniteFormee', echec: 'auContact', patience: 60 },
    // sans fin : on tient la fenêtre de tir — le bond de recul à chaque
    // approche (relance), l'abandon si le fer arrive quand même
    { ordre: { verbe: 'RECULER' }, succes: 'jamais', echec: 'auContact', relance: 'ennemiTropPres' },
  ],
};
