/**
 * ⚙️ Physique / Acoustique / Portée de voix — première passe.
 * La propagation d'une parole est un fait PHYSIQUE : c'est ici que la
 * Transmission (📯) demande « qui peut entendre ce cri ? ». Le premier
 * consommateur réel est la boîte de message de la page (index.html) : ce
 * qu'un homme dit depuis la carte est entendu de tous ceux à portée, et
 * d'eux seuls.
 * Les bulles (🖥️ calque bulles) sont la viz de cette chaîne.
 * Croissance : atténuation par les murs (terrain), bruit ambiant de la
 * mêlée, intensité `cor`, délais de propagation.
 */

/**
 * Rayon effectif d'une parole, en mètres. Une intensité inconnue est une
 * faute d'appel, pas un murmure par défaut : on la refuse.
 * @param {{intensite?: 'murmure'|'parole'|'cri'}} [options]
 * @param {{acoustique: {porteeVoix: Object}}} params
 * @returns {number}
 */
export function porteeVoix({ intensite = 'parole' } = {}, params) {
  const rayon = params?.acoustique?.porteeVoix?.[intensite];
  if (typeof rayon !== 'number') throw new Error('porteeVoix : intensite inconnue ' + intensite);
  return rayon;
}

/**
 * Qui entend cette parole ? Les ids des corps à portée du locuteur — sans
 * distinction de camp ni de vie : l'air ne trie pas, c'est l'appelant qui
 * retire le locuteur lui-même et les gisants s'il le souhaite.
 * (demain : moins les masqués par les murs, moins les couverts par le bruit)
 * @param {{x, y}} posLocuteur
 * @param {{intensite?: string}} options
 * @param {(pos, rayon) => Array<{id}>} voisinsDans — vue 🌍 (index spatial)
 * @param {Object} params
 * @returns {number[]}
 */
export function quiEntend(posLocuteur, options, voisinsDans, params) {
  const rayon = porteeVoix(options, params);
  return voisinsDans(posLocuteur, rayon).map((v) => v.id);
}
