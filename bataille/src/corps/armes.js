/**
 * ❤️ Corps / Armes — LE CATALOGUE : une arme est une DONNÉE (le pendant
 * équipement du livre de manœuvres) — jamais un if/else sur le type ailleurs.
 * Chaque entrée porte ses faits physiques : allonge (l'acte 🏃 et la garde ⚙️
 * les lisent), arc et réarmement du geste, coût de la posture prête (❤️),
 * et sa silhouette rendue (🖥️ ne connaît que ces chiffres, pas les types).
 * La lance longue paie sa portée : geste lent, arc étroit, garde épuisante.
 */

// `priseMin` — la ZONE MORTE : en deçà, la pointe ne peut plus se présenter
// (une pique ne s'emploie pas à un mètre). C'est LA niche de l'épée : passer
// sous la pointe gagne l'échange — l'asymétrie n'est écrite nulle part
// ailleurs, elle émerge de ces deux chiffres.
export const ARMES = {
  // mains nues — AUCUNE pointe : pas de garde émise, rien de rendu (le
  // cheval, le prisonnier de demain) ; frapper avec = un geste pour rien
  aucune: { allonge: 0, priseMin: 0, arc: 0, periodeCoupS: 1, coutPosturePret: 0, longueurRendue: 0 },
  // la lance d'ordonnance — l'arme par défaut (l'homme droppé)
  lance: { allonge: 1.5, priseMin: 0.5, arc: 2.1, periodeCoupS: 1.5, coutPosturePret: 0.5, longueurRendue: 1.2 },
  // la pique : tenir à distance — lente, étroite, épuisante en garde haute
  lanceLongue: { allonge: 4.5, priseMin: 2.2, arc: 1.1, periodeCoupS: 2.6, coutPosturePret: 0.85, longueurRendue: 4.0 },
  // l'épée : passer SOUS la pointe — vive, large, sobre, sans zone morte
  epee: { allonge: 1.1, priseMin: 0, arc: 2.8, periodeCoupS: 0.9, coutPosturePret: 0.25, longueurRendue: 0.8 },
  // le bordon (épée à deux mains génoise) : l'arme d'Antonio Bocanegra. 
  // Une allonge monstrueuse et de la puissance, mais lente et épuisante.
  bordon: { allonge: 2.0, priseMin: 0.5, arc: 2.5, periodeCoupS: 1.8, coutPosturePret: 0.6, longueurRendue: 1.5 },
  // le couteau : l'arme du dernier recours (l'archer au contact) — courte,
  // vive, sans garde qui tienne la mesure
  couteau: { allonge: 0.6, priseMin: 0, arc: 3.0, periodeCoupS: 0.7, coutPosturePret: 0.15, longueurRendue: 0.45 },
};

// L'ARC DE TIR — pas une arme de mêlée : un PROJECTEUR DE ZONE (au-delà de
// ~100 m la cible n'est pas un homme, c'est un rectangle de sol — docs/
// recherche/le-tir.md). Cadence 6/min en régime ; bander est un EFFORT.
// Pas de portée MINIMALE : on tire très bien sur un homme à 3 m — ce qui
// fait lâcher l'arc, ce n'est pas une distance, c'est quelqu'un AU CONTACT
// de moi (la garde ennemiAuContact). La dispersion est un CÔNE : elle croît
// avec la distance — à 100 m la volée bat ±6 m, à 3 m on ne rate guère.
export const ARC_DE_TIR = {
  porteeMax: 110,       // m — la volée porte loin, la précision est une dispersion
  periodeTirS: 10,      // s — 6 flèches/minute en régime (docs : 10-12 en pointe, brièvement)
  dispersionParMetre: 0.055, // rayon battu = distance × ce facteur (~6 m à 110 m)
  vitesseVol: 35,    // m/s — le long de l'arche : ~3 s de vol à 100 m, un clin d'œil à 15 m
  coutTirS: 2,       // effort-s par flèche — bander 100 livres n'est pas un geste d'adresse
  longueurRendue: 1.0,
};

// Le bouclier : une PARADE FRONTALE géométrique — un coup qui arrive dans
// l'arc couvert (autour du cap du porteur) fait CLANG, pas une blessure.
// Pas de points de vie : la protection est un fait d'angle, pas un compteur.
export const BOUCLIER = {
  arcCouverture: 1.3, // rad (~75°) — le secteur paré, centré sur le cap : les
  //                     coups obliques passent (110° rendait le mur immortel)
  coutParadeS: 0.6,   // effort-s par CLANG — le bras de bouclier fatigue
  rayonRendu: 0.28,   // m — le rond dessiné au bras gauche
};
