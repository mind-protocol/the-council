/**
 * 🏃 Action / Pathfinding / Lissage — string-pulling : avale les waypoints
 * intermédiaires tant que la ligne de vue est dégagée. Le chemin cranté de
 * la grille (segments à 45°) devient 3-4 points aux vrais coins d'obstacles ;
 * les courbes, elles, émergent de l'inertie (⚙️ intégration), pas d'ici.
 * PUR. La visibilité échantillonne estLibre (🌍 navgrid) le long du segment
 * — la marge de l'agent est déjà dans estLibre.
 */

/** Le segment [a, b] est-il entièrement traversable ? */
function segmentLibre(a, b, estLibre, pas) {
  const d = Math.hypot(b.x - a.x, b.y - a.y);
  const n = Math.max(1, Math.ceil(d / pas));
  for (let k = 1; k < n; k++) {
    const t = k / n;
    if (!estLibre({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t })) return false;
  }
  return true;
}

/**
 * Greedy avant, O(n) tests de segments : on étend la ligne de vue depuis
 * l'ancre tant que le waypoint suivant reste visible ; sinon le waypoint
 * courant devient un coin (et la nouvelle ancre).
 * @param {{x,y}[]} chemin — chemin brut de l'A* (arrivée exacte en dernier)
 * @param {{x,y}} depart — position actuelle du corps
 * @param {(pos) => boolean} estLibre — vue 🌍 (navgrid)
 * @param {number} [pas] — pas d'échantillonnage (m)
 * @returns {{x,y}[]} chemin réduit aux coins + l'arrivée
 */
export function lisserChemin(chemin, depart, estLibre, pas = 0.25) {
  if (chemin.length <= 1) return chemin;
  const resultat = [];
  let ancre = depart;
  let j = 0;
  while (j < chemin.length - 1) {
    if (segmentLibre(ancre, chemin[j + 1], estLibre, pas)) {
      j++;
    } else if (ancre !== chemin[j]) {
      resultat.push(chemin[j]);
      ancre = chemin[j];
    } else {
      // coin serré : même l'arête brute (garantie par l'A*) échantillonne
      // bloqué — on la garde telle quelle et on force la progression
      resultat.push(chemin[j + 1]);
      ancre = chemin[j + 1];
      j++;
    }
  }
  if (resultat[resultat.length - 1] !== chemin[chemin.length - 1]) {
    resultat.push(chemin[chemin.length - 1]);
  }
  return resultat;
}
