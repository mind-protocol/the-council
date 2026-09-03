/**
 * FOULE — une bataille de n hommes, engendree, pour les bancs.
 *
 * Deux camps qui bivouaquent et se cherchent, meme forme que BATAILLE_RANGEE
 * mise a l'echelle : des unites de 30 en grille, chacune avec son chef. Rien
 * n'est range au depart. Ce n'est pas un scenario du jeu — il n'entre pas au
 * catalogue et ne nomme aucun lieu : c'est de la matiere a mesurer.
 */

import { nomGenere } from '../src/scenarios/generer.js';

/**
 * Une bataille de n hommes, deux camps qui bivouaquent et se cherchent.
 * Meme forme que BATAILLE_RANGEE, mise a l'echelle : des unites de 30, en
 * grille, chacune avec son chef. Rien n'est range au depart.
 */
export function foule(n) {
  const PAR_UNITE = 30;
  const unites = [];
  const parCamp = Math.ceil(n / 2 / PAR_UNITE);
  for (const livree of ['bleu', 'rouge']) {
    const sens = livree === 'bleu' ? 1 : -1;
    for (let u = 0; u < parCamp; u++) {
      const xBase = sens > 0 ? 60 + (u % 5) * 26 : 640 - (u % 5) * 26;
      const yCentre = 40 + Math.floor(u / 5) * 34;
      const hommes = [];
      for (let i = 0; i < PAR_UNITE; i++) {
        hommes.push({
          nom: nomGenere(i),
          pos: { x: xBase + ((i * 7) % 13) - 6, y: yCentre + ((i * 5) % 11) - 5 },
          escouade: i % 3,
        });
      }
      unites.push({
        nom: `${livree} ${u}`,
        livree,
        posture: 'agression',
        memoire: { ennemis: { effectif: PAR_UNITE, direction: sens > 0 ? 'est' : 'ouest' } },
        equipement: { arme: 'lance' },
        capInitial: sens > 0 ? 0 : Math.PI,
        forme: { type: 'rangs', largeur: 6, espacementLateral: 1.2, espacementRang: 1.2 },
        zone: { x: 20, y: 20, largeur: 660, hauteur: 300 },
        chef: { nom: `chef ${livree} ${u}`, pos: { x: xBase, y: yCentre } },
        hommes,
      });
    }
  }
  return { titre: `foule de ${n}`, seed: 1305, zone: { x: 0, y: 0, largeur: 700, hauteur: 340 }, maisons: [], unites };
}
