/**
 * 🧠 Langage / Décrire — MATH → PAROLE : une croyance → du français.
 * Consommateurs : étiquettes du calque perception, inspecteur, et demain
 * l'ÉMISSION du commandant (il formule depuis sa carte mentale : émettre
 * passe par decrire, recevoir par resoudre — symétrie complète).
 * PUR. Le repère écran a y vers le bas : le sud est en bas.
 */

const DIRECTIONS = [
  "à l'est", 'au sud-est', 'au sud', 'au sud-ouest',
  "à l'ouest", 'au nord-ouest', 'au nord', 'au nord-est',
];

/** @param {number} cap — radians @returns {string} « au nord-est »… */
export function direction(cap) {
  const secteur = Math.round(cap / (Math.PI / 4));
  return DIRECTIONS[((secteur % 8) + 8) % 8];
}

const MOTS_DIRECTIONS = ['est', 'sud-est', 'sud', 'sud-ouest', 'ouest', 'nord-ouest', 'nord', 'nord-est'];

/** Le mot nu (pour une RefLieu {type:'direction'}). @param {number} cap */
export function motDirection(cap) {
  const secteur = Math.round(cap / (Math.PI / 4));
  return MOTS_DIRECTIONS[((secteur % 8) + 8) % 8];
}

/** @param {number} n @returns {string} « une vingtaine »… */
export function effectifEnMots(n) {
  if (n <= 7) return `${n} homme${n > 1 ? 's' : ''}`;
  if (n <= 13) return 'une dizaine';
  if (n <= 17) return 'une quinzaine';
  if (n <= 24) return 'une vingtaine';
  if (n <= 35) return 'une trentaine';
  return `environ ${Math.round(n / 10) * 10}`;
}

/**
 * Décrit une croyance-tas. « mon unité — une ligne de ~7 m de front, face
 * au nord (une vingtaine) » / « mon escouade — un attroupement (5 hommes) ».
 * @param {{etiquette, effectif, cap?, largeur?, profondeur?, premiereLigne?}} tas
 * @returns {string}
 */
export function decrireTas(tas) {
  const qui =
    tas.etiquette === 'escouade' ? 'mon escouade'
    : tas.etiquette === 'unite' ? 'mon unité'
    : tas.etiquette === 'inconnu' && tas.livree ? `une unité ${tas.livree}`
    : 'un groupe';
  if (!tas.barycentre) {
    // croyance sans position (rumeur, mémoire) : « quelque part »
    return `${qui} — quelque part (${effectifEnMots(tas.effectif)})`;
  }
  if (tas.cap === undefined || tas.largeur === undefined) {
    // le gabarit et l'altitude se DISENT — des faits, jamais des types : un
    // tas bien plus lourd que son compte est énorme, un tas là-haut vole
    const enorme = (tas.poids ?? 0) > (tas.effectif ?? 1) * 3 ? ' énorme' : '';
    const ciel = (tas.z ?? 0) > 30 ? ', dans le ciel' : '';
    return `${qui} — un attroupement${enorme}${ciel} (${effectifEnMots(tas.effectif)})`;
  }
  const silhouette =
    tas.profondeur > tas.largeur * 1.5 ? 'une colonne'
    : tas.largeur > tas.profondeur * 1.5 ? 'une ligne'
    : 'un bloc';
  const front = Math.round(tas.premiereLigne?.largeur ?? tas.largeur);
  return `${qui} — ${silhouette} de ~${front} m de front, face ${direction(tas.cap)} (${effectifEnMots(tas.effectif)})`;
}
