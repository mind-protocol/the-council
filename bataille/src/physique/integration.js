/**
 * ⚙️ Physique / Intégration — le pas élémentaire d'UN corps, avec DEUX
 * inerties :
 * - linéaire : la vitesse converge vers la cible (désirée + forces) sous
 *   accelMax — un demi-tour devient un arc de freinage-réaccélération ;
 * - angulaire : le cap converge vers le cap désiré (orientation 🧠) sous
 *   rotationMax, plus court chemin angulaire — on ne pivote pas instantanément.
 * Sans cap désiré : le cap suit la direction du mouvement (> 0.3 m/s), et se
 * conserve à l'arrêt. Fonction PURE — l'écriture passe par l'expose (🌍).
 */

/**
 * @param {{pos: {x,y}, vel: {x,y}, cap: number}} corps — état actuel (lu, pas modifié)
 * @param {{x, y} | undefined} velDesiree — de 🏃 Action
 * @param {{x, y} | undefined} force — des répulsions (m/s)
 * @param {{cap: number, vitesseRotation: number} | undefined} consigneCap
 *   — de 🏃 Action : le cap voulu et SON rythme (durée humaine ~N tirée en
 *   🧠) ; rotationMax reste le plafond corporel que rien ne dépasse
 * @param {number} dt
 * @param {{accelMax?: number, orientation?: {rotationMax?: number}}} [params]
 * @returns {{pos: {x,y}, vel: {x,y}, cap: number}}
 */
export function integrer(corps, velDesiree, force, consigneCap, dt, params = {}) {
  // l'accélération est un fait du GABARIT : un cheval s'arrête et s'élance
  // mieux qu'un homme chargé — c'est ce qui rend le refus exécutable
  const accelMax = corps.gabarit === 'cheval' ? params.cheval?.accelMax ?? 3.5 : params.accelMax ?? 1.5;
  const rotationMax = params.orientation?.rotationMax ?? 3;
  const vd = velDesiree ?? { x: 0, y: 0 };
  const f = force ?? { x: 0, y: 0 };
  const cible = { x: vd.x + f.x, y: vd.y + f.y };

  let dvx = cible.x - corps.vel.x;
  let dvy = cible.y - corps.vel.y;
  const dv = Math.hypot(dvx, dvy);
  const max = accelMax * dt;
  if (dv > max) {
    dvx = (dvx / dv) * max;
    dvy = (dvy / dv) * max;
  }
  let vel = { x: corps.vel.x + dvx, y: corps.vel.y + dvy };

  // LA MARCHE ARRIÈRE EST LENTE — une propriété du CORPS, pas de la volonté :
  // quand la vitesse s'oppose au cap (on recule face à l'ennemi), elle est
  // bornée. Fuir vite exige de tourner le dos — ce choix appartient au 🧠.
  const vRecul = params.vitesseRecul ?? 0.5;
  const vNorme = Math.hypot(vel.x, vel.y);
  if (vNorme > vRecul) {
    const versAvant = (vel.x * Math.cos(corps.cap) + vel.y * Math.sin(corps.cap)) / vNorme;
    if (versAvant < -0.2) {
      vel = { x: (vel.x / vNorme) * vRecul, y: (vel.y / vNorme) * vRecul };
    }
  }

  // cap cible : la consigne (🧠, à son rythme), sinon le sens de marche
  const capCible =
    consigneCap?.cap ?? (Math.hypot(vel.x, vel.y) > 0.3 ? Math.atan2(vel.y, vel.x) : null);
  let cap = corps.cap;
  if (capCible !== null) {
    const taux = Math.min(consigneCap?.vitesseRotation ?? rotationMax, rotationMax);
    let delta = Math.atan2(Math.sin(capCible - corps.cap), Math.cos(capCible - corps.cap));
    const maxRot = taux * dt;
    delta = Math.max(-maxRot, Math.min(maxRot, delta));
    cap = Math.atan2(Math.sin(corps.cap + delta), Math.cos(corps.cap + delta));
  }

  return {
    pos: { x: corps.pos.x + vel.x * dt, y: corps.pos.y + vel.y * dt },
    vel,
    cap,
  };
}
