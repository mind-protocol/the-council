/**
 * LA PARTIE — sauver et charger un monde. Une seule definition, partagee par
 * l'ecran (src/main.js) et par les bancs headless (coding/), pour qu'un champ
 * ajoute d'un cote ne manque jamais de l'autre.
 *
 * Ce n'est pas un container : c'est une fonction sur les containers. Elle ne
 * connait que leurs portes `etat()` / `restaurer()`.
 *
 * Doctrine : ../../docs/etat-sauvegardes.md — la sim EST le monde, une
 * sauvegarde est un INSTANTANE, et rien de reconstructible n'y entre.
 * Format champ par champ : ../docs/sauvegarde.md.
 */

// v2 : l'etat du HASARD entre dans l'instantane. Sans lui la photo etait
// fidele (corps, blessures, tetes, bit-exact a la relecture) mais la SUITE
// divergeait — un monde relu repartait de `creerRng(seed)`, donc du hasard du
// premier jour. Mesure avant correctif : 60 corps sur 60, ~2 m apres 10 s.
export const VERSION = 2;

/**
 * @param {{monde, corpsContainer, cognition, orchestration, rng}} sim
 * @param {{titre?: string, couvertureDepuis?: number}} [opts]
 *   — `couvertureDepuis` : la fenetre de couverture gardee pour qui ne
 *     commande pas (voir cognition.etat). `Infinity` = sauvegarde pleine,
 *     ce dont les bancs se servent pour mesurer ce que la decimation coute.
 * @returns {Object} — donnee plate, JSON-able, sans reference vivante
 */
export function sauver({ monde, corpsContainer, cognition, orchestration, rng }, { titre, couvertureDepuis } = {}) {
  return {
    version: VERSION,
    scenario: titre ?? null,
    // l'horloge entiere, pas seulement tempsSim : `accumMs` decide du
    // nombre de pas joues a la premiere frame de la reprise.
    horloge: orchestration.transport.etat(),
    tempsSim: orchestration.transport.etat().tempsSim,
    monde: monde.etat(),
    corps: corpsContainer.etat(),
    cognition: cognition.etat(couvertureDepuis === undefined ? undefined : { couvertureDepuis }),
    // Le hasard fait partie du monde : la graine courante et la reserve
    // de Box-Muller. Deux nombres, et la suite se rejoue a l'identique.
    rng: rng ? rng.etat() : null,
  };
}

/**
 * Reprend un instantane SUR UN MONDE DEJA COMPOSE : les corps existent, les
 * tetes sont attachees a leur semence. L'ordre n'est pas libre — une tete
 * restauree avant son corps croirait en quelqu'un qui n'existe pas.
 */
export function charger(d, { monde, corpsContainer, cognition, rng, orchestration }) {
  if (!d || d.version !== VERSION) throw new Error(`sauvegarde : version inconnue (${d?.version})`);
  monde.restaurer(d.monde);          // 🌍 les corps d'abord : les tetes les nomment
  corpsContainer.restaurer(d.corps); // ❤️ ce qu'ils ont subi
  cognition.restaurer(d.cognition);  // 🧠 les tetes, en dernier
  if (rng && d.rng) rng.restaurer(d.rng); // 🎲 et le hasard ou on l'avait laisse
  if (orchestration && d.horloge) orchestration.transport.restaurer(d.horloge); // ⏱️ et le temps
}
