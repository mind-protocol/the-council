/**
 * 🏃 Steering / Refus de la monture — LE RÉFLEXE DU CHEVAL : il ne s'enfonce
 * pas dans une masse hérissée. Jugé sur le RÉEL devant lui (comme l'acte de
 * frapper juge sur les corps réels) : les pointes LEVÉES (posture 'pret')
 * de livrée adverse dans la fenêtre de regard — une pique compte plein, une
 * épée inquiète peu. CONTINU : le freinage croît avec le hérissement, la
 * dérobade part vers le côté le moins piqué. Le cavalier VEUT, le cheval
 * refuse — c'est ce qui fait tenir les murs de piques, sans une règle de
 * plus nulle part.
 * Fonction pure : vitesse corrigée + intensité en sortie.
 */

/**
 * @param {Object} args
 * @param {{x,y}} args.pos — la position de la MONTURE
 * @param {string} args.livree — sa livrée (l'adverse se voit)
 * @param {{x,y}} args.vel — la vitesse désirée du couple (avant refus)
 * @param {(pos, rayon) => Array} args.voisinsDans — vue 🌍 (le réel devant)
 * @param {(id: number) => {allonge: number}} args.armeDe — vue ❤️
 * @param {Object} args.params — params.cheval.refus
 * @returns {{vel: {x,y}, intensite: number, regard: {x,y}|null}}
 */
export function refusDeLaMonture({ pos, livree, vel, voisinsDans, armeDe, params }) {
  const r = params.refus;
  const vitesse = Math.hypot(vel.x, vel.y);
  if (vitesse < 1e-6) return { vel, intensite: 0, regard: null };
  const ux = vel.x / vitesse;
  const uy = vel.y / vitesse;

  // la fenêtre de regard : devant, d'autant plus loin qu'on va vite
  const portee = r.regardBaseM + vitesse * r.regardParVitesseS;
  const regard = { x: pos.x + ux * portee, y: pos.y + uy * portee };

  let pointes = 0;
  let aGauche = 0;
  let aDroite = 0;
  for (const v of voisinsDans(regard, r.rayonRegard)) {
    if (v.livree === livree) continue; // les siens ne l'effraient pas
    if (v.posture !== 'pret') continue; // seule la pointe LEVÉE hérisse
    const poids = (armeDe(v.id)?.allonge ?? 0) >= r.allongePique ? r.poidsPique : r.poidsAutre;
    pointes += poids;
    const cote = ux * (v.pos.y - pos.y) - uy * (v.pos.x - pos.x);
    if (cote >= 0) aDroite += poids;
    else aGauche += poids;
  }

  const intensite = Math.min(1, pointes / r.pointesPourStopper);
  if (intensite <= 0) return { vel, intensite: 0, regard };

  // freine, et dérobe vers le côté le moins hérissé (départage déterministe)
  const sens = aGauche <= aDroite ? -1 : 1; // -1 : vers la gauche
  const derive = r.deriveMax * intensite;
  return {
    vel: {
      x: ux * vitesse * (1 - intensite) + -uy * sens * derive,
      y: uy * vitesse * (1 - intensite) + ux * sens * derive,
    },
    intensite,
    regard,
  };
}
