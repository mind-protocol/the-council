/**
 * ⚙️ Physique / Forces / Coude-à-coude — les rangs se soudent : deux corps
 * CÔTE À CÔTE (décalage surtout latéral) aux CAPS PARALLÈLES s'attirent
 * doucement vers l'épaulement (espacement cible). Défini sur des FAITS
 * géométriques purs — aucun flag « formation », aucune livrée : une ligne
 * dressée se soude, un attroupement aux regards divergents ne colle pas,
 * et deux lignes ennemies face à face (caps opposés) s'ignorent.
 * Tire LATÉRALEMENT seulement (les rangs ne s'aspirent pas en colonne).
 * Intensités en m/s (biais de vitesse, comme les répulsions). O(n²) assumé.
 */

/**
 * @param {Iterable<Object>} tousCorps — vue 🌍 (pos, cap)
 * @param {Map<number, {x, y}>} forces — accumulateur (partagé avec les répulsions)
 * @param {{capParallele, porteeLaterale, longitudinalMax, espacement, intensite}} params
 */
export function ajouterCoudeACoude(tousCorps, forces, params, paires = null) {
  const { capParallele, porteeLaterale, longitudinalMax, espacement, intensite } = params;

  const ajouter = (id, fx, fy) => {
    const f = forces.get(id) ?? { x: 0, y: 0 };
    f.x += fx;
    f.y += fy;
    forces.set(id, f);
  };

  const surPaire = (ca, cb) => {
    // caps parallèles ? (le fait géométrique n° 1)
    const dCap = Math.atan2(Math.sin(cb.cap - ca.cap), Math.cos(cb.cap - ca.cap));
    if (Math.abs(dCap) > capParallele) return;

    // décalage surtout LATÉRAL dans le repère du cap moyen ? (fait n° 2)
    const capMoyen = ca.cap + dCap / 2;
    const avant = { x: Math.cos(capMoyen), y: Math.sin(capMoyen) };
    const dx = cb.pos.x - ca.pos.x;
    const dy = cb.pos.y - ca.pos.y;
    const long = dx * avant.x + dy * avant.y;
    const lat = -dx * avant.y + dy * avant.x;
    const aLat = Math.abs(lat);
    if (Math.abs(long) > longitudinalMax) return;
    if (aLat <= espacement || aLat >= porteeLaterale) return;

    // ressort doux vers l'épaulement, tiré le long de l'axe latéral
    const t = (aLat - espacement) / (porteeLaterale - espacement); // 0 → 1
    const f = intensite * t * Math.sign(lat);
    ajouter(ca.id, -avant.y * f, avant.x * f);
    ajouter(cb.id, avant.y * f, -avant.x * f);
  };
  if (paires) {
    for (const [ca, cb] of paires) surPaire(ca, cb);
  } else {
    const corps = [...tousCorps];
    for (let a = 0; a < corps.length; a++) {
      for (let b = a + 1; b < corps.length; b++) surPaire(corps[a], corps[b]);
    }
  }
}
