// monde/reperes.js — les noms qui flottent sur la ville.
//
// Des étiquettes HTML posées au-dessus du canevas, projetées à chaque image.
// Pas des sprites : le texte reste net à toute distance, se lit comme le reste
// de l'interface, et coûte une multiplication de matrice par nom.
//
// Elles disparaissent quand on approche : à trois cents mètres, on n'a plus
// besoin qu'on nous dise où est le Donjon Rouge, on le voit. C'est encore une
// façon de dire l'échelle — les noms sont l'échelle des cartes, pas celle des
// rues.
//
// Et elles ne se montrent QUE sous le curseur. Cinquante noms posés en
// permanence font un semis de texte à travers lequel on ne voit plus la ville :
// on regarde une légende, pas un lieu. Le pointeur en élit UN — le plus proche
// dans un rayon de quelques dizaines de pixels — et le reste se tait. C'est la
// même règle que partout ailleurs : on montre ce qu'on interroge, pas tout.
"use strict";
import * as T from "/vendor/three.module.min.js";

// Rayon de saisie, en pixels d'écran : au-delà, le curseur ne désigne personne.
const RAYON = 70;

export function poser(hote, reperes, relief, opts = {}) {
  const haut = opts.haut ?? 40;
  const marques = (reperes || []).map((r) => {
    const el = document.createElement("span");
    el.textContent = r.nom;
    el.dataset.genre = r.genre;
    hote.appendChild(el);
    const z = Math.max(r.xyz[2], relief ? relief.sol(r.xyz[0], r.xyz[1]) : 0);
    return { el, genre: r.genre, v: new T.Vector3(r.xyz[0], r.xyz[1], z + haut) };
  });

  const p = new T.Vector3();
  let visible = true;

  // Où est le curseur, en pixels du cadre. L'hôte des étiquettes est en
  // `pointer-events:none` : on écoute donc sur son parent (le cadre du monde),
  // et l'on ramène la position dans son repère. Souris sortie : plus rien.
  const cadre = opts.cible || hote.parentElement || hote;
  let sx = -1e4, sy = -1e4;
  const bouger = (e) => {
    const r = hote.getBoundingClientRect();
    sx = e.clientX - r.left; sy = e.clientY - r.top;
  };
  const partir = () => { sx = sy = -1e4; };
  cadre.addEventListener("pointermove", bouger);
  cadre.addEventListener("pointerleave", partir);

  return {
    marques,
    montrer(v) { visible = v; hote.style.display = v ? "" : "none"; },
    suivre(cam, largeur, hauteur) {
      if (!visible) return;
      // Premier passage : qui est à l'écran, et à quelle distance du curseur.
      let elu = null, meilleure = RAYON * RAYON;
      for (const m of marques) {
        p.copy(m.v).project(cam);
        const d = m.v.distanceTo(cam.position);
        const dans = p.z < 1 && Math.abs(p.x) < 1.05 && Math.abs(p.y) < 1.05;
        // trop loin : la brume l'a mangé. Trop près : on n'en a plus besoin.
        const bonne = d > 240 && d < 9000;
        m.x = (p.x + 1) / 2 * largeur;
        m.y = (1 - p.y) / 2 * hauteur;
        m.d = d;
        m.offert = dans && bonne;
        if (!m.offert) continue;
        const dx = m.x - sx, dy = m.y - sy;
        const q = dx * dx + dy * dy;
        if (q < meilleure) { meilleure = q; elu = m; }
      }
      // Second passage : un seul nom paraît, celui qu'on désigne.
      for (const m of marques) {
        if (m !== elu) { if (m.el.style.display !== "none") m.el.style.display = "none"; continue; }
        m.el.style.display = "";
        m.el.style.opacity = String(Math.min(1, (m.d - 240) / 400) *
                                    Math.min(1, (9000 - m.d) / 2500));
        m.el.style.left = m.x + "px";
        m.el.style.top = m.y + "px";
      }
    },
    disposer() {
      cadre.removeEventListener("pointermove", bouger);
      cadre.removeEventListener("pointerleave", partir);
      for (const m of marques) m.el.remove();
    },
  };
}
