
// La silhouette anonyme, servie à qui n'a pas encore de portrait dessiné :
// personne n'apparaît sans son rond. Le gabarit est lu une fois ; sa teinte
// est tirée du NOM, pour que deux inconnus ne se confondent pas et que le
// même homme garde sa couleur d'un écran à l'autre. Même calcul côté Python
// (`scripts/append_flux.py`) : les deux doivent tomber sur la même couleur.

const fs = require("fs");
const path = require("path");
const { RACINE } = require("./http");

let _defautSvg = null;
function teinteDuNom(nom) {
  let h = 0;
  for (const c of String(nom || "")) h = (h * 31 + c.codePointAt(0)) % 360;
  return h;
}
// LE PORTRAIT INLINÉ DANS LE FLUX EST DATÉ DU JOUR DE LA POUSSÉE, et il ne
// vieillit pas bien : `append_flux.py` recopie le SVG dans l'item au moment où
// on l'écrit, si bien qu'un homme poussé avant qu'on lui peigne un visage garde
// sa silhouette « Portrait inconnu » pour toujours — dans tout l'historique, et
// jusque dans la galerie des présents de la scène en cours.
//
// On ne réécrit pas `flux.jsonl` pour autant : il est append-only, et une
// réécriture casserait les curseurs des navigateurs ouverts. On rafraîchit à la
// SERVITURE — le fichier sur disque fait foi au moment où l'on sert. Peindre un
// portrait suffit donc à le faire apparaître partout, y compris dans le passé.
//
// Le cache se contrôle sur la date du fichier : `medaillons.py` peut refaire un
// visage pendant que le serveur tourne, il part au premier `/scene` suivant.
const _portraitsFrais = new Map();
function portraitFrais(id) {
  if (!id || /[^a-zA-Z0-9_-]/.test(id)) return null;
  const p = path.join(RACINE, "ecrans", "portraits", id + ".svg");
  let m;
  try { m = fs.statSync(p).mtimeMs; } catch (e) { return null; }
  const tenu = _portraitsFrais.get(id);
  if (tenu && tenu.m === m) return tenu.svg;
  try {
    const svg = fs.readFileSync(p, "utf-8");
    _portraitsFrais.set(id, { m, svg });
    return svg;
  } catch (e) { return null; }
}
function rafraichirPortraits(it) {
  ["presents", "entrent"].forEach((k) => {
    (it[k] || []).forEach((p) => {
      if (!p || typeof p !== "object") return;
      const svg = portraitFrais(p.id);
      if (svg) p.portrait_svg = svg;
    });
  });
}
function portraitDefaut(nom) {
  if (_defautSvg === null) {
    try {
      _defautSvg = fs.readFileSync(
        path.join(RACINE, "ecrans", "portraits", "_defaut.svg"), "utf-8");
    } catch (e) { _defautSvg = ""; }
  }
  const h = teinteDuNom(nom);
  return _defautSvg
    .replace(/\{\{CLE\}\}/g, String(nom || "x").replace(/[^a-zA-Z0-9_-]/g, "") || "x")
    .replace(/\{\{TEINTE\}\}/g, `hsl(${h},32%,52%)`)
    .replace(/\{\{TEINTE_SOMBRE\}\}/g, `hsl(${h},22%,22%)`)
    .replace(/\{\{TEINTE_ETOFFE\}\}/g, `hsl(${h},20%,28%)`)
    .replace(/\{\{TEINTE_CHAIR\}\}/g, `hsl(${h},18%,38%)`)
    .replace(/\{\{TEINTE_FOND\}\}/g, `hsl(${h},18%,17%)`);
}

module.exports = { teinteDuNom, portraitFrais, rafraichirPortraits, portraitDefaut };
