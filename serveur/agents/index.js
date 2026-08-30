// LA PORTE serveur du container agents (docs/organisation.md §2) : les moteurs
// d'activation et de regie, lus par le plan (atelier, echiquier) — jamais en direct.
module.exports = {
  activations: require("../domaine/activations"), // sante, previsions, fil MJ
  regie: require("../domaine/regie"),             // chercher dans le flux, le fil d'un personnage
  chambres: require("../domaine/chambres"),      // l'envers du modele habitant : la frise, les salles, une chambre
  chambreLivres: require("../domaine/chambre-livres"), // les coffrets de chambre de l'onglet livres
};
