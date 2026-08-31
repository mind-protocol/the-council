// monde/relief.js — le sol, sa couleur, et le monde qui continue après lui.
//
// Le relief est l'autorité d'altitude (scripts/monde/relief.py) : aucun autre
// module ne calcule de hauteur, tous appellent `zsol`.
//
// Sa COULEUR, elle, ne sort pas de l'altitude : un sol qui ne change qu'avec la
// hauteur donne une maquette de plâtre teinté. Ici le sol dit ce qui s'y passe —
// la campagne est verte, le labour est paille, la grève est claire, et la ville
// est de la terre battue, grise de cendre et de piétinement. L'urbanité ne se
// dessine pas : elle se COMPTE, en semant les 48 000 bâtiments dans une grille.
// Les faubourgs apparaissent alors tout seuls, exactement où ils sont.
//
// Enfin, le monde ne s'arrête pas au bord du fichier. La couronne prolonge
// chaque point du pourtour vers le large, en gardant son altitude et sa
// couleur : la côte continue en côte, la plaine en plaine. C'est cette couronne,
// avec la brume, qui vend les kilomètres.
"use strict";
import * as T from "/vendor/three.module.min.js";
import { dedans, bruit, mp } from "/modules/monde/echelle.js";
import { SOL, EAU } from "/modules/monde/palette.js";
import { grain } from "/modules/monde/grain.js";

// La tuile du sol est sa MESURE, comme partout ailleurs. Elle a valu 8 m un
// moment, au prétexte qu'un sol se voit de haut et de loin et qu'à 4 m la trame
// se répéterait assez pour se lire comme une trame. Le prétexte était faux :
// `camera.js` a un mode à pied, hauteur d'yeux 1,68 m. On MARCHE sur ce sol, et
// sous les pieds une tuile de 8 m s'étale en bouillie. La règle vaut donc ici
// comme pour le bâti — on prend la mesure, et l'échelle réelle est le sujet.
//
// La répétition au loin n'était pas le problème qu'on croyait : vue d'altitude,
// une tuile de 4 m passe sous le pixel et le mipmap la moyenne en une teinte
// unie, ce qui est exactement le résultat voulu. C'est l'anisotropie (voir
// `grain.js`) qui fait le travail en fuyante, pas une tuile plus large.
//
// La projection reste PLANE malgré le relief, et c'est mesuré : 99 % du terrain
// est sous 13° de pente, soit 3 % d'étirement ; le point le plus raide (29°) en
// donne 15 %. Une projection triplanaire coûterait trois fois le travail de
// texture pour corriger ce qu'on ne voit pas.
const TUILE_SOL = 4.0;   // Ground068 — la même valeur que côté Blender

export class Relief {
  constructor(ter) {
    this.res = ter.res_m; this.nx = ter.nx; this.ny = ter.ny;
    this.z = ter.z; this.eau = ter.eau || null;
    this.L = (this.nx - 1) * this.res;
    this.H = (this.ny - 1) * this.res;
  }

  // le décalque de zsol (batir.py) : bilinéaire, et rien d'autre
  sol(x, y) {
    const R = this.res;
    const i = Math.min(this.nx - 2, Math.max(0, Math.floor(x / R)));
    const j = Math.min(this.ny - 2, Math.max(0, Math.floor(y / R)));
    const tx = (x - i * R) / R, ty = (y - j * R) / R;
    const a = this.z[j][i] * (1 - tx) + this.z[j][i + 1] * tx;
    const b = this.z[j + 1][i] * (1 - tx) + this.z[j + 1][i + 1] * tx;
    return a * (1 - ty) + b * ty;
  }

  // ---- la couleur d'un point de sol ---------------------------------------
  // `usage` : une fonction (x, y) → { u, genre } — l'urbanité et, s'il y en a
  // un, le genre de sol que la carte 2D déclare là (bois, champ, marais…).
  teinte(x, y, z, u, genre, out) {
    const c = out || new T.Color();
    if (z < 0.2) {                       // le lit du fleuve : sombre, sous l'eau
      c.setHex(EAU.fond).multiplyScalar(0.75);
      return c;
    }
    c.setHex(genre && SOL[genre] ? SOL[genre] : SOL.herbe);
    // la grève : le sable remonte sur les premiers mètres au-dessus de l'étale
    if (z < 4.5) c.lerp(new T.Color(SOL.greve), 1 - Math.min(1, (z - 0.2) / 4.3));
    // les sommets : passé 55 m l'herbe ne tient plus, la roche affleure
    if (z > 55) c.lerp(new T.Color(SOL.roche), Math.min(0.85, (z - 55) / 55));
    // la ville : elle mange la campagne à mesure qu'elle se densifie
    if (u > 0.02) {
      const t = Math.min(1, u * 1.35);
      c.lerp(new T.Color(SOL.urbain), t);
      if (u > 0.55) c.lerp(new T.Color(SOL.urbain_dense), Math.min(1, (u - 0.55) / 0.45));
    }
    const b = 0.88 + bruit(x, y) * 0.24;  // rien n'est uni sur cent mètres
    c.multiplyScalar(b);
    return c;
  }

  // ---- le maillage ---------------------------------------------------------
  maillage(usage) {
    const { nx, ny, res } = this;
    const pos = new Float32Array(nx * ny * 3);
    const col = new Float32Array(nx * ny * 3);
    const c = new T.Color();
    let k = 0;
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const x = i * res, y = j * res, z = this.z[j][i];
      pos[k] = x; pos[k + 1] = y; pos[k + 2] = z;
      const q = usage ? usage(x, y) : null;
      this.teinte(x, y, z, q ? q.u : 0, q ? q.genre : null, c);
      col[k] = c.r; col[k + 1] = c.g; col[k + 2] = c.b;
      k += 3;
    }
    const idx = new Uint32Array((nx - 1) * (ny - 1) * 6);
    let n = 0;
    for (let j = 0; j < ny - 1; j++) for (let i = 0; i < nx - 1; i++) {
      const a = j * nx + i;
      idx[n++] = a; idx[n++] = a + 1; idx[n++] = a + nx + 1;
      idx[n++] = a; idx[n++] = a + nx + 1; idx[n++] = a + nx;
    }
    const g = new T.BufferGeometry();
    g.setAttribute("position", new T.BufferAttribute(pos, 3));
    g.setAttribute("color", new T.BufferAttribute(col, 3));
    g.setIndex(new T.BufferAttribute(idx, 1));
    g.computeVertexNormals();
    this._pos = pos; this._col = col;
    // La COURONNE, elle, reste en aplat : elle part à des dizaines de
    // kilomètres, la trame y serait répétée des milliers de fois pour finir
    // noyée dans la brume. Un fond lointain n'a pas besoin de grain.
    return new T.Mesh(g, grain(new T.MeshLambertMaterial({ vertexColors: true }),
      "/textures/sol.jpg", { h: TUILE_SOL, mode: "plan" }));
  }

  // ---- la couronne : le monde continue ------------------------------------
  // On prend le pourtour du terrain et on le pousse vers le large, radialement,
  // en gardant l'altitude et la couleur de son point d'origine. La côte reste
  // une côte, la plaine reste une plaine, et il n'y a pas de falaise au bord du
  // fichier. La brume mange le reste.
  //
  // La TERRE seulement. Le pourtour de Port-Réal est maritime aux trois quarts,
  // et prolonger l'eau n'a aucun sens : la nappe de `mer()` va déjà à 220 km. Un
  // point d'eau à un mètre d'étale prolongé sur quatre-vingt-dix kilomètres est
  // pris pour une plage par `teinte()` — le sable ne vaut que sur les premiers
  // mètres — et il flotte au-dessus de la nappe pendant des lieues avant de la
  // recouper. On obtient une baie de sable striée. Donc : la couronne s'arrête
  // au rivage, et s'y ferme en fondu plutôt qu'en langue flottante.
  couronne(portee = 90000, anneaux = 6) {
    const { nx, ny, res } = this;
    if (!this._pos) throw new Error("couronne() après maillage()");
    const bord = [];
    for (let i = 0; i < nx; i++) bord.push(i);                       // sud
    for (let j = 1; j < ny; j++) bord.push(j * nx + nx - 1);          // est
    for (let i = nx - 2; i >= 0; i--) bord.push((ny - 1) * nx + i);   // nord
    for (let j = ny - 2; j >= 1; j--) bord.push(j * nx);              // ouest
    bord.push(0);

    // Combien de pas de grille séparent chaque point du rivage le plus proche,
    // le long du pourtour. C'est ce qui donne le fondu : la couronne naît large
    // au milieu des terres et se referme sur la côte.
    const TERRE = 2.5, FONDU = 10;
    const terre = bord.map((v) => this._pos[v * 3 + 2] >= TERRE);
    const loin = new Float32Array(bord.length).fill(FONDU);
    for (let k = 0; k < bord.length; k++) if (!terre[k]) loin[k] = 0;
    for (let p = 0; p < FONDU; p++)
      for (let k = 0; k < bord.length; k++) {
        const a = loin[(k - 1 + bord.length) % bord.length];
        const b = loin[(k + 1) % bord.length];
        loin[k] = Math.min(loin[k], Math.min(a, b) + 1);
      }

    const cx = this.L / 2, cy = this.H / 2;
    const R = anneaux + 1;                        // le bord compte comme anneau 0
    const pos = new Float32Array(bord.length * R * 3);
    const col = new Float32Array(bord.length * R * 3);
    bord.forEach((v, k) => {
      const x = this._pos[v * 3], y = this._pos[v * 3 + 1], z = this._pos[v * 3 + 2];
      const dx = x - cx, dy = y - cy, d = Math.hypot(dx, dy) || 1;
      // le fondu : 0 au rivage, plein après FONDU pas. Sans lui, la couronne se
      // termine en falaise verticale là où la côte s'arrête.
      const f = loin[k] / FONDU, s = f * f * (3 - 2 * f);
      const pk = portee * s;
      const zf = Math.min(z, 60);                 // au loin tout s'aplatit
      for (let r = 0; r < R; r++) {
        // les anneaux se resserrent près du bord : c'est là qu'on les voit, et
        // une lamelle de dix mètres sur quatre-vingt-dix kilomètres n'a pas de
        // normale stable — d'où les stries radiales quand il n'y en avait qu'un.
        const t = Math.pow(r / anneaux, 2.2);
        const o = (k * R + r) * 3;
        pos[o] = x + dx / d * pk * t;
        pos[o + 1] = y + dy / d * pk * t;
        pos[o + 2] = z + (zf - z) * t;
        for (let c3 = 0; c3 < 3; c3++) col[o + c3] = this._col[v * 3 + c3];
      }
    });
    // Un quad n'est émis que si ses deux côtés portent de la couronne ; ailleurs
    // il serait de surface nulle, et l'eau n'a rien à prolonger.
    const idx = [];
    for (let k = 0; k < bord.length - 1; k++) {
      if (loin[k] === 0 && loin[k + 1] === 0) continue;
      for (let r = 0; r < anneaux; r++) {
        const a = (k * R + r), b = ((k + 1) * R + r);
        idx.push(a, a + 1, b + 1, a, b + 1, b);
      }
    }
    const g = new T.BufferGeometry();
    g.setAttribute("position", new T.BufferAttribute(pos, 3));
    g.setAttribute("color", new T.BufferAttribute(col, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    return new T.Mesh(g, new T.MeshLambertMaterial({ vertexColors: true }));
  }
}

// ---------------------------------------------------------------------------
// L'urbanité : où la ville est épaisse, et où elle n'est plus qu'un faubourg.
// On sème les bâtiments dans une grille grossière, on floute deux fois, on
// courbe. Rien à écrire à la main : c'est le bâti qui dit où est la ville.
// ---------------------------------------------------------------------------
export function urbanite(bati, colonnes, relief, carte, maille = 45) {
  const LX = Math.ceil(relief.L / maille) + 1, LY = Math.ceil(relief.H / maille) + 1;
  let g = new Float32Array(LX * LY);
  const cx = colonnes.x, cy = colonnes.y, cf = colonnes.facade_m, cp = colonnes.profondeur_m;
  for (const b of bati) {
    const i = Math.round(b[cx] / maille), j = Math.round(b[cy] / maille);
    if (i < 0 || j < 0 || i >= LX || j >= LY) continue;
    g[j * LX + i] += (b[cf] * b[cp]) / (maille * maille);   // l'emprise au sol
  }
  const flou = (src) => {
    const d = new Float32Array(src.length);
    for (let j = 0; j < LY; j++) for (let i = 0; i < LX; i++) {
      let s = 0, n = 0;
      for (let dj = -1; dj <= 1; dj++) for (let di = -1; di <= 1; di++) {
        const a = i + di, b = j + dj;
        if (a < 0 || b < 0 || a >= LX || b >= LY) continue;
        s += src[b * LX + a]; n++;
      }
      d[j * LX + i] = s / n;
    }
    return d;
  };
  g = flou(flou(g));

  // les aires que la carte 2D déclare : bois, champ, marais. Elles ne sont pas
  // dans le bâti, et sans elles la campagne est une seule nappe verte.
  const AIRES = { bois: "bois", champ: "champ", marais: "marais", greve: "greve", colline: null };
  const aires = (carte && carte.sol ? carte.sol : [])
    .filter((s) => s.genre in AIRES && AIRES[s.genre] && Array.isArray(s.points))
    .map((s) => ({ genre: AIRES[s.genre], poly: s.points.map(mp) }));

  return (x, y) => {
    const i = Math.min(LX - 1, Math.max(0, Math.round(x / maille)));
    const j = Math.min(LY - 1, Math.max(0, Math.round(y / maille)));
    const v = g[j * LX + i];
    const u = 1 - Math.exp(-v * 3.2);          // une courbe douce : 0 → 1
    let genre = null;
    if (u < 0.25) for (const a of aires) if (dedans(a.poly, x, y)) { genre = a.genre; break; }
    return { u, genre };
  };
}

// ---------------------------------------------------------------------------
// La mer : une nappe qui va jusqu'à l'horizon. C'est elle et la brume qui
// disent « ce monde est grand » — une flaque de la taille du fichier dit le
// contraire, quoi qu'on mette dessus.
// ---------------------------------------------------------------------------
export function mer(portee = 220000, environnement = null) {
  // Pas de métal : l'eau n'est pas du chrome. Vue d'aplomb elle donne sa
  // couleur, vue en rasant elle donne le ciel — c'est le Fresnel du matériau
  // standard qui fait la bascule, et c'est ce qui vend la distance quand on
  // regarde vers le large.
  const mat = new T.MeshStandardMaterial({
    color: EAU.large, roughness: 0.14, metalness: 0.0,
    envMapIntensity: 0.75, transparent: true, opacity: 0.95,
  });
  if (environnement) mat.envMap = environnement;
  const m = new T.Mesh(new T.PlaneGeometry(portee, portee), mat);
  m.position.set(0, 0, 0);
  m.renderOrder = 1;
  return m;
}
