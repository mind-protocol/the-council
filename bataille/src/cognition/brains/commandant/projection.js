/**
 * 🧠 Commandant / Projection — le what-if, GÉNÉRIQUE : arithmétique mentale
 * grossière, six axes standard normalisés (~[-1, 1], POSITIF = désirable),
 * dérivés de la seule GÉOMÉTRIE fournie par la manœuvre.
 * Une manœuvre peut proposer PLUSIEURS OPTIONS (géométries nommées — « de
 * front », « par la gauche »…) : chacune est projetée, l'arbitre les score
 * toutes et la meilleure porte la manœuvre. gainDePosition et risqueDesordre
 * sont ANNONCÉS par la géométrie (qualite / desordre) — le moteur ne fait
 * que les lire : la connaissance tactique reste dans le livre.
 */

const distanceChemin = (chemin) => {
  let d = 0;
  for (let i = 1; i < chemin.length; i++) {
    d += Math.hypot(chemin[i].x - chemin[i - 1].x, chemin[i].y - chemin[i - 1].y);
  }
  return d;
};

/**
 * Projette UNE option (une géométrie) sur les six axes.
 * @param {{chemin: Array, destination, qualite?: number, desordre?: number}} geo
 * @param {Object} situation — les faits (estimation.js)
 * @param {Object} params
 * @returns {Object} axes
 */
export function projeterOption(geo, situation, params) {
  const d = distanceChemin(geo.chemin);
  const t = d / params.vitesseMax;

  // information : l'aire balayée en chemin vs l'aire encore inconnue
  const aireBalayee = d * 2 * params.perception.portee;
  const aireInconnue = situation.aireZone * situation.partInconnueDeLaZone;
  const gainInformation = aireInconnue > 1 ? Math.min(1, aireBalayee / aireInconnue) : 0;

  return {
    temps: -Math.min(1, t / 180),          // une manœuvre longue coûte
    // être porté DEVANT la bande amie = exposé seul — c'est cet axe qui
    // fait avancer un camp EN LIGNE (l'unité de tête attend les siens)
    exposition: -Math.min(
      1,
      (situation.avanceSurAllies?.(geo.destination) ?? 0) / params.commandement.porteeExposition
    ),
    gainDePosition: geo.qualite ?? 0,      // annoncé par la géométrie (ligne, flanc)
    coutFatigue: -Math.min(1, d / 200),
    risqueDesordre: -(geo.desordre ?? 0),  // annoncé : la marche qui désordonne
    gainInformation,
  };
}

/**
 * Les OPTIONS d'une manœuvre, projetées : geometrie() peut retourner une
 * géométrie seule ou un tableau de géométries nommées.
 * @returns {{nom: string|null, geo: Object, axes: Object}[]} — [] si aucune
 */
export function projeterAxes(manoeuvre, situation, params) {
  const brut = manoeuvre.geometrie(situation);
  const geos = brut == null ? [] : Array.isArray(brut) ? brut : [brut];
  return geos
    .filter((g) => g && g.chemin && g.destination)
    .map((geo) => ({ nom: geo.nom ?? null, geo, axes: projeterOption(geo, situation, params) }));
}
