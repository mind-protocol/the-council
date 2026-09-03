/**
 * 🧠 Cognition / Orientation — où pointe mon corps. Calculé au rythme de
 * l'attention (après chaque perception), en deux étages :
 *   1. en formation, EN PLACE → face au front (doctrine, hors arbitrage)
 *   2. sinon : ARBITRAGE pondéré de trois composantes — « où vais-je »
 *      (poids ∝ vitesse), « vers les gens intéressants » (les objets retenus
 *      par l'attention), « comme les gens » (conformité des regards).
 *      Le FLAG `facer` INVERSE les pondérations de certains objets : on ne
 *      s'aligne pas sur eux, on leur fait FACE — poids boosté vers eux
 *      (poidsFace), conformité inversée (leur cap + π). Facés : celui qui
 *      vient de parler (écho d'ordre), mes interlocuteurs quand je discute,
 *      et (réservé) tout ennemi perçu.
 *   3. résultante sous le seuil → conserver (retour null).
 * La continuité est ailleurs : ⚙️ borne la rotation (rotationMax).
 */

const versUnitaire = (de, vers) => {
  const dx = vers.x - de.x, dy = vers.y - de.y;
  const d = Math.hypot(dx, dy);
  return d > 1e-6 ? { x: dx / d, y: dy / d } : null;
};

/**
 * @param {Object} ctx
 * @param {{x, y}} ctx.vitesse — proprioception (vue 🌍)
 * @param {string|undefined} ctx.etatBrain — condition courante du brain
 * @param {{capFormation?: number, enPlace?: boolean}|null} ctx.formation — debug du brain
 * @param {Object} ctx.representation
 * @param {Object} ctx.params
 * @returns {{cap: number, condition: string, composantes: Object|null} | null}
 */
export function arbitrerOrientation({ vitesse, etatBrain, formation, representation, params }) {
  const p = params.orientation;
  const moi = representation.moi;
  if (!moi.pos) return null;

  // 0. UN ENNEMI CRU À PORTÉE D'ENGAGEMENT SE FACE D'OFFICE — quel que soit
  // l'état (on ne tourne JAMAIS le dos à une lance à deux mètres). Prime
  // même sur la règle de formation ; le recul lent reste corporel (⚙️).
  // SEULE exception : la panique — le fuyard tourne le dos, et paie ce choix
  // (c'est ce qui rend la déroute mortelle).
  if (etatBrain !== 'fuit') {
    let proche = null;
    let dMin = Infinity;
    for (const c of representation.contactsCrus?.() ?? []) {
      if (!c.livree || !representation.maLivree || c.livree === representation.maLivree) continue;
      const d = Math.hypot(c.pos.x - moi.pos.x, c.pos.y - moi.pos.y);
      if (d < dMin) {
        dMin = d;
        proche = c;
      }
    }
    if (proche && dMin < params.combat.rayonEngagement) {
      return {
        cap: Math.atan2(proche.pos.y - moi.pos.y, proche.pos.x - moi.pos.x),
        condition: 'combat',
        composantes: null,
      };
    }
  }

  // 1. en formation (statique ou en ratissage), en place : face au front
  if (
    (etatBrain === 'enFormation' || etatBrain === 'ratisse' || etatBrain === 'recule') &&
    formation?.enPlace &&
    Number.isFinite(formation.capFormation)
  ) {
    return { cap: formation.capFormation, condition: 'formation', composantes: null };
  }

  // FLAGS facer — les conditions spéciales inversent les pondérations
  const facesIds = new Set();
  const facesTas = new Set();
  const recu = representation.ordre();
  if (recu && recu.ageS < p.dureeEchoOrdre) facesIds.add(recu.emetteur);
  if (etatBrain === 'discute') {
    facesTas.add('escouade');
    facesTas.add('unite');
  }
  // (réservé) ennemis : toute livrée adverse perçue sera facée d'office

  // 2. arbitrage pondéré
  const composantes = { mouvement: { x: 0, y: 0 }, versGens: { x: 0, y: 0 }, commeGens: { x: 0, y: 0 } };
  const v = Math.hypot(vitesse.x, vitesse.y);
  if (v > 0.05) {
    const w = p.poidsMouvement * Math.min(1, v / params.vitesseMax);
    composantes.mouvement = { x: (vitesse.x / v) * w, y: (vitesse.y / v) * w };
  }

  const interessants = representation.snapshotDebug();
  const versAccum = { x: 0, y: 0 };
  const regardAccum = { x: 0, y: 0 };
  let poidsVers = 0;
  let nRegards = 0;
  for (const ind of interessants.individus) {
    if (!ind.pos) continue;
    const face = facesIds.has(ind.id);
    const u = versUnitaire(moi.pos, ind.pos);
    if (u) {
      const w = face ? p.poidsFace : 1;
      versAccum.x += u.x * w;
      versAccum.y += u.y * w;
      poidsVers += w;
    }
    if (Number.isFinite(ind.cap)) {
      // facé : conformité INVERSÉE (face-à-face = son cap + π)
      const s = face ? -1 : 1;
      regardAccum.x += Math.cos(ind.cap) * s;
      regardAccum.y += Math.sin(ind.cap) * s;
      nRegards++;
    }
  }
  for (const t of interessants.tas) {
    if (!t.barycentre) continue; // croyance sans position (rumeur) : rien à regarder
    const u = versUnitaire(moi.pos, t.barycentre);
    if (u) {
      const w = facesTas.has(t.etiquette) ? p.poidsFace : 1;
      versAccum.x += u.x * w;
      versAccum.y += u.y * w;
      poidsVers += w;
    }
  }
  if (poidsVers > 0) {
    composantes.versGens = {
      x: (versAccum.x / poidsVers) * p.poidsVersGens,
      y: (versAccum.y / poidsVers) * p.poidsVersGens,
    };
  }
  if (nRegards > 0) {
    composantes.commeGens = {
      x: (regardAccum.x / nRegards) * p.poidsCommeGens,
      y: (regardAccum.y / nRegards) * p.poidsCommeGens,
    };
  }

  const rx = composantes.mouvement.x + composantes.versGens.x + composantes.commeGens.x;
  const ry = composantes.mouvement.y + composantes.versGens.y + composantes.commeGens.y;
  if (Math.hypot(rx, ry) < p.seuilResultante) return null; // 3. conserver
  const condition = facesIds.size || facesTas.size ? 'face' : 'arbitrage';
  return { cap: Math.atan2(ry, rx), condition, composantes };
}
