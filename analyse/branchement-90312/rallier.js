// -*- coding: utf-8 -*-
/* LE PREMIER CRAN DE ⚔️ 90312 — banc des deux bras du ralliement.
 *
 *   node analyse/branchement-90312/rallier.js
 *   node analyse/branchement-90312/rallier.js --sans-arbitre
 *   ... --hommes=1700 --duree=600
 */
"use strict";
const fs = require("fs");
const path = require("path");

const RACINE = path.join(__dirname, "fixture-dddf6c8-parent");
const MODULES = path.join(RACINE, "ecrans", "modules");
const A = process.argv.slice(2);
const SANS_ARBITRE = A.includes("--sans-arbitre");
const HOMMES = +((A.find((x) => x.startsWith("--hommes=")) || "").split("=")[1]) || 1700;
const DUREE = +((A.find((x) => x.startsWith("--duree=")) || "").split("=")[1]) || 600;
const PAS = 1 / 20;
const SERVEUR = (A.find((x) => x.startsWith("--serveur=")) || "").split("=")[1] || "http://localhost:3129";

globalThis.window = globalThis;
globalThis.window.CHEMIN_JOURNEE = require("url").pathToFileURL(path.join(MODULES, "monde", "journee.js")).href;
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.document = { addEventListener() {} };
const vraiFetch = globalThis.fetch;
globalThis.fetch = (u, o) => vraiFetch(/^https?:/.test(u) ? u : SERVEUR + u, o);

const CHAINE = require(path.join(MODULES, "bataille", "moteur", "chaine.js"))
  .fichiers("moteur");

for (const f of CHAINE) {
  let src = fs.readFileSync(path.join(MODULES, f), "utf8");
  if (f === "bataille2d.js") {
    const avant = src;
    src = src.replace("  return { poser, preparer,", "  return { _hommes: () => hommes, poser, preparer,");
    if (src === avant) throw new Error("l'ancre du relevé n'a pas ete trouvee — la mesure mentirait");
  }
  (0, eval)(src);
}
const B = globalThis.window.Bataille2d;
if (!B) throw new Error("bataille2d ne s'est pas pose");
if (!SANS_ARBITRE && !globalThis.window.QuiConduit) throw new Error("l'arbitre devait etre la et n'y est pas");
if (SANS_ARBITRE) delete globalThis.window.QuiConduit;
if (SANS_ARBITRE && globalThis.window.QuiConduit) throw new Error("le temoin porte l'arbitre — les deux bras seraient le meme");

(async () => {
  await B.preparer("/monde");
  const t1 = Date.now();
  B.rejouer("La porte de la Gadoue", HOMMES);
  for (let t = 0; t < DUREE; t += PAS) B.pas(PAS);
  const cuisson = (Date.now() - t1) / 1000;
  const par = {};
  for (const f of B.faits()) par[f.quoi] = (par[f.quoi] || 0) + 1;
  const e = B.etat();
  const mains = {};
  let deroutes = 0, deroutesOrdre = 0;
  for (const h of B._hommes()) {
    if (h.etat === "mort" || h.tete) continue;
    const m = h.conduit || "(sans arbitre)";
    mains[m] = (mains[m] || 0) + 1;
    if (h.etat === "deroute") { deroutes++; if (h.conduit === "ordre") deroutesOrdre++; }
  }
  console.log(JSON.stringify({
    bras: SANS_ARBITRE ? "temoin — rallier lit h.l1.jambes" : "branche — rallier demande a l'arbitre",
    hommes: HOMMES, duree_s: DUREE, cuisson_s: +cuisson.toFixed(1),
    ralliements: par.ralliement || 0, fuyards_a_la_fin: e.fuyards,
    morts: e.morts, blesses: e.blesses, etats: e.etats,
    mains_sur_les_jambes: mains, deroutes_a_la_fin: deroutes,
    dont_l_ordre_tient_les_jambes: deroutesOrdre,
    faits_total: B.faits().length, par_quoi: par,
  }, null, 1));
})();
