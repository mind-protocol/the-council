/**
 * 🧠 Doctrine / Manœuvres / Se reformer — sortir du désordre : l'unité est
 * dispersée, le chef rallie SA MEILLEURE LIGNE (posteChef) et y reforme les
 * rangs. C'est l'entrée qui transforme le grumeau d'après-choc en front —
 * accomplie, l'arbitre re-délibère (tenir, charger, harceler…).
 */

export const SE_REFORMER = {
  nom: 'se-reformer',
  applicabilite: ['uniteDispersee', 'ennemiEnMemoire'],
  posteChef: true, // le chef se porte au trou de la ligne, l'unité le suit

  /** Où cette manœuvre voudrait l'unité : le trou de la meilleure ligne. */
  geometrie(situation) {
    const ligne = situation.meilleureLigne();
    const depart = situation.positionUnite;
    if (!ligne || !depart) return null;
    return {
      chemin: [depart, ligne.centre],
      destination: ligne.centre,
      qualite: ligne.qualite, // → gainDePosition
    };
  },

  poids: { defense: 0.2, agression: 0.1 },

  phases: [
    { ordre: { verbe: 'EN_FORMATION', sur: { type: 'locuteur' } }, succes: 'uniteFormee', patience: 120 },
  ],
};
