/**
 * ⚙️ Physique / Forces / Paires — la grille spatiale DU TICK : les paires de
 * corps à moins de `portee` mètres (centre à centre). Le « O(n²) assumé —
 * index spatial différé » des forces a trouvé sa limite (~600 corps, la
 * prise de Port-Réal) : le différé est levé, les forces deviennent
 * O(n × voisins). DÉTERMINISTE : balayage dans l'ordre de la liste, chaque
 * paire une fois (idA < idB) — même seed, mêmes paires, même ordre.
 */

/**
 * @param {Iterable<Object>} corps — snapshots {id, pos, ...}
 * @param {number} portee — m, centre à centre : au-delà, aucune force de
 *   paire ne s'applique (la plus longue : la garde, allonge max + marge)
 * @returns {Array<[Object, Object]>}
 */
export function pairesProches(corps, portee) {
  const CEL = portee; // cellule = portée : 9 cellules couvrent tout voisin
  const grille = new Map();
  const cle = (cx, cy) => cx * 200003 + cy;
  const liste = [...corps];
  for (const c of liste) {
    const k = cle(Math.floor(c.pos.x / CEL), Math.floor(c.pos.y / CEL));
    let cellule = grille.get(k);
    if (!cellule) grille.set(k, (cellule = []));
    cellule.push(c);
  }
  const p2 = portee * portee;
  const paires = [];
  for (const c of liste) {
    const cx = Math.floor(c.pos.x / CEL);
    const cy = Math.floor(c.pos.y / CEL);
    for (let gx = cx - 1; gx <= cx + 1; gx++) {
      for (let gy = cy - 1; gy <= cy + 1; gy++) {
        const cellule = grille.get(cle(gx, gy));
        if (!cellule) continue;
        for (const v of cellule) {
          if (v.id <= c.id) continue; // chaque paire UNE fois, ordre stable
          const dx = v.pos.x - c.pos.x;
          const dy = v.pos.y - c.pos.y;
          if (dx * dx + dy * dy > p2) continue;
          paires.push([c, v]);
        }
      }
    }
  }
  return paires;
}
