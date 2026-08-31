// LA PORTE serveur du container agents (docs/organisation.md §2) : les moteurs
// d'activation et de regie, lus par le plan (atelier, echiquier) — jamais en direct.
//
// EXPORTS PROGRESSIFS, ET L'ORDRE COMPTE — meme raison qu'a la porte du plan,
// qui porte la meme note. Le cycle est : agents → activations → plan → livres
// → agents. Avec un `module.exports = {...}` d'un bloc, le re-entrant voyait un
// objet ENCORE VIDE : `require("../agents").chambreLivres` rendait `undefined`,
// et livres.js mourait a la destructuration. Invisible par l'entree reelle
// (serveur.js remplit la porte avant d'atteindre le plan), fatal des qu'on
// entre par ici — un test, un outil, une verification a froid.
//
// On lie donc CE QUE LE RE-ENTRANT VIENDRA CHERCHER en premier, et `activations`
// — celui qui ouvre le cycle — en dernier.
module.exports.chambreLivres = require("../domaine/chambre-livres"); // les coffrets de chambre de l'onglet livres
module.exports.chambres = require("../domaine/chambres");   // l'envers du modele habitant : la frise, les salles, une chambre
module.exports.regie = require("../domaine/regie");         // chercher dans le flux, le fil d'un personnage
module.exports.activations = require("../domaine/activations"); // archives, sante, fil MJ
