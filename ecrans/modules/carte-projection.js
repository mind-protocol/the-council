// carte-projection.js — le nord du monde reste le haut de toutes ses cartes.
//
// Les donnees de Port-Real vivent dans un repere cartesien ordinaire : y croît
// vers le nord. SVG et canvas font l'inverse, y croît vers le bas. La projection
// appartient donc a l'ecran, jamais au plan, au graphe des rues ou aux masques
// de collision. Tout ce qui superpose une couche au plan passe par ce petit
// contrat afin qu'une maison, un homme et le point que l'on clique restent le
// meme lieu.
(() => {
"use strict";

function vue(v) {
  return [v[0], -(v[1] + v[3]), v[2], v[3]];
}

function repere(v, largeur, hauteur) {
  const k = Math.min(largeur / v[2], hauteur / v[3]);
  const margeX = (largeur - v[2] * k) / 2;
  const margeY = (hauteur - v[3] * k) / 2;
  return {
    k, kx:k, ky:-k,
    ox:margeX - v[0] * k,
    oy:margeY + (v[1] + v[3]) * k,
    gx:margeX,
    gy:margeY,
  };
}

function point(r, x, y) {
  return [r.ox + x * r.kx, r.oy + y * r.ky];
}

function depuisPixel(v, r, x, y) {
  return [v[0] + (x - r.gx) / r.k,
          v[1] + v[3] - (y - r.gy) / r.k];
}

window.CarteProjection = Object.freeze({ vue, repere, point, depuisPixel,
  transformSvg:"scale(1 -1)" });
})();
