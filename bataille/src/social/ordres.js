/**
 * 📯 Social / Ordres — LE format : un ordre est de la PAROLE. Vocabulaire
 * FERMÉ (verbes) + références SYMBOLIQUES (le locuteur, un lieu nommé, une
 * unité) — JAMAIS de coordonnées : la résolution spatiale se fait chez le
 * RÉCEPTEUR, contre ses croyances. C'est ce qui garde la formation dynamique
 * (et permet de mal comprendre, demain).
 * Le récepteur reçoit {ordre, emetteur} — on sait toujours QUI a parlé
 * (c'est un percept). Chaque nouveau verbe est une décision d'archi.
 *
 * L'IMPLICITE : ce que l'ordre ne dit pas est DÉDUIT par le récepteur
 * (convention, doctrine) — et peut toujours être explicité par l'émetteur.
 * Ex. : « En formation ! » tout court ⇒ à peu près DE FACE, devant le
 * locuteur, locuteur dehors. « … sur moi ! » ⇒ le locuteur est dedans,
 * la formation prend son orientation. La déduction vit dans la 🧠
 * (brains/soldat/interpretation.js), jamais ici.
 */

/**
 * @typedef {{type: 'locuteur'}
 *   | {type: 'lieuNomme', nom: string}
 *   | {type: 'unite', nom: string}} RefLieu — référence symbolique, du texte
 *
 * @typedef {{verbe: 'EN_FORMATION', sur?: RefLieu}
 *   | {verbe: 'REPOS'}} Ordre
 *
 * @typedef {{ordre: Ordre, emetteur: number}} OrdreRecu — tel qu'entendu
 */

/** « En formation ! » — avec `sur`, ex. sur le locuteur : « … sur moi ! » */
export const enFormation = (sur) => ({ verbe: 'EN_FORMATION', ...(sur ? { sur } : {}) });

/** « Repos ! » */
export const repos = () => ({ verbe: 'REPOS' });

/**
 * « Ratissez vers <direction> ! » — ⏸️ STUB (manœuvre ratisser à venir).
 * @param {{type: 'direction', nom: 'nord'|'sud'|'est'|'ouest'}} [vers]
 */
export const ratisser = (vers) => ({ verbe: 'RATISSER', ...(vers ? { vers } : {}) });

/**
 * « Chargez ! » — sus à l'ennemi. La cible n'est JAMAIS une coordonnée :
 * chaque récepteur résout contre SES ennemis crus, la direction criée sinon.
 * @param {{type: 'direction', nom: string}} [vers]
 */
export const charger = (vers) => ({ verbe: 'CHARGER', ...(vers ? { vers } : {}) });

/**
 * « Reculez vers <direction> ! » — le DÉCROCHAGE : un bond de formation en
 * arrière, FRONT AU DANGER (on recule dos au mouvement, jamais dos à la
 * pointe). `vers` = la direction DU MOUVEMENT.
 * @param {{type: 'direction', nom: string}} [vers]
 */
export const reculer = (vers) => ({ verbe: 'RECULER', ...(vers ? { vers } : {}) });

/** Le texte crié — ce que les bulles affichent. @param {Ordre} ordre */
export function enTexte(ordre) {
  switch (ordre.verbe) {
    case 'EN_FORMATION': {
      if (!ordre.sur) return 'En formation !';
      if (ordre.sur.type === 'locuteur') return 'En formation sur moi !';
      return `En formation sur ${ordre.sur.nom} !`;
    }
    case 'REPOS':
      return 'Repos !';
    case 'RATISSER':
      return ordre.vers ? `Ratissez vers le ${ordre.vers.nom} !` : 'Ratissez !';
    case 'CHARGER':
      return ordre.vers ? `Chargez vers le ${ordre.vers.nom} !` : 'Chargez !';
    case 'RECULER':
      return ordre.vers ? `Reculez vers le ${ordre.vers.nom} !` : 'Reculez !';
    default:
      return '… ?';
  }
}
