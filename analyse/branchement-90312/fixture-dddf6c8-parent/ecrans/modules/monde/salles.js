// monde/salles.js — les noms des salles, posés sur les salles.
//
// Les repères (reperes.js) sont les noms que la VILLE porte : les portes, les
// collines, le Dragonmont. Ils viennent du graphe, ils se lisent de loin, et
// ils s'effacent quand on approche — à trois cents mètres on voit la chose,
// on n'a plus besoin qu'on la nomme.
//
// L'échelle « le quartier » est justement en deçà de ce seuil, et il n'y
// restait donc plus un seul nom : une place forte de six cent cinquante mètres,
// trente-quatre pièces, et rien qui dise laquelle est laquelle. Ce module est
// l'autre moitié — les noms du DEDANS, pris là où ils sont vrais.
//
// Trois disciplines, et elles expliquent tout le fichier :
//  - **Les mètres viennent des intérieurs, jamais du graphe.** Les nœuds du
//    graphe qui portent des noms de salles sont posés sur un anneau autour de
//    la cour et tombent à cent mètres des pièces réelles ; `interieurs.json`
//    sait où est chaque dalle, parce que c'est lui qui les a creusées. Une
//    étiquette qui n'est pas sur sa pièce est pire qu'une pièce sans étiquette.
//  - **On centre sur la pièce, on ne la surplombe pas.** À la verticale d'un
//    plan, un nom se pose SUR ce qu'il nomme (`translate(-50%,-50%)`) — le
//    fanion au-dessus du point est la grammaire d'une balise, pas d'une carte.
//  - **Aucun nom n'en recouvre un autre.** On les place par ordre
//    d'importance, chacun cherche sa place autour de son point, et celui qui
//    n'en trouve pas se tait. Un semis de texte superposé ne nomme plus rien.
"use strict";
import * as T from "/vendor/three.module.min.js";

// Les bandes de distance, en mètres de caméra à la pièce.
const PRES = 40;      // dedans, ou à la porte : la pièce se voit, le nom gêne
const LOIN = 1500;    // l'île entière dans le cadre : une salle n'y tient plus
// En deçà de quoi les pièces ordinaires paraissent. Au-delà, seules les grandes
// — c'est le même dégradé que partout : on nomme ce qu'on peut encore lire.
const MENUES = 800;

// Les places qu'un nom essaie, dans l'ordre, autour de son point. Rien d'abord :
// le bon endroit est le milieu de la pièce. Puis dessus, dessous, de côté, en
// biais — de quoi démêler une chambre du sommet d'avec le donjon qui la porte.
//
// Et JAMAIS plus loin. On a essayé les pas doubles : « Vos appartements » se
// retrouvait à soixante-dix pixels de la chambre, c'est-à-dire posé sur la
// roukerie. Un nom déplacé de trop ne nomme plus sa pièce, il en nomme une
// autre — et un nom qui ment est pire qu'une pièce anonyme. Quand aucune des
// neuf places ne va, le nom se tait ; c'est la bonne réponse.
const ESSAIS = [[0, 0], [0, -1], [0, 1], [-1, 0], [1, 0],
                [-1, -1], [1, -1], [-1, 1], [1, 1]];
const MARGE = 2;      // pixels de blanc exigés entre deux noms
// Le déport latéral se mesure sur la pièce elle-même, pas sur l'étiquette : le
// donjon fait soixante pixels de large et supporte qu'on le pousse, une
// antichambre en fait huit et n'en supporte aucun.
const DEPORT_MIN = 10, DEPORT_MAX = 32;

// Un nom large tient moins de places qu'un nom haut : à cette échelle, la
// place forte fait deux cents pixels de large et cinquante de haut, et c'est
// l'horizontale qui manque. On recoupe donc les lignes trop longues en deux
// moitiés à peu près égales, sur un blanc — « La grande salle » sur deux
// lignes se case là où la même en une seule se tait.
const LARGE = 13;

function couper(lignes) {
  const out = [];
  for (const t of lignes) {
    if (t.length <= LARGE || t.indexOf(" ") < 0) { out.push(t); continue; }
    // La coupe la plus proche du milieu, pour deux lignes de même poids.
    let coupe = -1;
    for (let i = 0; i < t.length; i++) {
      if (t[i] !== " ") continue;
      if (coupe < 0 || Math.abs(i - t.length / 2) < Math.abs(coupe - t.length / 2)) coupe = i;
    }
    if (coupe < 0) { out.push(t); continue; }
    out.push(t.slice(0, coupe), t.slice(coupe + 1));
  }
  return out;
}

export function poser(hote, salles, opts = {}) {
  const plan = opts.plan || null;
  const parId = {};
  ((plan && plan.salles) || []).forEach((s) => { parId[s.id] = s; });

  const marques = (salles || []).map((s) => {
    const p = parId[s.id] || {};
    const el = document.createElement("span");
    el.className = "monde-salle";
    el.dataset.salle = s.id;
    // Le plan de château a déjà coupé chaque nom pour qu'il tienne dans sa
    // forme (« La Table / Peinte ») : c'est la forme carte du nom, et elle
    // vaut mieux ici qu'un intitulé d'une seule ligne large de cent pixels.
    const lignes = couper((p.lignes && p.lignes.length) ? p.lignes : [s.nom]);
    el.innerHTML = lignes.map((t) => "<b>" + t + "</b>").join("");
    if (p.cle) el.dataset.cle = "1";
    if (p.dehors) el.dataset.dehors = "1";
    hote.appendChild(el);

    const b = s.boite || [];
    const aire = (b.length === 4) ? (b[2] - b[0]) * (b[3] - b[1]) : 0;
    // Le milieu de la pièce, à mi-hauteur : à quatorze degrés de biais, c'est
    // le milieu de sa MASSE à l'écran, et pas le milieu de son plancher.
    const z = (s.sol_z != null ? s.sol_z : s.centre[2]) + (s.hauteur || 0) / 2;
    return {
      el, id: s.id, aire, cle: !!p.cle,
      sol: s.sol_z != null ? s.sol_z : s.centre[2],
      v: new T.Vector3(s.centre[0], s.centre[1], z),
      // Un coin de sa boîte, à la même hauteur : projeté avec le milieu, il
      // donne à chaque image la taille de la pièce EN PIXELS — la seule mesure
      // qui dise de combien on peut la pousser.
      coin: new T.Vector3(b.length === 4 ? b[2] : s.centre[0],
                          b.length === 4 ? b[3] : s.centre[1], z),
      w: 0, h: 0,
    };
  });

  // L'ordre de préséance : les salles clefs d'abord — celles que le plan de
  // château tient pour dignes de garder leur nom, le donjon, la Table Peinte,
  // la grande salle. Puis la pièce où l'on SE TIENT, qui passe devant les
  // pièces ordinaires sans passer devant le donjon : la balise d'or répond
  // déjà « où suis-je ? », le nom de la place forte n'a rien qui le supplée.
  // Puis les hautes avant les basses, parce qu'un cellier est SOUS la salle
  // qu'il sert et que c'est celle du dessus qu'on regarde. Puis les grandes.
  const rang = (m) => (m.cle ? 0 : (m.id === ou ? 1 : 2));
  const ordre = marques.slice();
  const reclasser = () => ordre.sort((a, b) =>
    (rang(a) - rang(b)) || (b.sol - a.sol) || (b.aire - a.aire));

  const p = new T.Vector3();
  const q = new T.Vector3();
  let visible = false;
  let mesure = false;
  let ou = null;                 // la pièce où se tient le joueur
  reclasser();

  // La taille de chaque étiquette, mesurée une fois pour toutes : elle ne
  // dépend que du texte et de la feuille de style, jamais du cadrage. On la
  // prend au premier passage visible — avant, l'hôte est caché et tout mesure
  // zéro.
  function mesurer() {
    let bon = true;
    for (const m of marques) {
      const d = m.el.style.display;
      m.el.style.display = "";
      m.el.style.visibility = "hidden";
      m.w = m.el.offsetWidth; m.h = m.el.offsetHeight;
      m.el.style.visibility = "";
      m.el.style.display = d;
      if (!m.w) bon = false;
    }
    return bon;
  }

  return {
    marques,
    montrer(v) {
      visible = v;
      if (!v) for (const m of marques) m.el.style.display = "none";
    },
    /** La pièce où se tient le joueur : elle se distingue, et elle passe devant. */
    ici(id) {
      if (id === ou) return;
      ou = id;
      for (const m of marques) {
        const est = (m.id === id) ? "1" : "";
        if (m.el.dataset.ici !== est) m.el.dataset.ici = est;
      }
      reclasser();
    },
    suivre(cam, largeur, hauteur) {
      if (!visible) return;
      if (!mesure) mesure = mesurer();

      // Premier passage : qui est dans le cadre, à quelle distance, et de
      // quelle taille il paraît.
      for (const m of marques) {
        p.copy(m.v).project(cam);
        q.copy(m.coin).project(cam);
        const d = m.v.distanceTo(cam.position);
        const dans = p.z < 1 && Math.abs(p.x) < 1.1 && Math.abs(p.y) < 1.1;
        const bonne = d > PRES && d < LOIN && (m.cle || d < MENUES);
        m.x = (p.x + 1) / 2 * largeur;
        m.y = (1 - p.y) / 2 * hauteur;
        m.rayon = Math.hypot((q.x - p.x) / 2 * largeur, (q.y - p.y) / 2 * hauteur);
        m.d = d;
        m.offert = dans && bonne;
      }

      // Second passage : chacun son tour, par préséance, chacun cherche une
      // place libre autour de son point. Qui n'en trouve pas ne paraît pas —
      // c'est ce qui fait qu'on peut tous les allumer sans noyer la vue.
      const prises = [];
      for (const m of ordre) {
        let pose = null;
        if (m.offert && m.w) {
          // Le pas vertical est d'une ligne : monter ou descendre d'un cran
          // garde le nom dans la colonne de sa pièce, et c'est ainsi qu'on
          // démêle deux étages. Le pas latéral, lui, est borné par la pièce.
          const dy = m.h + MARGE;
          const dx = Math.min(m.w / 2 + 8,
                              Math.max(DEPORT_MIN, Math.min(DEPORT_MAX, m.rayon)));
          for (const [ex, ey] of ESSAIS) {
            const cx = m.x + ex * dx, cy = m.y + ey * dy;
            const b = [cx - m.w / 2 - MARGE, cy - m.h / 2 - MARGE,
                       cx + m.w / 2 + MARGE, cy + m.h / 2 + MARGE];
            if (b[0] < 0 || b[1] < 0 || b[2] > largeur || b[3] > hauteur) continue;
            if (prises.some((r) => b[0] < r[2] && b[2] > r[0] &&
                                   b[1] < r[3] && b[3] > r[1])) continue;
            prises.push(b); pose = [cx, cy]; break;
          }
        }
        if (!pose) { if (m.el.style.display !== "none") m.el.style.display = "none"; continue; }
        m.el.style.display = "";
        m.el.style.left = pose[0] + "px";
        m.el.style.top = pose[1] + "px";
        // On s'efface aux deux bords de la bande, pour que l'apparition d'un
        // nom soit une venue et non un clignotement.
        m.el.style.opacity = String(Math.min(1, (m.d - PRES) / 60) *
                                    Math.min(1, (LOIN - m.d) / 500));
      }
    },
    disposer() { for (const m of marques) m.el.remove(); },
  };
}
