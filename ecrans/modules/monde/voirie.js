// monde/voirie.js — les rues, à leur vraie largeur.
//
// Le décalque de `ruban` (batir.py) : une bande posée sur le terrain le long
// d'une polyligne, décalée de quelques centimètres pour ne pas se battre avec
// le sol. Une artère fait 8 m, une ruelle 2 — et c'est cette différence-là,
// répétée dix-huit mille fois, qui donne à la ville sa texture vue de haut.
//
// Tout part dans une seule géométrie : dix-huit mille tronçons en un appel de
// dessin. Les couleurs passent par les sommets.
"use strict";
import * as T from "/vendor/three.module.min.js";
import { VOIE } from "/modules/monde/palette.js";
import { grain } from "/modules/monde/grain.js";

// Le pavé, en projection PLANE et non boîte : un ruban est couché, et sa trame
// doit être celle du sol qu'il recouvre — sinon chaque tronçon repart de zéro et
// la rue se met à clignoter d'un segment à l'autre. La couleur par genre reste
// aux sommets : une artère ne se distingue pas d'une ruelle par son pavage.
const TUILE_PAVE = 2.0;   // PavingStones136, accordé au pavé mesuré de PavingStones070

export function rubans(aretes, relief, opts = {}) {
  const dz = opts.dz ?? 0.35;
  const pos = [], col = [], idx = [];
  const c = new T.Color();
  for (const a of aretes) {
    const tr = a.trace;
    if (!tr || tr.length < 2) continue;
    c.setHex(VOIE[a.genre] || VOIE.rue);
    const base = pos.length / 3, w = (a.largeur_m || 4) / 2;
    for (let k = 0; k < tr.length; k++) {
      const av = tr[Math.min(k + 1, tr.length - 1)], ar = tr[Math.max(k - 1, 0)];
      const dx = av[0] - ar[0], dy = av[1] - ar[1];
      const d = Math.hypot(dx, dy) || 1;
      const nx = -dy / d * w, ny = dx / d * w;
      const z = relief.sol(tr[k][0], tr[k][1]) + dz;
      pos.push(tr[k][0] + nx, tr[k][1] + ny, z, tr[k][0] - nx, tr[k][1] - ny, z);
      col.push(c.r, c.g, c.b, c.r, c.g, c.b);
    }
    for (let k = 0; k < tr.length - 1; k++) {
      const a0 = base + k * 2;
      idx.push(a0, a0 + 1, a0 + 3, a0, a0 + 3, a0 + 2);
    }
  }
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
  g.setAttribute("color", new T.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  const m = new T.Mesh(g, grain(new T.MeshLambertMaterial({
    vertexColors: true, side: T.DoubleSide,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
  }), "/textures/rues.jpg", { h: TUILE_PAVE, mode: "plan" }));
  m.nombre = aretes.length;
  return m;
}
