// LA PORTE serveur du container plan (docs/organisation.md §2) : ses routes et
// sa bibliotheque, requises par l'assembleur (serveur.js) et les voisins —
// jamais en direct.
//
// EXPORTS PROGRESSIFS, ET L'ORDRE COMPTE : atelier requiert la porte des
// agents, dont activations relit CETTE porte (le cycle plan -> agents -> plan).
// Avec un `module.exports = {...}` d'un bloc, le re-entrant verrait un objet
// vide ; en liant `bibliotheque` AVANT atelier, il trouve ce qu'il cherche.
module.exports.bibliotheque = require("./bibliotheque"); // les books cote serveur : charger, ouvrir
module.exports.livres = require("../routes/livres");     // /books, /notes, /nappe, /plis
module.exports.echiquier = require("../routes/echiquier"); // /echiquier
module.exports.partie = require("../routes/partie");       // /partie — la vue en cartes
module.exports.agenda = require("../routes/agenda");     // POST /agenda, /notes, /nappe
module.exports.atelier = require("../routes/atelier");   // pages d'atelier, /admin, /regie
