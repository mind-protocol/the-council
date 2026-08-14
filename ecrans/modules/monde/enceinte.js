// monde/enceinte.js — la muraille, ses sept portes, et les grands édifices.
//
// Ceux-là ne sortent pas du graphe : ils sortent de la carte 2D, qui reste
// l'autorité géographique de surface (etat/villes/<ville>.json). On les reprend
// en vraie épaisseur, comme batir.py, et on ramène les monuments à leur taille
// réelle — un dessin lisible grossit ses monuments, un monde ne le peut pas.
"use strict";
import * as T from "/vendor/three.module.min.js";
import { mp, polygoneReel, MUR_HAUTEUR, MUR_EPAISSEUR } from "/modules/monde/echelle.js";
import { PIERRE } from "/modules/monde/palette.js";
import { grain } from "/modules/monde/grain.js";

// La courtine et les corps de garde partagent le moellon des maisons — c'est le
// même chantier et la même carrière, et ça évite une image de plus. Les grands
// édifices ont la leur : le Donjon ROUGE ne se lit qu'à sa brique.
const APPAREIL = {
  murs:     ["/textures/murs.jpg", 3.0, 1.5],       // Bricks083, mesuré
  edifices: ["/textures/edifices.jpg", 1.8, 0.9],   // Bricks094, mesuré
};

// Un semis de boîtes en une seule instance : [{cx, cy, z, larg, prof, haut, cap}]
function boites(liste, teinte, appareil = APPAREIL.murs) {
  const g = new T.BoxGeometry(1, 1, 1).translate(0, 0, 0.5);
  const [url, h, v] = appareil;
  const im = new T.InstancedMesh(g,
    grain(new T.MeshLambertMaterial({ color: teinte }), url, { h, v }),
    Math.max(1, liste.length));
  const m = new T.Matrix4(), q = new T.Quaternion(), ax = new T.Vector3(0, 0, 1);
  const p = new T.Vector3(), s = new T.Vector3();
  liste.forEach((b, i) => {
    q.setFromAxisAngle(ax, b.cap);
    im.setMatrixAt(i, m.compose(p.set(b.cx, b.cy, b.z), q, s.set(b.larg, b.prof, b.haut)));
  });
  im.count = liste.length;
  im.instanceMatrix.needsUpdate = true;
  im.computeBoundingSphere();
  // Un édifice est découpé en un pan de mur par côté : toutes ses instances
  // portent donc le même nom, et le survol répond « Le Donjon Rouge » de
  // n'importe quelle face. C'est la seule chose que ces boîtes savent d'elles.
  im.userData.noms = liste.map((b) => b.nom || "");
  return im;
}

// La hauteur d'un édifice : ce qui doit se voir de loin se voit de loin. Le
// Donjon coiffe sa colline, la tour de la Main dépasse tout le reste.
const HAUTEUR = {
  "Le Donjon Rouge": 46, "La Fosse aux Dragons": 38, "La tour de la Main": 58,
};

export function batir(carte, relief) {
  // Une carte peut arriver DÉJÀ EN MÈTRES (`metres: true`) au lieu des unités
  // de dessin. C'est le cas de tout ce qui est engendré : le modèle travaille
  // en mètres de bout en bout, et lui faire écrire des unités de carte pour
  // qu'on les remultiplie ici serait une échelle de plus à tenir juste.
  // Un dessin à la main garde `mp` et sa correction de taille — il est fait
  // pour être lu, pas pour être mesuré.
  const enMetres = !!carte.metres;
  const proj = enMetres ? ((p) => [p[0], p[1]]) : mp;
  const reel = enMetres ? ((nom, pts) => pts) : polygoneReel;

  const murs = [], portes = [], edifices = [];
  for (const s of carte.sol || []) {
    if (s.genre !== "mur") continue;

    if (s.largeur === undefined) {                    // la courtine
      const pts = s.points.map(proj);
      for (let i = 0; i < pts.length - 1; i++) {
        const a = pts[i], b = pts[i + 1];
        murs.push({
          cx: (a[0] + b[0]) / 2, cy: (a[1] + b[1]) / 2,
          z: Math.min(relief.sol(a[0], a[1]), relief.sol(b[0], b[1])) - 2,
          larg: Math.hypot(b[0] - a[0], b[1] - a[1]),
          prof: s.epaisseur || MUR_EPAISSEUR, haut: (s.haut || MUR_HAUTEUR) + 2,
          cap: Math.atan2(b[1] - a[1], b[0] - a[0]), nom: s.nom || "",
        });
      }
    } else if (s.largeur === 6) {                     // un corps de garde
      const a = proj(s.points[0]), b = proj(s.points[s.points.length - 1]);
      const cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2;
      portes.push({ cx, cy, z: relief.sol(cx, cy) - 2,
        larg: s.larg || 16, prof: s.epaisseur || 12, haut: s.haut || 24,
        cap: Math.atan2(b[1] - a[1], b[0] - a[0]), nom: s.nom || "" });
    } else if (s.largeur <= 4) {                      // un grand édifice
      const W = reel(s.nom || "", s.points).map(proj);
      const haut = s.haut || HAUTEUR[s.nom] || 22;
      for (let i = 0; i < W.length; i++) {
        const a = W[i], b = W[(i + 1) % W.length];
        const lg = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (lg < 1) continue;
        const cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2;
        edifices.push({ cx, cy, z: (s.assise !== undefined ? s.assise : relief.sol(cx, cy)) - 2,
          larg: lg, prof: s.epaisseur || 7, haut,
          cap: Math.atan2(b[1] - a[1], b[0] - a[0]), nom: s.nom || "" });
      }
    }
  }
  const courtine = boites(murs, PIERRE.courtine);
  const gardes = boites(portes, PIERRE.porte);
  const grands = boites(edifices, PIERRE.edifice, APPAREIL.edifices);
  return {
    courtine, portes: gardes, edifices: grands,
    muraille: [courtine, gardes], objets: [courtine, gardes, grands],
    nombre: { murs: murs.length, portes: portes.length, edifices: edifices.length },
  };
}
