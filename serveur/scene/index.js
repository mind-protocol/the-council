// LA PORTE serveur du container scene (docs/organisation.md §2) : ce que les
// autres containers ont le droit d'en lire. La scene est la peau — seul
// `bibliotheque` (les cahiers servis) est consommé d'ailleurs aujourd'hui.
module.exports = {
  bibliotheque: require("../bibliotheque"), // les books côté serveur : charger, ouvrir
};
