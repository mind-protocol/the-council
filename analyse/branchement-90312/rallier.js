// -*- coding: utf-8 -*-
/* LE PREMIER CRAN DE ⚔️ 90312 — ce que le ralliement devient quand il passe
 * par l'arbitre au lieu de lire `h.l1.jambes` lui-meme.
 *
 * `rallier()` (bataille2d.js) etait le SEUL acces a `h.l1` de tout le fichier
 * hors de `soldat()` : un appelant unique, deja ecrit, qui lisait deja la
 * couche en direct. C'est l'essai le moins cher qui existe, donc c'est par lui
 * qu'on commence la depose.
 *
 * LES DEUX BRAS SONT LE MEME FICHIER, ET AUCUNE LIGNE N'EST REECRITE. Le
 * branchement porte son propre repli : sans `h.conduit`, `rallier()` retombe
 * sur le vieux test. Retirer `5-qui-conduit.js` de la chaine rend donc
 * exactement la conduite d'hier — le temoin est la conduite d'avant, pas une
 * reconstitution de la conduite d'avant.
 *
 *   node analyse/branchement-90312/rallier.js                 avec l'arbitre
 *   node analyse/branchement-90312/rallier.js --sans-arbitre  le temoin
 *   ... --hommes=1700 --duree=600
 *
 * Le decor est celui de `analyse/etalon-90110/deux-causes.js` (Toll, le 3e),
 * a la virgule pres, plus les trois fichiers que `jeu.html` charge depuis :
 * la couche 2, son pourvoyeur, et l'arbitre. Il ne cuit rien et n'ecrit rien
 * dans `monde/`.
 */
"use strict";
const fs = require("fs");
const path = require("path");

const RACINE = path.resolve(__dirname, "..", "..");
const MODULES = path.join(RACINE, "ecrans", "modules");
const A = process.argv.slice(2);
const SANS_ARBITRE = A.includes("--sans-arbitre");
const HOMMES = +((A.find((x) => x.startsWith("--hommes=")) || "").split("=")[1]) || 1700;
const DUREE = +((A.find((x) => x.startsWith("--duree=")) || "").split("=")[1]) || 600;
const PAS = 1 / 20;

const SERVEUR = (A.find((x) => x.startsWith("--serveur=")) || "").split("=")[1]
              || "http://localhost:3129";
globalThis.window = globalThis;
globalThis.window.CHEMIN_JOURNEE =
  require("url").pathToFileURL(path.join(MODULES, "monde", "journee.js")).href;
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.document = { addEventListener() {} };
const vraiFetch = globalThis.fetch;
globalThis.fetch = (u, o) => vraiFetch(/^https?:/.test(u) ? u : SERVEUR + u, o);

// L'ordre de `jeu.html`, et il compte : `reflexion-adapt.js` resout
// `window.Reflexion` a son chargement, l'arbitre au battement (donc on peut le
// retirer). `bataille2d.js` en dernier.
const CHAINE = ["bataille/hasard.js", "bataille/mesures.js",
                "survival-stack/1-corps.js", "bataille/corps-adapt.js",
                "survival-stack/4-envie.js",
                "survival-stack/3-interpretation.js",
                "survival-stack/2-reflexion.js",
                "bataille/reflexion-adapt.js",
                "survival-stack/5-qui-conduit.js",
                "bataille2d.js"];
const RETIREES = SANS_ARBITRE ? ["survival-stack/5-qui-conduit.js"] : [];

for (const f of CHAINE.filter((x) => !RETIREES.includes(x))) {
  let src = fs.readFileSync(path.join(MODULES, f), "utf8");
  if (f === "bataille2d.js") {
    // MESURE, PAS TAILLE : on ouvre une fenetre sur les hommes pour compter qui
    // tient les jambes a la fin. Rien d'autre n'est touche, et si l'ancre a
    // bouge la mesure s'arrete au lieu de mentir.
    const avant = src;
    src = src.replace("  return { poser, preparer,",
                      "  return { _hommes: () => hommes, poser, preparer,");
    if (src === avant) throw new Error("l'ancre du relevé n'a pas ete trouvee — la mesure mentirait");
  }
  (0, eval)(src);
}
const B = globalThis.window.Bataille2d;
if (!B) throw new Error("bataille2d ne s'est pas pose");
if (!SANS_ARBITRE && !globalThis.window.QuiConduit)
  throw new Error("l'arbitre devait etre la et n'y est pas");
if (SANS_ARBITRE && globalThis.window.QuiConduit)
  throw new Error("le temoin porte l'arbitre — les deux bras seraient le meme");

(async () => {
  await B.preparer("/monde");
  const t1 = Date.now();
  B.rejouer("La porte de la Gadoue", HOMMES);
  for (let t = 0; t < DUREE; t += PAS) B.pas(PAS);
  const cuisson = (Date.now() - t1) / 1000;

  const par = {};
  for (const f of B.faits()) par[f.quoi] = (par[f.quoi] || 0) + 1;
  const e = B.etat();

  // QUI TIENT LES JAMBES, A LA FIN, SUR LES VIVANTS. C'est le chiffre qui dit
  // si l'arbitre a seulement de quoi changer quelque chose : une main qui ne
  // sort jamais de « ordre » ne peut rien retenir, et une main qui n'en dit
  // jamais rend le ralliement impossible.
  const mains = {};
  let deroutes = 0, deroutesOrdre = 0;
  for (const h of B._hommes()) {
    if (h.etat === "mort" || h.tete) continue;
    const m = h.conduit || "(sans arbitre)";
    mains[m] = (mains[m] || 0) + 1;
    if (h.etat === "deroute") { deroutes++; if (h.conduit === "ordre") deroutesOrdre++; }
  }

  console.log(JSON.stringify({
    bras: SANS_ARBITRE ? "temoin — rallier lit h.l1.jambes"
                       : "branche — rallier demande a l'arbitre",
    hommes: HOMMES, duree_s: DUREE, cuisson_s: +cuisson.toFixed(1),
    ralliements: par["ralliement"] || 0,
    fuyards_a_la_fin: e.fuyards, morts: e.morts, blesses: e.blesses,
    etats: e.etats,
    mains_sur_les_jambes: mains,
    deroutes_a_la_fin: deroutes, dont_l_ordre_tient_les_jambes: deroutesOrdre,
    faits_total: B.faits().length,
    par_quoi: par,
  }, null, 1));
})();
