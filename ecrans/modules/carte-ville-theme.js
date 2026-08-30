// carte-ville-theme.js — une seule matière pour tous les plans de Port-Réal.
//
// `carte-ville.js` dessine en SVG, les toiles posées par-dessus composent en
// pixels. Le matériau diffère, pas la carte : tous lisent ici les mêmes teintes,
// nuances d'usage et largeurs de voies. Le petit style injecté passe après les
// feuilles de page et fait de cette table l'autorité d'exécution ; les valeurs
// restées dans `jeu.css` ne sont plus que le repli si ce script manque.
(() => {
"use strict";

const COMMUN = Object.freeze({
  nuances: Object.freeze({
    cabane:[0,26], taudis:[0,16], "maison-officier":[12,0], manse:[26,0],
    "chantier-bois":[0,22], entrepot:[0,14], "marche-quartier":[16,0], change:[26,0],
    forge:[0,18], corderie:[0,8], voilerie:[8,0], boulangerie:[14,0], moulin:[24,0],
    poterie:[10,0], tannerie:[0,10], abattoir:[0,20], "fosse-vidange":[0,28],
    bordel:[18,0], ecurie:[0,16], etuve:[16,0], puits:[20,0], grenier:[0,12],
    geole:[0,24], "fosse-dragons":[0,14], caserne:[0,22],
    "vieux-septuaire":[14,0], "guilde-alchimistes":[24,0], "bureau-port":[30,0],
  }),
  voies: Object.freeze({
    ruelle:[2.5,.9,.42], abord:[4,1,.42], escalier:[2,1.2,.60],
    rue:[4,1.2,.50], quai:[8,2.2,.55], artere:[10,2.8,.60],
  }),
});

const PALETTES = Object.freeze({
  light: Object.freeze({
    sol:"#efe7d6", solIntra:"#e7ddca", eau:"#b9d2d9", eauTrait:"#8fb0ba",
    niveau:"rgba(150,120,70,.30)", batiTrait:"rgba(110,85,50,.45)",
    voie:"#a8926d", quai:"#3d7b86", artere:"#a34a22",
    mur:"#8a8378", tour:"#a9a196", lum:"#fbf3e0", nuit:"#6b543a",
    encre:"#2b2119", repere:"#a34a22",
    familles:Object.freeze({
      habitat:"#d9cbb0", artisanat:"#c08a5e", commerce:"#d6a93f",
      plaisir:"#b05a72", service:"#7fa08c", civique:"#8fa04e",
      culte:"#8c93bd", institution:"#a8443c", nuisance:"#6f6350",
    }),
  }),
  dark: Object.freeze({
    sol:"#1b1712", solIntra:"#16120e", eau:"#1d2c33", eauTrait:"#33555f",
    niveau:"rgba(220,190,140,.16)", batiTrait:"rgba(220,190,140,.22)",
    voie:"#6d5c42", quai:"#63b3c1", artere:"#e0824a",
    mur:"#6a6459", tour:"#847d70", lum:"#8a7856", nuit:"#120f0b",
    encre:"#e6dbc6", repere:"#e0824a",
    familles:Object.freeze({
      habitat:"#2e2820", artisanat:"#5c3e29", commerce:"#6b5423",
      plaisir:"#5a2e39", service:"#3a4f45", civique:"#454f28",
      culte:"#42465c", institution:"#5e2622", nuisance:"#3a352c",
    }),
  }),
});

const mode = () => matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
const palette = (nom) => PALETTES[nom || mode()] || PALETTES.light;
// `melanger()` est composé : son résultat `rgb(r,g,b)` peut devenir l'entrée
// du mélange suivant. Le parseur historique ne savait lire que `#rrggbb` et
// transformait donc le second passage en `rgb(NaN,NaN,…)` — le navigateur
// rejetait silencieusement la couleur. On accepte les deux notations.
const rgb = (s) => {
  const couleur = String(s || "");
  if (couleur[0] === "#") return [1, 3, 5].map((i) => parseInt(couleur.slice(i, i + 2), 16));
  return (couleur.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
};
const melanger = (a, b, p) => {
  const x = rgb(a), y = rgb(b), t = p / 100;
  return "rgb(" + x.map((v, i) => Math.round(v + (y[i] - v) * t)).join(",") + ")";
};

function couleurUsage(plan, usage, nomMode) {
  const p = palette(nomMode), t = ((plan || {}).types || {})[usage] || {};
  const base = p.familles[t.cat] || p.familles.habitat;
  const [lum, nuit] = COMMUN.nuances[usage] || [0, 0];
  return melanger(melanger(base, p.lum, lum), p.nuit, nuit);
}

function variables(p) {
  return [
    ["sol",p.sol],["sol-intra",p.solIntra],["eau",p.eau],["eau-trait",p.eauTrait],
    ["niveau",p.niveau],["bati-trait",p.batiTrait],["voie",p.voie],
    ["quai",p.quai],["artere",p.artere],["mur",p.mur],
    ["mur-tour",p.tour],["lum",p.lum],["nuit",p.nuit],
  ].map(([k,v]) => "--cv-" + k + ":" + v + ";").join("");
}

// La courtine est interrompue aux portes pour rester honnête comme mur. Pour
// teinter le sol, ces brèches doivent au contraire être refermées : on relie
// les tronçons, puis on ferme le circuit, sans inventer une seconde enceinte.
function enceinte(plan) {
  const d = (((plan || {}).rempart || {}).courtine || "");
  if (!d) return "";
  let premier = true;
  return d.replace(/M/g, () => premier ? (premier = false, "M") : "L") + "Z";
}

function familles(p) {
  return Object.entries(p.familles)
    .map(([k,v]) => ".cv-b-" + k + "{--tf:" + v + ";}").join("");
}

function installer() {
  if (document.getElementById("carte-ville-theme")) return;
  const s = document.createElement("style");
  s.id = "carte-ville-theme";
  s.textContent = ":root{" + variables(PALETTES.light) + "}" +
    familles(PALETTES.light) +
    ".cv-sol-intra{fill:var(--cv-sol-intra);}" +
    ".cv-v-quai{stroke:var(--cv-quai);}.cv-v-artere{stroke:var(--cv-artere);}" +
    "@media (prefers-color-scheme:dark){:root{" + variables(PALETTES.dark) + "}" +
    familles(PALETTES.dark) + "}";
  document.head.appendChild(s);
}

installer();
window.CarteVilleTheme = Object.freeze({
  palettes: PALETTES, nuances: COMMUN.nuances, voies: COMMUN.voies,
  mode, palette, rgb, melanger, couleurUsage, enceinte,
});
})();
