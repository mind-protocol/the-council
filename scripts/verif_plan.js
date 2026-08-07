// verif_plan.js — les plans de chateau, mesures et non regardes.
//
// Une salle ajoutee a la main dans ecrans/modules/plans.js casse en silence :
// deux noms qui se marchent dessus ne font pas d'erreur, ils font une carte
// illisible — et on ne s'en apercoit qu'au deplie, des semaines plus tard. Ce
// script projette les boites de tous les noms (corps x 1.13 d'interligne,
// ~0.52 de chasse moyenne, la meme geometrie que nomSalle dans plan.js) et
// cherche les recouvrements, a la largeur voulue.
//
// Il verifie aussi la structure : ornements declares mais inexistants dans
// plan.js, ids ou motifs en double, champs manquants, salles qu'aucune arete
// de etat/chemins.json ne relie (une salle sans chemin est une salle morte :
// personne ne peut y aller, donc personne n'y sera jamais).
//
// Le SEUIL_TOUS de plan.js (520 px) est la largeur en-dessous de laquelle on
// n'ecrit plus que les salles `cle` : c'est donc la plus petite largeur ou
// TOUS les noms s'affichent, et la seule qui doive etre sans collision.
//
// Usage :
//   node scripts/verif_plan.js                 — tous les chateaux, a 520 px
//   node scripts/verif_plan.js 800             — a une autre largeur
//   node scripts/verif_plan.js 520 peyredragon — un seul chateau
"use strict";
const fs = require("fs");
const path = require("path");

const RACINE = path.dirname(__dirname);
global.window = {};
require(path.join(RACINE, "ecrans", "modules", "plans.js"));

const SEUIL_TOUS = 520;          // doit suivre plan.js
const CIBLE = 11.5;              // px reels visés par nomSalle (grand)
const CHASSE = 0.52;             // largeur moyenne d'un caractere

const LARGE = Number(process.argv[2]) || SEUIL_TOUS;
const SEUL = process.argv[3] || null;

const srcPlan = fs.readFileSync(
  path.join(RACINE, "ecrans", "modules", "plan.js"), "utf-8");
let aretes = [];
try {
  aretes = JSON.parse(fs.readFileSync(
    path.join(RACINE, "etat", "chemins.json"), "utf-8")).aretes || [];
} catch (e) { /* pas de chemins : on ne reproche rien */ }
const relie = new Set();
aretes.forEach((a) => { relie.add(a[0]); relie.add(a[1]); });

// La boite englobante d'une forme. Grossiere pour un cercle — d'ou l'avis
// « a verifier a l'oeil » plutot qu'une erreur : deux cercles voisins se
// touchent par les coins de leurs boites sans se toucher vraiment.
function boite(s) {
  const f = s.forme;
  if (f.c) return [f.c[0] - f.c[2], f.c[1] - f.c[2], f.c[0] + f.c[2], f.c[1] + f.c[2]];
  if (f.r) return [f.r[0], f.r[1], f.r[0] + f.r[2], f.r[1] + f.r[3]];
  const n = String(f.d || "").match(/-?\d+(\.\d+)?/g).map(Number);
  const xs = [], ys = [];
  for (let i = 0; i + 1 < n.length; i += 2) { xs.push(n[i]); ys.push(n[i + 1]); }
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}
const croise = (a, b) => Math.min(a[2], b[2]) - Math.max(a[0], b[0]) > 1 &&
                         Math.min(a[3], b[3]) - Math.max(a[1], b[1]) > 1;

let fautes = 0, avis = 0;
const dire = (m) => { console.log("  " + m); fautes++; };

for (const [nom, p] of Object.entries(window.Plans)) {
  if (SEUL && nom !== SEUL) continue;
  const vbL = parseFloat(p.viewBox.split(/\s+/)[2]);
  const ech = LARGE / vbL, police = CIBLE / ech, inter = police * 1.13;

  console.log("\n=== " + nom + " — " + p.salles.length + " salles, a " + LARGE + " px ===");

  // --- structure
  const ids = new Set(), motifs = new Map();
  p.salles.forEach((s) => {
    if (ids.has(s.id)) dire("id en double : " + s.id);
    ids.add(s.id);
    if (!s.forme || !s.etiq) dire(s.id + " : forme ou etiq manquante");
    if (!s.quoi) dire(s.id + " : pas de `quoi` (l'infobulle sera muette)");
    if (s.orne && !srcPlan.includes("O." + s.orne[0] + " =")) {
      dire(s.id + " : ornement inconnu de plan.js — " + s.orne[0]);
    }
    (s.motifs || []).forEach((m) => {
      if (motifs.has(m)) dire("motif en double : " + JSON.stringify(m) +
        " (" + motifs.get(m) + " et " + s.id + ")");
      motifs.set(m, s.id);
    });
  });

  // --- chemins : une salle sans arete ne se visite pas. Mais un chateau dont
  // AUCUNE salle n'est cablee n'est pas fautif, il est neuf : on le signale une
  // fois. La vraie faute est la salle oubliee dans un chateau deja cable —
  // celle-la se visite sur la carte et nulle part dans le moteur.
  if (aretes.length) {
    const dedans = p.salles.filter((s) => !s.fond);
    const orphelines = dedans.filter((s) => !relie.has(s.id));
    if (orphelines.length === dedans.length) {
      console.log("  avis — aucun chemin pour ce chateau : etat/chemins.json " +
        "ne le connait pas encore (personne ne peut y circuler).");
      avis++;
    } else if (orphelines.length) {
      dire("salles qu'aucun chemin ne relie (etat/chemins.json) : " +
        orphelines.map((s) => s.id).join(", "));
    }
  }

  // --- formes : avis seulement, les cercles font des faux positifs
  const plains = p.salles.filter((s) => !s.etage && !s.fond);
  for (let i = 0; i < plains.length; i++) {
    for (let j = i + 1; j < plains.length; j++) {
      if (croise(boite(plains[i]), boite(plains[j]))) {
        console.log("  avis — boites qui se croisent (a verifier a l'oeil) : " +
          plains[i].id + " x " + plains[j].id);
        avis++;
      }
    }
  }

  // --- etiquettes : la vraie faute, celle qui rend la carte illisible
  const bs = [];
  const pousser = (id, t, x, y) => {
    const w = t.length * police * CHASSE;
    bs.push({ id, t, x0: x - w / 2, x1: x + w / 2,
              y0: y - police * 0.78, y1: y + police * 0.25 });
  };
  p.salles.forEach((s) => (s.lignes || [s.nom]).forEach((l, i) =>
    pousser(s.id, l, s.etiq[0], s.etiq[1] + i * inter)));
  (p.etiquettes || []).forEach((e) => pousser("(libre)", e.texte, e.x, e.y));

  let n = 0;
  for (let i = 0; i < bs.length; i++) {
    for (let j = i + 1; j < bs.length; j++) {
      const a = bs[i], b = bs[j];
      if (a.id === b.id) continue;
      const dx = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0);
      const dy = Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0);
      if (dx > 0.5 && dy > 0.5) {
        n++;
        dire('etiquettes qui se marchent dessus : "' + a.t + '" (' + a.id +
          ') x "' + b.t + '" (' + b.id + ')  ' +
          dx.toFixed(1) + " x " + dy.toFixed(1));
      }
    }
  }
  console.log("  " + bs.length + " etiquettes, " + n + " collision(s)");
}

console.log("\n" + (fautes ? fautes + " faute(s)" : "aucune faute") +
  (avis ? " — " + avis + " avis de formes" : ""));
process.exit(fautes ? 1 : 0);
