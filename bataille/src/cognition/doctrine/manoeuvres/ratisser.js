/**
 * 🧠 Doctrine / Manœuvres / Ratisser — la première entrée du livre : balayer
 * la zone en formation, secteur par secteur, jusqu'à trouver l'ennemi
 * (contactSubi INTERROMPT — c'est un succès de la chasse, pas de la manœuvre)
 * ou conclure bredouille (« Repos ! », croyance infirmée). Le serpentin
 * n'est écrit nulle part : il émerge de « toujours le vierge le plus proche ».
 * Gagne mécaniquement quand l'ennemi n'est PAS localisé (gainInformation).
 */

export const RATISSER = {
  nom: 'ratisser',
  applicabilite: ['ennemiEnMemoire', 'ennemiNonLocalise', 'uniteAvecMoi', 'partInconnueRestante'],

  /**
   * Où cette manœuvre enverrait l'unité : le prochain secteur vierge,
   * depuis la position crue de l'unité. @param {Object} situation
   */
  geometrie(situation) {
    const depart = situation.positionUnite;
    const destination = situation.prochainSecteurVierge();
    if (!depart || !destination) return null;
    return { chemin: [depart, destination], destination };
  },

  poids: {}, // pas de biais de posture propres : les axes suffisent

  phases: [
    { ordre: { verbe: 'EN_FORMATION' }, succes: 'uniteFormee', echec: 'contactSubi', patience: 90 },
    // ré-émise tant qu'il reste du vierge : le secteur vient de geometrie()
    // relance : dès que l'unité est posée au ralliement, le bond suivant est
    // crié (la marche = la succession des bonds) ; repete : secteur couvert
    // → on recommence tant qu'il reste du vierge
    { ordre: { verbe: 'RATISSER' }, succes: 'secteurCouvert', echec: 'contactSubi', patience: 240, repete: 'partInconnueRestante', relance: 'uniteFormee' },
    { ordre: { verbe: 'REPOS' }, succes: 'toujours', conclusion: 'infirmerEnnemi' },
  ],
};
