// GET /habillage.css, /habillage/<fichier> — L'HABILLAGE DE LA PARTIE.
//
// Un monde a son paquet (`/monde.js`) : ses plans, ses armes, sa carte. Il lui
// manquait son VISAGE. Westeros se lit sur du papier ivoire ; Charmed 1906 se
// lit dans un Livre des Ombres relié de cuir vert, doré aux coins. Ce n'est
// pas le même jeu à l'œil, et `jeu.css` ne peut pas le savoir : il ne connaît
// aucun monde.
//
// LA RÈGLE : l'habillage vit dans le paquet du monde, `<monde>/habillage/`, et
// il ne fait QUE s'ajouter. `jeu.html` charge `/habillage.css` en DERNIÈRE
// feuille : elle surcharge ce qu'elle veut et ne retire rien. Un monde sans
// dossier `habillage/` reçoit une feuille vide — la page est celle d'avant, au
// pixel près. Aucun module ne teste le nom du monde : le moteur reste aveugle,
// et c'est la feuille qui sait.
//
//   <monde>/habillage/
//     habillage.css    — la feuille, chargée après jeu.css et partie.css
//     habillage.json   — ce que la feuille ne peut pas écrire seule : le titre
//                        de l'onglet, le bandeau, le logo. Servi sous
//                        /habillage.json à modules/habillage.js
//     *.png|webp|jpg|svg|woff2 — ses images et ses fontes, servies sous
//                        /habillage/<nom> ; la feuille les cite ainsi.
//
// Les ressources ne sortent pas du dossier : un nom sans séparateur ni
// remontée, et une extension connue. Comme les salles peintes, elles se
// gardent un jour en cache — la feuille, elle, ne se garde jamais (on la
// retouche en jouant).
"use strict";
const fs = require("fs");
const path = require("path");
const { RACINE, envoyer } = require("../http");

const DOSSIER = path.join(RACINE, "habillage");
const TYPES = {
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".webp": "image/webp", ".svg": "image/svg+xml", ".gif": "image/gif",
  ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf",
};

function traiter(req, res, url) {
  if (req.method !== "GET") return false;
  if (url === "/habillage.css") {
    let css;
    try { css = fs.readFileSync(path.join(DOSSIER, "habillage.css"), "utf-8"); }
    catch (e) { css = "/* ce monde n'a pas d'habillage : la page de jeu.css, telle quelle */\n"; }
    return envoyer(res, 200, css, "text/css; charset=utf-8");
  }
  // la fiche, pour modules/habillage.js — `null` pour un monde sans visage
  if (url === "/habillage.json") return envoyer(res, 200, JSON.stringify(fiche()));
  if (url.startsWith("/habillage/")) {
    const nom = decodeURIComponent(url.slice("/habillage/".length));
    const type = TYPES[path.extname(nom).toLowerCase()];
    if (!type || nom !== path.basename(nom) || nom.startsWith("."))
      return envoyer(res, 404, JSON.stringify({ erreur: nom }));
    try {
      const corps = fs.readFileSync(path.join(DOSSIER, nom));
      res.writeHead(200, { "Content-Type": type, "Cache-Control": "public, max-age=86400" });
      return res.end(corps);
    } catch (e) {
      return envoyer(res, 404, JSON.stringify({ erreur: nom }));
    }
  }
  return false;
}

// `habillage.json`, augmenté de l'id du monde (lu dans son manifeste) : c'est
// lui que la page pose en `data-habillage`. Ou rien.
function fiche() {
  let f;
  try { f = JSON.parse(fs.readFileSync(path.join(DOSSIER, "habillage.json"), "utf-8")); }
  catch (e) { return null; }
  try { f.monde = JSON.parse(fs.readFileSync(path.join(RACINE, "manifeste.json"), "utf-8")).id; }
  catch (e) {}
  return f;
}

module.exports = traiter;
