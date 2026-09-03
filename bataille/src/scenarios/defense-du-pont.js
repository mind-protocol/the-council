/**
 * DEFENSE_DU_PONT — le goulot, testé EN NAÏF : aucune logique de défense
 * n'existe — juste la géométrie (une rivière infranchissable, une trouée de
 * 5 m) et les cerveaux existants. Deux unités bleues (piques + épées-
 * boucliers) DÉJÀ postées devant le pont, quatre unités rouges à l'est qui
 * ne savent qu'une chose : « ils sont à l'ouest ». Ce qui doit émerger, on
 * le regarde : l'entonnoir, le mur de piques dans la trouée, la curée — ou
 * le contournement qu'on n'avait pas prévu.
 */

import { genererBan } from './generer.js';

const RIVE_HAUTE = { x: 56, y: 0, largeur: 6, hauteur: 15 };
const RIVE_BASSE = { x: 56, y: 20, largeur: 6, hauteur: 16 }; // trouée : y 15..20

const assaillants = (nom, chef, frontX, yCentre, equipement) => ({
  nom,
  livree: 'rouge',
  equipement,
  posture: 'agression',
  memoire: { ennemis: { effectif: 30, direction: 'ouest' } },
  capInitial: Math.PI,
  forme: { type: 'rangs', largeur: 4, espacementLateral: 1.2, espacementRang: 1.2 },
  zone: { x: 66, y: 0, largeur: 54, hauteur: 36 },
  chef: { nom: chef, pos: { x: frontX - 1.5, y: yCentre } },
  hommes: genererBan(11, frontX, -1, 4, yCentre),
});

export const DEFENSE_DU_PONT = {
  titre: 'La défense du pont',
  seed: 20260831,
  zone: { x: 0, y: 0, largeur: 120, hauteur: 36 },
  maisons: [RIVE_HAUTE, RIVE_BASSE, { x: 20, y: 4, largeur: 6, hauteur: 5 }],
  unites: [
    {
      nom: 'Piques du Pont',
      livree: 'bleu',
      posture: 'defense',
      memoire: { ennemis: { effectif: 48, direction: 'est' } }, // l axe de menace du barrage
      equipement: { arme: 'lanceLongue' }, // le bouchon : 4 de front = la trouée
      capInitial: 0,
      ordreInitial: 'surMoi',
      forme: { type: 'rangs', largeur: 4, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 0, y: 0, largeur: 56, hauteur: 36 },
      chef: { nom: 'Aldric', pos: { x: 54.5, y: 17.5 } },
      hommes: genererBan(15, 53.3, 1, 4, 17.5),
    },
    {
      nom: "Garde de l'Écu",
      livree: 'bleu',
      posture: 'defense',
      memoire: { ennemis: { effectif: 48, direction: 'est' } },
      equipement: { arme: 'epee', bouclier: true }, // la réserve derrière les piques
      capInitial: 0,
      ordreInitial: 'surMoi',
      forme: { type: 'rangs', largeur: 5, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 0, y: 0, largeur: 56, hauteur: 36 },
      chef: { nom: 'Berthaud', pos: { x: 47, y: 17.5 } },
      hommes: genererBan(15, 45.8, 1, 5, 17.5),
    },
    // quatre bandes, dispersées sur la rive est — elles devront TROUVER le pont
    assaillants('Bande du Loup', 'Gormond', 80, 6, { arme: 'epee', bouclier: true }),
    assaillants('Bande du Freux', 'Maugis', 95, 12, { arme: 'lance' }),
    assaillants("Bande de l'Ours", 'Hardouin', 88, 24, { arme: 'epee', bouclier: true }),
    assaillants('Bande du Sanglier', 'Thiébaut', 102, 30, { arme: 'lance' }),
  ],
};
