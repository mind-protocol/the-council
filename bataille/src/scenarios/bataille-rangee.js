/**
 * BATAILLE_RANGEE — 4 unités contre 4, mais RIEN n'est rangé au départ :
 * chaque camp bivouaque LOIN de l'autre, hommes éparpillés, sans formation.
 * Chacun ne sait qu'une chose : « l'ennemi est par là » (la rumeur, une
 * DIRECTION vraie). Tout le reste doit émerger : les huit commandants
 * forment leurs unités, chassent, se trouvent — et la ligne de bataille se
 * dessine (ou pas) au milieu — les archers derriere, qui arrosent des
 * qu'une masse adverse entre dans leur vue. 130 hommes.
 */

import { nomGenere } from './generer.js';

const uniteBivouac = (nom, chefNom, livree, equipement, xBase, yCentre, chefPos) => {
  const sens = livree === 'bleu' ? 1 : -1;
  // éparpillement DÉTERMINISTE (arithmétique, pas de rng) autour du bivouac
  const hommes = [];
  for (let i = 0; i < 12; i++) {
    hommes.push({
      nom: nomGenere(i),
      pos: { x: xBase + ((i * 7) % 13) - 6, y: yCentre + ((i * 5) % 11) - 5 },
      escouade: i % 3,
    });
  }
  return {
    nom,
    livree,
    equipement,
    posture: 'agression',
    memoire: { ennemis: { effectif: 52, direction: sens === 1 ? 'est' : 'ouest' } },
    forme: { type: 'rangs', largeur: 4, espacementLateral: 1.2, espacementRang: 1.2 },
    zone: sens === 1 ? { x: 0, y: 0, largeur: 56, hauteur: 44 } : { x: 64, y: 0, largeur: 56, hauteur: 44 },
    // le chef part du CONSEIL DE GUERRE (les quatre chefs du camp, proches) ;
    // ses hommes savent où il est (chefCru), la formation se fait sur lui
    chef: { nom: chefNom, pos: chefPos ?? { x: xBase, y: yCentre } },
    hommes,
  };
};
const PIQUES = { arme: 'lanceLongue' };
const ECUS = { arme: 'epee', bouclier: true };
// les archers : couteau a la ceinture, arc en main, une botte de 12 fleches
const ARCS = { arme: 'couteau', arc: true, fleches: 12 };

export const BATAILLE_RANGEE = {
  titre: 'Bataille rangée (4 contre 4)',
  seed: 20260830,
  zone: { x: 0, y: 0, largeur: 120, hauteur: 44 },
  maisons: [
    { x: 28, y: 2, largeur: 6, hauteur: 5 },
    { x: 56, y: 19, largeur: 5, hauteur: 6 },
    { x: 86, y: 36, largeur: 7, hauteur: 5 },
  ],
  unites: [
    // les bivouacs bleus, à l'ouest — les quatre chefs au CONSEIL (~(13, 24))
    uniteBivouac('Lance du Nord', 'Aldric', 'bleu', PIQUES, 13, 14, { x: 12, y: 22 }),
    uniteBivouac('Écus du Roi', 'Berthaud', 'bleu', ECUS, 10, 21, { x: 14, y: 23.5 }),
    uniteBivouac('Lance du Milieu', 'Maugis', 'bleu', PIQUES, 14, 28, { x: 12, y: 25 }),
    uniteBivouac('Écus du Sud', 'Renier', 'bleu', ECUS, 11, 35, { x: 14, y: 26.5 }),
    uniteBivouac("Archers de l'If", 'Osmond', 'bleu', ARCS, 7, 24, { x: 11, y: 28 }),
    // les bivouacs rouges, à l'est — les quatre chefs au CONSEIL (~(107, 22))
    uniteBivouac('Corbeaux du Nord', 'Gormond', 'rouge', ECUS, 107, 12, { x: 108, y: 20 }),
    uniteBivouac('Piques Noires', 'Thiébaut', 'rouge', PIQUES, 109, 19, { x: 106, y: 21.5 }),
    uniteBivouac("Corbeaux de l'Aube", 'Hardouin', 'rouge', ECUS, 106, 26, { x: 108, y: 23 }),
    uniteBivouac('Piques du Couchant', 'Ulric', 'rouge', PIQUES, 108, 33, { x: 106, y: 24.5 }),
    uniteBivouac('Archers du Corbeau', 'Sanche', 'rouge', ARCS, 113, 24, { x: 109, y: 26 }),
  ],
};
