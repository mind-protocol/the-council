/**
 * FACE_A_FACE — le laboratoire du combat : deux unités DÉJÀ en rangs
 * constitués, premières lignes à 5 m, face à face (capInitial), ordre
 * EN_FORMATION « sur moi » injecté aux deux au chargement. Pas de posture
 * d'agression : personne ne manœuvre, la rencontre est déjà là.
 */

const rangsBleus = [];
const nomsBleus = ['Paul', 'Jean', 'Thibaut', 'Gauthier', 'Renaud', 'Bertrand', 'Guiot', 'Foulques', 'Eudes', 'Hugues', 'Raoul', 'Enguerrand', 'Barnabé', 'Colin', 'Anselme', 'Perrin', 'Mathis', 'Rémi', 'Ancel', 'Josse'];
nomsBleus.forEach((nom, i) => {
  rangsBleus.push({
    nom,
    // rangs de 6 derrière le chef : x décroît vers l'arrière, y s'étale
    pos: { x: 44.8 - Math.floor(i / 6) * 1.2, y: 7 + (i % 6) * 1.2 },
    escouade: i % 4,
  });
});
const rangsRouges = [];
const nomsRouges = ['Ulric', 'Baudouin', 'Thierry', 'Amaury', 'Garin', 'Ogier', 'Landry', 'Wautier', 'Sigebert', 'Frotaire'];
nomsRouges.forEach((nom, i) => {
  rangsRouges.push({
    nom,
    pos: { x: 51.2 + Math.floor(i / 5) * 1.2, y: 7.6 + (i % 5) * 1.2 },
    escouade: i % 2,
  });
});

export const FACE_A_FACE = {
  titre: 'Face à face',
  seed: 20260829,
  zone: { x: 20, y: 0, largeur: 60, hauteur: 20 },
  maisons: [{ x: 30, y: 2, largeur: 5, hauteur: 4 }],
  unites: [
    {
      nom: 'Première Lance',
      livree: 'bleu',
      equipement: { arme: 'lanceLongue' }, // le mur de piques
      capInitial: 0,
      posture: 'agression', // face à l'est — vers les rouges
      ordreInitial: 'surMoi',
      forme: { type: 'rangs', largeur: 6, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 20, y: 0, largeur: 28, hauteur: 20 },
      chef: { nom: 'Aldric', pos: { x: 46, y: 10 } },
      hommes: rangsBleus,
    },
    {
      nom: 'Bannière du Corbeau',
      livree: 'rouge',
      equipement: { arme: 'epee', bouclier: true }, // l epee-bouclier : passer sous la pointe
      capInitial: Math.PI,
      posture: 'agression', // face à l'ouest — vers les bleus
      ordreInitial: 'surMoi',
      forme: { type: 'rangs', largeur: 5, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 52, y: 0, largeur: 28, hauteur: 20 },
      chef: { nom: 'Gormond', pos: { x: 51, y: 10 } },
      hommes: rangsRouges,
    },
  ],
};
