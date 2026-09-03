/**
 * 🧠 Doctrine / Manœuvres / Tenir — le barrage : se former et TENIR la
 * meilleure ligne (estimation : trous minimaux entre moi et la menace — le
 * goulot gagne mécaniquement, aucun mot « pont » nulle part). Son axe
 * gainDePosition = la qualité de la ligne : c'est LE consommateur qui
 * l'attendait. La phase 2 n'a pas de fin (succès `jamais`) — on tient tant
 * qu'on est engagé ; l'hystérésis laisse une meilleure idée détrôner.
 * `posteChef` : le rôle dépose la destination comme CROYANCE « mon poste » —
 * le chef s'y porte (sa machine soldat), et « sur moi » y amène l'unité :
 * le corps du chef EST le point de ralliement, rien ne transite en
 * coordonnées dans les paroles.
 */

export const TENIR = {
  nom: 'tenir',
  applicabilite: ['ennemiEnMemoire', 'uniteAvecMoi', 'uniteAuFer'],
  posteChef: true, // le chef se porte au trou de la ligne, l'unité le suit

  /** Où cette manœuvre voudrait l'unité : le trou de la meilleure ligne. */
  geometrie(situation) {
    const ligne = situation.meilleureLigne();
    const depart = situation.positionUnite;
    if (!ligne || !depart) return null;
    return {
      chemin: [depart, ligne.centre],
      destination: ligne.centre,
      qualite: ligne.qualite, // → gainDePosition (projection)
    };
  },

  // la défense tient, l'agression piaffe
  poids: { defense: 0.6, agression: -0.4 },

  phases: [
    { ordre: { verbe: 'EN_FORMATION', sur: { type: 'locuteur' } }, succes: 'uniteFormee', patience: 90 },
    // pas d'échec, pas de fin : on TIENT — seule une meilleure idée détrône
    { ordre: { verbe: 'EN_FORMATION' }, succes: 'jamais' },
  ],
};
