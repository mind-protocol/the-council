// monde/maillage.js — un corps bâti servi en VRAI maillage, pas en boîtes.
//
// `bati.js` sème des instances : deux appels de dessin pour quarante-huit mille
// volumes, et c'est la seule façon de tenir une ville. Mais une instance est une
// boîte : on ne peut pas y percer une porte, ni voir qu'un mur a une épaisseur.
//
// Quand un lieu a un morceau qui mérite d'être vu de près — un château de deux
// cents mètres, vingt mille triangles —, le serveur en donne le maillage indexé
// et ce module le pose tel quel. Une géométrie, un groupe de faces par matière.
//
// Les faces sont PLATES par construction (le modèle est facetté) : on ne calcule
// donc pas de normales lissées, qui donneraient à de la pierre taillée l'air
// d'une chose organique.
"use strict";
import * as T from "/vendor/three.module.min.js";
import { PIERRE } from "/modules/monde/palette.js";

// Les matières du modèle, traduites une fois. Ce qui n'est pas connu tombe sur
// la pierre : mieux vaut un mur gris qu'un objet invisible.
const TEINTE = {
  pierre: PIERRE.courtine, taille: 0xa09a90, toit: 0x4b3f3c,
  basalte: 0x33302f, quai: 0x8d877e, bois: 0x574434,
  "mur-bourg": 0x7b7060, chaume: 0x6d5c3c, greve: 0x8a8172, cendre: 0x55504c,
};

export function poser(paquet) {
  const g = new T.BufferGeometry();
  g.setAttribute("position",
    new T.Float32BufferAttribute(new Float32Array(paquet.sommets), 3));
  g.setIndex(paquet.index);

  const matieres = [];
  (paquet.groupes || []).forEach((gr, i) => {
    g.addGroup(gr.debut, gr.compte, i);
    matieres.push(new T.MeshLambertMaterial({
      color: TEINTE[gr.matiere] ?? PIERRE.courtine,
      // Un intérieur ne se voit que si l'on regarde ses murs par-dedans : sans
      // les deux faces, entrer par la porte donne sur une pièce transparente.
      side: T.DoubleSide,
      name: gr.matiere,
    }));
  });
  g.computeVertexNormals();
  g.computeBoundingSphere();

  const objet = new T.Mesh(g, matieres);
  objet.name = "Le maillage";
  return { objet, faces: paquet.index.length / 3, matieres: matieres.length };
}
