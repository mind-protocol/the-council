// monde/echelle.js — L'AUTORITÉ, côté navigateur.
//
// Le décalque exact de scripts/monde/echelle.py. Rien dans le monde 3D n'a le
// droit d'inventer une dimension : tout se prend ici, et il n'y a qu'un pont
// entre la carte 2D (en unités de dessin) et le monde (en mètres).
//
// Le repère du monde : x vers l'est, y vers le nord, z vers le haut, l'origine
// au coin sud-ouest, le 0 à l'étale de la Néra. La carte, elle, compte ses y
// vers le sud (c'est un écran) : le miroir se fait dans `mp`, et nulle part
// ailleurs.
"use strict";

export const METRE_PAR_UNITE = 12.0;
export const CARTE_L = 440, CARTE_H = 300;
export const MONDE_L = CARTE_L * METRE_PAR_UNITE;   // 5 280 m d'est en ouest
export const MONDE_H = CARTE_H * METRE_PAR_UNITE;   // 3 600 m du nord au sud

export const m = (u) => u * METRE_PAR_UNITE;
export const mx = (u) => u * METRE_PAR_UNITE;
export const my = (u) => (CARTE_H - u) * METRE_PAR_UNITE;
export const mp = (p) => [mx(p[0]), my(p[1])];
export const ux = (x) => x / METRE_PAR_UNITE;
export const uy = (y) => CARTE_H - y / METRE_PAR_UNITE;

export const SOL_VILLE = 11.0;
export const MUR_HAUTEUR = 18.0, MUR_EPAISSEUR = 6.0;

// Un dessin lisible grossit ses monuments : sur la carte, le Donjon Rouge fait
// 60 unités de large, soit 720 m une fois métrisé — deux fois trop. On ne touche
// pas au dessin (il est juste POUR un dessin) : on corrige ici, et seulement
// pour le monde.
export const TAILLE_REELLE = {
  "Le Donjon Rouge": 330.0, "La Fosse aux Dragons": 240.0, "Le vieux septuaire": 110.0,
  "La Guilde des Alchimistes": 70.0, "Les casernes du Guet": 95.0, "La tour de la Main": 24.0,
  "Le bureau du maître de port": 26.0, "Le hangar du chantier": 40.0,
  "La grande place": 135.0, "Le marché aux chevaux": 105.0, "Le marché aux poissons": 85.0,
  "L'aire de bris": 150.0,
};

export function polygoneReel(nom, points) {
  const cible = TAILLE_REELLE[nom];
  if (!cible || !points || !points.length) return points;
  const cx = points.reduce((s, p) => s + p[0], 0) / points.length;
  const cy = points.reduce((s, p) => s + p[1], 0) / points.length;
  const grand = Math.max(
    Math.max(...points.map((p) => Math.abs(p[0] - cx))) * 2,
    Math.max(...points.map((p) => Math.abs(p[1] - cy))) * 2) * METRE_PAR_UNITE;
  if (grand <= cible) return points;
  const k = cible / grand;
  return points.map((p) => [cx + (p[0] - cx) * k, cy + (p[1] - cy) * k]);
}

// Un point dans un polygone — le rayon lancé, comme partout ailleurs dans le
// projet (terrain.js le fait pour le semis d'un bois).
export function dedans(poly, x, y) {
  let d = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    if ((poly[i][1] > y) !== (poly[j][1] > y) &&
        x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0])
      d = !d;
  }
  return d;
}

// Un hasard reproductible : sans graine, le sol bouillonnerait à chaque
// redessin. Le même générateur que ecrans/modules/terrain.js.
export function graine(s) {
  let h = 2166136261;
  for (let i = 0; i < String(s).length; i++) {
    h ^= String(s).charCodeAt(i); h = Math.imul(h, 16777619);
  }
  return () => {
    h += 0x6D2B79F5;
    let t = h;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Un bruit de valeur lissé, en mètres : ce qui empêche une prairie d'être une
// nappe de peinture. Deux octaves suffisent — on colore, on ne sculpte pas.
export function bruit(x, y) {
  const h = (i, j) => {
    let n = Math.imul(i, 374761393) ^ Math.imul(j, 668265263);
    n = Math.imul(n ^ (n >>> 13), 1274126177);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
  };
  const val = (px, py) => {
    const i = Math.floor(px), j = Math.floor(py);
    const fx = px - i, fy = py - j;
    const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    const a = h(i, j) * (1 - sx) + h(i + 1, j) * sx;
    const b = h(i, j + 1) * (1 - sx) + h(i + 1, j + 1) * sx;
    return a * (1 - sy) + b * sy;
  };
  return val(x / 180, y / 180) * 0.65 + val(x / 46, y / 46) * 0.35;
}
