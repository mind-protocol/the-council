/**
 * LA_CONROI — le laboratoire de l'attelage : huit lances montées (épée et
 * écu, un cheval sous chaque homme) traversent le champ vers une bande à
 * pied. Ce qu'on regarde : le train de la monture, la poussée du choc
 * (des renversés), et ce que l'infanterie y oppose. Le refus du cheval
 * devant les piques viendra à l'étape suivante.
 */

import { genererBan } from './generer.js';

export const LA_CONROI = {
  titre: 'La conroi',
  seed: 20260902,
  zone: { x: 0, y: 0, largeur: 120, hauteur: 24 },
  maisons: [],
  unites: [
    {
      nom: 'Conroi du Lys',
      livree: 'bleu',
      equipement: { arme: 'epee', bouclier: true },
      monture: true, // un cheval sous chaque homme
      posture: 'agression',
      memoire: { ennemis: { effectif: 20, direction: 'est' } },
      capInitial: 0,
      // la charge est sonnee au lever de rideau : le laboratoire teste le choc,
      // pas l'humeur de l'arbitre
      ordreInitial: 'charger',
      sansCommandant: true, // Aubert mène du front — pas d'état-major qui écrase la charge
      forme: { type: 'rangs', largeur: 8, espacementLateral: 2.0, espacementRang: 2.5 },
      zone: { x: 0, y: 0, largeur: 60, hauteur: 24 },
      chef: { nom: 'Aubert', pos: { x: 21, y: 12 } },
      hommes: [
        { nom: 'Girout', pos: { x: 18, y: 5 }, escouade: 0 },
        { nom: 'Herluin', pos: { x: 18, y: 8 }, escouade: 0 },
        { nom: 'Aimeri', pos: { x: 18, y: 11 }, escouade: 0 },
        { nom: 'Bovon', pos: { x: 18, y: 14 }, escouade: 1 },
        { nom: 'Gaydon', pos: { x: 18, y: 17 }, escouade: 1 },
        { nom: 'Naimes', pos: { x: 15, y: 7 }, escouade: 1 },
        { nom: 'Berart', pos: { x: 15, y: 12 }, escouade: 2 },
        { nom: 'Estout', pos: { x: 15, y: 16 }, escouade: 2 },
      ],
    },
    // le laboratoire du REFUS : au nord le mur de piques (le cheval doit se
    // dérober), au sud les écus (la charge doit porter) — la comparaison
    // dans une seule scène
    {
      nom: 'Piques Noires',
      livree: 'rouge',
      equipement: { arme: 'lanceLongue' },
      posture: 'defense',
      memoire: { ennemis: { effectif: 9, direction: 'ouest' } },
      capInitial: Math.PI,
      ordreInitial: 'surMoi',
      forme: { type: 'rangs', largeur: 5, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 60, y: 0, largeur: 60, hauteur: 12 },
      chef: { nom: 'Thiébaut', pos: { x: 91.2, y: 6.5 } },
      hommes: genererBan(9, 90, -1, 5, 6.5),
    },
    {
      nom: 'Bannière du Corbeau',
      livree: 'rouge',
      equipement: { arme: 'epee', bouclier: true },
      posture: 'defense',
      memoire: { ennemis: { effectif: 9, direction: 'ouest' } },
      capInitial: Math.PI,
      ordreInitial: 'surMoi',
      forme: { type: 'rangs', largeur: 5, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 60, y: 12, largeur: 60, hauteur: 12 },
      chef: { nom: 'Gormond', pos: { x: 91.2, y: 17.5 } },
      hommes: genererBan(9, 90, -1, 5, 17.5),
    },
  ],
};
