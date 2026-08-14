/* COMPTE-TIRAGES — combien de fois la bataille puise dans l'urne, et quand.
 *
 * POURQUOI. `bataille/hasard.js` n'a qu'un seul etat, `_s`, et TOUT le monde y
 * puise dans l'ordre ou il passe. Un tirage de plus ou de moins en amont —
 * une couche branchee, un homme qui decide autrement, un habitant recrute —
 * decale toute la suite pour TOUS les hommes. Ce que ce compte etablit, c'est
 * la TAILLE de ce qui se decale : si le dressage a lui seul consomme des
 * dizaines de milliers de tirages, alors deux cuissons qui different d'un rien
 * n'ont meme pas les memes hommes, et leurs quatre comptes ne sont pas
 * comparables — pas « proches », pas « a une unite pres » : PAS COMPARABLES.
 *
 * Il ne cuit rien et n'ecrit rien : il compte, comme le reste de ce dossier.
 *
 *   node analyse/etalon-90110/compte-tirages.js --hommes=1700 --duree=5
 */
const fs = require("fs");
const path = require("path");

const RACINE = path.resolve(__dirname, "..", "..");
const MODULES = path.join(RACINE, "ecrans", "modules");
const A = process.argv.slice(2);
const HOMMES = +((A.find((x) => x.startsWith("--hommes=")) || "").split("=")[1]) || 1700;
const DUREE = +((A.find((x) => x.startsWith("--duree=")) || "").split("=")[1]) || 5;
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

const CHAINE = ["bataille/hasard.js", "bataille/mesures.js",
                "survival-stack/1-corps.js", "bataille/corps-adapt.js",
                "survival-stack/4-envie.js",
                "survival-stack/3-interpretation.js",
                "bataille2d.js"];

globalThis.__nR = 0;
for (const f of CHAINE) {
  let src = fs.readFileSync(path.join(MODULES, f), "utf8");
  if (f === "bataille/hasard.js") {
    const avant = src;
    // Le compteur est POSE DANS LA SOURCE et non autour de l'objet : chaque
    // module destructure `R` a son chargement (bataille2d.js l.725), donc une
    // enveloppe posee apres coup ne verrait rien passer.
    src = src.replace(
      "const R = () => (_s = (_s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;",
      "const R = () => { globalThis.__nR++; return (_s = (_s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff; };");
    if (src === avant) throw new Error("la ligne de R n'a pas ete trouvee — le compte mentirait");
  }
  (0, eval)(src);
}
const B = globalThis.window.Bataille2d;
if (!B) throw new Error("bataille2d ne s'est pas pose");

(async () => {
  await B.preparer("/monde");
  const apresCharge = globalThis.__nR;
  B.rejouer("La porte de la Gadoue", HOMMES);
  const apresDressage = globalThis.__nR;
  for (let t = 0; t < DUREE; t += PAS) B.pas(PAS);
  const apresCuisson = globalThis.__nR;
  const corps = (B.corps && B.corps().length) || null;
  console.log(JSON.stringify({
    hommes: HOMMES, duree_s: DUREE, corps,
    tirages: {
      chargement: apresCharge,
      dressage: apresDressage - apresCharge,
      cuisson: apresCuisson - apresDressage,
    },
    par_seconde_de_bataille: +((apresCuisson - apresDressage) / DUREE).toFixed(0),
    par_homme_au_dressage: corps ? +((apresDressage - apresCharge) / corps).toFixed(1) : null,
  }, null, 1));
})();
