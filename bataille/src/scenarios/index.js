/**
 * Scénarios — PURE DONNÉE : seed, zone (le théâtre), maisons, UNITÉS, et
 * parfois des OISEAUX (le ciel est à part : ni drill, ni forme, ni camp). Un fichier par scénario ; les aides de génération
 * partagées vivent dans generer.js. Chaque unité : livrée, forme, zone de
 * flânerie propre, chef nommé (panache), hommes nommés en escouades.
 * `ordreDrill` implicite : le chef, puis les hommes dans l'ordre de la liste
 * (les habitués de l'avant en tête). La forme est un vocabulaire ouvert —
 * 'rangs' aujourd'hui. Personne ne se connaît d'un camp à l'autre —
 * l'interprétation « ennemi » sera une croyance (🧠), jamais un tag.
 */

import { PREMIERE_LANCE } from './premiere-lance.js';
import { FACE_A_FACE } from './face-a-face.js';
import { BATAILLE_RANGEE } from './bataille-rangee.js';
import { DEFENSE_DU_PONT } from './defense-du-pont.js';
import { LA_VOLEE } from './la-volee.js';
import { LA_CONROI } from './la-conroi.js';
import { ASSAUT_DE_RUE } from './assaut-de-rue.js';
import { LES_OISEAUX } from './les-oiseaux.js';

export { PREMIERE_LANCE, FACE_A_FACE, BATAILLE_RANGEE, DEFENSE_DU_PONT, LA_VOLEE, LA_CONROI, ASSAUT_DE_RUE, LES_OISEAUX };

// Le catalogue — la LISTE que le sélecteur (🖥️) affiche ; l'id est stable,
// le titre vit dans le scénario lui-même. Toujours de la pure donnée.
export const SCENARIOS = [
  { id: 'la-conroi', scenario: LA_CONROI },
  { id: 'la-volee', scenario: LA_VOLEE },
  { id: 'assaut-de-rue', scenario: ASSAUT_DE_RUE },
  { id: 'les-oiseaux', scenario: LES_OISEAUX },
  { id: 'defense-du-pont', scenario: DEFENSE_DU_PONT },
  { id: 'bataille-rangee', scenario: BATAILLE_RANGEE },
  { id: 'premiere-lance', scenario: PREMIERE_LANCE },
  { id: 'face-a-face', scenario: FACE_A_FACE },
];
