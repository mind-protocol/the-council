/**
 * 🧠 Cognition / Intentions — LE contrat de sortie vers 🏃 Action.
 * Union taguée à vocabulaire FERMÉ : chaque nouveau tag est une décision
 * d'archi, pas un ajout au fil de l'eau.
 */

/**
 * @typedef {{x: number, y: number}} Vec2
 * @typedef {{type: 'allerA', cible: Vec2, allure: number}
 *   | {type: 'attendre'}
 *   | {type: 'frapper', cible: number}
 *   | {type: 'tirer', zone: Vec2}
 *   | {type: 'voler', capVoulu: number, zVoulue: number, regime: string}} Intention
 */

/**
 * @param {Vec2} cible
 * @param {number} [allure] — fraction de la vitesse max (1 = plein pas ;
 *   0.35 ≈ pousser doucement / reculer sans tourner le dos)
 * @returns {Intention}
 */
// `train` (optionnel) : l'ALLURE DEMANDÉE À LA MONTURE ('pas'|'trot'|'galop')
// — un cavalier parle à son cheval ; à pied, le mot est ignoré
export const allerA = (cible, allure = 1, train) => ({ type: 'allerA', cible, allure, ...(train ? { train } : {}) });

/** @returns {Intention} */
export const attendre = () => ({ type: 'attendre' });

/**
 * Frapper UN homme — la cible est nommée (croyance de contact), mais l'ACTE
 * (🏃) juge physiquement : allonge, arc du cap, la cible y est-elle encore.
 * Un coup peut rater. @param {number} cible — id @returns {Intention}
 */
export const frapper = (cible) => ({ type: 'frapper', cible });

/**
 * Tirer une volée sur une ZONE — au-delà d'une centaine de mètres la cible
 * n'est pas un homme, c'est un rectangle de sol (docs/recherche/le-tir.md).
 * L'acte (🏃) disperse, la flèche touche qui se trouve là où elle tombe.
 * @param {Vec2} zone @returns {Intention}
 */
export const tirer = (zone) => ({ type: 'tirer', zone });

/**
 * Voler — l'intention d'un corps volant : un cap voulu, une altitude voulue,
 * un régime ('croisiere' | 'rallie' | 'basseAllure' | 'pique' | 'sortie').
 * L'actuateur (🏃 steering/vol) borne tout par le profil : le brain VEUT,
 * les ailes PEUVENT. `reste` (piqué) : la distance crue jusqu'à la cible —
 * la verticale intercepte le plan de tir sur ce reste, jamais une asymptote.
 * @param {number} capVoulu — rad @param {number} zVoulue — m
 * @param {string} [regime] @param {number} [reste] — m @returns {Intention}
 */
export const voler = (capVoulu, zVoulue, regime = 'croisiere', reste) => ({ type: 'voler', capVoulu, zVoulue, regime, ...(reste !== undefined ? { reste } : {}) });

