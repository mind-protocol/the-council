// LA PORTE serveur du container plan (docs/organisation.md §2) : ses routes,
// requises par l'assembleur (serveur.js) — jamais en direct.
module.exports = {
  livres: require("../routes/livres"),       // /books, /notes, /nappe, /plis
  echiquier: require("../routes/echiquier"), // /echiquier
  agenda: require("../routes/agenda"),       // POST /agenda, /notes, /nappe
  atelier: require("../routes/atelier"),     // pages d'atelier, /admin, /regie
};
