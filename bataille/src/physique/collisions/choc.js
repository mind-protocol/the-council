/**
 * ⚙️ Physique / Collisions / Choc — le TRANSFERT DE QUANTITÉ DE MOUVEMENT :
 * la poussée de masse. Quand deux corps se pénètrent en se RAPPROCHANT vite,
 * ils échangent une impulsion le long de la normale (presque molle : on
 * encaisse, on ne rebondit pas) — pondérée par les masses : le lourd bouscule
 * le léger, une colonne profonde fait reculer une ligne mince, et demain un
 * demi-tonne au galop ouvre un rang.
 * L'a-coup subi (delta-v) bouscule toujours ; au-delà d'un cran, il RENVERSE
 * (le corps part à terre, se relèvera) — la durée croît avec l'excès.
 * Fonction PURE : vitesses corrigées + renversements en sortie, rien d'écrit.
 */

/**
 * @param {{id, pos: {x,y}, rayon: number, masse: number}[]} corps — provisoires du pas
 * @param {Map<number, {x,y}>} vels — vitesses du pas (lues, jamais modifiées)
 * @param {{restitution, vRelMin, deltaVRenverse, dureeMinS, dureeParDeltaV, dureeMaxS}} params
 * @returns {{velsCorrigees: Map<number, {x,y}>, renversements: Array<{id, dureeS, deltaV}>,
 *   chocs: Array<{a, b, pos: {x,y}, impulsion: number}>}}
 */
export function resoudreChocs(corps, vels, params, pairesIds = null) {
  const velsCorrigees = new Map();
  const renversements = [];
  const chocs = [];
  const velDe = (id) => velsCorrigees.get(id) ?? vels.get(id) ?? { x: 0, y: 0 };

  // paires candidates : la grille du tick (ids), ou toutes (fallback n²)
  const parId = pairesIds ? new Map(corps.map((c) => [c.id, c])) : null;
  const candidates = pairesIds
    ? pairesIds.map(([a, b]) => [parId.get(a), parId.get(b)]).filter(([a, b]) => a && b)
    : (() => {
        const liste = [];
        for (let i = 0; i < corps.length; i++) {
          for (let j = i + 1; j < corps.length; j++) liste.push([corps[i], corps[j]]);
        }
        return liste;
      })();

  for (const [ca, cb] of candidates) {
    {
      const dx = cb.pos.x - ca.pos.x;
      const dy = cb.pos.y - ca.pos.y;
      const d = Math.hypot(dx, dy);
      if (d >= ca.rayon + cb.rayon) continue; // pas en contact
      const ux = d > 1e-9 ? dx / d : 1;
      const uy = d > 1e-9 ? dy / d : 0;

      const va = velDe(ca.id), vb = velDe(cb.id);
      // vitesse d'APPROCHE le long de la normale (positive = ils se ferment)
      const vRel = (va.x - vb.x) * ux + (va.y - vb.y) * uy;
      if (vRel < params.vRelMin) continue; // une bousculade, pas un choc

      // l'impulsion du choc (1D le long de la normale, restitution partielle)
      const ma = ca.masse ?? 80, mb = cb.masse ?? 80;
      const j1 = ((1 + params.restitution) * vRel * ma * mb) / (ma + mb);
      const dva = j1 / ma; // l'a-coup subi par chacun — c'est LUI qui renverse
      const dvb = j1 / mb;
      velsCorrigees.set(ca.id, { x: va.x - ux * dva, y: va.y - uy * dva });
      velsCorrigees.set(cb.id, { x: vb.x + ux * dvb, y: vb.y + uy * dvb });
      chocs.push({
        a: ca.id,
        b: cb.id,
        pos: { x: ca.pos.x + ux * ca.rayon, y: ca.pos.y + uy * ca.rayon },
        impulsion: j1,
      });

      // le RENVERSEMENT : durée à terre qui croît avec l'excès (continu)
      for (const [id, dv] of [[ca.id, dva], [cb.id, dvb]]) {
        if (dv <= params.deltaVRenverse) continue;
        const dureeS = Math.min(
          params.dureeMaxS,
          params.dureeMinS + (dv - params.deltaVRenverse) * params.dureeParDeltaV
        );
        renversements.push({ id, dureeS, deltaV: dv });
      }
    }
  }
  return { velsCorrigees, renversements, chocs };
}
