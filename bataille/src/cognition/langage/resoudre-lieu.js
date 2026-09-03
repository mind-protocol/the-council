/**
 * 🧠 Langage / Résoudre un lieu — PAROLE → MATH : une référence symbolique
 * (format 📯) + MES croyances → une géométrie {pos, cap}. Héberge LES
 * IMPLICITES (ce que l'ordre ne dit pas, déduit par convention).
 * PUR, ne lit que la Représentation : une résolution sur croyances périmées
 * se trompe — c'est VOULU (le mécanisme du « mal comprendre »).
 * null est un résultat : « je ne sais pas où c'est ».
 */

/** Les mots de direction → un cap (repère écran : y vers le bas, sud en bas). */
const CAPS_DIRECTIONS = {
  est: 0, 'sud-est': Math.PI / 4, sud: Math.PI / 2, 'sud-ouest': (3 * Math.PI) / 4,
  ouest: Math.PI, 'nord-ouest': (-3 * Math.PI) / 4, nord: -Math.PI / 2, 'nord-est': -Math.PI / 4,
};

/** @param {string|undefined} nom @returns {number|null} */
export function capDeDirection(nom) {
  return nom !== undefined && nom in CAPS_DIRECTIONS ? CAPS_DIRECTIONS[nom] : null;
}

/**
 * Résout le repère d'un ordre EN_FORMATION. Échelle :
 * 1. « sur moi » (explicite) → le corps CRU du locuteur, locuteur dedans.
 * 2. implicite, et ma croyance `unite` a une première ligne nette et
 *    fraîche → LA FORMATION EST SON PROPRE REPÈRE (auto-référent, dynamique :
 *    le chef peut circuler, rien ne bouge). Locuteur dehors.
 * 3. implicite, pas de forme lisible (premier rassemblement) → amorçage :
 *    devant le locuteur, première ligne face à lui. Locuteur dehors.
 *
 * @param {{ordre: Object, emetteur: number}} recu
 * @param {ReturnType<import('../representation.js').creerRepresentation>} representation
 * @param {Object} params
 * @param {{ordreDrill: number[], forme: Object}} [drill] — le savoir du drill :
 *   sert à dériver l'origine du BARYCENTRE cru (une moyenne, stable) plutôt
 *   que de la tranche avant (un max → effet CLIQUET : quiconque dépasse fait
 *   avancer le repère et la formation rampe)
 * @returns {{origine: {pos: {x,y}, cap: number}, chefDedans: boolean,
 *            source: 'surLocuteur'|'premiereLigne'|'devantLocuteur'} | null}
 */
export function resoudreEnFormation(recu, representation, params, drill) {
  // le locuteur se résout LUI-MÊME par proprioception (on ne se « croit »
  // pas soi-même dans les suivis) — son cap propre viendra avec moi.cap
  const emetteur =
    recu.emetteur === representation.monId
      ? representation.moi.pos && { pos: representation.moi.pos, cap: 0 }
      : representation.individuCru(recu.emetteur);

  // 1. explicite : « sur moi »
  if (recu.ordre.sur?.type === 'locuteur') {
    if (!emetteur?.pos) return null;
    return {
      origine: { pos: emetteur.pos, cap: emetteur.cap },
      chefDedans: true,
      source: 'surLocuteur',
    };
  }

  // 2. implicite : la formation existe déjà — son repère cru. Trois garde-fous :
  // nette (les lances alignées), fraîche, et SUBSTANTIELLE (au moins la moitié
  // du drill — un fragment de 2 hommes n'est pas « la formation », sinon
  // chacun bascule sur un fantôme différent). Le cap vient de la forme
  // perçue ; la première ligne se dérive du BARYCENTRE (stable) + la
  // demi-profondeur du drill (savoir statique)
  const unite = representation.tasCru('unite');
  // l'effectif attendu : le drill MOINS les morts vus (croyance) — une unité
  // saignée garde un repère de formation à sa taille réelle crue
  const effectifDrill = drill ? Math.max(1, representation.attendu?.('unite') ?? drill.ordreDrill.length - 1) : Infinity;
  if (
    unite?.premiereLigne &&
    unite.nettete >= params.perception.forme.netteteMin &&
    unite.ageS < params.formation.fraicheurRepere &&
    (unite.formeEffectif ?? 0) >= effectifDrill / 2 // le NOYAU FORMÉ, pas le tas
  ) {
    const { largeur, espacementRang } = drill?.forme ?? {};
    // demi-profondeur EXACTE : moyenne des rangs pondérée par leur occupation
    // (un dernier rang creux décale le barycentre — l'ignorer ferait ramper
    // la formation de quelques dizaines de cm par cycle, effet cliquet)
    let demiProfondeur = 0;
    if (largeur && effectifDrill > 0 && Number.isFinite(effectifDrill)) {
      let sommeRangs = 0;
      for (let k = 0; k < effectifDrill; k++) sommeRangs += Math.floor(k / largeur);
      demiProfondeur = (espacementRang ?? 1.2) * (sommeRangs / effectifDrill);
    }
    const avant = { x: Math.cos(unite.cap), y: Math.sin(unite.cap) };
    return {
      origine: {
        pos: {
          x: unite.barycentre.x + avant.x * demiProfondeur,
          y: unite.barycentre.y + avant.y * demiProfondeur,
        },
        cap: unite.cap,
      },
      chefDedans: false,
      source: 'premiereLigne',
    };
  }

  // 3. implicite : amorçage devant le locuteur — dans SON cap cru (il
  // regarde ses hommes quand il crie), première ligne face à lui. Le cap
  // du locuteur est STABLE : pas de rétroaction avec la troupe qui bouge.
  if (!emetteur?.pos) return null;
  const dist = params.formation.distanceImplicite;
  const ax = Math.cos(emetteur.cap);
  const ay = Math.sin(emetteur.cap);
  return {
    origine: {
      pos: { x: emetteur.pos.x + ax * dist, y: emetteur.pos.y + ay * dist },
      cap: Math.atan2(-ay, -ax), // l'avant de la formation pointe VERS lui
    },
    chefDedans: false,
    source: 'devantLocuteur',
  };
}
