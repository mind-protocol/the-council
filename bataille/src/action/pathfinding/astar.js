/**
 * 🏃 Action / Pathfinding / A* — l'algorithme, PUR : région + départ/arrivée
 * (mètres) → chemin en mètres (waypoints, départ exclu, arrivée exacte en
 * dernier), ou null si aucun. Voisinage 8 directions sans coupe de coin,
 * coût diagonal √2, heuristique octile. Ordre des voisins FIXE (déterminisme).
 */

const VOISINS = [
  [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1],
  [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2],
];

/**
 * @param {import('../../monde/navgrid.js').RegionNav} region
 * @param {{x: number, y: number}} depart
 * @param {{x: number, y: number}} arrivee
 * @returns {{x: number, y: number}[] | null}
 */
// ATELIER RÉUTILISÉ entre recherches (169 recherches/s à 630 hommes :
// allouer et remplir ~2,6 Mo de tableaux par recherche dominait le profil).
// Le tampon `gen` évite même le remplissage : une case n'est valide que si
// sa génération est celle de la recherche courante.
const atelier = { taille: 0, generation: 0, gen: null, g: null, f: null, parent: null, ferme: null };

export function trouverChemin(region, depart, arrivee) {
  const { colonnes, lignes } = region;
  const dep = region.versCase(depart);
  const arr = region.versCase(arrivee);
  const dans = (i, j) => i >= 0 && j >= 0 && i < colonnes && j < lignes;
  if (!dans(dep.i, dep.j) || !dans(arr.i, arr.j)) return null;
  // cible dans un mur : PAS de retour anticipé — la recherche tourne et le
  // « meilleur nœud » donnera un chemin au plus près
  if (dep.i === arr.i && dep.j === arr.j) return [{ x: arrivee.x, y: arrivee.y }];

  const n = colonnes * lignes;
  if (atelier.taille < n) {
    atelier.taille = n;
    atelier.gen = new Uint32Array(n);
    atelier.g = new Float64Array(n);
    atelier.f = new Float64Array(n);
    atelier.parent = new Int32Array(n);
    atelier.ferme = new Uint8Array(n);
    atelier.generation = 0;
  }
  const G = ++atelier.generation;
  const { gen, g, f, parent, ferme } = atelier;
  const vu = (k) => gen[k] === G;
  const toucher = (k) => {
    if (gen[k] !== G) {
      gen[k] = G;
      g[k] = Infinity;
      f[k] = Infinity;
      parent[k] = -1;
      ferme[k] = 0;
    }
  };
  // tie-break : l'heuristique à peine gonflée casse les égalités de f — en
  // terrain ouvert, l'octile pur explore une BANDE, pas un corridor
  const octile = (i, j) => {
    const dx = Math.abs(i - arr.i), dy = Math.abs(j - arr.j);
    return (dx + dy + (Math.SQRT2 - 2) * Math.min(dx, dy)) * 1.0005;
  };

  // tas binaire min sur f
  const tas = [];
  const pousser = (k) => {
    tas.push(k);
    let c = tas.length - 1;
    while (c > 0) {
      const p = (c - 1) >> 1;
      if (f[tas[p]] <= f[tas[c]]) break;
      [tas[p], tas[c]] = [tas[c], tas[p]];
      c = p;
    }
  };
  const retirer = () => {
    const tete = tas[0];
    const dernier = tas.pop();
    if (tas.length) {
      tas[0] = dernier;
      let c = 0;
      for (;;) {
        const a = 2 * c + 1, b = 2 * c + 2;
        let m = c;
        if (a < tas.length && f[tas[a]] < f[tas[m]]) m = a;
        if (b < tas.length && f[tas[b]] < f[tas[m]]) m = b;
        if (m === c) break;
        [tas[m], tas[c]] = [tas[c], tas[m]];
        c = m;
      }
    }
    return tete;
  };

  const kDep = dep.j * colonnes + dep.i;
  const kArr = arr.j * colonnes + arr.i;
  toucher(kDep);
  toucher(kArr);
  g[kDep] = 0;
  f[kDep] = octile(dep.i, dep.j);
  pousser(kDep);

  // meilleur nœud exploré (h minimal) : si la cible exacte est inatteignable,
  // on ira AU PLUS PRÈS — un homme ne reste pas planté loin
  let meilleur = kDep;
  let meilleureH = f[kDep];

  // BORNE d'exploration : une cible inatteignable (dans un mur, cour fermee)
  // faisait epuiser la region entiere (~2,3 M de cases sur la ville — 7
  // recherches concentraient 99 % du cout A* a 630 hommes). Le « plus pres »
  // se trouve tot ; au plafond, on rend le chemin vers lui.
  const LIMITE_NOEUDS = 20000;
  let fermes = 0;
  while (tas.length && fermes < LIMITE_NOEUDS) {
    const k = retirer();
    if (ferme[k]) continue;
    ferme[k] = 1;
    fermes++;
    const h = f[k] - g[k];
    if (h < meilleureH) {
      meilleureH = h;
      meilleur = k;
    }
    if (k === kArr) break;
    const i = k % colonnes, j = (k / colonnes) | 0;
    for (const [di, dj, cout] of VOISINS) {
      const ni = i + di, nj = j + dj;
      if (!dans(ni, nj) || !region.estLibre(ni, nj)) continue;
      // pas de coupe de coin : les deux orthogonales doivent être libres
      if (di !== 0 && dj !== 0 && (!region.estLibre(i + di, j) || !region.estLibre(i, j + dj))) continue;
      const nk = nj * colonnes + ni;
      toucher(nk);
      if (ferme[nk]) continue;
      const ng = g[k] + cout;
      if (ng < g[nk]) {
        g[nk] = ng;
        f[nk] = ng + octile(ni, nj);
        parent[nk] = k;
        pousser(nk);
      }
    }
  }

  let cibleK = kArr;
  let exacte = true;
  if (!ferme[kArr]) {
    if (meilleur === kDep) return null; // même au plus près, rien
    cibleK = meilleur;
    exacte = false;
  }

  // remonte les parents, départ exclu ; dernier waypoint : l'arrivée exacte,
  // ou le point atteignable le plus proche
  const chemin = [];
  for (let k = parent[cibleK]; k !== -1 && k !== kDep; k = parent[k]) {
    chemin.push(region.versMonde(k % colonnes, (k / colonnes) | 0));
  }
  chemin.reverse();
  chemin.push(
    exacte ? { x: arrivee.x, y: arrivee.y } : region.versMonde(cibleK % colonnes, (cibleK / colonnes) | 0)
  );
  return chemin;
}
