/* DEUX CAUSES — separer ce que 745c8eb a fait tomber dans le meme anneau.
 *
 * Verrou 90110 : l'etalon 5, 5, 14, 54 a ete lu APRES un commit qui portait
 * DEUX changements — le drapeau PORTE_OUVERTE_ESSAI retire, et les couches
 * 3-interpretation / 4-envie branchees dans la chaine du four. Un etalon qui
 * bouge ne dirait pas LEQUEL des deux l'a fait bouger.
 *
 * Ce script ne cuit rien et n'ecrit rien dans monde/ : il monte la meme chaine
 * que scripts/monde/sac.js, la fait tourner, et COMPTE les faits. Il ne touche
 * pas ecrans/ — il lit la source et la reecrit en memoire, le temps du eval.
 * C'est de la mesure, pas de la taille.
 *
 *   node analyse/etalon-90110/deux-causes.js            les quatre, tel quel
 *   node analyse/etalon-90110/deux-causes.js --sans-couches
 *   node analyse/etalon-90110/deux-causes.js --porte-ouverte
 */
const fs = require("fs");
const path = require("path");

const RACINE = path.resolve(__dirname, "..", "..");
const MODULES = path.join(RACINE, "ecrans", "modules");
const A = process.argv.slice(2);
const SANS_COUCHES = A.includes("--sans-couches");
// `4-envie` ne se debranche PAS : bataille2d.js l.1458 appelle
// window.Envie.temperament sans garde, au dressage, avant le premier pas.
// `3-interpretation` se debranche : l.3451 est gardee (`if (window.Interpretation
// && e)`) et l.4557 passe par `chef.l3`, qui n'existe pas sans la couche. C'est
// donc le SEUL des deux bras qui se mesure, et il mesure les initiatives.
const SANS_INTERPRETATION = A.includes("--sans-interpretation");
const PORTE_OUVERTE = A.includes("--porte-ouverte");
const HOMMES = +((A.find((x) => x.startsWith("--hommes=")) || "").split("=")[1]) || 1700;
const DUREE = +((A.find((x) => x.startsWith("--duree=")) || "").split("=")[1]) || 600;
const PAS = 1 / 20;

// Le meme decor de navigateur que `planter()` dans scripts/monde/sac.js — a la
// virgule pres, sinon la mesure ne porte pas sur la meme chose que le four.
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

const CHAINE = ["bataille/hasard.js", "bataille/mesures.js",
                "survival-stack/1-corps.js", "bataille/corps-adapt.js",
                "survival-stack/4-envie.js",
                "survival-stack/3-interpretation.js",
                "bataille2d.js"];
const HAUTES = ["survival-stack/4-envie.js", "survival-stack/3-interpretation.js"];

const RETIREES = SANS_COUCHES ? HAUTES
               : SANS_INTERPRETATION ? ["survival-stack/3-interpretation.js"] : [];
for (const f of CHAINE.filter((x) => !RETIREES.includes(x))) {
  let src = fs.readFileSync(path.join(MODULES, f), "utf8");
  if (PORTE_OUVERTE && f === "bataille2d.js") {
    const avant = src;
    src = src.replace("const PORTE_OUVERTE_ESSAI = false;",
                      "const PORTE_OUVERTE_ESSAI = true;");
    if (src === avant) throw new Error("le drapeau n'a pas ete trouve — la mesure mentirait");
  }
  (0, eval)(src);
}
const B = globalThis.window.Bataille2d;
if (!B) throw new Error("bataille2d ne s'est pas pose");

(async () => {
  const t0 = Date.now();
  await B.preparer("/monde");
  const tCharge = (Date.now() - t0) / 1000;
  const t1 = Date.now();
  B.rejouer("La porte de la Gadoue", HOMMES);
  for (let t = 0; t < DUREE; t += PAS) B.pas(PAS);
  const tCuit = (Date.now() - t1) / 1000;

  const faits = B.faits().slice();
  const par = {};
  for (const f of faits) par[f.quoi] = (par[f.quoi] || 0) + 1;
  const q = (k) => par[k] || 0;
  console.log(JSON.stringify({
    variante: SANS_COUCHES ? "sans-couches-hautes"
            : SANS_INTERPRETATION ? "sans-3-interpretation"
            : PORTE_OUVERTE ? "porte-ouverte-essai=true" : "tel-quel",
    hommes: HOMMES, duree_s: DUREE,
    les_quatre: {
      "ordres deformes": q("ordre-deforme"),
      "declencheurs tombes": q("declencheur-tombe"),
      initiatives: q("initiative"),
      coureurs: q("coureur-part"),
    },
    faits_total: faits.length,
    charge_s: +tCharge.toFixed(1), cuisson_s: +tCuit.toFixed(1),
    par_quoi: par,
  }, null, 1));
})();
