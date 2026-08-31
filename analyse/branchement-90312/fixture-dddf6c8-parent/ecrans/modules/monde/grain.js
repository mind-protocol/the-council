// monde/grain.js — poser une photo sur une surface, à l'échelle du monde.
//
// Ce qui manque à un volume coloré, ce n'est pas la couleur : c'est le JOINT.
// Sans lui on ne sait pas si un mur fait trois mètres ou trente — le même mal
// que `materialisation/palette.py` corrige côté rasteriseur en peignant les
// assises au pixel. Ici, c'est une photo, mais posée sous trois conditions dont
// aucune n'est négociable.
//
// 1. EN NIVEAUX DE GRIS. La teinte reste celle de `palette.js` — par instance
//    pour le bâti, par sommet pour le sol et les rues — et le shader la
//    multiplie par le grain. On garde donc la lecture par métier (le port, les
//    tanneries, la rue d'Acier) et par usage du sol, qui est le seul repère sur
//    trente mille volumes ; en couleur, la photo l'effacerait. Accessoirement
//    une luminance pèse le tiers d'une couleur : cinq images, 150 ko en tout,
//    contre 114 Mo pour les originaux. Voir scripts/monde/textures.py.
//
// 2. UN BLANC D'ABORD, LA PHOTO ENSUITE. Une `map` dont l'image n'est pas
//    arrivée ne se dessine pas « sans texture » : elle s'échantillonne en NOIR.
//    Brancher la photo directement sur le matériau, c'est faire dépendre tout le
//    décor d'un fichier — un serveur d'avant la route, un cache vide, un réseau
//    lent, et la ville devient une silhouette noire. C'est arrivé. On pose donc
//    un pixel blanc, élément neutre de la multiplication : tant qu'il est là, la
//    surface est exactement ce qu'elle était avant les textures. Une texture
//    absente doit dégrader le décor, jamais l'éteindre.
//
// 3. À L'ÉCHELLE RÉELLE, ce qui demande de refaire l'UV dans le shader. Les
//    volumes du bâti et de la muraille sont des INSTANCES d'une seule boîte
//    unité : ses UV vont de 0 à 1 par face, donc une masure de 4 m et un
//    entrepôt de 40 m recevraient le même nombre d'assises — exactement
//    l'absence d'échelle qu'on vient corriger. Deux projections, donc, selon ce
//    qu'on habille : `boite` pour ce qui a des faces, `plan` pour ce qui est
//    couché (le sol, les rubans de voirie).
"use strict";
import * as T from "/vendor/three.module.min.js";

function blanc() {
  const t = new T.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1);
  t.needsUpdate = true;
  return t;
}

// La projection boîte, en mètres, pour ce qui a des faces. Sur une face
// verticale on échantillonne un axe du sol et l'axe Z : largeur et hauteur
// tombent chacune sur la bonne mesure — ce qui compte, car toutes les photos ne
// sont pas carrées et une échelle unique étirerait l'appareil.
const BOITE = (th, tv) => `
  #ifdef USE_INSTANCING
    vec3 ech = vec3(length(instanceMatrix[0].xyz),
                    length(instanceMatrix[1].xyz),
                    length(instanceMatrix[2].xyz));
  #else
    vec3 ech = vec3(1.0);
  #endif
  vec3 pm = position * ech;
  vec3 an = abs(normal);
  vec2 uvm, tl;
  if (an.z >= an.x && an.z >= an.y) { uvm = pm.xy; tl = vec2(${th}, ${th}); }
  else if (an.x >= an.y)            { uvm = pm.yz; tl = vec2(${th}, ${tv}); }
  else                              { uvm = pm.xz; tl = vec2(${th}, ${tv}); }
  vMapUv = uvm / tl;`;

// La projection plane, pour ce qui est couché : on prend la position MONDE en
// x et y. Le sol et les rues partagent ainsi la même trame, et une rue ne glisse
// pas sur le terrain quand on bouge la caméra.
const PLAN = (th, tv) => `
  vec4 pmond = modelMatrix * vec4(position, 1.0);
  vMapUv = pmond.xy / vec2(${th}, ${tv});`;

/**
 * Habille un matériau d'un grain à l'échelle du monde.
 * @param {Material} mat  le matériau à modifier (rendu tel quel)
 * @param {string} url    l'image, en niveaux de gris
 * @param {object} o      {h, v} la tuile en mètres ; {mode} "boite" | "plan"
 */
export function grain(mat, url, o = {}) {
  const h = (o.h ?? 2).toFixed(3), v = (o.v ?? o.h ?? 2).toFixed(3);
  const mode = o.mode === "plan" ? "plan" : "boite";

  mat.map = blanc();
  new T.TextureLoader().load(url, (t) => {
    t.wrapS = t.wrapT = T.RepeatWrapping;
    t.colorSpace = T.SRGBColorSpace;
    // Sans anisotropie, une trame vue en fuyante scintille — et le sol est vu
    // en fuyante presque tout le temps.
    t.anisotropy = 4;
    mat.map = t;
    mat.needsUpdate = true;
  }, undefined, () => {
    console.warn("[monde] texture absente, on reste en aplat :", url);
  });

  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace("#include <uv_vertex>",
      "#include <uv_vertex>" + (mode === "plan" ? PLAN(h, v) : BOITE(h, v)));
  };
  // Deux matériaux dont le shader diffère ne doivent pas partager un programme
  // compilé : sans cette clef, three réutilise le premier et le second sort avec
  // la trame de l'autre.
  mat.customProgramCacheKey = () => `grain-${mode}-${h}-${v}`;
  return mat;
}
