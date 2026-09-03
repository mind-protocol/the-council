/**
 * LES OISEAUX DU CHAMP — une colonne en marche, et deux bêtes au-dessus.
 *
 * Le banc d'essai du vol : la colonne marche au milieu du champ, les deux
 * bêtes tournent au-dessus d'elle. À découvert, rien entre le ciel et elle, de
 * quoi voir les deux profils faire deux métiers différents sur la même
 * machine. Le corbeau suit l'armée, tient son cercle à soixante-cinq mètres,
 * se laisse tomber et tourne bas longtemps. Le faucon se poste à cent
 * quatre-vingts, ferme les ailes, fond à quatre-vingts mètres par seconde et
 * remonte aussitôt.
 *
 * Aucun des deux ne touche personne : c'est le point. On les regarde voler.
 */

import { genererBan } from './generer.js';

export const LES_OISEAUX = {
  titre: 'Les oiseaux du champ',
  seed: 20260902,
  zone: { x: 0, y: 0, largeur: 400, hauteur: 250 },
  maisons: [], // à découvert : rien entre le ciel et la colonne
  oiseaux: [
    { profil: 'corbeau', livree: 'noir', pos: { x: 170, y: 95 }, z: 65, cap: 0 },
    { profil: 'faucon', livree: 'blanc', pos: { x: 150, y: 160 }, z: 185, cap: 0 },
  ],
  unites: [
    {
      nom: 'Bannière du Corbeau',
      livree: 'rouge',
      equipement: { arme: 'epee', bouclier: true },
      posture: 'agression',
      memoire: { ennemis: { effectif: 15, direction: 'ouest' } },
      capInitial: Math.PI,
      ordreInitial: 'ratisser',
      forme: { type: 'rangs', largeur: 5, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 0, y: 0, largeur: 400, hauteur: 250 },
      chef: { nom: 'Gormond', pos: { x: 202.5, y: 125 } },
      hommes: genererBan(19, 204, -1, 5, 125),
    },
  ],
};
