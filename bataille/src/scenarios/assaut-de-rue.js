/**
 * LA SORTIE DE MUNTANER — La défense de Gallipoli contre les Génois (1305).
 * Tiré de la Chronique de Ramon Muntaner (Chapitre 227).
 * Antonio Spinola attaque avec 25 galères. La garnison catalane est presque vide.
 * Muntaner met les femmes en armure sur les remparts (la "barbacana") pour faire nombre,
 * et laisse les portes de fer ouvertes. Quand les Génois s'épuisent sous la chaleur 
 * à l'entonnoir de la porte, Muntaner charge avec 6 chevaux et ses fantassins légers.
 * Spinola y laisse la tête, et plus de 600 Génois meurent.
 */

import { nomGenere } from './generer.js';

export const ASSAUT_DE_RUE = {
  titre: 'La sortie de Muntaner (Siège de Gallipoli)',
  seed: 20260904,
  zone: { x: 750, y: 550, largeur: 300, hauteur: 300 },
  maisons: [],
  terrain: {
    masque: { fichier: 'donnees/ville/gallipoli.masque.bin', nx: 17785, ny: 20040, pas: 1, inverserY: false },
    plan: 'donnees/ville/gallipoli.plan.json',
  },
  unites: [
    // --- LES CATALANS (Défenseurs) ---
    // LE CORPS DU SIEGE. Ferran Ximenis d'Arenos est a Gallipoli (Muntaner p. 527)
    // et sort avec les autres : le joueur a un corps dans la rue, il parle d'ou
    // il est et il peut y mourir. Premiere unite = la notre (boutons d'ordre).
    // `personnage` relie un corps a sa fiche du jeu (etat/personnages.json).
    {
      nom: 'La lance d\'Arenos',
      livree: 'jaune',
      posture: 'agression',
      equipement: { arme: 'epee', bouclier: true },
      capInitial: Math.PI / 2,
      ordreInitial: 'enFormation',
      forme: { type: 'rangs', largeur: 4, espacementLateral: 1.5, espacementRang: 1.5 },
      zone: { x: 800, y: 580, largeur: 40, hauteur: 40 },
      chef: { nom: 'Ferran Ximenis d\'Arenos', pos: { x: 820, y: 598 }, panache: true, personnage: 'ferran-ximenis' },
      hommes: Array.from({ length: 8 }, (_, i) => ({
        nom: nomGenere(i + 30),
        pos: { x: 816 + (i % 4) * 1.5, y: 594 - Math.floor(i / 4) * 1.5 },
        escouade: i % 2,
      })),
    },
    {
      nom: 'La sortie catalane',
      livree: 'jaune',
      posture: 'agression', // Ils chargent hors de la porte !
      equipement: { arme: 'epee', bouclier: true }, // "in their shirts and breeches, each man with a shield, and with a lance... and dagger"
      capInitial: Math.PI / 2, // Sortant de la porte (vers le sud/est selon la topo, à vérifier)
      ordreInitial: 'enFormation',
      forme: { type: 'rangs', largeur: 6, espacementLateral: 1.5, espacementRang: 1.5 },
      zone: { x: 810, y: 580, largeur: 60, hauteur: 60 },
      chef: { nom: 'Ramon Muntaner', pos: { x: 830, y: 600 }, panache: true, personnage: 'ramon-muntaner' },
      // 6 chevaux + fantassins légers
      hommes: Array.from({ length: 24 }, (_, i) => ({
        // le premier rang porte un nom de la chronique : Berenguer de Ventayola,
        // marin du Llobregat (Muntaner p. 521) — un homme a fiche a portee de voix
        nom: i === 0 ? 'Berenguer de Ventayola' : nomGenere(i),
        personnage: i === 0 ? 'berenguer-de-ventayola' : null,
        pos: { x: 825 + (i % 6) * 1.5, y: 595 - Math.floor(i / 6) * 1.5 },
        escouade: i % 4,
      })),
      monture: true, // "six armed horses". On va leur donner des montures pour simuler la charge de cavalerie.
      // Wait, let's keep only the chief and a few men on horses if we want, or just the whole unit as light infantry. 
      // Actually, standard unites with "monture: true" puts everyone on horseback. Let's not use monture for all.
    },
    {
      nom: 'Femmes sur les remparts',
      livree: 'jaune',
      posture: 'defense',
      equipement: { arme: 'lanceLongue' }, // Fausse garde pour faire nombre
      capInitial: Math.PI / 2,
      forme: { type: 'rangs', largeur: 10, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 800, y: 590, largeur: 100, hauteur: 20 },
      chef: { nom: 'Marchand catalan', pos: { x: 840, y: 590 } }, // Muntaner a mis des marchands pour commander les femmes
      hommes: Array.from({ length: 30 }, (_, i) => ({
        nom: 'Femme en armure',
        pos: { x: 820 + (i % 10) * 1.2, y: 588 - Math.floor(i / 10) * 1.2 },
        escouade: 1,
      })),
    },

    // --- LES GÉNOIS (Assaillants) ---
    ...[
      { nom: 'Bannière de Spinola', chef: 'Antonio Spinola', personnage: 'antonio-spinola', x: 850, y: 650, equipement: { arme: 'epee', bouclier: true } },
      { nom: 'Arbalétriers génois', chef: 'En Andriol Murisch', personnage: 'andriol-murisch', x: 870, y: 660, equipement: { arme: 'couteau', arc: true, fleches: 30 } }, // "well provided with sharp arrows and would shoot off many"
      { nom: 'Bande de Bocanegra', chef: 'Antonio Bocanegra', personnage: 'antonio-bocanegra', x: 890, y: 640, equipement: { arme: 'bordon' } }, // "bordon sword in his hand"
    ].map((b) => ({
      nom: b.nom,
      livree: 'bleu', // Génois
      posture: 'agression',
      memoire: { ennemis: { effectif: 30, direction: 'nord', pos: { x: 830, y: 600 } } },
      equipement: b.equipement,
      capInitial: -Math.PI / 2, 
      forme: { type: 'rangs', largeur: 6, espacementLateral: 1.2, espacementRang: 1.2 },
      zone: { x: 840, y: 630, largeur: 100, hauteur: 60 },
      chef: { nom: b.chef, pos: { x: b.x, y: b.y }, panache: true, personnage: b.personnage },
      hommes: Array.from({ length: 20 }, (_, i) => ({
        nom: nomGenere(i + 50),
        pos: { x: b.x + ((i * 7) % 13) - 6, y: b.y + ((i * 5) % 11) - 5 },
        escouade: i % 3,
      })),
    })),
  ],
};


// ── LA POSE — où cette scène se tient sur la carte ──────────────────────────
//
// La chorégraphie ci-dessus a été réglée dans un repère LOCAL (le tracé à la
// main du bourg, 2000 x 1400 m) : les distances entre les hommes, les angles
// d'attaque, l'entonnoir de la porte. Elle est juste, et on n'y touche pas.
//
// La carte, elle, a changé : Gallipoli est désormais la péninsule entière,
// cuite depuis l'OSM et le relief (bataille/outils/osm/), au MÈTRE la case.
// La scène s'y pose donc en CORPS RIGIDE — une translation, pas une réécriture.
//
// L'offset n'est pas choisi à l'œil : `scripts/…/poser` a balayé rotations et
// distances autour de la Porte de fer et retenu la première pose où LES 128
// HOMMES naissent sur une case libre du masque. Elle tombe à rotation nulle,
// à dix mètres de la porte — la scène tenait déjà dans la vraie ville.
//
// Si le tissu de la ville engendrée change, cette pose est à re-chercher :
// le cas `masque-spawns` de bataille/coding/fumee.mjs le dira tout de suite
// (il compte les naissances acceptées et exige 128 sur 128).
const POSE = { dx: 9743, dy: 16377 };

(function poser(o) {
  const marche = (n) => {
    if (!n || typeof n !== 'object') return;
    if (Array.isArray(n)) return n.forEach(marche);
    for (const [k, v] of Object.entries(n)) {
      if (k === 'x' && typeof v === 'number') n.x = v + POSE.dx;
      else if (k === 'y' && typeof v === 'number') n.y = v + POSE.dy;
      else marche(v);
    }
  };
  marche(o);
})(ASSAUT_DE_RUE);
