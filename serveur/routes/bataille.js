// /bataille — le moteur de mêlée, servi par le serveur du jeu.
//
// `bataille/` est un dépôt importé (voir bataille/IMPORT.md) : il a sa propre
// page, ses scénarios, ses containers. On ne le réécrit pas — on le SERT, sous
// un préfixe d'URL, pour que la mêlée soit une échelle du décor et non une
// démonstration dans un second onglet sur un second port.
//
// Le montage `donnees/ville` reprend celui de `bataille/outils/montages.mjs` :
// les villes cuites restent dans leur dépôt, une seule source canonique.

const fs = require("fs");
const path = require("path");
const { RACINE, envoyer } = require("../http");

const MOTEUR = path.join(RACINE, "bataille");
// Le moteur ayant été extrait de l'archive, les données cuites sont maintenant dans son propre dossier
const MONTAGES = { "donnees/ville": path.join(MOTEUR, "donnees/ville") };

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".bin": "application/octet-stream",
};

function monte(relatif) {
  for (const [prefixe, racine] of Object.entries(MONTAGES)) {
    if (relatif.startsWith(prefixe + "/")) return racine + relatif.slice(prefixe.length);
  }
  return null;
}

module.exports = function bataille(req, res, url) {
  // Les villes cuites sont demandees a la RACINE par le moteur (`donnees/ville/
  // portreal.masque.bin`), pas sous son prefixe : sa page ignore ou on la sert.
  // On prend donc les deux, et le montage repond dans les deux cas.
  if (url.startsWith("/donnees/ville/")) {
    return servir(res, url.slice(1));
  }
  if (url !== "/bataille" && !url.startsWith("/bataille/")) return false;

  // `/bataille` sans barre : la page du moteur. Les chemins qu'elle demande
  // ensuite sont relatifs, donc on redirige pour que la barre soit là.
  if (url === "/bataille") {
    res.writeHead(302, { Location: "/bataille/" });
    return res.end();
  }

  let relatif = decodeURIComponent(url.slice("/bataille/".length));
  if (relatif === "") relatif = "index.html";
  return servir(res, relatif);
};

function servir(res, relatif) {
  relatif = decodeURIComponent(relatif);
  // Un chemin d'URL ne choisit pas quel fichier le serveur ouvre.
  const monteur = monte(relatif);
  const fichier = monteur || path.join(MOTEUR, path.normalize(relatif));
  if (!monteur && !path.resolve(fichier).startsWith(path.resolve(MOTEUR))) {
    return envoyer(res, 403, JSON.stringify({ erreur: "hors racine" }));
  }
  try {
    const corps = fs.readFileSync(fichier);
    return envoyer(res, 200, corps, TYPES[path.extname(fichier)] || "application/octet-stream");
  } catch (e) {
    return envoyer(res, 404, JSON.stringify({ erreur: relatif }));
  }
}
