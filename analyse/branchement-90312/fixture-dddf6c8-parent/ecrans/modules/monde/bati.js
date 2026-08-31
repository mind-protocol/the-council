// monde/bati.js — les 48 000 volumes, en deux semis d'instances.
//
// Le décalque de la fonction `maison` de scripts/monde/batir.py : des murs, puis
// un TOIT — c'est le toit qui fait qu'une ville se lit. Un corps et un toit, ça
// fait deux appels de dessin pour toute la ville : le reste du budget d'images
// reste pour l'air et pour les gens.
//
// Rien n'est modélisé à l'œil. Position, cap, façade, profondeur, hauteur et
// métier viennent tous de monde/<monde>.bati.json, en colonnes — le monde est
// une DONNÉE, pas une constante : `portreal` par défaut, `peyredragon` quand
// c'est le château qu'on regarde. Le pendant Python est scripts/monde/bati.py,
// seul lecteur du bâti côté scripts ; ici, c'est `/monde/<lieu>/bati` servi par
// serveur.js qui joue ce rôle, et ce module ne fait que dessiner ce qu'on lui
// donne. Il ne doit donc JAMAIS nommer un monde en dur : le jour où il l'a
// fait, l'autre monde a cessé d'exister pour tout le reste du code.
"use strict";
import * as T from "/vendor/three.module.min.js";
import { BATI } from "/modules/monde/palette.js";
import { grain } from "/modules/monde/grain.js";

// --- le grain -------------------------------------------------------------
// Le mécanisme (gris, blanc d'abord, échelle réelle) vit dans `grain.js`, parce
// que le sol, les rues et la muraille en font exactement autant. Ici on ne garde
// que les MESURES, qui sont propres au bâti.
const TUILE_MURS_H = 3.0, TUILE_MURS_V = 1.5;   // Bricks083 : 300 x 150 cm, mesuré
const TUILE_TOITS = 2.9;                        // RoofingTiles013A : 290 cm, mesuré

// une boîte unité, posée sur son plancher : l'instance porte l'échelle et le cap
const gCorps = () => new T.BoxGeometry(1, 1, 1).translate(0, 0, 0.5);

// Un toit à deux pentes, faîte PERPENDICULAIRE à la façade — le « pignon sur
// rue », la parcelle étroite et profonde, la plus commune d'une ville
// médiévale. `long` met le faîte le long de la façade : hangars, granges.
function gToit(long) {
  const g = new T.BufferGeometry();
  const v = long
    ? [-.5,-.5,0, .5,-.5,0, .5,.5,0, -.5,.5,0, -.5,0,1, .5,0,1]
    : [-.5,-.5,0, .5,-.5,0, .5,.5,0, -.5,.5,0, 0,-.5,1, 0,.5,1];
  const f = long
    ? [0,1,4, 1,5,4, 1,2,5, 2,3,5, 3,4,5, 3,0,4]
    : [0,1,4, 2,3,5, 1,2,5, 1,5,4, 3,0,4, 3,4,5];
  g.setAttribute("position", new T.Float32BufferAttribute(v, 3));
  g.setIndex(f);
  g.computeVertexNormals();
  return g;
}

export const MONDE_DEFAUT = "portreal";

// La tranche courante du test de boîte, tenue À PART. Une fermeture par
// candidat, c'est quelques centaines d'objets jetés à chaque visée et dix
// visées par seconde : le ramasse-miettes finit par s'arrêter en plein
// mouvement de souris, et c'est lui qu'on voyait dans les cinquante
// millisecondes. Deux variables de module coûtent zéro et durent toujours.
let _t0 = 0, _t1 = 0;
function fente(org, dir, demi) {
  if (Math.abs(dir) < 1e-9) return Math.abs(org) <= demi;
  let a = (-demi - org) / dir, b = (demi - org) / dir;
  if (a > b) { const w = a; a = b; b = w; }
  if (a > _t0) _t0 = a;
  if (b < _t1) _t1 = b;
  return _t0 <= _t1;
}

export function batir(paquet, monde) {
  const { bati, _colonnes } = paquet;
  // Le nom sert à se dire d'où viennent ces volumes (traces, couches, mesures) ;
  // le paquet peut le porter lui-même, sinon c'est celui qu'on passe.
  const nomMonde = paquet.monde || monde || MONDE_DEFAUT;
  const C = {}; _colonnes.forEach((n, i) => C[n] = i);
  const N = bati.length;

  const corps = new T.InstancedMesh(gCorps(),
    grain(new T.MeshLambertMaterial(), "/textures/murs.jpg",
      { h: TUILE_MURS_H, v: TUILE_MURS_V }), N);
  const toits = new T.InstancedMesh(gToit(false),
    grain(new T.MeshLambertMaterial({ side: T.DoubleSide }), "/textures/toits.jpg",
      { h: TUILE_TOITS }), N);

  const mat = new T.Matrix4(), q = new T.Quaternion(), ax = new T.Vector3(0, 0, 1);
  const p = new T.Vector3(), s = new T.Vector3(), c = new T.Color(), ct = new T.Color();

  // --- de quoi VISER un volume ------------------------------------------------
  // Le survol demande « lequel est sous le curseur ? ». Le raycast d'un
  // InstancedMesh répond en inversant une matrice par instance : quarante-huit
  // mille inversions par interrogation, cinquante millisecondes, un hoquet à
  // chaque fois qu'on bouge la souris. On garde donc à part, en tableaux
  // typés, le milieu et le rayon de chaque volume — dix flottants qu'on écrit
  // ici puisqu'on tient déjà les mesures — et l'on écarte d'abord, en un
  // produit scalaire, tout ce que le rai ne frôle même pas. Il en reste
  // quelques dizaines, qu'on teste alors pour de bon contre la boîte.
  const mx = new Float32Array(N), my = new Float32Array(N), mz = new Float32Array(N);
  const rayonN = new Float32Array(N);
  const demiF = new Float32Array(N), demiP = new Float32Array(N);
  const basZ = new Float32Array(N), hautZ = new Float32Array(N);
  const cos = new Float32Array(N), sin = new Float32Array(N);

  for (let n = 0; n < N; n++) {
    const b = bati[n];
    const x = b[C.x], y = b[C.y];
    // 0.98 et pas 0.94 : le retrait ne sert qu'à ce que deux murs mitoyens ne
    // se battent pas en Z. Le vide entre deux maisons est une donnée du
    // quartier (echelle.GRAIN), pas un effet de rendu — à 6 % de retrait, le
    // Culpucier rendait un demi-mètre de fossé qu'aucune donnée ne demandait.
    const f = b[C.facade_m] * 0.98, prof = b[C.profondeur_m] * 0.98;
    const h = b[C.hauteur_m] + 1.0;
    // le z du bâti est CELUI DU FICHIER quand il y est : le relief a déjà été
    // interrogé à la génération, et le réinterroger ici ferait flotter les
    // maisons d'un demi-mètre là où les deux calculs divergent
    const z = (C.z !== undefined ? b[C.z] : 0) - 1.0;
    q.setFromAxisAngle(ax, T.MathUtils.degToRad(b[C.cap]));

    corps.setMatrixAt(n, mat.compose(p.set(x, y, z), q, s.set(f, prof, h)));
    const ht = Math.min(f, prof) * 0.45;
    toits.setMatrixAt(n, mat.compose(p.set(x, y, z + h), q, s.set(f, prof, ht)));

    // Les mêmes mesures, mises de côté pour le viseur — murs ET toit, parce que
    // c'est le toit qu'on désigne quand on regarde une ville d'en haut.
    const a = T.MathUtils.degToRad(b[C.cap]);
    demiF[n] = f / 2; demiP[n] = prof / 2;
    basZ[n] = z; hautZ[n] = z + h + ht;
    cos[n] = Math.cos(a); sin[n] = Math.sin(a);
    mx[n] = x; my[n] = y; mz[n] = z + (h + ht) / 2;
    rayonN[n] = 0.5 * Math.hypot(f, prof, h + ht);

    const cat = C.cat !== undefined ? b[C.cat] : null;
    const usage = b[C.usage];
    c.setHex((cat && BATI.cat[cat]) || BATI.usage[usage] || BATI.cat.habitat);
    // deux maisons voisines ne sont jamais du même enduit : sans ce grain, un
    // quartier entier devient un aplat, et l'échelle se perd
    const g = 0.86 + ((n * 2654435761) % 1000) / 1000 * 0.28;
    corps.setColorAt(n, c.multiplyScalar(g));
    ct.setHex(usage === "taudis" ? BATI.toit_taudis : BATI.toit);
    toits.setColorAt(n, ct.multiplyScalar(0.88 + ((n * 40503) % 1000) / 1000 * 0.24));
  }
  corps.instanceMatrix.needsUpdate = true;
  toits.instanceMatrix.needsUpdate = true;
  corps.instanceColor.needsUpdate = true;
  toits.instanceColor.needsUpdate = true;
  corps.computeBoundingSphere(); toits.computeBoundingSphere();

  /**
   * Le volume que ce rai rencontre en premier, ou null.
   * `{ n, t }` — l'indice de la ligne du bâti, et la distance en mètres.
   * `portee` borne la recherche : au-delà, on ne désigne plus rien.
   */
  function viser(rai, portee) {
    const o = rai.origin, d = rai.direction;
    let elu = -1, meilleure = portee || Infinity;
    for (let n = 0; n < N; n++) {
      // Le rejet en gros : la distance du milieu à la droite du rai.
      const ex = mx[n] - o.x, ey = my[n] - o.y, ez = mz[n] - o.z;
      const t = ex * d.x + ey * d.y + ez * d.z;
      const r = rayonN[n];
      if (t + r < 0 || t - r > meilleure) continue;   // derrière, ou trop loin
      const px = ex - d.x * t, py = ey - d.y * t, pz = ez - d.z * t;
      if (px * px + py * py + pz * pz > r * r) continue;
      // Le test pour de bon : la boîte, dans son propre repère (on tourne le rai
      // du cap de la maison plutôt que la maison, c'est le même calcul en moins
      // cher). Trois paires de plans, la tranche commune, et voilà l'entrée.
      const ox = o.x - mx[n], oy = o.y - my[n];
      const c1 = cos[n], s1 = sin[n];
      const lox = ox * c1 + oy * s1, loy = -ox * s1 + oy * c1;
      const ldx = d.x * c1 + d.y * s1, ldy = -d.x * s1 + d.y * c1;
      const zc = (basZ[n] + hautZ[n]) / 2, hz = (hautZ[n] - basZ[n]) / 2;
      _t0 = 0; _t1 = meilleure;
      if (!fente(lox, ldx, demiF[n])) continue;
      if (!fente(loy, ldy, demiP[n])) continue;
      if (!fente(o.z - zc, d.z, hz)) continue;
      if (_t0 >= 0 && _t0 < meilleure) { meilleure = _t0; elu = n; }
    }
    return elu < 0 ? null : { n: elu, t: meilleure };
  }

  return {
    corps, toits, objets: [corps, toits], nombre: N, monde: nomMonde,
    viser, colonnes: C, lignes: bati, types: paquet._types || {},
  };
}
