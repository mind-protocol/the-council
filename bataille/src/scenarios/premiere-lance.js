/**
 * PREMIERE_LANCE — le ratissage fondateur : deux unités, deux livrées,
 * hommes éparpillés. La Première Lance (piques, agression, rumeur « une
 * bande ennemie, vers l'est ») ratisse sa zone ; la Bannière du Corbeau
 * (épées-boucliers) flâne à l'est. Personne ne se connaît d'un camp à
 * l'autre — « ennemi » sera une croyance (🧠), jamais un tag.
 */

export const PREMIERE_LANCE = {
  titre: 'Ratissage — Première Lance',
  seed: 20260828,

  // le théâtre entier (drag & drop, cadrage) — chaque unité a SA zone
  zone: { x: 0, y: 0, largeur: 100, hauteur: 20 },

  maisons: [
    { x: 10, y: 4, largeur: 6, hauteur: 5 },
    { x: 24, y: 11, largeur: 8, hauteur: 4 },
    { x: 38, y: 3, largeur: 5, hauteur: 6 },
    { x: 68, y: 9, largeur: 6, hauteur: 5 },
  ],

  unites: [
    {
      nom: 'Première Lance',
      livree: 'bleu',
      equipement: { arme: 'lanceLongue' }, // le mur de piques
      // l'optique d'agression + la RUMEUR : « une bande ennemie, vers l'est »
      // (sans position, mais une direction VRAIE) — le déclencheur du
      // ratissage, qui biaisera ses secteurs vers l'est... jusqu'au contact
      posture: 'agression',
      memoire: { ennemis: { effectif: 11, direction: 'est' } },
      // espacements ≥ 1.2 m : la surface entre voisins (~0.5 m) sort de la
      // portée de répulsion — la physique ne combat pas le drill
      forme: { type: 'rangs', largeur: 6, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 0, y: 0, largeur: 50, hauteur: 20 },
      chef: { nom: 'Aldric', pos: { x: 21, y: 8 } },
      // 20 hommes, 4 escouades de 5 (éparpillées : i % 4)
      hommes: [
        { nom: 'Paul', pos: { x: 2, y: 2 }, escouade: 0 },
        { nom: 'Jean', pos: { x: 7, y: 9 }, escouade: 1 },
        { nom: 'Thibaut', pos: { x: 3, y: 16 }, escouade: 2 },
        { nom: 'Gauthier', pos: { x: 12, y: 12 }, escouade: 3 },
        { nom: 'Renaud', pos: { x: 18, y: 3 }, escouade: 0 },
        { nom: 'Bertrand', pos: { x: 18, y: 17 }, escouade: 1 },
        { nom: 'Guiot', pos: { x: 22, y: 6 }, escouade: 2 },
        { nom: 'Foulques', pos: { x: 21, y: 14 }, escouade: 3 },
        { nom: 'Eudes', pos: { x: 27, y: 3 }, escouade: 0 },
        { nom: 'Hugues', pos: { x: 28, y: 17 }, escouade: 1 },
        { nom: 'Raoul', pos: { x: 33, y: 8 }, escouade: 2 },
        { nom: 'Enguerrand', pos: { x: 33, y: 17 }, escouade: 3 },
        { nom: 'Barnabé', pos: { x: 36, y: 13 }, escouade: 0 },
        { nom: 'Colin', pos: { x: 41, y: 11 }, escouade: 1 },
        { nom: 'Anselme', pos: { x: 44, y: 2 }, escouade: 2 },
        { nom: 'Perrin', pos: { x: 45, y: 17 }, escouade: 3 },
        { nom: 'Mathis', pos: { x: 47, y: 8 }, escouade: 0 },
        { nom: 'Rémi', pos: { x: 9, y: 18 }, escouade: 1 },
        { nom: 'Ancel', pos: { x: 14, y: 2 }, escouade: 2 },
        { nom: 'Josse', pos: { x: 48, y: 13 }, escouade: 3 },
      ],
    },
    {
      nom: 'Bannière du Corbeau',
      livree: 'rouge',
      equipement: { arme: 'epee', bouclier: true }, // l epee-bouclier : passer sous la pointe
      forme: { type: 'rangs', largeur: 5, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 60, y: 0, largeur: 40, hauteur: 20 },
      chef: { nom: 'Gormond', pos: { x: 80, y: 10 } },
      // 10 hommes, 2 escouades de 5
      hommes: [
        { nom: 'Ulric', pos: { x: 63, y: 3 }, escouade: 0 },
        { nom: 'Baudouin', pos: { x: 66, y: 16 }, escouade: 1 },
        { nom: 'Thierry', pos: { x: 74, y: 2 }, escouade: 0 },
        { nom: 'Amaury', pos: { x: 77, y: 17 }, escouade: 1 },
        { nom: 'Garin', pos: { x: 84, y: 4 }, escouade: 0 },
        { nom: 'Ogier', pos: { x: 87, y: 15 }, escouade: 1 },
        { nom: 'Landry', pos: { x: 92, y: 8 }, escouade: 0 },
        { nom: 'Wautier', pos: { x: 95, y: 17 }, escouade: 1 },
        { nom: 'Sigebert', pos: { x: 97, y: 3 }, escouade: 0 },
        { nom: 'Frotaire', pos: { x: 90, y: 12 }, escouade: 1 },
      ],
    },
  ],
};
