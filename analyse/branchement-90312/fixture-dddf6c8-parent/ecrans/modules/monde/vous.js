// monde/vous.js — où se tient le joueur, sur le relief.
//
// À quatre cents mètres d'altitude, une place forte fait cent pixels et le
// joueur n'y est nulle part : l'échelle « la ville » montrait un beau caillou
// dont rien ne disait qu'on était DEDANS. C'est la seule marque du décor en
// volume qui ne représente pas une chose du monde mais une chose du joueur —
// d'où sa forme : une balise, pas un bâtiment.
//
// Deux disciplines :
//  - Elle traverse la pierre (`depthTest: false`). Une marque qu'un flanc de
//    Dragonmont peut cacher ne répond plus à la question qu'on lui pose, et la
//    question — « où suis-je ? » — n'a pas de réponse à moitié.
//  - Elle ne rétrécit pas avec la distance. Le halo et le fanion se remettent à
//    l'échelle du recul à chaque image : de la rade au chemin de ronde, la
//    balise garde la même taille à l'écran, parce que c'est un repère
//    d'interface et non un objet posé sur le sol.
"use strict";
import * as T from "/vendor/three.module.min.js";

const OR = 0xf0c860;

export function poser(scene, o = {}) {
  const [x, y] = o.xyz || [0, 0, 0];
  const relief = o.relief || null;
  const zsol = Math.max((o.xyz || [0, 0, 0])[2] || 0,
                        relief ? relief.sol(x, y) : 0);

  const g = new T.Group();
  g.position.set(x, y, zsol);
  g.renderOrder = 998;

  const feu = (op) => new T.MeshBasicMaterial({
    color: OR, transparent: true, opacity: op, depthTest: false,
    depthWrite: false, blending: T.AdditiveBlending, side: T.DoubleSide,
  });

  // Le halo au sol : un anneau couché, qui dit l'endroit exact.
  const anneau = new T.Mesh(new T.RingGeometry(16, 22, 48), feu(0.85));
  anneau.position.z = 1;
  // Le second, plus large et plus pâle, respire — c'est ce qui accroche l'œil
  // sans qu'on ait à clignoter, ce qu'une carte ne se permet jamais.
  const onde = new T.Mesh(new T.RingGeometry(22, 25, 48), feu(0.4));
  onde.position.z = 1;

  // Le rai vertical : de loin, l'anneau fait trois pixels et disparaît dans la
  // roche ; c'est la colonne qu'on voit, et elle plante le lieu dans le relief.
  const rai = new T.Mesh(new T.CylinderGeometry(2.2, 6.5, 120, 10, 1, true), feu(0.32));
  rai.geometry.rotateX(Math.PI / 2);      // z-up : la hauteur suit z, pas y
  rai.geometry.translate(0, 0, 60);

  g.add(anneau, onde, rai);
  g.traverse((m) => { m.renderOrder = 998; });
  scene.add(g);

  // Le fanion : deux lignes de texte HTML, comme les repères — net à toute
  // distance, et lisible comme le reste de l'interface.
  let el = null, dernierNom = o.nom || "";
  if (o.hote) {
    el = document.createElement("span");
    el.className = "monde-vous";
    el.innerHTML = '<b>Vous êtes ici</b>' + (o.nom ? '<i>' + o.nom + '</i>' : '');
    o.hote.appendChild(el);
  }

  const p = new T.Vector3();
  const sommet = new T.Vector3();
  let visible = true;

  return {
    objet: g,
    /** Là où le joueur se tient a changé de château. */
    deplacer(xyz) {
      const z = Math.max(xyz[2] || 0, relief ? relief.sol(xyz[0], xyz[1]) : 0);
      g.position.set(xyz[0], xyz[1], z);
    },
    /** La salle où il se tient — elle change plus souvent que le lieu. */
    nommer(nom) {
      if (!el || nom === dernierNom) return;
      dernierNom = nom;
      el.innerHTML = '<b>Vous êtes ici</b>' + (nom ? '<i>' + nom + '</i>' : '');
    },
    montrer(v) {
      visible = v; g.visible = v;
      if (el) el.style.display = v ? "" : "none";
    },
    suivre(cam, largeur, hauteur) {
      if (!visible) return;
      const d = g.position.distanceTo(cam.position);
      // Taille constante à l'écran : le rayon du halo suit le recul. Borné, pour
      // qu'une vue à hauteur d'homme ne fasse pas un anneau de trois mètres.
      const s = Math.max(0.12, Math.min(9, d / 700));
      anneau.scale.setScalar(s); rai.scale.set(s, s, s);
      const t = performance.now() / 1000;
      const bat = 1 + 0.35 * (1 + Math.sin(t * 2.2)) / 2;
      onde.scale.setScalar(s * bat);
      onde.material.opacity = 0.42 * (1 - (bat - 1) / 0.35 * 0.8);
      if (!el) return;
      // Le fanion s'accroche au SOL, pas au sommet du rai : à taille d'écran
      // constante, le sommet sort du cadre dès que la vue est serrée, et le
      // fanion s'en allait avec lui. On monte ensuite de quelques pixels, en
      // CSS, ce qui ne dépend d'aucune distance.
      sommet.copy(g.position);
      p.copy(sommet).project(cam);
      if (p.z >= 1) { el.style.display = "none"; return; }   // derrière la caméra
      el.style.display = "";
      // Et on le retient dans le cadre : une balise qui répond « où suis-je ? »
      // ne peut pas être la seule chose que le cadrage ait le droit de perdre.
      // Hors champ, elle se colle au bord du côté où il faut aller.
      const cx = (p.x + 1) / 2 * largeur, cy = (1 - p.y) / 2 * hauteur;
      el.style.left = Math.max(46, Math.min(largeur - 46, cx)) + "px";
      el.style.top = Math.max(30, Math.min(hauteur - 8, cy)) + "px";
      el.dataset.hors = (cx < 0 || cx > largeur || cy < 0 || cy > hauteur) ? "1" : "";
    },
    disposer() {
      scene.remove(g);
      g.traverse((m) => {
        if (m.geometry) m.geometry.dispose();
        if (m.material) m.material.dispose();
      });
      if (el) el.remove();
    },
  };
}
