/**
 * LA_VOLEE — le laboratoire du tir : une ligne d'archers (couteau à la
 * ceinture, carquois COMPTÉS — le freestyle n'existe pas) qui tient sur
 * place, face à une bande d'épées-boucliers qui doit traverser À DÉCOUVERT.
 * Ce qui doit émerger : les volées pendant la traversée, les carquois qui
 * se vident, puis le corps-à-corps au couteau — et son issue.
 */

import { genererBan } from './generer.js';

const archers = [];
const NOMS_ARCHERS = ['Yvon', 'Maheu', 'Gaudin', 'Rainier', 'Sylvestre', 'Amiel',
  'Bérard', 'Cadoc', 'Denisot', 'Ernaut', 'Fulbert', 'Guérin'];
NOMS_ARCHERS.forEach((nom, i) => {
  archers.push({ nom, pos: { x: 30, y: 5.4 + i * 1.2 }, escouade: i % 3 });
});

export const LA_VOLEE = {
  titre: 'La volée',
  seed: 20260901,
  zone: { x: 0, y: 0, largeur: 140, hauteur: 24 },
  maisons: [], // à découvert : pas un mur entre l'arc et la traversée
  unites: [
    {
      nom: "Compagnie de l'If",
      livree: 'bleu',
      // le couteau à la ceinture, l'arc en main, une botte de 12 flèches
      equipement: { arme: 'couteau', arc: true, fleches: 12 },
      posture: 'defense',
      memoire: { ennemis: { effectif: 20, direction: 'est' } },
      capInitial: 0,
      ordreInitial: 'surMoi',
      forme: { type: 'rangs', largeur: 12, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 0, y: 0, largeur: 45, hauteur: 24 },
      chef: { nom: 'Osmond', pos: { x: 31.2, y: 12 } },
      hommes: archers,
    },
    {
      nom: 'Bannière du Corbeau',
      livree: 'rouge',
      equipement: { arme: 'epee', bouclier: true },
      posture: 'agression',
      memoire: { ennemis: { effectif: 13, direction: 'ouest' } },
      capInitial: Math.PI,
      // l'assaut est deja ordonne : la traversee ne depend pas de l'humeur
      // de l'arbitre — le rideau se leve sur une bande EN MARCHE
      ordreInitial: 'ratisser',
      forme: { type: 'rangs', largeur: 5, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 45, y: 0, largeur: 95, hauteur: 24 },
      // 80 m de terrain nu : la zone battue existe AVANT le fer
      chef: { nom: 'Gormond', pos: { x: 108.5, y: 12 } },
      hommes: genererBan(19, 110, -1, 5, 12),
    },
  ],
};
