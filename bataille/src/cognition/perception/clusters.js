/**
 * 🧠 Perception / Clusters — regroupe les corps visibles en TAS par chaînage
 * géométrique : deux hommes à moins de `chainage` mètres appartiennent au
 * même tas — SANS traverser les livrées : la livrée se voit et structure
 * le groupement (sinon la mêlée fusionnerait les deux camps en un tas
 * mixte, et la croyance « ennemi » s'évaporerait au moment du contact).
 * Tourne DANS la perception de chaque homme (sur ses voisins à portée, jamais
 * globalement — le détail est LOCAL) : une GRILLE DE HACHAGE (cellule =
 * chaînage) borne le voisinage, deux corps à moins de `chainage` sont dans des
 * cellules adjacentes, on ne compare qu'au 9-voisinage. Quasi-linéaire au lieu
 * du O(voisins²) qui, en mêlée dense (des centaines de voisins), coûtait le
 * carré et dominait la perception (~60 % du tick à 1600 corps).
 *
 * DÉTERMINISTE, mais pas bit-à-bit identique au scan naïf : les COMPOSANTES
 * CONNEXES sont les mêmes (mêmes tas, mêmes membres), seul l'ordre INTERNE d'un
 * tas change — donc le dernier bit d'un barycentre peut bouger. La sim reste
 * reproductible (même seed → même scène) ; c'est la garantie que tient la
 * fumée, pas l'égalité à une version passée.
 */

/**
 * @param {{id, pos: {x,y}}[]} voisins — snapshot, triés par id
 * @param {number} chainage — distance de chaînage (m)
 * @returns {Array<Array>} — liste de tas (chaque tas : liste de voisins)
 */
export function regrouperEnTas(voisins, chainage) {
  const n = voisins.length;
  const c2 = chainage * chainage;
  // petit effectif : le scan naïf est imbattable (aucune grille à monter) —
  // c'est le cas courant (un homme isolé, une poignée de voisins).
  if (n < 24) return regrouperNaif(voisins, c2);

  const visite = new Array(n).fill(false);
  const tas = [];
  // grille : cellule de côté `chainage`, seau = index (ordre d'insertion 0..n).
  const cellule = (v) => Math.floor(v / chainage);
  const clef = (cx, cy) => cx * 73856093 ^ cy * 19349663;
  const grille = new Map();
  for (let i = 0; i < n; i++) {
    const k = clef(cellule(voisins[i].pos.x), cellule(voisins[i].pos.y));
    const seau = grille.get(k);
    if (seau) seau.push(i); else grille.set(k, [i]);
  }

  for (let i = 0; i < n; i++) {
    if (visite[i]) continue;
    const groupe = [];
    const file = [i];
    visite[i] = true;
    while (file.length) {
      const a = file.shift();
      const va = voisins[a];
      groupe.push(va);
      const cx = cellule(va.pos.x), cy = cellule(va.pos.y);
      for (let gx = cx - 1; gx <= cx + 1; gx++)
        for (let gy = cy - 1; gy <= cy + 1; gy++) {
          const seau = grille.get(clef(gx, gy));
          if (!seau) continue;
          for (const b of seau) {
            if (visite[b]) continue;
            const vb = voisins[b];
            const dx = va.pos.x - vb.pos.x, dy = va.pos.y - vb.pos.y;
            const dz = (va.z ?? 0) - (vb.z ?? 0);
            if (va.livree === vb.livree && dx * dx + dy * dy + dz * dz <= c2) {
              visite[b] = true;
              file.push(b);
            }
          }
        }
    }
    tas.push(groupe);
  }
  return tas;
}

/** Le scan naïf O(n²), pour les petits effectifs. */
function regrouperNaif(voisins, c2) {
  const visite = new Array(voisins.length).fill(false);
  const tas = [];
  for (let i = 0; i < voisins.length; i++) {
    if (visite[i]) continue;
    const groupe = [];
    const file = [i];
    visite[i] = true;
    while (file.length) {
      const a = file.shift();
      groupe.push(voisins[a]);
      for (let b = 0; b < voisins.length; b++) {
        if (visite[b]) continue;
        const dx = voisins[a].pos.x - voisins[b].pos.x;
        const dy = voisins[a].pos.y - voisins[b].pos.y;
        const dz = (voisins[a].z ?? 0) - (voisins[b].z ?? 0);
        if (voisins[a].livree === voisins[b].livree && dx * dx + dy * dy + dz * dz <= c2) {
          visite[b] = true;
          file.push(b);
        }
      }
    }
    tas.push(groupe);
  }
  return tas;
}
