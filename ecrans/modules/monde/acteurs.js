// monde/acteurs.js — les gens de la salle, dans le décor en volume.
//
// À l'échelle « la salle » (vingt mètres de recul, une pièce dans le cadre),
// le château était habité par personne : la balise du joueur, et le vide. Or
// c'est précisément l'échelle où la question « qui est là ? » se pose, et où
// une pièce vide est un mensonge — il y a douze personnes autour de la Table
// Peinte depuis une heure.
//
// Ce ne sont pas les silhouettes de `foule.js`. La foule est un semis anonyme
// qui dit une densité ; ici on montre des gens NOMMÉS, ceux du bandeau, ceux
// à qui le joueur parle. Trois ou douze, jamais mille : on peut donc se
// permettre un corps par personne et une étiquette par corps.
//
// Deux disciplines, les mêmes que pour la balise du joueur :
//  - Ils traversent la pierre (`depthTest: false`). Une vue plongeante sur une
//    salle voûtée cacherait tout le monde sous son toit.
//  - Ils gardent une taille lisible à l'écran, bornée : à hauteur d'homme un
//    corps fait sa taille d'homme, de plus haut il cesse de rétrécir avant de
//    devenir un pixel.
//
// Le brouillard ne s'applique pas ici, et c'est voulu : on n'affiche que les
// présents de la salle où se tient le joueur — des gens qu'il voit de ses yeux.
"use strict";
import * as T from "/vendor/three.module.min.js";

const HAUT = 1.75;          // un homme debout, en mètres du monde
const LARGE = 0.30;
const PAS = 1.5;            // l'écart entre deux corps de la couronne
// Au-delà, ces gens ne sont plus lisibles et la foule reprend la parole : la
// portée couvre « la salle » et « le château », jamais « la ville ».
const PORTEE = 700;

/** Une couronne de n places, rayon r, autour de l'origine — déterministe. */
function couronne(n, r) {
  if (n <= 1) return [[0, 0]];
  const p = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 - Math.PI / 2;
    p.push([Math.cos(a) * r, Math.sin(a) * r]);
  }
  return p;
}

function nombre(teinte) {
  const s = String(teinte || "").replace("#", "");
  const n = parseInt(s.length === 3 ? s.replace(/./g, (c) => c + c) : s, 16);
  return Number.isFinite(n) ? n : 0x8a7a5a;
}

export function poser(scene, o = {}) {
  const relief = o.relief || null;
  const hote = o.hote || null;
  let base = (o.xyz || [0, 0, 0]).slice();

  const racine = new T.Group();
  racine.renderOrder = 997;
  scene.add(racine);

  // Deux géométries pour tout le monde : le corps et la tête. Douze personnes
  // ne justifient pas d'instancier, mais ne justifient pas non plus douze
  // cylindres distincts en mémoire.
  const gCorps = new T.CylinderGeometry(LARGE * .72, LARGE, HAUT * .78, 10, 1, false);
  gCorps.rotateX(Math.PI / 2);                 // z-up
  gCorps.translate(0, 0, HAUT * .39);
  const gTete = new T.SphereGeometry(LARGE * .62, 12, 8);
  gTete.translate(0, 0, HAUT * .88);

  let corps = [];             // { id, g, el, v }
  let signature = "";
  let visible = true;
  const p = new T.Vector3();

  function sol(x, y) {
    return Math.max(base[2] || 0, relief ? relief.sol(x, y) : 0);
  }

  function vider() {
    corps.forEach((c) => {
      racine.remove(c.g);
      c.g.traverse((m) => { if (m.material) m.material.dispose(); });
      if (c.el) c.el.remove();
    });
    corps = [];
  }

  /**
   * `gens` : [{ id, nom, titre?, joueur? }] — les présents de la salle, dans
   * l'ordre où on veut les voir. Une liste identique à la précédente ne
   * reconstruit rien : on l'appelle à chaque battement du flux.
   */
  function maj(gens) {
    const liste = (gens || []).filter((g) => g && g.id);
    const sig = liste.map((g) => g.id).join("|") + "@" + base.join(",");
    if (sig === signature) return;
    signature = sig;
    vider();
    if (!liste.length) return;

    // Le joueur au centre, les autres autour : c'est sa salle, vue de sa place.
    const joueur = liste.filter((g) => g.joueur);
    const autres = liste.filter((g) => !g.joueur);
    const r = Math.max(PAS, (autres.length * PAS) / (2 * Math.PI));
    const places = couronne(autres.length, r);
    const rangés = joueur.map((g) => [g, [0, 0]])
      .concat(autres.map((g, i) => [g, places[i]]));

    rangés.forEach(([g, [dx, dy]]) => {
      const x = base[0] + dx, y = base[1] + dy;
      const teinte = nombre(window.Taches ? Taches.teinte(g) : null);
      const mat = new T.MeshBasicMaterial({
        color: teinte, transparent: true, opacity: g.joueur ? .95 : .82,
        depthTest: false, depthWrite: false,
      });
      const grp = new T.Group();
      grp.position.set(x, y, sol(x, y));
      grp.add(new T.Mesh(gCorps, mat), new T.Mesh(gTete, mat));
      grp.traverse((m) => { m.renderOrder = 997; });
      racine.add(grp);

      let el = null;
      if (hote) {
        el = document.createElement("span");
        el.className = "monde-acteur";
        if (g.joueur) el.dataset.joueur = "1";
        el.innerHTML = "<b>" + esc(g.nom || g.id) + "</b>" +
          (g.titre ? "<i>" + esc(g.titre) + "</i>" : "");
        // Penser à quelqu'un depuis le décor : le même canal que le fil et le
        // plan du château — on ne rouvre pas un second chemin pour la 3D.
        el.addEventListener("click", () => {
          if (window.Entites) Entites.penser(g.id, "personnage", g.nom || g.id);
        });
        hote.appendChild(el);
      }
      corps.push({ id: g.id, g: grp, el, dx, dy,
                   v: new T.Vector3(x, y, sol(x, y) + HAUT) });
    });
  }

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  return {
    objet: racine,
    maj,
    /** Le joueur a changé de salle ou de château : la couronne suit. */
    deplacer(xyz) { base = (xyz || base).slice(); signature = ""; },
    /**
     * Où se tient CETTE personne, si elle est dans la pièce. Rien sinon — et
     * c'est la réponse utile : ce que quelqu'un porte ne se voit pas quand il
     * n'est pas là. `livres.js` s'en sert pour poser un carnet sous un bras.
     */
    ou(id) {
      const c = corps.find((x) => x.id === id);
      return c ? [c.g.position.x, c.g.position.y, c.g.position.z] : null;
    },
    montrer(v) {
      visible = v; racine.visible = v;
      corps.forEach((c) => { if (c.el) c.el.style.display = v ? "" : "none"; });
    },
    suivre(cam, largeur, hauteur) {
      if (!visible) return;
      // Une taille d'écran bornée : de près, un homme fait un homme ; de loin,
      // il cesse de rétrécir plutôt que de disparaître. Au-delà de la salle,
      // ces gens n'ont plus rien à dire et s'effacent — c'est la foule qui
      // reprend la parole à cette hauteur-là.
      for (const c of corps) {
        const d = c.g.position.distanceTo(cam.position);
        const s = Math.max(1, Math.min(9, d / 22));
        c.g.scale.setScalar(s);
        // La couronne s'ouvre du même facteur que les corps. Sans cela, six
        // personnes à un mètre cinquante l'une de l'autre se superposent en un
        // seul point dès qu'on prend deux cents mètres de recul : on verrait
        // qu'il y a quelqu'un, jamais combien.
        c.g.position.set(base[0] + c.dx * s, base[1] + c.dy * s, 0);
        c.g.position.z = sol(c.g.position.x, c.g.position.y);
        const dedans = d < PORTEE;
        c.g.visible = dedans;
        if (!c.el) continue;
        if (!dedans) { c.el.style.display = "none"; continue; }
        c.v.set(c.g.position.x, c.g.position.y, c.g.position.z + HAUT * s);
        p.copy(c.v).project(cam);
        const dans = p.z < 1 && Math.abs(p.x) < 1.1 && Math.abs(p.y) < 1.1;
        if (!dans) { c.el.style.display = "none"; continue; }
        c.el.style.display = "";
        c.el.style.opacity = String(Math.min(1, (PORTEE - d) / 220));
        c.el.style.left = ((p.x + 1) / 2 * largeur) + "px";
        c.el.style.top = ((1 - p.y) / 2 * hauteur) + "px";
      }
    },
    disposer() {
      vider();
      scene.remove(racine);
      gCorps.dispose(); gTete.dispose();
    },
  };
}
