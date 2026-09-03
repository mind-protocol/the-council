/**
 * 🧠 Perception / Forme d'un tas — la forme SE PERÇOIT : les caps des membres
 * sont visibles (les lances), donc un groupe a une orientation observable —
 * moyenne circulaire des caps, avec une NETTETÉ (longueur de la résultante,
 * 0→1) : une cohue n'a pas d'orientation, une formation en a une forte.
 * Sous le seuil : pas de forme lisible, le tas reste un rond flou.
 * Dans le repère du cap : largeur (transverse), profondeur (dans l'axe), et
 * la PREMIÈRE LIGNE (la tranche avant) — la position d'une unité, c'est elle.
 * Fonction PURE, calculée dans la perception de chacun.
 */

const DIAMETRE_CORPS = 0.7; // m — les étendues incluent l'encombrement

/**
 * La forme se lit sur le NOYAU À L'ARRÊT : ceux qui marchent (ça se voit)
 * ont le cap de leur marche, pas celui de la formation — les inclure noierait
 * la netteté pendant l'assemblage. « La formation, ce sont les hommes plantés
 * en rangs ; ceux qui courent autour n'en font pas encore partie. »
 * @param {{pos: {x,y}, cap: number, enMouvement?: boolean}[]} groupe — membres perçus
 * @param {{x, y}} barycentreTas — du tas entier (repris si pas de noyau)
 * @param {{netteteMin: number, trancheAvant: number}} options
 * @returns {{nettete: number, formeEffectif?: number, cap?: number, largeur?: number,
 *            profondeur?: number, premiereLigne?: {centre: {x,y}, largeur: number}}}
 */
export function analyserFormeTas(groupe, barycentreTas, { netteteMin, trancheAvant }) {
  const poses = groupe.filter((v) => !v.enMouvement);
  if (poses.length < 3) return { nettete: 0 };
  const barycentre = {
    x: poses.reduce((s, v) => s + v.pos.x, 0) / poses.length,
    y: poses.reduce((s, v) => s + v.pos.y, 0) / poses.length,
  };
  let sx = 0;
  let sy = 0;
  for (const v of poses) {
    sx += Math.cos(v.cap);
    sy += Math.sin(v.cap);
  }
  const nettete = Math.hypot(sx, sy) / poses.length;
  if (nettete < netteteMin) return { nettete };

  const cap = Math.atan2(sy, sx);
  const avant = { x: Math.cos(cap), y: Math.sin(cap) };
  const droite = { x: -avant.y, y: avant.x };
  let minA = Infinity, maxA = -Infinity, minL = Infinity, maxL = -Infinity;
  const projections = poses.map((v) => {
    const dx = v.pos.x - barycentre.x;
    const dy = v.pos.y - barycentre.y;
    const a = dx * avant.x + dy * avant.y;
    const l = dx * droite.x + dy * droite.y;
    minA = Math.min(minA, a); maxA = Math.max(maxA, a);
    minL = Math.min(minL, l); maxL = Math.max(maxL, l);
    return { v, a, l };
  });

  // la première ligne : la tranche avant
  const front = projections.filter((p) => p.a > maxA - trancheAvant);
  const centre = {
    x: front.reduce((s, p) => s + p.v.pos.x, 0) / front.length,
    y: front.reduce((s, p) => s + p.v.pos.y, 0) / front.length,
  };
  let minLF = Infinity, maxLF = -Infinity;
  for (const p of front) {
    minLF = Math.min(minLF, p.l);
    maxLF = Math.max(maxLF, p.l);
  }

  return {
    nettete,
    formeEffectif: poses.length, // la taille du noyau formé (pas du tas)
    cap,
    largeur: maxL - minL + DIAMETRE_CORPS,
    profondeur: maxA - minA + DIAMETRE_CORPS,
    premiereLigne: { centre, largeur: maxLF - minLF + DIAMETRE_CORPS },
  };
}
