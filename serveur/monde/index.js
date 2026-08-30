// LA PORTE serveur du container monde (docs/organisation.md §2) : ses routes et
// son moteur 3D, requis par l'assembleur (serveur.js) — jamais en direct.
module.exports = {
  monde3d: require("../monde3d"),          // le service 3D : graphe pieton, bati, peremption
  carte: require("../routes/carte"),       // /carte, /ville
  terrain: require("../routes/terrain"),   // /terrain
  chemin: require("../routes/chemin"),     // /chemin, /monde/...
  foule: require("../routes/foule"),       // POST /foule/journal
  mondeJeu: require("../routes/monde-jeu"),// /salles, /entites, /gens
  presence: require("../routes/presence"), // /presence
  marche: require("../routes/marche"),     // POST /ou, /marche
};
