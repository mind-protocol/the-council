// monde/marques.js — les noms et les positions de ce qui est ACTIF, en volume.
//
// La table peinte porte cinquante jetons : quinze têtes, cinq osts, une flotte,
// deux dragons, quatre incidents, six desseins, trois oreilles. Le volume n'en
// montrait aucun. Un joueur qui bascule de la carte au monde perdait d'un coup
// tout ce qu'il savait de qui est où — et c'est précisément ce qu'il regarde
// pour décider.
//
// ── ON NE RECALCULE PAS LE BROUILLARD ────────────────────────────────────────
// La tentation était de lire `etat/vues.json` et `intentions.json` depuis la
// page. C'est interdit et ce serait faux : `intentions.json` ne doit JAMAIS
// atteindre le joueur, et une position vient de ce qu'il CROIT, jamais de
// `personnages.lieu_id`.
//
// Le serveur fait déjà ce travail, et bien : `/carte` projette les têtes depuis
// `vues.json`, vieillit leur certitude jour par jour, laisse tomber celles qu'on
// ne sait plus, et écrit la provenance en clair — « il y a 4 jours — de vos
// yeux — votre époux ». On consomme cette sortie telle quelle. Une seule
// autorité pour le brouillard, et c'est le serveur.
//
// ── DEUX PLACEMENTS, PARCE QU'IL Y A DEUX CAS ────────────────────────────────
// Un jeton porte une PLACE (`ou`), pas des mètres. Or le monde en volume fait
// cinq kilomètres et le royaume en fait quinze cents.
//
//   ICI     — la place du jeton est celle où l'on se tient : la marque se pose
//             sur le lieu, dans le monde, et l'on peut aller y voir.
//   AILLEURS— la place est hors du fichier : la marque se pose sur l'HORIZON,
//             au cap vrai que donne `Geo.lieux`, avec le nom de la place. On ne
//             fait pas semblant d'y aller ; on dit de quel côté c'est.
//
// C'est la même règle que pour les corbeaux : ce qui est trop loin ne se
// simule pas, il s'indique.
"use strict";
import * as T from "/vendor/three.module.min.js";

const HORIZON = 3400;     // où se posent les marques du lointain, en mètres
const HAUT_ICI = 90;      // ce qu'une marque d'ici flotte au-dessus du sol
const HAUT_LOIN = 260;

// Ce qu'on montre, et dans quel ordre de préséance quand la place est encombrée.
// Un dessein et une tête ne pèsent pas pareil : l'un dit ce qui va se faire,
// l'autre où quelqu'un se trouve.
const GENRES = {
  tete:     { rang: 1, signe: "" },
  dragon:   { rang: 0, signe: "▲" },
  armee:    { rang: 2, signe: "✦" },
  flotte:   { rang: 2, signe: "≈" },
  camp:     { rang: 3, signe: "⌂" },
  garnison: { rang: 3, signe: "▣" },
  incident: { rang: 1, signe: "!" },
  dessein:  { rang: 4, signe: "→" },
  oreille:  { rang: 4, signe: "◦" },
};

// La certitude se VOIT : ce qu'on tient de ses yeux n'a pas le poids d'une
// rumeur de taverne, et le décor doit le dire sans qu'on lise le détail.
const CERTITUDE = { sure: 1, rapportee: 0.72, rumeur: 0.45 };

export function poser(scene, hote, o = {}) {
  let ici = o.lieu || null;
  let ancre = (o.xyz || [0, 0, 0]).slice();   // où se pose ce qui est « ici »
  const relief = o.relief || null;

  let marques = [];
  let signature = "";
  let visible = true;
  let genresMontres = null;                   // null = tous
  const p = new T.Vector3();
  const v = new T.Vector3();

  const esc = (s) => String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  /** Le cap d'ici vers cette place, en radians du monde. */
  function cap(place) {
    const G = window.Geo && window.Geo.lieux;
    if (!G || !ici || !G[ici] || !G[place]) return null;
    const a = G[ici], b = G[place];
    const ax = a.p ? a.p[0] : a[0], ay = a.p ? a.p[1] : a[1];
    const bx = b.p ? b.p[0] : b[0], by = b.p ? b.p[1] : b[1];
    if (ax === bx && ay === by) return null;
    // y descend vers le sud sur la carte, il monte vers le nord dans le monde.
    return { rad: Math.atan2(-(by - ay), bx - ax),
             loin: Math.hypot(bx - ax, by - ay) };
  }

  function vider() {
    marques.forEach((m) => m.el.remove());
    marques = [];
  }

  /**
   * `jetons` : le tableau servi par `/carte`, tel quel.
   * `lieux` : la table des noms de place, pour écrire « à Port-Réal » en clair.
   */
  function maj(jetons, lieux) {
    const bons = (jetons || []).filter((j) => j && GENRES[j.genre]);
    const sig = bons.map((j) => j.id + ":" + j.ou + ":" + j.certitude).join("|")
      + "@" + ici + "@" + ancre.join(",");
    if (sig === signature) return;
    signature = sig;
    vider();
    const noms = {};
    (lieux || []).forEach((l) => { noms[l.id] = l.nom || l.id; });

    // On empile ce qui partage une place, sinon quinze têtes de Port-Réal se
    // superposent en un seul mot illisible.
    const parPlace = new Map();
    bons.forEach((j) => {
      const k = j.ou || "?";
      if (!parPlace.has(k)) parPlace.set(k, []);
      parPlace.get(k).push(j);
    });

    for (const [place, liste] of parPlace) {
      liste.sort((a, b) => GENRES[a.genre].rang - GENRES[b.genre].rang);
      const dedans = place === ici;
      const c = dedans ? null : cap(place);
      // Une place qu'on ne sait pas situer ne s'invente pas : on la tait.
      if (!dedans && !c) continue;
      liste.forEach((j, n) => {
        const g = GENRES[j.genre];
        let x, y, z;
        if (dedans) {
          x = ancre[0]; y = ancre[1];
          z = (relief ? relief.sol(x, y) : ancre[2] || 0) + HAUT_ICI + n * 26;
        } else {
          x = ancre[0] + Math.cos(c.rad) * HORIZON;
          y = ancre[1] + Math.sin(c.rad) * HORIZON;
          z = (relief ? relief.sol(x, y) : 0) + HAUT_LOIN + n * 34;
        }
        const el = document.createElement("div");
        el.className = "monde-marque" + (dedans ? " ici" : " loin")
          + " certitude-" + (j.certitude || "sure") + " genre-" + j.genre;
        el.innerHTML =
          '<b>' + esc((g.signe ? g.signe + " " : "") + (j.nom || j.id)) + '</b>'
          + (dedans ? "" : '<i>' + esc(noms[place] || place) + '</i>')
          + (j.detail ? '<em>' + esc(j.detail) + '</em>' : "");
        el.style.opacity = String(CERTITUDE[j.certitude] ?? 1);
        hote.appendChild(el);
        marques.push({ j, el, pos: new T.Vector3(x, y, z), dedans, place });
      });
    }
  }

  return {
    maj,
    /** On a bougé, ou changé de lieu : tout se recalcule. */
    situer(o2 = {}) {
      if (o2.lieu !== undefined) ici = o2.lieu;
      if (o2.xyz) ancre = o2.xyz.slice();
      signature = "";
    },
    /** N'afficher que certains genres — la même idée que les filtres de la table. */
    filtrer(genres) { genresMontres = genres ? new Set(genres) : null; signature = ""; },
    montrer(vis) {
      visible = vis;
      marques.forEach((m) => { m.el.style.display = vis ? "" : "none"; });
    },
    /** Projeter les étiquettes, à chaque image. */
    suivre(cam, largeur, hauteur) {
      if (!visible) return;
      for (const m of marques) {
        if (genresMontres && !genresMontres.has(m.j.genre)) {
          m.el.style.display = "none"; continue;
        }
        v.copy(m.pos);
        p.copy(v).project(cam);
        const dans = p.z < 1 && Math.abs(p.x) < 1.15 && Math.abs(p.y) < 1.15;
        if (!dans) { m.el.style.display = "none"; continue; }
        m.el.style.display = "";
        m.el.style.left = ((p.x + 1) / 2 * largeur) + "px";
        m.el.style.top = ((1 - p.y) / 2 * hauteur) + "px";
      }
    },
    /** Ce qui est affiché — pour le dire, et pour vérifier. */
    etat() {
      return marques.map((m) => ({
        id: m.j.id, genre: m.j.genre, nom: m.j.nom, place: m.place,
        ou: m.dedans ? "ici" : "horizon", certitude: m.j.certitude,
      }));
    },
    disposer() { vider(); },
  };
}
