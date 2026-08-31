// monde/palette.js — toutes les couleurs du monde, en un seul endroit.
//
// Une ville se lit à ses matières, pas à ses contours : la teinte dit le métier,
// le sol dit l'usage, et l'air dit la distance. Trois familles, et rien qui
// s'invente au milieu d'un module de géométrie.
"use strict";

// --- l'air ------------------------------------------------------------------
// C'est lui qui vend l'échelle. Un ciel uni et une brume grise donnent une
// maquette ; un dégradé qui blanchit vers l'horizon donne des kilomètres.
export const CIEL = {
  zenith: 0x2f4f7a,        // le bleu profond du haut
  horizon: 0xb9c4cd,       // la brume où le monde s'arrête d'être net
  bas: 0x8d8f8c,           // sous l'horizon : la terre qu'on devine
  soleil: 0xfff0d4,
  ambiance_haut: 0x9fb4d0,
  ambiance_bas: 0x453d2e,
  // La brume est EXPONENTIELLE : la perspective aérienne ne se règle pas à la
  // règle. À 9,2e-5 on perd la moitié du contraste vers 9 km — la ville entière
  // vue de la baie reste lisible, et le fond de la baie se dissout. Plus dense,
  // Port-Réal disparaît dès qu'on prend du recul ; plus clair, tout redevient
  // une maquette nette de trente centimètres.
  densite_brume: 0.000092,
};

// --- l'eau ------------------------------------------------------------------
export const EAU = {
  fond: 0x14303f,          // la Néra, vue de haut
  large: 0x1b3b4d,         // la baie, plus au large
};

// --- le sol -----------------------------------------------------------------
// Le sol de la VILLE n'est pas de la terre : c'est de la terre battue, piétinée,
// grise de cendre et de crotte. Il s'obtient en mêlant `urbain` à la campagne à
// mesure que le bâti se densifie — ce qui fait apparaître les faubourgs sans
// qu'on ait à les dessiner.
export const SOL = {
  greve: 0xa89a76,         // l'estran, le sable, la vase claire
  herbe: 0x6f7548,         // la campagne
  champ: 0x8e8a55,         // ce qui est labouré et moissonné
  bois: 0x3f5233,
  marais: 0x555c3e,
  roche: 0x8b8578,         // les sommets, où l'herbe ne tient plus
  urbain: 0x6b6252,        // la terre battue de la ville
  urbain_dense: 0x59503f,  // le cœur : plus rien n'y pousse
};

// --- ce que les hommes ont bâti ---------------------------------------------
export const BATI = {
  // par catégorie de métier (usages.py) — c'est ce qui fait apparaître le port,
  // les tanneries et la rue d'Acier sans qu'on les dessine
  cat: {
    habitat: 0x6a3b2d, commerce: 0xa17a37, artisanat: 0x5a5a64, nuisance: 0x413a29,
    plaisir: 0x8f2b3a, service: 0x84643e, culte: 0xcabfa5, civique: 0x91918a,
  },
  // à défaut de catégorie, l'usage brut
  usage: {
    taudis: 0x453320, entrepot: 0x5a4f3e, atelier: 0x5a5a64, forge: 0x4d474a,
    "maison d'officier": 0x80613f, "hôtel": 0x916d46, cabane: 0x4f4029, maison: 0x6a3b2d,
  },
  toit: 0x5e3124,
  toit_taudis: 0x4a4034,
};

export const VOIE = {
  artere: 0xb3a382, rue: 0x968a6e, ruelle: 0x746d5b, escalier: 0xa4825b,
  quai: 0x8a867e, abord: 0x6b6455,
};

export const PIERRE = {
  courtine: 0x8a8172, porte: 0xa08e68, edifice: 0x7a4e43,
};
