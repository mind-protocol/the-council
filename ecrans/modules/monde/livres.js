// monde/livres.js — les registres et les carnets, comme OBJETS de la pièce.
//
// `docs/books.md` ouvre par une phrase qui est une spécification : « Un livre
// est un OBJET du monde : un registre posé sur une table, un carnet qu'on porte
// sous le bras. » Il portait du JSON, il se lisait sous son onglet, et il
// n'existait nulle part dans le volume. Une salle du conseil avec sept
// registres sur la Table Peinte et rien à voir dessus est le même mensonge
// qu'une pièce vide de gens.
//
// POURQUOI CE N'EST PAS DU MOBILIER. On pourrait croire qu'un registre posé se
// cuit dans `peyredragon.interieurs.json` avec les tables et les coffres. Non,
// et pour deux raisons qui ne se rattrapent pas :
//   - `etat/books.json` est de l'ÉTAT DE PARTIE. Un registre naît en scène,
//     change de main, se referme. Le maillage, lui, est engendré hors ligne :
//     un livre cuit dedans serait figé au jour de la génération.
//   - TRENTE-QUATRE des quarante-trois sont PORTÉS, pas posés. Un carnet sous
//     le bras d'Aurore n'a pas de place dans la coque d'une salle — il est là
//     où elle est, et il sort quand elle sort.
//
// Un livre porté ne paraît donc que si son porteur est dans la pièce. C'est la
// règle, et elle est juste : le carnet de Marlo n'est pas à Peyredragon.
"use strict";
import * as T from "/vendor/three.module.min.js";

// Un registre de conseil est un in-folio : trente centimètres sur vingt, et
// une épaisseur qui se voit. Un carnet qu'on glisse sous un bras est plus
// petit. On ne cherche pas la vraisemblance du relieur — on cherche qu'un
// registre se distingue d'un carnet à trois mètres.
const TAILLE = {
  registre: [0.34, 0.24, 0.075],
  carnet:   [0.19, 0.13, 0.035],
  rouleau:  [0.30, 0.07, 0.07],
};
const DEFAUT = TAILLE.registre;

const TABLE_H = 0.78;    // le plateau sur lequel un registre est posé
const SOUS_BRAS = 1.05;  // la hauteur d'une main qui tient un carnet
const PORTEE = 90;       // au-delà, un livre n'est plus lisible : on l'éteint

// Le cuir des reliures, pas la couleur du texte : un registre d'office est
// sombre et lourd, un carnet personnel est fauve, un rouleau est du parchemin.
const TEINTE = { registre: 0x4a3428, carnet: 0x8a6a42, rouleau: 0xc8b78e };
const TRANCHE = 0xd8cba8;   // les pages, sur le champ

function mesure(type) { return TAILLE[type] || DEFAUT; }

/**
 * `poser(scene, {relief, xyz})` — la pile des livres de la pièce.
 *
 * `maj(livres, ou)` :
 *   `livres` — le tableau de `/books`, tel quel.
 *   `ou(acteur_id)` — rend [x, y, z] si cet acteur est visible dans la pièce,
 *      sinon rien. C'est ce qui fait qu'un carnet suit son porteur sans que ce
 *      module ait à savoir comment les gens sont placés.
 */
export function poser(scene, o = {}) {
  const relief = o.relief || null;
  let base = (o.xyz || [0, 0, 0]).slice();
  let salleId = o.salle || null;

  const racine = new T.Group();
  racine.renderOrder = 996;          // sous les gens, au-dessus du décor
  scene.add(racine);

  // Deux géométries pour tout le monde, comme pour les corps : à quarante
  // livres on ne justifie pas d'instancier, mais pas non plus quarante boîtes.
  const geos = new Map();
  function geo(type) {
    if (!geos.has(type)) {
      const [l, p, h] = mesure(type);
      geos.set(type, new T.BoxGeometry(l, p, h));
    }
    return geos.get(type);
  }

  let objets = [];
  let signature = "";
  let visible = true;

  function sol(x, y) {
    return Math.max(base[2] || 0, relief ? relief.sol(x, y) : 0);
  }

  function vider() {
    objets.forEach((o2) => {
      racine.remove(o2.g);
      o2.g.traverse((m) => { if (m.material) m.material.dispose(); });
    });
    objets = [];
  }

  // Les registres d'une même salle s'EMPILENT plutôt que de s'éparpiller : sept
  // registres autour de la Table Peinte, ce sont sept volumes posés côte à côte
  // et en pile, pas sept îlots. C'est ce qu'on voit sur une table de travail.
  function placer(n) {
    const par_pile = 3;
    const i = Math.floor(n / par_pile), k = n % par_pile;
    const a = (i * 2.399);                       // l'angle d'or : ça ne s'aligne pas
    const r = 0.55 + i * 0.30;
    return [Math.cos(a) * r, Math.sin(a) * r, k * 0.085];
  }

  function maj(livres, ou) {
    const liste = (livres || []).filter((b) => b && b.id);
    // Ce qui compte pour cette pièce : ce qui y est POSÉ, et ce que portent les
    // gens qui s'y trouvent. Tout le reste du rayon n'a rien à faire ici.
    const poses = salleId ? liste.filter((b) => b.salle_id === salleId) : [];
    const portes = [];
    for (const b of liste) {
      if (!b.acteur_id || b.salle_id) continue;
      const p = ou ? ou(b.acteur_id) : null;
      if (p) portes.push([b, p]);
    }
    const sig = poses.map((b) => b.id).join("|") + "//"
      + portes.map(([b, p]) => b.id + "@" + p.map((v) => v.toFixed(1)).join(",")).join("|")
      + "//" + base.join(",");
    if (sig === signature) return;
    signature = sig;
    vider();

    const un = (b, x, y, z, couche) => {
      const type = b.type === "carnet" || b.type === "rouleau" ? b.type : "registre";
      const g = new T.Group();
      const corps = new T.Mesh(geo(type), new T.MeshLambertMaterial({
        color: TEINTE[type] || TEINTE.registre,
      }));
      // La tranche : un liseré clair sur le champ, sinon un livre fermé n'est
      // qu'une boîte brune et l'on ne voit pas que c'en est un.
      const [l, p, h] = mesure(type);
      const pages = new T.Mesh(new T.BoxGeometry(l * 0.94, p * 1.01, h * 0.62),
        new T.MeshLambertMaterial({ color: TRANCHE }));
      g.add(corps, pages);
      g.position.set(x, y, z);
      g.rotation.z = (b.id.charCodeAt(0) % 40) / 40 * Math.PI;   // rien n'est d'équerre
      g.traverse((m) => { m.renderOrder = 996; });
      racine.add(g);
      objets.push({ id: b.id, titre: b.titre, g, couche });
    };

    poses.forEach((b, n) => {
      const [dx, dy, dz] = placer(n);
      const x = base[0] + dx, y = base[1] + dy;
      un(b, x, y, sol(x, y) + TABLE_H + dz, "pose");
    });
    portes.forEach(([b, p], n) => {
      // Sous le bras, décalé du corps : un carnet ne pousse pas dans le ventre.
      const a = 2.1 + n * 0.7;
      un(b, p[0] + Math.cos(a) * 0.34, p[1] + Math.sin(a) * 0.34,
         (p[2] || 0) + SOUS_BRAS, "porte");
    });
  }

  return {
    objet: racine,
    maj,
    /** Le joueur a changé de pièce : la pile suit, et change de salle. */
    deplacer(xyz, salle) {
      base = (xyz || base).slice();
      if (salle !== undefined) salleId = salle;
      signature = "";
    },
    montrer(v) { visible = v; racine.visible = v; },
    /** Ce qu'on voit à cette distance — même discipline que les acteurs. */
    suivre(cam) {
      if (!visible) return;
      for (const o2 of objets) {
        const d = o2.g.position.distanceTo(cam.position);
        o2.g.visible = d < PORTEE;
        // Un in-folio fait trente centimètres : passé quinze mètres il tombe
        // sous le pixel. On le grossit un peu plutôt que de le perdre, sans
        // jamais aller jusqu'à en faire un meuble.
        o2.g.scale.setScalar(Math.max(1, Math.min(4, d / 14)));
      }
    },
    /** Ce que la pièce porte en ce moment — pour le dire, et pour le vérifier. */
    etat() {
      return objets.map((o2) => ({ id: o2.id, titre: o2.titre, couche: o2.couche }));
    },
    disposer() {
      vider();
      scene.remove(racine);
      geos.forEach((g) => g.dispose());
      geos.clear();
    },
  };
}
